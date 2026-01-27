import base64
import re
import httpx

BASE_URL = "http://api:8000"

UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[1-5][0-9a-fA-F]{3}-"
    r"[89abAB][0-9a-fA-F]{3}-[0-9a-fA-F]{12}$"
)

def _tiny_png_bytes() -> bytes:
    # Valid 1x1 PNG
    return base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMB/6X9l0sAAAAASUVORK5CYII="
    )

def test_extract_rejects_non_image():
    files = {"file": ("note.txt", b"hello", "text/plain")}
    data = {"store_outputs": "true", "return_annotated": "true", "ocr_engine": "paddle"}

    r = httpx.post(f"{BASE_URL}/extract", files=files, data=data, timeout=20)

    # Contract expects 400 for non-image
    assert r.status_code == 400

def test_extract_happy_path_contract_minimum():
    img = _tiny_png_bytes()
    files = {"file": ("page.png", img, "image/png")}
    data = {"store_outputs": "false", "return_annotated": "true", "ocr_engine": "paddle"}

    r = httpx.post(f"{BASE_URL}/extract", files=files, data=data, timeout=30)

    # This will FAIL until you implement /extract (currently likely 404)
    assert r.status_code == 200

    body = r.json()

    # meta
    assert "meta" in body
    assert UUID_RE.match(body["meta"]["request_id"])

    # image meta must be >0
    assert body["meta"]["image"]["width"] >= 1
    assert body["meta"]["image"]["height"] >= 1

    # timings
    t = body["meta"]["timings_ms"]
    for k in ["preprocess", "layout", "ocr", "crop"]:
        assert isinstance(t[k], int)
        assert t[k] >= 0

    # shape fields always exist
    assert isinstance(body["blocks"], list)
    assert isinstance(body["figures"], list)
    assert "exports" in body

    # store_outputs=false => annotated must be null even if return_annotated=true
    assert body["exports"]["annotated_image_path"] is None

