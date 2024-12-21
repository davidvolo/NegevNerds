
from sqlalchemy import Column, Integer, String, Boolean, PickleType
from sqlalchemy.ext.declarative import declarative_base
from ..Base import Base


class QuestionModel(Base):

    __tablename__ = 'questions'

    # Primary key
    question_id = Column(String, primary_key=True)

    year = Column(Integer, nullable=False)
    semester = Column(String, nullable=False)
    moed = Column(String, nullable=False)
    question_number = Column(Integer, nullable=False)
    is_american = Column(Boolean, nullable=False)
    link_to_question = Column(String, nullable=True)
    link_to_exam = Column(String, nullable=True)



    def to_business_model(self):
        from Backend.BusinessLayer.Course.Question import Question

        question = Question(
            question_id=self.question_id,
            year=self.year,
            is_american=self.is_american,
            link_to_question=self.link_to_question,
            link_to_exam=self.link_to_question,
            semester=self.semester,
            moed=self.moed,
            question_number=self.question_number,
            question_topics=None
        )
        return question

    @classmethod
    def from_business_model(cls, question):

        return cls(
            question_id=question.question_id,
            year=question.year,
            is_american=question.is_american,
            link_to_question=question.link_to_question,
            link_to_exam=question.link_to_question,
            semester=question.semester,
            moed=question.moed,
            question_number=question.question_number,
            question_topics=None
        )