import fitz
from bidi.algorithm import get_display
import arabic_reshaper
import re
import pdfplumber
from collections import defaultdict

from dotenv import load_dotenv
import os

from Backend.DataLayer.DTOs.QuestionDTO import QuestionDTO
from Backend.DataLayer.DTOs.SearchDTO import SearchDTO
from Backend.DataLayer.WordsQuestions.WordsQuestionsRepository import WordsQuestionsRepository
from elasticsearch import Elasticsearch



# Load environment variables from .env file
load_dotenv()


class InformationRetrival:
    def __init__(self):
        elastic_url = os.getenv('ELASTICSEARCH_URL')
        elastic_username = os.getenv('ELASTICSEARCH_USER_NAME')
        elastic_password = os.getenv('ELASTICSEARCH_PASSWORD')
        self.elastic_search = Elasticsearch(
            elastic_url,
            basic_auth=(elastic_username, elastic_password),
            verify_certs=False
        )
        self.common_words_en = set(self.get_english_common_words())  # Set of common English words
        self.common_words_he = set(self.get_common_hebrew())  # Set of common Hebrew words
        self.words_repository = WordsQuestionsRepository()
        self.wordIndex1 = WordIndex1(self.common_words_en, self.common_words_he)
        self.wordIndex2 = WordIndex2(self.common_words_en, self.common_words_he)
        self.index_name = 'questions'

    def _ensure_index_exists(self):
        if not self.elastic_search.indices.exists(index=self.index_name):
            self.elastic_search.indices.create(index=self.index_name, body={
                "mappings": {
                    "properties": {
                        "text": {"type": "text"},
                        "question_id": {"type": "keyword"},
                        "course_id": {"type": "keyword"},
                    }
                }
            })

    def search_free_text(self, query: str, course_id: int = None, limit: int = 50) -> list:


        es_query = {
            "size": limit,
            "query": {
                "bool": {
                    "must": [  # מחפש התאמה מדויקת יחסית
                        {
                            "match_phrase": {  # חיפוש ביטוי מדויק
                                "text": query
                            }
                        }
                    ],
                    "filter": [{"term": {"course_id": str(course_id)}}] if course_id else []
                }
            },
            "suggest": {
                "text_suggestion": {
                    "text": query,
                    "term": {
                        "field": "text"
                    }
                }
            },
            "sort": [
                {"_score": {"order": "desc"}},
            ]
        }


        res = self.elastic_search.search(index=self.index_name, body=es_query)

        hits = res['hits']['hits']

        question_dtos = []
        for hit in hits:
            source = hit['_source']
            question_dto = SearchDTO(
                question_id=source['question_id'],
                course_id=source['course_id'],
            )
            question_dtos.append(question_dto)

        suggestions = res.get('suggest', {}).get('text_suggestion', [])
        first_suggestion = None
        for suggest in suggestions:
            if suggest.get('options'):
                first_suggestion = suggest['options'][0]['text']
                break
        return question_dtos, first_suggestion


    def index_question_to_elasticsearch(self, question_id, course_id, all_text):
        doc = {
            "question_id": str(question_id),
            "course_id": str(course_id),
            "text": all_text
        }
        self.elastic_search.index(index=self.index_name, id=f"{course_id}_{question_id}", document=doc)

    def process_pdf(self, pdf_file_path, question_id, course_id):

        self._ensure_index_exists()

        words1 = self.wordIndex1.process_pdf(pdf_file_path)
        print("words1", words1)
        words2 = self.wordIndex2.process_pdf(pdf_file_path)
        print("words2", words2)
        words = set(words1 + words2)
        print("words", words)
        all_text = " ".join(words)
        print("all_text", all_text)
        self.index_question_to_elasticsearch(question_id=question_id, course_id=course_id, all_text=all_text)

        self.update_words(words=words, question_id=question_id, course_id=course_id)


    def process_photo(self, text, question_id , course_id):

        self._ensure_index_exists()

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
        all_text = " ".join(words_set)
        self.index_question_to_elasticsearch(question_id=question_id, course_id=course_id, all_text=all_text)
        self.update_words(words=words_set, question_id=question_id, course_id=course_id)



    def update_words(self, words, question_id, course_id):
        for word in words:
            word = word.lower()
            if len(word)>1:
                if word not in self.common_words_en and word not in self.common_words_he:
                    self.words_repository.add_word_to_question(word, question_id, course_id)





    def get_english_common_words(self):
        return {'i', 'me', 'my', 'myself', 'we', 'our', 'ours',
                'ourselves', 'you', "you're", "you've", "you'll", "you'd", 'your', 'yours', 'yourself',
                'yourselves', 'he', 'him', 'his', 'himself', 'she', "she's", 'her', 'hers', 'herself',
                'it', "it's", 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves',
                'what', 'which', 'who', 'whom', 'this', 'that', "that'll", 'these', 'those', 'am', 'is', 'are',
                'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does', 'did',
                'doing',
                'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until', 'while', 'of', 'at', 'by',
                'for',
                'with', 'about', 'against', 'between', 'into', 'through', 'during', 'before', 'after', 'above',
                'below', 'to',
                'from', 'up', 'down', 'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then',
                'once',
                'here', 'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more',
                'most',
                'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very',
                's', 't', 'can', 'will', 'just', 'don', "don't", 'should', "should've", 'now', 'd', 'll', 'm',
                'o',
                're', 've', 'y',
                'ain', 'aren', "aren't", 'couldn', "couldn't", 'didn', "didn't", 'doesn', "doesn't",
                'hadn', "hadn't", 'hasn', "hasn't", 'haven', "haven't", 'isn', "isn't", 'ma', 'mightn',
                "mightn't", 'mustn', "mustn't", 'needn', "needn't", 'shan', "shan't", 'shouldn', "shouldn't",
                'wasn', "wasn't", 'weren', "weren't", 'won', "won't", 'wouldn', "wouldn't"}

    def get_common_hebrew(self):
        return {'אני', 'את', 'אתה', 'אנחנו', 'אתן', 'אתם', 'הם', 'הן', 'היא', 'הוא', 'שלי', 'שלו',
                'שלך', 'שלה', 'שלנו', 'שלכם', 'שלכן', 'שלהם', 'שלהן', 'לי', 'לו', 'לה', 'לנו',
                'לכם', 'לכן', 'להם', 'להן', 'אותה', 'אותו', 'זה', 'זאת', 'אלה', 'אלו', 'תחת',
                'מתחת', 'מעל', 'בין', 'עם', 'עד', 'נגר', 'על', 'אל', 'מול', 'של', 'אצל', 'כמו', 'אחר',
                'אותו', 'בלי', 'לפני', 'אחרי', 'מאחורי', 'עלי', 'עליו', 'עליה', 'עליך', 'עלינו', 'עליכם',
                'לעיכן', 'עליהם', 'עליהן', 'כל', 'כולם', 'כולן', 'כך', 'ככה', 'כזה', 'זה', 'זות', 'אותי',
                'אותה', 'אותם', 'אותך', 'אותו', 'אותן', 'אותנו', 'ואת', 'את', 'אתכם', 'אתכן', 'איתי', 'איתו',
                'איתך',
                'איתה', 'איתם', 'איתן', 'איתנו', 'איתכם', 'איתכן', 'יהיה', 'תהיה', 'היתי', 'היתה', 'היה',
                'להיות',
                'עצמי',
                'עצמו', 'עצמה', 'עצמם', 'עצמן', 'זו', 'עצמנו', 'עצמהם', 'עצמהן', 'מי', 'מה', 'איפה', 'היכן',
                'במקום שבו', 'אם',
                'לאן', 'למקום שבו', 'מקום בו', 'איזה', 'מהיכן', 'איך', 'כיצד', 'באיזו מידה', 'מתי', 'בשעה ש',
                'כאשר',
                'כש',
                'למרות', 'לפני', 'אחרי', 'מאיזו סיבה', 'הסיבה שבגללה', 'למה', 'מדוע', 'לאיזו תכלית', 'כי', 'יש',
                'אין', 'אך',
                'מנין', 'מאין', 'מאיפה', 'יכל', 'יכלה', 'יכלו', 'יכול', 'יכולה', 'יכולים', 'יכולות', 'יוכלו',
                'יוכל',
                'מסוגל',
                'לא', 'רק', 'אולי', 'אין', 'לאו', 'אי', 'כלל', 'נגד', 'אם', 'עם', 'אל', 'אלה', 'אלו', 'אף', 'על',
                'מעל', 'מתחת', 'מצד', 'בשביל',
                'לבין', 'באמצע', 'בתוך', 'דרך', 'מבעד', 'באמצעות', 'למעלה', 'למטה', 'מחוץ', 'מן', 'לעבר', 'מכאן',
                'כאן', 'הנה', 'הרי', 'פה', 'שם', 'אך', 'ברם', 'שוב', 'אבל', 'מבלי', 'בלי', 'מלבד', 'רק', 'בגלל',
                'מכיוון', 'עד', 'אשר',
                'ואילו', 'למרות', 'אס', 'כמו', 'כפי', 'אז', 'אחרי', 'כן', 'לכן', 'לפיכך', 'מאד', 'עז', 'מעט',
                'מעטים', 'במידה', 'שוב',
                'יותר', 'מדי', 'גם', 'כן', 'נו', 'להלן', 'לפי', 'אחר', 'אחרת', 'אחרים', 'אחרות', 'אשר', 'או'}




