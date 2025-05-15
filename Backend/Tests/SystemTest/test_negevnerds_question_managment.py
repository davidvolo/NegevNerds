import io
import json
from unittest.mock import patch, MagicMock
from werkzeug.datastructures import FileStorage

from Backend.DataLayer.ReactionData.ReactionRepository import ReactionRepository
from Backend.BusinessLayer.Util.Exceptions import CourseIsNotExist, QuestionAlreadyInExam, CommentNotFound, \
    ExamIsNotExist, ReactionNotFound, QuestionNotFound
from Backend.DataLayer.DTOs.QuestionDTO import QuestionDTO
from Backend.Tests.SystemTest.BaseTestCase import BaseTestCase


def _mock_invalid_file(filename="exam.txt", content=b"invalid"):
    file = MagicMock()
    file.filename = filename
    file.file = io.BytesIO(content)
    file.content_type = 'text/plain'
    return file


class TestNegevNerdsQuestionManagement(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.user = self._complete_user_registration("examuser@bgu.ac.il", "Pass1!", "Exam", "Uploader")
        self.course_id = "777.1.1010"
        self.year = 2023
        self.semester = "אביב"
        self.moed = "א"
        self.exam_file = self._mock_pdf_file()
        self.invalid_file = _mock_invalid_file()
        self._open_course(self.user, self.course_id, "מבוא להעלאת מבחנים")
        self.question_number = 165

    def tearDown(self):
        super().tearDown()

        if isinstance(self.negev.courseFacade.check_valid_question, MagicMock):
            del self.negev.courseFacade.check_valid_question

        if isinstance(self.negev.courseFacade.check_exam_full_pdf, MagicMock):
            del self.negev.courseFacade.check_exam_full_pdf

    # ---Tests for exams---
    def test_get_exam_full_pdf_exam_not_found(self):
        """Verify getting exam PDF fails when exam does not exist for the course."""
        # Open a course but do NOT add questions or upload exam
        new_course_id = "888.8.8888"
        self._open_course(self.user, new_course_id, "קורס טסט ללא מבחן")

        result = self.negev.get_exam_full_pdf(new_course_id, self.year, self.semester, self.moed)
        self.assertIsInstance(result, str)
        self.assertIn("CourseFacade Error", result)
        self.assertIn("not exist", result.lower())

    # ---Tests for Questions---
    @patch('Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf', return_value=None)
    def test_add_question_success_pdf_only(self, mock_process_pdf):
        """Test: Add a question successfully with only a PDF file (no answer)."""

        new_course_id = "999.9.9999"
        self._open_course(self.user, new_course_id, "קורס טסט לשאלות")

        result = self.negev.add_question(
            course_id=new_course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=1,
            is_american=True,
            question_topics=["מיון"],
            question_file=self.exam_file,
            answer_file=None
        )

        self.assertEqual(result, "Question added successfully.")

    @patch('Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf', return_value=None)
    def test_add_question_with_solution_success(self, mock_process_pdf):
        """Successfully add a question with a solution file."""

        result = self.negev.add_question(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=11,
            is_american=False,
            question_topics=["מבני נתונים"],
            question_file=self.exam_file,
            answer_file=self.exam_file  # קובץ פתרון
        )

        self.assertEqual(result, "Question added successfully.")

    @patch('Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf', return_value=None)
    def test_add_question_course_not_exist(self, mock_process_pdf):
        """Test: Fail to add question when the course does not exist."""
        fake_course_id = "000.0.0000"

        with self.assertRaises(Exception) as context:
            self.negev.add_question(
                course_id=fake_course_id,
                year=self.year,
                semester=self.semester,
                moed=self.moed,
                question_number=14,
                is_american=True,
                question_topics=["מבני נתונים"],
                question_file=self.exam_file,
                answer_file=None
            )
        self.assertIn("Failed to add question", str(context.exception))

    @patch('Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf', return_value=None)
    def test_add_question_already_exists(self, mock_process_pdf):
        """Try to add a duplicate question and expect an error."""

        self.negev.add_question(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=12,
            is_american=True,
            question_topics=["מבני נתונים"],
            question_file=self.exam_file,
            answer_file=None
        )

        with self.assertRaises(QuestionAlreadyInExam):
            self.negev.add_question(
                course_id=self.course_id,
                year=self.year,
                semester=self.semester,
                moed=self.moed,
                question_number=12,  # אותו מספר שאלה
                is_american=True,
                question_topics=["מבני נתונים"],
                question_file=self.exam_file,
                answer_file=None
            )

    def test_add_question_missing_required_parameter(self):
        """Test Case 4: Missing necessary parameter causes failure"""
        with self.assertRaises(Exception):
            self.negev.add_question(None, 2023, "A", "MoedA", 1, True, ["arrays"], self.mock_pdf_file(), None)

    @patch('Backend.BusinessLayer.Analyzer.AnalyzerFacade.AnalyzerFacade.search_free_text_from_course')
    @patch('Backend.BusinessLayer.Analyzer.AnalyzerFacade.AnalyzerFacade.perform_information_retrival_question_pdf',
           return_value=None)
    def test_search_free_text_system_basic_no_course_id(self, mock_retrival_pdf, mock_search_free_text):
        """System Test: User searches for a term without specifying course_id – expects relevant results."""

        question_number = 1001
        topic = "גרפים"

        self.negev.add_question(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=question_number,
            is_american=True,
            question_topics=[topic],
            question_file=self.exam_file,
            answer_file=None
        )

        # mock elastic search result
        mock_dtos = [{"question_id": str(question_number)}]
        mock_search_free_text.return_value = (mock_dtos, None)

        mock_question_dto = QuestionDTO(
            question_id=str(question_number),
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=question_number,
            question_topics=["גרפים"],
            is_american=True,
            link_to_question="some_link.pdf",  # או קובץ אמיתי אם יש
            comments_list=[],
            course_id=self.course_id
        )

        self.negev.courseFacade.get_questions_dto_by_search_dtos = MagicMock(return_value=[mock_question_dto])

        search_text = "BFS"
        results, suggestion = self.negev.search_free_text(text=search_text)

        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].question_id, str(question_number))
        self.assertIsNone(suggestion)

    @patch('Backend.BusinessLayer.Analyzer.AnalyzerFacade.AnalyzerFacade.search_free_text_from_course')
    @patch('Backend.BusinessLayer.Analyzer.AnalyzerFacade.AnalyzerFacade.perform_information_retrival_question_pdf',
           return_value=None)
    def test_search_free_text_system_with_course_id(self, mock_retrival_pdf, mock_search_free_text):
        """System Test: User searches for a term with a specific course_id – expects filtered results."""

        # שלב 1: הוספת שאלה בקורס הקיים
        question_number = 1002
        topic = "אוטומטים"

        self.negev.add_question(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=question_number,
            is_american=False,
            question_topics=[topic],
            question_file=self.exam_file,
            answer_file=None
        )

        # שלב 2: החזרת תוצאה מדומה שמכילה את השאלה הנכונה
        mock_dtos = [{"question_id": str(question_number)}]
        mock_search_free_text.return_value = (mock_dtos, None)

        mock_question_dto = QuestionDTO(
            question_id=str(question_number),
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=question_number,
            question_topics=[topic],
            is_american=False,
            link_to_question="link_to_q.pdf",
            comments_list=[],
            course_id=self.course_id
        )
        self.negev.courseFacade.get_questions_dto_by_search_dtos = MagicMock(return_value=[mock_question_dto])

        # שלב 3: הפעלת החיפוש עם course_id
        search_text = "DFA"
        results, suggestion = self.negev.search_free_text(text=search_text, course_id=self.course_id)

        # שלב 4: אימותים
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].course_id, self.course_id)
        self.assertIsNone(suggestion)

    @patch('Backend.BusinessLayer.Analyzer.AnalyzerFacade.AnalyzerFacade.search_free_text_from_course')
    @patch('Backend.BusinessLayer.Analyzer.AnalyzerFacade.AnalyzerFacade.perform_information_retrival_question_pdf',
           return_value=None)
    def test_search_free_text_system_no_results(self, mock_retrival_pdf, mock_search_free_text):
        """System Test: User searches for a term that has no matching results – expects empty list."""

        # אין צורך להוסיף שאלה – המנוע מחזיר תוצאה ריקה
        mock_search_free_text.return_value = ([], None)

        search_text = "מושגשלאקיים"
        results, suggestion = self.negev.search_free_text(text=search_text)

        # בדיקות
        self.assertIsInstance(results, list)
        self.assertIsNone(suggestion, "Expected no suggestion when nothing matches.")

    @patch('Backend.BusinessLayer.Analyzer.AnalyzerFacade.AnalyzerFacade.search_free_text_from_course')
    @patch('Backend.BusinessLayer.Analyzer.AnalyzerFacade.AnalyzerFacade.perform_information_retrival_question_pdf',
           return_value=None)
    def test_search_free_text_system_with_typo_suggestion(self, mock_retrival_pdf, mock_search_free_text):
        """System Test: Search with typo returns suggestion even if results are empty."""

        mock_search_free_text.return_value = ([], "גרף")

        search_text = "גראף"
        results, suggestion = self.negev.search_free_text(text=search_text)

        self.assertIsInstance(results, list)
        self.assertEqual(suggestion, "גרף", "Expected suggestion to correct the typo.")

    @patch('Backend.BusinessLayer.Analyzer.AnalyzerFacade.AnalyzerFacade.search_free_text_from_course')
    @patch('Backend.BusinessLayer.Analyzer.AnalyzerFacade.AnalyzerFacade.perform_information_retrival_question_pdf',
           return_value=None)
    def test_search_free_text_system_case_insensitive(self, mock_retrival_pdf, mock_search_free_text):
        """System Test: Search is case-insensitive (e.g., 'dfa' should match 'DFA')."""

        question_number = 1003
        topic = "אוטומטים"

        self.negev.add_question(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=question_number,
            is_american=False,
            question_topics=[topic],
            question_file=self.exam_file,
            answer_file=None
        )

        mock_dtos = [{"question_id": str(question_number)}]
        mock_search_free_text.return_value = (mock_dtos, None)

        mock_question_dto = QuestionDTO(
            question_id=str(question_number),
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=question_number,
            question_topics=[topic],
            is_american=False,
            link_to_question="q_link.pdf",
            comments_list=[],
            course_id=self.course_id
        )
        self.negev.courseFacade.get_questions_dto_by_search_dtos = MagicMock(return_value=[mock_question_dto])

        search_text = "dfa"
        results, suggestion = self.negev.search_free_text(text=search_text)

        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].question_id, str(question_number))
        self.assertIsNone(suggestion)

    @patch('Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf', return_value=None)
    def test_search_by_topic_success(self, mock_process_pdf):
        """Test: Search by existing topic returns questions."""
        # שלב 1: מוסיפים שאלה עם נושא
        topic = "מבני נתונים"
        self.negev.add_question(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=200,
            is_american=True,
            question_topics=[topic],
            question_file=self.exam_file,
            answer_file=None
        )

        # שלב 2: חיפוש לפי נושא
        results = self.negev.search_by_topic(self.course_id, topic)

        # שלב 3: וידוא תוצאה
        self.assertIsInstance(results, list)
        self.assertGreaterEqual(len(results), 1, "Expected at least one question with the topic.")

    @patch('Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf', return_value=None)
    def test_search_by_topic_no_results(self, mock_process_pdf):
        """Test: Search by non-existing topic returns empty list."""
        results = self.negev.search_by_topic(self.course_id, "נושא שלא קיים בכלל")
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 0, "Expected no questions with non-existing topic.")

    @patch('Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf', return_value=None)
    def test_search_by_topic_course_not_exist(self, mock_process_pdf):
        """Test: Course does not exist raises Exception."""
        with self.assertRaises(Exception) as context:
            self.negev.search_by_topic("000.0.0000", "מבני נתונים")

        self.assertIn("Error while searching by topic", str(context.exception))

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

    @patch('Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf', return_value=None)
    def test_check_exist_solution_exists(self, mock_process_pdf):
        """Test: Solution exists for a question."""
        self.negev.add_question(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=16,  # מספר חדש
            is_american=True,
            question_topics=["מבני נתונים"],
            question_file=self.exam_file,
            answer_file=self.exam_file  # יש קובץ פתרון
        )

        result = self.negev.checkExistSolution(self.course_id, self.year, self.semester, self.moed, 16)

        self.assertTrue(result, "Expected solution to exist for the question.")

    def test_check_exist_solution_course_not_found(self):
        """Test: Course does not exist, should return an error string."""
        fake_course_id = "999.9.9999"
        result = self.negev.checkExistSolution(fake_course_id, self.year, self.semester, self.moed, 1)

        self.assertFalse(result, "suppose to be false")

    @patch('Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf', return_value=None)
    def test_upload_solution_success(self, mock_process_pdf):
        self.negev.add_question(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=20,
            is_american=True,
            question_topics=["מבני נתונים"],
            question_file=self.exam_file,
            answer_file=None
        )

        response = self.negev.uploadSolution(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=20,
            solution_file=self.exam_file
        )

        self.assertEqual(response["status"], "success")
        self.assertIn("uploaded", response["message"].lower())
        self.assertTrue(response["link"].endswith(".pdf"))

    @patch('Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf', return_value=None)
    @patch('Backend.BusinessLayer.Analyzer.AnalyzerFacade.AnalyzerFacade.perform_information_retrival_question_pdf',
           return_value=None)
    def test_upload_solution_already_exists(self, mock_perform_retrival, mock_process_pdf):
        """Verify error is raised when uploading solution that already exists."""
        self.negev.add_question(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=21,
            is_american=True,
            question_topics=["מבני נתונים"],
            question_file=self.exam_file,
            answer_file=self.exam_file  # זה יוצר פתרון שכבר קיים
        )

        # Step 2: Try uploading the same solution again
        response = self.negev.uploadSolution(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=21,
            solution_file=self.exam_file
        )

        # Step 3: Check that the upload fails as expected
        self.assertEqual(response["status"], "error")
        self.assertIn("already", response["message"].lower())

    def test_upload_solution_missing_file(self):
        """Verify uploading with no file returns error."""
        response = self.negev.uploadSolution(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=22,
            solution_file=None
        )

        self.assertEqual(response["status"], "error")
        self.assertIn("NoneType", response["message"])

    @patch('Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf', return_value=None)
    def test_delete_question_success(self, mock_process_pdf):
        """Test: Successfully delete an existing question."""
        self.negev.add_question(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=100,
            is_american=True,
            question_topics=["טסטים"],
            question_file=self.exam_file,
            answer_file=None
        )

        # וידוא שהשאלה קיימת לפני מחיקה
        questions_before = self.negev.courseFacade.get_questions_dto_by_search_dtos([
            {"course_id": self.course_id, "year": self.year, "semester": self.semester, "moed": self.moed,
             "question_number": 100}
        ])
        self.assertEqual(len(questions_before), 1, "Question should exist before deletion.")

        try:
            self.negev.delete_question(
                course_id=self.course_id,
                year=self.year,
                semester=self.semester,
                moed=self.moed,
                question_number=100
            )
        except Exception as e:
            self.fail(f"delete_question raised an exception unexpectedly: {e}")

        # חיפוש ישירות מהקורס אחרי מחיקה
        questions_after = self.negev.courseFacade.get_questions_dto_by_search_dtos([
            {"course_id": self.course_id, "year": self.year, "semester": self.semester, "moed": self.moed,
             "question_number": 100}
        ])
        self.assertEqual(
            len(questions_after), 0,
            "Expected the question to be deleted from database."
        )

        questions_after = self.negev.search_question_by_specifics(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=100
        )

        self.assertEqual(
            len(questions_after), 0,
            "Expected the question to be deleted from database."
        )

    def test_delete_nonexistent_question(self):
        """Test: Trying to delete a question that does not exist should raise an error."""
        with self.assertRaises(Exception) as context:
            self.negev.delete_question(
                course_id=self.course_id,
                year=self.year,
                semester=self.semester,
                moed=self.moed,
                question_number=85  # מספר שלא קיים
            )
        self.assertIn("Error", str(context.exception))

    def test_get_question_path_success(self):
        """Test: Successfully retrieve question path."""
        path = self.negev.get_question_path(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=1
        )
        self.assertIsInstance(path, str)
        self.assertTrue(path.endswith(".pdf") or path.endswith(".jpg") or path.endswith(".png"))

    def test_get_question_path_course_not_found(self):
        """Test: Course not found raises CourseIsNotExist."""
        with self.assertRaises(CourseIsNotExist):
            self.negev.get_question_path(
                course_id="000.0.0000",
                year=self.year,
                semester=self.semester,
                moed=self.moed,
                question_number=1
            )

    def test_get_question_path_exam_not_found(self):
        """Test: Exam not found raises ExamIsNotExist."""
        with self.assertRaises(ExamIsNotExist):
            self.negev.get_question_path(
                course_id=self.course_id,
                year=2099,  # שנה עתידית שלא קיימת
                semester=self.semester,
                moed=self.moed,
                question_number=1
            )

    def test_get_answer_path_success(self):
        """Test: Successfully retrieve answer path."""
        path = self.negev.get_answer_path(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=1
        )
        self.assertIsInstance(path, str)
        self.assertTrue(path.endswith(".pdf") or path.endswith(".jpg") or path.endswith(".png"))

    def test_get_answer_path_course_not_found(self):
        """Test: Course not found raises CourseIsNotExist."""
        with self.assertRaises(CourseIsNotExist):
            self.negev.get_answer_path(
                course_id="000.0.0000",
                year=self.year,
                semester=self.semester,
                moed=self.moed,
                question_number=1
            )

    def test_get_answer_path_exam_not_found(self):
        """Test: Exam not found raises ExamIsNotExist."""
        with self.assertRaises(ExamIsNotExist):
            self.negev.get_answer_path(
                course_id=self.course_id,
                year=2099,  # שנה שלא קיימת
                semester=self.semester,
                moed=self.moed,
                question_number=1
            )

    # ---Tests for Discussions---
    @patch('Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf', return_value=None)
    @patch('Backend.BusinessLayer.Notifications.NotificationFacade.NotificationFacade.send_notification')
    def test_add_comment_success(self, mock_send_notification, mock_process_pdf):
        """Test: Add a comment successfully to a question discussion."""

        course_id = self.course_id
        year = self.year
        semester = self.semester
        moed = self.moed

        question_number = 9001  # ודא שזה נשמר לאורך כל הטסט

        self.negev.add_question(
            course_id=course_id,
            year=year,
            semester=semester,
            moed=moed,
            question_number=question_number,
            is_american=True,
            question_topics=["מבני נתונים"],
            question_file=self.exam_file,
            answer_file=None
        )

        writer_name = "Test User"
        writer_id = "test_user_id"
        prev_id = "0"  # תגובה ראשונה
        comment_text = "זוהי תגובת בדיקה"
        question_id = str(question_number)  # תואם לשאלה שהוספה

        result = self.negev.add_comment(
            course_id=course_id,
            year=year,
            semester=semester,
            moed=moed,
            question_number=question_number,
            writer_name=writer_name,
            writer_id=writer_id,
            prev_id=prev_id,
            comment_text=comment_text,
            photo_file=None,
            question_id=question_id
        )

        self.assertEqual(result, "CommentData added successfully.")

    @patch('Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf', return_value=None)
    @patch('Backend.BusinessLayer.Notifications.NotificationFacade.NotificationFacade.send_notification')
    def test_add_comment_course_not_found(self, mock_send_notification, mock_process_pdf):
        """Test: Attempt to add comment to non-existent course should fail."""

        writer_name = "Test User"
        writer_id = "test_user_id"
        prev_id = "0"
        comment_text = "תגובה על קורס שלא קיים"
        question_id = "99"

        with self.assertRaises(Exception) as context:
            self.negev.add_comment(
                course_id="fake_course",
                year=2025,
                semester="חורף",
                moed="ב",
                question_number=1,
                writer_name=writer_name,
                writer_id=writer_id,
                prev_id=prev_id,
                comment_text=comment_text,
                photo_file=None,
                question_id=question_id
            )

        self.assertIn("Failed to add comment", str(context.exception))

    @patch('Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf', return_value=None)
    @patch('Backend.BusinessLayer.Notifications.NotificationFacade.NotificationFacade.send_notification')
    def test_add_comment_question_not_found(self, mock_send_notification, mock_process_pdf):
        """Test: Attempt to add comment to non-existent question should fail."""

        # פתיחת קורס אבל בלי להוסיף שאלה
        course_id = self.course_id

        writer_name = "Test User"
        writer_id = "test_user_id"
        prev_id = "0"
        comment_text = "תגובה על שאלה שלא קיימת"
        question_id = "999"  # מזהה שאלה שלא קיים

        with self.assertRaises(Exception) as context:
            self.negev.add_comment(
                course_id=course_id,
                year=self.year,
                semester=self.semester,
                moed=self.moed,
                question_number=999,  # אין שאלה כזו
                writer_name=writer_name,
                writer_id=writer_id,
                prev_id=prev_id,
                comment_text=comment_text,
                photo_file=None,
                question_id=question_id
            )

        self.assertIn("Failed to add comment", str(context.exception))

    @patch('Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf', return_value=None)
    @patch('Backend.BusinessLayer.Notifications.NotificationFacade.NotificationFacade.send_notification')
    def test_add_comment_with_photo_success(self, mock_send_notification, mock_process_pdf):
        """Test: Successfully add a comment with a photo."""

        # פתיחת שאלה רגילה
        self.negev.add_question(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=31,
            is_american=True,
            question_topics=["מבני נתונים"],
            question_file=self.exam_file,
            answer_file=None
        )

        # יצירת קובץ תמונה מזויף
        photo_file = self._mock_pdf_file(filename="image.jpg", content=b"fake image content")

        result = self.negev.add_comment(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=31,
            writer_name="Test User",
            writer_id="user123",
            prev_id="0",
            comment_text="הנה תמונה מצורפת",
            photo_file=photo_file,
            question_id="31"
        )

        self.assertEqual(result, "CommentData added successfully.")

    @patch('Backend.BusinessLayer.Notifications.NotificationFacade.NotificationFacade.send_notification')
    @patch('Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf', return_value=None)
    def test_add_reaction_success(self, mock_process_pdf, mock_send_notification):
        """Test: Add reaction to a comment successfully."""
        new_course_id = "888.8.8888"
        self._open_course(self.user, new_course_id, "קורס לבדיקה תגובות")

        self.negev.add_question(
            course_id=new_course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=99,
            is_american=True,
            question_topics=["תגובות"],
            question_file=self.exam_file,
            answer_file=None
        )

        writer_name = "User A"
        writer_id = "user_a"
        question_id = "99"

        self.negev.add_comment(
            course_id=new_course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=99,
            writer_name=writer_name,
            writer_id=writer_id,
            prev_id="0",
            comment_text="זו תגובה לבדיקה",
            photo_file=None,
            question_id=question_id
        )

        # הוספת משתמש שמבצע את הריאקציה
        reacting_user = self._complete_user_registration("another@bgu.ac.il", "Pass1!", "Another", "User")

        comment_id = "99_0"

        response = self.negev.add_reaction(
            course_id=new_course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=99,
            comment_id=comment_id,
            user_id=reacting_user.user_id,
            emoji="❤️"
        )

        self.assertEqual(response, "ReactionData added successfully.")
        mock_send_notification.assert_called()

    @patch('Backend.BusinessLayer.Notifications.NotificationFacade.NotificationFacade.send_notification')
    def test_add_reaction_same_user_no_notification(self, mock_send_notification):
        """Test: No notification sent when user reacts to their own comment."""
        comment_id = "some_comment_id"

        receiver_id = "user123"

        self.negev.courseFacade.add_reaction = MagicMock(return_value=receiver_id)

        result = self.negev.add_reaction(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=1,
            comment_id=comment_id,
            user_id="user123",  # אותו יוזר
            emoji="👍"
        )

        self.assertEqual(result, "ReactionData added successfully.")
        mock_send_notification.assert_not_called()

    def test_add_reaction_invalid_comment(self):
        """Test: Adding reaction to a non-existent comment raises CommentNotFound."""
        self.negev.courseFacade.add_reaction = MagicMock(side_effect=CommentNotFound("Comment does not exist"))

        with self.assertRaises(CommentNotFound):
            self.negev.add_reaction(
                course_id=self.course_id,
                year=self.year,
                semester=self.semester,
                moed=self.moed,
                question_number=1,
                comment_id="invalid_comment_id",
                user_id="user1",
                emoji="👍"
            )

    def test_add_reaction_course_not_exist(self):
        """Test: Adding reaction to a course that doesn't exist raises CourseIsNotExist."""
        self.negev.courseFacade.add_reaction = MagicMock(side_effect=CourseIsNotExist("Course not found"))

        with self.assertRaises(CourseIsNotExist):
            self.negev.add_reaction(
                course_id="invalid_course",
                year=2023,
                semester="אביב",
                moed="א",
                question_number=1,
                comment_id="some_comment_id",
                user_id="user1",
                emoji="😂"
            )

    def test_get_comment_media_link_success(self):
        """Test: Successfully get media link of a comment."""
        link = self.negev.get_comment_media_link(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=1,
            comment_id="1_0"
        )
        self.assertIsInstance(link, str)
        self.assertTrue(link.endswith(".jpg") or link.endswith(".png") or link.endswith(".pdf"))

    def test_get_comment_media_link_comment_not_found(self):
        """Test: Getting media link for non-existing comment raises CommentNotFound."""
        with self.assertRaises(CommentNotFound):
            self.negev.get_comment_media_link(
                course_id=self.course_id,
                year=self.year,
                semester=self.semester,
                moed=self.moed,
                question_number=1,
                comment_id="nonexistent_comment"
            )

    def test_get_comment_media_link_course_not_exist(self):
        """Test: Getting media link for non-existing course raises CourseIsNotExist."""
        with self.assertRaises(CourseIsNotExist):
            self.negev.get_comment_media_link(
                course_id="000.0.0000",
                year=self.year,
                semester=self.semester,
                moed=self.moed,
                question_number=1,
                comment_id="1_0"
            )

    def test_remove_reaction_success(self):
        """Test: Add question, comment, reaction, then remove reaction successfully."""

        # Step 1: Add question
        self.negev.add_question(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=1,
            is_american=True,
            question_topics=["בדיקה"],
            question_file=self.exam_file,
            answer_file=None
        )

        # Step 2: Add comment
        writer_name = "User A"
        writer_id = "user_a"
        question_id = "165"
        self.negev.add_comment(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=165,
            writer_name=writer_name,
            writer_id=writer_id,
            prev_id="0",
            comment_text="תגובה לבדיקה",
            photo_file=None,
            question_id=question_id
        )
        comment_id = "1_0"

        # Step 3: Add reaction
        user_id = "another_user"
        emoji = "👍"
        self.negev.add_reaction(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=1,
            comment_id=comment_id,
            user_id=user_id,
            emoji=emoji
        )

        # Get reaction_id from the DB (if you're storing it)
        repo = ReactionRepository()
        reactions = repo.get_reactions_for_comment(comment_id)
        self.assertTrue(len(reactions) > 0)
        reaction_id = reactions[0].reaction_id

        # Step 4: Remove reaction
        result = self.negev.remove_reaction(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=1,
            comment_id=comment_id,
            reaction_id=reaction_id
        )

        # Step 5: Assert removal
        self.assertEqual(result, "ReactionData removed successfully.")
        self.assertEqual(len(repo.get_reactions_for_comment(comment_id)), 0)

    @patch('Backend.BusinessLayer.Course.CourseFacade.CourseFacade.remove_reaction')
    def test_remove_reaction_course_not_exist(self, mock_remove_reaction):
        """Test: Remove reaction fails because course does not exist."""
        mock_remove_reaction.side_effect = CourseIsNotExist("Course not found")

        with self.assertRaises(CourseIsNotExist):
            self.negev.remove_reaction(
                course_id="invalid_course",
                year=self.year,
                semester=self.semester,
                moed=self.moed,
                question_number=self.question_number,
                comment_id=self.comment_id,
                reaction_id=self.reaction_id
            )

    @patch('Backend.BusinessLayer.Course.CourseFacade.CourseFacade.remove_reaction')
    def test_remove_reaction_comment_not_found(self, mock_remove_reaction):
        """Test: Remove reaction fails because comment not found."""
        mock_remove_reaction.side_effect = CommentNotFound("comment_id")

        with self.assertRaises(CommentNotFound):
            self.negev.remove_reaction(
                course_id=self.course_id,
                year=self.year,
                semester=self.semester,
                moed=self.moed,
                question_number=self.question_number,
                comment_id="invalid_comment",
                reaction_id=self.reaction_id
            )

    @patch('Backend.BusinessLayer.Course.CourseFacade.CourseFacade.remove_reaction')
    def test_remove_reaction_reaction_not_found(self, mock_remove_reaction):
        """Test: Remove reaction fails because reaction not found."""
        mock_remove_reaction.side_effect = ReactionNotFound("reaction_id")

        with self.assertRaises(ReactionNotFound):
            self.negev.remove_reaction(
                course_id=self.course_id,
                year=self.year,
                semester=self.semester,
                moed=self.moed,
                question_number=self.question_number,
                comment_id=self.comment_id,
                reaction_id="invalid_reaction"
            )

    @patch('Backend.BusinessLayer.NegevNerds.CommentRepository')
    def test_get_comments_metadata_success(self, mock_comment_repo_class):
        """Test: Successfully retrieves comments metadata for a question."""
        fake_comments_metadata = [
            {"comment_id": "comment1", "writer_name": "User A", "timestamp": "2025-04-30"},
            {"comment_id": "comment2", "writer_name": "User B", "timestamp": "2025-04-30"}
        ]

        mock_comment_repo = MagicMock()
        mock_comment_repo.get_comments_metadata_by_question_id.return_value = fake_comments_metadata
        mock_comment_repo_class.return_value = mock_comment_repo

        question_id = "some_question_id"
        result = self.negev.get_comments_metadata(question_id)

        self.assertEqual(result, fake_comments_metadata)
        mock_comment_repo.get_comments_metadata_by_question_id.assert_called_once_with(question_id)

    @patch('Backend.BusinessLayer.NegevNerds.CommentRepository')
    def test_get_comments_metadata_failure(self, mock_comment_repo_class):
        """Test: Fail to retrieve comments metadata returns empty list."""

        mock_comment_repo = MagicMock()
        mock_comment_repo.get_comments_metadata_by_question_id.side_effect = Exception("Database error")
        mock_comment_repo_class.return_value = mock_comment_repo

        question_id = "some_question_id"
        result = self.negev.get_comments_metadata(question_id)

        self.assertEqual(result, [])

    @patch('Backend.BusinessLayer.NegevNerds.CourseFacade')
    def test_delete_comment_success(self, mock_course_facade_class):
        """Test: Successfully delete a comment."""

        mock_course_facade = MagicMock()
        mock_course_facade.delete_comment.return_value = None  # לא מחזיר כלום במחיקה
        mock_course_facade_class.return_value = mock_course_facade

        result = self.negev.delete_comment(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=self.question_number,
            comment_id=self.comment_id
        )

        self.assertEqual(result, "CommentData deleted successfully.")
        mock_course_facade.delete_comment.assert_called_once_with(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=self.question_number,
            comment_id=self.comment_id
        )

    @patch('Backend.BusinessLayer.NegevNerds.CourseFacade')
    def test_delete_comment_not_found(self, mock_course_facade_class):
        """Test: Deleting non-existing comment raises CommentNotFound."""

        mock_course_facade = MagicMock()
        mock_course_facade.delete_comment.side_effect = CommentNotFound(comment_id=self.comment_id)
        mock_course_facade_class.return_value = mock_course_facade

        with self.assertRaises(CommentNotFound):
            self.negev.delete_comment(
                course_id=self.course_id,
                year=self.year,
                semester=self.semester,
                moed=self.moed,
                question_number=self.question_number,
                comment_id=self.comment_id
            )

    def _add_question_and_comment(self, question_number=9002, comment_id="9002_0"):
        self.negev.add_question(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=question_number,
            is_american=True,
            question_topics=["מבני נתונים"],
            question_file=self.exam_file,
            answer_file=None
        )

        self.negev.add_comment(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=question_number,
            writer_name="Editor",
            writer_id="user123",
            prev_id="0",
            comment_text="תגובה מקורית",
            photo_file=None,
            question_id=str(question_number)
        )

        return question_number, comment_id

    def test_edit_comment_text_success(self):
        question_number, comment_id = self._add_question_and_comment()

        result = self.negev.edit_comment_text(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=question_number,
            comment_id=comment_id,
            new_text="טקסט חדש לעריכה"
        )

        self.assertEqual(result, "CommentData edited successfully.")

    def test_edit_comment_text_course_not_found(self):
        with self.assertRaises(CourseIsNotExist):
            self.negev.edit_comment_text(
                course_id="000.0.0000",
                year=self.year,
                semester=self.semester,
                moed=self.moed,
                question_number=1,
                comment_id="1_0",
                new_text="טקסט"
            )

    def test_edit_comment_text_question_not_found(self):
        with self.assertRaises(QuestionNotFound):
            self.negev.edit_comment_text(
                course_id=self.course_id,
                year=self.year,
                semester=self.semester,
                moed=self.moed,
                question_number=9999,
                comment_id="9999_0",
                new_text="עדכון"
            )

    @patch('Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf', return_value=None)
    @patch('Backend.BusinessLayer.Analyzer.AnalyzerFacade.AnalyzerFacade.perform_information_retrival_question_pdf')
    def test_edit_comment_text_comment_not_found(self, mock_retrival_pdf, mock_process_pdf):
        """Test editing comment that does not exist raises CommentNotFound."""

        # מוסיף שאלה אבל לא תגובה
        self.negev.add_question(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=9010,
            is_american=True,
            question_topics=["בדיקה"],
            question_file=self.exam_file,
            answer_file=None
        )

        with self.assertRaises(CommentNotFound):
            self.negev.edit_comment_text(
                course_id=self.course_id,
                year=self.year,
                semester=self.semester,
                moed=self.moed,
                question_number=9010,
                comment_id="9010_0",  # לא קיימת תגובה
                new_text="עדכון"
            )

    def test_check_exist_solution_exists(self):
        """Test: Solution exists for a question."""
        self.negev.add_question(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=1,
            is_american=True,
            question_topics=["בדיקה"],
            question_file=self.exam_file,
            answer_file=self.exam_file  # מצרפים פתרון
        )

        result = self.negev.checkExistSolution(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=1
        )

        self.assertTrue(result, "Expected solution to exist for the question.")

    def test_check_exist_solution_not_exists(self):
        """Test: No solution file uploaded for the question."""
        self.negev.add_question(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=2,
            is_american=True,
            question_topics=["בדיקה"],
            question_file=self.exam_file,
            answer_file=None  # אין פתרון
        )

        result = self.negev.checkExistSolution(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=2
        )

        self.assertFalse(result, "Expected no solution to exist for the question.")

    def test_check_exist_solution_course_not_found(self):
        """Test: Course does not exist, should return an error string."""
        result = self.negev.checkExistSolution(
            course_id="000.0.0000",
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=1
        )

        self.assertIsInstance(result, str)
        self.assertTrue(result.startswith("Error:"), "Expected error message when course does not exist.")


