
from sqlalchemy import Column, Integer, String, Boolean, PickleType, ForeignKey
from sqlalchemy.orm import relationship
from Backend.DataLayer.ReactionData.ReactionModel import ReactionModel
from ..Base import Base


class CommentModel(Base):

    __tablename__ = 'comments'

    # Primary key
    comment_id = Column(String, primary_key=True)

    writer_name = Column(String, nullable=False)
    writer_id = Column(String, nullable=False)
    date = Column(String, nullable=False)
    prev_id = Column(String, nullable=False)
    text = Column(String, nullable=False)
    deleted = Column(Boolean, nullable=False)
    edited = Column(Boolean, nullable=False)
    link_to_media = Column(String, nullable=True)
    question_id = Column(String, ForeignKey('questions.question_id'), nullable=False)

    question = relationship('QuestionModel',
                            back_populates='comments')

    reactions = relationship('ReactionModel',
                            back_populates='comment',
                            cascade='all, delete')

    def to_business_model(self):
        from Backend.BusinessLayer.Course.Comment import Comment
        business_reactions = [reaction.to_business_model() for reaction in self.reactions]
        comment = Comment(
            comment_id=self.comment_id,
            writer_name=self.writer_name,
            writer_id = self.writer_id,
            date=self.date,
            prev_id=self.prev_id,
            comment_text=self.text,
            deleted=self.deleted,
            edited=self.edited,
            link_to_media=self.link_to_media,
            reactions=business_reactions
        )
        return comment

    @classmethod
    def from_business_model(cls, comment):

        return cls(
            comment_id=comment.comment_id,
            writer_name=comment.writer_name,
            writer_id = comment.writer_id,
            date=comment.date,
            prev_id=comment.prev_id,
            text=comment.text,
            deleted=comment.deleted,
            edited=comment.edited,
            link_to_media=comment.link_to_media
        )
