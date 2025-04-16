from Backend.BusinessLayer.Analyzer.SyllabusAnalyzer import SyllabusAnalyzer
from Backend.BusinessLayer.Analyzer.InformationRetrival import *
from Backend.BusinessLayer.Analyzer.QuestionAnalyzer import QuestionAnalyzer




class AnalyzerFacade:
    _instance = None  # Class-level attribute to hold the single instance

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        # Only initialize attributes if they don't already exist
        if not hasattr(self, 'course_syllabus'):
            self.course_syllabus = SyllabusAnalyzer()


        self.information_retrival =  InformationRetrival()
        self.question_analyser= QuestionAnalyzer()




    def extract_text_from_pdf_file(self, question_file):
        return self.question_analyser.extract_text_from_pdf_file(question_file)

    def extract_text_from_image(self, question_file):
        return self.question_analyser.extract_text_from_image(question_file)

    def extract_syllabus_topic_total(self, pdf_path):
        syllabus = self.course_syllabus.extract_syllabus_topic_total(pdf_path)
        return syllabus
    
    def perform_information_retrival_question_pdf(self, pdf_question_path, question_id, course_id):
        self.information_retrival.process_pdf(pdf_file_path=pdf_question_path , question_id=question_id, course_id=course_id)

    def perform_information_retrival_question_photo(self, text, question_id , course_id):

        self.information_retrival.process_photo(text=text, question_id=question_id, course_id=course_id)

    # def search_free_text(self , text):
    #     return self.information_retrival.search_free_text(text=text)

    def search_free_text_from_course(self , text, course_id):
        return self.information_retrival.search_free_text(query=text, course_id=course_id)

    def splitPDF(self, pdf_file, lines):
        return self.question_analyser.splitPDF(pdf_file=pdf_file, lines=lines)