def test_edit_question_topic_success(self):
    """System Test: Successfully update topics of existing question."""

    # יצירת שאלה חדשה
    self.negev.add_question(
        course_id=self.course_id,
        year=self.year,
        semester=self.semester,
        moed=self.moed,
        question_number=101,
        is_american=True,
        question_topics=["גרפים"],
        question_file=self.exam_file,
        answer_file=None
    )

    # עריכת הנושאים
    new_topics = ["חיפוש", "BFS"]
    response_json = self.negev.edit_question_topic(
        course_id=self.course_id,
        year=self.year,
        semester=self.semester,
        moed=self.moed,
        question_number=101,
        topics=new_topics
    )
    response = json.loads(response_json)

    self.assertEqual(response["status"], "success")
    self.assertIn("עודכנו", response["message"])

def test_edit_question_topic_nonexistent_question(self):
    """System Test: Attempt to edit a non-existent question – expect error response."""

    response_json = self.negev.edit_question_topic(
        course_id=self.course_id,
        year=self.year,
        semester=self.semester,
        moed=self.moed,
        question_number=9999,  # מספר שאלה לא קיים
        topics=["תכנות דינמי"]
    )
    response = json.loads(response_json)

    self.assertEqual(response["status"], "error")
    self.assertIn("אירעה שגיאה", response["message"])

