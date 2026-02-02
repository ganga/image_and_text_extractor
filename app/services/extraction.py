import cv2
import numpy as np
import logging
from pathlib import Path
from paddleocr import PPStructure
from paddleocr.ppstructure.recovery.recovery_to_doc import sorted_layout_boxes
from PIL import Image

logger = logging.getLogger(__name__)

class ExtractionService:
    def __init__(self):
        # Initialize PP-Structure (English)
        # table=False because we focus on general layout/text/figures for this MVP
        # recovery=True allows us to get structured results
        logger.info("Initializing PaddleOCR PP-Structure...")
        self.engine = PPStructure(
            show_log=False,
            image_orientation=False,
            lang='en',
            layout=True,
            table=False, 
            ocr=True
        )
    
    def run_extraction(self, image_bytes: bytes, request_id: str, output_dir: Path, store_outputs: bool, return_annotated: bool):
        """
        Runs layout analysis and OCR on the provided image bytes.
        Returns the structured response data (meta, blocks, figures, exports).
        """
        import time
        t_start = time.time()
        
        # 1. Load image
        # Convert bytes to numpy array for cv2
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
             raise ValueError("Could not decode image")
        
        height, width, _ = img.shape
        t_preprocess = (time.time() - t_start) * 1000
        
        # 2. Run Inference
        t_layout_start = time.time()
        # parameters: img: ndarray
        results = self.engine(img)
        t_layout_end = time.time()
        
        # PaddleOCR returns a list of dicts. For PP-Structure, usually just one item for a single page image?
        # Actually PPStructure returns a list of regions.
        
        blocks = []
        figures = []
        
        # Helper to convert layout to our schema
        # Paddle result structure: [{'type': 'text', 'bbox': [x1, y1, x2, y2], 'img': array, 'res': [{'text': '...', 'confidence': 0.9}, ...]}, ...]
        
        # We need to sort by reading order manually or rely on Paddle. 
        # paddleocr.ppstructure.recovery.recovery_to_doc.sorted_layout_boxes sorts them.
        # But `results` is ALREADY a list of regions.
        
        # Let's standardize the format
        # Each 'region' in results has:
        # - type: str
        # - bbox: [x1, y1, x2, y2]
        # - video-frame irrelevant
        # - res: list of dict(text, confidence, text_region) OR single dict (for table)
        # - img: cropped image of the region
        
        # Sorting
        # We can implement a simple top-to-bottom sort based on bbox y1
        results.sort(key=lambda x: x['bbox'][1])
        
        total_ocr_time = 0 # Included in layout time for PPStructure usually, unless we separate it. 
                           # Implementation detail: PPStructure runs OCR internally on text regions.
        
        crop_time_start = time.time()
        
        for idx, region in enumerate(results):
            region_type = region.get('type', 'unknown').lower()
            bbox = region.get('bbox') # [x1, y1, x2, y2]
            
            # Map Paddle types to our Contract types
            # Paddle: title, text, figure, table, header, footer, reference, equation
            # Contract: title, text, list, table, figure
            mapped_type = 'text'
            if region_type == 'figure': mapped_type = 'figure'
            elif region_type == 'table': mapped_type = 'table'
            elif region_type == 'title': mapped_type = 'title'
            elif region_type == 'list': mapped_type = 'list'
            
            block_id = f"b{idx+1}"
            
            # Extract text and lines
            block_text = ""
            block_lines = []
            block_conf = 0.0
            
            res = region.get('res')
            if isinstance(res, list):
                # Text region
                texts = [line['text'] for line in res]
                block_text = "\n".join(texts)
                confs = [line['confidence'] for line in res]
                block_conf = float(np.mean(confs)) if confs else 0.0
                
                for line_res in res:
                    line_text = line_res['text']
                    line_conf = line_res['confidence']
                    # Re-calculate line bbox if possible, or just skip local bbox if not provided
                    # PPStructure often provides text_region inside res
                    # but let's keep it simple for MVP
                    block_lines.append({
                        "bbox": [0,0,0,0], # Placeholder, extraction is complex here without more parsing
                        "text": line_text,
                        "confidence": line_conf
                    })
            
            # Check for Figure
            if mapped_type == 'figure':
                # Save cropped image
                fig_id = f"f{len(figures)+1}"
                rel_path = None
                if store_outputs:
                    # The 'img' key in region contains the crop, but it might be drawn on? 
                    # Actually safer to crop from original myself or use region['img']
                    # region['img'] is an ndarray
                    crop_img = region.get('img')
                    if crop_img is not None:
                         # Save it
                         fname = f"{fig_id}_{region_type}.png"
                         # output_dir is /outputs/<request_id>/
                         # We need to make sure we don't save if not requested, but logic says store_outputs
                         # rel_path is "figures/..." relative to request dir?
                         # Contract says: relative path ... typically under /outputs/<request_id>/...
                         save_path = output_dir / fname
                         cv2.imwrite(str(save_path), crop_img)
                         rel_path = f"/outputs/{request_id}/{fname}"

                figures.append({
                    "id": fig_id,
                    "bbox": bbox,
                    "image_path": rel_path or "", # Contract requires string
                    "caption": None,
                    "confidence": region.get('score', 0.9) # Layout score
                })
            
            blocks.append({
                "id": block_id,
                "type": mapped_type,
                "bbox": bbox,
                "order": idx + 1,
                "text": block_text,
                "confidence": block_conf,
                "lines": block_lines
            })

        t_crop_end = time.time()
        
        annotated_path = None
        if store_outputs and return_annotated:
            # We can use paddle's utility or draw ourselves. 
            # Draw ourselves for simplicity and consistency
            vis_img = img.copy()
            for b in blocks:
                x1, y1, x2, y2 = b['bbox']
                cv2.rectangle(vis_img, (x1, y1), (x2, y2), (0, 255, 0), 2)
                # Put ID
                cv2.putText(vis_img, b['id'], (x1, y1-5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 1)
            
            save_path = output_dir / "annotated.png"
            cv2.imwrite(str(save_path), vis_img)
            annotated_path = f"/outputs/{request_id}/annotated.png"

        
        timings = {
            "preprocess": int(t_preprocess),
            "layout": int((t_layout_end - t_layout_start) * 1000),
            "ocr": int(total_ocr_time * 1000), # Embedded in layout for PPStructure
            "crop": int((t_crop_end - crop_time_start) * 1000)
        }
        
        return {
            "meta": {
                "request_id": request_id,
                "image": {"width": width, "height": height},
                "timings_ms": timings
            },
            "blocks": blocks,
            "figures": figures,
            "exports": {
                "annotated_image_path": annotated_path
            }
        }

# Global instance
_service = None

def get_extraction_service():
    global _service
    if _service is None:
        _service = ExtractionService()
    return _service
