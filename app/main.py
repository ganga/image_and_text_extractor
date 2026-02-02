from pathlib import Path

from fastapi import FastAPI, File, Form, UploadFile, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
import uuid
import time
import os
from io import BytesIO
from PIL import Image

APP_TITLE = "Book Screenshot Extraction API"
APP_VERSION = "0.1.0"

# Resolve openapi.yaml from project root (mounted into container)
SPEC_PATH = Path(__file__).resolve().parents[1] / "openapi.yaml"
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "/shared_outputs")).resolve()

app = FastAPI(
    title=APP_TITLE,
    version=APP_VERSION,
    description="Contract-first backend. Spec is served at /openapi.yaml",
)

# Ensure the output directory exists
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

app.mount("/outputs", StaticFiles(directory=str(OUTPUT_DIR)), name="outputs")

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

from app.services.pdf_service import get_pdf_service
from app.services.extraction import get_extraction_service

@app.post("/extract")
async def extract(
    file: UploadFile = File(...),
    store_outputs: bool = Form(True), 
    return_annotated: bool = Form(True), 
    ocr_engine: str = Form("paddle"),
    generate_pdf: bool = Form(False)
):
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Only image uploads are supported.")
    
    request_id = str(uuid.uuid4())
    image_bytes = await file.read()
    
    # Validate image
    try:
        with Image.open(BytesIO(image_bytes)) as img:
            width, height = img.size
            if width <= 0 or height <= 0:
                raise ValueError("Invalid image dimensions")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image file.")

    request_dir = OUTPUT_DIR / request_id
    if store_outputs:
        request_dir.mkdir(parents=True, exist_ok=True)
        input_path = request_dir / f"input_{file.filename or 'image'}"
        input_path.write_bytes(image_bytes)

    response_data = None
    try:
        service = get_extraction_service()
        response_data = service.run_extraction(
            image_bytes=image_bytes, 
            request_id=request_id, 
            output_dir=request_dir if store_outputs else None, 
            store_outputs=store_outputs, 
            return_annotated=return_annotated
        )
    except Exception as e:
        # In production, log generic error and return 500
        print(f"Extraction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

    if generate_pdf and store_outputs:
        try:
            pdf_service = get_pdf_service()
            pdf_path = request_dir / "output.pdf"
            pdf_service.create_pdf(response_data["blocks"], pdf_path)
            response_data["exports"]["pdf_path"] = f"/outputs/{request_id}/output.pdf"
        except Exception as e:
            print(f"PDF Generation failed: {e}")
            # We don't fail the whole request, just log it or add error to response
            response_data["errors"] = response_data.get("errors", []) + [f"PDF generation failed: {str(e)}"]

    return response_data




    return {"status": "ok"}
