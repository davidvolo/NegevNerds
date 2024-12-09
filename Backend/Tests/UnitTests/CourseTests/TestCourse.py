import unittest
from Backend.BusinessLayer.Course.Course import Course
from Backend.BusinessLayer.Util.Exceptions import *
from Backend.DataLayer.QuestionDTO import *


class TestCourse(unittest.TestCase):

    def setUp(self):
        """
        Set up test environment before each test.
        """
        self.course_id = 101
        self.course_name = "Algorithms"
        self.syllabus = "Introduction to Algorithms"
        self.course_topics = ["Data Structures", "Graph Theory", "Sorting Algorithms"]
        self.course = Course(self.course_id, self.course_name, self.syllabus, self.course_topics)

    def test_add_exam_success(self):
        """
        Test adding an exam to the course.
        """
        self.course.add_exam(self.course_name, "http://example.com/exam", 2024, "Spring", "A")
        exam = self.course.get_exam(2024, "Spring", "A")
        self.assertIsNotNone(exam)
        self.assertEqual(exam.course_name, self.course_name)

    def test_add_exam_already_exists(self):
        """
        Test adding an exam that already exists.
        """
        self.course.add_exam(self.course_name, "http://example.com/exam", 2024, "Spring", "A")
        with self.assertRaises(ExamAlreadyExists):
            self.course.add_exam(self.course_name, "http://example.com/exam", 2024, "Spring", "A")

    def test_get_exam_not_exist(self):
        """
        Test retrieving an exam that does not exist.
        """
        with self.assertRaises(ExamIsNotExist):
            self.course.get_exam(2024, "Spring", "A")

    def test_remove_exam_success(self):
        """
        Test removing an existing exam.
        """
        self.course.add_exam(self.course_name, "http://example.com/exam", 2024, "Spring", "A")
        self.course.remove_exam(2024, "Spring", "A")
        with self.assertRaises(ExamIsNotExist):
            self.course.get_exam(2024, "Spring", "A")

    def test_remove_exam_not_exist(self):
        """
        Test removing an exam that does not exist.
        """
        with self.assertRaises(ExamIsNotExist):
            self.course.remove_exam(2024, "Spring", "A")

    def test_add_question_to_existing_exam(self):
        """
        Test adding a question to an existing exam.
        """
        # Add exam first
        self.course.add_exam(self.course_name, "http://example.com/exam", 2024, "Spring", "A")

        # Create a question DTO
        question_dto = QuestionDTO(
            question_id=1,
            year=2024,
            semester="Spring",
            moed="A",
            question_number=1,
            question_topics=["Sorting Algorithms"],
            is_american=False,
            link_to_question="http://example.com/question1"
        )

        # Add question to the exam
        self.course.add_question(2024, "Spring", "A", question_dto)

        # Verify question was added
        exam = self.course.get_exam(2024, "Spring", "A")
        self.assertIn(1, exam.questions_list)

    def test_add_question_with_invalid_topic(self):
        """
        Test adding a question with an invalid topic.
        """

        self.course.add_exam(self.course_name, "http://example.com/exam", 2024, "Spring", "A")
        question_dto = QuestionDTO(
            question_id=1,
            year=2024,
            semester="Spring",
            moed="A",
            question_number=1,
            question_topics=["Invalid Topic"],
            is_american=False,
            link_to_question="http://example.com/question1"
        )
        with self.assertRaises(TopicNotFound):
            self.course.add_question(2024, "Spring", "A", question_dto)

    def test_edit_exam_course_name(self):
        """
        Test editing the course name of an exam.
        """
        self.course.add_exam(self.course_name, "http://example.com/exam", 2024, "Spring", "A")
        self.course.edit_exam_course_name(2024, "Spring", "A", "New Algorithms")
        exam = self.course.get_exam(2024, "Spring", "A")
        self.assertEqual(exam.course_name, "New Algorithms")

    def test_edit_exam_year(self):
        """
        Test editing the year of an exam.
        """
        self.course.add_exam(self.course_name, "http://example.com/exam", 2024, "Spring", "A")
        self.course.edit_exam_year(2024, "Spring", "A", 2025)
        with self.assertRaises(ExamIsNotExist):
            self.course.get_exam(2024, "Spring", "A")
        exam = self.course.get_exam(2025, "Spring", "A")
        self.assertIsNotNone(exam)

    def test_get_all_exams(self):
        """
        Test retrieving all exams from the course.
        """
        self.course.add_exam(self.course_name, "http://example.com/exam1", 2024, "Spring", "A")
        self.course.add_exam(self.course_name, "http://example.com/exam2", 2024, "Spring", "B")
        all_exams = self.course.get_all_exams()
        self.assertEqual(len(all_exams), 2)


if __name__ == "__main__":
    unittest.main()
