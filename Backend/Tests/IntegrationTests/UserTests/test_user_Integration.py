from Backend.BusinessLayer.User.UserFacade import UserFacade
import os
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from Backend.BusinessLayer.User.UserFacade import UserFacade
from Backend.BusinessLayer.Util.Exceptions import UserAlreadyRegisterToCourse
# Adjust these imports according to your project structure.
from Backend.BusinessLayer.Util.Exceptions import UserIsNotRegisterToCourse
from Backend.DataLayer.Base import delete_all_data, Base


class TestUser(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        os.environ["APP_ENV"] = "test"
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))  # העלאה של 3 רמות לתיקיית ה-Backend
        db_path = os.path.join(base_dir, "test_NegevNerds.db")  # יצירת הנתיב המוחלט לקובץ ה-DB

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
        self.session =self.Session()
        user_facade = UserFacade()
        user_facade.users_byEmail={}
        user_facade.registerWithoutAuth("u1234@post.bgu.ac.il", "pass111!D",  "נדב", "קטלב")
        self.user = user_facade.getUser_by_email("u1234@post.bgu.ac.il")




    def test_reset_new_password(self):
        last_pass = self.user.password
        self.user.reset_new_password("test@example.com", "Newpass11!")
        self.assertNotEqual(self.user.password, last_pass)  # בהנחה שפונקציה מחזירה "updated"

    def test_registerToCourse_success(self):
        self.user.registerToCourse("course1")
        self.assertIn("course1", self.user.courses)

    def test_registerToCourse_already_registered(self):
        self.user.courses = ["course1"]
        with self.assertRaises(UserAlreadyRegisterToCourse):
            self.user.registerToCourse("course1")

    def test_removeCourse_success(self):
        self.user.courses = ["course1"]
        self.user.removeCourse("course1")
        self.assertNotIn("course1", self.user.courses)

    def test_removeCourse_not_registered(self):
        self.user.courses = []
        with self.assertRaises(UserIsNotRegisterToCourse):
            self.user.removeCourse("course1")

    def test_editProfile(self):
        self.user.editProfile(
            email="changed@example.com",
            password="newpass",
            first_name="Changed",
            last_name="User"
        )
        self.assertEqual(self.user.email, "changed@example.com")
        self.assertEqual(self.user.password, "newpass")
        self.assertEqual(self.user.first_name, "Changed")
        self.assertEqual(self.user.last_name, "User")

    # def test_delete(self):
    #     user_id = self.user.user_id
    #     self.user.delete()
    #     self.assertIsNone(self.user.user_id)

    def test_get_courses(self):
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