import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime

from Backend.BusinessLayer.Course.enums import Moed, Semester
from Backend.BusinessLayer.Util.Exceptions import CommentNotFound
from Backend.DataLayer.DTOs.QuestionDTO import QuestionDTO

# Adjust the import below to point to the module where Question is defined.
from Backend.BusinessLayer.Course.Question import Question
from Backend.BusinessLayer.Course.Comment import Comment


class TestQuestion(unittest.TestCase):
    def setUp(self):
        self.year = 2025
        self.semester = Semester.SPRING  # Pass valid Enum instance
        self.moed = Moed.A              # Pass valid Enum instance
        self.question_number = 1
        self.is_american = True
        self.link_to_question = "question.pdf"
        self.link_to_answer = "answer.pdf"
        self.question_topics = ["topic1", "topic2"]
        self.question_id = "q1"
        self.text = "sample question text"
        self.comments = []  # start with no comments

        self.question = Question(
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=self.question_number,
            is_american=self.is_american,
            link_to_question=self.link_to_question,
            link_to_answer=self.link_to_answer,
            question_topics=self.question_topics.copy(),
            question_id=self.question_id,
            comments=self.comments,
            text=self.text
        )

    @patch("Backend.DataLayer.Questions.QuestionRepository.QuestionRepository.add_question")
    def test_create(self, mock_add_question):
        exam_id = "exam123"
        created_question = Question.create(
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=self.question_number,
            is_american=self.is_american,
            link_to_question=self.link_to_question,
            link_to_answer=self.link_to_answer,
            exam_id=exam_id,
            question_id=self.question_id,
            question_topics=self.question_topics,
            question_text=self.text
        )
        # Verify that add_question was called with the created question and exam_id
        mock_add_question.assert_called_once_with(created_question, exam_id)
        self.assertEqual(created_question.year, self.year)
        self.assertEqual(created_question.semester, self.semester)
        self.assertEqual(created_question.moed, self.moed)

    def test_to_dto(self):
        # Prepare a dummy comment with a to_dto method.
        dummy_comment = MagicMock()
        dummy_comment.to_dto.return_value = {"dummy": "comment"}
        self.question.comments.append(dummy_comment)

        dto = self.question.to_dto("course123")
        self.assertIsInstance(dto, QuestionDTO)
        self.assertEqual(dto.question_id, self.question_id)
        self.assertEqual(dto.year, self.year)
        self.assertEqual(dto.semester, self.question.semester)
        self.assertEqual(dto.moed, self.question.moed)
        self.assertEqual(dto.question_number, self.question_number)
        self.assertEqual(dto.question_topics, self.question_topics)
        self.assertEqual(dto.is_american, self.is_american)
        self.assertEqual(dto.link_to_question, self.link_to_question)
        self.assertEqual(dto.comments_list, [{"dummy": "comment"}])
        self.assertEqual(dto.course_id, "course123")

    def test_generate_comment_id(self):
        comment_id = self.question.generate_comment_id()
        self.assertTrue(comment_id.startswith("comment"))

    @patch("Backend.DataLayer.QuestionTopics.QuestionTopicsRepository.QuestionTopicsRepository.get_question_topics")
    def test_get_question_topics(self, mock_get_topics):
        # Simulate repository returning a new topics list.
        new_topics = ["new_topic1", "new_topic2"]
        mock_get_topics.return_value = new_topics
        topics = self.question.get_question_topics()
        self.assertEqual(topics, new_topics)
        self.assertEqual(self.question.question_topics, new_topics)
        mock_get_topics.assert_called_once_with(self.question.id)

    def test_get_link_to_question(self):
        self.assertEqual(self.question.get_link_to_question(), self.link_to_question)

    def test_get_link_to_answer(self):
        self.assertEqual(self.question.get_link_to_answer(), self.link_to_answer)

    @patch("Backend.DataLayer.QuestionTopics.QuestionTopicsRepository.QuestionTopicsRepository.add_Topic_to_Question")
    def test_add_question_topic(self, mock_add_topic):
        new_topic = "new_topic"
        self.question.question_topics = set(self.question.question_topics)
        original_length = len(self.question.question_topics)
        self.question.add_question_topic(new_topic)
        self.assertEqual(len(self.question.question_topics), original_length + 1)
        self.assertIn(new_topic, self.question.question_topics)

    def test_generate_question_details_name(self):
        details_name = self.question.generate_question_details_name()
        expected = f"E-{self.year}-{self.semester}-{self.moed}-Q{self.question_number}"
        self.assertEqual(details_name, expected)

    @patch("Backend.DataLayer.QuestionTopics.QuestionTopicsRepository.QuestionTopicsRepository.remove_topic_from_question")
    def test_remove_question_topic_found(self, mock_remove_topic):
        topic_to_remove = self.question.question_topics[0]
        self.assertIn(topic_to_remove, self.question.question_topics)
        self.question.remove_question_topic(topic_to_remove)
        self.assertNotIn(topic_to_remove, self.question.question_topics)
        mock_remove_topic.assert_called_once_with(topic_to_remove, self.question.id)

    @patch("builtins.print")
    def test_remove_question_topic_not_found(self, mock_print):
        topic_not_present = "nonexistent_topic"
        original_topics = self.question.question_topics.copy()
        self.question.remove_question_topic(topic_not_present)
        mock_print.assert_called()  # Check that print was called
        self.assertEqual(self.question.question_topics, original_topics)

    @patch("Backend.BusinessLayer.Course.Comment.Comment.create")
    def test_add_comment_success(self, mock_comment_create):
        # Create a dummy comment with a writer_id attribute.
        dummy_comment = MagicMock()
        dummy_comment.writer_id = "writer1"
        mock_comment_create.return_value = dummy_comment
        result = self.question.add_comment(
            writer_name="John Doe",
            writer_id="writer1",
            prev_id=None,
            comment_text="Nice question",
            deleted=False,
            edited=False
        )
        self.assertIn(dummy_comment, self.question.comments)
        self.assertEqual(result, {"writer1"})
        mock_comment_create.assert_called_once()

    def test_add_reaction_success(self):
        # Prepare a dummy comment with a matching comment_id.
        dummy_comment = MagicMock()
        dummy_comment.comment_id = "comm1"
        dummy_comment.add_reaction.return_value = "result_value"
        self.question.comments.append(dummy_comment)
        result = self.question.add_reaction("comm1", "user1", "👍")
        self.assertEqual(result, "result_value")
        dummy_comment.add_reaction.assert_called_once_with("user1", "👍")

    def test_add_reaction_not_found(self):
        with self.assertRaises(Exception):  # Expect CommentNotFound to be raised
            self.question.add_reaction("nonexistent", "user1", "👍")

    def test_delete_comment_success(self):
        dummy_comment = MagicMock()
        dummy_comment.comment_id = "comm_del"
        self.question.comments.append(dummy_comment)
        self.question.delete_comment("comm_del")
        dummy_comment.delete_comment.assert_called_once()
        self.assertNotIn(dummy_comment, self.question.comments)

    def test_delete_comment_not_found(self):
        with self.assertRaises(Exception):  # Expect CommentNotFound
            self.question.delete_comment("nonexistent")

    def test_delete_comment_success(self):
        dummy_comment = MagicMock()
        dummy_comment.comment_id = "comm_del"
        self.question.comments.append(dummy_comment)
        self.question.delete_comment("comm_del")
        dummy_comment.delete_comment.assert_called_once()

    def test_edit_comment_text_not_found(self):
        with self.assertRaises(Exception):  # Expect CommentNotFound
            self.question.edit_comment_text("nonexistent", "New text")

    @patch("Backend.DataLayer.Questions.QuestionRepository.QuestionRepository.uploadSolution")
    def test_uploadSolution_success(self, mock_upload_solution):
        new_answer_path = "new_answer.pdf"
        mock_upload_solution.return_value = None  # Simulate successful update
        result = self.question.uploadSolution(new_answer_path)
        self.assertEqual(self.question.link_to_answer, new_answer_path)
        mock_upload_solution.assert_called_once_with(self.question.id, new_answer_path)
        self.assertEqual(result["status"], "success")

    @patch("Backend.DataLayer.Questions.QuestionRepository.QuestionRepository.uploadSolution", side_effect=Exception("db error"))
    def test_uploadSolution_failure(self, mock_upload_solution):
        new_answer_path = "new_answer.pdf"
        result = self.question.uploadSolution(new_answer_path)
        self.assertEqual(result["status"], "error")
        self.assertIn("db error", result["message"])

    def test_remove_reaction_success(self):
        dummy_comment = MagicMock()
        dummy_comment.comment_id = "comm_react"
        self.question.comments.append(dummy_comment)
        self.question.remove_reaction("comm_react", "reaction1")
        dummy_comment.remove_reaction.assert_called_once_with("reaction1")

    def test_remove_reaction_not_found(self):
        with self.assertRaises(Exception):  # Expect CommentNotFound
            self.question.remove_reaction("nonexistent", "reaction1")

    @patch("Backend.DataLayer.QuestionTopics.QuestionTopicsRepository.QuestionTopicsRepository.edit_question_topic")
    def test_edit_question_topic(self, mock_edit_question_topic):
        mock_edit_question_topic.return_value = "edited_topics"
        result = self.question.edit_question_topic(["new_topic"])
        mock_edit_question_topic.assert_called_once_with(self.question.id, ["new_topic"])
        self.assertEqual(result, "edited_topics")

    def test_str(self):
        # Add a dummy comment to simulate non-empty comments
        dummy_comment = MagicMock()
        self.question.comments.append(dummy_comment)
        s = str(self.question)
        self.assertIn(self.question.id, s)
        self.assertIn(str(self.year), s)
        self.assertIn(str(self.question_number), s)
        self.assertIn(str(len(self.question.comments)), s)


if __name__ == "__main__":
    unittest.main()