class WordIndex1:
    def __init__(self, common_words_en, common_words_he):
        self.hebrew_characters = re.compile(r'[\u0590-\u05FF]')
        self.hebrew_pattern = re.compile(r'[\u0590-\u05FF\uFB1D-\uFB4F]+')
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
        try:
            with pdfplumber.open(pdf_file_path) as pdf:
                text = ""

                for page in pdf.pages:
                    text += page.extract_text() + " "

            normalized_text = self.normalize_mixed_text(text)
            english_words, hebrew_words = self.extract_words(normalized_text)
            print("proc" , hebrew_words)
            return english_words + hebrew_words

        except Exception as e:
            print(f"Error processing PDF: {e}")
            return []

    def normalize_mixed_text(self, text):
        # Split into lines to preserve structure
        lines = text.split('\n')
        normalized_lines = []

        for line in lines:
            # Process each line separately
            reshaped_text = arabic_reshaper.reshape(line)
            bidi_text = get_display(reshaped_text)
            normalized_lines.append(bidi_text)

        return '\n'.join(normalized_lines)


class WordIndex2:
    def __init__(self, common_words_en, common_words_he):
        self.hebrew_characters = re.compile(r'[\u0590-\u05FF]')
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

        # Split hyphenated words into components as well
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
            doc = fitz.open(pdf_file_path)
            text = ""

            for page in doc:
                page_text = page.get_text()
                if page_text:
                    text += page_text + " "

            #normalized_text = self.normalize_text_direction(text)

            # Extract English and Hebrew words
            english_words, hebrew_words = self.extract_words(text)

            print("Extracted Hebrew words:", hebrew_words)
            return english_words + hebrew_words

        except Exception as e:
            print(f"Error processing PDF: {e}")
            return []



    def contains_hebrew(self, text):
        return bool(self.hebrew_characters.search(text))

    def reverse_hebrew_words(self, line):
        words = line.split()
        reversed_words = []
        for word in words:
            if self.contains_hebrew(word):
                reversed_words.append(word[::-1])
            else:
                reversed_words.append(word)
        return " ".join(reversed_words)



    # def search_free_text(self, text: str) -> list:
    #     """
    #     Search for the 50 best matching question IDs based on the number of words in common with the text.
    #
    #     :param text: The input free-text string.
    #     :return: A list of up to 50 question IDs with the most words in common with the text.
    #     """
    #     from collections import defaultdict
    #
    #     # Step 1: Split the input text into words
    #     words = text.split()  # You may want to preprocess (e.g., lowercase, remove punctuation) as needed.
    #
    #     # Step 2: Dictionary to count the number of matching words for each question ID
    #     dto_count = defaultdict(int)
    #
    #     # Step 3: Iterate over words and fetch associated question IDs
    #     for word in words:
    #         word = word.lower()
    #         search_dtos = self.words_repository.get_search_dto_by_word(word)
    #         for dto in search_dtos:
    #             dto_count[dto] += 1
    #
    #         # Step 4: Sort SearchDTOs by frequency (descending), with a secondary sort by course ID and question ID
    #     sorted_dtos = sorted(
    #         dto_count.items(),
    #         key=lambda item: (-item[1], item[0].course_id, item[0].question_id)
    #         # Primary sort by count, then course/question IDs
    #     )
    #
    #     # Step 5: Extract the top 50 SearchDTOs
    #     top_50_dtos = [dto for dto, _ in sorted_dtos[:50]]
    #
    #     return top_50_dtos


    # def search_free_text_with_course(self, text, course_id) -> list:
    #     """
    #     Search for the 50 best matching question IDs based on the number of words in common with the text.
    #
    #     :param text: The input free-text string.
    #     :return: A list of up to 50 question IDs with the most words in common with the text.
    #     """
    #     from collections import defaultdict
    #
    #     # Step 1: Split the input text into words
    #     words = text.split()  # You may want to preprocess (e.g., lowercase, remove punctuation) as needed.
    #
    #     # Step 2: Dictionary to count the number of matching words for each question ID
    #     question_word_count = defaultdict(int)
    #
    #     # Step 3: Iterate over words and fetch associated question IDs
    #     for word in words:
    #         word = word.lower()
    #         question_ids = self.words_repository.get_questions_id_by_word_and_course(word, course_id)
    #         for question_id in question_ids:
    #             question_word_count[question_id] += 1
    #
    #     # Step 4: Sort question IDs by the number of matching words (descending)
    #     # If counts are equal, secondary sorting by question ID (optional)
    #     sorted_questions = sorted(
    #         question_word_count.items(),
    #         key=lambda item: (-item[1], item[0])  # Sort by count descending, then by ID ascending
    #     )
    #
    #     # Step 5: Extract the top 50 question IDs
    #     top_50_questions = [question_id for question_id, _ in sorted_questions[:50]]
    #
    #     return top_50_questions

