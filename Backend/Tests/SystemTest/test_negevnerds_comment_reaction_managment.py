import io
import json
from unittest.mock import patch, MagicMock
from werkzeug.datastructures import FileStorage

from Backend.DataLayer.ReactionData.ReactionRepository import ReactionRepository
from Backend.BusinessLayer.Util.Exceptions import CourseIsNotExist, QuestionAlreadyInExam, CommentNotFound, \
    ExamIsNotExist, ReactionNotFound, QuestionNotFound
from Backend.DataLayer.DTOs.QuestionDTO import QuestionDTO
from Backend.Tests.SystemTest.BaseTestCase import BaseTestCase


def _mock_invalid_file(filename="exam.txt", content=b"invalid"):
    file = MagicMock()
    file.filename = filename
    file.file = io.BytesIO(content)
    file.content_type = 'text/plain'
    return file


class TestNegevNerdsCommentReactionManagement(BaseTestCase):

    def setUp(self):
        super().setUp()
        self.user = self._complete_user_registration("examuser@bgu.ac.il", "Pass1!", "Exam", "Uploader")
        self.course_id = "777.1.1010"
        self.year = 2023
        self.semester = "אביב"
        self.moed = "א"
        self.exam_file = self._mock_pdf_file()
        self.invalid_file = _mock_invalid_file()
        self._open_course(self.user, self.course_id, "מבוא להעלאת מבחנים")
        self.question_number = 165

    def tearDown(self):
        super().tearDown()

        if isinstance(self.negev.courseFacade.check_valid_question, MagicMock):
            del self.negev.courseFacade.check_valid_question

        if isinstance(self.negev.courseFacade.check_exam_full_pdf, MagicMock):
            del self.negev.courseFacade.check_exam_full_pdf

    # ---Tests for Discussions---
    @patch('Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf', return_value=None)
    @patch('Backend.BusinessLayer.Notifications.NotificationFacade.NotificationFacade.send_notification')
    def test_add_comment_success(self, mock_send_notification, mock_process_pdf):
        """Test: Add a comment successfully to a question discussion."""

        course_id = self.course_id
        year = self.year
        semester = self.semester
        moed = self.moed

        question_number = 9001  # ודא שזה נשמר לאורך כל הטסט

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
    def test_add_reaction_success(self, mock_process_pdf, mock_send_notification):
        """Test: Add reaction to a comment successfully."""
        new_course_id = "888.8.8888"
        self._open_course(self.user, new_course_id, "קורס לבדיקה תגובות")

        self.negev.add_question(
            course_id=new_course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=99,
            is_american=True,
            question_topics=["תגובות"],
            question_file=self.exam_file,
            answer_file=None
        )

        writer_name = "User A"
        writer_id = "user_a"
        question_id = "99"

        self.negev.add_comment(
            course_id=new_course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=99,
            writer_name=writer_name,
            writer_id=writer_id,
            prev_id="0",
            comment_text="זו תגובה לבדיקה",
            photo_file=None,
            question_id=question_id
        )

        reacting_user = self._complete_user_registration("another@bgu.ac.il", "Pass1!", "Another", "User")

        comment_id = "99_0"

        response = self.negev.add_reaction(
            course_id=new_course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=99,
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

    def test_get_comment_media_link_success(self):
        """Test: Successfully get media link of a comment."""
        link = self.negev.get_comment_media_link(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=1,
            comment_id="1_0"
        )
        self.assertIsInstance(link, str)
        self.assertTrue(link.endswith(".jpg") or link.endswith(".png") or link.endswith(".pdf"))

    def test_get_comment_media_link_comment_not_found(self):
        """Test: Getting media link for non-existing comment raises CommentNotFound."""
        with self.assertRaises(CommentNotFound):
            self.negev.get_comment_media_link(
                course_id=self.course_id,
                year=self.year,
                semester=self.semester,
                moed=self.moed,
                question_number=1,
                comment_id="nonexistent_comment"
            )

    def test_get_comment_media_link_course_not_exist(self):
        """Test: Getting media link for non-existing course raises CourseIsNotExist."""
        with self.assertRaises(CourseIsNotExist):
            self.negev.get_comment_media_link(
                course_id="000.0.0000",
                year=self.year,
                semester=self.semester,
                moed=self.moed,
                question_number=1,
                comment_id="1_0"
            )

    def test_remove_reaction_success(self):
        """Test: Add question, comment, reaction, then remove reaction successfully."""

        # Step 1: Add question
        self.negev.add_question(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=1,
            is_american=True,
            question_topics=["בדיקה"],
            question_file=self.exam_file,
            answer_file=None
        )

        # Step 2: Add comment
        writer_name = "User A"
        writer_id = "user_a"
        question_id = "165"
        self.negev.add_comment(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=165,
            writer_name=writer_name,
            writer_id=writer_id,
            prev_id="0",
            comment_text="תגובה לבדיקה",
            photo_file=None,
            question_id=question_id
        )
        comment_id = "1_0"

        # Step 3: Add reaction
        user_id = "another_user"
        emoji = "👍"
        self.negev.add_reaction(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=1,
            comment_id=comment_id,
            user_id=user_id,
            emoji=emoji
        )

        # Get reaction_id from the DB (if you're storing it)
        repo = ReactionRepository()
        reactions = repo.get_reactions_for_comment(comment_id)
        self.assertTrue(len(reactions) > 0)
        reaction_id = reactions[0].reaction_id

        # Step 4: Remove reaction
        result = self.negev.remove_reaction(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=1,
            comment_id=comment_id,
            reaction_id=reaction_id
        )

        # Step 5: Assert removal
        self.assertEqual(result, "ReactionData removed successfully.")
        self.assertEqual(len(repo.get_reactions_for_comment(comment_id)), 0)

    @patch('Backend.BusinessLayer.Course.CourseFacade.CourseFacade.remove_reaction')
    def test_remove_reaction_course_not_exist(self, mock_remove_reaction):
        """Test: Remove reaction fails because course does not exist."""
        mock_remove_reaction.side_effect = CourseIsNotExist("Course not found")

        with self.assertRaises(CourseIsNotExist):
            self.negev.remove_reaction(
                course_id="invalid_course",
                year=self.year,
                semester=self.semester,
                moed=self.moed,
                question_number=self.question_number,
                comment_id=self.comment_id,
                reaction_id=self.reaction_id
            )

    @patch('Backend.BusinessLayer.Course.CourseFacade.CourseFacade.remove_reaction')
    def test_remove_reaction_comment_not_found(self, mock_remove_reaction):
        """Test: Remove reaction fails because comment not found."""
        mock_remove_reaction.side_effect = CommentNotFound("comment_id")

        with self.assertRaises(CommentNotFound):
            self.negev.remove_reaction(
                course_id=self.course_id,
                year=self.year,
                semester=self.semester,
                moed=self.moed,
                question_number=self.question_number,
                comment_id="invalid_comment",
                reaction_id=self.reaction_id
            )

    @patch('Backend.BusinessLayer.Course.CourseFacade.CourseFacade.remove_reaction')
    def test_remove_reaction_reaction_not_found(self, mock_remove_reaction):
        """Test: Remove reaction fails because reaction not found."""
        mock_remove_reaction.side_effect = ReactionNotFound("reaction_id")

        with self.assertRaises(ReactionNotFound):
            self.negev.remove_reaction(
                course_id=self.course_id,
                year=self.year,
                semester=self.semester,
                moed=self.moed,
                question_number=self.question_number,
                comment_id=self.comment_id,
                reaction_id="invalid_reaction"
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

    @patch('Backend.BusinessLayer.NegevNerds.CourseFacade')
    def test_delete_comment_success(self, mock_course_facade_class):
        """Test: Successfully delete a comment."""

        mock_course_facade = MagicMock()
        mock_course_facade.delete_comment.return_value = None  # לא מחזיר כלום במחיקה
        mock_course_facade_class.return_value = mock_course_facade

        result = self.negev.delete_comment(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=self.question_number,
            comment_id="self.comment_id"
        )

        self.assertEqual(result, "CommentData deleted successfully.")
        mock_course_facade.delete_comment.assert_called_once_with(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=self.question_number,
            comment_id=self.comment_id
        )

    @patch('Backend.BusinessLayer.NegevNerds.CourseFacade')
    def test_delete_comment_not_found(self, mock_course_facade_class):
        """Test: Deleting non-existing comment raises CommentNotFound."""

        mock_course_facade = MagicMock()
        mock_course_facade.delete_comment.side_effect = CommentNotFound(comment_id="self.comment_id")
        mock_course_facade_class.return_value = mock_course_facade

        with self.assertRaises(CommentNotFound):
            self.negev.delete_comment(
                course_id=self.course_id,
                year=self.year,
                semester=self.semester,
                moed=self.moed,
                question_number=self.question_number,
                comment_id="000"
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

    def test_edit_comment_text_success(self):
        question_number, comment_id = self._add_question_and_comment()

        result = self.negev.edit_comment_text(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=question_number,
            comment_id=comment_id,
            new_text="טקסט חדש לעריכה"
        )

        self.assertEqual(result, "CommentData edited successfully.")

    @patch('Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf', return_value=None)
    def test_edit_comment_text_course_not_found(self, mock_process_pdf):
        with self.assertRaises(CourseIsNotExist(course_id="000.0.0000")):
            self.negev.edit_comment_text(
                course_id="000.0.0000",
                year=self.year,
                semester=self.semester,
                moed=self.moed,
                question_number=1,
                comment_id="1_0",
                new_text="טקסט"
            )

    def test_edit_comment_text_question_not_found(self):
        with self.assertRaises(QuestionNotFound):
            self.negev.edit_comment_text(
                course_id=self.course_id,
                year=self.year,
                semester=self.semester,
                moed=self.moed,
                question_number=9999,
                comment_id="9999_0",
                new_text="עדכון"
            )

    @patch('Backend.BusinessLayer.Analyzer.InformationRetrival.InformationRetrival.process_pdf', return_value=None)
    @patch('Backend.BusinessLayer.Analyzer.AnalyzerFacade.AnalyzerFacade.perform_information_retrival_question_pdf')
    def test_edit_comment_text_comment_not_found(self, mock_retrival_pdf, mock_process_pdf):
        """Test editing comment that does not exist raises CommentNotFound."""

        # מוסיף שאלה אבל לא תגובה
        self.negev.add_question(
            course_id=self.course_id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=9010,
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
                question_number=9010,
                comment_id="9010_0",  # לא קיימת תגובה
                new_text="עדכון"
            )