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
from Backend.BusinessLayer.Util.Exceptions import CourseAlreadyExists, InvalidCourseIdFormat
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


class TestCourseFacade(TestCase):

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

    def test_register_to_course(self):
        course = self.facade.get_course("123.4.5678")
        course.add_student("user1")
        self.assertIn("user1", course.users)

    def test_get_questions_dto_by_search_dtos(self):
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

        search_dto = SearchDTO(question_id=question_id, course_id="123.4.5678")
        result: List = self.facade.get_questions_dto_by_search_dtos([search_dto])
        self.assertEqual(result[0].question_id, question_id)

    def test_get_questions_dto_by_ids(self):
        # Create a question and add it to the course

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

        # Get the question DTO by IDs
        result = self.facade.get_questions_dto_by_ids([question_id], self.course.course_id)

        # Verify that the returned result is correct
        self.assertEqual(result[0].question_id, question_id)
        self.assertEqual(result[0].question_number, 1)



    def test_remove_student_from_course(self):
        # Add a student to the course
        self.facade.open_course("1.123.1234", "new course", [])
        curr_course  = self.facade.get_course("1.123.1234")
        curr_course.add_student("user1")
        # Remove the student
        self.facade.remove_student_from_course("1.123.1234", "user1")

        # Check that the student was removed
        self.assertNotIn("user1", curr_course.users)

    def test_open_course(self):
        new_course_id = "234.5.6789"
        new_course_name = "New Course"
        new_course_topics = ["topicX", "topicY"]

        # Open the new course
        self.facade.open_course(new_course_id, new_course_name, new_course_topics)

        # Verify that the new course is in the courses dictionary
        self.assertIn(new_course_id, self.facade.courses)
        self.assertEqual(self.facade.courses[new_course_id].name, new_course_name)
        for topic in new_course_topics:
            self.assertTrue(topic in self.facade.courses[new_course_id].course_topics )

    def test_open_course_already_exist(self):

        with self.assertRaises(CourseAlreadyExists) as context:
            self.facade.open_course_possibility("123.4.5678", "קורס לא תקין")

        # Check the message of the raised exception
        self.assertEqual(str(context.exception), "Course 123.4.5678 is already exist.")

    def test_open_course_possibility(self):

        # Call the open_course_possibility method
        result = self.facade.open_course_possibility("133.4.5678", "קורס תקין")

        # Assert that the result is True
        self.assertTrue(result)

    def test_open_course_possibility_invalid_id(self):


        # Try to open a course with an invalid ID format, and assert that it raises an exception
        with self.assertRaises(InvalidCourseIdFormat):
            self.facade.open_course_possibility("invalid_id", "valid name")

    def test_remove_course(self):
        # Add the course to the facade
        self.facade.open_course("1.123.1234", "new course", ["new topic"])
        # Remove the course
        self.assertIsNotNone(self.facade.courses["1.123.1234"])
        self.facade.remove_course("1.123.1234")

        # Assert that the course is no longer in the courses dictionary
        self.assertNotIn("1.123.1234", self.facade.courses)

    def test_get_question_id(self):
        # Directly call the method without mocking

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

        result = self.facade.get_question_id(self.course.course_id, 2025, "אביב", "א", 1)


        # Assert that the result from the facade matches the expected result
        self.assertEqual(result, question_id)



    def test_get_all_courses(self):
        # Directly retrieve all courses from the repository
        self.facade.open_course("1.123.1234", "new course", ["new"])
        self.facade.open_course("1.123.1254", "new course", ["new"])

        result = self.facade.get_all_courses()  # Assuming this calls the real method to get courses

        # Assert that the result is a list of CourseDTO objects
        self.assertEqual(len(result), 2)  # You can adjust this based on your real data
        for dto in result:
            self.assertIsInstance(dto, CourseDTO)

    def test_get_course_DTO(self):
        # Directly call the method without mocking
        result = self.facade.get_course_DTO(self.course.course_id)

        # Assuming the get_course method returns a valid course object
        course = self.facade.get_course(self.course.course_id)

        # Assert that the result is a CourseDTO and its values are correct
        self.assertIsInstance(result, CourseDTO)
        self.assertEqual(result.get_course_id(), self.course.course_id)
        self.assertEqual(result.get_name(), course.get_name())  # Assuming the course has a name method

    def test_get_courses_DTO(self):
        # Directly call the method without mocking
        result = self.facade.get_courses_DTO([self.course.course_id])

        # Assert the returned value is a list of CourseDTO objects
        self.assertEqual(len(result), 1)  # Assuming one course is fetched
        self.assertIsInstance(result[0], CourseDTO)

    def test_get_course_topics(self):
        # Directly call the method without mocking
        result = self.facade.get_course_topics(self.course.course_id)

        # Assuming the real get_course method inside the facade returns a valid course object
        course = self.facade.get_course(self.course.course_id)
        result_from_course = course.get_topics()  # Assuming the course has a get_topics method

        # Assert that the result from the facade matches the expected result
        self.assertEqual(result, result_from_course)

    def test_check_valid_question(self):
        # Directly call the method without mocking
        result = self.facade.check_valid_question(self.course.course_id, 2025, "אביב", "א", 1, "text")

        # Assuming the real get_course method inside the facade returns a valid course object
        course = self.facade.get_course(self.course.course_id)
        result_from_course = course.check_valid_question(
            year=2025,
            semester=Semester("אביב"),  # Assuming Semester is a valid class
            moed=Moed("א"),  # Assuming Moed is a valid class
            question_number=1,
            question_text="text"
        )

        # Assert that the result from the facade matches the expected result
        self.assertEqual(result, result_from_course)

    def test_add_question(self):
        # Directly call the method without mocking
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
        # Assuming the real get_course method inside the facade returns a valid course object
        course:Course = self.facade.get_course(self.course_id)
        # Assert that the result from the facade matches the expected result
        self.assertIsNotNone(course.get_questions_by_specific(year=2025, semester=Semester.SPRING, moed=Moed.A, question_number=1))

    def test_upload_full_exam_pdf(self):
        # Directly call the method without mocking

        self.course.add_exam(2025, Semester.SPRING, Moed.A, "")
        result = self.facade.upload_full_exam_pdf(self.course_id, 2025, "אביב", "א", "new_exam.pdf")

        # Assuming the real get_course method inside the facade returns a valid course object
        course = self.facade.get_course(self.course_id)
        result_from_course = course.upload_full_exam_pdf(2025, "אביב", "א", "new_exam.pdf")

        # Assert that the result from the facade matches the expected result
        self.assertEqual(result, result_from_course)

    def test_add_topic_to_question(self):
        # Directly call the method without mocking
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

        self.facade.add_topic_to_question(self.course_id, 2025, "אביב", "א", 1, "new_topic")

        # Assuming the real get_course method inside the facade returns a valid course object
        course = self.facade.get_course(self.course_id)
        exam = course.get_exam(2025, "אביב", "א")
        question = exam.get_question(1)

        # Assert that the result from the facade matches the expected result
        self.assertTrue("new_topic" in question.question_topics)

    def test_remove_topic_from_question(self):
        # Directly call the method without mocking
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
        course = self.facade.get_course(self.course_id)
        exam = course.get_exam(2025, "אביב", "א")
        question = exam.get_question(1)

        self.assertTrue("Math" in question.question_topics)
        result = self.facade.remove_topic_from_question(self.course_id, 2025, "אביב", "א", 1, "Math")

        # Assuming the real get_course method inside the facade returns a valid course object


        # Assert that the result from the facade matches the expected result
        self.assertEqual(len(question.question_topics), 1)
        self.assertFalse("Math" in question.question_topics)

    def test_search_question_by_specifics(self):

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

        result = self.facade.search_question_by_specifics(self.course_id, 2025, "אביב", "א", 1)

        # Assuming the real get_course method inside the facade returns a valid course object
        course = self.facade.get_course(self.course_id)
        exam = course.get_exam(2025, "אביב", "א")
        result_from_course = exam.get_questions_by_specific(1)  # Ensure real method is used

        # Assert that the result from the facade matches the expected result
        self.assertEqual(result[0].question_id, result_from_course[0].question_id)
        self.assertIsNotNone(result)

    def test_search_questions_by_topic(self):
        # Directly call the method without mocking
        result = self.facade.search_questions_by_topic(self.course_id, "topic1")

        # Assuming the real get_course method inside the facade returns a valid course object
        course = self.facade.get_course(self.course_id)
        exams = course.get_all_exams()
        result_from_course = []

        for exam in exams:
            questions = exam.get_all_exam_question()
            for question in questions:
                if "topic1" in question.get_question_topics():
                    result_from_course.append(question.to_dto())

        # Assert that the result from the facade matches the expected result
        self.assertEqual(result, result_from_course)




    def test_edit_question_topic(self):
        # Directly call the method without mocking

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
        question = self.course.get_questions_by_specific(2025, Semester.SPRING, Moed.A,1)

        self.assertEqual(question[0].question_topics, {"Math", "Physics"})

        self.facade.edit_question_topic(self.course_id, 2025, "אביב", "א", 1, ["new_topic"])

        question = self.course.get_questions_by_specific(2025, Semester.SPRING, Moed.A,1)
        # Assert that the result from the facade matches the expected result
        self.assertEqual(question[0].question_topics, {"new_topic"})

