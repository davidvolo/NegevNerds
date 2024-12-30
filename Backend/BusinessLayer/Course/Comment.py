import uuid
from datetime import datetime

from Backend.BusinessLayer.Course.Reaction import Reaction
from Backend.BusinessLayer.Util.Exceptions import ReactionNotFound
from Backend.DataLayer.Comment.CommentRepository import CommentRepository
from Backend.DataLayer.DTOs.CommentDTO import CommentDTO
from Backend.DataLayer.Reaction.ReactionRepository import ReactionRepository


class Comment:
    def __init__(self, comment_id, writer_name, date=None, prev_id=None, comment_text="", reactions=None):
        """
        Initialize a Comment instance.
        """
        self.comment_id = comment_id
        self.writer_name = writer_name
        self.date = date if date else datetime.now()  # Default to current date if not provided
        self.prev_id = prev_id
        self.comment_text = comment_text
        self.reactions = reactions if reactions is not None else [] #reactions_list

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
        comment_repo.add_comment(comment, question_id)

        return comment

    def to_dto(self):
        """
        Converts the Comment instance to a CommentDTO.
        :return: CommentDTO instance.
        """
        reaction_dtos = [reaction.to_dto() for reaction in self.reactions]
        return CommentDTO(
            comment_id=self.comment_id,
            writer_name=self.writer_name,
            date=self.date,
            prev_id=self.prev_id,
            comment_text=self.comment_text,
            reactions=reaction_dtos
        )

    def generate_reaction_id(self):
        return "reaction" + str(uuid.uuid4())

    def add_reaction(self, user_id, emoji):
        """
        Add a reaction to the Comment.
        """

        # Check if the user already reacted
        for reaction in self.reactions:
            if reaction.user_id == user_id:
                if reaction.emoji != emoji:
                    self.remove_reaction(reaction.reaction_id)
                else:
                    return
        reaction = Reaction.create(self.generate_reaction_id(), user_id, emoji, self.comment_id)
        self.reactions.append(reaction)

    def remove_reaction(self, reaction_id):
        """
        Remove a reaction from the Comment for a specific user.
        """
        for reaction in self.reactions:
            if reaction.reaction_id == reaction_id:
                reaction_repo = ReactionRepository()
                reaction_repo.remove_reaction(reaction.reaction_id)
                self.reactions.remove(reaction)
                return

    def edit_text(self, new_text):
        self.text = new_text

    def get_score(self):
        """
        Calculate and return the score of the Comment.
        The score is the count of 'like' emojis minus the count of 'dislike' emojis.
        """
        return len(self.emoji_counter_map["like"]) - len(self.emoji_counter_map["dislike"])

