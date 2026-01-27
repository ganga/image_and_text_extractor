from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import FileResponse
import uuid
import time
import os
from io import BytesIO
from PIL import Image

APP_TITLE = "Book Screenshot Extraction API"
APP_VERSION = "0.1.0"

# Resolve openapi.yaml from project root (mounted into container)
SPEC_PATH = Path(__file__).resolve().parents[1] / "openapi.yaml"

app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    description="Contract-first backend. Spec is served at /openapi.yaml",
)

@app.get("/health", tags=["system"])
def health():
    return {"status": "ok"}

@app.get("/openapi.yaml", include_in_schema=False)
def openapi_yaml():
    if not SPEC_PATH.exists():
        # You’ll see this clearly if the file wasn’t copied/mounted into the container
        return {"detail": f"Spec not found at {SPEC_PATH}"}
    return FileResponse(
        path=str(SPEC_PATH),
        media_type="application/yaml",
        filename="openapi.yaml",
    )

@app.post("/extract")
async def extract(file: UploadFile = File(...),store_outputs: bool = Form(True), return_annotated: bool = Form(True), ocr_engine: str = Form("paddle")):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image uploads are supported.")
    request_id = str(uuid.uuid4())
    OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "/shared_outputs")).resolve()
    if store_outputs:
        request_dir = OUTPUT_DIR / request_id
        request_dir.mkdir(parents=True, exist_ok=True)
    image_bytes = await file.read()
    try:
        with Image.open(BytesIO(image_bytes)) as img:
            width, height = img.size
            if width <= 0 or height <= 0:
                raise ValueError("Invalid image dimensions")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image file.")

    annotated_path = None
    if store_outputs and return_annotated:
        annotated_file = request_dir / "annotated.png"
        annotated_file.write_bytes(b"...")
        annotated_path = f"/outputs/{request_id}/annotated.png"

    # 4. Minimal response (contract-compliant)
    return {
        "meta": {
            "request_id": request_id,
            "image": {
                "width": width,
                "height": height
            },
            "timings_ms": {
                "preprocess": 0,
                "layout": 0,
                "ocr": 0,
                "crop": 0
            }
        },
        "blocks": [],
        "figures": [],
        "exports": {
            "annotated_image_path": annotated_path
        }
    }

    return {"status": "ok"}
