import io
import unittest
from unittest.mock import patch, MagicMock

from Backend.BusinessLayer.Analyzer.QuestionAnalyzer import QuestionAnalyzer


class TestQuestionAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = QuestionAnalyzer()
        self.dummy_pdf_bytes = b"%PDF-1.4 dummy pdf content"
        self.dummy_image_bytes = b"dummy image content"

    @patch("fitz.open")
    def test_extract_text_from_pdf_file_success(self, mock_fitz_open):
        # Create a dummy file-like object.
        file_obj = io.BytesIO(self.dummy_pdf_bytes)

        # Set up a dummy document with two pages.
        dummy_page1 = MagicMock()
        dummy_page1.get_text.return_value = "Page 1 text\n"
        dummy_page2 = MagicMock()
        dummy_page2.get_text.return_value = "Page 2 text\n"
        dummy_document = MagicMock()
        dummy_document.__iter__.return_value = [dummy_page1, dummy_page2]
        mock_fitz_open.return_value = dummy_document

        result = self.analyzer.extract_text_from_pdf_file(file_obj)

        # Verify the concatenated text.
        self.assertEqual(result, "Page 1 text\nPage 2 text\n")
        dummy_document.close.assert_called_once()

    @patch("fitz.open", side_effect=Exception("pdf error"))
    def test_extract_text_from_pdf_file_error(self, mock_fitz_open):
        file_obj = io.BytesIO(self.dummy_pdf_bytes)
        result = self.analyzer.extract_text_from_pdf_file(file_obj)
        self.assertIn("An error occurred: pdf error", result)

    @patch("pytesseract.image_to_string")
    @patch("PIL.Image.open")
    def test_extract_text_from_image_success(self, mock_image_open, mock_image_to_string):
        # Create a dummy image file-like object.
        dummy_image_file = io.BytesIO(self.dummy_image_bytes)
        dummy_image = MagicMock()
        mock_image_open.return_value = dummy_image
        mock_image_to_string.return_value = "Extracted text"

        result = self.analyzer.extract_text_from_image(dummy_image_file)
        self.assertEqual(result, "Extracted text")
        mock_image_open.assert_called_once_with(dummy_image_file)
        mock_image_to_string.assert_called_once_with(dummy_image, lang="heb+eng")

    @patch("PIL.Image.open", side_effect=Exception("image error"))
    def test_extract_text_from_image_error(self, mock_image_open):
        dummy_image_file = io.BytesIO(self.dummy_image_bytes)
        result = self.analyzer.extract_text_from_image(dummy_image_file)
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
