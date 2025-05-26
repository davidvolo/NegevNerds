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
    TopicAlreadyExist, TopicNotFound, UserIsNotRegisterToCourse, ExamAlreadyExists
from Backend.DataLayer.DTOs.CourseDTO import CourseDTO
from Backend.DataLayer.DTOs.QuestionDTO import QuestionDTO

from Backend.DataLayer.DTOs.SearchDTO import SearchDTO

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest import TestCase
from Backend.BusinessLayer.Course.enums import Semester, Moed
from Backend.DataLayer.Base import Base, delete_all_data

from Backend.DataLayer.UserData import UserModel  # Import the UserModel
from Backend.DataLayer.ReactionData import ReactionModel # Import the ReactionModel
from Backend.DataLayer.Questions import QuestionModel
from Backend.DataLayer.QuestionTopics import QuestionTopicsModel
from Backend.DataLayer.CourseTopics import CourseTopicsModel

from Backend.DataLayer.CourseData import CourseModel  # Import other models as needed
from Backend.ServiceLayer.ServiceLayer import ServiceLayer


class TestCourse(TestCase):

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
            question_number=1,
            is_american=True,
            question_topics={"Math", "Physics"},
            pdf__question_path="q_path",
            pdf__answer_path="a path",
            question_text="2+2="
        )
        self.exam = self.course.get_exam(2025, Semester.SPRING, Moed.A)
        self.question = self.exam.get_question(1)

    def test_get_id(self):
        self.assertEqual(self.course.get_id(), self.course_id)

    def test_get_exams_by_year(self):
        exams = self.course.get_exams_by_year(2025)
        self.assertEqual(len(exams) , 2)
        self.assertEqual(exams[0].year, 2025)
        self.assertEqual(exams[1].year, 2025)



    def test_get_all_exams(self):
        # Use actual or in-memory data for testing

        exams = self.course.get_all_exams()
        self.assertEqual(len(exams), 3)

    def test_get_questions_by_specific_no_year(self):

        result = self.course.get_questions_by_specific(question_number=1)
        self.assertEqual(len(result), 1)



    def test_get_exam_found_in_repo(self):

        self.course.exams = {}
        exam = self.course.get_exam(2025, Semester.SPRING, Moed.A)
        self.assertIsNotNone(exam)

    def test_get_exams_success(self):

        exams = self.course.get_exams(2025, semester=Semester.SPRING, moed=Moed.A)
        self.assertEqual(len(exams),1 )

    def test_get_exams_not_found(self):
        self.course.exams = {}
        with self.assertRaises(ExamIsNotExist):
            self.course.get_exams(2025, semester=Semester.SUMMER, moed="A")


    def test_set_syllabus(self):
        self.course.set_syllabus("Syllabus Content")
        self.assertEqual(self.course.syllabus, "Syllabus Content")

    def test_add_course_topic_success(self):
        self.course.course_topics = set()
        self.course.add_course_topic("new_topic")
        self.assertIn("new_topic", self.course.course_topics)

    def test_add_course_topic_already_exists(self):
        self.course.course_topics = ["topic1"]
        with self.assertRaises(TopicAlreadyExist):
            self.course.add_course_topic("topic1")

    def test_remove_course_topic_success(self):
        self.course.course_topics = ["topic1", "topic2"]
        self.course.remove_course_topic("topic1")
        self.assertNotIn("topic1", self.course.course_topics)

    def test_remove_course_topic_not_found(self):
        self.course.course_topics = ["topic1"]
        with self.assertRaises(TopicNotFound):
            self.course.remove_course_topic("topic2")

    def test_add_student_success(self):
        self.course.users = []
        self.course.add_student("user1")
        self.assertIn("user1", self.course.users)

    def test_remove_student_success(self):
        self.course.users = ["user1", "user2"]
        self.course.remove_student("user1")
        self.assertNotIn("user1", self.course.users)

    def test_remove_student_not_registered(self):
        self.course.users = ["user2"]
        with self.assertRaises(UserIsNotRegisterToCourse):
            self.course.remove_student("user1")

    def test_generate_exam_id(self):
        exam_id = self.course.generate_exam_id(2025, "SPRING", "A")
        expected = f"EXAM-{self.course_id}-2025-SPRING-A"
        self.assertEqual(exam_id, expected)

    def test_add_exam_success(self):

        self.course.add_exam(2023, Semester.SPRING, Moed.C, link="exam_link")
        self.assertIn(2023, self.course.exams)
        self.assertTrue( len(self.course.exams[2023])>0)

    def test_add_exam_already_exists(self):
        # Add a dummy exam

        # Try to add a duplicate exam, should raise ExamAlreadyExists
        with self.assertRaises(ExamAlreadyExists):
            self.course.add_exam(2025, Semester.SPRING, Moed.A, link="exam_link")

    def test_remove_exam_success(self):
        # Add a dummy exam

        self.assertIsNotNone(self.course.get_exam(2025, Semester.SPRING, Moed.A))

        # Remove the exam and check if it is removed
        self.course.remove_exam(2025, Semester.SPRING, Moed.A)
        self.assertIsNone(self.course.get_exam(2025, Semester.SPRING,Moed.A))

    def test_remove_exam_not_found(self):
        # Trying to remove an exam that does not exist
        with self.assertRaises(ExamIsNotExist):
            self.course.remove_exam(2015, Semester.SPRING, Moed.A)

    def test_get_exam_full_pdf_success(self):
        # Add a dummy exam

        # Test if the PDF link is returned
        link = self.course.get_exam_full_pdf(2025, Semester.SPRING, Moed.A)
        self.assertEqual(link, "link1")

    def test_get_exam_full_pdf_not_found(self):
        # No exam exists
        with self.assertRaises(ExamIsNotExist):
            self.course.get_exam_full_pdf(2015, Semester.SPRING, Moed.A)

    def test_check_exam_full_pdf_true(self):
        # Add a dummy exam with a PDF link

        # Check if the exam has a full PDF link
        result = self.course.check_exam_full_pdf(2025, Semester.SPRING, Moed.A)
        self.assertTrue(result)

    def test_add_comment(self):
        # Create an exam and add a comment
        result = self.course.add_comment(
            year=2025,
            semester="אביב",
            moed="א",
            question_number=1,
            writer_name="John Doe",
            writer_id="writer1",
            prev_id="0",
            comment_text="Nice question",
            comment_id="c42",
            link_to_media=""
        )
        self.assertEqual("0", result)

    def test_get_answer_path(self):
        # Test getting the answer path
        result = self.course.get_answer_path(2025,"אביב", "א", 1)
        self.assertEqual(result, "a path")

    def test_check_valid_question_exam_none(self):
        # Add a dummy exam
        # Check question availability when exam doesn't exist
        result, exam_id = self.course.checkQuestionAvailability(2025, Semester.SPRING, Moed.A, 1)
        self.assertFalse(result)

    def test_edit_exam_year(self):
        # Add a dummy exam
        # Edit the exam year
        self.assertEqual(len(self.course.get_exams_by_year(2025)), 2)
        self.course.edit_exam_year(2025, Semester.SPRING, Moed.A, 2030)
        self.assertEqual(len(self.course.get_exams_by_year(2025)), 1)
        self.assertEqual(len(self.course.get_exams_by_year(2030)), 1)


    def test_get_question_path(self):
        # Create a real exam


        result = self.course.get_question_path(2025, "אביב", "א", 1)
        self.assertEqual(result, "q_path")

    def test_get_answer_path(self):
        # Create a real exam

        result = self.course.get_answer_path(2025, "אביב", "א", 1)
        self.assertEqual(result, "a path")

    def test_get_question_id(self):
        # Create a real exam
        result = self.course.get_question_id(2025, "אביב", "א", 1)
        self.assertTrue("question" in result)

    def test_get_question_id_and_path(self):
        # Create a real exam
        result , id = self.course.get_question_id_and_path(2025, "אביב", "א", 1)
        self.assertEqual(result, "a path")
        self.assertTrue("question" in  id )

    def test_delete_comment(self):
        # Create a real exam and question
        self.question.add_comment("c1", "writer", "writer_id", "0", "comment_des", False, False, "")
        self.assertEqual(len(self.question.comments), 1)
        self.course.delete_comment(2025, "אביב","א", 1, self.question.comments[0].comment_id)
        self.assertEqual(len(self.question.comments), 1)
        self.assertEqual(self.question.comments[0].deleted,True)


    def test_edit_comment_text(self):
        # Create a real exam and question

        self.question.add_comment("c1", "writer", "writer_id", "0", "comment_des", False, False, "")
        comment_id = self.question.comments[0].comment_id
        self.course.edit_comment_text(2025, "אביב", "א", 1, comment_id, "Updated text")
        self.assertEqual(self.question.comments[0].edited, True)
        self.assertEqual(self.question.comments[0].comment_text, "Updated text")




    def test_add_question(self):
        # Create a real exam and add a question


        question_id = self.course.add_question(2025, Semester.SPRING, Moed.A,  2, True, ["topic1"], "q.pdf", "a.pdf", "question text")
        self.assertTrue("question" in question_id)


    def test_edit_question_topic(self):
        # Create a real exam and edit the question topic

        self.course.add_course_topic("new_topic")
        result = self.course.edit_question_topic(2025, "אביב", "א", 1, ["new_topic"])
        self.assertEqual(result, True)

    def test_checkQuestionAvailability_exam_none(self):

        result, exam_id = self.course.checkQuestionAvailability(2023, "קיץ", "א", 1)
        self.assertTrue(result)
        self.assertTrue("EXAM" in exam_id)

    def test_checkQuestionAvailability_exam_exists(self):
        # Create a real exam instance

        result, exam_id = self.course.checkQuestionAvailability(2025, "אביב", "א", 1)
        self.assertFalse(result)
        self.assertTrue("EXAM" in exam_id, )

    def test_edit_question_details(self):

        result = self.course.edit_question_details(
            2025, "אביב", "א", 1,
            2030, "אביב", "א", 2,
            "exam123", "new_q.pdf", "new_a.pdf"
        )
        self.assertEqual(result, True)