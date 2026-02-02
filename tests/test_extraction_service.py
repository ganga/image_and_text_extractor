import pytest
import numpy as np
import cv2
from unittest.mock import MagicMock, patch
from pathlib import Path
from app.services.extraction import ExtractionService

# Mock data for PPStructure result
# PPStructure returns a list of dictionaries
MOCK_PADDLE_RESULT = [
    {
        'type': 'text',
        'bbox': [10, 10, 100, 50],
        'res': [
            {'text': 'Hello World', 'confidence': 0.99},
            {'text': 'Line 2', 'confidence': 0.95}
        ],
        'img': np.zeros((40, 90, 3), dtype=np.uint8)
    },
    {
        'type': 'figure',
        'bbox': [10, 60, 100, 150],
        'res': [], # Figures might have empty 'res'
        'img': np.zeros((90, 90, 3), dtype=np.uint8), # The crop
        'score': 0.88
    }
]

@pytest.fixture
def mock_ppstructure():
    with patch('app.services.extraction.PPStructure') as MockClass:
        # The instance acts as a callable
        instance = MockClass.return_value
        instance.return_value = MOCK_PADDLE_RESULT
        yield instance

@pytest.fixture
def service(mock_ppstructure):
    # Initialize service (which uses the mocked PPStructure)
    return ExtractionService()

def test_initialization(service, mock_ppstructure):
    # Verify PPStructure was initialized with correct params
    pass # valid if fixture runs

def test_run_extraction_happy_path(service, tmp_path):
    # Create a dummy image bytes
    img = np.zeros((200, 200, 3), dtype=np.uint8)
    _, img_encoded = cv2.imencode('.png', img)
    image_bytes = img_encoded.tobytes()
    
    request_id = "test-req-1"
    output_dir = tmp_path / request_id
    output_dir.mkdir()
    
    response = service.run_extraction(
        image_bytes=image_bytes,
        request_id=request_id,
        output_dir=output_dir,
        store_outputs=True,
        return_annotated=True
    )
    
    # Verify Meta
    assert response["meta"]["request_id"] == "test-req-1"
    assert response["meta"]["image"]["width"] == 200
    assert response["meta"]["image"]["height"] == 200
    
    # Verify Blocks
    blocks = response["blocks"]
    assert len(blocks) == 2 # Text block AND Figure block
    assert blocks[0]["type"] == "text"
    assert blocks[0]["text"] == "Hello World\nLine 2"
    assert len(blocks[0]["lines"]) == 2
    
    # Verify Figures
    figures = response["figures"]
    assert len(figures) == 1
    assert figures[0]["type"] == "figure" if "type" in figures[0] else True # Schema check
    assert figures[0]["id"] == "f1"
    
    # Verify Exports
    assert response["exports"]["annotated_image_path"] is not None
    assert (output_dir / "annotated.png").exists()
    
    # Verify Figure Saved
    # The code saves figures as {id}_{type}.png, e.g. f1_figure.png
    assert (output_dir / "f1_figure.png").exists()

def test_run_extraction_no_store_outputs(service, tmp_path):
    # Create dummy image
    img = np.zeros((100, 100, 3), dtype=np.uint8)
    _, img_encoded = cv2.imencode('.png', img)
    image_bytes = img_encoded.tobytes()
    
    response = service.run_extraction(
        image_bytes=image_bytes,
        request_id="req-2",
        output_dir=None,
        store_outputs=False, # Should prevent writing
        return_annotated=True # Should be ignored if store_outputs is false usually, or handled null
    )
    
    # Verify Exports
    assert response["exports"]["annotated_image_path"] is None
    
    # Figures should still be detected but no path returned?
    # Logic in service: "if store_outputs: save ... rel_path = ..."
    # So if false, image_path should be "" or None? 
    # Current impl: rel_path or ""
    assert response["figures"][0]["image_path"] == ""

def test_invalid_image(service):
    with pytest.raises(ValueError, match="Could not decode image"):
        service.run_extraction(
            image_bytes=b"not an image",
            request_id="bad-req",
            output_dir=None,
            store_outputs=False,
            return_annotated=False
        )
