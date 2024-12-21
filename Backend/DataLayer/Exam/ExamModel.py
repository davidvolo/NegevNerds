from sqlalchemy import Column, Integer, String, Boolean, PickleType
from sqlalchemy.ext.declarative import declarative_base

from ..Base import Base


class ExamModel(Base):
    __tablename__ = 'exams'

    # Primary key
    year = Column(Integer, primary_key=True)
    semester = Column(String, primary_key=True)
    moed = Column(String, primary_key=True)

    exam_id = Column(String, unique=True)
    course_name = Column(String, nullable=False)
    link = Column(String, nullable=True)



    def to_business_model(self):
        from Backend.BusinessLayer.Course.Exam import Exam

        exam = Exam(
            exam_id=self.exam_id,
            semester=self.semester,
            moed=self.moed,
            year=self.year,
            link=self.link,
            course_name=self.course_name
        )
        return exam

    @classmethod
    def from_business_model(cls, exam):
        return cls(
            exam_id=exam.exam_id,
            semester=exam.semester,
            moed=exam.moed,
            year=exam.year,
            link=exam.link,
            course_name=exam.course_name
        )
