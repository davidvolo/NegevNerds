import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime
from Backend.BusinessLayer.Course.Comment import Comment
from Backend.BusinessLayer.Util.Exceptions import ReactionNotFound
from Backend.DataLayer.Questions.QuestionModel import QuestionModel
from Backend.DataLayer.UserCourses.UserCoursesModel import UserCoursesModel
from Backend.DataLayer.CourseManagers.CourseManagersModel import CourseManagersModel
from Backend.DataLayer.QuestionTopics.QuestionTopicsModel import QuestionTopicsModel
from Backend.DataLayer.User.UserModel import UserModel
from Backend.DataLayer.Exam.ExamModel import ExamModel
from Backend.DataLayer.Course.CourseModel import CourseModel
# from Backend.DataLayer import *


class TestComment(unittest.TestCase):

    def setUp(self):
        """Patch all necessary modules before running each test."""
        self.mocked_classes = patch.multiple(
            'Backend.DataLayer.CommentData',
            CommentRepository=MagicMock,
            ReactionRepository=MagicMock,
            ReactionModel=MagicMock,
            UserModel=MagicMock,
            CommentModel=MagicMock,
            QuestionModel=MagicMock,
            UserCoursesModel=MagicMock,
            CourseManagersModel=MagicMock,
            QuestionTopicsModel=MagicMock,
            ExamModel=MagicMock,
            CourseModel=MagicMock
        )
        self.mocked_classes.start()  # Start patching

        self.comment = Comment(
            comment_id="1",
            writer_name="User1",
            writer_id="user123",
            date=datetime.now(),
            prev_id=None,
            comment_text="This is a test comment",
            deleted=False,
            edited=False
        )

    @patch('Backend.DataLayer.CommentData.CommentRepository')  # Mock the CommentRepository
    @patch('Backend.DataLayer.Reaction.ReactionRepository')  # Mock the ReactionRepository
    # @patch('Backend.DataLayer.Reaction.ReactionModel')  # Mock the ReactionModel
    # @patch('Backend.DataLayer.User.UserModel')  # Mock the UserModel
    # @patch('Backend.DataLayer.CommentData.CommentModel')  # Mock the CommentModel
    # @patch('Backend.DataLayer.Questions.QuestionModel')  # Mock the QuestionModel
    # @patch('Backend.DataLayer.UserCourses.UserCoursesModel')  # Mock the UserCoursesModel
    # @patch('Backend.DataLayer.CourseManagers.CourseManagersModel')
    # @patch('Backend.DataLayer.QuestionTopics.QuestionTopicsModel')
    # @patch('Backend.DataLayer.Exam.ExamModel')
    # @patch('Backend.DataLayer.Course.CourseModel')
    def test_create_comment(self , MockCourseModel ,MockExamModel ,MockQuestionTopicModel ,MockCourseManagerModel,
                            MockUserCoursesModel, MockQuestionModel, MockCommentModel, MockUserModel,MockReactionModel,
                            MockReactionRepo, MockCommentRepo):
        """Test case for creating a new comment."""
        # Arrange
        mock_repo = MagicMock()
        MockCommentRepo.return_value = mock_repo

        # Mock the add_comment method to avoid database interaction
        mock_repo.add_comment = MagicMock()

        # Act
        comment = Comment.create(
            comment_id="2",
            writer_name="User2",
            writer_id="user456",
            date=datetime.now(),
            prev_id=None,
            comment_text="New test comment",
            deleted=False,
            edited=False,
            question_id="q1"
        )

        # Assert
        self.assertEqual(comment.comment_id, "2")
        mock_repo.add_comment.assert_called_once_with(comment, "q1")

    def test_to_dto(self):
        """Test case for converting comment to DTO."""
        # Act
        dto = self.comment.to_dto()

        # Assert
        self.assertEqual(dto.comment_id, self.comment.comment_id)
        self.assertEqual(dto.writer_name, self.comment.writer_name)
        self.assertEqual(dto.comment_text, self.comment.comment_text)

    @patch('Backend.DataLayer.Reaction.ReactionRepository')  # Mock the ReactionRepository
    @patch('Backend.DataLayer.Reaction.ReactionModel')  # Mock the ReactionModel
    @patch('Backend.DataLayer.CommentData.CommentRepository')  # Mock the CommentRepository
    @patch('Backend.DataLayer.User.UserModel')
    def test_add_reaction(self, MockUserModel, MockCommentRepo, MockReactionModel, MockReactionRepo):
        """Test case for adding a reaction to a comment."""
        # Arrange
        mock_reaction_repo = MagicMock()
        MockReactionRepo.return_value = mock_reaction_repo
        mock_reaction_model = MagicMock()
        MockReactionModel.return_value = mock_reaction_model

        # Act
        writer_id = self.comment.add_reaction(user_id="user789", emoji="like")

        # Assert
        self.assertEqual(writer_id, "user123")  # The comment writer's ID
        mock_reaction_repo.create.assert_called_once()

    def test_remove_reaction(self):
        """Test case for removing a reaction from a comment."""
        # Arrange
        reaction = MagicMock()
        reaction.reaction_id = "reaction1"
        self.comment.reactions.append(reaction)

        with patch('Backend.DataLayer.Reaction.ReactionRepository') as MockReactionRepo:
            mock_reaction_repo = MagicMock()
            MockReactionRepo.return_value = mock_reaction_repo

            # Act
            self.comment.remove_reaction("reaction1")

            # Assert
            self.assertNotIn(reaction, self.comment.reactions)
            mock_reaction_repo.remove_reaction.assert_called_once_with("reaction1")

    def test_delete_comment(self):
        """Test case for deleting a comment."""
        # Arrange
        with patch('Backend.DataLayer.CommentData.CommentRepository') as MockCommentRepo:
            mock_repo = MagicMock()
            MockCommentRepo.return_value = mock_repo

            # Act
            self.comment.delete_comment()

            # Assert
            self.assertTrue(self.comment.deleted)
            mock_repo.update_deleted_comment.assert_called_once_with(self.comment)

    def test_edit_comment_text(self):
        """Test case for editing a comment's text."""
        # Arrange
        new_text = "Updated test comment"

        with patch('Backend.DataLayer.CommentData.CommentRepository') as MockCommentRepo:
            mock_repo = MagicMock()
            MockCommentRepo.return_value = mock_repo

            # Act
            self.comment.edit_comment_text(new_text)

            # Assert
            self.assertEqual(self.comment.comment_text, new_text)
            self.assertTrue(self.comment.edited)
            mock_repo.edit_comment_text.assert_called_once_with(self.comment)

    def test_generate_reaction_id(self):
        """Test case for generating a unique reaction ID."""
        # Act
        reaction_id = self.comment.generate_reaction_id()

        # Assert
        self.assertTrue(reaction_id.startswith("reaction"))
        self.assertTrue(len(reaction_id) > 8)  # UUID will generate a long string


if __name__ == '__main__':
    unittest.main()
