import io
import json
from unittest.mock import patch, MagicMock

from Backend.BusinessLayer.Util.Exceptions import CourseIsNotExist, QuestionAlreadyInExam, ExamIsNotExist
from Backend.DataLayer.DTOs.QuestionDTO import QuestionDTO
from Backend.DataLayer.ExamData.ExamRepository import ExamRepository
from Backend.DataLayer.Questions.QuestionRepository import QuestionRepository
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
        self.answer_file = self._mock_pdf_file(filename="answer.pdf", content=b"Dummy answer content")

    def tearDown(self):
        super().tearDown()

        if isinstance(self.negev.courseFacade.check_valid_question, MagicMock):
            del self.negev.courseFacade.check_valid_question

        if isinstance(self.negev.courseFacade.check_exam_full_pdf, MagicMock):
            del self.negev.courseFacade.check_exam_full_pdf

    # ---Tests for Questions---
    @patch('Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf', return_value=None)
    def test_search_by_topic_success(self, mock_process_pdf):
        """Test: Search by existing topic returns questions."""
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

        results = self.negev.search_by_topic(self.course_id, topic)

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
    def test_search_by_specifics_full_match(self, mock_process_pdf):
        """Test Case 1: Search with all details returns specific question."""

        # הוספת שאלה שתתאים לפרטי החיפוש
        self.negev.add_question(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=1,
            is_american=True,
            question_topics=["אילמות"],
            question_file=self.exam_file,
            answer_file=None
        )

        # ביצוע החיפוש
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

    import io
    from unittest.mock import patch

    @patch("Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf", return_value=None)
    def test_get_question_path_success(self, mock_process_pdf):
        try:
            self.negev.courseFacade.open_course(self.course_id, "מבוא לבינה", ["נושאים"])
        except Exception:
            pass  # הקורס כבר קיים

        # יצירת קובץ PDF מזויף עם שדה filename
        fake_pdf = io.BytesIO(b"Dummy PDF content")
        fake_pdf.filename = "fake.pdf"

        self.negev.add_question(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=5555,
            is_american=True,
            question_topics=["נושאים"],
            question_file=fake_pdf,
            answer_file=None
        )

        result = self.negev.get_question_path(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=5555
        )

        self.assertTrue(result.endswith(".pdf"))

    def test_get_question_path_invalid_course(self):
        with self.assertRaises(Exception) as context:
            self.negev.get_question_path(
                course_id="000.0.0000",  # קורס לא קיים
                year=self.year,
                semester=self.semester,
                moed=self.moed,
                question_number=self.question_number
            )
        self.assertIn("Failed to get path", str(context.exception))

    @patch('Backend.BusinessLayer.Analyzer.AnalyzerFacade.AnalyzerFacade.perform_information_retrival_question_pdf',
           return_value=None)
    def test_get_link_to_answer_success(self, mock_info_retrieval):
        """Test: Get answer file link for existing question."""
        try:
            self.negev.courseFacade.open_course(self.course_id, "מערכות", ["מממ"])
        except Exception:
            pass

        self.negev.add_question(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=self.question_number,
            is_american=False,
            question_topics=["קבצים"],
            question_file=self.exam_file,
            answer_file=self.answer_file
        )

        result = self.negev.courseFacade.get_link_to_answer(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=self.question_number
        )

        self.assertTrue(result.endswith(".pdf"))

    def test_get_link_to_answer_course_not_found(self):
        """Test: Try to get answer link for non-existing course."""
        with self.assertRaises(CourseIsNotExist):
            self.negev.courseFacade.get_link_to_answer(
                course_id="fake.course",
                year=self.year,
                semester=self.semester,
                moed=self.moed,
                question_number=self.question_number
            )

    def test_get_link_to_answer_exam_not_found(self):
        """Test: Try to get answer link for course with no such exam."""
        self.negev.courseFacade.open_course("999.9.9699", "חדש", ["נושאים"])
        with self.assertRaises(ExamIsNotExist):
            self.negev.courseFacade.get_link_to_answer(
                course_id="999.9.9699",
                year=self.year,
                semester=self.semester,
                moed="ב",  # מועד לא קיים
                question_number=self.question_number
            )

    @patch('Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf', return_value=None)
    @patch('elasticsearch.Elasticsearch.delete', return_value=None)
    def test_delete_question_success(self, mock_delete_elastic, mock_process_pdf):
        """Test: Successfully delete an existing question."""
        # הוספת שאלה
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

        # שליפת מזהה מבחן
        exam_repo = ExamRepository()
        exam = exam_repo.get_exam_by_date(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed
        )
        self.assertIsNotNone(exam, "Exam should exist before checking its ID")
        exam_id = exam.id

        # ודא שהשאלה קיימת לפני מחיקה
        question_repo = QuestionRepository()
        question = question_repo.get_question_by_number(exam_id=exam_id, question_number=100)
        self.assertIsNotNone(question, "Question should exist before deletion.")

        # מחיקת שאלה
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

        # ודא שהשאלה נמחקה
        question_after = question_repo.get_question_by_number(exam_id=exam_id, question_number=100)
        self.assertIsNone(question_after, "Expected the question to be deleted from database.")

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
    def test_edit_question_topic_success(self, mock_process_pdf):
        """System Test: Successfully update topics of existing question."""

        # הוספת שאלה
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

        # הוספת הנושאים החדשים לקורס לפני העדכון
        from Backend.DataLayer.CourseTopics.CourseTopicsRepository import CourseTopicsRepository
        course_topic_repo = CourseTopicsRepository()
        course_topic_repo.add_Topic_to_course(self.course_id, "BFS")
        course_topic_repo.add_Topic_to_course(self.course_id, "חיפוש")

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

        print("📤 edit_question_topic response:", response)

        if response["status"] != "success":
            print("❌ טסט נכשל – התקבלה שגיאה:", response["message"])

        self.assertEqual(response["status"], "success")
        self.assertIn("עודכנו", response["message"])

    def test_edit_question_topic_nonexistent_question(self):
        """System Test: Attempt to edit a non-existent question – expect error response."""

        response_json = self.negev.edit_question_topic(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=9999,
            topics=["תכנות דינמי"]
        )
        response = json.loads(response_json)

        self.assertEqual(response["status"], "error")
        self.assertIn("אירעה שגיאה", response["message"])

    @patch('Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf', return_value=None)
    def test_edit_question_topic_empty_topic_list(self, mock_process_pdf):
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
            topics=[]
        )
        response = json.loads(response_json)

        self.assertEqual(response["status"], "success")

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
        self.assertIn("Invalid", response["message"])

    @patch('Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf', return_value=None)
    def test_delete_question_solution_success(self, mock_process_pdf):
        """System Test: Delete existing solution file successfully."""
        question_number = 601

        self.negev.add_question(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=question_number,
            is_american=False,
            question_topics=["אוטומטים"],
            question_file=self.exam_file,
            answer_file=self.exam_file
        )

        result = self.negev.delete_question_solution(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=question_number
        )

        self.assertTrue(result)

    @patch('Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf', return_value=None)
    def test_delete_question_solution_no_solution(self, mock_process_pdf):
        """System Test: Try deleting a solution when none exists – expect False."""

        question_number = 602

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
        """System Test: Expect ExamIsNotExist exception for non-existent question."""
        with self.assertRaises(ExamIsNotExist):
            self.negev.delete_question_solution(
                course_id=self.course_id,
                year=2099,
                semester=self.semester,
                moed=self.moed,
                question_number=9999
            )

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

    @patch('Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf', return_value=None)
    def test_is_following_true(self, mock_process_pdf):
        """System Test: User is following the discussion – expect True."""
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
        self.negev.follow_question(user_id=self.user.user_id, question_id=question_id)

        result = self.negev.is_following(user_id=self.user.user_id, question_id=question_id)
        self.assertTrue(result)

    @patch('Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf', return_value=None)
    def test_is_following_false(self, mock_process_pdf):
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

    @patch('Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf', return_value=None)
    def test_follow_question_success(self, mock_process_pdf):
        """System Test: User follows a question successfully."""
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

    @patch('Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf', return_value=None)
    def test_follow_question_idempotent(self, mock_process_pdf):
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

    @patch('Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf', return_value=None)
    def test_unfollow_question_success(self, mock_process_pdf):
        """System Test: User successfully unfollows a followed question."""
        question_number = 43
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

        self.negev.follow_question(self.user.user_id, question_id)
        self.assertTrue(self.negev.is_following(self.user.user_id, question_id))

        self.negev.unfollow_question(self.user.user_id, question_id)

        self.assertFalse(self.negev.is_following(self.user.user_id, question_id))

    @patch('Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf', return_value=None)
    def test_unfollow_question_not_following(self, mock_process_pdf):
        """System Test: Unfollow a question that wasn't being followed – should not raise."""

        question_number = 79
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
