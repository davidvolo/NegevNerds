import pytest
import threading
from datetime import datetime
from unittest.mock import Mock, patch
from Backend.BusinessLayer.Course.Comment import Comment
from Backend.BusinessLayer.Course.Reaction import Reaction


class TestComment:
    def test_comment_initialization(self):
        comment = Comment(
            comment_id="test1",
            writer_name="John",
            writer_id="user123",
            comment_text="Hello world"
        )
        assert comment.comment_id == "test1"
        assert comment.writer_name == "John"
        assert comment.comment_text == "Hello world"
        assert comment.reactions == []


    def test_delete_comment(self, mocker):
        mock_repo = mocker.patch('Backend.BusinessLayer.Course.Comment.CommentRepository.update_deleted_comment')
        comment = Comment(comment_id="test1", writer_name="John", writer_id="user123")
        comment.delete_comment()

        assert comment.deleted is True
        mock_repo.assert_called_once()

    def test_edit_comment_text(self, mocker):
        mock_repo = mocker.patch('Backend.BusinessLayer.Course.Comment.CommentRepository.edit_comment_text')
        comment = Comment(comment_id="test1", writer_name="John", writer_id="user123")

        comment.edit_comment_text("Updated text")

        assert comment.comment_text == "Updated text"
        assert comment.edited is True
        mock_repo.assert_called_once()

    def test_add_reaction(self, mocker):
        mocker.patch('Backend.BusinessLayer.Course.Reaction.Reaction.create',
                     return_value=Mock(reaction_id="r1", user_id="user1", emoji="👍"))
        comment = Comment(comment_id="test1", writer_name="John", writer_id="user123")

        result = comment.add_reaction("user1", "👍")

        assert len(comment.reactions) == 1
        assert comment.reactions[0].emoji == "👍"
        assert result == "user123"

    def test_add_reaction_replace_existing(self, mocker):
        comment = Comment(comment_id="test1", writer_name="John", writer_id="user123")

        # Mock Reaction.create to return different reactions
        mocker.patch('Backend.BusinessLayer.Course.Reaction.Reaction.create',
                     side_effect=[
                         Mock(reaction_id="r1", user_id="user1", emoji="👍"),
                         Mock(reaction_id="r2", user_id="user1", emoji="👎")
                     ])

        # Mock remove_reaction to actually remove the reaction
        def remove_mock(reaction_id):
            comment.reactions = [r for r in comment.reactions if r.reaction_id != reaction_id]

        mocker.patch('Backend.BusinessLayer.Course.Reaction.ReactionRepository.remove_reaction')
        mocker.patch.object(comment, 'remove_reaction', side_effect=remove_mock)

        comment.add_reaction("user1", "👍")
        assert len(comment.reactions) == 1
        assert comment.reactions[0].emoji == "👍"

        comment.add_reaction("user1", "👎")

        assert len(comment.reactions) == 1
        assert comment.reactions[0].emoji == "👎"

    def test_remove_reaction(self, mocker):
        mock_repo = mocker.patch('Backend.BusinessLayer.Course.Reaction.ReactionRepository.remove_reaction')
        mock_reaction = Mock(reaction_id="r1", user_id="user1", emoji="👍")
        comment = Comment(comment_id="test1", writer_name="John", writer_id="user123")
        comment.reactions = [mock_reaction]

        comment.remove_reaction("r1")

        assert len(comment.reactions) == 0
        mock_repo.assert_called_once_with("r1")