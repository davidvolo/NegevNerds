import json
import unittest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch

from Backend.BusinessLayer.NegevNerds import NegevNerds
from Backend.BusinessLayer.Util.Exceptions import CourseIsNotExist
from Backend.DataLayer.Base import Base, delete_all_data
from Backend.DataLayer.UserData.UserModel import UserModel
from Backend.Tests.SystemTest.BaseTestCase import BaseTestCase
from Backend.DataLayer.SystemManagers.SystemManagersRepository import SystemManagersRepository


class TestNegevNerdsCourseManagement(BaseTestCase):
    """
    This class contains system tests for the course management functionality
    of the NegevNerds system. These include:
    - Opening and removing courses
    - Registering and removing students from courses
    - Checking user roles and retrieving courses
    Each test uses a real database and avoids mocking for full integration validation.
    """

    @classmethod
    def setUpClass(cls):
        """Create test database and schema before all tests."""
        os.environ["APP_ENV"] = "test"
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
        db_path = os.path.join(base_dir, "test_NegevNerds.db")
        engine = create_engine(f"sqlite:///{db_path}")
        cls.Session = sessionmaker(bind=engine)
        cls.engine = engine
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

    @classmethod
    def tearDownClass(cls):
        """Drop test schema and verify DB is clean after all tests."""
        session = cls.Session()
        user_count = session.query(UserModel).count()
        assert user_count == 0, f"Expected 0 users in DB after tests, found {user_count}"
        session.close()
        Base.metadata.drop_all(cls.engine)

    def setUp(self):
        """Clear data and create a fresh instance of NegevNerds before each test."""
        self.session = self.Session()
        delete_all_data(engine=self.engine, session=self.session)
        self.negev = NegevNerds(mkdir="test_directory")

    def _extract_course_ids(self, courses):
        """Helper: extract course IDs from various formats including DTOs."""
        if isinstance(courses, list):
            course_ids = []
            for course in courses:
                if isinstance(course, dict):
                    course_ids.append(course.get("course_id"))
                elif hasattr(course, "course_id"):
                    course_ids.append(course.course_id)
                elif hasattr(course, "get_course_id") and callable(course.get_course_id):
                    course_ids.append(course.get_course_id())
                elif isinstance(course, str):
                    course_ids.append(course)
                else:
                    self.fail(f"Unexpected course object type: {type(course)}")
            return course_ids
        elif isinstance(courses, str):
            return [courses]
        else:
            self.fail(f"Unexpected type for courses: {type(courses)}")

    def _get_syllabus_path(self):
        """Returns the path to the test syllabus file."""
        return os.path.join(os.path.dirname(__file__), "sylabus.pdf")

    def _open_course(self, user, course_id, course_name):
        """Helper: open a course using the given user and return the response."""
        return self.negev.open_course(user.user_id, course_id, course_name, self._get_syllabus_path())

    # --- Test Cases Begin Below ---
    def test_open_course_success(self):
        """Verify a user can successfully open a new course."""
        user = self._complete_user_registration("creator@bgu.ac.il", "Pass1!", "Creator", "User")
        response = self._open_course(user, "987.1.1010", "מבוא למדעי המחשב")
        self.assertEqual(response, "Course מבוא למדעי המחשב opened successfully ")
        course_ids = self._extract_course_ids(user.get_courses() if hasattr(user, "get_courses") else user.courses)
        self.assertIn("987.1.1010", course_ids)

    def test_open_course_duplicate(self):
        """Verify that opening an existing course again returns an error."""
        user = self._complete_user_registration("dup@bgu.ac.il", "Pass1!", "Dup", "User")
        course_id = "101.1.1010"
        self._open_course(user, course_id, "מבוא למדעי המחשב")
        response = self._open_course(user, course_id, "מבוא למדעי המחשב")
        self.assertIn("Error", response)

    def test_user_becomes_course_manager_after_opening(self):
        """Verify a user becomes course manager after opening the course."""
        user = self._complete_user_registration("manager@post.bgu.ac.il", "Pass1!", "Manager", "User")
        course_id = "103.1.1010"
        course_name = "מבני נתונים"
        self._open_course(user, course_id, course_name)
        is_manager = self.negev.courseFacade.is_course_manager(course_id, user.user_id)
        self.assertTrue(is_manager)

    def test_remove_course_success(self):
        """Verify system manager can remove a course."""
        user = self._complete_user_registration("sysadmin@bgu.ac.il", "Pass1!", "מנהל", "מערכת")
        course_id = "202.1.1010"

        self._open_course(user, course_id, "קורס לבדיקה")

        SystemManagersRepository().add_system_manager(user.user_id)

        self.assertTrue(self.negev.is_system_manager(user.user_id), "User should be a system manager")

        response = self.negev.remove_course(course_id, user.user_id)
        print(response)

        self.assertEqual(response["status"], "success")
        self.assertIn("removed successfully", response["message"])

    def test_remove_course_invalid_user(self):
        """Verify a user who is not the course manager cannot remove it."""
        user = self._complete_user_registration("notowner@bgu.ac.il", "Pass1!", "Not", "Owner")
        response = self.negev.remove_course("nonexistent_course", user.user_id)

        self.assertEqual(response["status"], "error")

    def test_register_to_course_success(self):
        """Verify a second user can register to an existing course."""
        creator = self._complete_user_registration("creator@bgu.ac.il", "Pass1!", "Creator", "User")
        student = self._complete_user_registration("student@bgu.ac.il", "Pass1!", "Student", "User")
        course_id = "222.1.1010"
        self._open_course(creator, course_id, "תכנות מונחה עצמים")
        response = self.negev.registerToCourse(course_id, student.user_id)
        self.assertEqual(response, "UserData successfully registered to the course.")
        course_ids = self._extract_course_ids(student.get_courses() if hasattr(student, "get_courses") else student.courses)
        self.assertIn(course_id, course_ids)

    def test_register_to_course_already_registered(self):
        """Verify that a user cannot register twice to the same course."""
        user = self._complete_user_registration("dupeuser@bgu.ac.il", "Pass1!", "Duplicate", "User")
        course_id = "654.2.1010"
        self._open_course(user, course_id, "תכנות למתחילים")
        course_ids = self._extract_course_ids(user.get_courses() if hasattr(user, "get_courses") else user.courses)
        self.assertIn(course_id, course_ids, "User should be automatically registered after opening the course.")
        duplicate_response = self.negev.registerToCourse(course_id, user.user_id)
        self.assertIn("already", duplicate_response,
                      "Expected error message indicating user is already enrolled.")

    def test_register_to_course_course_not_exist(self):
        """Verify that registering to a non-existent course returns an error."""
        user = self._complete_user_registration("noexist@bgu.ac.il", "Pass1!", "Missing", "Course")
        course_id = "123.1.1010"  # This course was never opened

        response = self.negev.registerToCourse(course_id, user.user_id)

        self.assertIn("not exist", response,
                      "Expected error message when registering to a non-existent course.")

    def test_remove_student_from_course_success(self):
        """Verify that a student can be removed from a course successfully."""
        creator = self._complete_user_registration("creator@bgu.ac.il", "Pass1!", "Creator", "User")
        student = self._complete_user_registration("student@bgu.ac.il", "Pass1!", "Student", "User")
        course_id = "321.1.1010"
        self._open_course(creator, course_id, "מבוא למדעי המחשב")
        response = self.negev.registerToCourse(course_id, student.user_id)
        self.assertEqual(response, "UserData successfully registered to the course.")
        course_ids = self._extract_course_ids(
            student.get_courses() if hasattr(student, "get_courses") else student.courses)
        self.assertIn(course_id, course_ids)
        remove_response = self.negev.removeStudentFromCourse(course_id, student.user_id)
        self.assertEqual(remove_response, "UserData successfully removed from the course.")
        updated_student = self.negev._user_facade.getUser_by_email(student.email)
        updated_courses = self._extract_course_ids(
            updated_student.get_courses() if hasattr(updated_student, "get_courses") else updated_student.courses)
        self.assertNotIn(course_id, updated_courses)

    def test_remove_course_error_user_not_found(self):
        """Verify that removing a non-existent user from a course returns an error."""
        course_id = "202.1.1010"
        invalid_user_id = "non_existent_user_id"
        response = self.negev.removeStudentFromCourse(course_id, invalid_user_id)
        self.assertIn("Error", response,
                      "Expected error when attempting to remove a non-existent user from a course.")

    def test_get_user_courses(self):
        """Verify get_user_courses returns all courses the user is registered to."""
        user = self._complete_user_registration("coursesuser@post.bgu.ac.il", "Pass1!", "Course", "Tester")
        course_id1 = "555.1.1010"
        course_id2 = "666.1.1010"
        self._open_course(user, course_id1, "מבוא למדעי המחשב")
        self._open_course(user, course_id2, "מבוא לכלכלה")
        courses_dto = self.negev.get_user_courses(user.user_id)
        course_ids = self._extract_course_ids(courses_dto)
        self.assertIn(course_id1, course_ids)
        self.assertIn(course_id2, course_ids)

    def test_is_user_manager_true(self):
        """Verify a user who opened a course is marked as its manager."""
        user = self._complete_user_registration("manager@post.bgu.ac.il", "Pass1!", "Manager", "User")
        course_id = "444.1.1010"
        self._open_course(user, course_id, "מבני נתונים")
        is_manager = self.negev.courseFacade.is_course_manager(course_id, user.user_id)
        self.assertTrue(is_manager)

    def test_is_user_manager_false(self):
        """Verify a user who did not open a course is not its manager."""
        creator = self._complete_user_registration("creator@post.bgu.ac.il", "Pass1!", "Creator", "User")
        student = self._complete_user_registration("student@post.bgu.ac.il", "Pass1!", "Student", "User")
        course_id = "333.1.1010"
        self._open_course(creator, course_id, "מבני נתונים")
        is_manager = self.negev.courseFacade.is_course_manager(course_id, student.user_id)
        self.assertFalse(is_manager)

    def test_get_course_topics_success(self):
        """Verify that get_course_topics returns non-empty topics for an opened course."""
        user = self._complete_user_registration("topics@bgu.ac.il", "Pass1!", "Topic", "Tester")
        course_id = "888.1.1010"
        self._open_course(user, course_id, "מבוא למתודולוגיה")
        topics = self.negev.get_course_topics(course_id)
        self.assertTrue(isinstance(topics, (list, set)), "Expected course topics to be a list or set.")
        topics_list = list(topics) if isinstance(topics, set) else topics
        self.assertGreater(len(topics_list), 0, "The course topics list should not be empty.")

    def test_get_course_topics_course_not_found(self):
        """Verify that get_course_topics returns None when course does not exist."""
        fake_course_id = "000.0.0000"
        topics = self.negev.get_course_topics(fake_course_id)
        self.assertIsNone(topics, "Expected None when course does not exist.")

    def test_update_course_topics_success(self):
        """Verify successful update of course topics."""
        user = self._complete_user_registration("success@bgu.ac.il", "Pass1!", "Topic", "User")
        course_id = "101.1.1010"
        self._open_course(user, course_id, "מערכות הפעלה")

        response = self.negev.update_course_topics(course_id, added_topics=["תהליכים"], removed_topics=[])
        parsed = json.loads(response)
        self.assertEqual(parsed["status"], "success")
        self.assertIn("עודכנו בהצלחה", parsed["message"])

    def test_update_course_topics_success(self):
        """Verify successful update of course topics."""
        user = self._complete_user_registration("success@bgu.ac.il", "Pass1!", "Topic", "User")
        course_id = "101.1.1010"
        self._open_course(user, course_id, "מערכות הפעלה")

        response = self.negev.update_course_topics(course_id, added_topics=["תהליכים"], removed_topics=[])
        parsed = json.loads(response)
        self.assertEqual(parsed["status"], "success")
        self.assertIn("עודכנו בהצלחה", parsed["message"])

    def test_update_course_topics_topic_already_exists(self):
        """Verify error when trying to add a topic that already exists."""
        user = self._complete_user_registration("exists@bgu.ac.il", "Pass1!", "Topic", "Exists")
        course_id = "101.1.2020"
        self._open_course(user, course_id, "חישוביות")

        self.negev.update_course_topics(course_id, added_topics=["אוטומטים"], removed_topics=[])

        response = self.negev.update_course_topics(course_id, added_topics=["אוטומטים"], removed_topics=[])
        parsed = json.loads(response)
        self.assertEqual(parsed["status"], "error")
        self.assertIn("כבר קיים", parsed["message"])

    def test_update_course_topics_topic_not_exist_for_removal(self):
        """Verify error when trying to remove a topic that doesn't exist."""
        user = self._complete_user_registration("notexist@bgu.ac.il", "Pass1!", "Topic", "Remove")
        course_id = "101.1.3030"
        self._open_course(user, course_id, "יסודות ההנדסה")

        response = self.negev.update_course_topics(course_id, added_topics=[], removed_topics=["לא_קיים"])
        parsed = json.loads(response)
        self.assertEqual(parsed["status"], "error")
        self.assertIn("כבר לא קיים", parsed["message"])

    @patch('Backend.BusinessLayer.Analyzer.AnalyzerFacade.AnalyzerFacade.perform_information_retrival_question_pdf')
    @patch('Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf')
    def test_update_course_topics_removal_blocked_due_to_question(self, mock_process_pdf, mock_retrival):
        """Verify error when trying to remove a topic that is still in use by a question."""
        user = self._complete_user_registration("removalock@bgu.ac.il", "Pass1!", "Topic", "Lock")
        course_id = "888.3.8888"
        self._open_course(user, course_id, "מבוא לאבטחת מידע")
        self.negev._course_facade.add_course_topics(course_id, ["הצפנה"])

        self.negev.add_question(
            course_id=course_id,
            year=2023,
            semester="אביב",
            moed="א",
            question_number=1,
            is_american=True,
            question_topics=["הצפנה"],
            question_file=self._mock_pdf_file(),
            answer_file=None
        )

        response = self.negev.update_course_topics(course_id, [], ["הצפנה"])
        parsed = json.loads(response)
        self.assertEqual(parsed["status"], "error")
        self.assertIn("משוייך לשאלה", parsed["message"])

    def test_get_all_courses(self):
        """Verify that get_all_courses returns all courses present in the system."""
        user = self._complete_user_registration("allcourses@bgu.ac.il", "Pass1!", "Course", "Tester")
        course_id1 = "101.1.1010"
        course_id2 = "102.1.1010"
        self._open_course(user, course_id1, "מבוא למדעי המחשב")
        self._open_course(user, course_id2, "מבוא לכלכלה")
        all_courses = self.negev.get_all_courses()
        self.assertIsInstance(all_courses, list)
        course_ids = self._extract_course_ids(all_courses)
        self.assertIn(course_id1, course_ids)
        self.assertIn(course_id2, course_ids)

    def test_get_all_courses_does_not_include_unknown_course(self):
        """Verify that get_all_courses does not include courses that were not created."""
        user = self._complete_user_registration("failcourse@bgu.ac.il", "Pass1!", "No", "Course")
        course_id = "777.7.7777"  # לא נפתח בפועל

        # לא פותחים שום קורס
        all_courses = self.negev.get_all_courses()
        course_ids = self._extract_course_ids(all_courses)

        self.assertNotIn(course_id, course_ids, "Course that was not opened should not appear.")

    def test_get_course(self):
        """Verify that get_course returns the correct course DTO for a given course ID."""
        user = self._complete_user_registration("getcourse@bgu.ac.il", "Pass1!", "Get", "Course")
        course_id = "321.2.1010"
        self._open_course(user, course_id, "מבוא לאלגוריתמים")
        course = self.negev.get_course(course_id)
        self.assertIsNotNone(course, "Expected course DTO but got None.")
        if hasattr(course, "get_course_id"):
            retrieved_id = course.get_course_id()
        elif hasattr(course, "course_id"):
            retrieved_id = course.course_id
        elif hasattr(course, "to_dict"):
            retrieved_id = course.to_dict().get("course_id")
        elif isinstance(course, dict):
            retrieved_id = course.get("course_id")
        else:
            self.fail(f"Unknown course DTO format: {type(course)}")

        self.assertEqual(retrieved_id, course_id, "Returned course ID does not match requested ID.")

    def test_get_course_not_found(self):
        """Verify that get_course raises CourseIsNotExist when the course does not exist."""
        fake_course_id = "365.9.9999"
        with self.assertRaises(CourseIsNotExist):
            self.negev.get_course(fake_course_id)

    def test_get_courses_by_name(self):
        """Verify that get_courses_by_name returns courses matching a given substring."""
        user = self._complete_user_registration("coursebyname@post.bgu.ac.il", "Pass1!", "קורס", "לפישם")
        course_id1 = "333.2.1010"
        course_id2 = "102.2.1010"
        self._open_course(user, course_id1, "מבוא למדעי המחשב")
        self._open_course(user, course_id2, "מדעי המחשב מתקדם")
        courses = self.negev.get_courses_by_name("מדעי המחשב")
        course_ids = self._extract_course_ids(courses)
        self.assertIn(course_id1, course_ids)
        self.assertIn(course_id2, course_ids)

    def test_get_courses_by_name_no_match(self):
        """Verify that get_courses_by_name returns an empty list when no courses match the given name."""
        user = self._complete_user_registration("nomatch@post.bgu.ac.il", "Pass1!", "לא", "מותאם")
        course_id = "404.4.4040"
        self._open_course(user, course_id, "תורת הקומפילציה")

        results = self.negev.get_courses_by_name("היסטוריה של יוון")
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 0, "Expected no matching courses to be returned.")

    def test_is_course_exists(self):
        """Verify that isCourseExists returns correct boolean for existing and non-existing courses."""
        user = self._complete_user_registration("exists@bgu.ac.il", "Pass1!", "Course", "Exists")
        course_id = "101.3.1010"
        self._open_course(user, course_id, "מבוא לפרויקטים")
        self.assertTrue(self.negev.isCourseExists(course_id), "Expected course to exist but it does not.")
        self.assertFalse(self.negev.isCourseExists("565.9.9999"), "Expected non-existing course to return False.")

    @patch('Backend.BusinessLayer.Notifications.LateNotifications.socketio.emit')
    def test_remove_course_manager_success(self, mock_emit):
        # רישום שני משתמשים
        user1 = self._complete_user_registration("nominator@bgu.ac.il", "Pass1!", "מציע", "מנהל")
        user2 = self._complete_user_registration("target@bgu.ac.il", "Pass1!", "מנהל", "להסרה")
        course_id = "123.4.5678"
        self._open_course(user1, course_id, "קורס טסט")

        # שליחת בקשת מינוי למנהל קורס
        appoint_response = self.negev.appoint_course_manager(user2.email, user1.user_id, course_id)
        appoint_data = json.loads(appoint_response)
        self.assertEqual(appoint_data["status"], "success", f"Appoint failed: {appoint_data}")

        # שליפת ההתראה שנשלחה למועמד
        notifications = self.negev.get_unapproved_notification_list(user2.user_id)
        notif_data = json.loads(notifications)
        notif_id = notif_data["notifications"][0]["notification_id"]

        # אישור המינוי
        approve_response = self.negev.approve_course_manager_appoint(notif_id, user2.user_id)
        approve_data = json.loads(approve_response)
        self.assertEqual(approve_data["status"], "success", f"Approval failed: {approve_data}")

        # הסרה של המנהל החדש
        response = self.negev.remove_course_manager(user2.email, user1.user_id, course_id)
        data = json.loads(response)

        self.assertEqual(data["status"], "success")
        self.assertIn("removal request", data["message"])

    def test_remove_course_manager_invalid_email(self):
        user1 = self._complete_user_registration("nominator2@bgu.ac.il", "Pass1!", "בודק", "אימייל")
        response = self.negev.remove_course_manager("invalid_email@", user1.user_id, "999.9.9999")
        data = json.loads(response)
        self.assertEqual(data["status"], "error")
        self.assertIn("אימייל חוקי", data["message"])

    def test_remove_course_manager_user_not_found(self):
        user1 = self._complete_user_registration("nominator3@bgu.ac.il", "Pass1!", "בודק", "חיפוש")
        response = self.negev.remove_course_manager("ghost@bgu.ac.il", user1.user_id, "999.9.9999")
        data = json.loads(response)
        self.assertEqual(data["status"], "error")
        self.assertIn("לא קיים במערכת", data["message"])

    def test_remove_course_manager_not_a_manager(self):
        user1 = self._complete_user_registration("nominator4@bgu.ac.il", "Pass1!", "בודק", "הסרה")
        user2 = self._complete_user_registration("regular@bgu.ac.il", "Pass1!", "סתם", "משתמש")
        course_id = "444.4.4444"
        self._open_course(user1, course_id, "קורס לבדיקה")

        response = self.negev.remove_course_manager(user2.email, user1.user_id, course_id)
        data = json.loads(response)
        self.assertEqual(data["status"], "error")
        self.assertIn("אינו מנהל קורס", data["message"])

    def test_remove_only_course_manager(self):
        user1 = self._complete_user_registration("lonely@bgu.ac.il", "Pass1!", "בודד", "מנהל")
        course_id = "555.5.5555"
        self._open_course(user1, course_id, "קורס עם מנהל אחד בלבד")

        response = self.negev.remove_course_manager(user1.email, user1.user_id, course_id)
        data = json.loads(response)
        self.assertEqual(data["status"], "error")
        self.assertIn("מנהל הקורס היחיד", data["message"])


if __name__ == '__main__':
    unittest.main()