def test_edit_question_topic_empty_topic_list(self):
    """System Test: Attempt to clear topics of an existing question."""

    self.negev.add_question(
        course_id=self.course_id,
        year=self.year,
        semester=self.semester,
        moed=self.moed,
        question_number=102,
        is_american=False,
        question_topics=["מורכבויות"],
        question_file=self.exam_file,
        answer_file=None
    )

    response_json = self.negev.edit_question_topic(
        course_id=self.course_id,
        year=self.year,
        semester=self.semester,
        moed=self.moed,
        question_number=102,
        topics=[]  # רשימה ריקה
    )
    response = json.loads(response_json)

    self.assertEqual(response["status"], "success")  # אלא אם מוגדר אחרת בלוגיקה

@patch('Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf', return_value=None)
def test_edit_question_details_success(self, mock_process_pdf):
    """System Test: Successfully edit question details and move to new exam."""

    old_question_number = 201
    new_question_number = 301

    # שלב 1: הוספת שאלה למבחן המקורי
    self.negev.add_question(
        course_id=self.course_id,
        year=self.year,
        semester=self.semester,
        moed=self.moed,
        question_number=old_question_number,
        is_american=True,
        question_topics=["מבני נתונים"],
        question_file=self.exam_file,
        answer_file=None
    )

    # שלב 2: קריאה לפונקציה – מעבירה את השאלה
    result_json = self.negev.edit_question_details(
        old_course_id=self.course_id,
        old_year=self.year,
        old_semester=self.semester,
        old_moed=self.moed,
        old_question_number=old_question_number,
        new_course_id=self.course_id,  # אותו קורס
        new_year=self.year,
        new_semester=self.semester,
        new_moed=self.moed,
        new_question_number=new_question_number
    )

    result = json.loads(result_json)
    self.assertEqual(result["status"], "success")

