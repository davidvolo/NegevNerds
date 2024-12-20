from Backend.BusinessLayer.PDFAnalyzer.Course_syllabus import Course_syllabus 
from Backend.BusinessLayer.PDFAnalyzer.InformationRetrival import * 




class PDFAnalyzerFacade:
    _instance = None  # Class-level attribute to hold the single instance

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        # Only initialize attributes if they don't already exist
        if not hasattr(self, 'course_syllabus'):
            self.course_syllabus = Course_syllabus()
        common_words_en = ["the", "is", "in", "and", "of"]  # Replace with actual common words
        common_words_he = ["של", "על", "זה", "עם", "את"]   # Replace with actual common words
        self.inforamtion_retrival =  WordIndex(common_words_en,common_words_he)


    def extract_syllabus_topic_total(self, pdf_path):
        syllabus = self.course_syllabus.extract_syllabus_topic_total(pdf_path)
        return syllabus
    
    def perform_information_retrival_question(self, pdf_question_path, question_dto):
        self.inforamtion_retrival.process_pdf(pdf_question_path,question_dto)


       