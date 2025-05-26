import os
import unittest

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from Backend.DataLayer.Base import Base, delete_all_data
from Backend.BusinessLayer.NegevNerds import NegevNerds
import io
from werkzeug.datastructures import FileStorage
import bcrypt


class BaseTestCase(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["APP_ENV"] = "test"  # חשוב להבטיח שהקוד ירוץ על סביבה טסט
        # שימוש בדאטהבייס הקיים: instance/test_negevnerds.db
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        db_path = os.path.join(base_dir, "instance", "test_negevnerds.db")

        cls.engine = create_engine(f"sqlite:///{db_path}")
        cls.Session = sessionmaker(bind=cls.engine)

        # Drop and create all tables fresh
        Base.metadata.drop_all(bind=cls.engine)
        Base.metadata.create_all(bind=cls.engine)

    @classmethod
    def tearDownClass(cls):
        Base.metadata.drop_all(bind=cls.engine)

    def setUp(self):
        self.session = self.Session()
        os.environ["APP_ENV"] = "test"  # שימוש בדאטהבייס טסט
        delete_all_data(engine=self.engine, session=self.session)
        self.negev = NegevNerds(mkdir="test_directory")

    def tearDown(self):
        # מחיקת דאטה אחרי כל טסט
        delete_all_data(engine=self.engine, session=self.session)
        # try:
        #     Base.metadata.drop_all(bind=self.engine)
        # except Exception:
        #     pass
        self.session.close()

    def _encrypt_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

    def _complete_user_registration(self, email, password, first_name, last_name):
        user, _ = self.negev.register(email, password, password, first_name, last_name)
        encrypted_password = self._encrypt_password(password)
        self.negev.register_termOfUse_part(email, encrypted_password, first_name, last_name, profile_picture_file=None)
        return self.negev._user_facade.getUser_by_email(email)

    def _open_course(self, user, course_id, course_name):
        syllabus_path = os.path.join(os.path.dirname(__file__), "sylabus.pdf")
        return self.negev.open_course(user.user_id, course_id, course_name, syllabus_path)

    def _mock_pdf_file(self, filename="exam.pdf", content=b"%PDF-1.4\nFake PDF content"):
        stream = io.BytesIO(content)
        return FileStorage(stream=stream, filename=filename, content_type='application/pdf')