@patch('Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf', return_value=None)
def test_edit_question_details_question_already_exists(self, mock_process_pdf):
    """System Test: Fail to move question if new question number already exists in target exam."""

    # הוספת שתי שאלות שונות
    self.negev.add_question(
        course_id=self.course_id,
        year=self.year,
        semester=self.semester,
        moed=self.moed,
        question_number=401,
        is_american=True,
        question_topics=["בדיקה"],
        question_file=self.exam_file,
        answer_file=None
    )
    self.negev.add_question(
        course_id=self.course_id,
        year=self.year,
        semester=self.semester,
        moed=self.moed,
        question_number=402,  # ננסה להעביר ל־402
        is_american=True,
        question_topics=["אחר"],
        question_file=self.exam_file,
        answer_file=None
    )

    # ניסיון להעביר את 401 לתוך 402
    response_json = self.negev.edit_question_details(
        old_course_id=self.course_id,
        old_year=self.year,
        old_semester=self.semester,
        old_moed=self.moed,
        old_question_number=401,
        new_course_id=self.course_id,
        new_year=self.year,
        new_semester=self.semester,
        new_moed=self.moed,
        new_question_number=402  # שכבר קיים
    )

    response = json.loads(response_json)
    self.assertEqual(response["status"], "error")

def test_edit_question_details_invalid_parameters(self):
    """System Test: Fail with invalid parameters (invalid moed or year)."""

    response_json = self.negev.edit_question_details(
        old_course_id="bad_course",
        old_year=1999,
        old_semester="חורף",
        old_moed="ז",
        old_question_number=1,
        new_course_id="also_bad",
        new_year=1999,
        new_semester="סתיו",
        new_moed="ח",
        new_question_number=5
    )

    response = json.loads(response_json)
    self.assertEqual(response["status"], "error")
    self.assertIn("לא חוקי", response["message"])

