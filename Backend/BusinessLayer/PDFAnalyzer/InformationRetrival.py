from tika import parser
from collections import defaultdict
import re
import pdfplumber
from collections import defaultdict
from Backend.DataLayer.WordsQuestions.WordsQuestionsRepository import WordsQuestionsRepository


class WordIndexController:
    def __init__(self, common_words_en, common_words_he):
        # self.english_dict = defaultdict(list)  # English word dictionary
        # self.hebrew_dict = defaultdict(list)   # Hebrew word dictionary
        self.common_words_en = set(common_words_en)  # Set of common English words
        self.common_words_he = set(common_words_he)  # Set of common Hebrew words
        self.words_repository = WordsQuestionsRepository()
        self.wordIndex1 = WordIndex1(common_words_en, common_words_he)
        self.wordIndex2 = WordIndex2(common_words_en, common_words_he)

    def process_pdf(self, pdf_file_path, question_data):
        # Process PDF using both WordIndex classes
        # english_words1, hebrew_words1 = self.wordIndex1.process_pdf(pdf_file_path, question_data)
        # english_words2, hebrew_words2 = self.wordIndex2.process_pdf(pdf_file_path, question_data)
        words1 = self.wordIndex1.process_pdf(pdf_file_path)
        words2 = self.wordIndex2.process_pdf(pdf_file_path)
        total_words = set([word for sublist in (words1 + words2) for word in sublist])

        self.update_words(words=total_words, question_data=question_data)

    def process_photo(self, text, question_data):
        # Process PDF using both WordIndex classes
        # english_words1, hebrew_words1 = self.wordIndex1.process_pdf(pdf_file_path, question_data)
        # english_words2, hebrew_words2 = self.wordIndex2.process_pdf(pdf_file_path, question_data)

        english_words = re.findall(r'\b[a-zA-Z]+(?:-[a-zA-Z]+)?\b', text)

        # Regex for Hebrew words, including hyphenated ones
        hebrew_words = re.findall(r'\b[א-ת]+(?:-[א-ת]+)?\b', text)

        split_english = []
        for word in english_words:
            if '-' in word:
                split_english.extend(word.split('-'))
            else:
                split_english.append(word)

        # Process Hebrew words
        split_hebrew = []
        for word in hebrew_words:
            if '-' in word:
                split_hebrew.extend(word.split('-'))
            else:
                split_hebrew.append(word)

        words = split_english + split_hebrew
        words_set = set(words)

        self.update_words(words=words_set, question_data=question_data)




        # Merge and update dictionaries
        #self._update_main_dictionary(english_words1, english_words2, question_data, self.english_dict, self.common_words_en, lower=True)
        #self._update_main_dictionary(hebrew_words1, hebrew_words2, question_data, self.hebrew_dict, self.common_words_he)

        #sorted_english_dict, sorted_hebrew_dict = self.get_sorted_dictionaries()
        #self.english_dict = sorted_english_dict
        #self.hebrew_dict = sorted_hebrew_dict


    # def _update_main_dictionary(self, words1, words2, question_data, main_dict, common_words, lower=False):
    #     """
    #     Merges words from two sources and updates the main dictionary, avoiding duplicates.
    #     """
    #     all_words = set(words1 + words2)  # Combine and remove duplicates
    #     for word in all_words:
    #         normalized_word = word.lower() if lower else word  # Convert to lowercase if specified
    #         if normalized_word not in common_words and question_data not in main_dict[normalized_word]:
    #             main_dict[normalized_word].append(question_data)


    def update_words(self, words, question_data):
        for word in words:
            word = word.lower()
            if len(word)>1:
                if word not in self.common_words_en and word not in self.common_words_he:
                    self.words_repository.add_word_to_question(word, question_data)


    # def get_sorted_dictionaries(self):
    #     # Return sorted versions of both dictionaries
    #     sorted_english_dict = dict(sorted(self.english_dict.items()))
    #     sorted_hebrew_dict = dict(sorted(self.hebrew_dict.items()))
    #     return sorted_english_dict, sorted_hebrew_dict



    


class WordIndex1:
    def __init__(self, common_words_en, common_words_he):
        self.english_dict = defaultdict(list)
        self.hebrew_dict = defaultdict(list)
        self.common_words_en = set(common_words_en)
        self.common_words_he = set(common_words_he)

    def extract_words(self, text):
        if text is None:
            return [],[]

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

        return split_english , split_hebrew


    def process_pdf(self, pdf_file_path):
        # Parse the PDF
        parsed = parser.from_file(pdf_file_path)
        text = parsed.get('content', '')

        # Extract English and Hebrew words
        english_words, hebrew_words = self.extract_words(text)

        return english_words + hebrew_words
        
    # def get_sorted_dictionaries(self):
    #     # Return sorted versions of both dictionaries
    #     sorted_english_dict = dict(sorted(self.english_dict.items()))
    #     sorted_hebrew_dict = dict(sorted(self.hebrew_dict.items()))
    #     return sorted_english_dict, sorted_hebrew_dict





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

    def process_pdf(self, pdf_file_path):
        try:
            with pdfplumber.open(pdf_file_path) as pdf:
                text = ""
                for page in pdf.pages:
                    text += page.extract_text() + " "  # Combine text from all pages

            # Extract English and Hebrew words
            english_words, hebrew_words = self.extract_words(text)

            return english_words + hebrew_words
        except Exception as e:
            print(f"Error processing PDF: {e}")

