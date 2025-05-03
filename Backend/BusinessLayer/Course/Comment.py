import threading
import uuid
from datetime import datetime

from Backend.BusinessLayer.Course.Reaction import Reaction
from Backend.BusinessLayer.Util.Exceptions import ReactionNotFound
from Backend.DataLayer.CommentData.CommentRepository import CommentRepository
from Backend.DataLayer.DTOs.CommentDTO import CommentDTO
from Backend.DataLayer.ReactionData.ReactionRepository import ReactionRepository


class Comment:
    def __init__(self, comment_id, writer_name,writer_id, link_to_media, date=None, prev_id=None, comment_text="",
                 deleted=None, edited=None, reactions=None):
        """
        Initialize a CommentData instance.
        """
        self.comment_id = comment_id
        self.writer_name = writer_name
        self.writer_id = writer_id
        self.date = date if date else datetime.now()  # Default to current date if not provided
        self.prev_id = prev_id
        self.comment_text = comment_text
        self.reactions = reactions if reactions is not None else [] #reactions_list
        self.deleted = deleted
        self.edited = edited
        self.link_to_media = link_to_media
        self.reactions_lock = threading.Lock()

    @classmethod
    def create(cls, comment_id, writer_name,writer_id, date, prev_id, comment_text, deleted, edited, link_to_media, question_id):
        """
        Class method to create a new comment and save to database
        Returns:
            Comment: Newly created comment instance
        """

        comment = cls(
            comment_id=comment_id,
            writer_name=writer_name,
            writer_id = writer_id,
            date=date,
            prev_id=prev_id,
            comment_text=comment_text,
            deleted=deleted,
            edited=edited,
            link_to_media=link_to_media
        )
        comment_repo = CommentRepository()
        comment_repo.add_comment(comment, question_id)

        return comment

    def to_dto(self):
        """
        Converts the CommentData instance to a CommentDTO.
        :return: CommentDTO instance.
        """
        reaction_dtos = [reaction.to_dto() for reaction in self.reactions]
        return CommentDTO(
            comment_id=self.comment_id,
            writer_name=self.writer_name,
            date=self.date,
            prev_id=self.prev_id,
            comment_text=self.comment_text,
            deleted=self.deleted,
            edited=self.edited,
            reactions=reaction_dtos,
            link_to_media=self.link_to_media
        )

    def get_link_to_media(self):
        return self.link_to_media

    def generate_reaction_id(self):
        return "reaction" + str(uuid.uuid4())

    def delete_comment(self):
        self.deleted = True
        reactions_repo = ReactionRepository()
        reactions_repo.delete_reactions_by_comment_id(self.comment_id)      
        comment_repo = CommentRepository()
        comment_repo.update_deleted_comment(self)

    def edit_comment_text(self, new_text):
        if self.comment_text != new_text:
            self.comment_text = new_text
            self.edited = True
            comment_repo = CommentRepository()
            comment_repo.edit_comment_text(self)

    def add_reaction(self, user_id, emoji):
        """
        Add a reaction to the CommentData.
        """
        # Check if the user already reacted
        for reaction in self.reactions:
            if reaction.user_id == user_id:
                if reaction.emoji != emoji:
                    self.remove_reaction(reaction.reaction_id)
                else:
                    return
        with self.reactions_lock:
            reaction = Reaction.create(self.generate_reaction_id(), user_id, emoji, self.comment_id)
            if reaction is not None:
                self.reactions.append(reaction)
                return self.writer_id
            else:
                raise Exception("error while creating reaction")

    def remove_reaction(self, reaction_id):
        """
        Remove a reaction from the CommentData for a specific user.
        """
        with self.reactions_lock:
            for reaction in self.reactions:
                if reaction.reaction_id == reaction_id:
                    reaction_repo = ReactionRepository()
                    reaction_repo.remove_reaction(reaction.reaction_id)
                    self.reactions.remove(reaction)
                    return

    def edit_text(self, new_text):
        self.comment_text = new_text

    # def get_score(self):
    #     """
    #     Calculate and return the score of the CommentData.
    #     The score is the count of 'like' emojis minus the count of 'dislike' emojis.
    #     """
    #     return len(self.emoji_counter_map["like"]) - len(self.emoji_counter_map["dislike"])
    #
