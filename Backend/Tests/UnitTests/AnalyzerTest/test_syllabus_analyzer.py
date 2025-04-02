import os
import re
import datetime
import unittest
from unittest.mock import patch, MagicMock

import pandas as pd
from PyPDF2 import PdfReader, PdfWriter
import pdfplumber
from tabula import read_pdf

from Backend.BusinessLayer.Analyzer.SyllabusAnalyzer import SyllabusAnalyzer

class TestSyllabusAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = SyllabusAnalyzer()
        self.fake_pdf_path = "dummy.pdf"
        self.fake_cropped_path = "dummy_cropped.pdf"  # our fake cropped output

    @patch.object(SyllabusAnalyzer, "crop_pdf_top_margin", return_value="dummy_cropped.pdf")
    @patch.object(SyllabusAnalyzer, "has_valid_table_with_pdfplumber", return_value=False)
    @patch.object(SyllabusAnalyzer, "extract_syllabus_topics_with_pdfplumber", return_value={"1. TopicA", "• TopicB", "TopicC"})
    @patch("os.path.exists", return_value=True)
    @patch("os.remove")
    def test_extract_syllabus_topic_total_no_table(self, mock_remove, mock_exists, mock_extract, mock_has_table, mock_crop):
        # When no valid table is found, it should extract topics via pdfplumber.
        topics = self.analyzer.extract_syllabus_topic_total(self.fake_pdf_path)
        # Cleaning: "1. TopicA" -> "TopicA", "• TopicB" -> "TopicB", "TopicC" stays.
        expected = {"TopicA", "TopicB", "TopicC"}
        self.assertEqual(topics, expected)
        mock_crop.assert_called_once_with(self.fake_pdf_path)
        mock_remove.assert_called_once_with("dummy_cropped.pdf")

    @patch("pdfplumber.open")
    def test_has_valid_table_with_pdfplumber_true(self, mock_pdfplumber_open):
        # Create a dummy page that returns at least one valid table.
        dummy_page = MagicMock()
        dummy_page.extract_tables.return_value = [
            [["Header1", "Header2"], ["Data1", "Data2"]]
        ]
        dummy_pdf = MagicMock()
        dummy_pdf.pages = [dummy_page]
        mock_pdfplumber_open.return_value.__enter__.return_value = dummy_pdf

        result = self.analyzer.has_valid_table_with_pdfplumber("dummy.pdf")
        self.assertTrue(result)

    @patch("pdfplumber.open")
    def test_has_valid_table_with_pdfplumber_false(self, mock_pdfplumber_open):
        # Simulate PDF with no tables.
        dummy_pdf = MagicMock()
        dummy_pdf.pages = []
        mock_pdfplumber_open.return_value.__enter__.return_value = dummy_pdf

        result = self.analyzer.has_valid_table_with_pdfplumber("dummy.pdf")
        self.assertFalse(result)

    @patch("pdfplumber.open")
    def test_extract_syllabus_topics_with_pdfplumber(self, mock_pdfplumber_open):
        # Simulate a PDF page that contains a syllabus line.
        dummy_page = MagicMock()
        # When the regex pattern is applied to the text below,
        # re.findall(r'סילבוס[:\n](.*?)\n', text, re.DOTALL) should return ["TopicA, TopicB"]
        dummy_page.extract_text.return_value = "סילבוס:\nTopicA, TopicB\n"
        dummy_pdf = MagicMock()
        dummy_pdf.pages = [dummy_page]
        mock_pdfplumber_open.return_value.__enter__.return_value = dummy_pdf

        result = self.analyzer.extract_syllabus_topics_with_pdfplumber("dummy.pdf", [r'סילבוס[:\n](.*?)\n'])
        # Expect that splitting "TopicA, TopicB" yields {"TopicA", "TopicB"}.
        self.assertEqual(result, {"TopicA", "TopicB"})

    @patch("tabula.read_pdf")
    def test_extract_table_with_topics_final(self, mock_read_pdf):
        # Simulate tabula.read_pdf returning a list of tables.
        # For simplicity, we create a dummy table as a list of lists.
        # Let's assume the table looks like:
        #   Row0: ["Header1", "Header2"]
        #   Row1: ["Value1", "Value2"]
        dummy_table = [["Header1", "Header2"], ["Value1", "Value2"]]
        mock_read_pdf.return_value = [dummy_table]
        topics = ["Header1"]
        result = self.analyzer.extract_table_with_topics_final("dummy.pdf", topics, pages="all")
        # The code assumes the first row is header and returns data under matching columns.
        # Here, "Header1" matches and its column has "Value1" as data.
        self.assertEqual(result, {"Value1"})

    @patch("os.remove")
    @patch("os.path.exists", return_value=True)
    @patch("PyPDF2.PdfWriter.write")
    @patch("PyPDF2.PdfWriter.add_page")
    @patch("PyPDF2.PdfReader")
    @patch("pdfplumber.open")
    def test_crop_pdf_top_margin(self, mock_pdfplumber_open, mock_pdfreader, mock_add_page, mock_writer_write, mock_exists, mock_remove):
        # Set up dummy pdfplumber open to yield a pdf with one page.
        dummy_page = MagicMock()
        dummy_page.width = 600
        dummy_page.height = 800
        dummy_pdf = MagicMock()
        dummy_pdf.pages = [dummy_page]
        mock_pdfplumber_open.return_value.__enter__.return_value = dummy_pdf

        # Simulate PdfReader returning a list of pages.
        dummy_reader = MagicMock()
        dummy_reader.pages = [MagicMock()]
        mock_pdfreader.return_value = dummy_reader

        output_path = self.analyzer.crop_pdf_top_margin("dummy.pdf", margin_cm=4.0)
        # Expected output: same directory as dummy.pdf with "_cropped.pdf" appended.
        expected_output = os.path.join(os.path.dirname("dummy.pdf"), os.path.basename("dummy.pdf").replace('.pdf', '_cropped.pdf'))
        self.assertEqual(output_path, expected_output)
        # Assert that os.remove was called to delete the temporary file.
        mock_remove.assert_called_once_with(expected_output)

if __name__ == "__main__":
    unittest.main()
