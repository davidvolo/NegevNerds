from Backend.BusinessLayer.PDFAnalyzer.Course_syllabus import Course_syllabus



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

        
    def extract_syllabus_topic_total(self, pdf_path):
        syllabus = self.course_syllabus.extract_syllabus_topic_total(pdf_path)
        return syllabus