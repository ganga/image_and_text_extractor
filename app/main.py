from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

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

