import io
import unittest

from unittest.mock import MagicMock

from Backend.BusinessLayer.NegevNerds import NegevNerds
from Backend.BusinessLayer.Util.Exceptions import CourseIsNotExist, QuestionAlreadyInExam
from Backend.DataLayer.DTOs.QuestionDTO import QuestionDTO
from Backend.Tests.SystemTest.BaseTestCase import BaseTestCase


def _mock_pdf_file(filename="exam.pdf", content=b"%PDF-1.4"):
    file = MagicMock()
    file.filename = filename
    file.file = io.BytesIO(content)
    file.content_type = 'application/pdf'
    return file


def _mock_invalid_file(filename="exam.txt", content=b"invalid"):
    file = MagicMock()
    file.filename = filename
    file.file = io.BytesIO(content)
    file.content_type = 'text/plain'
    return file


class TestNegevNerdsExamAndQuestionManagement(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.user = self._complete_user_registration("examuser@bgu.ac.il", "Pass1!", "Exam", "Uploader")
        self.course_id = "777.1.1010"
        self.year = 2023
        self.semester = "A"
        self.moed = "A"
        self._open_course(self.user, self.course_id, "מבוא להעלאת מבחנים")

    # ---Tests for exams---
    def test_upload_exam_success(self):
        """Verify user can upload a valid exam file."""
        response = self.negev.upload_full_exam_pdf(self.course_id, self.year, self.semester, self.moed, self.exam_file)
        self.assertEqual(response["status"], "success")
        self.assertIn("File uploaded", response["message"])

    def test_upload_exam_invalid_format(self):
        """Verify uploading a file with an invalid format returns an error."""
        response = self.negev.upload_full_exam_pdf(self.course_id, self.year, self.semester, self.moed, self.invalid_file)
        self.assertEqual(response["status"], "error")
        self.assertIn("valid PDF", response["message"])

    def test_upload_exam_course_not_exist(self):
        """Verify uploading an exam for a non-existent course returns an error."""
        self.negev.courseFacade.check_exam_full_pdf = MagicMock(return_value=False)
        fake_course_id = "000.0.0000"
        response = self.negev.upload_full_exam_pdf(fake_course_id, self.year, self.semester, self.moed, self.exam_file)
        self.assertEqual(response["status"], "error")
        self.assertIn("not found", response["message"].lower())

    def test_upload_exam_already_exists(self):
        """Verify uploading an exam that already exists returns an error."""
        # Simulate exam already uploaded
        self.negev._course_facade.check_exam_full_pdf = MagicMock(return_value=True)
        response = self.negev.upload_full_exam_pdf(self.course_id, self.year, self.semester, self.moed, self.exam_file)
        self.assertEqual(response["status"], "error")
        self.assertIn("already exists", response["message"].lower())

    # ---Tests for Questions---
    def test_add_question_success(self):
        """Test Case 1: User can successfully post a valid exam question"""
        result = self.negev.add_question("101.1.1010", 2023, "A", "MoedA", 1, True, ["arrays"], self.mock_pdf_file(),
                                         self.mock_pdf_file())
        self.assertEqual(result, "Question added successfully.")

    def test_add_question_course_not_exist(self):
        """Test Case 2: Error if the course doesn’t exist"""
        self.negev.courseFacade.check_valid_question.side_effect = CourseIsNotExist("Course not found")
        with self.assertRaises(CourseIsNotExist):
            self.negev.add_question("000.0.0000", 2023, "A", "MoedA", 1, True, ["arrays"], self.mock_pdf_file(), None)

    def test_add_question_already_exists(self):
        """Test Case 3: Error if the question already exists"""
        self.negev.courseFacade.check_valid_question = MagicMock(
            side_effect=QuestionAlreadyInExam("Question already exists"))
        with self.assertRaises(QuestionAlreadyInExam):
            self.negev.add_question("101.1.1010", 2023, "A", "MoedA", 1, True, ["arrays"], self.mock_pdf_file(), None)

    def test_add_question_missing_required_parameter(self):
        """Test Case 4: Missing necessary parameter causes failure"""
        with self.assertRaises(Exception):
            self.negev.add_question(None, 2023, "A", "MoedA", 1, True, ["arrays"], self.mock_pdf_file(), None)

    def test_search_question_success(self):
        """Verify user can search and retrieve matching questions."""
        mock_dto = QuestionDTO("123", "שאלה על מבני נתונים", course_id=self.course_id)
        self.negev._pdfFacade.search_free_text = MagicMock(return_value=[{"question_id": "123"}])
        self.negev.courseFacade.get_questions_dto_by_search_dtos = MagicMock(return_value=[mock_dto])
        results = self.negev.search_free_text("מבני נתונים")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].question_text, "שאלה על מבני נתונים")

    def test_search_question_multiple_matches(self):
        """Verify multiple matching questions are returned."""
        mock_dtos = [
            QuestionDTO("q1", "שאלה על גרפים", course_id=self.course_id),
            QuestionDTO("q2", "שאלה על גרפים מכוונים", course_id=self.course_id),
        ]
        self.negev._pdfFacade.search_free_text = MagicMock(return_value=[{"question_id": "q1"}, {"question_id": "q2"}])
        self.negev.courseFacade.get_questions_dto_by_search_dtos = MagicMock(return_value=mock_dtos)
        results = self.negev.search_free_text("גרפים")
        self.assertEqual(len(results), 2)
        self.assertTrue(any("גרפים" in q.question_text for q in results))

    def test_search_partial_match(self):
        """Verify search returns questions that partially match the input text."""
        mock_dto = QuestionDTO("234", "אלגוריתם חיפוש בינארי", course_id=self.course_id)
        self.negev._pdfFacade.search_free_text = MagicMock(return_value=[{"question_id": "234"}])
        self.negev.courseFacade.get_questions_dto_by_search_dtos = MagicMock(return_value=[mock_dto])
        results = self.negev.search_free_text("חיפוש")
        self.assertGreaterEqual(len(results), 1)
        self.assertIn("חיפוש", results[0].question_text)

    def test_search_case_insensitive(self):
        """Verify search is case-insensitive."""
        mock_dto = QuestionDTO("777", "מערך דינאמי", course_id=self.course_id)
        self.negev._pdfFacade.search_free_text = MagicMock(return_value=[{"question_id": "777"}])
        self.negev.courseFacade.get_questions_dto_by_search_dtos = MagicMock(return_value=[mock_dto])
        results = self.negev.search_free_text("מַעֲרָך")
        self.assertEqual(len(results), 1)
        self.assertIn("מערך", results[0].question_text)

    def test_search_by_topic_success(self):
        """Test Case 1: Verify user can search and retrieve matching questions by topic"""
        question1_id = self._add_question_with_topic("מחרוזות")
        results = self.negev.search_by_topic(self.course_id, "מחרוזות")
        self.assertTrue(any(q.question_id == question1_id for q in results), "Expected question not found in results.")

    def test_search_by_topic_no_results(self):
        """Test Case 2: Verify error message is returned if no questions match the topic"""
        results = self.negev.search_by_topic(self.course_id, "גרפים")  # Topic not added
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 0, "Expected no results but found some questions.")

    def test_search_by_topic_multiple_matches(self):
        """Test Case 3: Verify multiple matching questions are returned for a common topic"""
        q1 = self._add_question_with_topic("מערכים")
        q2 = self._add_question_with_topic("מערכים")
        results = self.negev.search_by_topic(self.course_id, "מערכים")
        ids = [q.question_id for q in results]
        self.assertIn(q1, ids)
        self.assertIn(q2, ids)
        self.assertGreaterEqual(len(results), 2, "Expected multiple results for the topic.")

    def test_search_by_topic_partial_match(self):
        """Test Case 4: Verify search functionality with partial topic match"""
        full_topic = "חיפוש בינארי"
        partial_topic = "חיפוש"
        self._add_question_with_topic(full_topic)
        results = self.negev.search_by_topic(self.course_id, partial_topic)
        self.assertTrue(any(partial_topic in topic for q in results for topic in q.topics),
                        "Expected partial topic match not found.")

    def test_search_by_specifics_full_match(self):
        """Test Case 1: Search with all details returns specific question."""
        result = self.negev.search_question_by_specifics(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=1
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].question_number, 1)

    def test_search_by_specifics_no_match(self):
        """Test Case 2: No match returns empty list or error message."""
        result = self.negev.search_question_by_specifics(
            course_id=self.course_id,
            year=2030,
            semester="B",
            moed="B",
            question_number=99
        )
        self.assertEqual(result, [])

    def test_search_by_specifics_partial(self):
        """Test Case 3: Partial details (e.g., only course) returns multiple results."""
        result = self.negev.search_question_by_specifics(
            course_id=self.course_id
        )
        self.assertGreaterEqual(len(result), 2)

    # ---Tests for Discussions---