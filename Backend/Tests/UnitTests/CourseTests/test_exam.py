import unittest
from unittest.mock import patch, MagicMock

from Backend.BusinessLayer.Course.enums import Moed, Semester
from Backend.BusinessLayer.Util.Exceptions import (
    QuestionAlreadyInExam,
    QuestionDoesNotMeetExamFields,
    QuestionNotFound
)
from Backend.DataLayer.DTOs.ExamDTO import ExamDTO
from Backend.BusinessLayer.Course.Question import Question

# יש להתאים את הנתיב בהתאם למיקום המחלקה Exam
from Backend.BusinessLayer.Course.Exam import Exam


class TestExam(unittest.TestCase):
    def setUp(self):
        self.exam_id = "exam1"
        self.course_id = "course1"
        self.link = "http://example.com/exam.pdf"
        self.year = 2025
        self.semester_val = Semester.SPRING
        self.moed_val = Moed.A
        self.exam = Exam(
            exam_id=self.exam_id,
            course_id=self.course_id,
            link=self.link,
            year=self.year,
            semester=self.semester_val,
            moed=self.moed_val
        )

    @patch("Backend.DataLayer.ExamData.ExamRepository.ExamRepository.add_exam")
    def test_create(self, mock_add_exam):
        exam = Exam.create(
            exam_id=self.exam_id,
            course_id=self.course_id,
            link=self.link,
            year=self.year,
            semester=self.semester_val,
            moed=self.moed_val,
        )
        mock_add_exam.assert_called_once()
        self.assertEqual(exam.id, self.exam_id)

    def test_to_dto(self):
        # ניצור שאלה בדויה עם מתודת to_dict
        dummy_question = MagicMock()
        dummy_question.to_dict.return_value = {"id": "q1", "question_text": "dummy"}
        self.exam.questions_list[1] = dummy_question

        dto = self.exam.to_dto()
        self.assertIsInstance(dto, ExamDTO)
        self.assertEqual(dto.exam_id, self.exam_id)
        self.assertEqual(dto.course_id, self.course_id)
        self.assertEqual(dto.link, self.link)
        self.assertEqual(dto.year, self.year)
        self.assertEqual(dto.semester, self.exam.semester)
        self.assertEqual(dto.moed, self.exam.moed)
        self.assertEqual(dto.questions_list, [{"id": "q1", "question_text": "dummy"}])

    def test_generate_question_id(self):
        qid = self.exam.generate_question_id()
        self.assertTrue(qid.startswith("question"))

    @patch("Backend.BusinessLayer.Course.Question.Question.create")
    def test_add_question_success(self, mock_question_create):
        dummy_question = MagicMock()
        dummy_question.id = "q_dummy"
        mock_question_create.return_value = dummy_question

        returned_id = self.exam.add_question(
            question_number=1,
            is_american=True,
            question_topics=["topic1"],
            pdf__question_path="question.pdf",
            pdf__answer_path="answer.pdf",
            question_text="What is unit testing?"
        )
        self.assertIn(1, self.exam.questions_list)
        self.assertEqual(returned_id, "q_dummy")

    @patch("Backend.BusinessLayer.Course.Question.Question.create")
    def test_add_question_failure(self, mock_question_create):
        mock_question_create.return_value = None
        with self.assertRaises(Exception):
            self.exam.add_question(
                question_number=2,
                is_american=False,
                question_topics=["topic2"],
                pdf__question_path="q2.pdf",
                pdf__answer_path="a2.pdf",
                question_text="What is integration testing?"
            )

    @patch("Backend.DataLayer.Questions.QuestionRepository.QuestionRepository.is_exist")
    def test_check_add_question_possibility_valid(self, mock_is_exist):
        mock_is_exist.return_value = False
        result = self.exam.check_add_question_possibility(
            year=self.year,
            semester=self.exam.semester,
            moed=self.exam.moed,
            question_number=1
        )
        self.assertTrue(result)

    @patch("Backend.DataLayer.Questions.QuestionRepository.QuestionRepository.is_exist")
    def test_check_add_question_possibility_already_exists(self, mock_is_exist):
        mock_is_exist.return_value = True
        with self.assertRaises(QuestionAlreadyInExam):
            self.exam.check_add_question_possibility(
                year=self.year,
                semester=self.exam.semester,
                moed=self.exam.moed,
                question_number=1
            )

    def test_check_add_question_possibility_fields_mismatch(self):
        # העברת שנה שגויה כדי לעורר חריגה
        with self.assertRaises(QuestionDoesNotMeetExamFields):
            self.exam.check_add_question_possibility(
                year=self.year - 1,
                semester=self.exam.semester,
                moed=self.exam.moed,
                question_number=1
            )

    def test_get_question_path_success(self):
        dummy_question = MagicMock()
        dummy_question.link_to_question = "question_path.pdf"
        with patch.object(self.exam, "get_question", return_value=dummy_question):
            result = self.exam.get_question_path(1)
            self.assertEqual(result, "question_path.pdf")

    def test_get_question_path_not_found(self):
        with patch.object(self.exam, "get_question", return_value=None):
            with self.assertRaises(QuestionNotFound):
                self.exam.get_question_path(99)

    def test_get_answer_path_success(self):
        dummy_question = MagicMock()
        dummy_question.link_to_answer = "answer_path.pdf"
        with patch.object(self.exam, "get_question", return_value=dummy_question):
            result = self.exam.get_answer_path(1)
            self.assertEqual(result, "answer_path.pdf")

    def test_get_answer_path_not_found(self):
        with patch.object(self.exam, "get_question", return_value=None):
            with self.assertRaises(QuestionNotFound):
                self.exam.get_answer_path(99)

    def test_get_question_id_success(self):
        dummy_question = MagicMock()
        dummy_question.id = "q1"
        with patch.object(self.exam, "get_question", return_value=dummy_question):
            result = self.exam.get_question_id(1)
            self.assertEqual(result, "q1")

    def test_get_question_id_not_found(self):
        with patch.object(self.exam, "get_question", return_value=None):
            with self.assertRaises(QuestionNotFound):
                self.exam.get_question_id(1)

    def test_get_question_id_and_path(self):
        dummy_question = MagicMock()
        dummy_question.link_to_answer = "answer_path"
        dummy_question.id = "q1"
        with patch.object(self.exam, "get_question", return_value=dummy_question):
            link, qid = self.exam.get_question_id_and_path(1)
            self.assertEqual(link, "answer_path")
            self.assertEqual(qid, "q1")

    @patch("Backend.DataLayer.Questions.QuestionRepository.QuestionRepository.get_question_by_exam_id")
    def test_get_all_exam_question(self, mock_get_by_exam_id):
        dummy_questions = [MagicMock(), MagicMock()]
        mock_get_by_exam_id.return_value = dummy_questions
        result = self.exam.get_all_exam_question()
        self.assertEqual(result, dummy_questions)

    @patch("Backend.DataLayer.ExamData.ExamRepository.ExamRepository.update_exam_link")
    def test_upload_full_exam_pdf_success(self, mock_update_exam_link):
        new_link = "http://newlink.com/exam.pdf"
        result = self.exam.upload_full_exam_pdf(new_link)
        self.assertEqual(self.exam.link, new_link)
        mock_update_exam_link.assert_called_once_with(self.exam.id, new_link)
        self.assertEqual(result["status"], "success")

    @patch("Backend.DataLayer.ExamData.ExamRepository.ExamRepository.update_exam_link", side_effect=Exception("db error"))
    def test_upload_full_exam_pdf_failure(self, mock_update_exam_link):
        new_link = "http://newlink.com/exam.pdf"
        result = self.exam.upload_full_exam_pdf(new_link)
        self.assertEqual(result["status"], "error")
        self.assertIn("db error", result["message"])

    @patch("Backend.DataLayer.Questions.QuestionRepository.QuestionRepository.delete_question")
    def test_remove_question_success(self, mock_delete_question):
        dummy_question = MagicMock()
        dummy_question.id = "q_remove"
        self.exam.questions_list[1] = dummy_question
        self.exam.remove_question(1)
        # Update expectation: expect the keyword argument 'question_id'
        mock_delete_question.assert_called_once_with(question_id="q_remove")
        self.assertNotIn(1, self.exam.questions_list)

    def test_remove_question_not_found(self):
        with self.assertRaises(QuestionNotFound):
            self.exam.remove_question(99)

    def test_get_question_existing(self):
        dummy_question = MagicMock()
        self.exam.questions_list[1] = dummy_question
        result = self.exam.get_question(1)
        self.assertEqual(result, dummy_question)

    @patch("Backend.DataLayer.Questions.QuestionRepository.QuestionRepository.get_question_by_number")
    def test_get_question_not_existing(self, mock_get_by_number):
        dummy_question = MagicMock()
        mock_get_by_number.return_value = dummy_question
        result = self.exam.get_question(2)
        self.assertEqual(result, dummy_question)
        self.assertIn(2, self.exam.questions_list)

    def test_get_questions_by_keywords(self):
        dummy_question1 = MagicMock()
        dummy_question1.get_question_topics.return_value = ["math", "algebra"]
        dummy_question2 = MagicMock()
        dummy_question2.get_question_topics.return_value = ["science"]
        self.exam.questions_list = {1: dummy_question1, 2: dummy_question2}
        result = self.exam.get_questions_by_keywords(["math"])
        self.assertIn(dummy_question1, result)
        self.assertNotIn(dummy_question2, result)

    def test_edit_link(self):
        new_link = "http://updatedlink.com/exam.pdf"
        self.exam.edit_link(new_link)
        self.assertEqual(self.exam.link, new_link)

    def test_edit_year_valid(self):
        self.exam.edit_year(2030)
        self.assertEqual(self.exam.year, 2030)

    def test_edit_year_invalid(self):
        with self.assertRaises(ValueError):
            self.exam.edit_year("2030")

    @patch("Backend.DataLayer.Questions.QuestionRepository.QuestionRepository.get_question_by_exam_id")
    def test_get_questions_by_specific_all(self, mock_get_by_exam_id):
        dummy_question = MagicMock()
        dummy_dto = {"id": "q1", "dummy": "value"}
        dummy_question.to_dto.return_value = dummy_dto
        mock_get_by_exam_id.return_value = [dummy_question]
        result = self.exam.get_questions_by_specific()
        self.assertEqual(result, [dummy_dto])

    def test_get_questions_by_specific_single(self):
        dummy_question = MagicMock()
        dummy_dto = {"id": "q2", "dummy": "value2"}
        dummy_question.to_dto.return_value = dummy_dto
        with patch.object(self.exam, "get_question", return_value=dummy_question):
            result = self.exam.get_questions_by_specific(question_number=2)
            self.assertEqual(result, [dummy_dto])

    def test_edit_question_topic(self):
        dummy_question = MagicMock()
        dummy_question.edit_question_topic.return_value = "edited"
        with patch.object(self.exam, "get_question", return_value=dummy_question):
            result = self.exam.edit_question_topic(1, ["new_topic"])
            dummy_question.edit_question_topic.assert_called_once_with(["new_topic"])
            self.assertEqual(result, "edited")

    def test_checkQuestionAvailability_true(self):
        with patch.object(self.exam, "get_question", return_value=None):
            result = self.exam.checkQuestionAvailability(new_question_number=3)
            self.assertTrue(result)

    def test_checkQuestionAvailability_false(self):
        dummy_question = MagicMock()
        with patch.object(self.exam, "get_question", return_value=dummy_question):
            result = self.exam.checkQuestionAvailability(new_question_number=3)
            self.assertFalse(result)

    def test_edit_question_details(self):
        dummy_question = MagicMock()
        dummy_question.edit_question_details.return_value = "edited_details"
        with patch.object(self.exam, "get_question", return_value=dummy_question):
            result = self.exam.edit_question_details(
                old_question_number=1,
                new_year=2030,
                new_semester="SPRING",
                new_moed="א",
                new_question_number=2,
                exam_id=self.exam_id,
                question_new_path="new_q.pdf",
                solution_new_path="new_a.pdf"
            )
            dummy_question.edit_question_details.assert_called_once_with(
                2030, "SPRING", "א", 2, self.exam_id, "new_q.pdf", "new_a.pdf"
            )
            self.assertEqual(result, "edited_details")

    def test_str(self):
        self.exam.questions_list = {1: MagicMock(), 2: MagicMock()}
        s = str(self.exam)
        self.assertIn(self.exam_id, s)
        self.assertIn(self.course_id, s)
        self.assertIn(str(self.year), s)
        self.assertIn("2", s)


if __name__ == "__main__":
    unittest.main()
