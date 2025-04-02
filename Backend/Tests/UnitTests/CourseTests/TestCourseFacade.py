import unittest
from unittest.mock import patch, MagicMock
from Backend.BusinessLayer.Course.CourseFacade import CourseFacade
from Backend.BusinessLayer.Util.Exceptions import CourseAlreadyExists, CourseIsNotExist
from Backend.DataLayer.User import UserModel

class TestCourseFacade(unittest.TestCase):

    def setUp(self):
        # Set up the mock objects for the test
        self.course_facade = CourseFacade()  # Instantiate the CourseFacade
        self.course = MagicMock()  # Mock the Course object
        self.course_facade.courses = {}  # Mock an empty courses dictionary

    def tearDown(self):
        """Clean up after each test."""
        self.course_facade.courses.clear()  # Clear the courses after each test

    @patch('Backend.DataLayer.Course.CourseModel')  # Mock the CourseModel
    @patch('Backend.DataLayer.User.UserModel')  # Mocking the UserModel
    @patch('sqlalchemy.orm.session.Session.commit')  # Mock the commit to prevent database action
    def test_open_course_success(self, MockUserModel, MockCourseModel, mock_commit):
        """Test case for successfully creating a new course."""

        # Mock the UserModel methods if needed
        mock_user_model = MagicMock()
        MockUserModel.return_value = mock_user_model

        # Mock the CourseModel methods
        mock_course = MagicMock()
        MockCourseModel.return_value = mock_course

        # Mock the method for checking if the course exists (e.g. `open_course_possibility`)
        mock_course.open_course_possibility.return_value = True

        # Mock the add_course method to avoid database interaction
        mock_course.add_course.return_value = None  # Simulate adding the course without database action

        # Define the course data
        course_id = "CS101"
        course_name = "Computer Science 101"
        course_topics = ["Algorithms", "Data Structures"]

        # Call the method to open the course
        result = self.course_facade.open_course(course_id, course_name, course_topics)

        # Assert the course was added to the courses dictionary
        self.assertIn(course_id, self.course_facade.courses)

        # Verify that commit was never called (i.e., no DB interaction happened)
        mock_commit.assert_not_called()

    @patch('Backend.DataLayer.Course.CourseModel')  # Mock the CourseModel
    def test_remove_student_from_course(self, MockCourseModel):
        """Test case for removing a student from a course."""
        course_id = "CS101"
        user_id = "user123"
        self.course_facade.courses[course_id] = self.course  # Add a course to the facade

        # Mock the remove_student method on the course
        self.course.remove_student = MagicMock()

        # Call the remove_student_from_course function
        self.course_facade.remove_student_from_course(course_id, user_id)

        # Check if remove_student was called with the correct user_id
        self.course.remove_student.assert_called_with(user_id)

    @patch('Backend.DataLayer.Course.CourseModel')  # Mock the CourseModel
    def test_remove_student_from_course_course_not_found(self, MockCourseModel):
        """Test case for when trying to remove a student from a non-existing course."""
        course_id = "CS102"
        user_id = "user123"

        with self.assertRaises(CourseIsNotExist):
            self.course_facade.remove_student_from_course(course_id, user_id)

    @patch('Backend.DataLayer.Course.CourseModel')  # Mock the CourseModel
    def test_add_exam_to_course(self, MockCourseModel):
        """Test case for adding an exam to a course."""
        course_id = "CS101"
        course_name = "Computer Science 101"
        exam_name = "Final Exam"
        link = "/path/to/exam.pdf"
        year = 2023
        semester = "Fall"
        moed = "A"

        self.course_facade.courses[course_id] = self.course  # Add a course to the facade

        # Mock the add_exam function of the course
        self.course.add_exam = MagicMock()

        # Call the add_exam_to_course function
        self.course_facade.add_exam_to_course(course_id, course_name, link, year, semester, moed)

        # Check if the add_exam method was called
        self.course.add_exam.assert_called_with(course_name, link, year, semester, moed)

    @patch('Backend.DataLayer.Course.CourseModel')  # Mock the CourseModel
    def test_remove_exam_from_course(self, MockCourseModel):
        """Test case for removing an exam from a course."""
        course_id = "CS101"
        year = 2023
        semester = "Fall"
        moed = "A"
        self.course_facade.courses[course_id] = self.course  # Add a course to the facade

        # Mock the remove_exam method of the course
        self.course.remove_exam = MagicMock()

        # Call the remove_exam_from_course function
        self.course_facade.remove_exam_from_course(course_id, year, semester, moed)

        # Check if remove_exam method was called
        self.course.remove_exam.assert_called_with(year, semester, moed)

    @patch('Backend.DataLayer.Course.CourseRepository')  # Mock the CourseRepository
    @patch('Backend.DataLayer.Course.CourseModel')  # Mock the CourseModel
    @patch('sqlalchemy.orm.session.Session.commit')  # Mock commit to avoid database interaction
    def test_remove_course(self, mock_commit, MockCourseModel, MockCourseRepo):
        """Test case for removing a course."""
        course_id = "CS101"
        self.course_facade.courses[course_id] = self.course  # Add a course to the facade

        # Mock the delete_course method in the CourseRepository
        mock_course_repo = MagicMock()
        MockCourseRepo.return_value = mock_course_repo

        # Mock the delete_course method on the mock course repository
        mock_course_repo.delete_course = MagicMock()

        # Call the remove_course function
        self.course_facade.remove_course(course_id)

        # Check if the course was removed from the courses dictionary
        self.assertNotIn(course_id, self.course_facade.courses)

        # Verify that delete_course was called with the correct course_id
        mock_course_repo.delete_course.assert_called_with(course_id)

        # Verify that commit was never called (i.e., no DB interaction happened)
        mock_commit.assert_not_called()

    @patch('Backend.DataLayer.Course.CourseModel')  # Mock the CourseModel
    def test_remove_course_not_found(self, MockCourseModel):
        """Test case for trying to remove a non-existing course."""
        course_id = "CS101"

        # Make sure the course does not exist in the courses dictionary
        self.course_facade.courses = {}

        # Ensure CourseIsNotExist exception is raised
        with self.assertRaises(CourseIsNotExist):
            self.course_facade.remove_course(course_id)

    @patch('Backend.DataLayer.Course.CourseModel')  # Mock the CourseModel
    def test_add_course_topic(self, MockCourseModel):
        """Test case for adding a topic to a course."""
        course_id = "CS101"
        course_topic = "New Topic"
        self.course_facade.courses[course_id] = self.course  # Add a course to the facade

        # Mock the add_course_topic function
        self.course.add_course_topic = MagicMock()

        # Call the add_course_topic function
        self.course_facade.add_course_topic(course_id, course_topic)

        # Check if the add_course_topic was called
        self.course.add_course_topic.assert_called_with(course_topic)

    @patch('Backend.DataLayer.Course.CourseModel')  # Mock the CourseModel
    def test_get_course_success(self, MockCourseModel):
        """Test case for retrieving an existing course."""
        course_id = "CS101"
        self.course_facade.courses[course_id] = self.course  # Add a course to the facade

        # Call the get_course function
        result = self.course_facade.get_course(course_id)

        # Verify the course returned is the correct one
        self.assertEqual(result, self.course)

    @patch('Backend.DataLayer.Course.CourseModel')  # Mock the CourseModel
    def test_get_course_not_found(self, MockCourseModel):
        """Test case for trying to retrieve a non-existing course."""
        course_id = "CS101"

        with self.assertRaises(CourseIsNotExist):
            self.course_facade.get_course(course_id)

if __name__ == '__main__':
    unittest.main()
