import unittest
from unittest.mock import patch, MagicMock
import json
import re
from datetime import datetime

# Adjust these imports according to your project structure.
from Backend.BusinessLayer.Course.CourseFacade import CourseFacade
from Backend.BusinessLayer.Course.Course import Course
from Backend.BusinessLayer.Util.Exceptions import (
    CourseIsNotExist,
    CourseAlreadyExists,
    InvalidCourseIdFormat
)
from Backend.DataLayer.DTOs.CourseDTO import CourseDTO
from Backend.DataLayer.DTOs.SearchDTO import SearchDTO
from Backend.BusinessLayer.Course.enums import Semester, Moed


class TestCourseFacade(unittest.TestCase):
    def setUp(self):
        # Create a new facade instance and clear any existing courses.
        self.facade = CourseFacade()
        self.facade.courses = {}
        self.course_id = "123.4.5678"
        self.course_name = "קורס דוגמה"
        self.course_topics = {"מתמטיקה", "פיזיקה"}
        # Create a dummy course (a MagicMock that implements Course methods)
        self.dummy_course = MagicMock(spec=Course)
        self.dummy_course.get_id.return_value = self.course_id
        self.dummy_course.get_name.return_value = self.course_name
        # For methods that delegate to the course (e.g. get_exam) we use MagicMock attributes.
        self.facade.courses[self.course_id] = self.dummy_course

    def test_register_to_course(self):
        # Ensure that get_course returns the dummy course.
        self.facade.get_course = MagicMock(return_value=self.dummy_course)
        self.dummy_course.add_student = MagicMock()
        self.facade.register_to_course(self.course_id, "user1")
        self.dummy_course.add_student.assert_called_once_with("user1")

    @patch("Backend.DataLayer.Questions.QuestionRepository.QuestionRepository.get_questions_by_dto")
    def test_get_questions_dto_by_search_dtos(self, mock_get_by_dto):
        dummy_search_dto = MagicMock(spec=SearchDTO)
        # Set the required attribute
        dummy_search_dto.course_id = "course1"

        dummy_question = MagicMock()
        dummy_question.to_dto.return_value = {"id": "q1"}
        mock_get_by_dto.return_value = dummy_question

        result = self.facade.get_questions_dto_by_search_dtos([dummy_search_dto])
        mock_get_by_dto.assert_called_once_with(dummy_search_dto)
        self.assertEqual(result, [{"id": "q1"}])

    @patch("Backend.DataLayer.Questions.QuestionRepository.QuestionRepository.get_questions_by_ids_list")
    def test_get_questions_dto_by_ids(self, mock_get_by_ids_list):
        dummy_question = MagicMock()
        dummy_question.to_dto.return_value = {"id": "q1"}
        mock_get_by_ids_list.return_value = [dummy_question]

        result = self.facade.get_questions_dto_by_ids(["q1"], self.course_id)
        mock_get_by_ids_list.assert_called_once_with(["q1"])
        self.assertEqual(result, [{"id": "q1"}])

    def test_handleDownloadAllExamsZip(self):
        # Ensure get_course returns the dummy course.
        self.facade.get_course = MagicMock(return_value=self.dummy_course)
        # Set the dummy course's handleDownloadAllExamsZip method to return a tuple.
        self.dummy_course.handleDownloadAllExamsZip.return_value = ("folder1", {"exam1": "link1"})
        folder, exams = self.facade.handleDownloadAllExamsZip(self.course_id)
        self.dummy_course.handleDownloadAllExamsZip.assert_called_once()
        self.assertEqual(folder, "folder1")
        self.assertEqual(exams, {"exam1": "link1"})

    def test_remove_student_from_course(self):
        # Ensure get_course returns the dummy course.
        self.facade.get_course = MagicMock(return_value=self.dummy_course)
        self.dummy_course.remove_student = MagicMock()
        self.facade.remove_student_from_course(self.course_id, "user1")
        self.dummy_course.remove_student.assert_called_once_with("user1")

    @patch("Backend.BusinessLayer.Course.Course.Course.create")
    def test_open_course(self, mock_course_create):
        new_course = MagicMock(spec=Course)
        mock_course_create.return_value = new_course
        new_course_id = "234.5.6789"
        new_course_topics = {"topicX", "topicY"}
        if new_course_id in self.facade.courses:
            del self.facade.courses[new_course_id]
        self.facade.open_course(new_course_id, "חדש", new_course_topics)
        expected_topics = set(new_course_topics).union({"אחר"})
        mock_course_create.assert_called_once_with(course_id=new_course_id, name="חדש", course_topics=expected_topics)
        self.assertIn(new_course_id, self.facade.courses)
        self.assertEqual(self.facade.courses[new_course_id], new_course)

    def test_open_course_possibility_valid(self):
        # When get_course returns None (course does not exist) and parameters are valid.
        self.facade.get_course = MagicMock(return_value=None)
        result = self.facade.open_course_possibility("123.4.5678", "קורס תקין")
        self.assertTrue(result)

    def test_open_course_possibility_already_exists(self):
        self.facade.get_course = MagicMock(return_value=self.dummy_course)
        with self.assertRaises(CourseAlreadyExists):
            self.facade.open_course_possibility(self.course_id, self.course_name)

    def test_open_course_possibility_invalid_id(self):
        self.facade.get_course = MagicMock(return_value=None)
        with self.assertRaises(InvalidCourseIdFormat):
            self.facade.open_course_possibility("invalid_id", self.course_name)

    @patch("Backend.DataLayer.CourseData.CourseRepository.CourseRepository.delete_course")
    def test_remove_course(self, mock_delete_course):
        # Ensure the course exists in the facade's courses dictionary.
        self.facade.courses[self.course_id] = self.dummy_course
        # Also override get_course to return the dummy course.
        self.facade.get_course = MagicMock(return_value=self.dummy_course)
        self.facade.remove_course(self.course_id)
        self.assertNotIn(self.course_id, self.facade.courses)
        mock_delete_course.assert_called_once_with(course_id=self.course_id)

    def test_get_question_id(self):
        self.facade.get_course = MagicMock(return_value=self.dummy_course)
        self.dummy_course.get_question_id.return_value = "q_id"
        result = self.facade.get_question_id(self.course_id, 2025, "אביב", "א", 1)
        self.dummy_course.get_question_id.assert_called_once_with(2025, "אביב", "א", 1)
        self.assertEqual(result, "q_id")

    def test_get_question_id_and_path(self):
        # Make sure that get_course returns the dummy course.
        self.facade.get_course = MagicMock(return_value=self.dummy_course)
        # Set the dummy course's get_question_id_and_path method to return a known value.
        self.dummy_course.get_question_id_and_path.return_value = ("a_path", "q_id")
        # Call the facade method.
        result = self.facade.get_question_id_and_path(self.course_id, 2025, "אביב", "א", 1)
        # Assert that the dummy course's method was called with the expected parameters.
        self.dummy_course.get_question_id_and_path.assert_called_once_with(2025, "אביב", "א", 1)
        # Check that the returned value is as expected.
        self.assertEqual(result, ("a_path", "q_id"))

    @patch("Backend.DataLayer.CourseData.CourseRepository.CourseRepository.get_all_courses")
    def test_get_all_courses(self, mock_get_all_courses):
        dummy_course1 = MagicMock(spec=Course)
        dummy_course1.get_id.return_value = "id1"
        dummy_course1.get_name.return_value = "Name1"
        dummy_course2 = MagicMock(spec=Course)
        dummy_course2.get_id.return_value = "id2"
        dummy_course2.get_name.return_value = "Name2"
        mock_get_all_courses.return_value = [dummy_course1, dummy_course2]
        result = self.facade.get_all_courses()
        self.assertEqual(len(result), 2)
        for dto in result:
            self.assertIsInstance(dto, CourseDTO)

    def test_get_course_DTO(self):
        self.dummy_course.get_name.return_value = self.course_name
        result = self.facade.get_course_DTO(self.course_id)
        self.assertIsInstance(result, CourseDTO)
        # Use getter methods to verify the values
        self.assertEqual(result.get_course_id(), self.course_id)
        self.assertEqual(result.get_name(), self.course_name)

    def test_get_courses_DTO(self):
        self.facade.get_course = MagicMock(return_value=self.dummy_course)
        result = self.facade.get_courses_DTO([self.course_id])
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], CourseDTO)

    def test_get_course_topics(self):
        # Ensure get_course returns the dummy course.
        self.facade.get_course = MagicMock(return_value=self.dummy_course)
        self.dummy_course.get_topics.return_value = self.course_topics
        result = self.facade.get_course_topics(self.course_id)
        self.dummy_course.get_topics.assert_called_once()
        self.assertEqual(result, self.course_topics)

    def test_check_valid_question(self):
        # Ensure that get_course returns the dummy course.
        self.facade.get_course = MagicMock(return_value=self.dummy_course)
        # Set the dummy course's check_valid_question to return a known value.
        self.dummy_course.check_valid_question.return_value = ("result", "exam_id")
        # Call the facade method.
        result = self.facade.check_valid_question(self.course_id, 2025, "אביב", "א", 1, "text")
        # Verify that the dummy course's check_valid_question was called with the expected arguments.
        self.dummy_course.check_valid_question.assert_called_once_with(
            year=2025,
            semester=Semester("אביב"),
            moed=Moed("א"),
            question_number=1,
            question_text="text"
        )
        # Check the result.
        self.assertEqual(result, ("result", "exam_id"))

    def test_add_question(self):
        self.dummy_course.add_question.return_value = "q_new"
        result = self.facade.add_question(self.course_id, 2025, "אביב", "א", 1, True, ["topic1"], "q.pdf", "a.pdf", "question text")
        self.dummy_course.add_question.assert_called_once_with(2025, "אביב", "א", 1, True, ["topic1"], "q.pdf", "a.pdf", "question text")
        self.assertEqual(result, "q_new")

    def test_upload_full_exam_pdf(self):
        dummy_exam = MagicMock()
        dummy_exam.upload_full_exam_pdf.return_value = {"status": "success", "link": "new_exam.pdf"}
        # Ensure get_course returns a dummy course that has the upload_full_exam_pdf method.
        self.facade.get_course = MagicMock(return_value=self.dummy_course)
        # Set the dummy course's upload_full_exam_pdf method.
        self.dummy_course.upload_full_exam_pdf = MagicMock(return_value={"status": "success", "link": "new_exam.pdf"})

        result = self.facade.upload_full_exam_pdf(self.course_id, 2025, "אביב", "א", "new_exam.pdf")

        self.dummy_course.upload_full_exam_pdf.assert_called_once_with(2025, "אביב", "א", "new_exam.pdf")
        self.assertEqual(result["status"], "success")

    def test_uploadSolution(self):
        # Ensure get_course returns the dummy course.
        self.facade.get_course = MagicMock(return_value=self.dummy_course)
        # Set the dummy course's uploadSolution method to return a success result.
        self.dummy_course.uploadSolution.return_value = {"status": "success", "link": "new_answer.pdf"}

        result = self.facade.uploadSolution(self.course_id, 2025, "אביב", "א", 1, "new_answer.pdf")

        # Assert that the dummy course's uploadSolution was called with the correct arguments.
        self.dummy_course.uploadSolution.assert_called_once_with(2025, "אביב", "א", 1, "new_answer.pdf")
        self.assertEqual(result["status"], "success")

    def test_add_topic_to_question(self):
        dummy_exam = MagicMock()
        dummy_question = MagicMock()
        dummy_question.add_topic_to_question = MagicMock()
        dummy_exam.get_question.return_value = dummy_question
        self.dummy_course.get_exam.return_value = dummy_exam
        self.facade.add_topic_to_question(self.course_id, 2025, "אביב", "א", 1, "new_topic")
        dummy_question.add_topic_to_question.assert_called_once_with("new_topic")

    def test_remove_topic_from_question(self):
        dummy_exam = MagicMock()
        dummy_question = MagicMock()
        dummy_question.remove_topic_from_question = MagicMock()
        dummy_exam.get_question.return_value = dummy_question
        # Ensure that get_course returns the dummy course that has get_exam defined.
        self.facade.get_course = MagicMock(return_value=self.dummy_course)
        self.dummy_course.get_exam.return_value = dummy_exam

        self.facade.remove_topic_from_question(self.course_id, 2025, "אביב", "א", 1, "topic_to_remove")
        dummy_question.remove_topic_from_question.assert_called_once_with("topic_to_remove")

    def test_search_question_by_specifics(self):
        dummy_exam = MagicMock()
        dummy_exam.get_questions_by_specific.return_value = [{"id": "q1"}]
        # When course.get_questions_by_specific is called, we simulate a list of question dtos.
        self.dummy_course.get_questions_by_specific = MagicMock(return_value=[{"id": "q1"}])
        self.dummy_course.get_exam.return_value = dummy_exam
        self.facade.get_course = MagicMock(return_value=self.dummy_course)
        result = self.facade.search_question_by_specifics(self.course_id, 2025, "אביב", "א", 1)
        self.assertEqual(result, [{"id": "q1"}])

    def test_search_questions_by_topic(self):
        dummy_exam = MagicMock()
        dummy_question = MagicMock()
        dummy_question.get_question_topics.return_value = ["topic1", "topic2"]
        dummy_question.to_dto.return_value = {"id": "q1"}
        dummy_exam.get_all_exam_question.return_value = [dummy_question]
        self.dummy_course.get_all_exams.return_value = [dummy_exam]
        self.facade.get_course = MagicMock(return_value=self.dummy_course)
        result = self.facade.search_questions_by_topic(self.course_id, "topic1")
        self.assertEqual(result, [{"id": "q1"}])

    def test_get_questions_by_keywords(self):
        # Make sure that get_course returns the dummy course.
        self.facade.get_course = MagicMock(return_value=self.dummy_course)
        self.dummy_course.get_questions_by_keywords.return_value = [{"id": "q1"}]
        result = self.facade.get_questions_by_keywords(self.course_id, ["keyword"])
        self.dummy_course.get_questions_by_keywords.assert_called_once_with(["keyword"])
        self.assertEqual(result, [{"id": "q1"}])

    @patch("Backend.DataLayer.Questions.QuestionRepository.QuestionRepository.checkQuestionLeft")
    def test_checkQuestionLeft(self, mock_checkQuestionLeft):
        mock_checkQuestionLeft.return_value = True
        # Force get_course to return the dummy course, and set its get_exam to return None.
        self.facade.get_course = MagicMock(return_value=self.dummy_course)
        self.dummy_course.get_exam = MagicMock(return_value=None)
        result, exam_id = self.facade.checkQuestionLeft(self.course_id, 2025, "אביב", "א")
        mock_checkQuestionLeft.assert_called_once_with(None)
        self.assertTrue(result)
        self.assertIsNone(exam_id)

    def test_edit_question_topic(self):
        # Ensure get_course returns the dummy course.
        self.facade.get_course = MagicMock(return_value=self.dummy_course)
        # Set the dummy course's edit_question_topic method return value.
        self.dummy_course.edit_question_topic.return_value = "edited_topic"
        # Call the facade method.
        result = self.facade.edit_question_topic(self.course_id, 2025, "אביב", "א", 1, ["new_topic"])
        # Assert that the course's edit_question_topic method was called with the expected arguments.
        self.dummy_course.edit_question_topic.assert_called_once_with(2025, "אביב", "א", 1, ["new_topic"])
        # Assert that the returned value is as expected.
        self.assertEqual(result, "edited_topic")


if __name__ == "__main__":
    unittest.main()
