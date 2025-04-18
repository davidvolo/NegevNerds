from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

# from Backend.DataLayer.UserData.UserModel import UserModel
# from Backend.DataLayer.Questions.QuestionModel import QuestionModel

from ..Base import Base


class DiscussionFollowModel(Base):
    __tablename__ = 'discussion_follow'

    user_id = Column(String, ForeignKey('users.user_id'), primary_key=True, nullable=False)
    question_id = Column(String, ForeignKey('questions.question_id'), primary_key=True, nullable=False)

    user = relationship('UserModel', back_populates='follows')
    question = relationship('QuestionModel', back_populates='followers')

    def __repr__(self):
        return f"<DiscussionFollow(user_id='{self.user_id}', question_id='{self.question_id}')>"
