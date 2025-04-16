from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship
from ..Base import Base

class ExamsDoneUserModel(Base):
    __tablename__ = 'exams_done_users'

    exam_id = Column(String, primary_key=True)
    course_id = Column(String, primary_key=True)
    user_id = Column(String, ForeignKey('users.user_id'), primary_key=True)

    # Optional: Relationships if needed
    # exam = relationship('ExamModel', back_populates='exams_done')  # if you add this on the ExamModel side
    # user = relationship('UserModel', back_populates='exams_done')  # if you add this on the UserModel side

    def to_dict(self):
        return {
            "exam_id": self.exam_id,
            "course_id": self.course_id,
            "user_id": self.user_id
        }
