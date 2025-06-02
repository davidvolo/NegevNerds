import os
import unittest

# Adjust these imports according to your project structure.
from Backend.BusinessLayer.Course.CourseFacade import CourseFacade
from Backend.BusinessLayer.Util.Exceptions import QuestionDoesNotMeetExamFields, QuestionAlreadyInExam, QuestionNotFound

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from Backend.BusinessLayer.Course.enums import Semester, Moed
from Backend.DataLayer.Base import Base, delete_all_data


class TestExam(unittest.TestCase):

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
        self.session = self.Session()
        self.facade = CourseFacade()

        self.facade.open_course("123.4.5678", "new course", ["topic1", "topic 2"])
        self.course_id = "123.4.5678"
        self.course = self.facade.get_course(self.course_id)
        self.course.add_exam(2025, Semester.SPRING, Moed.A, "link1")
        self.course.add_exam(2025, Semester.FALL, Moed.B, "link2")
        self.course.add_exam(2024, Semester.FALL, Moed.B, "link2")
        question_id = self.course.add_question(
            year=2025,
            semester=Semester.SPRING,
            moed=Moed.A,
            question_number=2,
            is_american=True,
            question_topics={"Math", "Physics"},
            pdf__question_path="q_path",
            pdf__answer_path="a path",
            question_text="2+2="
        )
        self.exam = self.course.get_exam(2025, Semester.SPRING, Moed.A)
        self.question = self.exam.get_question(1)

    def test_generate_question_id(self):
        qid = self.exam.generate_question_id()
        self.assertTrue(qid.startswith("question"))

    def test_add_question_success(self):
        returned_id = self.exam.add_question(
            question_number=1,
            is_american=True,
            question_topics=["topic1"],
            pdf__question_path="question.pdf",
            pdf__answer_path="answer.pdf",
            question_text="What is unit testing?"
        )
        self.assertIn(1, self.exam.questions_list)
        self.assertEqual(self.exam.questions_list[1].id, returned_id)

    def test_add_question_failure(self):
        # Force a failure by passing bad arguments (e.g., missing text)
        with self.assertRaises(Exception):
            self.exam.add_question(
                question_number=2,
                is_american=False,
                question_topics=["topic2"],
                pdf__question_path="q2.pdf",
                pdf__answer_path="a2.pdf",
                question_text=None
            )

    def test_check_add_question_possibility_valid(self):
        result = self.exam.check_add_question_possibility(
            year=self.exam.year,
            semester=self.exam.semester,
            moed=self.exam.moed,
            question_number=99
        )
        self.assertTrue(result)

    def test_check_add_question_possibility_already_exists(self):
        self.exam.add_question(
            question_number=1,
            is_american=True,
            question_topics=["topic"],
            pdf__question_path="q.pdf",
            pdf__answer_path="a.pdf",
            question_text="test"
        )
        with self.assertRaises(QuestionAlreadyInExam):
            self.exam.check_add_question_possibility(
                year=self.exam.year,
                semester=self.exam.semester,
                moed=self.exam.moed,
                question_number=1
            )

    def test_check_add_question_possibility_fields_mismatch(self):
        with self.assertRaises(QuestionDoesNotMeetExamFields):
            self.exam.check_add_question_possibility(
                year=self.exam.year - 1,
                semester=self.exam.semester,
                moed=self.exam.moed,
                question_number=1
            )

    def test_get_question_path_success(self):
        self.exam.add_question(
            question_number=1,
            is_american=True,
            question_topics=["topic"],
            pdf__question_path="path/to/question.pdf",
            pdf__answer_path="path/to/answer.pdf",
            question_text="text"
        )
        result = self.exam.get_question_path(1)
        self.assertEqual(result, "path/to/question.pdf")

    def test_get_question_path_not_found(self):
        with self.assertRaises(QuestionNotFound):
            self.exam.get_question_path(99)
