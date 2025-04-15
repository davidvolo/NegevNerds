from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from Backend.DataLayer.ExamsDoneUser.ExamsDoneUserModel import ExamsDoneUserModel
from ..Base import Base

class ExamsDoneUserRepository:
    def __init__(self, engine):
        self.engine = engine
        self.Session = sessionmaker(bind=engine)
        Base.metadata.create_all(engine)

    def mark_exam_done(self, exam_id, course_id, user_id):
        session = self.Session()
        try:
            record = ExamsDoneUserModel(
                exam_id=exam_id,
                course_id=course_id,
                user_id=user_id
            )
            session.add(record)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def is_exam_done_by_user(self, exam_id, course_id, user_id):
        session = self.Session()
        try:
            return session.query(ExamsDoneUserModel).filter_by(
                exam_id=exam_id,
                course_id=course_id,
                user_id=user_id
            ).first() is not None
        finally:
            session.close()

    def get_done_exam_ids_for_user(self, user_id):
        session = self.Session()
        try:
            records = session.query(ExamsDoneUserModel).filter_by(user_id=user_id).all()
            return [(r.exam_id, r.course_id) for r in records]
        finally:
            session.close()
    
    def unmark_exam_done(self, exam_id, course_id, user_id):
        session = self.Session()
        try:
            record = session.query(ExamsDoneUserModel).filter_by(
                exam_id=exam_id,
                course_id=course_id,
                user_id=user_id
            ).first()
            if record:
                session.delete(record)
                session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