@patch('Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf', return_value=None)
def test_delete_question_solution_success(self, mock_process_pdf):
    """System Test: Delete existing solution file successfully."""

    question_number = 601

    # הוספת שאלה עם פתרון
    self.negev.add_question(
        course_id=self.course_id,
        year=self.year,
        semester=self.semester,
        moed=self.moed,
        question_number=question_number,
        is_american=False,
        question_topics=["אוטומטים"],
        question_file=self.exam_file,
        answer_file=self.exam_file  # ← פתרון קיים
    )

    # פעולה: מחיקת הפתרון
    result = self.negev.delete_question_solution(
        course_id=self.course_id,
        year=self.year,
        semester=self.semester,
        moed=self.moed,
        question_number=question_number
    )

    self.assertTrue(result)

    # בדיקה: וידוא שהקישור לפתרון נמחק
    updated_question = self.negev.search_question_by_specifics(
        course_id=self.course_id,
        year=self.year,
        semester=self.semester,
        moed=self.moed,
        question_number=question_number
    )[0]
    self.assertEqual(updated_question.link_to_answer, "")

@patch('Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf', return_value=None)
def test_delete_question_solution_no_solution(self, mock_process_pdf):
    """System Test: Try deleting a solution when none exists – expect False."""

    question_number = 602

    # יצירת שאלה בלי פתרון
    self.negev.add_question(
        course_id=self.course_id,
        year=self.year,
        semester=self.semester,
        moed=self.moed,
        question_number=question_number,
        is_american=True,
        question_topics=["חיפוש"],
        question_file=self.exam_file,
        answer_file=None
    )

    result = self.negev.delete_question_solution(
        course_id=self.course_id,
        year=self.year,
        semester=self.semester,
        moed=self.moed,
        question_number=question_number
    )

    self.assertFalse(result)

