# Backend/Tests/SystemTest/BaseTestCase.py
import os
import unittest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from Backend.DataLayer.Base import Base, delete_all_data
from Backend.BusinessLayer.NegevNerds import NegevNerds

class BaseTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        db_path = os.path.join(base_dir, "test_NegevNerds.db")
        cls.engine = create_engine(f"sqlite:///{db_path}")
        cls.Session = sessionmaker(bind=cls.engine)
        Base.metadata.drop_all(bind=cls.engine)
        Base.metadata.create_all(bind=cls.engine)

    @classmethod
    def tearDownClass(cls):
        Base.metadata.drop_all(bind=cls.engine)

    def setUp(self):
        self.session = self.Session()
        delete_all_data(engine=self.engine, session=self.session)
        self.negev = NegevNerds(mkdir="test_directory")

    def _complete_user_registration(self, email, password, first_name, last_name):
        user, _ = self.negev.register(email, password, password, first_name, last_name)
        self.negev.register_termOfUse_part(email, password, first_name, last_name)
        return self.negev._user_facade.getUser_by_email(email)

    def _open_course(self, user, course_id, course_name):
        syllabus_path = os.path.join(os.path.dirname(__file__), "sylabus.pdf")
        return self.negev.open_course(user.user_id, course_id, course_name, syllabus_path)
