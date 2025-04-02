import io
import os
import re
import datetime
import unittest
from collections import defaultdict
from unittest.mock import patch, MagicMock

import pandas as pd

# Import the classes to test (adjust the paths as necessary)
from Backend.BusinessLayer.Analyzer.InformationRetrival import InformationRetrival, WordIndex1, WordIndex2

# For tests involving PDF, we patch pdfplumber and tabula.
import pdfplumber
from tabula import read_pdf

# We'll also patch arabic_reshaper and bidi.algorithm.get_display for normalization.
import arabic_reshaper
from bidi.algorithm import get_display


class TestWordIndex1(unittest.TestCase):
    def setUp(self):
        # Create a WordIndex1 instance with a small set of common words.
        common_en = {"the", "and"}
        common_he = {"וה", "של"}
        self.index = WordIndex1(common_en, common_he)

    def test_extract_words(self):
        # Test extraction with hyphenated words.
        text = "Hello world-this is a test שלום עולם-טסט"
        eng, heb = self.index.extract_words(text)
        # For english, expect both "world-this" and its split components.
        self.assertIn("world-this", eng)
        self.assertIn("world", eng)
        self.assertIn("this", eng)
        # For hebrew, similar behavior.
        self.assertIn("שלום", heb)
        self.assertIn("עולם-טסט", heb)
        self.assertIn("עולם", heb)
        self.assertIn("טסט", heb)

    @patch("pdfplumber.open")
    def test_process_pdf(self, mock_pdfplumber_open):
        # Create a dummy pdf with two pages.
        dummy_page1 = MagicMock()
        dummy_page1.extract_text.return_value = "Hello world"
        dummy_page2 = MagicMock()
        dummy_page2.extract_text.return_value = "שלום עולם"
        dummy_pdf = MagicMock()
        dummy_pdf.pages = [dummy_page1, dummy_page2]
        mock_pdfplumber_open.return_value.__enter__.return_value = dummy_pdf

        # Patch normalization to return the text as is.
        self.index.normalize_mixed_text = lambda t: t

        result = self.index.process_pdf("dummy.pdf")
        # Expect the union of english and hebrew words from both pages.
        # "Hello", "world", "שלום", "עולם" should be present.
        self.assertIn("Hello", result)
        self.assertIn("world", result)
        self.assertIn("שלום", result)
        self.assertIn("עולם", result)

    def test_normalize_mixed_text(self):
        # To test normalization, we patch arabic_reshaper and get_display.
        original_line = "שלום"
        # For simplicity, assume reshape and get_display return the same string.
        with patch("arabic_reshaper.reshape", return_value=original_line), \
             patch("bidi.algorithm.get_display", return_value=original_line):
            normalized = self.index.normalize_mixed_text(original_line)
            # Since there's one line, it should equal the original.
            self.assertEqual(normalized, original_line)


class TestWordIndex2(unittest.TestCase):
    def setUp(self):
        common_en = {"the", "and"}
        common_he = {"וה", "של"}
        self.index = WordIndex2(common_en, common_he)

    def test_extract_words(self):
        text = "Hello world-this is a test שלום עולם-טסט"
        eng, heb = self.index.extract_words(text)
        self.assertIn("world-this", eng)
        self.assertIn("world", eng)
        self.assertIn("this", eng)
        self.assertIn("שלום", heb)
        self.assertIn("עולם-טסט", heb)
        self.assertIn("עולם", heb)
        self.assertIn("טסט", heb)

    @patch("pdfplumber.open")
    def test_process_pdf(self, mock_pdfplumber_open):
        dummy_page = MagicMock()
        dummy_page.extract_text.return_value = "Hello\nשלום"
        dummy_pdf = MagicMock()
        dummy_pdf.pages = [dummy_page]
        mock_pdfplumber_open.return_value.__enter__.return_value = dummy_pdf

        # For WordIndex2, we'll patch normalize_text_direction to simply return the input.
        self.index.normalize_text_direction = lambda t: t

        result = self.index.process_pdf("dummy.pdf")
        # Expect both English and Hebrew words.
        self.assertIn("Hello", result)
        self.assertIn("שלום", result)

    def test_normalize_text_direction(self):
        # Test that a line containing Hebrew is processed by reverse_hebrew_words.
        sample_line = "Hello שלום"
        # In our implementation, if line contains Hebrew, we call reverse_hebrew_words.
        # We'll simulate that reverse_hebrew_words reverses the Hebrew words.
        # For example, "שלום" reversed becomes "םולש". Non-Hebrew ("Hello") remains.
        expected_line = "Hello םולש"
        # Patch contains_hebrew to return True if the word contains any Hebrew.
        self.index.contains_hebrew = lambda text: any('\u0590' <= ch <= '\u05FF' for ch in text)
        self.index.reverse_hebrew_words = lambda line: "Hello םולש"
        normalized = self.index.normalize_text_direction(sample_line)
        self.assertEqual(normalized, "Hello םולש")

    def test_contains_hebrew(self):
        self.assertTrue(self.index.contains_hebrew("שלום"))
        self.assertFalse(self.index.contains_hebrew("Hello"))

    def test_reverse_hebrew_words(self):
        line = "Hello שלום world"
        # For words that contain Hebrew, we reverse them.
        # "שלום" reversed becomes "םולש". Non-Hebrew remain unchanged.
        # We expect: "Hello םולש world"
        result = self.index.reverse_hebrew_words(line)
        self.assertEqual(result, "Hello םולש world")