def test_delete_question_solution_question_not_found(self):
    """System Test: Try deleting solution for a non-existent question."""

    result = self.negev.delete_question_solution(
        course_id=self.course_id,
        year=2099,
        semester=self.semester,
        moed=self.moed,
        question_number=9999
    )

    self.assertFalse(result)

@patch('Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf', return_value=None)
def test_swap_question_file_success_pdf(self, mock_process_pdf):
    """System Test: Successfully swap existing PDF question file with a new one."""

    question_number = 701

    # הוספת שאלה עם קובץ קיים
    self.negev.add_question(
        course_id=self.course_id,
        year=self.year,
        semester=self.semester,
        moed=self.moed,
        question_number=question_number,
        is_american=True,
        question_topics=["גרפים"],
        question_file=self.exam_file,
        answer_file=None
    )

    # יצירת קובץ חדש להחלפה
    new_file = self._mock_pdf_file(filename="new_question.pdf", content=b"%PDF-1.4\nNew Content")

    # החלפה בפועל
    result_json = self.negev.swap_question_file(
        course_id=self.course_id,
        year=self.year,
        semester=self.semester,
        moed=self.moed,
        question_number=question_number,
        new_file=new_file
    )

    result = json.loads(result_json)
    self.assertEqual(result["status"], "success")
    self.assertIn("swapped", result["message"])
    self.assertTrue(result["has_link"])
    self.assertTrue(result["link"].endswith(".pdf"))

