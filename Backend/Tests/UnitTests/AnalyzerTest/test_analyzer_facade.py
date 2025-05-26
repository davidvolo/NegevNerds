import io
import unittest
from unittest.mock import MagicMock

# Import the facade and its sub-components (adjust paths if needed)
from Backend.BusinessLayer.Analyzer.AnalyzerFacade import AnalyzerFacade
from Backend.BusinessLayer.Analyzer.SyllabusAnalyzer import SyllabusAnalyzer
from Backend.BusinessLayer.Analyzer.InformationRetrival import InformationRetrival
from Backend.BusinessLayer.Analyzer.QuestionAnalyzer import QuestionAnalyzer

class TestAnalyzerFacade(unittest.TestCase):
    def setUp(self):
        # Create a new instance of AnalyzerFacade
        self.facade = AnalyzerFacade()
        # Override its internal components with mocks.
        self.facade.course_syllabus = MagicMock(spec=SyllabusAnalyzer)
        self.facade.information_retrival = MagicMock(spec=InformationRetrival)
        self.facade.question_analyser = MagicMock(spec=QuestionAnalyzer)

    def test_extract_text_from_pdf_file(self):
        # Prepare a dummy file-like object.
        dummy_file = io.BytesIO(b"dummy pdf content")
        expected_text = "extracted text from pdf"
        # Set the return value for question_analyser.extract_text_from_pdf_file.
        self.facade.question_analyser.extract_text_from_pdf_file.return_value = expected_text

        result = self.facade.extract_text_from_pdf_file(dummy_file)
        self.facade.question_analyser.extract_text_from_pdf_file.assert_called_once_with(dummy_file)
        self.assertEqual(result, expected_text)

    def test_extract_text_from_image(self):
        dummy_file = io.BytesIO(b"dummy image content")
        expected_text = "extracted text from image"
        self.facade.question_analyser.extract_text_from_image.return_value = expected_text

        result = self.facade.extract_text_from_image(dummy_file)
        self.facade.question_analyser.extract_text_from_image.assert_called_once_with(dummy_file)
        self.assertEqual(result, expected_text)

    def test_extract_syllabus_topic_total(self):
        pdf_path = "dummy_syllabus.pdf"
        expected_topics = {"TopicA", "TopicB"}
        self.facade.course_syllabus.extract_syllabus_topic_total.return_value = expected_topics

        result = self.facade.extract_syllabus_topic_total(pdf_path)
        self.facade.course_syllabus.extract_syllabus_topic_total.assert_called_once_with(pdf_path)
        self.assertEqual(result, expected_topics)

    def test_perform_information_retrival_question_pdf(self):
        pdf_question_path = "dummy_question.pdf"
        question_id = "q1"
        course_id = "c1"
        # No return value expected.
        self.facade.information_retrival.process_pdf.return_value = None

        self.facade.perform_information_retrival_question_pdf(pdf_question_path, question_id, course_id)
        self.facade.information_retrival.process_pdf.assert_called_once_with(
            pdf_file_path=pdf_question_path, question_id=question_id, course_id=course_id
        )

    def test_perform_information_retrival_question_photo(self):
        text = "dummy photo text"
        question_id = "q1"
        course_id = "c1"
        self.facade.information_retrival.process_photo.return_value = None

        self.facade.perform_information_retrival_question_photo(text, question_id, course_id)
        self.facade.information_retrival.process_photo.assert_called_once_with(
            text=text, question_id=question_id, course_id=course_id
        )

    def test_search_free_text(self):
        text = "free text search"
        course_id = "123.4.5678"
        expected_result = ["result1", "result2"]

        # mock את השיטה הקיימת במידע הקיים (בדוק שם נכון)
        self.facade.information_retrival.search_free_text = MagicMock(return_value=expected_result)

        result = self.facade.search_free_text_from_course(text, course_id)

        self.facade.information_retrival.search_free_text.assert_called_once_with(
            query=text, course_id=course_id
        )
        self.assertEqual(result, expected_result)



if __name__ == "__main__":
    unittest.main()