class TestInformationRetrival(unittest.TestCase):
    def setUp(self):
        # We create an InformationRetrival instance.
        self.ir = InformationRetrival()
        # Patch the words_repository to be a MagicMock.
        self.ir.words_repository = MagicMock()
        # Also, set the wordIndex1 and wordIndex2 to dummy instances
        self.ir.wordIndex1 = MagicMock()
        self.ir.wordIndex2 = MagicMock()

    def test_process_pdf(self):
        # Simulate wordIndex1.process_pdf and wordIndex2.process_pdf returning lists.
        self.ir.wordIndex1.process_pdf.return_value = ["word1", "word2"]
        self.ir.wordIndex2.process_pdf.return_value = ["word3"]
        # Patch update_words so we can capture the call.
        with patch.object(self.ir, "update_words") as mock_update_words:
            self.ir.process_pdf("dummy.pdf", "q1", "c1")
            # The union of the lists is ["word1", "word2", "word3"].
            expected = set(["word1", "word2", "word3"])
            mock_update_words.assert_called_once_with(words=expected, question_id="q1", course_id="c1")

    def test_process_photo(self):
        # Test process_photo with text containing English and Hebrew words.
        text = "Hello world-test שלום-עולם"
        # Expected:
        # For English: "Hello", "world-test", and split "world", "test"
        # For Hebrew: "שלום-עולם" split into "שלום", "עולם" and also include the original.
        # So union is: {"hello", "world-test", "world", "test", "שלום-עולם", "שלום", "עולם"}
        # (All lowercased.)
        with patch.object(self.ir, "update_words") as mock_update_words:
            self.ir.process_photo(text, "q1", "c1")
            expected = {"hello", "world-test", "world", "test", "שלום-עולם", "שלום", "עולם"}
            mock_update_words.assert_called_once_with(words=expected, question_id="q1", course_id="c1")

    def test_update_words(self):
        # Test update_words: For each word that is not in the common words,
        # words_repository.add_word_to_question should be called.
        self.ir.common_words_en = {"the", "and"}
        self.ir.common_words_he = {"וה", "של"}
        words = {"hello", "world", "the", "של"}
        self.ir.update_words(words, "q1", "c1")
        # Should call add_word_to_question for "hello" and "world" only.
        calls = [ (("hello", "q1", "c1"),), (("world", "q1", "c1"),) ]
        actual_calls = self.ir.words_repository.add_word_to_question.call_args_list
        # Convert each call to a tuple for comparison.
        expected_calls = [ (("hello", "q1", "c1"),), (("world", "q1", "c1"),) ]
        self.assertEqual(len(actual_calls), 2)
        for call in expected_calls:
            self.assertIn(call, actual_calls)

    def test_search_free_text(self):
        # Prepare dummy SearchDTO objects.
        dummy_dto1 = MagicMock()
        dummy_dto1.course_id = "c1"
        dummy_dto1.question_id = "q1"
        dummy_dto2 = MagicMock()
        dummy_dto2.course_id = "c2"
        dummy_dto2.question_id = "q2"
        # For two words, simulate repository returning different dtos.
        self.ir.words_repository.get_search_dto_by_word.side_effect = lambda word: [dummy_dto1] if word=="hello" else [dummy_dto2]
        # Input text with two words.
        result = self.ir.search_free_text("hello world")
        # Expect that dummy_dto1 appears once and dummy_dto2 appears once.
        # Sorting is based on count (each count=1) then course_id, then question_id.
        # The sorted order is determined by the sorting key.
        # We'll simply check that result is a list containing dummy_dto1 and dummy_dto2 (order not strictly enforced here).
        self.assertEqual(set(result), {dummy_dto1, dummy_dto2})

    def test_search_free_text_with_course(self):
        # Simulate repository returning question IDs.
        self.ir.words_repository.get_questions_id_by_word_and_course.side_effect = lambda word, cid: [f"{word}_id"] if word=="hello" else []
        result = self.ir.search_free_text_with_course("hello world", "c1")
        # For "hello", we expect "hello_id" to be returned.
        self.assertEqual(result, ["hello_id"])

    def test_get_english_common_words(self):
        common = self.ir.get_english_common_words()
        self.assertTrue(isinstance(common, set))
        self.assertIn("i", common)

    def test_get_common_hebrew(self):
        common = self.ir.get_common_hebrew()
        self.assertTrue(isinstance(common, set))
        self.assertIn("אני", common)

if __name__ == "__main__":
    unittest.main()