def test_swap_question_file_no_existing_file(self):
    """System Test: Try to swap file for a question that has no file – expect error."""

    question_number = 702

    # לא מוסיפים שאלה, כלומר אין קובץ קיים

    fake_file = self._mock_pdf_file(filename="fake.pdf", content=b"Test content")

    result_json = self.negev.swap_question_file(
        course_id=self.course_id,
        year=self.year,
        semester=self.semester,
        moed=self.moed,
        question_number=question_number,
        new_file=fake_file
    )

    result = json.loads(result_json)
    self.assertEqual(result["status"], "error")
    self.assertIn("No existing question file", result["message"])

@patch('Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf', return_value=None)
def test_swap_question_file_success_image(self, mock_process_pdf):
    """System Test: Swap file when new file is an image (photo)."""

    question_number = 703

    # יצירת שאלה עם קובץ
    self.negev.add_question(
        course_id=self.course_id,
        year=self.year,
        semester=self.semester,
        moed=self.moed,
        question_number=question_number,
        is_american=False,
        question_topics=["חישוביות"],
        question_file=self.exam_file,
        answer_file=None
    )

    # קובץ חדש מסוג תמונה
    new_image = self._mock_pdf_file(filename="img.jpg", content=b"\xff\xd8\xff\xe0JPEG...")

    result_json = self.negev.swap_question_file(
        course_id=self.course_id,
        year=self.year,
        semester=self.semester,
        moed=self.moed,
        question_number=question_number,
        new_file=new_image
    )

    result = json.loads(result_json)
    self.assertEqual(result["status"], "success")
    self.assertTrue(result["link"].endswith(".jpg"))

