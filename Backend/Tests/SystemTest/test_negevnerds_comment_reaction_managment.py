import io
from unittest.mock import patch, MagicMock

from Backend.BusinessLayer.Course.CourseFacade import CourseFacade
from Backend.BusinessLayer.User.UserFacade import UserFacade
from Backend.DataLayer.CommentData.CommentRepository import CommentRepository
from Backend.BusinessLayer.Util.Exceptions import CourseIsNotExist, CommentNotFound, QuestionNotFound, ExamIsNotExist
from Backend.Tests.SystemTest.BaseTestCase import BaseTestCase


def _mock_invalid_file(filename="exam.txt", content=b"invalid"):
    file = MagicMock()
    file.filename = filename
    file.file = io.BytesIO(content)
    file.content_type = 'text/plain'
    return file


class TestNegevNerdsCommentReactionManagement(BaseTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

    def setUp(self):
        super().setUp()

        self.course_id = "777.1.1010"
        self.year = 2023
        self.semester = "אביב"
        self.moed = "א"
        self.exam_file = self._mock_pdf_file()

        # משתמשי ברירת מחדל
        self.uploader = self._complete_user_registration("examuser@bgu.ac.il", "Pass1!", "Exam", "Uploader")
        self.comment_writer = self._complete_user_registration("writer@bgu.ac.il", "Pass1!", "Writer", "Test")

        # פתיחת קורס
        self._open_course(self.uploader, self.course_id, "מבוא לבדיקות")

    def tearDown(self):
        super().tearDown()
        self.negev.courseFacade = CourseFacade()
        self.negev.userFacade = UserFacade()

    # --- Static helpers for setUpClass ---
    @staticmethod
    def _mock_pdf_file_static(filename="exam.pdf", content=b"%PDF-1.4"):
        file = MagicMock()
        file.filename = filename
        file.file = io.BytesIO(content)
        file.content_type = 'application/pdf'
        return file

    @staticmethod
    def _mock_invalid_file(filename="exam.txt", content=b"invalid"):
        file = MagicMock()
        file.filename = filename
        file.file = io.BytesIO(content)
        file.content_type = 'text/plain'
        return file

    @staticmethod
    def _mock_image_file(filename="image.jpg", content=b"fake image"):
        file = MagicMock()
        file.filename = filename
        file.file = io.BytesIO(content)
        file.content_type = 'image/jpeg'
        return file

    def _add_question_comment_with_users(self, question_number=9999):
        """
        יוצר משתמש שכותב תגובה, מוסיף שאלה, מוסיף תגובה, ומחזיר את comment_id ואת ה-user_id של כותב התגובה
        """
        # יוצר משתמש חדש שהוא כותב התגובה
        comment_writer = self._complete_user_registration(
            email=f"writer{question_number}@bgu.ac.il",
            password="Pass1!",
            first_name="Comment",
            last_name="Writer"
        )

        # מוסיף שאלה
        self.negev.add_question(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=question_number,
            is_american=True,
            question_topics=["בדיקה"],
            question_file=self.exam_file,
            answer_file=None
        )

        comment_id = f"{question_number}_0"

        # מוסיף תגובה
        self.negev.add_comment(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=question_number,
            writer_name="Comment Writer",
            writer_id=comment_writer.user_id,
            prev_id="0",
            comment_text="תגובה לבדיקה",
            photo_file=None,
            question_id=str(question_number)
        )

        return comment_id, comment_writer.user_id

    # ---Tests for Discussions---
    @patch('Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf', return_value=None)
    @patch('Backend.BusinessLayer.Notifications.NotificationFacade.NotificationFacade.send_notification')
    def test_add_comment_success(self, mock_send_notification, mock_process_pdf):
        """Test: Add a comment successfully to a question discussion."""
        course_id = self.course_id
        year = self.year
        semester = self.semester
        moed = self.moed
        question_number = 9001
        self.negev.add_question(
            course_id=course_id,
            year=year,
            semester=semester,
            moed=moed,
            question_number=question_number,
            is_american=True,
            question_topics=["מבני נתונים"],
            question_file=self.exam_file,
            answer_file=None
        )

        writer_name = "Test User"
        writer_id = "test_user_id"
        prev_id = "0"  # תגובה ראשונה
        comment_text = "זוהי תגובת בדיקה"
        question_id = str(question_number)  # תואם לשאלה שהוספה

        result = self.negev.add_comment(
            course_id=course_id,
            year=year,
            semester=semester,
            moed=moed,
            question_number=question_number,
            writer_name=writer_name,
            writer_id=writer_id,
            prev_id=prev_id,
            comment_text=comment_text,
            photo_file=None,
            question_id=question_id
        )

        self.assertEqual(result, "CommentData added successfully.")

    @patch('Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf', return_value=None)
    @patch('Backend.BusinessLayer.Notifications.NotificationFacade.NotificationFacade.send_notification')
    def test_add_comment_course_not_found(self, mock_send_notification, mock_process_pdf):
        """Test: Attempt to add comment to non-existent course should fail."""

        writer_name = "Test User"
        writer_id = "test_user_id"
        prev_id = "0"
        comment_text = "תגובה על קורס שלא קיים"
        question_id = "99"

        with self.assertRaises(Exception) as context:
            self.negev.add_comment(
                course_id="fake_course",
                year=2025,
                semester="חורף",
                moed="ב",
                question_number=1,
                writer_name=writer_name,
                writer_id=writer_id,
                prev_id=prev_id,
                comment_text=comment_text,
                photo_file=None,
                question_id=question_id
            )

        self.assertIn("Failed to add comment", str(context.exception))

    @patch('Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf', return_value=None)
    @patch('Backend.BusinessLayer.Notifications.NotificationFacade.NotificationFacade.send_notification')
    def test_add_comment_question_not_found(self, mock_send_notification, mock_process_pdf):
        """Test: Attempt to add comment to non-existent question should fail."""

        # פתיחת קורס אבל בלי להוסיף שאלה
        course_id = self.course_id

        writer_name = "Test User"
        writer_id = "test_user_id"
        prev_id = "0"
        comment_text = "תגובה על שאלה שלא קיימת"
        question_id = "999"  # מזהה שאלה שלא קיים

        with self.assertRaises(Exception) as context:
            self.negev.add_comment(
                course_id=course_id,
                year=self.year,
                semester=self.semester,
                moed=self.moed,
                question_number=999,  # אין שאלה כזו
                writer_name=writer_name,
                writer_id=writer_id,
                prev_id=prev_id,
                comment_text=comment_text,
                photo_file=None,
                question_id=question_id
            )

        self.assertIn("Failed to add comment", str(context.exception))

    @patch('Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf', return_value=None)
    @patch('Backend.BusinessLayer.Notifications.NotificationFacade.NotificationFacade.send_notification')
    def test_add_comment_with_photo_success(self, mock_send_notification, mock_process_pdf):
        """Test: Successfully add a comment with a photo."""

        # פתיחת שאלה רגילה
        self.negev.add_question(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=31,
            is_american=True,
            question_topics=["מבני נתונים"],
            question_file=self.exam_file,
            answer_file=None
        )

        # יצירת קובץ תמונה מזויף
        photo_file = self._mock_pdf_file(filename="image.jpg", content=b"fake image content")

        result = self.negev.add_comment(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=31,
            writer_name="Test User",
            writer_id="user123",
            prev_id="0",
            comment_text="הנה תמונה מצורפת",
            photo_file=photo_file,
            question_id="31"
        )

        self.assertEqual(result, "CommentData added successfully.")

    @patch('Backend.BusinessLayer.Notifications.NotificationFacade.NotificationFacade.send_notification')
    @patch('Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf', return_value=None)
    @patch('Backend.BusinessLayer.User.UserFacade.UserFacade.should_send_notification', return_value=True)
    def test_add_reaction_success(self, mock_should_send_notification, mock_process_pdf, mock_send_notification):
        """Test: Add reaction to a comment successfully."""

        # משתמש שיכתוב את התגובה
        self.comment_writer = self._complete_user_registration(
            "writer@bgu.ac.il", "Pass1!", "Writer", "Test"
        )

        # מוסיפים את המשתמש ידנית למפת המשתמשים
        self.negev._user_facade.users_byId[self.comment_writer.user_id] = self.comment_writer

        question_number = 8888
        comment_id = f"{question_number}_0"

        self.negev.add_question(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=question_number,
            is_american=True,
            question_topics=["מבני נתונים"],
            question_file=self.exam_file,
            answer_file=None
        )

        self.negev.add_comment(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=question_number,
            writer_name="Writer Test",
            writer_id=self.comment_writer.user_id,  # ← פה השינוי
            prev_id="0",
            comment_text="תגובה לבדיקה",
            photo_file=None,
            question_id=str(question_number)
        )

        reacting_user = self._complete_user_registration(
            "reactor@bgu.ac.il", "Pass1!", "React", "User"
        )

        # ✅ גם אותו מוסיפים
        self.negev._user_facade.users_byId[reacting_user.user_id] = reacting_user

        response = self.negev.add_reaction(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=question_number,
            comment_id=comment_id,
            user_id=reacting_user.user_id,
            emoji="❤️"
        )

        self.assertEqual(response, "ReactionData added successfully.")

    @patch('Backend.BusinessLayer.Notifications.NotificationFacade.NotificationFacade.send_notification')
    def test_add_reaction_same_user_no_notification(self, mock_send_notification):
        """Test: No notification sent when user reacts to their own comment."""
        comment_id = "some_comment_id"

        receiver_id = "user123"

        self.negev.courseFacade.add_reaction = MagicMock(return_value=receiver_id)

        result = self.negev.add_reaction(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=1,
            comment_id=comment_id,
            user_id="user123",  # אותו יוזר
            emoji="👍"
        )

        self.assertEqual(result, "ReactionData added successfully.")
        mock_send_notification.assert_not_called()

    def test_add_reaction_invalid_comment(self):
        """Test: Adding reaction to a non-existent comment raises CommentNotFound."""
        self.negev.courseFacade.add_reaction = MagicMock(side_effect=CommentNotFound("Comment does not exist"))

        with self.assertRaises(CommentNotFound):
            self.negev.add_reaction(
                course_id=self.course_id,
                year=self.year,
                semester=self.semester,
                moed=self.moed,
                question_number=1,
                comment_id="invalid_comment_id",
                user_id="user1",
                emoji="👍"
            )

    def test_add_reaction_course_not_exist(self):
        """Test: Adding reaction to a course that doesn't exist raises CourseIsNotExist."""
        self.negev.courseFacade.add_reaction = MagicMock(side_effect=CourseIsNotExist("Course not found"))

        with self.assertRaises(CourseIsNotExist):
            self.negev.add_reaction(
                course_id="invalid_course",
                year=2023,
                semester="אביב",
                moed="א",
                question_number=1,
                comment_id="some_comment_id",
                user_id="user1",
                emoji="😂"
            )

    @patch('Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf', return_value=None)
    @patch('Backend.BusinessLayer.Analyzer.AnalyzerFacade.AnalyzerFacade.perform_information_retrival_question_pdf')
    def test_get_comment_media_link_success(self, mock_ir, mock_pdf):
        writer = self._complete_user_registration("writer@bgu.ac.il", "Pass1!", "Writer", "Test")
        self.negev._user_facade.users_byId[writer.user_id] = writer

        question_number = 1111
        self.negev.add_question(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=question_number,
            is_american=True,
            question_topics=["נושאים"],
            question_file=self.exam_file,
            answer_file=None
        )

        # מוסיף תגובה
        course = self.negev.courseFacade.get_course(self.course_id)
        exam = course.get_exam(self.year, self.semester, self.moed)
        question = exam.get_question(question_number)
        real_question_id = question.id

        self.negev.add_comment(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=question_number,
            writer_name="Writer Test",
            writer_id=writer.user_id,
            prev_id="0",
            comment_text="תגובה עם לינק",
            photo_file=None,
            question_id=real_question_id
        )

        metadata = self.negev.get_comments_metadata(real_question_id)
        comment_id = metadata[0]["comment_id"]

        link = self.negev.get_comment_media_link(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=question_number,
            comment_id=comment_id
        )

        self.assertIsInstance(link, str)

    def test_get_comment_media_link_question_not_found(self):
        with self.assertRaises(QuestionNotFound):
            self.negev.get_comment_media_link(
                course_id=self.course_id,
                year=self.year,
                semester=self.semester,
                moed=self.moed,
                question_number=9999,
                comment_id="nonexistent_comment_id"
            )

    def test_get_comment_media_link_exam_not_found(self):
        # יוצרים קורס אבל לא מוסיפים מבחן
        new_course_id = "123.3.3333"
        self.negev.courseFacade.open_course(
            course_id=new_course_id,
            name="מערכות",
            course_topics=["בדיקה"]
        )

        with self.assertRaises(ExamIsNotExist):
            self.negev.get_comment_media_link(
                course_id=new_course_id,
                year=self.year,
                semester=self.semester,
                moed=self.moed,
                question_number=1,
                comment_id="fake_id"
            )

    @patch('Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf', return_value=None)
    @patch.object(UserFacade, "should_send_notification", return_value=False)
    @patch("Backend.BusinessLayer.Notifications.LateNotifications.socketio.emit", return_value=None)
    def test_remove_reaction_success(self, mock_emit, mock_should_send_notification, mock_process_pdf):
        # הרשמת משתמשים
        writer = self._complete_user_registration("writer@bgu.ac.il", "Pass1!", "Writer", "Test")
        reactor = self._complete_user_registration("reactor@bgu.ac.il", "Pass1!", "Reactor", "User")

        # הוספה של המשתמשים למערכת
        self.negev._user_facade.users_byId[writer.user_id] = writer
        self.negev._user_facade.users_byId[reactor.user_id] = reactor

        question_number = 9010
        self.negev.add_question(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=question_number,
            is_american=True,
            question_topics=["בדיקה"],
            question_file=self.exam_file,
            answer_file=None
        )

        real_question_id = self.negev.courseFacade.get_course(self.course_id).get_exam(
            self.year, self.semester, self.moed).get_question(question_number).id

        self.negev.add_comment(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=question_number,
            writer_name="Writer Test",
            writer_id=writer.user_id,
            prev_id="0",
            comment_text="טקסט לבדיקה",
            photo_file=None,
            question_id=real_question_id
        )

        comment_metadata = self.negev.get_comments_metadata(real_question_id)[0]
        comment_id = comment_metadata["comment_id"]
        receiver_id = comment_metadata["writer_id"]

        # ✅ הדפסות לאבחון הבעיה
        print("writer.user_id =", writer.user_id)
        print("receiver_id =", receiver_id)
        print("users_byId.keys =", list(self.negev._user_facade.users_byId.keys()))

        # ודא שכותב התגובה (receiver_id) קיים במערכת כדי למנוע שגיאה בשליחה
        self.negev._user_facade.users_byId[receiver_id] = writer

        # הוספת רגש
        reaction_id = self.negev.add_reaction(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=question_number,
            comment_id=comment_id,
            user_id=reactor.user_id,
            emoji="👍"
        )

        # הסרת הרגש
        result = self.negev.remove_reaction(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=question_number,
            comment_id=comment_id,
            reaction_id=reaction_id
        )

        assert result == "ReactionData removed successfully."

    def test_remove_reaction_question_not_found(self):
        with self.assertRaises(QuestionNotFound):
            self.negev.remove_reaction(
                course_id=self.course_id,
                year=self.year,
                semester=self.semester,
                moed=self.moed,
                question_number=12345,  # לא קיימת
                comment_id="some_comment_id",
                reaction_id="some_reaction_id"
            )

    def test_remove_reaction_course_not_found(self):
        with self.assertRaises(CourseIsNotExist):
            self.negev.remove_reaction(
                course_id="fake.course.id",
                year=self.year,
                semester=self.semester,
                moed=self.moed,
                question_number=1,
                comment_id="c1",
                reaction_id="r1"
            )

    def test_remove_reaction_exam_not_found(self):
        self.negev.courseFacade.open_course("999.9.9999", "מערכות", ["בדיקה"])
        with self.assertRaises(ExamIsNotExist):
            self.negev.remove_reaction(
                course_id="999.9.9999",
                year=self.year,
                semester=self.semester,
                moed=self.moed,
                question_number=1,
                comment_id="c1",
                reaction_id="r1"
            )

    @patch('Backend.BusinessLayer.NegevNerds.CommentRepository')
    def test_get_comments_metadata_success(self, mock_comment_repo_class):
        """Test: Successfully retrieves comments metadata for a question."""
        fake_comments_metadata = [
            {"comment_id": "comment1", "writer_name": "User A", "timestamp": "2025-04-30"},
            {"comment_id": "comment2", "writer_name": "User B", "timestamp": "2025-04-30"}
        ]

        mock_comment_repo = MagicMock()
        mock_comment_repo.get_comments_metadata_by_question_id.return_value = fake_comments_metadata
        mock_comment_repo_class.return_value = mock_comment_repo

        question_id = "some_question_id"
        result = self.negev.get_comments_metadata(question_id)

        self.assertEqual(result, fake_comments_metadata)
        mock_comment_repo.get_comments_metadata_by_question_id.assert_called_once_with(question_id)

    @patch('Backend.BusinessLayer.NegevNerds.CommentRepository')
    def test_get_comments_metadata_failure(self, mock_comment_repo_class):
        """Test: Fail to retrieve comments metadata returns empty list."""

        mock_comment_repo = MagicMock()
        mock_comment_repo.get_comments_metadata_by_question_id.side_effect = Exception("Database error")
        mock_comment_repo_class.return_value = mock_comment_repo

        question_id = "some_question_id"
        result = self.negev.get_comments_metadata(question_id)

        self.assertEqual(result, [])

    @patch('Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf', return_value=None)
    def test_delete_comment_success(self, mock_ir):
        """Test: Deleting an existing comment should succeed."""

        # Step 1: Add user
        writer = self._complete_user_registration(
            "writer@bgu.ac.il", "Pass1!", "Writer", "Test"
        )
        self.negev._user_facade.users_byId[writer.user_id] = writer

        # Step 2: Add question
        question_number = 88881
        self.negev.add_question(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=question_number,
            is_american=True,
            question_topics=["בדיקות"],
            question_file=self.exam_file,
            answer_file=None
        )

        # Step 3: Get the real question ID
        course = self.negev.courseFacade.get_course(self.course_id)
        exam = course.get_exam(self.year, self.semester, self.moed)
        question = exam.get_question(question_number)
        real_question_id = question.id

        # Step 4: Add comment
        self.negev.add_comment(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=question_number,
            writer_name="Writer Test",
            writer_id=writer.user_id,
            prev_id="0",
            comment_text="תגובה לבדיקה למחיקה",
            photo_file=None,
            question_id=real_question_id
        )

        # Step 5: Retrieve the comment_id via metadata
        metadata_list = self.negev.get_comments_metadata(real_question_id)
        print(f"[DEBUG] Metadata list: {metadata_list}")
        assert len(metadata_list) > 0, "לא נמצאו תגובות"

        real_comment_id = metadata_list[0]["comment_id"]
        print(f"[DEBUG] Found real_comment_id: {real_comment_id}")

        # Step 6: Load it into memory for deletion
        comment_model = CommentRepository().get_comment_by_id(real_comment_id)
        assert comment_model is not None, "התגובה לא נשמרה במסד הנתונים"
        comment = comment_model
        question.comments.append(comment)

        # Step 7: Delete comment
        result = self.negev.delete_comment(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=question_number,
            comment_id=real_comment_id
        )

        self.assertEqual(result, "CommentData deleted successfully.")

    @patch('Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf', return_value=None)
    def test_delete_comment_not_found(self, mock_ir):
        """Test: Deleting non-existing comment raises CommentNotFound."""

        # שלב 1: מוסיפים שאלה אמיתית
        question_number = 88880
        self.negev.add_question(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=question_number,
            is_american=True,
            question_topics=["בדיקות"],
            question_file=self.exam_file,
            answer_file=None
        )

        non_existent_comment_id = "9999_0"
        with self.assertRaises(CommentNotFound):
            self.negev.delete_comment(
                course_id=self.course_id,
                year=self.year,
                semester=self.semester,
                moed=self.moed,
                question_number=question_number,
                comment_id=non_existent_comment_id
            )

    def _add_question_and_comment(self, question_number=9002, comment_id="9002_0"):
        self.negev.add_question(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=question_number,
            is_american=True,
            question_topics=["מבני נתונים"],
            question_file=self.exam_file,
            answer_file=None
        )

        self.negev.add_comment(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=question_number,
            writer_name="Editor",
            writer_id="user123",
            prev_id="0",
            comment_text="תגובה מקורית",
            photo_file=None,
            question_id=str(question_number)
        )

        return question_number, comment_id

    @patch('Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf', return_value=None)
    @patch('Backend.BusinessLayer.Analyzer.AnalyzerFacade.AnalyzerFacade.perform_information_retrival_question_pdf')
    def test_edit_comment_text_success(self, mock_retrival_pdf, mock_process_pdf):
        """Test editing an existing comment's text works as expected."""

        writer = self._complete_user_registration("writer@bgu.ac.il", "Pass1!", "Writer", "Test")
        self.negev._user_facade.users_byId[writer.user_id] = writer

        question_number = 9011
        self.negev.add_question(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=question_number,
            is_american=True,
            question_topics=["טסטים"],
            question_file=self.exam_file,
            answer_file=None
        )

        course = self.negev.courseFacade.get_course(self.course_id)
        exam = course.get_exam(self.year, self.semester, self.moed)
        question = exam.get_question(question_number)
        real_question_id = question.id

        self.negev.add_comment(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=question_number,
            writer_name="Writer Test",
            writer_id=writer.user_id,
            prev_id="0",
            comment_text="תגובה לפני עריכה",
            photo_file=None,
            question_id=real_question_id
        )

        metadata_list = self.negev.get_comments_metadata(real_question_id)
        comment_id = metadata_list[0]["comment_id"]

        result = self.negev.edit_comment_text(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=question_number,
            comment_id=comment_id,
            new_text="טקסט מעודכן"
        )

        self.assertEqual(result, "CommentData edited successfully.")

    @patch('Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf', return_value=None)
    @patch('Backend.BusinessLayer.Analyzer.AnalyzerFacade.AnalyzerFacade.perform_information_retrival_question_pdf')
    def test_edit_comment_text_not_found(self, mock_retrival_pdf, mock_process_pdf):
        """Test editing a non-existing comment raises CommentNotFound."""

        self.negev.add_question(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=9012,
            is_american=True,
            question_topics=["בדיקה"],
            question_file=self.exam_file,
            answer_file=None
        )

        with self.assertRaises(CommentNotFound):
            self.negev.edit_comment_text(
                course_id=self.course_id,
                year=self.year,
                semester=self.semester,
                moed=self.moed,
                question_number=9012,
                comment_id="9012_0",
                new_text="ניסיון לעריכה"
            )
