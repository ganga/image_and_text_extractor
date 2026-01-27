import httpx
import yaml
from openapi_spec_validator import validate_spec

BASE_URL = "http://api:8000"

#def test_openapi_yaml_endpoint_exists_and_is_valid_openapi():
#    r = httpx.get(f"{BASE_URL}/openapi.yaml", timeout=10)
#    assert r.status_code == 200
#    assert "openapi:" in r.text  # quick sanity check
#
#    spec = yaml.safe_load(r.text)
#    assert isinstance(spec, dict)
#    assert spec.get("openapi", "").startswith("3.")
#
#    # Validates structure of OpenAPI spec (not your business logic)
#    validate_spec(spec)
#
def test_openapi_has_required_paths():
    r = httpx.get(f"{BASE_URL}/openapi.yaml", timeout=10)
    spec = yaml.safe_load(r.text)

    paths = spec.get("paths", {})
    assert "/health" in paths
    assert "/extract" in paths

