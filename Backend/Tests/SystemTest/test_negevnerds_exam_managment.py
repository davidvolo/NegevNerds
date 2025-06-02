import io
import json
import os
import shutil
from unittest.mock import patch, MagicMock
from werkzeug.datastructures import FileStorage

from Backend.BusinessLayer.Course.enums import Semester, Moed
from Backend.BusinessLayer.NegevNerds import NegevNerds
from Backend.BusinessLayer.Util.Exceptions import CourseIsNotExist, QuestionAlreadyInExam, CommentNotFound, \
    ExamIsNotExist, ReactionNotFound, QuestionNotFound
from Backend.DataLayer.DTOs.QuestionDTO import QuestionDTO
from Backend.Tests.SystemTest.BaseTestCase import BaseTestCase
from Backend.BusinessLayer.Util.Exceptions import ExamIsNotExist
from Backend.BusinessLayer.FileManager.FileManager import FileManager


class TestNegevNerdsExamManagement(BaseTestCase):

    def _mock_pdf_file(self, filename="exam.pdf", content=b"%PDF-1.4 test pdf content"):
        stream = io.BytesIO(content)
        return FileStorage(stream=stream, filename=filename, content_type='application/pdf')

    def setUp(self):
        super().setUp()

        self.test_files_dir = os.path.abspath("test_temp_files")
        os.makedirs(self.test_files_dir, exist_ok=True)

        FileManager._instance = None  # Reset the singleton
        self.file_manager = FileManager(base_dir=self.test_files_dir)
        self.negev._file_manager = self.file_manager

        self.user = self._complete_user_registration("examuser@bgu.ac.il", "Password1!", "מבחן", "מעלה")
        self.course_id = "777.1.1010"
        self.year = 2023
        self.semester = Semester.SPRING
        self.moed = Moed.A

        self.exam_file = self._mock_pdf_file(filename="exam.pdf", content=b"dummy exam content")
        self.solution_file = self._mock_pdf_file(filename="solution.pdf", content=b"dummy solution content")

        self._open_course(self.user, self.course_id, "מבוא להעלאת מבחנים")

    def tearDown(self):
        super().tearDown()
        shutil.rmtree(self.test_files_dir, ignore_errors=True)
        FileManager._instance = None

    def test_check_exam_full_pdf_success(self):
        with patch.object(self.negev._pdfFacade, 'perform_information_retrival_question_pdf',
                             return_value=None), \
                patch.object(self.negev._pdfFacade, 'extract_text_from_pdf_file',
                             return_value="שאלה לדוגמה"):
            # Step 1: Add a question to create ExamData
            result = self.negev.add_question(
                course_id=self.course_id,
                year=self.year,
                semester=self.semester,
                moed=self.moed,
                question_number=565,
                is_american=True,
                question_topics=["מבני נתונים"],
                question_file=self.exam_file,
                answer_file=None
            )
            self.assertIn("successfully", result.lower(), "Expected question to be added")

            # Step 2: Upload the full exam PDF
            upload_response = self.negev.upload_full_exam_pdf(
                course_id=self.course_id,
                year=self.year,
                semester=self.semester,
                moed=self.moed,
                pdf_file=self.exam_file
            )
            self.assertEqual(upload_response["status"], "success", "Exam upload should succeed")

            # Step 3: Check that the full exam PDF exists
            result = self.negev.check_exam_full_pdf(
                course_id=self.course_id,
                year=self.year,
                semester=self.semester,
                moed=self.moed
            )
            self.assertTrue(result, "Expected full exam PDF to exist after upload")

    def test_check_exam_full_pdf_not_exists(self):
        """Test: Exam full PDF does not exist when not uploaded."""
        new_course_id = "999.9.9999"
        self._open_course(self.user, new_course_id, "קורס ללא מבחן")

        result = self.negev.check_exam_full_pdf(new_course_id, self.year, self.semester, self.moed)
        self.assertFalse(result)

    def test_check_exam_full_pdf_course_not_found(self):
        """Test: Course not found should return error string."""
        fake_course_id = "999.9.9991"
        result = self.negev.check_exam_full_pdf(fake_course_id, self.year, self.semester, self.moed)

        self.assertIsInstance(result, str)
        self.assertIn("Course with ID", result)
        self.assertIn("not found", result.lower())

    @patch('Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf', return_value=None)
    @patch('Backend.BusinessLayer.Analyzer.AnalyzerFacade.AnalyzerFacade.extract_text_from_pdf_file', return_value="שאלה לדוגמה")
    def test_upload_exam_success(self, mock_extract_text, mock_process_pdf):
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
        self.assertIn("file uploaded", response["message"].lower())

    def test_upload_exam_course_not_exist(self):
        """Verify uploading an exam for a non-existent course returns an error."""
        original_check_exam_full_pdf = self.negev.courseFacade.check_exam_full_pdf
        self.negev.courseFacade.check_exam_full_pdf = MagicMock(return_value=False)

        fake_course_id = "000.0.0000"
        response = self.negev.upload_full_exam_pdf(fake_course_id, self.year, self.semester, self.moed, self.exam_file)
        self.assertEqual(response["status"], "error")
        self.assertIn("not found", response["message"].lower())

        self.negev.courseFacade.check_exam_full_pdf = original_check_exam_full_pdf

    @patch('Backend.BusinessLayer.Analyzer.AnalyzerFacade.AnalyzerFacade.extract_text_from_pdf_file', return_value="שאלה לדוגמה")
    @patch('Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf', return_value=None)
    def test_upload_exam_already_exists(self, mock_process_pdf, mock_extract_text):
        """Verify uploading an exam that already exists returns an error."""

        new_course_id = "777.7.7777"
        self._open_course(self.user, new_course_id, "קורס למבחן כפול")

        # Step 1: Add a question to create ExamData
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

        # Step 2: First upload
        upload_response_1 = self.negev.upload_full_exam_pdf(
            new_course_id, self.year, self.semester, self.moed, self.exam_file
        )
        self.assertEqual(upload_response_1["status"], "success", "First upload should succeed.")

        exam = self.negev.courseFacade.get_course(new_course_id).get_exam(self.year, self.semester, self.moed)
        assert exam.link is not None, "Expected exam link to be set after first upload"

        # Step 3: Second upload (should fail)
        upload_response_2 = self.negev.upload_full_exam_pdf(
            new_course_id, self.year, self.semester, self.moed, self.exam_file
        )
        self.assertEqual(upload_response_2["status"], "error")
        self.assertIn("already exist", upload_response_2["message"].lower())

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

    @patch('Backend.BusinessLayer.Analyzer.AnalyzerFacade.AnalyzerFacade.splitPDF')
    @patch('Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf', return_value=None)
    @patch('Backend.BusinessLayer.Analyzer.AnalyzerFacade.AnalyzerFacade.extract_text_from_pdf_file', return_value="Sample question")
    def test_split_pdf_success(self, mock_extract_text, mock_process_pdf, mock_split_pdf):
        """Test: Successfully splitting and adding questions."""

        # Step 1: Simulate two fake FileStorage-like objects
        mock_file1 = MagicMock()
        mock_file1.filename = "question1.pdf"
        mock_file1.content_type = "application/pdf"
        mock_file2 = MagicMock()
        mock_file2.filename = "question2.pdf"
        mock_file2.content_type = "application/pdf"

        # Step 2: Mock the PDF splitting to return them
        mock_split_pdf.return_value = [mock_file1, mock_file2]

        # Step 3: Call splitPDF
        self.negev.splitPDF(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            pdf_file=self.exam_file,
            line_data=[100, 200]
        )

        # Step 4: Assert that at least 2 questions were added
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

    @patch('Backend.BusinessLayer.Course.CourseFacade.CourseFacade.upload_full_exam_solution', return_value=None)
    @patch('Backend.BusinessLayer.Course.CourseFacade.CourseFacade.existFullExamSolution', return_value=False)
    def test_add_exam_solution_success(self, mock_exist, mock_upload):
        mock_file_manager = MagicMock()
        mock_file_manager.save_exam_solution_file.return_value = "mocked/path/solution.pdf"
        self.negev._file_manager = mock_file_manager

        result = self.negev.add_exam_solution(
            self.course_id, self.year, self.semester, self.moed, self.solution_file
        )

        self.assertEqual(result["status"], "success")
        self.assertIn("File uploaded", result["message"])
        self.assertTrue(result["link"].endswith(".pdf"))

    @patch('Backend.BusinessLayer.Course.CourseFacade.CourseFacade.existFullExamSolution', return_value=True)
    def test_add_exam_solution_already_exists(self, mock_exist):
        result = self.negev.add_exam_solution(
            self.course_id, self.year, self.semester, self.moed, self.solution_file
        )

        self.assertEqual(result["status"], "error")
        self.assertIn("exam_id", result["message"].lower())

    @patch('Backend.BusinessLayer.Course.CourseFacade.CourseFacade.existFullExamSolution', side_effect=Exception("DB error"))
    def test_add_exam_solution_unexpected_exception(self, mock_exist):
        result = self.negev.add_exam_solution(
            self.course_id, self.year, self.semester, self.moed, self.solution_file
        )

        self.assertEqual(result["status"], "error")
        self.assertIn("DB error", result["message"])

    @patch('Backend.BusinessLayer.Course.CourseFacade.CourseFacade.existFullExamSolution', return_value=True)
    def test_exist_full_exam_solution_true(self, mock_check):
        result = self.negev.existFullExamSolution(self.course_id, self.year, self.semester, self.moed)
        self.assertTrue(result)

    @patch('Backend.BusinessLayer.Course.CourseFacade.CourseFacade.existFullExamSolution', return_value=False)
    def test_exist_full_exam_solution_false(self, mock_check):
        result = self.negev.existFullExamSolution(self.course_id, self.year, self.semester, self.moed)
        self.assertFalse(result)

    def test_get_exam_pdf_link_success(self):
        mock_link = "files/777.1.1010/2023/אביב/א/full_exam.pdf"
        self.negev.courseFacade.get_exam_full_pdf = MagicMock(return_value=mock_link)

        result = self.negev.get_exam_pdf_link(self.course_id, self.year, self.semester, self.moed)
        self.assertEqual(result, mock_link)

    def test_get_exam_pdf_link_course_not_exist(self):
        self.negev.courseFacade.get_exam_full_pdf = MagicMock(side_effect=Exception("Course not found"))

        result = self.negev.get_exam_pdf_link(self.course_id, self.year, self.semester, self.moed)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["status"], "error")
        self.assertIn("Course not found", result["message"])

    def test_get_exam_pdf_link_exam_not_exist(self):
        self.negev.courseFacade.get_exam_full_pdf = MagicMock(
            side_effect=ExamIsNotExist(self.year, self.semester, self.moed)
        )

        result = self.negev.get_exam_pdf_link(self.course_id, self.year, self.semester, self.moed)

        self.assertEqual(result["status"], "error")
        self.assertIn("exam from year", result["message"].lower())
        self.assertIn("is not exist", result["message"].lower())

    @patch('Backend.BusinessLayer.Analyzer.AnalyzerFacade.AnalyzerFacade.perform_information_retrival_question_pdf',
           return_value=None)
    @patch('Backend.BusinessLayer.Analyzer.AnalyzerFacade.AnalyzerFacade.extract_text_from_pdf_file',
           return_value="שאלה לדוגמה")
    def test_get_exam_solution_pdf_link_success(self, mock_extract_text, mock_info):
        self.negev.add_question(
        course_id=self.course_id,
        year=self.year,
        semester=self.semester,
        moed=self.moed,
        question_number=15,
        is_american=True,
        question_topics=["מבני נתונים"],
        question_file=self.exam_file,
        answer_file=None
    )

        # שלב 2: העלאת פתרון מבחן (solution)
        upload_response = self.negev.add_exam_solution(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            solution=self.solution_file
        )
        self.assertEqual(upload_response["status"], "success")

        # שלב 3: שליפת הקישור לקובץ הפתרון
        link_response = self.negev.get_exam_solution_pdf_link(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed
        )

        self.assertIsInstance(link_response, str)
        self.assertTrue(link_response.endswith(".pdf"))
        self.assertIn("solution_exam_", link_response)

    @patch('Backend.BusinessLayer.Course.CourseFacade.CourseFacade.get_full_exam_solution', return_value="")
    def test_get_exam_solution_pdf_link_success_without_link(self, mock_get_solution):
        link_response = self.negev.get_exam_solution_pdf_link(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed
        )

        self.assertIsInstance(link_response, str)
        self.assertEqual(link_response, "")

    def test_get_exam_solution_pdf_link_failure_invalid_course(self):
        response = self.negev.get_exam_solution_pdf_link("000.0.0000", self.year, self.semester, self.moed)
        self.assertEqual(response["status"], "error")
        self.assertIn("not found", response["message"].lower())

    def test_handle_download_all_exams_zip_success(self):
        expected_folder = "mocked_folder.zip"
        expected_exams = ["exam1.pdf", "exam2.pdf"]

        self.negev._course_facade.handleDownloadAllExamsZip = MagicMock(return_value=(expected_folder, expected_exams))

        folder, exams = self.negev.handleDownloadAllExamsZip(self.course_id)

        self.assertEqual(folder, expected_folder)
        self.assertEqual(exams, expected_exams)

    def test_handle_download_all_exams_zip_course_not_found(self):
        self.negev._course_facade.handleDownloadAllExamsZip = MagicMock(side_effect=Exception("Course not found"))

        with self.assertRaises(Exception) as context:
            self.negev.handleDownloadAllExamsZip("000.0.0000")

        self.assertIn("Course not found", str(context.exception))
        self.assertIn("Failed to search questions", str(context.exception))

    def test_handle_download_all_exams_zip_unexpected_error(self):
        self.negev._course_facade.handleDownloadAllExamsZip = MagicMock(side_effect=Exception("Disk full"))

        with self.assertRaises(Exception) as context:
            self.negev.handleDownloadAllExamsZip(self.course_id)

        self.assertIn("Disk full", str(context.exception))