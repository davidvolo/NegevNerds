import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..')))
from Backend.BusinessLayer.User import UserFacade
from Backend.BusinessLayer.Util.Exceptions import *

class TestUserController(unittest.TestCase):
    def setUp(self):
        """Set up a fresh UserController instance for each test."""
        self.user_controller = UserController()

    @patch("UserController.UserController.send_auth_code")
    def test_register_step1_happy_path(self, mock_send_auth_code):
        """Test registration step 1 (happy path)."""
        mock_send_auth_code.return_value = (123456, datetime.now() + timedelta(minutes=3))
        
        result = self.user_controller.register_step1(
            email="testuser@bgu.ac.il",
            password="password123",
            first_name="Test",
            last_name="User"
        )
        
        self.assertTrue(result)
        self.assertIn("testuser@bgu.ac.il", self.user_controller.pending_auth_codes)
        self.assertEqual(self.user_controller.pending_auth_codes["testuser@bgu.ac.il"]["code"], 123456)

    def test_register_step1_existing_user(self):
        """Test registration step 1 for an already registered user (sad path)."""
        self.user_controller.users["existing@bgu.ac.il"] = "dummy_user"

        with self.assertRaises(UserAlreadyExistsError):
            self.user_controller.register_step1(
                email="existing@bgu.ac.il",
                password="password123",
                first_name="Existing",
                last_name="User"
            )

    def test_register_step1_invalid_email(self):
        """Test registration step 1 with invalid email (sad path)."""
        with self.assertRaises(InvalidEmailDomainError):
            self.user_controller.register_step1(
                email="invalid_email@notbgu.com",
                password="password123",
                first_name="Invalid",
                last_name="Email"
            )

    @patch("UserController.UserController.verify_auth_code")
    def test_register_step2_happy_path(self, mock_verify_auth_code):
        """Test registration step 2 (happy path)."""
        email = "newuser@bgu.ac.il"
        self.user_controller.pending_auth_codes[email] = {
            "code": 123456,
            "expiry": datetime.now() + timedelta(minutes=3)
        }
        mock_verify_auth_code.return_value = True

        result = self.user_controller.register_step2(
            email=email,
            entered_code=123456,
            password="password123",
            first_name="New",
            last_name="User"
        )

        self.assertTrue(result)
        self.assertIn(email, self.user_controller.users)
        self.assertNotIn(email, self.user_controller.pending_auth_codes)

    def test_register_step2_wrong_code(self):
        """Test registration step 2 with incorrect authentication code (sad path)."""
        email = "newuser@bgu.ac.il"
        self.user_controller.pending_auth_codes[email] = {
            "code": 123456,
            "expiry": datetime.now() + timedelta(minutes=3)
        }

        with self.assertRaises(AuthenticationCodeError):
            self.user_controller.register_step2(
                email=email,
                entered_code=654321,
                password="password123",
                first_name="New",
                last_name="User"
            )

    def test_register_step2_expired_code(self):
        """Test registration step 2 with expired authentication code (sad path)."""
        email = "newuser@bgu.ac.il"
        self.user_controller.pending_auth_codes[email] = {
            "code": 123456,
            "expiry": datetime.now() - timedelta(minutes=1)
        }

        with self.assertRaises(AuthenticationCodeError):
            self.user_controller.register_step2(
                email=email,
                entered_code=123456,
                password="password123",
                first_name="New",
                last_name="User"
            )

    def test_register_step2_no_pending_code(self):
        """Test registration step 2 with no pending code (sad path)."""
        with self.assertRaises(AuthenticationCodeError):
            self.user_controller.register_step2(
                email="notfound@bgu.ac.il",
                entered_code=123456,
                password="password123",
                first_name="Not",
                last_name="Found"
            )

    @patch("UserController.smtplib.SMTP")
    def test_send_auth_code_happy_path(self, mock_smtp):
        """Test send_auth_code method (happy path)."""
        mock_server = MagicMock()
        mock_smtp.return_value = mock_server

        auth_code, auth_code_expiry = self.user_controller.send_auth_code(
            email="testuser@bgu.ac.il",
            first_name="Test"
        )

        self.assertIsInstance(auth_code, int)
        self.assertTrue(100000 <= auth_code <= 999999)
        self.assertTrue(auth_code_expiry > datetime.now())
        mock_server.starttls.assert_called_once()
        mock_server.login.assert_called_once()
        mock_server.sendmail.assert_called_once()

    @patch("UserController.smtplib.SMTP")
    def test_send_auth_code_email_failure(self, mock_smtp):
        """Test send_auth_code method when email sending fails (sad path)."""
        mock_server = MagicMock()
        mock_server.sendmail.side_effect = Exception("SMTP Error")
        mock_smtp.return_value = mock_server

        with self.assertRaises(EmailSendingError):
            self.user_controller.send_auth_code(
                email="testuser@bgu.ac.il",
                first_name="Test"
            )

if __name__ == "__main__":
    unittest.main()
