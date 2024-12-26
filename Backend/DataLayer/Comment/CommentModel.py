
from sqlalchemy import Column, Integer, String, Boolean, PickleType, ForeignKey
from sqlalchemy.orm import relationship

from ..Base import Base


class CommentModel(Base):

    __tablename__ = 'comments'

    # Primary key
    comment_id = Column(String, primary_key=True)

    writer_name = Column(String, nullable=False)
    date = Column(String, nullable=False)
    prev_id = Column(String, nullable=False)
    text = Column(String, nullable=False)
    question_id = Column(String, ForeignKey('questions.question_id'), nullable=False)

    question = relationship('QuestionModel',
                            back_populates='comments')

    def to_business_model(self):
        from Backend.BusinessLayer.Course.Comment import Comment

        comment = Comment(
            comment_id=self.comment_id,
            writer_name=self.writer_name,
            date=self.date,
            prev_id=self.prev_id,
            comment_text=self.text,
        )
        return comment

    @classmethod
    def from_business_model(cls, comment):

        return cls(
            comment_id=comment.id,
            writer_name=comment.writer_name,
            date=comment.date,
            prev_id=comment.prev_id,
            text=comment.text,
        )
