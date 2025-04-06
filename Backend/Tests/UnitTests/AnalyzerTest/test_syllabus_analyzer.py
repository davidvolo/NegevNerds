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
        # כאשר לא נמצא טבלה תקפה, יש לחלץ נושאים באמצעות pdfplumber.
        topics = self.analyzer.extract_syllabus_topic_total(self.fake_pdf_path)
        # ניקוי: "1. TopicA" -> "TopicA", "• TopicB" -> "TopicB", "TopicC" נשאר.
        expected = {"TopicA", "TopicB", "TopicC"}
        self.assertEqual(topics, expected)
        mock_crop.assert_called_once_with(self.fake_pdf_path)
        mock_remove.assert_called_once_with("dummy_cropped.pdf")

    @patch("pdfplumber.open")
    def test_has_valid_table_with_pdfplumber_true(self, mock_pdfplumber_open):
        # יצירת עמוד מדומה שמחזיר לפחות טבלה אחת תקפה.
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
        # סימולציה של PDF ללא טבלאות.
        dummy_pdf = MagicMock()
        dummy_pdf.pages = []
        mock_pdfplumber_open.return_value.__enter__.return_value = dummy_pdf

        result = self.analyzer.has_valid_table_with_pdfplumber("dummy.pdf")
        self.assertFalse(result)

    def test_process_real_syllabus_file(self):
        # בדיקה עם קובץ סילבוס אמיתי
        syllabus_path = os.path.join(os.path.dirname(__file__), "sylabus.pdf")
        topics = self.analyzer.extract_syllabus_topic_total(syllabus_path)
        print("Extracted topics from real syllabus:", topics)
        self.assertIsInstance(topics, set)
        self.assertGreater(len(topics), 0)


if __name__ == "__main__":
    unittest.main()
