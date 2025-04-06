import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
from Backend.BusinessLayer.Course.Comment import Comment
from Backend.BusinessLayer.Course.Reaction import Reaction


class TestComment(unittest.TestCase):
    def setUp(self):
        self.comment_id = "c1"
        self.writer_name = "John Doe"
        self.writer_id = "u1"
        self.date = datetime(2025, 4, 2)
        self.prev_id = None
        self.comment_text = "This is a test comment."
        self.deleted = False
        self.edited = False
        # יצירת מופע לבדיקה
        self.comment = Comment(
            comment_id=self.comment_id,
            writer_name=self.writer_name,
            writer_id=self.writer_id,
            date=self.date,
            prev_id=self.prev_id,
            comment_text=self.comment_text,
            deleted=self.deleted,
            edited=self.edited
        )

    @patch("Backend.DataLayer.CommentData.CommentRepository.CommentRepository.add_comment")
    def test_create(self, mock_add_comment):
        question_id = "q1"
        # קריאה למתודת create – שצריכה ליצור מופע חדש ולקרוא ל־add_comment
        new_comment = Comment.create(
            comment_id=self.comment_id,
            writer_name=self.writer_name,
            writer_id=self.writer_id,
            date=self.date,
            prev_id=self.prev_id,
            comment_text=self.comment_text,
            deleted=self.deleted,
            edited=self.edited,
            question_id=question_id
        )
        # בדיקה ש־add_comment נקראה עם הפרמטרים הנכונים
        mock_add_comment.assert_called_once_with(new_comment, question_id)
        self.assertEqual(new_comment.comment_id, self.comment_id)

    def test_to_dto(self):
        # יצירת תגובה בדויה עם מתודת to_dto מדומה
        dummy_reaction = MagicMock()
        dummy_reaction.to_dto.return_value = "reaction_dto"
        self.comment.reactions.append(dummy_reaction)

        dto = self.comment.to_dto()
        self.assertEqual(dto.comment_id, self.comment_id)
        self.assertEqual(dto.writer_name, self.writer_name)
        self.assertEqual(dto.comment_text, self.comment_text)
        self.assertIn("reaction_dto", dto.reactions)

    @patch("Backend.DataLayer.CommentData.CommentRepository.CommentRepository.update_deleted_comment")
    @patch("Backend.DataLayer.ReactionData.ReactionRepository.ReactionRepository.delete_reactions_by_comment_id")
    def test_delete_comment(self, mock_delete_reactions, mock_update_deleted_comment):
        self.comment.deleted = False
        self.comment.delete_comment()
        # ודא שהמאפיין deleted הוגדר כ-True
        self.assertTrue(self.comment.deleted)
        # בדיקה שקריאות לדאטה בייס בוצעו
        mock_delete_reactions.assert_called_once_with(self.comment_id)
        mock_update_deleted_comment.assert_called_once_with(self.comment)

    @patch("Backend.DataLayer.CommentData.CommentRepository.CommentRepository.edit_comment_text")
    def test_edit_comment_text(self, mock_edit_comment_text):
        new_text = "Updated comment text."
        self.comment.edit_comment_text(new_text)
        self.assertEqual(self.comment.comment_text, new_text)
        self.assertTrue(self.comment.edited)
        mock_edit_comment_text.assert_called_once_with(self.comment)

    @patch("Backend.BusinessLayer.Course.Reaction.Reaction.create")
    def test_add_reaction_new(self, mock_reaction_create):
        # יצירת תגובה בדויה
        dummy_reaction = MagicMock()
        dummy_reaction.reaction_id = "r1"
        mock_reaction_create.return_value = dummy_reaction

        # המשתמש לא הגיב קודם לכן – אמור ליצור תגובה חדשה
        result = self.comment.add_reaction("user1", "👍")
        self.assertIn(dummy_reaction, self.comment.reactions)
        self.assertEqual(result, self.writer_id)
        mock_reaction_create.assert_called_once()

    @patch("Backend.BusinessLayer.Course.Reaction.Reaction.create")
    def test_add_reaction_same_emoji(self, mock_reaction_create):
        # יצירת תגובה קיימת מהמשתמש עם אותו אמוג'י
        dummy_reaction = MagicMock()
        dummy_reaction.reaction_id = "r1"
        dummy_reaction.user_id = "user1"
        dummy_reaction.emoji = "👍"
        self.comment.reactions.append(dummy_reaction)

        # קריאה להוספת תגובה עם אותו אמוג'י – אין מה לעשות
        result = self.comment.add_reaction("user1", "👍")
        self.assertIsNone(result)
        mock_reaction_create.assert_not_called()

    @patch("Backend.DataLayer.ReactionData.ReactionRepository.ReactionRepository.remove_reaction")
    @patch("Backend.BusinessLayer.Course.Reaction.Reaction.create")
    def test_add_reaction_different_emoji(self, mock_reaction_create, mock_remove_reaction):
        # יצירת תגובה קיימת עם אמוג'י אחר
        existing_reaction = MagicMock()
        existing_reaction.reaction_id = "r1"
        existing_reaction.user_id = "user1"
        existing_reaction.emoji = "👎"
        self.comment.reactions.append(existing_reaction)

        # הגדרת תגובה חדשה
        new_reaction = MagicMock()
        new_reaction.reaction_id = "r2"
        new_reaction.user_id = "user1"
        new_reaction.emoji = "👍"
        mock_reaction_create.return_value = new_reaction

        result = self.comment.add_reaction("user1", "👍")
        # ודא שהסרת את התגובה הישנה והוספת את החדשה
        mock_remove_reaction.assert_called_once_with(existing_reaction.reaction_id)
        self.assertIn(new_reaction, self.comment.reactions)
        self.assertEqual(result, self.writer_id)

    @patch("Backend.DataLayer.ReactionData.ReactionRepository.ReactionRepository.remove_reaction")
    def test_remove_reaction(self, mock_remove_reaction):
        # יצירת תגובה בדויה והוספתה למערך התגובות
        dummy_reaction = MagicMock()
        dummy_reaction.reaction_id = "r1"
        self.comment.reactions.append(dummy_reaction)
        self.comment.remove_reaction("r1")
        mock_remove_reaction.assert_called_once_with("r1")
        self.assertNotIn(dummy_reaction, self.comment.reactions)

    def test_edit_text(self):
        # בדיקה פשוטה למתודת edit_text
        new_text = "New text content"
        self.comment.edit_text(new_text)
        self.assertEqual(self.comment.comment_text, new_text)

if __name__ == "__main__":
    unittest.main()
