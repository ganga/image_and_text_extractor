import httpx

BASE_URL = "http://api:8000"

def test_health_ok():
    r = httpx.get(f"{BASE_URL}/health", timeout=10)
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}

