import unittest
from Backend.BusinessLayer.Course.Course import Course
from Backend.BusinessLayer.Util.Exceptions import *
from Backend.BusinessLayer.Course.Exam import Exam
from Backend.BusinessLayer.Course.enums import Semester, Moed


class TestCourse(unittest.TestCase):

    def setUp(self):
        """Create a course instance for testing"""
        self.course = Course(course_id=1, name="Math", syllabus="Syllabus Content",
                             course_topics=["Algebra", "Calculus"])

    def test_add_course_topic(self):
        """Test adding a new course topic"""
        self.course.add_course_topic("Geometry")
        self.assertIn("Geometry", self.course.get_topics())

    def test_remove_course_topic(self):
        """Test removing an existing course topic"""
        self.course.remove_course_topic("Calculus")
        self.assertNotIn("Calculus", self.course.get_topics())

    def test_add_student(self):
        """Test adding a student to the course"""
        self.course.add_student(1001)
        self.assertIn(1001, self.course.get_students())

    def test_remove_student(self):
        """Test removing a student from the course"""
        self.course.add_student(1002)
        self.course.remove_student(1002)
        self.assertNotIn(1002, self.course.get_students())

    def test_add_exam(self):
        """Test adding an exam to the course"""
        self.course.add_exam(course_name="Midterm", link="exam_link", year=2024, semester=Semester.FALL, moed=Moed.A)
        exams = self.course.get_exams(2024, Semester.FALL, Moed.A)
        self.assertEqual(len(exams), 1)
        self.assertEqual(exams[0].course_name, "Midterm")

    def test_remove_exam(self):
        """Test removing an exam from the course"""
        self.course.add_exam(course_name="Midterm", link="exam_link", year=2024, semester=Semester.FALL, moed=Moed.A)
        self.course.remove_exam(2024, Semester.FALL, Moed.A)
        exams = self.course.get_exams(2024, Semester.FALL, Moed.A)
        self.assertEqual(len(exams), 0)

    def test_add_manager(self):
        """Test adding a manager to the course"""
        self.course.add_manager(1, "Manager1")
        self.assertIn(1, self.course.get_managers())

    def test_remove_manager(self):
        """Test removing a manager from the course"""
        self.course.add_manager(1, "Manager1")
        self.course.remove_manager(1)
        self.assertNotIn(1, self.course.get_managers())

    def test_get_exam(self):
        """Test retrieving a specific exam"""
        self.course.add_exam(course_name="Final", link="final_exam_link", year=2024, semester=Semester.SPRING,
                             moed=Moed.B)
        exam = self.course.get_exam(2024, Semester.SPRING, Moed.B)
        self.assertEqual(exam.course_name, "Final")

    def test_get_exams_by_year(self):
        """Test retrieving exams by year"""
        self.course.add_exam(course_name="Midterm", link="midterm_link", year=2024, semester=Semester.FALL, moed=Moed.A)
        self.course.add_exam(course_name="Final", link="final_link", year=2024, semester=Semester.SPRING, moed=Moed.B)
        exams = self.course.get_exams(2024)
        self.assertEqual(len(exams), 2)

    def test_add_course_topic_duplicate(self):
        """Test that adding a duplicate topic raises an exception"""
        with self.assertRaises(TopicAlreadyExist):
            self.course.add_course_topic("Algebra")

    def test_remove_course_topic_not_found(self):
        """Test removing a non-existing topic raises an exception"""
        with self.assertRaises(TopicNotFound):
            self.course.remove_course_topic("Trigonometry")

    def test_remove_student_not_found(self):
        """Test removing a student who is not enrolled in the course raises an exception"""
        with self.assertRaises(UserIsNotRegisterToCourse):
            self.course.remove_student(9999)

    def test_add_student_duplicate(self):
        """Test adding a duplicate student raises an exception"""
        self.course.add_student(1001)
        with self.assertRaises(UserAlreadyRegisterToCourse):
            self.course.add_student(1001)

    def test_add_exam_duplicate(self):
        """Test adding a duplicate exam raises an exception"""
        self.course.add_exam(course_name="Midterm", link="exam_link", year=2024, semester=Semester.FALL, moed=Moed.A)
        with self.assertRaises(ExamAlreadyExists):
            self.course.add_exam(course_name="Midterm", link="exam_link", year=2024, semester=Semester.FALL,
                                 moed=Moed.A)


if __name__ == "__main__":
    unittest.main()
