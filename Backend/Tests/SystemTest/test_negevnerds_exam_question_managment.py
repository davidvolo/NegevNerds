import io
import unittest
from unittest.mock import patch

from unittest.mock import MagicMock

from werkzeug.datastructures import FileStorage

from Backend.BusinessLayer.NegevNerds import NegevNerds
from Backend.BusinessLayer.Util.Exceptions import CourseIsNotExist, QuestionAlreadyInExam, CommentNotFound, \
    ExamIsNotExist, ReactionNotFound
from Backend.DataLayer.DTOs.QuestionDTO import QuestionDTO
from Backend.Tests.SystemTest.BaseTestCase import BaseTestCase


def _mock_pdf_file(filename="exam.pdf", content=b"%PDF-1.4\n%Fake PDF content\n"):
    stream = io.BytesIO(content)
    file = FileStorage(stream=stream, filename=filename, content_type='application/pdf')
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
        self.semester = "אביב"
        self.moed = "א"
        self.exam_file = _mock_pdf_file()
        self.invalid_file = _mock_invalid_file()
        self._open_course(self.user, self.course_id, "מבוא להעלאת מבחנים")

    def tearDown(self):
        super().tearDown()

        if isinstance(self.negev.courseFacade.check_valid_question, MagicMock):
            del self.negev.courseFacade.check_valid_question

        if isinstance(self.negev.courseFacade.check_exam_full_pdf, MagicMock):
            del self.negev.courseFacade.check_exam_full_pdf

    # ---Tests for exams---
    @patch('Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf', return_value=None)
    def test_upload_exam_success(self, mock_process_pdf):
        """Verify user can upload a valid exam file."""

        # Step 0: Define a fresh exam identifiers
        new_year = 2024
        new_semester = "סתיו"
        new_moed = "ב"

        # Step 1: Add dummy question to create new ExamData
        self.negev.add_question(
            course_id=self.course_id,
            year=new_year,
            semester=new_semester,
            moed=new_moed,
            question_number=1,
            is_american=True,
            question_topics=["מבני נתונים"],
            question_file=self.exam_file,
            answer_file=None
        )

        # Step 2: Upload exam
        response = self.negev.upload_full_exam_pdf(
            self.course_id, new_year, new_semester, new_moed, self.exam_file
        )

        # Step 3: Assertions
        self.assertEqual(response["status"], "success")
        self.assertIn("File uploaded", response["message"])

    @patch('Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf', return_value=None)
    def test_upload_solution_invalid_format(self, mock_process_pdf):
        """Verify uploading a non-PDF file still succeeds (since no format validation)."""

        self.negev.add_question(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=23,
            is_american=True,
            question_topics=["מבני נתונים"],
            question_file=self.exam_file,
            answer_file=None
        )

        invalid_file = _mock_invalid_file()

        response = self.negev.uploadSolution(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=23,
            solution_file=invalid_file
        )

        self.assertEqual(response["status"], "success")
        self.assertIn("uploaded", response["message"].lower())

    def test_upload_exam_course_not_exist(self):
        """Verify uploading an exam for a non-existent course returns an error."""
        original_check_exam_full_pdf = self.negev.courseFacade.check_exam_full_pdf
        self.negev.courseFacade.check_exam_full_pdf = MagicMock(return_value=False)

        fake_course_id = "000.0.0000"
        response = self.negev.upload_full_exam_pdf(fake_course_id, self.year, self.semester, self.moed, self.exam_file)
        self.assertEqual(response["status"], "error")
        self.assertIn("not found", response["message"].lower())

        self.negev.courseFacade.check_exam_full_pdf = original_check_exam_full_pdf

    @patch('Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf', return_value=None)
    def test_upload_exam_already_exists(self, mock_process_pdf):
        """Verify uploading an exam that already exists returns an error."""

        new_course_id = "777.7.7777"
        self._open_course(self.user, new_course_id, "קורס למבחן כפול")

        self.negev.add_question(
            course_id=new_course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=1,
            is_american=True,
            question_topics=["כפול"],
            question_file=self.exam_file,
            answer_file=None
        )

        upload_response_1 = self.negev.upload_full_exam_pdf(
            new_course_id, self.year, self.semester, self.moed, self.exam_file
        )
        self.assertEqual(upload_response_1["status"], "success", "First upload should succeed.")

        exam = self.negev.courseFacade.get_course(new_course_id).get_exam(self.year, self.semester, self.moed)
        assert exam.link is not None, "Expected exam link to be set after first upload"

        upload_response_2 = self.negev.upload_full_exam_pdf(
            new_course_id, self.year, self.semester, self.moed, self.exam_file
        )
        self.assertEqual(upload_response_2["status"], "error")
        self.assertIn("already exists", upload_response_2["message"].lower())

    @patch('Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf', return_value=None)
    def test_upload_and_get_exam_full_pdf_success(self, mock_process_pdf):
        """Full flow: Add question -> Upload exam -> Retrieve exam."""

        new_course_id = "888.8.8888"
        self._open_course(self.user, new_course_id, "מבוא לבדיקות משולבות")

        self.negev.add_question(
            course_id=new_course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=15,  # מספר חדש
            is_american=True,
            question_topics=["מבני נתונים"],
            question_file=self.exam_file,
            answer_file=None
        )

        upload_response = self.negev.upload_full_exam_pdf(
            new_course_id, self.year, self.semester, self.moed, self.exam_file
        )
        self.assertEqual(upload_response["status"], "success")
        self.assertIn("File uploaded", upload_response["message"])

        result = self.negev.get_exam_full_pdf(
            new_course_id, self.year, self.semester, self.moed
        )

        self.assertIsNotNone(result)

    def test_get_exam_full_pdf_course_not_found(self):
        """Verify getting exam PDF fails when course does not exist."""
        fake_course_id = "999.9.9999"
        result = self.negev.get_exam_full_pdf(fake_course_id, self.year, self.semester, self.moed)
        self.assertIsInstance(result, str)
        self.assertFalse(result, "Expected error message to start with 'Error:'")

    def test_get_exam_full_pdf_exam_not_found(self):
        """Verify getting exam PDF fails when exam does not exist for the course."""
        # Open a course but do NOT add questions or upload exam
        new_course_id = "888.8.8888"
        self._open_course(self.user, new_course_id, "קורס טסט ללא מבחן")

        result = self.negev.get_exam_full_pdf(new_course_id, self.year, self.semester, self.moed)
        self.assertIsInstance(result, str)
        self.assertIn("CourseFacade Error", result)
        self.assertIn("not exist", result.lower())

    @patch('Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf', return_value=None)
    def test_get_exam_full_pdf_wrong_year(self, mock_process_pdf):
        """Test: Trying to get exam with wrong year."""
        self.negev.add_question(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=2,
            is_american=True,
            question_topics=["מבני נתונים"],
            question_file=self.exam_file,
            answer_file=None
        )
        wrong_year = 2030
        result = self.negev.get_exam_full_pdf(self.course_id, wrong_year, self.semester, self.moed)
        self.assertIsInstance(result, str)
        self.assertIn("CourseFacade Error", result)

    @patch('Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf', return_value=None)
    def test_get_exam_full_pdf_wrong_semester(self, mock_process_pdf):
        """Test: Trying to get exam with wrong semester."""
        self.negev.add_question(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=4,
            is_american=True,
            question_topics=["מבני נתונים"],
            question_file=self.exam_file,
            answer_file=None
        )
        wrong_semester = "חורף"
        result = self.negev.get_exam_full_pdf(self.course_id, self.year, wrong_semester, self.moed)
        self.assertIsInstance(result, str)
        self.assertIn("CourseFacade Error", result)

    @patch('Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf', return_value=None)
    def test_check_exam_full_pdf_exists(self, mock_process_pdf):
        """Test: Exam full PDF exists after upload."""
        # Step 1: Add a question to create ExamData
        self.negev.add_question(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=1,
            is_american=True,
            question_topics=["מבני נתונים"],
            question_file=self.exam_file,
            answer_file=None
        )

        # Step 2: Upload the full exam PDF
        self.negev.upload_full_exam_pdf(
            self.course_id, self.year, self.semester, self.moed, self.exam_file
        )

        # Step 3: Check that the exam exists
        result = self.negev.check_exam_full_pdf(self.course_id, self.year, self.semester, self.moed)
        self.assertTrue(result)

    def test_check_exam_full_pdf_not_exists(self):
        """Test: Exam full PDF does not exist when not uploaded."""
        new_course_id = "999.9.9999"
        self._open_course(self.user, new_course_id, "קורס ללא מבחן")

        result = self.negev.check_exam_full_pdf(new_course_id, self.year, self.semester, self.moed)
        self.assertFalse(result)

    def test_check_exam_full_pdf_course_not_found(self):
        """Test: Course not found should return False."""
        fake_course_id = "999.9.9999"
        result = self.negev.check_exam_full_pdf(fake_course_id, self.year, self.semester, self.moed)

        self.assertFalse(result, "Expected result to be False when course is not found.")

    @patch('Backend.BusinessLayer.Analyzer.AnalyzerFacade.AnalyzerFacade.splitPDF')
    @patch('Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf', return_value=None)
    def test_split_pdf_success(self, mock_process_pdf, mock_split_pdf):
        """Test: Successfully splitting and adding questions."""

        mock_split_pdf.return_value = [self.exam_file, self.exam_file]

        self.negev.splitPDF(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            pdf_file=self.exam_file,
            line_data=[100, 200]
        )

        results = self.negev.search_question_by_specifics(course_id=self.course_id)
        self.assertGreaterEqual(len(results), 2, "Expected at least two questions to be added.")

    @patch('Backend.BusinessLayer.Analyzer.AnalyzerFacade.AnalyzerFacade.splitPDF')
    @patch('Backend.BusinessLayer.Course.CourseFacade.CourseFacade.check_valid_question', return_value=False)
    @patch('Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf', return_value=None)
    def test_split_pdf_question_not_valid(self, mock_process_pdf, mock_check_valid, mock_split_pdf):
        """Test: Questions not added when check_valid_question fails."""

        mock_split_pdf.return_value = [self.exam_file]

        results_before = self.negev.search_question_by_specifics(course_id=self.course_id)
        count_before = len(results_before)

        self.negev.splitPDF(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            pdf_file=self.exam_file,
            line_data=[100]
        )

        results_after = self.negev.search_question_by_specifics(course_id=self.course_id)
        count_after = len(results_after)

        self.assertEqual(count_after, count_before, "Expected no new questions to be added.")

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

    @patch('Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf', return_value=None)
    def test_search_free_text_without_course_id_real(self, mock_process_pdf):
        """System Test: Search free text without course_id."""

        # יצירת שאלה אמיתית
        course_id = self.course_id
        year = self.year
        semester = self.semester
        moed = self.moed
        question_number = 501
        topic = "מבני נתונים"
        question_text = "זו שאלה על עצי חיפוש בינאריים."

        self.negev.add_question(
            course_id=course_id,
            year=year,
            semester=semester,
            moed=moed,
            question_number=question_number,
            is_american=True,
            question_topics=[topic],
            question_file=self.exam_file,
            answer_file=None
        )

        # חיפוש טקסט חופשי
        search_text = "עץ חיפוש"
        results = self.negev.search_free_text(text=search_text)

        # בדיקות
        self.assertIsInstance(results, list)
        self.assertGreaterEqual(len(results), 1, "Expected at least one result.")
        self.assertTrue(
            any(q.course_id == course_id for q in results),
            "Expected to find question related to course."
        )

    @patch('Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf', return_value=None)
    def test_search_free_text_with_course_id_real(self, mock_process_pdf):
        """System Test: Search free text within a specific course."""

        # יצירת שאלה אמיתית
        course_id = self.course_id
        year = self.year
        semester = self.semester
        moed = self.moed
        question_number = 502
        topic = "אוטומטים"
        question_text = "מה זה DFA?"

        self.negev.add_question(
            course_id=course_id,
            year=year,
            semester=semester,
            moed=moed,
            question_number=question_number,
            is_american=True,
            question_topics=[topic],
            question_file=self.exam_file,
            answer_file=None
        )

        # חיפוש טקסט חופשי בקורס
        search_text = "DFA"
        results = self.negev.search_free_text(text=search_text, course_id=course_id)

        # בדיקות
        self.assertIsInstance(results, list)
        self.assertGreaterEqual(len(results), 1, "Expected at least one result.")
        self.assertTrue(
            all(q.course_id == course_id for q in results),
            "All results must belong to the correct course."
        )

    @patch('Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf', return_value=None)
    def test_search_free_text_no_results_real(self, mock_process_pdf):
        """System Test: Search free text returns no results when nothing matches."""

        search_text = "משהו שלא קיים בכלל"

        results = self.negev.search_free_text(text=search_text)

        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 0, "Expected no results.")

    def test_search_question_free_text_multiple_matches(self):
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

    @patch('Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf', return_value=None)
    def test_search_free_text_case_insensitive(self, mock_process_pdf):
        """System Test: Verify search is case-insensitive (patch instance elastic_search)."""

        # שלב 1: הוספת שאלה
        course_id = self.course_id
        year = self.year
        semester = self.semester
        moed = self.moed
        question_number = 701

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

        # שלב 2: Patch על אובייקט קיים
        with patch.object(self.negev._pdfFacade.information_retrival, 'elastic_search') as mock_elastic_search:
            mock_elastic_search.search.return_value = {
                "hits": {
                    "hits": [
                        {
                            "_source": {
                                "question_id": str(question_number),
                                "course_id": str(course_id),
                            }
                        }
                    ]
                }
            }

            # שלב 3: חיפוש
            search_text = "מַעֲרָך"
            results = self.negev.search_free_text(search_text)

            # שלב 4: בדיקות
            self.assertIsInstance(results, list)
            self.assertGreaterEqual(len(results), 1, "Expected at least one result for case-insensitive search.")
            self.assertTrue(
                any("מבני" in q.question_topics[0] or "מערך" in q.question_text for q in results),
                "Expected to find 'מערך' or 'מבני' in question text ignoring casing/nikkud."
            )

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
        """Verify uploading a solution PDF works correctly."""
        # הוספת שאלה כדי שיהיה מה להעלות עליו פתרון
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
        self.assertIn("File uploaded", response["message"])
        self.assertTrue(response["link"].endswith(".pdf"))

    @patch('Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf', return_value=None)
    @patch('Backend.BusinessLayer.Analyzer.AnalyzerFacade.AnalyzerFacade.perform_information_retrival_question_pdf',
           return_value=None)
    def test_upload_solution_already_exists(self, mock_perform_retrival, mock_process_pdf):
        """Verify error is raised when uploading solution that already exists."""

        # הוספת שאלה
        self.negev.add_question(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=21,
            is_american=True,
            question_topics=["מבני נתונים"],
            question_file=self.exam_file,
            answer_file=self.exam_file  # כבר יש פתרון
        )

        response = self.negev.uploadSolution(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=21,
            solution_file=self.exam_file
        )

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
    def test_upload_solution_invalid_format(self, mock_process_pdf):
        """Verify invalid format file (e.g., text) returns an error."""

        self.negev.add_question(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=23,
            is_american=True,
            question_topics=["מבני נתונים"],
            question_file=self.exam_file,
            answer_file=None
        )

        invalid_file = _mock_invalid_file()

        response = self.negev.uploadSolution(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=23,
            solution_file=invalid_file
        )

        self.assertEqual(response["status"], "error")
        self.assertIn("valid PDF", response["message"].lower())

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

        self.negev.add_question(
            course_id=course_id,
            year=year,
            semester=semester,
            moed=moed,
            question_number=30,  # מספר חדש
            is_american=True,
            question_topics=["מבני נתונים"],
            question_file=self.exam_file,
            answer_file=None
        )

        writer_name = "Test User"
        writer_id = "test_user_id"
        prev_id = "0"  # תגובה ראשונה
        comment_text = "זוהי תגובת בדיקה"
        question_id = "30"  # אותו מזהה של השאלה

        result = self.negev.add_comment(
            course_id=course_id,
            year=year,
            semester=semester,
            moed=moed,
            question_number=30,
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
        photo_file = _mock_pdf_file(filename="image.jpg", content=b"fake image content")

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

        comment_id = "99_0"

        response = self.negev.add_reaction(
            course_id=new_course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=99,
            comment_id=comment_id,
            user_id="another_user",
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
    @patch('Backend.BusinessLayer.Course.CourseFacade.CourseFacade.remove_reaction')
    def test_remove_reaction_success(self, mock_remove_reaction):
        """Test: Successfully remove a reaction."""
        mock_remove_reaction.return_value = None  # אין החזרה אמיתית

        result = self.negev.remove_reaction(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=self.question_number,
            comment_id=self.comment_id,
            reaction_id=self.reaction_id
        )

        self.assertEqual(result, "ReactionData removed successfully.")
        mock_remove_reaction.assert_called_once()

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

        # יצירת דמה של תגובות
        fake_comments_metadata = [
            {"comment_id": "comment1", "writer_name": "User A", "timestamp": "2025-04-30"},
            {"comment_id": "comment2", "writer_name": "User B", "timestamp": "2025-04-30"}
        ]

        mock_comment_repo = MagicMock()
        mock_comment_repo.get_comments_metadata_by_question_id.return_value = fake_comments_metadata
        mock_comment_repo_class.return_value = mock_comment_repo

        # קריאה לפונקציה
        question_id = "some_question_id"
        result = self.negev.get_comments_metadata(question_id)

        # בדיקות
        self.assertEqual(result, fake_comments_metadata)
        mock_comment_repo.get_comments_metadata_by_question_id.assert_called_once_with(question_id)

    @patch('Backend.BusinessLayer.NegevNerds.CommentRepository')
    def test_get_comments_metadata_failure(self, mock_comment_repo_class):
        """Test: Fail to retrieve comments metadata raises an Exception."""

        mock_comment_repo = MagicMock()
        mock_comment_repo.get_comments_metadata_by_question_id.side_effect = Exception("Database error")
        mock_comment_repo_class.return_value = mock_comment_repo

        question_id = "some_question_id"
        with self.assertRaises(Exception) as context:
            self.negev.get_comments_metadata(question_id)

        self.assertIn("Error in NegevNerds delete_question", str(context.exception))

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