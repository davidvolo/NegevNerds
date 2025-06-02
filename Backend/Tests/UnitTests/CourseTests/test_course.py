import unittest
from unittest.mock import patch, MagicMock
from Backend.BusinessLayer.Course.enums import Semester, Moed
from Backend.BusinessLayer.Util.Exceptions import (
    ExamIsNotExist,
    ExamAlreadyExists,
    TopicAlreadyExist,
    TopicNotFound,
    UserAlreadyRegisterToCourse,
    UserIsNotRegisterToCourse
)
from Backend.BusinessLayer.Course.Course import Course
from Backend.DataLayer.UserData.UserRepository import UserRepository
from Backend.DataLayer.CourseData.CourseRepository import CourseRepository
from Backend.DataLayer.ReactionData.ReactionRepository import ReactionRepository
from Backend.DataLayer.SystemManagers.SystemManagersRepository import SystemManagersRepository
from Backend.DataLayer.Noitifications.NotificationRepository import NotificationRepository
from Backend.DataLayer.NotificationsSetting.NotificationsSettingRepository import NotificationsSettingRepository




class TestCourse(unittest.TestCase):
    def setUp(self):
        self.course_id = "course1"
        self.name = "Test Course"
        # In __init__, course_topics is set to the provided value (or a set if None)
        # For testing add/remove topic we will override with a list.
        self.course_topics = {"topic1", "topic2"}
        self.course = Course(course_id=self.course_id, name=self.name, course_topics=self.course_topics)

    @patch("Backend.DataLayer.CourseData.CourseRepository.CourseRepository.add_course")
    def test_create(self, mock_add_course):
        topics = {"topic1", "topic2"}
        course = Course.create(course_id="course2", name="New Course", course_topics=topics)
        mock_add_course.assert_called_once_with(course)
        self.assertEqual(course.course_id, "course2")
        self.assertEqual(course.name, "New Course")

    def test_get_id(self):
        self.assertEqual(self.course.get_id(), self.course_id)

    @patch("Backend.DataLayer.ExamData.ExamRepository.ExamRepository.get_all_exams_by_year_and_course")
    def test_get_exams_by_year(self, mock_get_exams_by_year):
        dummy_exams = [MagicMock(), MagicMock()]
        mock_get_exams_by_year.return_value = dummy_exams
        exams = self.course.get_exams_by_year(2025)
        mock_get_exams_by_year.assert_called_once_with(year=2025, course_id=self.course_id)
        self.assertEqual(exams, dummy_exams)

    def test_get_name(self):
        self.assertEqual(self.course.get_name(), self.name)

    def test_get_topics(self):
        topics = self.course.get_topics()
        self.assertEqual(topics, self.course_topics)

    @patch("Backend.DataLayer.ExamData.ExamRepository.ExamRepository.get_exam_by_course")
    def test_get_all_exams(self, mock_get_exam_by_course):
        dummy_exams = [MagicMock(), MagicMock()]
        mock_get_exam_by_course.return_value = dummy_exams
        exams = self.course.get_all_exams()
        mock_get_exam_by_course.assert_called_once_with(course_id=self.course_id)
        self.assertEqual(exams, dummy_exams)

    @patch.object(Course, "get_all_exams")
    def test_get_questions_by_specific_no_year(self, mock_get_all_exams):
        # When year is None, get_questions_by_specific calls each exam's method.
        dummy_exam = MagicMock()
        dummy_exam.get_questions_by_specific.return_value = ["q_dto"]
        mock_get_all_exams.return_value = [dummy_exam]
        result = self.course.get_questions_by_specific(question_number=1)
        dummy_exam.get_questions_by_specific.assert_called_with(1)
        self.assertEqual(result, ["q_dto"])

    @patch.object(Course, "get_all_exams")
    def test_get_questions_by_keywords(self, mock_get_all_exams):
        dummy_exam1 = MagicMock()
        dummy_exam1.get_questions_by_keywords.return_value = ["q1"]
        dummy_exam2 = MagicMock()
        dummy_exam2.get_questions_by_keywords.return_value = ["q2"]
        mock_get_all_exams.return_value = [dummy_exam1, dummy_exam2]
        result = self.course.get_questions_by_keywords(["keyword"])
        dummy_exam1.get_questions_by_keywords.assert_called_with(["keyword"])
        dummy_exam2.get_questions_by_keywords.assert_called_with(["keyword"])
        self.assertEqual(result, ["q1", "q2"])

    @patch("Backend.DataLayer.ExamData.ExamRepository.ExamRepository.get_allExams_Link_and_name")
    def test_get_allExams_Link_and_name(self, mock_get_allExams_Link_and_name):
        dummy = {"exam_id": "e1", "link": "link.pdf", "name": "Exam 1"}
        mock_get_allExams_Link_and_name.return_value = dummy
        result = self.course.get_allExams_Link_and_name()
        mock_get_allExams_Link_and_name.assert_called_once_with(self.course_id)
        self.assertEqual(result, dummy)

    @patch("Backend.DataLayer.ExamData.ExamRepository.ExamRepository.get_exam_by_date")
    def test_get_exam_found_in_repo(self, mock_get_exam_by_date):
        dummy_exam = MagicMock()
        dummy_exam.semester = Semester.SPRING
        dummy_exam.moed = Moed.A
        mock_get_exam_by_date.return_value = dummy_exam
        self.course.exams = {}
        exam = self.course.get_exam(2025, "אביב", "א")
        # The get_exam call converts the strings to Enums in the repository call.
        mock_get_exam_by_date.assert_called_once_with(year=2025, semester=Semester("אביב"), moed=Moed("א"),
                                                      course_id=self.course_id)
        self.assertEqual(exam, dummy_exam)
        self.assertIn(2025, self.course.exams)
        self.assertIn(dummy_exam, self.course.exams[2025])

    def test_get_exams_success(self):
        dummy_exam = MagicMock()
        dummy_exam.semester = Semester.SPRING
        dummy_exam.moed = Moed.A
        self.course.exams = {2025: [dummy_exam]}
        exams = self.course.get_exams(2025, semester=Semester.SPRING, moed=Moed.A)
        self.assertEqual(exams, [dummy_exam])

    def test_get_exams_not_found(self):
        self.course.exams = {}
        with self.assertRaises(ExamIsNotExist):
            self.course.get_exams(2025, semester=Semester.SPRING, moed=Moed.A)

    def test_get_managers(self):
        self.course.managers = {"manager1", "manager2"}
        self.assertEqual(self.course.get_managers(), {"manager1", "manager2"})

    def test_get_users(self):
        self.course.users = ["user1", "user2"]
        self.assertEqual(self.course.get_users(), ["user1", "user2"])

    def test_set_syllabus(self):
        self.course.set_syllabus("Syllabus Content")
        self.assertEqual(self.course.syllabus, "Syllabus Content")

    @patch("Backend.DataLayer.CourseTopics.CourseTopicsRepository.CourseTopicsRepository.add_Topic_to_course")
    def test_add_course_topic_success(self, mock_add_topic):
        # For add_course_topic, override course_topics with a list
        self.course.course_topics = set()
        self.course.add_course_topic("new_topic")
        self.assertIn("new_topic", self.course.course_topics)
        mock_add_topic.assert_called_once_with(course_id=self.course_id, topic="new_topic")

    @patch("Backend.DataLayer.CourseTopics.CourseTopicsRepository.CourseTopicsRepository.add_Topic_to_course")
    def test_add_course_topic_already_exists(self, mock_add_topic):
        # When topic already exists, exception is raised.
        self.course.course_topics = ["topic1"]
        with self.assertRaises(TopicAlreadyExist):
            self.course.add_course_topic("topic1")

    @patch("Backend.DataLayer.CourseTopics.CourseTopicsRepository.CourseTopicsRepository.remove_topic_from_course")
    def test_remove_course_topic_success(self, mock_remove_topic):
        self.course.course_topics = ["topic1", "topic2"]
        self.course.remove_course_topic("topic1")
        self.assertNotIn("topic1", self.course.course_topics)
        mock_remove_topic.assert_called_once_with(course_id=self.course_id, topic="topic1")

    @patch("Backend.DataLayer.CourseTopics.CourseTopicsRepository.CourseTopicsRepository.remove_topic_from_course")
    def test_remove_course_topic_not_found(self, mock_remove_topic):
        self.course.course_topics = ["topic1"]
        with self.assertRaises(TopicNotFound):
            self.course.remove_course_topic("topic2")

    def test_add_student_success(self):
        self.course.users = []
        self.course.add_student("user1")
        self.assertIn("user1", self.course.users)

    @patch("Backend.DataLayer.CourseData.CourseRepository.CourseRepository.update_course")
    def test_remove_student_success(self, mock_update_course):
        self.course.users = ["user1", "user2"]
        self.course.remove_student("user1")
        self.assertNotIn("user1", self.course.users)
        mock_update_course.assert_called_once_with(self.course)

    def test_remove_student_not_registered(self):
        self.course.users = ["user2"]
        with self.assertRaises(UserIsNotRegisterToCourse):
            self.course.remove_student("user1")

    def test_generate_exam_id(self):
        exam_id = self.course.generate_exam_id(2025, "SPRING", "A")
        expected = f"EXAM-{self.course_id}-2025-SPRING-A"
        self.assertEqual(exam_id, expected)

    @patch("Backend.BusinessLayer.Course.Exam.Exam.create")
    def test_add_exam_success(self, mock_exam_create):
        self.course.exams = {}
        dummy_exam = MagicMock()
        mock_exam_create.return_value = dummy_exam
        self.course.add_exam(2025, "אביב", "א", link="exam_link")
        mock_exam_create.assert_called_once()
        self.assertIn(2025, self.course.exams)
        self.assertIn(dummy_exam, self.course.exams[2025])

    def test_add_exam_already_exists(self):
        dummy_exam = MagicMock()
        dummy_exam.semester = Semester.SPRING
        dummy_exam.moed = Moed.A
        self.course.exams = {2025: [dummy_exam]}
        with self.assertRaises(ExamAlreadyExists):
            self.course.add_exam(2025, Semester.SPRING, Moed.A, link="exam_link")

    @patch("Backend.DataLayer.ExamData.ExamRepository.ExamRepository.delete_exam", return_value=None)
    def test_remove_exam_success(self, mock_delete_exam):
        dummy_exam = MagicMock()
        # נניח שהקורס שלנו כבר כולל מזהה קורס תקין, למשל "course1"
        self.course.course_id = "course1"
        self.course.exams = {2025: [dummy_exam]}
        # Patch get_exam to return the dummy exam
        self.course.get_exam = MagicMock(return_value=dummy_exam)

        # קריאה למחיקת המבחן. המתודה delete_exam הפטושה לא תגרום ל־ValueError.
        self.course.remove_exam(2025, "אביב", "א")

        # נוודא ש־delete_exam נקראה עם הפרמטרים הנכונים.
        mock_delete_exam.assert_called_once_with("course1", 2025, "אביב", "א")
        # נוודא שהמבחן הוסר מהמפה של exams
        self.assertNotIn(dummy_exam, self.course.exams[2025])

    def test_remove_exam_not_found(self):
        self.course.exams = {}
        with self.assertRaises(ExamIsNotExist):
            self.course.remove_exam(2025, "אביב", "א")

    def test_get_exam_full_pdf_success(self):
        dummy_exam = MagicMock()
        dummy_exam.link = "full_exam.pdf"
        self.course.get_exam = MagicMock(return_value=dummy_exam)
        link = self.course.get_exam_full_pdf(2025, "אביב", "א")
        self.assertEqual(link, "full_exam.pdf")

    def test_get_exam_full_pdf_not_found(self):
        self.course.get_exam = MagicMock(return_value=None)
        with self.assertRaises(ExamIsNotExist):
            self.course.get_exam_full_pdf(2025, "אביב", "א")

    def test_check_exam_full_pdf_true(self):
        dummy_exam = MagicMock()
        dummy_exam.link = "full_exam.pdf"
        self.course.get_exam = MagicMock(return_value=dummy_exam)
        result = self.course.check_exam_full_pdf(2025, "אביב", "א")
        self.assertTrue(result)

    def test_check_exam_full_pdf_false(self):
        dummy_exam = MagicMock()
        dummy_exam.link = ""
        self.course.get_exam = MagicMock(return_value=dummy_exam)
        result = self.course.check_exam_full_pdf(2025, "SPRING", "A")
        self.assertFalse(result)

    def test_checkExistSolution(self):
        dummy_exam = MagicMock()
        dummy_question = MagicMock()
        dummy_question.link_to_answer = "answer.pdf"
        dummy_exam.get_question.return_value = dummy_question
        self.course.get_exam = MagicMock(return_value=dummy_exam)
        result = self.course.checkExistSolution(2025, "SPRING", "A", 1)
        self.assertTrue(result)

    def test_checkExistQuestion(self):
        dummy_exam = MagicMock()
        dummy_question = MagicMock()
        dummy_question.generate_question_details_name.return_value = "detail_name"
        dummy_question.id = "q1"
        dummy_question.link_to_question = "q.pdf"
        dummy_question.link_to_answer = "a.pdf"
        dummy_exam.get_question.return_value = dummy_question
        self.course.get_exam = MagicMock(return_value=dummy_exam)
        result = self.course.checkExistQuestion(2025, "SPRING", "A", 1)
        self.assertEqual(result, ("q1", "detail_name", "q.pdf", "a.pdf"))

    @patch("Backend.DataLayer.ExamData.ExamRepository.ExamRepository.update_exam_link")
    def test_upload_full_exam_pdf_success(self, mock_update_exam_link):
        dummy_exam = MagicMock()
        self.course.get_exam = MagicMock(return_value=dummy_exam)
        dummy_exam.upload_full_exam_pdf.return_value = {"status": "success", "link": "new_exam.pdf"}
        result = self.course.upload_full_exam_pdf(2025, "SPRING", "A", "new_exam.pdf")
        dummy_exam.upload_full_exam_pdf.assert_called_once_with("new_exam.pdf")
        self.assertEqual(result["status"], "success")

    def test_uploadSolution(self):
        dummy_exam = MagicMock()
        dummy_question = MagicMock()
        dummy_question.uploadSolution.return_value = {"status": "success", "link": "new_answer.pdf"}
        dummy_exam.get_question.return_value = dummy_question
        self.course.get_exam = MagicMock(return_value=dummy_exam)
        result = self.course.uploadSolution(2025, "SPRING", "A", 1, "new_answer.pdf")
        dummy_question.uploadSolution.assert_called_once_with("new_answer.pdf")
        self.assertEqual(result["status"], "success")

    @patch("Backend.DataLayer.CourseManagers.CourseManagersRepository.CourseManagersRepository.is_exist")
    def test_exist_manager_true(self, mock_is_exist):
        mock_is_exist.return_value = True
        self.course.managers = {"manager1"}
        result = self.course.exist_manager("manager1")
        self.assertTrue(result)

    @patch("Backend.DataLayer.CourseManagers.CourseManagersRepository.CourseManagersRepository.is_exist")
    def test_exist_manager_false(self, mock_is_exist):
        mock_is_exist.return_value = False
        self.course.managers = set()
        result = self.course.exist_manager("manager1")
        self.assertFalse(result)

    @patch("Backend.DataLayer.CourseManagers.CourseManagersRepository.CourseManagersRepository.add_manager_to_course")
    def test_add_manager_success(self, mock_add_manager):
        self.course.managers = set()
        self.course.exist_manager = MagicMock(return_value=False)
        self.course.add_manager("manager1")
        self.assertIn("manager1", self.course.managers)
        mock_add_manager.assert_called_once_with(user_id="manager1", course_id=self.course_id)

    @patch(
        "Backend.DataLayer.CourseManagers.CourseManagersRepository.CourseManagersRepository.remove_manager_from_course")
    def test_remove_manager_success(self, mock_remove_manager):
        self.course.managers = {"manager1"}
        self.course.exist_manager = MagicMock(return_value=True)
        self.course.remove_manager("manager1")
        self.assertNotIn("manager1", self.course.managers)
        mock_remove_manager.assert_called_once_with(user_id="manager1", course_id=self.course_id)

    @patch("Backend.DataLayer.ExamData.ExamRepository.ExamRepository.update_exam", return_value=None)
    @patch("Backend.DataLayer.UserData.UserModel.UserModel")
    def test_edit_exam_year(self, MockUserModel, mock_update_exam):
        dummy_exam = MagicMock()
        dummy_exam.id = 1  # הגדרת מזהה תקין
        dummy_exam.edit_year = MagicMock()
        self.course.exams = {2025: [dummy_exam]}
        self.course.get_exam = MagicMock(return_value=dummy_exam)

        # כעת, כשהמתודה update_exam פטשה ומחזירה None, לא תתרחש השאילתה למסד נתונים.
        self.course.edit_exam_year(2025, "אביב", "א", 2030)

        dummy_exam.edit_year.assert_called_once_with(2030)
        self.assertNotIn(dummy_exam, self.course.exams.get(2025, []))
        self.assertIn(dummy_exam, self.course.exams.get(2030, []))

    @patch("Backend.BusinessLayer.Course.Exam.Exam.create")
    def test_check_valid_question_exam_none(self, mock_exam_create):
        self.course.exams = {}
        dummy_exam = MagicMock()
        dummy_exam.id = "exam_created"
        mock_exam_create.return_value = dummy_exam
        result, exam_id = self.course.checkQuestionAvailability(2025, "אביב", "א", 1)
        mock_exam_create.assert_called_once()
        self.assertTrue(result)
        self.assertEqual(exam_id, "exam_created")

    def test_check_valid_question_exam_exists(self):
        dummy_exam = MagicMock()
        dummy_exam.checkQuestionAvailability.return_value = True
        dummy_exam.id = "exam_existing"
        self.course.get_exam = MagicMock(return_value=dummy_exam)
        result, exam_id = self.course.checkQuestionAvailability(2025, "אביב", "א", 1)
        # Expect a positional argument instead of keyword arguments:
        dummy_exam.checkQuestionAvailability.assert_called_once_with(1)
        self.assertTrue(result)
        self.assertEqual(exam_id, "exam_existing")

    def test_add_comment(self):
        dummy_exam = MagicMock()
        dummy_question = MagicMock()
        dummy_question.add_comment.return_value = {"writer1"}
        dummy_exam.get_question.return_value = dummy_question
        self.course.get_exam = MagicMock(return_value=dummy_exam)
        result = self.course.add_comment(2025, "SPRING", "A", 1, "comment_id", "John Doe" , "writer1", "0"
                                         ,"Nice question", "")
        dummy_question.add_comment.assert_called_once_with("comment_id", "John Doe", "writer1", "0", "Nice question", False, False, '')
        self.assertEqual(result, {"writer1"})

    def test_get_question_path(self):
        dummy_exam = MagicMock()
        dummy_exam.get_question_path.return_value = "q_path.pdf"
        self.course.get_exam = MagicMock(return_value=dummy_exam)
        result = self.course.get_question_path(2025, "SPRING", "A", 1)
        dummy_exam.get_question_path.assert_called_once_with(1)
        self.assertEqual(result, "q_path.pdf")

    def test_get_answer_path(self):
        dummy_exam = MagicMock()
        dummy_exam.get_answer_path.return_value = "a_path.pdf"
        self.course.get_exam = MagicMock(return_value=dummy_exam)
        result = self.course.get_answer_path(2025, "SPRING", "A", 1)
        dummy_exam.get_answer_path.assert_called_once_with(1)
        self.assertEqual(result, "a_path.pdf")

    def test_get_question_id(self):
        dummy_exam = MagicMock()
        dummy_exam.get_question_id.return_value = "q_id"
        self.course.get_exam = MagicMock(return_value=dummy_exam)
        result = self.course.get_question_id(2025, "SPRING", "A", 1)
        dummy_exam.get_question_id.assert_called_once_with(1)
        self.assertEqual(result, "q_id")

    def test_get_question_id_and_path(self):
        dummy_exam = MagicMock()
        dummy_exam.get_question_id_and_path.return_value = ("a_path", "q_id")
        self.course.get_exam = MagicMock(return_value=dummy_exam)
        result = self.course.get_question_id_and_path(2025, "SPRING", "A", 1)
        dummy_exam.get_question_id_and_path.assert_called_once_with(1)
        self.assertEqual(result, ("a_path", "q_id"))

    def test_add_reaction(self):
        dummy_exam = MagicMock()
        dummy_question = MagicMock()
        dummy_question.add_reaction.return_value = "reaction_result"
        dummy_exam.get_question.return_value = dummy_question
        self.course.get_exam = MagicMock(return_value=dummy_exam)
        result = self.course.add_reaction(2025, "SPRING", "A", 1, "comm1", "user1", "👍")
        dummy_question.add_reaction.assert_called_once_with("comm1", "user1", "👍")
        self.assertEqual(result, "reaction_result")

    def test_delete_comment(self):
        dummy_exam = MagicMock()
        dummy_question = MagicMock()
        dummy_exam.get_question.return_value = dummy_question
        self.course.get_exam = MagicMock(return_value=dummy_exam)
        self.course.delete_comment(2025, "SPRING", "A", 1, "comm_del")
        dummy_question.delete_comment.assert_called_once_with("comm_del")

    def test_edit_comment_text(self):
        dummy_exam = MagicMock()
        dummy_question = MagicMock()
        self.course.get_exam = MagicMock(return_value=dummy_exam)
        dummy_exam.get_question.return_value = dummy_question
        self.course.edit_comment_text(2025, "SPRING", "A", 1, "comm_edit", "Updated text")
        dummy_question.edit_comment_text.assert_called_once_with("comm_edit", "Updated text")

    def test_remove_reaction(self):
        dummy_exam = MagicMock()
        dummy_question = MagicMock()
        self.course.get_exam = MagicMock(return_value=dummy_exam)
        dummy_exam.get_question.return_value = dummy_question
        self.course.remove_reaction(2025, "SPRING", "A", 1, "comm1", "reaction1")
        dummy_question.remove_reaction.assert_called_once_with("comm1", "reaction1")

    @patch("Backend.DataLayer.ExamData.ExamRepository.ExamRepository.get_allExams_Link_and_name")
    def test_handleDownloadAllExamsZip(self, mock_get_allExams_Link_and_name):
        dummy_exams = {"exam1": "link1", "exam2": "link2"}
        mock_get_allExams_Link_and_name.return_value = dummy_exams
        folder_name, exams = self.course.handleDownloadAllExamsZip()
        expected_folder = f"{self.course_id}_{self.name}_NegevNerds_מבחנים"
        self.assertEqual(folder_name, expected_folder)
        self.assertEqual(exams, dummy_exams)

    def test_add_question(self):
        dummy_exam = MagicMock()
        dummy_exam.add_question.return_value = "q_id_new"
        self.course.get_exam = MagicMock(return_value=dummy_exam)
        result = self.course.add_question(2025, "SPRING", "A", 1, True, ["topic1"], "q.pdf", "a.pdf", "question text")
        dummy_exam.add_question.assert_called_once_with(1, True, ["topic1"], "q.pdf", "a.pdf", "question text")
        self.assertEqual(result, "q_id_new")

    @patch("Backend.DataLayer.CourseTopics.CourseTopicsRepository.CourseTopicsRepository")
    def test_edit_question_topic(self, mock_repo_cls):
        mock_repo = MagicMock()
        mock_repo.is_exist.return_value = True
        mock_repo_cls.return_value = mock_repo

        dummy_exam = MagicMock()
        dummy_exam.edit_question_topic.return_value = "edited_topic"

        self.course.get_exam = MagicMock(return_value=dummy_exam)
        self.course.course_topics_repository = mock_repo  # <<< הזרקה מפורשת

        result = self.course.edit_question_topic(2025, "SPRING", "A", 1, ["new_topic"])

        dummy_exam.edit_question_topic.assert_called_once_with(1, ["new_topic"])
        self.assertEqual(result, "edited_topic")

    def test_checkQuestionAvailability_exam_none(self):
        self.course.exams = {}
        with patch("Backend.BusinessLayer.Course.Exam.Exam.create") as mock_exam_create:
            dummy_exam = MagicMock()
            dummy_exam.id = "exam_created"
            mock_exam_create.return_value = dummy_exam
            result, exam_id = self.course.checkQuestionAvailability(2025, "אביב", "א", 1)
            mock_exam_create.assert_called_once()
            self.assertTrue(result)
            self.assertEqual(exam_id, "exam_created")

    def test_checkQuestionAvailability_exam_exists(self):
        dummy_exam = MagicMock()
        dummy_exam.checkQuestionAvailability.return_value = False
        dummy_exam.id = "exam_existing"
        self.course.get_exam = MagicMock(return_value=dummy_exam)
        result, exam_id = self.course.checkQuestionAvailability(2025, "אביב", "א", 1)
        dummy_exam.checkQuestionAvailability.assert_called_once_with(1)
        self.assertFalse(result)
        self.assertEqual(exam_id, "exam_existing")

    def test_edit_question_details(self):
        dummy_exam = MagicMock()
        dummy_exam.edit_question_details.return_value = "edited_details"
        self.course.get_exam = MagicMock(return_value=dummy_exam)
        result = self.course.edit_question_details(
            2025, "SPRING", "A", 1,
            2030, "SPRING", "A", 2,
            "exam123", "new_q.pdf", "new_a.pdf"
        )
        dummy_exam.edit_question_details.assert_called_once_with(1, 2030, "SPRING", "A", 2, "exam123", "new_q.pdf",
                                                                 "new_a.pdf")
        self.assertEqual(result, "edited_details")


if __name__ == "__main__":
    unittest.main()
