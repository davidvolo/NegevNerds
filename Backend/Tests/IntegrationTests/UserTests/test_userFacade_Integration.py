import bcrypt
import os
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from Backend.BusinessLayer.User.UserFacade import UserFacade
from Backend.DataLayer.Base import delete_all_data, Base


class TestUser(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        os.environ["APP_ENV"] = "test"
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
        db_path = os.path.join(base_dir, "test_NegevNerds.db")

        engine = create_engine(f"sqlite:///{db_path}")
        cls.Session = sessionmaker(bind=engine)
        cls.session = cls.Session()
        cls.engine = engine
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

    @classmethod
    def tearDownClass(cls):
        Base.metadata.drop_all(cls.engine)

    def setUp(self):
        delete_all_data(engine=self.engine, session=self.session)
        self.session = self.Session()
        self.user_facade = UserFacade()
        self.user_facade.users_byEmail = {}
        self.user_facade.users_byName = {}
        self.user_facade.users_byId = {}
        self.user_id, massage = self.user_facade.registerWithoutAuth("u1234@post.bgu.ac.il", "pass111!D",  "נדב", "קטלב")
        self.user = self.user_facade.getUser_by_email("u1234@post.bgu.ac.il")

    def test_generate_user_id(self):
        user_id = self.user_facade.generateUserId()
        # Assert that the user ID starts with 'user' followed by a UUID
        self.assertTrue(user_id.startswith("user"))
        self.assertEqual(len(user_id), 40)  # "user" + 36-character UUID

    def test_hash_password(self):
        password = "TestPassword123!"
        hashed_password = self.user_facade.hash_password(password)

        # Ensure the hashed password is not the same as the plain password
        self.assertNotEqual(password, hashed_password)

        # Verify that the hashed password is a valid bcrypt hash
        self.assertTrue(bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8')))

    def test_verify_password(self):
        password = "TestPassword123!"
        hashed_password = self.user_facade.hash_password(password)

        # Test valid password
        self.assertTrue(self.user_facade.verify_password(password, hashed_password))

        # Test invalid password
        invalid_password = "WrongPassword"
        self.assertFalse(self.user_facade.verify_password(invalid_password, hashed_password))

    def test_is_valid_email(self):
        # Valid emails
        valid_email_1 = "testuser@post.bgu.ac.il"
        valid_email_2 = "testuser@bgu.ac.il"
        self.assertTrue(self.user_facade.is_valid_email(valid_email_1))
        self.assertTrue(self.user_facade.is_valid_email(valid_email_2))

        # Invalid email
        invalid_email = "testuser@gmail.com"
        self.assertFalse(self.user_facade.is_valid_email(invalid_email))

    def test_is_valid_name(self):
        # Valid names
        valid_name_1 = "משה כהן"
        valid_name_2 = "יוסי-לוי"
        self.assertTrue(self.user_facade.is_valid_name(valid_name_1))
        self.assertTrue(self.user_facade.is_valid_name(valid_name_2))

        # Invalid names
        invalid_name_1 = "John Doe"
        invalid_name_2 = "מושע@כהן"
        self.assertFalse(self.user_facade.is_valid_name(invalid_name_1))
        self.assertFalse(self.user_facade.is_valid_name(invalid_name_2))

    def test_is_valid_password(self):
        # Valid passwords
        valid_password_1 = "TestPassword1!"
        valid_password_2 = "Valid@123"
        self.assertTrue(self.user_facade.is_valid_password(valid_password_1))
        self.assertTrue(self.user_facade.is_valid_password(valid_password_2))

        # Invalid passwords
        invalid_password_1 = "short"
        invalid_password_2 = "noSpecialChar123"
        invalid_password_3 = "N@specialbutmissinglower123"
        self.assertFalse(self.user_facade.is_valid_password(invalid_password_1))
        self.assertFalse(self.user_facade.is_valid_password(invalid_password_2))
        self.assertFalse(self.user_facade.is_valid_password(invalid_password_3))

    def test_login_success(self):
        first_name, last_name, user_id, message = self.user_facade.login("u1234@post.bgu.ac.il", "pass111!D")
        self.assertEqual(first_name, "נדב")
        self.assertEqual(last_name, "קטלב")
        self.assertEqual(user_id, self.user_id)
        self.assertEqual(message, "התחברות בוצעה בהצלחה")

    def test_login_failed_incorrect_password(self):
        user_first_name, user_last_name, user_id, msg = self.user_facade.login("u1234@post.bgu.ac.il", "wrongpassword")
        self.assertIsNone(user_first_name)
        self.assertIsNone(user_last_name)
        self.assertIsNone(user_id)

    def test_logout_success(self):
        self.user_facade.login("u1234@post.bgu.ac.il", "pass111!D")
        message = self.user_facade.logout(self.user_id)
        self.assertEqual(message, "התנתקות בוצעה בהצלחה")

    def test_register_to_course(self):
        self.user_facade.registerToCourse("course_123", self.user_id)
        user = self.user_facade.getUser_by_id(self.user_id)
        self.assertIn("course_123", user.get_courses())

    def test_register_to_course_user_not_found(self):
        with self.assertRaises(Exception):
            self.user_facade.registerToCourse("course_123", "999")

    def test_edit_user_profile_user_not_found(self):
        with self.assertRaises(Exception):
            self.user_facade.editUserProfile("notfound@bgu.ac.il", first_name="Johnny")
