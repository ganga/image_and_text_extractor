from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as PlatypusImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from pathlib import Path
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class PDFService:
    def __init__(self):
        pass

    def create_pdf(self, blocks: List[Dict[str, Any]], output_path: Path):
        """
        Generates a PDF from the extracted blocks.
        
        Args:
            blocks: List of block dictionaries (from extraction service).
            output_path: Path where the PDF should be saved.
        """
        try:
            doc = SimpleDocTemplate(
                str(output_path),
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=72
            )
            
            story = []
            styles = getSampleStyleSheet()
            
            # Custom styles
            title_style = styles["Title"]
            normal_style = styles["Normal"]
            
            # Create a style for code/monospaced text if needed, or just improve Normal
            # For now, we map types to styles
            
            for block in blocks:
                block_type = block.get("type", "text")
                text = block.get("text", "")
                
                # ReportLab Paragraphs don't handle newlines well in default Normal style without <br/>
                # We need to replace newlines with <br/> for Paragraph
                formatted_text = text.replace("\n", "<br/>")
                
                if block_type == "title":
                    story.append(Paragraph(formatted_text, title_style))
                    story.append(Spacer(1, 12))
                elif block_type == "figure":
                    # If we have an image path, we could try to embed it
                    # But the extraction service might not have saved it or we might not have the path here easily
                    # depending on how 'blocks' is constructed.
                    # For MVP, we'll just note it's a figure or try to show caption/text
                    story.append(Paragraph(f"<i>[Figure: {formatted_text}]</i>", normal_style))
                    story.append(Spacer(1, 12))
                elif block_type == "table":
                     # Tables are complex. For now, dump text.
                    story.append(Paragraph(f"<b>[Table]</b><br/>{formatted_text}", normal_style))
                    story.append(Spacer(1, 12))
                else:
                    # Generic text
                    story.append(Paragraph(formatted_text, normal_style))
                    story.append(Spacer(1, 12))
            
            doc.build(story)
            logger.info(f"PDF generated successfully at {output_path}")
            return output_path
            
        except Exception as e:
            logger.error(f"Failed to generate PDF: {e}")
            raise

_service = None

def get_pdf_service():
    global _service
    if _service is None:
        _service = PDFService()
    return _service
