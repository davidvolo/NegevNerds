from tika import parser
from collections import defaultdict
import re
import pdfplumber
from collections import defaultdict


class WordIndexController:
    def __init__(self, common_words_en, common_words_he):
        self.english_dict = defaultdict(list)  # English word dictionary
        self.hebrew_dict = defaultdict(list)   # Hebrew word dictionary
        self.common_words_en = set(common_words_en)  # Set of common English words
        self.common_words_he = set(common_words_he)  # Set of common Hebrew words
        self.wordIndex1 = WordIndex1(common_words_en, common_words_he)
        self.wordIndex2 = WordIndex2(common_words_en, common_words_he)

    def process_pdf(self, pdf_file_path, question_dto):
        # Process PDF using both WordIndex classes
        english_words1, hebrew_words1 = self.wordIndex1.process_pdf(pdf_file_path, question_dto)
        english_words2, hebrew_words2 = self.wordIndex2.process_pdf(pdf_file_path, question_dto)

        # Merge and update dictionaries
        self._update_main_dictionary(english_words1, english_words2, question_dto, self.english_dict, self.common_words_en, lower=True)
        self._update_main_dictionary(hebrew_words1, hebrew_words2, question_dto, self.hebrew_dict, self.common_words_he)

        sorted_english_dict, sorted_hebrew_dict = self.get_sorted_dictionaries()
        self.english_dict = sorted_english_dict
        self.hebrew_dict = sorted_hebrew_dict


    def _update_main_dictionary(self, words1, words2, question_dto, main_dict, common_words, lower=False):
        """
        Merges words from two sources and updates the main dictionary, avoiding duplicates.
        """
        all_words = set(words1 + words2)  # Combine and remove duplicates
        for word in all_words:
            normalized_word = word.lower() if lower else word  # Convert to lowercase if specified
            if normalized_word not in common_words and question_dto not in main_dict[normalized_word]:
                main_dict[normalized_word].append(question_dto)

    def get_sorted_dictionaries(self):
        # Return sorted versions of both dictionaries
        sorted_english_dict = dict(sorted(self.english_dict.items()))
        sorted_hebrew_dict = dict(sorted(self.hebrew_dict.items()))
        return sorted_english_dict, sorted_hebrew_dict



    


class WordIndex1:
    def __init__(self, common_words_en, common_words_he):
        self.english_dict = defaultdict(list)
        self.hebrew_dict = defaultdict(list)
        self.common_words_en = set(common_words_en)
        self.common_words_he = set(common_words_he)

    def extract_words(self, text):
        if text is None:
            return [], []

        # Regex for English words, including hyphenated ones
        english_words = re.findall(r'\b[a-zA-Z]+(?:-[a-zA-Z]+)?\b', text)

        # Regex for Hebrew words, including hyphenated ones
        hebrew_words = re.findall(r'\b[א-ת]+(?:-[א-ת]+)?\b', text)

        # Additionally, include components of hyphenated words
        split_english = []
        for word in english_words:
            if '-' in word:
                split_english.extend(word.split('-'))  # Add components of hyphenated words
            split_english.append(word)  # Keep the hyphenated word itself

        split_hebrew = []
        for word in hebrew_words:
            if '-' in word:
                split_hebrew.extend(word.split('-'))  # Add components of hyphenated words
            split_hebrew.append(word)  # Keep the hyphenated word itself

        return split_english, split_hebrew


    def process_pdf(self, pdf_file_path, question_data):
        # Parse the PDF
        parsed = parser.from_file(pdf_file_path)
        text = parsed.get('content', '')

        # Extract English and Hebrew words
        english_words, hebrew_words = self.extract_words(text)

        return english_words, hebrew_words
        
    def get_sorted_dictionaries(self):
        # Return sorted versions of both dictionaries
        sorted_english_dict = dict(sorted(self.english_dict.items()))
        sorted_hebrew_dict = dict(sorted(self.hebrew_dict.items()))
        return sorted_english_dict, sorted_hebrew_dict





class WordIndex2:
    def __init__(self, common_words_en, common_words_he):
        self.english_dict = defaultdict(list)
        self.hebrew_dict = defaultdict(list)
        self.common_words_en = set(common_words_en)
        self.common_words_he = set(common_words_he)

  
    def extract_words(self, text):
        if text is None:
            return [], []

        # Regex for English words, including hyphenated ones
        english_words = re.findall(r'\b[a-zA-Z]+(?:-[a-zA-Z]+)?\b', text)

        # Regex for Hebrew words, including hyphenated ones
        hebrew_words = re.findall(r'\b[א-ת]+(?:-[א-ת]+)?\b', text)

        # Additionally, include components of hyphenated words
        split_english = []
        for word in english_words:
            if '-' in word:
                split_english.extend(word.split('-'))
            split_english.append(word)

        split_hebrew = []
        for word in hebrew_words:
            if '-' in word:
                split_hebrew.extend(word.split('-'))
            split_hebrew.append(word)

        return split_english, split_hebrew

    def process_pdf(self, pdf_file_path, question_dto):
        try:
            with pdfplumber.open(pdf_file_path) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() + " "  # Combine text from all pages

            # Extract English and Hebrew words
            english_words, hebrew_words = self.extract_words(text)

            return english_words , hebrew_words
        except Exception as e:
            print(f"Error processing PDF: {e}")