def test_is_following_true(self):
    """System Test: User is following the discussion – expect True."""

    # הוספת שאלה
    question_number = 801
    self.negev.add_question(
        course_id=self.course_id,
        year=self.year,
        semester=self.semester,
        moed=self.moed,
        question_number=question_number,
        is_american=True,
        question_topics=["מכונות מצבים"],
        question_file=self.exam_file,
        answer_file=None
    )

    question_id = str(question_number)

    # משתמש עוקב אחרי השאלה
    self.negev.toggle_follow_discussion(user_id=self.user.user_id, question_id=question_id)

    result = self.negev.is_following(user_id=self.user.user_id, question_id=question_id)
    self.assertTrue(result)

def test_is_following_false(self):
    """System Test: User is not following the discussion – expect False."""

    question_number = 802
    self.negev.add_question(
        course_id=self.course_id,
        year=self.year,
        semester=self.semester,
        moed=self.moed,
        question_number=question_number,
        is_american=True,
        question_topics=["שפות פורמליות"],
        question_file=self.exam_file,
        answer_file=None
    )

    question_id = str(question_number)

    # לא מפעילים toggle_follow → המשתמש לא עוקב
    result = self.negev.is_following(user_id=self.user.user_id, question_id=question_id)
    self.assertFalse(result)


def test_is_following_invalid_ids(self):
    """System Test: Invalid user/question IDs should still return False safely."""

    result = self.negev.is_following(user_id="nonexistent_user", question_id="nonexistent_q")
    self.assertFalse(result)

def test_follow_question_success(self):
    """System Test: User follows a question successfully."""

    # יצירת שאלה
    question_number = 901
    self.negev.add_question(
        course_id=self.course_id,
        year=self.year,
        semester=self.semester,
        moed=self.moed,
        question_number=question_number,
        is_american=True,
        question_topics=["אלגוריתמים"],
        question_file=self.exam_file,
        answer_file=None
    )
    question_id = str(question_number)

    # פעולת המעקב
    self.negev.follow_question(user_id=self.user.user_id, question_id=question_id)

    # בדיקה שהמשתמש עוקב באמת
    result = self.negev.is_following(user_id=self.user.user_id, question_id=question_id)
    self.assertTrue(result)

def test_follow_question_idempotent(self):
    """System Test: Calling follow_question twice should not crash or duplicate."""

    question_number = 902
    self.negev.add_question(
        course_id=self.course_id,
        year=self.year,
        semester=self.semester,
        moed=self.moed,
        question_number=question_number,
        is_american=False,
        question_topics=["גרפים"],
        question_file=self.exam_file,
        answer_file=None
    )
    question_id = str(question_number)

    # פעולת מעקב פעמיים
    self.negev.follow_question(user_id=self.user.user_id, question_id=question_id)
    self.negev.follow_question(user_id=self.user.user_id, question_id=question_id)

    # עדיין עוקב
    result = self.negev.is_following(user_id=self.user.user_id, question_id=question_id)
    self.assertTrue(result)


def test_follow_question_invalid_ids(self):
    """System Test: Follow with invalid user or question IDs should not raise unhandled exceptions."""

    try:
        self.negev.follow_question(user_id="nonexistent_user", question_id="nonexistent_question")
    except Exception as e:
        self.fail(f"follow_question raised an exception unexpectedly: {e}")

def test_unfollow_question_success(self):
    """System Test: User successfully unfollows a followed question."""

    question_number = 1001
    self.negev.add_question(
        course_id=self.course_id,
        year=self.year,
        semester=self.semester,
        moed=self.moed,
        question_number=question_number,
        is_american=True,
        question_topics=["מערכים"],
        question_file=self.exam_file,
        answer_file=None
    )
    question_id = str(question_number)

    # משתמש עוקב
    self.negev.follow_question(self.user.user_id, question_id)
    self.assertTrue(self.negev.is_following(self.user.user_id, question_id))

    # פעולה: ביטול מעקב
    self.negev.unfollow_question(self.user.user_id, question_id)

    # בדיקה: אינו עוקב עוד
    self.assertFalse(self.negev.is_following(self.user.user_id, question_id))

def test_unfollow_question_not_following(self):
    """System Test: Unfollow a question that wasn't being followed – should not raise."""

    question_number = 1002
    self.negev.add_question(
        course_id=self.course_id,
        year=self.year,
        semester=self.semester,
        moed=self.moed,
        question_number=question_number,
        is_american=False,
        question_topics=["מיון"],
        question_file=self.exam_file,
        answer_file=None
    )
    question_id = str(question_number)

    # פעולה: unfollow בלי follow קודם
    try:
        self.negev.unfollow_question(self.user.user_id, question_id)
    except Exception as e:
        self.fail(f"unfollow_question raised an unexpected exception: {e}")

def test_unfollow_question_invalid_ids(self):
    """System Test: Attempting to unfollow with invalid IDs should not crash."""

    try:
        self.negev.unfollow_question("bad_user", "bad_question")
    except Exception as e:
        self.fail(f"unfollow_question raised an unexpected exception: {e}")
