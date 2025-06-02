import os
from datetime import datetime

from Backend.BusinessLayer.Course.CourseFacade import CourseFacade
from Backend.BusinessLayer.Course.Course import Course
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest import TestCase
from Backend.BusinessLayer.Course.enums import Semester, Moed
from Backend.DataLayer.Base import Base, delete_all_data


class TestComment(TestCase):
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

        self.course = Course(course_id="123.4.5678", name="Test Course", course_topics={"Math", "CS"})
        self.facade.courses["123.4.5678"] = self.course
        self.course_id = "123.4.5678"

        self.comment_id = "c1"
        self.writer_name = "John Doe"
        self.writer_id = "u1"
        self.date = datetime(2025, 4, 2)

        # 🛠️ במקום "None" (מחרוזת), נשתמש בערך "0" שמסמל שאין תגובה קודמת
        self.prev_id = "0"

        self.comment_text = "This is a test comment."
        self.deleted = False
        self.edited = False

        self.course.add_exam(2025, Semester.SPRING, Moed.A, "")

        question_id = self.course.add_question(
            year=2025,
            semester=Semester.SPRING,
            moed=Moed.A,
            question_number=1,
            is_american=True,
            question_topics={"Math", "Physics"},
            pdf__question_path="",
            pdf__answer_path=" ",
            question_text="2+2="
        )

        self.comment_id = self.course.add_comment(
            year=2025,
            semester=Semester.SPRING,
            moed=Moed.A,
            question_number=1,
            writer_name=self.writer_name,
            writer_id=self.writer_id,
            prev_id=self.prev_id,
            comment_text=self.comment_text,
            comment_id=self.comment_id,
            link_to_media=""
        )

        self.exam = self.course.get_exam(2025, Semester.SPRING, Moed.A)
        self.question = self.exam.get_question(1)
        self.comment = self.question.comments[0]

    def test_to_dto(self):
        # Convert the comment to a DTO and verify the content
        dto = self.comment.to_dto()
        self.assertEqual(dto.writer_name, self.writer_name)
        self.assertEqual(dto.comment_text, self.comment_text)

    def test_delete_comment(self):
        self.comment.delete_comment()
        self.assertTrue(self.comment.deleted)

    def test_edit_comment_text(self):
        new_text = "Updated comment text."
        self.comment.edit_comment_text(new_text)
        self.assertEqual(self.comment.comment_text, new_text)
        self.assertTrue(self.comment.edited)

    def test_add_reaction_new(self):
        result = self.comment.add_reaction("user1", "👍")
        self.assertEqual(len(self.comment.reactions), 1)
        self.assertEqual(result, self.writer_id)

    def test_add_reaction_same_emoji(self):
        self.comment.add_reaction("user1", "👍")
        result = self.comment.add_reaction("user1", "👍")
        self.assertIsNone(result)
        self.assertEqual(len(self.comment.reactions), 1)

    def test_add_reaction_different_emoji(self):
        self.comment.add_reaction("user1", "👎")
        result = self.comment.add_reaction("user1", "👍")
        self.assertEqual(len(self.comment.reactions), 1)

    def test_remove_reaction(self):
        self.comment.add_reaction("user1", "👍")
        self.assertEqual(len(self.comment.reactions), 1)
        self.comment.remove_reaction(self.comment.reactions[0].reaction_id)
        self.assertEqual(len(self.comment.reactions), 0)

    def test_edit_text(self):
        new_text = "New text content"
        self.comment.edit_text(new_text)
        self.assertEqual(self.comment.comment_text, new_text)
