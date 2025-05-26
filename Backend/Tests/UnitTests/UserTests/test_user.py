import unittest
from unittest.mock import patch, MagicMock
from Backend.BusinessLayer.Util.Exceptions import (
    UserAlreadyRegisterToCourse,
    UserIsNotRegisterToCourse
)
from Backend.BusinessLayer.Course.Course import Course  # if needed

from Backend.DataLayer.UserData.UserModel import UserModel
from Backend.DataLayer.SystemManagers.SystemManagersModel import SystemManagersModel
from Backend.DataLayer.UserData.UserRepository import UserRepository
from Backend.DataLayer.UserCourses.UserCoursesRepository import UserCoursesRepository
from Backend.BusinessLayer.User.User import User  # adjust if the class is located here


class TestUser(unittest.TestCase):
    def setUp(self):
        # Create a sample user instance.
        self.user = User(
            user_id="u123",
            email="test@example.com",
            password="secret",
            first_name="Test",
            last_name="User"
        )
        # Override the _repo instance with a MagicMock to avoid real DB calls.
        self.user._repo = MagicMock(spec=UserRepository)

    @patch("Backend.DataLayer.UserData.UserRepository.UserRepository.add_user")
    def test_create(self, mock_add_user):
        # Test that User.create calls add_user on the repository and returns a User instance.
        user = User.create("u456", "new@example.com", "pass", "New", "User")
        mock_add_user.assert_called_once_with(user)
        self.assertEqual(user.user_id, "u456")
        self.assertEqual(user.email, "new@example.com")
        self.assertEqual(user.first_name, "New")
        self.assertEqual(user.last_name, "User")

    @patch("Backend.DataLayer.UserData.UserRepository.UserRepository.get_user_by_id")
    def test_get_by_id(self, mock_get_user_by_id):
        # Simulate repository returning a user.
        mock_get_user_by_id.return_value = self.user
        result = User.get_by_id("u123")
        mock_get_user_by_id.assert_called_once_with("u123")
        self.assertEqual(result, self.user)

    def test_login(self):
        # Test login sets loggedIn to True and calls update_user.
        self.user.loggedIn = False
        self.user._repo.update_user = MagicMock()
        self.user.login()
        self.assertTrue(self.user.loggedIn)
        self.user._repo.update_user.assert_called_once_with(self.user)

    def test_logout(self):
        # Test logout sets loggedIn to False and calls update_user.
        self.user.loggedIn = True
        self.user._repo.update_user = MagicMock()
        self.user.logout()
        self.assertFalse(self.user.loggedIn)
        self.user._repo.update_user.assert_called_once_with(self.user)

    def test_reset_new_password(self):
        # Test that reset_new_password delegates to update_user_password_by_email.
        self.user._repo.update_user_password_by_email = MagicMock(return_value="updated")
        result = self.user.reset_new_password("test@example.com", "newpass")
        self.user._repo.update_user_password_by_email.assert_called_once_with("test@example.com", "newpass")
        self.assertEqual(result, "updated")

    @patch("Backend.DataLayer.UserCourses.UserCoursesRepository.UserCoursesRepository.is_exist")
    @patch("Backend.DataLayer.UserCourses.UserCoursesRepository.UserCoursesRepository.add_user_to_course")
    def test_registerToCourse_success(self, mock_add_to_course, mock_is_exist):
        # Assume user is not registered.
        mock_is_exist.return_value = False
        self.user.courses = []
        self.user._repo.update_user = MagicMock()
        self.user.registerToCourse("course1")
        self.assertIn("course1", self.user.courses)
        mock_add_to_course.assert_called_once_with(user_id=self.user.user_id, course_id="course1")
        self.user._repo.update_user.assert_called_once_with(self.user)

    @patch("Backend.DataLayer.UserCourses.UserCoursesRepository.UserCoursesRepository.is_exist")
    def test_registerToCourse_already_registered(self, mock_is_exist):
        # Simulate that the course already exists either in user.courses or via repository.
        mock_is_exist.return_value = True
        self.user.courses = []  # even if empty, repository says exists
        with self.assertRaises(UserAlreadyRegisterToCourse):
            self.user.registerToCourse("course1")

    @patch("Backend.DataLayer.UserCourses.UserCoursesRepository.UserCoursesRepository.is_exist")
    @patch("Backend.DataLayer.UserCourses.UserCoursesRepository.UserCoursesRepository.remove_user_from_course")
    def test_removeCourse_success(self, mock_remove_from_course, mock_is_exist):
        # Set up the user as registered to a course.
        self.user.courses = ["course1"]
        self.user._repo.update_user = MagicMock()
        mock_is_exist.return_value = True
        self.user.removeCourse("course1")
        self.assertNotIn("course1", self.user.courses)
        self.user._repo.update_user.assert_called_once_with(self.user)
        mock_remove_from_course.assert_called_once_with(user_id=self.user.user_id, course_id="course1")

    @patch("Backend.DataLayer.UserCourses.UserCoursesRepository.UserCoursesRepository.is_exist")
    def test_removeCourse_not_registered(self, mock_is_exist):
        # If course not in user's courses and repository returns False.
        self.user.courses = []
        mock_is_exist.return_value = False
        with self.assertRaises(UserIsNotRegisterToCourse):
            self.user.removeCourse("course1")

    def test_editProfile(self):
        self.user._repo.update_user = MagicMock()
        # Change profile data.
        self.user.editProfile(email="changed@example.com", password="newpass", first_name="Changed", last_name="User")
        self.assertEqual(self.user.email, "changed@example.com")
        self.assertEqual(self.user.password, "newpass")
        self.assertEqual(self.user.first_name, "Changed")
        self.assertEqual(self.user.last_name, "User")
        self.user._repo.update_user.assert_called_once_with(self.user)

    def test_delete(self):
        original_user_id = self.user.user_id
        self.user._repo.delete_user = MagicMock()
        self.user.delete()
        self.user._repo.delete_user.assert_called_once_with(original_user_id)
        self.assertIsNone(self.user.user_id)

    def test_get_courses(self):
        # Test that get_courses returns the courses list in a thread-safe manner.
        self.user.courses = ["course1", "course2"]
        result = self.user.get_courses()
        self.assertEqual(result, ["course1", "course2"])

    def test_get_first_name(self):
        self.user.first_name = "TestName"
        self.assertEqual(self.user.get_first_name(), "TestName")

    def test_get_last_name(self):
        self.user.last_name = "LastName"
        self.assertEqual(self.user.get_last_name(), "LastName")

    def test_get_user_id(self):
        self.user.user_id = "u123"
        self.assertEqual(self.user.get_user_id(), "u123")


if __name__ == "__main__":
    unittest.main()
