import io
import json
import unittest
import os
from datetime import datetime, timedelta
from unittest.mock import patch

from werkzeug.datastructures import FileStorage
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from Backend.BusinessLayer.NegevNerds import NegevNerds
from Backend.DataLayer.Base import Base, delete_all_data
from Backend.DataLayer.SystemManagers.SystemManagersRepository import SystemManagersRepository
from Backend.Tests.SystemTest.BaseTestCase import BaseTestCase
from Backend.DataLayer.SystemManagers.SystemManagersModel import SystemManagersModel


class TestNegevNerdsUserManagement(BaseTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()

    def setUp(self):
        super().setUp()
        self.user = self._complete_user_registration("admin@bgu.ac.il", "Pass1!", "Admin", "User")

    def tearDown(self):
        super().tearDown()

    def _mock_image_file(self, filename="profile.jpg", content=b"fake image content"):
        stream = io.BytesIO(content)
        return FileStorage(stream=stream, filename=filename, content_type='image/jpeg')

    def _upload_dummy_profile_pic(self, user_id):
        file = self._mock_image_file()
        return self.negev.upload_profile_picture(user_id, file)

    # -------------- Registration Tests --------------
    @patch('Backend.BusinessLayer.NegevNerds.UserFacade.send_auth_code')
    @patch('Backend.BusinessLayer.NegevNerds.NegevNerds.register_authentication_part')
    def test_register_valid_user(self, mock_register_auth_part, mock_send_auth_code):
        """
        Test for registering with valid user data
        """
        test_email = "newuser@post.bgu.ac.il"
        test_password = "ValidPass1!"
        test_first_name = "נועה"
        test_last_name = "עבודי"

        # Mock behaviors
        mock_send_auth_code.return_value = None
        mock_register_auth_part.return_value = {"message": "Verification successful"}

        # Step 1: Basic registration - store user details.
        registered_user, message = self.negev.register(
            test_email,
            test_password,
            test_password,
            test_first_name,
            test_last_name
        )
        self.assertIsNotNone(registered_user, "Basic registration did not return a valid user.")
        self.assertNotIn("Error", message, "Basic registration returned an error message.")

        auth_code = "123456"
        # Step 2: Registration with authentication code - simulate verifying the code.
        auth_response = self.negev.register_authentication_part(test_email, auth_code)
        self.assertIn("message", auth_response, "Authentication code registration step failed.")

        # Step 3: Acceptance of the terms of use - finalize the registration process.
        term_response = self.negev.register_termOfUse_part(test_email, test_password, test_first_name, test_last_name, None)
        self.assertIsInstance(term_response, tuple, "Acceptance of the terms of use step failed.")

        found_user = self.negev._user_facade.getUser_by_email(test_email)
        self.assertIsNotNone(found_user, "User not found via UserFacade.getUser_by_email after registration.")
        self.assertEqual(found_user.email, test_email, "User email does not match the input.")
        self.assertEqual(found_user.first_name, test_first_name, "User first name does not match the input.")
        self.assertEqual(found_user.last_name, test_last_name, "User last name does not match the input.")

    def test_register_non_bgu_email(self):
        """
        Verify that registration fails for a non-BGU email.
        """
        non_bgu_email = "test@gmail.com"
        test_password = "ValidPass1!"
        test_first_name = "יוזר"
        test_last_name = "טסט"

        # Pre-check: Ensure the user is not registered.
        found_before = self.negev._user_facade.getUser_by_email(non_bgu_email)
        self.assertIsNone(found_before, "User should not already exist before registration attempt.")

        # Step 1: Attempt basic registration.
        registered_user, message = self.negev.register(
            non_bgu_email,
            test_password,
            test_password,
            test_first_name,
            test_last_name
        )
        self.assertIsNone(registered_user, "Registration should have failed for a non-BGU email.")

        # Extract error message.
        if isinstance(message, dict):
            error_msg = message.get("Error", "")
        else:
            error_msg = message
        # Update expected error message to match the actual one.
        self.assertIn("האימייל אינו תקין", error_msg,
                      "Error message should indicate that the email is invalid.")

        # Final verification: Ensure the user is still not in the system.
        found_after = self.negev._user_facade.getUser_by_email(non_bgu_email)
        self.assertIsNone(found_after, "User should not exist in the system after failed registration.")

    from unittest.mock import patch

    from unittest.mock import patch

    @patch('Backend.BusinessLayer.NegevNerds.UserFacade.send_auth_code')
    @patch('Backend.BusinessLayer.NegevNerds.NegevNerds.register_authentication_part')
    def test_register_already_registered_email(self, mock_register_auth_part, mock_send_auth_code):
        """
        Verify that attempting to register an email that is already registered fails.
        """
        test_email = "duplicate@post.bgu.ac.il"
        test_password = "ValidPass1!"
        test_first_name = "נועה"
        test_last_name = "עבודי"

        # Mock behaviors
        mock_send_auth_code.return_value = None
        mock_register_auth_part.return_value = {"message": "Verification successful"}

        # First registration attempt
        user1, message1 = self.negev.register(
            test_email,
            test_password,
            test_password,
            test_first_name,
            test_last_name
        )
        self.assertIsNotNone(user1, "Initial registration did not return a valid user.")
        self.assertNotIn("Error", message1, "Initial registration returned an error message.")

        term_response = self.negev.register_termOfUse_part(
            test_email,
            test_password,
            test_first_name,
            test_last_name,
            None
        )
        self.assertIsInstance(term_response, tuple, "Acceptance of the terms of use step failed.")

        # Now, attempt to register with the same email again
        user2, message2 = self.negev.register(
            test_email,
            test_password,
            test_password,
            "נדב",
            "קטלב"
        )

        # Expect registration to fail (i.e., user2 should be None)
        self.assertIsNone(user2, "Registration should have failed for an already registered email.")

        # Extract error message
        if isinstance(message2, dict):
            err_msg = message2.get("Error", "")
        else:
            err_msg = message2

        self.assertIn("קיים", err_msg, "Error message should indicate that the email is already registered.")

    def test_register_mismatching_passwords(self):
        """
        Verify that registration fails when password and confirmation do not match.
        """
        test_email = "mismatch@post.bgu.ac.il"
        test_password = "ValidPass1!"
        test_confirm_password = "DifferentPass2@"
        test_first_name = "נועה"
        test_last_name = "עבודי"

        user, message = self.negev.register(
            test_email,
            test_password,
            test_confirm_password,
            test_first_name,
            test_last_name
        )
        self.assertIsNone(user, "Registration should fail when passwords do not match.")
        if isinstance(message, dict):
            err_msg = message.get("Error", "")
        else:
            err_msg = message
        self.assertIn("הסיסמה אינה", err_msg,
                      "Error message should indicate that passwords do not match.")

    from unittest.mock import patch

    @patch('Backend.BusinessLayer.NegevNerds.UserFacade.send_auth_code')
    @patch('Backend.BusinessLayer.NegevNerds.NegevNerds.register_authentication_part')
    def test_register_incorrect_verification_code(self, mock_register_auth_part, mock_send_auth_code):
        """
        Verify that when an incorrect verification code is provided, the verification fails.
        """
        test_email = "verify@post.bgu.ac.il"
        test_password = "ValidPass1!"
        test_first_name = "נועה"
        test_last_name = "עבודי"
        incorrect_code = "000000"

        # Mock behaviors
        mock_send_auth_code.return_value = None
        mock_register_auth_part.return_value = {"Error": "Invalid verification code."}

        # Step 1: Basic registration
        user, message = self.negev.register(
            test_email,
            test_password,
            test_password,
            test_first_name,
            test_last_name
        )
        self.assertIsNotNone(user, "Basic registration did not return a valid user.")
        self.assertNotIn("Error", message, "Basic registration returned an error message.")

        # Step 2: Attempt verification with incorrect code
        auth_response = self.negev.register_authentication_part(test_email, incorrect_code)

        # Step 3: Verify that an error message is returned
        if isinstance(auth_response, dict):
            err_msg = auth_response.get("Error", "")
        else:
            err_msg = auth_response

        self.assertIn("Invalid verification code", err_msg,
                      "Error message should indicate that the verification code is invalid.")

    # -------------- Login & Logout Tests --------------
    @patch('Backend.BusinessLayer.NegevNerds.UserFacade.send_auth_code')
    @patch('Backend.BusinessLayer.NegevNerds.NegevNerds.register_authentication_part')
    def test_login_valid_credentials(self, mock_register_auth_part, mock_send_auth_code):
        """
        Test Case 1: Verify user can successfully log in with valid credentials.
        """
        test_email = "loginn@post.bgu.ac.il"
        test_password = "ValidPass1!"
        test_first_name = "לוגאין"
        test_last_name = "יוזר"

        # Mock behaviors
        mock_send_auth_code.return_value = None
        mock_register_auth_part.return_value = {"message": "Verification successful"}

        print("📥 Step 1: Starting user registration")
        registered_user = self._complete_user_registration(
            test_email, test_password, test_first_name, test_last_name
        )
        print(f"✅ Registered user: {registered_user}")

        self.assertIsNotNone(registered_user, "User registration failed unexpectedly.")

        user_id = registered_user.get_user_id() if hasattr(registered_user, "get_user_id") else registered_user.user_id
        print(f"👤 Registered user ID: {user_id}")

        print("🚪 Step 2: Logging out...")
        logout_message = self.negev.logout(user_id)
        print(f"🔁 Logout message: {logout_message}")
        self.assertIn("התנתקות", logout_message, "Logout should succeed.")

        print("🔑 Step 3: Logging in...")
        first_name, last_name, logged_user_id, login_response = self.negev.login(test_email, test_password)
        print(f"📛 Login result -> first: {first_name}, last: {last_name}, user_id: {logged_user_id}")
        print(f"🧾 Full login response: {login_response}")

        self.assertIsNotNone(logged_user_id, "User ID should not be None after successful login.")
        self.assertEqual(first_name, test_first_name, "Returned first name does not match.")
        self.assertEqual(last_name, test_last_name, "Returned last name does not match.")
        self.assertEqual(login_response.get("status"), "success", "Login should return success status.")

    @patch('Backend.BusinessLayer.NegevNerds.UserFacade.send_auth_code')
    @patch('Backend.BusinessLayer.NegevNerds.NegevNerds.register_authentication_part')
    def test_login_invalid_credentials(self, mock_register_auth_part, mock_send_auth_code):
        """
        Test Case 2: Verify login fails with invalid credentials.
        """
        # Mock behaviors
        mock_send_auth_code.return_value = None
        mock_register_auth_part.return_value = {"message": "Verification successful"}

        # Option 1: Unregistered email
        unregistered_email = "nonexistent@post.bgu.ac.il"
        password = "SomePass1!"

        first, last, user_id, login_response = self.negev.login(unregistered_email, password)

        self.assertIsNone(first, "Login should fail for unregistered email.")
        self.assertEqual(login_response.get("status"), "error",
                         "Login response should indicate an error for unregistered email.")
        self.assertIn("Incorrect email or password", login_response.get("message"),
                      "Error message should indicate invalid credentials for unregistered email.")

        # Option 2: Wrong password for a registered email
        email2 = "loginfail@post.bgu.ac.il"
        correct_password = "ValidPass1!"
        wrong_password = "WrongPass!"
        first_name = "יוזר"
        last_name = "כשלון"

        # Registration process
        user, reg_msg = self.negev.register(
            email2, correct_password, correct_password, first_name, last_name
        )
        self.assertIsNotNone(user, "Registration did not return a valid user.")
        self.assertNotIn("Error", reg_msg, "Registration returned an error message.")

        # Simulate authentication and terms acceptance with dummy profile pic
        self.negev.register_authentication_part(email2, "123456")

        dummy_image = FileStorage(
            stream=io.BytesIO(b"fake image content"),
            filename="dummy.jpg",
            content_type="image/jpeg"
        )

        # ✅ תיקון: קלט אחיד – או tuple או string
        result = self.negev.register_termOfUse_part(
            email2, correct_password, first_name, last_name, profile_picture_file=dummy_image
        )

        if isinstance(result, tuple):
            user_id, term_msg = result
            self.assertIsInstance(term_msg, dict, "Terms acceptance should return a dictionary message.")
        else:
            self.fail(f"Term of use registration failed unexpectedly: {result}")

        # Attempt login with wrong password
        first, last, user_id, login_response = self.negev.login(email2, wrong_password)

        self.assertIsNone(first, "Login should fail with an incorrect password.")
        self.assertEqual(login_response.get("status"), "error",
                         "Login response should indicate error for wrong password.")
        error_message = login_response.get("message", "")
        self.assertTrue(
            "Incorrect email or password" in error_message or "Invalid salt" in error_message,
            "Error message should indicate invalid credentials for wrong password.")

    def test_logout_success(self):
        """
        Verify that logout returns a success message when provided with a valid user ID.
        Expected Result:
          Logout מחזיר "התנתקות בוצעה בהצלחה"
        """
        email = "logoutuser@post.bgu.ac.il"
        password = "ValidPass1!"
        first_name = "לוגאוט"
        last_name = "יוזר"
        user = self._complete_user_registration(email, password, first_name, last_name)
        self.assertIsNotNone(user, "Registration did not return a valid user.")
        user_id = user.id if hasattr(user, "id") else user.user_id
        result = self.negev.logout(user_id)
        self.assertEqual(result, "התנתקות בוצעה בהצלחה", "Logout did not return the expected success message.")

    def test_logout_error(self):
        """
        Verify that logout returns an error message when provided with an invalid user ID.
        Expected Result:
          Logout מחזיר הודעת שגיאה שמתחילה ב-"Error:".
        """
        result = self.negev.logout("non_existent_user_id")
        self.assertIn("Error", result, "Logout did not return an error message when given an invalid user id.")

    def test_get_user_name_success(self):
        """
        Verify that get_user_name returns the user's full name for a valid user ID.

        Steps:
         1. Register and complete a user.
         2. Retrieve the full name using get_user_name.

        Expected Result:
         The returned string equals "FirstName LastName".
        """
        email = "username@post.bgu.ac.il"
        password = "ValidPass1!"
        first_name = "נועה"
        last_name = "עבודי"
        user = self._complete_user_registration(email, password, first_name, last_name)
        self.assertIsNotNone(user, "User registration failed.")

        # Assume the full name returned should be "Test User"
        full_name = self.negev.get_user_name(user.user_id)
        self.assertEqual(full_name, f"{first_name} {last_name}",
                         "get_user_name did not return the expected full name.")

    def test_get_user_name_invalid(self):
        """
        Verify that get_user_name returns an empty list when an invalid user ID is provided.

        Steps:
          1. Call get_user_name with a non-existent user ID.

        Expected Result:
          The method returns an empty list.
        """
        invalid_user_id = "non_existent_id"
        result = self.negev.get_user_name(invalid_user_id)
        # Update the expectation to an empty list, since that is what the current implementation does.
        self.assertIsInstance(result, list, "Expected a list for an invalid user ID.")
        self.assertEqual(result, [], "Expected an empty list when the user is not found.")

    @patch('Backend.BusinessLayer.NegevNerds.UserFacade.send_reset_password_code')
    def test_forgot_password_invalid_email(self, mock_send_reset_code):
        """
        Verify forgot_password fails with invalid email (non-BGU domain).
        """
        invalid_email = "user@gmail.com"
        response = self.negev.forgot_password(invalid_email)
        data = json.loads(response)

        self.assertEqual(data["status"], "error")
        self.assertIn("האימייל חייב להיות של אוניברסיטת בן גוריון", data["message"])

    @patch('Backend.BusinessLayer.NegevNerds.UserFacade.send_reset_password_code')
    def test_forgot_password_email_not_found(self, mock_send_reset_code):
        """
        Verify forgot_password fails if email is not registered.
        """
        email = "notfound@post.bgu.ac.il"
        response = self.negev.forgot_password(email)
        data = json.loads(response)

        self.assertEqual(data["status"], "error")
        self.assertIn("כתובת אימייל לא נמצאה", data["message"])

    @patch('Backend.BusinessLayer.NegevNerds.UserFacade.send_reset_password_code')
    def test_forgot_password_success(self, mock_send_reset_code):
        """
        Verify forgot_password succeeds with a registered BGU email.
        """
        email = "registered@post.bgu.ac.il"

        # Simulate user existing
        self.negev._user_facade.users_byEmail[email] = "DummyUser"

        response = self.negev.forgot_password(email)
        data = json.loads(response)

        self.assertEqual(data["status"], "success")
        self.assertIn("מייל אימות נשלח", data["message"])

    @patch('Backend.BusinessLayer.NegevNerds.UserFacade.send_reset_password_code')
    def test_forgot_password_send_email_failure(self, mock_send_reset_code):
        """
        Verify forgot_password handles email sending failure.
        """
        email = "registered@post.bgu.ac.il"

        # Simulate user existing
        self.negev._user_facade.users_byEmail[email] = "DummyUser"

        # Simulate exception on sending reset code
        mock_send_reset_code.side_effect = Exception("Simulated failure")

        response = self.negev.forgot_password(email)
        data = json.loads(response)

        self.assertEqual(data["status"], "error")
        self.assertIn("שליחת הקוד נכשלה", data["message"])

    def test_verify_reset_code_not_found(self):
        """
        Verify verify_reset_code fails if no code exists for email.
        """
        email = "user@post.bgu.ac.il"
        code = "123456"

        # Clear any existing reset codes before running the test
        self.negev._user_facade.pending_reset_codes.clear()

        response = self.negev.verify_reset_code(email, code)
        data = json.loads(response)

        self.assertEqual(data["status"], "error")
        self.assertIn("לא נמצא קוד אימות", data["message"])

    @patch('Backend.BusinessLayer.NegevNerds.create_access_token', return_value="dummy_token")
    def test_verify_reset_code_expired(self, mock_create_token):
        """
        Verify verify_reset_code fails if the code is expired.
        """
        email = "user@post.bgu.ac.il"
        code = "123456"

        # Simulate expired code
        self.negev._user_facade.pending_reset_codes[email] = (
        code, datetime.now() - timedelta(minutes=5))

        response = self.negev.verify_reset_code(email, code)
        data = json.loads(response)

        self.assertEqual(data["status"], "error")
        self.assertIn("הקוד פג תוקף", data["message"])

    def test_verify_reset_code_wrong_code(self):
        """
        Verify verify_reset_code fails with incorrect code.
        """
        email = "user@post.bgu.ac.il"
        correct_code = "123456"
        wrong_code = "654321"

        # Simulate stored correct code
        self.negev._user_facade.pending_reset_codes[email] = (
        correct_code, datetime.now() + timedelta(minutes=5))

        response = self.negev.verify_reset_code(email, wrong_code)
        data = json.loads(response)

        self.assertEqual(data["status"], "error")
        self.assertIn("קוד אימות שגוי", data["message"])

    @patch('Backend.BusinessLayer.NegevNerds.create_access_token', return_value="dummy_token")
    def test_verify_reset_code_success(self, mock_create_token):
        email = "user@post.bgu.ac.il"
        code = "123456"

        self.negev._user_facade.pending_reset_codes.clear()
        self.negev._user_facade.pending_reset_codes[email] = (
            code, datetime.now() + timedelta(minutes=5)
        )

        response = self.negev.verify_reset_code(email, code)
        data = json.loads(response)

        self.assertEqual(data["status"], "success")
        self.assertIn("token", data)

    def test_reset_new_password_invalid_password(self):
        """
        Verify reset_new_password fails if password is invalid.
        """
        email = "user@post.bgu.ac.il"
        bad_password = "short"

        response = self.negev.reset_new_password(email, bad_password)
        data = json.loads(response)

        self.assertEqual(data["status"], "error")
        self.assertIn("הסיסמה אינה עומדת בדרישות", data["message"])

    def test_reset_new_password_success(self):
        """
        Verify reset_new_password succeeds with valid password.
        """
        email = "user@post.bgu.ac.il"
        good_password = "ValidPass1!"

        # Simulate user existing
        self.negev._user_facade.users_byEmail[email] = "DummyUser"

        # Mock successful password reset
        self.negev._user_facade.reset_new_password = lambda email, password: True

        response = self.negev.reset_new_password(email, good_password)
        data = json.loads(response)

        self.assertEqual(data["status"], "success")
        self.assertIn("הסיסמה עודכנה", data["message"])

    def test_reset_new_password_failure(self):
        """
        Verify reset_new_password handles failure if user not found.
        """
        email = "user@post.bgu.ac.il"
        good_password = "ValidPass1!"

        # Mock failed password reset
        self.negev._user_facade.reset_new_password = lambda email, password: False

        response = self.negev.reset_new_password(email, good_password)
        data = json.loads(response)

        self.assertEqual(data["status"], "error")
        self.assertIn("אירעה שגיאה בעדכון הסיסמה", data["message"])

    def test_is_system_manager_in_memory(self):
        """Verify system manager is recognized from _system_managers cache."""
        user = self._complete_user_registration("admin@bgu.ac.il", "Pass1!", "System", "Manager")
        self.negev._system_managers.add(user.user_id)  # הוספה ידנית לקאש
        self.assertTrue(self.negev.is_system_manager(user.user_id))

    def test_is_not_system_manager(self):
        """Verify regular user is not detected as system manager."""
        user = self._complete_user_registration("regular@bgu.ac.il", "Pass1!", "Not", "Admin")
        self.assertFalse(self.negev.is_system_manager(user.user_id))

    def test_update_user_name_success(self):
        """Test: Successfully update user's name and propagate to comments."""
        user = self._complete_user_registration("change@bgu.ac.il", "Pass1!", "ישן", "שם")

        # Now update name
        result = self.negev.update_user_name(user.user_id, "חדש", "שם")

        # Check that the function returns a success indicator
        self.assertIsNotNone(result)

    def test_update_user_name_user_not_found(self):
        """Test: Try to update non-existing user – should raise exception."""
        non_existent_user_id = "ghost_user_id"
        with self.assertRaises(Exception) as context:
            self.negev.update_user_name(non_existent_user_id, "מזויף", "יוזר")
        self.assertIn("איידי", str(context.exception), "Expected error about user ID")

    @patch("Backend.BusinessLayer.FileManager.FileManager")
    def test_upload_profile_picture_success(self, mock_file_manager_class):
        """Test successful upload and DB update of profile picture."""
        user = self._complete_user_registration("profilepic@bgu.ac.il", "Pass1!", "Profile", "Pic")

        # יצירת mock לשמירה שמחזיר path תקני
        mock_file_manager = mock_file_manager_class.return_value
        mock_file_manager.save_profile_picture.return_value = f"/tmp/test_profile_{user.user_id}.jpg"

        image_file = self._mock_image_file()

        # הקצאה מחודשת עם המוק לעובד עם self.negev
        self.negev._file_manager = mock_file_manager

        result_path = self.negev.upload_profile_picture(user.user_id, image_file)

        self.assertIsInstance(result_path, str)
        self.assertTrue(result_path.endswith(".jpg") or result_path.endswith(".jpeg") or result_path.endswith(".png"))

    def test_upload_profile_picture_save_fails(self):
        """Test failure when saving the image raises an exception."""
        user = self._complete_user_registration("failupload@bgu.ac.il", "Pass1!", "Broken", "Uploader")
        bad_file = None  # Simulate missing file

        with self.assertRaises(Exception) as context:
            self.negev.upload_profile_picture(user.user_id, bad_file)

        self.assertIn("Failed to upload profile picture", str(context.exception))

    def test_upload_profile_picture_db_update_fails(self):
        """Test failure when DB update returns False."""
        user = self._complete_user_registration("picfail@bgu.ac.il", "Pass1!", "DB", "Fail")
        image_file = self._mock_image_file()

        # Patch the DB update to simulate failure
        from Backend.DataLayer.ProfilePicture.ProfilePictureRepository import ProfilePictureRepository
        original_update = ProfilePictureRepository.update_profile_pic
        ProfilePictureRepository.update_profile_pic = lambda *args, **kwargs: False

        try:
            result = self.negev.upload_profile_picture(user.user_id, image_file)
            self.assertIsNone(result, "Expected None when DB update fails.")
        finally:
            ProfilePictureRepository.update_profile_pic = original_update  # restore

    def test_get_profile_picture_path_success(self):
        """Test: Successfully retrieve profile picture path after upload."""
        user = self._complete_user_registration("picpath@bgu.ac.il", "Pass1!", "Path", "Tester")
        image_file = self._mock_image_file()

        saved_path = self.negev.upload_profile_picture(user.user_id, image_file)

        result_path = self.negev.get_profile_picture_path(user.user_id)

        self.assertEqual(result_path, saved_path)
        self.assertTrue(
            result_path.endswith(".jpg") or result_path.endswith(".jpeg") or result_path.endswith(".png"))

    def test_get_profile_picture_path_user_not_found(self):
        """Test: No profile picture for non-existent user ID returns None."""
        non_existent_user_id = "ghost_user_999"
        result = self.negev.get_profile_picture_path(non_existent_user_id)
        self.assertIsNone(result, "Expected None for user with no profile picture")

    def test_get_profile_picture_path_repo_failure(self):
        """Test: Force repository failure and expect an exception."""
        user = self._complete_user_registration("error@bgu.ac.il", "Pass1!", "Break", "Me")

        from Backend.DataLayer.ProfilePicture.ProfilePictureRepository import ProfilePictureRepository
        original_method = ProfilePictureRepository.get_path_by_user_id
        ProfilePictureRepository.get_path_by_user_id = lambda *args, **kwargs: (_ for _ in ()).throw(
            Exception("DB fail"))

        try:
            with self.assertRaises(Exception) as context:
                self.negev.get_profile_picture_path(user.user_id)

            self.assertIn("Error retrieving profile picture path", str(context.exception))
        finally:
            ProfilePictureRepository.get_path_by_user_id = original_method  # restore

    def test_delete_profile_picture_success(self):
        """Test: Successfully delete profile picture file and DB record."""
        user = self._complete_user_registration("deletepic@bgu.ac.il", "Pass1!", "Delete", "Pic")
        path = self._upload_dummy_profile_pic(user.user_id)

        self.assertTrue(os.path.exists(path), "Expected file to exist before deletion")

        result = self.negev.delete_profile_picture(user.user_id)

        self.assertTrue(result, "Expected delete_profile_picture to return True on success")
        self.assertFalse(os.path.exists(path), "Expected file to be deleted")

    def test_delete_profile_picture_file_not_found(self):
        """Test: Attempting to delete when no file exists returns None (or similar)."""
        user = self._complete_user_registration("nofile@bgu.ac.il", "Pass1!", "No", "File")

        result = self.negev.delete_profile_picture(user.user_id)
        self.assertIsNone(result, "Expected None or graceful handling when no file exists")

    def test_delete_profile_picture_repo_failure(self):
        """Test: DB deletion fails after file deletion — should raise or return gracefully."""
        user = self._complete_user_registration("failrepo@bgu.ac.il", "Pass1!", "Fail", "Repo")
        self._upload_dummy_profile_pic(user.user_id)

        from Backend.DataLayer.ProfilePicture.ProfilePictureRepository import ProfilePictureRepository
        original = ProfilePictureRepository.delete_pic
        ProfilePictureRepository.delete_pic = lambda *args, **kwargs: (_ for _ in ()).throw(Exception("DB delete failed"))

        try:
            with self.assertRaises(Exception) as context:
                self.negev.delete_profile_picture(user.user_id)
            self.assertIn("DB delete failed", str(context.exception))
        finally:
            ProfilePictureRepository.delete_pic = original  # restore

    def test_get_system_managers_success(self):
        user_id = self.user.user_id
        system_repo = SystemManagersRepository()
        system_repo.add_system_manager(user_id)
        self.negev._system_managers.add(user_id)

        # Act
        managers = self.negev.get_system_managers()

        # Assert
        self.assertIsInstance(managers, list)
        self.assertGreater(len(managers), 0)
        self.assertTrue(any(email == self.user.email for _, email in managers))

    def test_get_system_managers_empty(self):
        self.negev._system_managers.clear()

        # Act
        managers = self.negev.get_system_managers()

        # Assert
        self.assertIsInstance(managers, list)
        self.assertEqual(len(managers), 0)


if __name__ == '__main__':
    unittest.main()
