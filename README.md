# Image and Text Extractor

Backend service to extract text and structure from images (contract-first API).

## Running Locally (No Docker)

### Prerequisites

- **Python 3.10, 3.11, or 3.12** is required.
    - *Note: Python 3.13 is currently incompatible with required ML libraries (PaddleOCR dependencies).*
- `pip`

> [!IMPORTANT]
> **Apple Silicon (M1/M2/M3) Users:**
> - Docker build may fail or crash (`Illegal instruction`) due to `paddlepaddle` Linux ARM64 limitations.
> - **Recommended:** Run the application **locally** on your Mac using Python 3.10-3.12.

### Installation

1. Create a virtual environment (Python 3.11 recommended):
   ```bash
   python3.11 -m venv .venv
   source .venv/bin/activate
   ```


2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: For development/testing, also install dev requirements if available:*
   ```bash
   pip install -r requirements-dev.txt
   ```

### Running the Server

Start the FastAPI server using `uvicorn`:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`.
API Documentation (Swagger UI): `http://localhost:8000/docs`.

### Running Tests

Run unit tests using `unittest`:

```bash
python3 -m unittest discover tests
```

Or run specific tests:
```bash
python3 tests/test_pdf_service.py
```

## Running with Docker

### Run the Server

Build and start the services:

```bash
docker compose up -d --build
```

The API will be accessible at `http://localhost:8000`.

To view logs:
```bash
docker compose logs -f api
```

To stop the services:
```bash
docker compose down
```

### Run Tests in Docker

This runs the test suite inside a container:

```bash
docker compose run --rm tests
```

### Inspecting Outputs

Outputs (extracted images, PDFs) are stored in a docker volume `shared_outputs`. To inspect them:

```bash
docker compose exec api sh -lc "ls -la /shared_outputs"
```
