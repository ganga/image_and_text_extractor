import unittest
from pathlib import Path
from app.services.pdf_service import PDFService
import os

class TestPDFService(unittest.TestCase):
    def test_create_pdf(self):
        service = PDFService()
        blocks = [
            {"type": "title", "text": "Test Document"},
            {"type": "text", "text": "This is a paragraph of text."},
            {"type": "table", "text": "Column A | Column B\nVal 1 | Val 2"},
            {"type": "figure", "text": "Figure 1"}
        ]
        
        output_path = Path("test_output.pdf")
        if output_path.exists():
            os.remove(output_path)
            
        try:
            result_path = service.create_pdf(blocks, output_path)
            self.assertTrue(result_path.exists())
            self.assertGreater(result_path.stat().st_size, 0)
            print(f"PDF generated at {result_path.absolute()}")
        finally:
            if output_path.exists():
                os.remove(output_path)

if __name__ == "__main__":
    unittest.main()
