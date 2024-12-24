from tika import parser
from collections import defaultdict
import re

class WordIndex:
    def __init__(self, common_words_en, common_words_he):
        self.english_dict = defaultdict(list)  # English word dictionary
        self.hebrew_dict = defaultdict(list)   # Hebrew word dictionary
        self.common_words_en = set(common_words_en)  # Set of common English words
        self.common_words_he = set(common_words_he)  # Set of common Hebrew words

    def update_dictionary(self, words, question_data, dictionary, common_words):
        for word in words:
            if word not in common_words:
                if question_data not in dictionary[word]:
                    dictionary[word].append(question_data)

    def extract_words(self, text):
        if text is None:
            return [], []  # Return empty lists if no text
        english_words = re.findall(r'\b[a-zA-Z]+\b', text)  # Extract English words
        hebrew_words = re.findall(r'\b[א-ת]+\b', text)      # Extract Hebrew words
        return english_words, hebrew_words

    def process_pdf(self, pdf_file_path, question_data):
        # Parse the PDF
        parsed = parser.from_file(pdf_file_path)
        text = parsed.get('content', '')

        # Extract English and Hebrew words
        english_words, hebrew_words = self.extract_words(text)

        # Update English and Hebrew dictionaries
        self.update_dictionary(english_words, question_data, self.english_dict, self.common_words_en)
        self.update_dictionary(hebrew_words, question_data, self.hebrew_dict, self.common_words_he)

        # self.sorted_english_dict, self.sorted_hebrew_dict = self.get_sorted_dictionaries()
        self.english_dict = dict(sorted(self.english_dict.items(), key=lambda x: x[0].lower()))
        self.hebrew_dict = dict(sorted(self.hebrew_dict.items()))
        
    def get_sorted_dictionaries(self):
        # Return sorted versions of both dictionaries
        sorted_english_dict = dict(sorted(self.english_dict.items()))
        sorted_hebrew_dict = dict(sorted(self.hebrew_dict.items()))
        return sorted_english_dict, sorted_hebrew_dict

    def search_word(self, word, language="en"):
        # Search for a word in the specified dictionary
        if language == "en":
            return self.english_dict.get(word, [])
        elif language == "he":
            return self.hebrew_dict.get(word, [])
        else:
            raise ValueError("Invalid language. Use 'en' for English or 'he' for Hebrew.")