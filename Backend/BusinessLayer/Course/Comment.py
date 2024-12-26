from datetime import datetime

from Backend.BusinessLayer.Util.Exceptions import UserAlreadyPostEmoji, EmojiNotFounded
from Backend.DataLayer.Comment.CommentRepository import CommentRepository
from Backend.DataLayer.DTOs.CommentDTO import CommentDTO


class Comment:
    def __init__(self, comment_id, writer_name, date=None, prev_id=None, comment_text=""):
        """
        Initialize a Comment instance.
        """
        self.comment_id = comment_id
        self.writer_name = writer_name
        self.date = date if date else datetime.now()  # Default to current date if not provided
        self.prev_id = prev_id
        self.comment_text = comment_text
        self.emoji_counter_map = {"like": set(), "dislike": set()}

    @classmethod
    def create(cls, comment_id, writer_name, date, prev_id, comment_text, question_id):
        """
        Class method to create a new comment and save to database
        Returns:
            Comment: Newly created comment instance
        """

        comment = cls(
            comment_id=comment_id,
            writer_name=writer_name,
            date=date,
            prev_id=prev_id,
            comment_text=comment_text,
        )
        comment_repo = CommentRepository()
        comment_repo.add_Comment(comment, question_id)

        return comment

    def to_dto(self):
        """
        Converts the Comment instance to a CommentDTO.
        :return: CommentDTO instance.
        """
        return CommentDTO(
            comment_id=self.comment_id,
            writer_name=self.writer_name,
            date=self.date,
            prev_id=self.prev_id,
            comment_text=self.comment_text
        )

    def add_emoji(self, emoji, userId):
        """
        Add an emoji to the Comment, incrementing its count.
        """
        # Ensure the emoji exists in the counter map
        if emoji not in self.emoji_counter_map:
            raise EmojiNotFounded()

        # Check if the user already posted this emoji
        if userId in self.emoji_counter_map[emoji]:
            raise UserAlreadyPostEmoji(userId)

        # Remove conflicting emoji if needed
        if emoji == "like" and userId in self.emoji_counter_map["dislike"]:
            self.emoji_counter_map["dislike"].remove(userId)
        elif emoji == "dislike" and userId in self.emoji_counter_map["like"]:
            self.emoji_counter_map["like"].remove(userId)

        # Add the userId to the emoji set
        self.emoji_counter_map[emoji].add(userId)

    def remove_emoji(self, emoji, userId):
        """
        Remove an emoji from the Comment for a specific user.
        """
        if emoji in self.emoji_counter_map and userId in self.emoji_counter_map[emoji]:
            self.emoji_counter_map[emoji].remove(userId)
        else:
            raise EmojiNotFounded

    def edit_text(self, new_text):
        self.text = new_text

    def get_score(self):
        """
        Calculate and return the score of the Comment.
        The score is the count of 'like' emojis minus the count of 'dislike' emojis.
        """
        return len(self.emoji_counter_map["like"]) - len(self.emoji_counter_map["dislike"])

