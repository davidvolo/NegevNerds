import unittest
from unittest.mock import patch, MagicMock

from Backend.BusinessLayer.Analyzer.InformationRetrieval import InformationRetrieval, WordIndex1, WordIndex2


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
        reversed_line = original_line[::-1]  # "םולש"
        # For simplicity, assume reshape returns the same string and get_display returns the reversed string.
        with patch("arabic_reshaper.reshape", return_value=original_line), \
                patch("bidi.algorithm.get_display", return_value=reversed_line):
            normalized = self.index.normalize_mixed_text(original_line)
            # Since there's one line, it should equal the reversed text.
            self.assertEqual(normalized, reversed_line)


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


class TestInformationRetrieval(unittest.TestCase):
    def setUp(self):
        # We create an InformationRetrieval instance.
        self.ir = InformationRetrieval()
        # Patch the words_repository to be a MagicMock.
        self.ir.words_repository = MagicMock()
        # Also, set the wordIndex1 and wordIndex2 to dummy instances
        self.ir.wordIndex1 = MagicMock()
        self.ir.wordIndex2 = MagicMock()

    def test_process_pdf(self):
        self.ir.wordIndex1.process_pdf.return_value = ["word1", "word2"]
        self.ir.wordIndex2.process_pdf.return_value = ["word3"]

        with patch.object(self.ir.elastic_search.indices, "exists", return_value=True):
            with patch.object(self.ir.elastic_search, "index") as mock_index:
                with patch.object(self.ir, "update_words") as mock_update_words:
                    self.ir.process_pdf("dummy.pdf", "q1", "c1")

                    expected = set(["word1", "word2", "word3"])
                    mock_update_words.assert_called_once_with(words=expected, question_id="q1", course_id="c1")

                    mock_index.assert_called_once()
                    args, kwargs = mock_index.call_args
                    assert kwargs["index"] == "questions"
                    assert kwargs["id"] == "c1_q1"
                    assert kwargs["document"]["question_id"] == "q1"
                    assert kwargs["document"]["course_id"] == "c1"
                    assert set(kwargs["document"]["text"].split()) == expected

    def test_update_words(self):
        # Test update_words: For each word that is not in the common words,
        # words_repository.add_word_to_question should be called.
        self.ir.common_words_en = {"the", "and"}
        self.ir.common_words_he = {"וה", "של"}
        words = {"hello", "world", "the", "של"}
        self.ir.update_words(words, "q1", "c1")
        # Should call add_word_to_question for "hello" and "world" only.
        calls = [(("hello", "q1", "c1"),), (("world", "q1", "c1"),)]
        actual_calls = self.ir.words_repository.add_word_to_question.call_args_list
        # Convert each call to a tuple for comparison.
        expected_calls = [(("hello", "q1", "c1"),), (("world", "q1", "c1"),)]
        self.assertEqual(len(actual_calls), 2)
        for call in expected_calls:
            self.assertIn(call, actual_calls)

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
