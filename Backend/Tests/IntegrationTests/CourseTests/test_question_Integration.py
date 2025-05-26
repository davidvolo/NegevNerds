import os
import unittest
from typing import List
from unittest.mock import patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# Adjust these imports according to your project structure.
from Backend.BusinessLayer.Course.CourseFacade import CourseFacade
from Backend.BusinessLayer.Course.Course import Course
from Backend.BusinessLayer.Course.Question import Question
from Backend.BusinessLayer.Course.Question import Question
from Backend.BusinessLayer.Util.Exceptions import CourseAlreadyExists, InvalidCourseIdFormat, ExamIsNotExist, \
    TopicAlreadyExist, TopicNotFound, UserIsNotRegisterToCourse, ExamAlreadyExists, QuestionDoesNotMeetExamFields, \
    QuestionAlreadyInExam, QuestionNotFound
from Backend.DataLayer.DTOs.CourseDTO import CourseDTO
from Backend.DataLayer.DTOs.QuestionDTO import QuestionDTO

from Backend.DataLayer.DTOs.SearchDTO import SearchDTO

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest import TestCase
from Backend.BusinessLayer.Course.enums import Semester, Moed
from Backend.DataLayer.Base import Base, delete_all_data
from Backend.DataLayer.QuestionTopics.QuestionTopicsRepository import QuestionTopicsRepository

from Backend.DataLayer.UserData import UserModel  # Import the UserModel
from Backend.DataLayer.ReactionData import ReactionModel # Import the ReactionModel
from Backend.DataLayer.Questions import QuestionModel
from Backend.DataLayer.QuestionTopics import QuestionTopicsModel
from Backend.DataLayer.CourseTopics import CourseTopicsModel

from Backend.DataLayer.CourseData import CourseModel  # Import other models as needed
from Backend.ServiceLayer.ServiceLayer import ServiceLayer

class TestQuestion(unittest.TestCase):
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

        self.facade.open_course("123.4.5678", "new course" ,["topic1", "topic 2"])
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
        self.question = self.exam.get_question(2)

        self.question.add_comment(
            comment_id="123445",
            writer_name="Alice",
            writer_id="alice123",
            prev_id="0",
            comment_text="Looks good",
            deleted=False,
            edited=False,
            link_to_media=""
        )

        self.comment = self.question.comments[0]
        self.prev_id = self.question.comments[0].comment_id

    def test_to_dto(self):

        dto = self.question.to_dto("course123")
        self.assertIsInstance(dto, QuestionDTO)
        self.assertEqual(dto.question_id, self.question.id)
        self.assertEqual(dto.year, self.question.year)
        self.assertEqual(dto.question_number, self.question.question_number)
        self.assertEqual(dto.question_topics, self.question.question_topics)
        self.assertEqual(dto.is_american, self.question.is_american)
        self.assertEqual(dto.link_to_question, self.question.link_to_question)
        self.assertEqual(dto.course_id, "course123")
        self.assertEqual(len(dto.comments_list), 1)

    def test_generate_comment_id(self):
        comment_id = self.question.generate_comment_id()
        self.assertTrue(comment_id.startswith("comment"))

    def test_get_link_to_question(self):
        self.assertEqual(self.question.get_link_to_question(), self.question.link_to_question)

    def test_get_link_to_answer(self):
        self.assertEqual(self.question.get_link_to_answer(), self.question.link_to_answer)

    def test_add_question_topic(self):
        new_topic = "algorithms"
        self.assertNotIn(new_topic, self.question.question_topics)
        self.question.add_question_topic(new_topic)
        self.assertIn(new_topic, self.question.question_topics)

    def test_generate_question_details_name(self):
        expected = f"E-{self.question.year}-{self.question.semester}-{self.question.moed}-Q{self.question.question_number}"
        self.assertEqual(self.question.generate_question_details_name(), expected)

    def test_remove_question_topic_found(self):
        topic_to_remove = "Math"
        self.assertIn(topic_to_remove, self.question.question_topics)
        self.question.remove_question_topic(topic_to_remove)
        self.assertNotIn(topic_to_remove, self.question.question_topics)

    def test_remove_question_topic_not_found(self):
        topic_not_present = "not_a_topic"
        original_topics = self.question.question_topics.copy()
        self.question.remove_question_topic(topic_not_present)
        self.assertEqual(self.question.question_topics, original_topics)

    def test_add_comment_success(self):

        result = self.question.add_comment(
            comment_id="c2",
            writer_name="Alice",
            writer_id="alice123",
            prev_id=self.prev_id,
            comment_text="Looks good",
            deleted=False,
            edited=False,
            link_to_media=""
        )
        self.comment = self.question.comments[1]
        self.assertEqual(len(self.question.comments), 2)
        self.assertEqual(result, "alice123")
        self.assertEqual(self.question.comments[1].writer_id, "alice123")

    def test_add_reaction_success(self):
        result = self.question.add_reaction(self.comment.comment_id, "user1", "👍")
        self.assertEqual("alice123", result)
        self.assertEqual(self.comment.reactions[0].emoji, "👍")


    def test_add_reaction_not_found(self):
        with self.assertRaises(Exception):  # CommentNotFound
            self.question.add_reaction("nonexistent", "user1", "👍")

    def test_delete_comment_success(self):

        comment_id = self.comment.comment_id
        self.question.delete_comment(comment_id)
        self.assertTrue(self.comment.deleted)

    def test_delete_comment_not_found(self):
        with self.assertRaises(Exception):  # CommentNotFound
            self.question.delete_comment("nonexistent")

    def test_edit_comment_text_not_found(self):
        with self.assertRaises(Exception):  # CommentNotFound
            self.question.edit_comment_text("nonexistent", "New text")

    def test_uploadSolution_success(self):
        new_answer_path = "new_answer.pdf"
        result = self.question.uploadSolution(new_answer_path)
        self.assertEqual(self.question.link_to_answer, new_answer_path)
        self.assertEqual(result["status"], "success")

    def test_uploadSolution_failure(self):
        # Force an error by setting id to None or something invalid
        self.question.id = None
        result = self.question.uploadSolution("broken.pdf")
        self.assertEqual(result["status"], "error")
        self.assertIn("message", result)

    def test_remove_reaction_success(self):

        self.comment.add_reaction("user2", "🔥")
        self.question.remove_reaction(self.comment.comment_id, "user2")
        self.assertNotIn("user2", self.comment.reactions)

    def test_remove_reaction_not_found(self):
        with self.assertRaises(Exception):  # CommentNotFound
            self.question.remove_reaction("nonexistent", "reaction1")

    def test_edit_question_topic(self):
        new_topics = ["new_topic"]
        result = self.question.edit_question_topic(new_topics)
        self.assertEqual(self.question.question_topics, set(new_topics))

    def test_str(self):

        s = str(self.question)
        self.assertIn(self.question.id, s)
        self.assertIn(str(self.question.year), s)
        self.assertIn(str(self.question.question_number), s)
        self.assertIn(str(len(self.question.comments)), s)


