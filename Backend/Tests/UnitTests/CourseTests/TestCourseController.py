import unittest
from Backend.BusinessLayer.Course.CourseFacade import CourseController
from Backend.BusinessLayer.Course.Course import Course
from Backend.BusinessLayer.Util.Exceptions import CourseIsNotExist, CourseAlreadyExists


class TestCourseController(unittest.TestCase):
    def setUp(self):
        """
        Set up a CourseController instance and mock data for testing.
        """
        self.controller = CourseController()
        self.course_id = "CS101"
        self.course_name = "Computer Science Basics"
        self.syllabus = "Intro to CS"
        self.course_topics = ["Algorithms", "Data Structures"]

        self.controller.open_course(self.course_id, self.course_name, self.syllabus, self.course_topics)

    def test_open_course_success(self):
        """
        Test opening a new course successfully.
        """
        new_course_id = "MATH101"
        self.controller.open_course(new_course_id, "Mathematics Basics", "Intro to Math", ["Calculus", "Algebra"])
        self.assertIn(new_course_id, self.controller.courses)

    def test_open_course_already_exists(self):
        """
        Test opening a course that already exists raises an exception.
        """
        with self.assertRaises(CourseAlreadyExists):
            self.controller.open_course(self.course_id, self.course_name, self.syllabus, self.course_topics)

    def test_get_course_success(self):
        """
        Test retrieving an existing course.
        """
        course = self.controller.get_course(self.course_id)
        self.assertIsInstance(course, Course)
        self.assertEqual(course.name, self.course_name)

    def test_get_course_not_exist(self):
        """
        Test retrieving a course that does not exist raises an exception.
        """
        with self.assertRaises(CourseIsNotExist):
            self.controller.get_course("INVALID_ID")

    def test_add_exam_to_course(self):
        """
        Test adding an exam to an existing course.
        """
        self.controller.add_exam_to_course(self.course_id, "Algorithms Exam", "http://example.com/exam", 2024, "Spring", "A")
        course = self.controller.get_course(self.course_id)
        self.assertEqual(len(course.get_all_exams()), 1)

    def test_remove_course_success(self):
        """
        Test removing an existing course.
        """
        self.controller.remove_course(self.course_id)
        with self.assertRaises(CourseIsNotExist):
            self.controller.get_course(self.course_id)

    def test_remove_course_not_exist(self):
        """
        Test removing a non-existing course raises an exception.
        """
        with self.assertRaises(CourseIsNotExist):
            self.controller.remove_course("INVALID_ID")


if __name__ == "__main__":
    unittest.main()
