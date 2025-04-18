import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# from Backend.DataLayer.DiscussionFollow.DiscussionFollowModel import Base, DiscussionFollowModel
from Backend.DataLayer.Base import Base
from Backend.DataLayer.DiscussionFollow.DiscussionFollowModel import DiscussionFollowModel


class DiscussionFollowRepository:

    def __init__(self, db_path=None):
        if db_path is None:
            db_env = os.getenv("APP_ENV", "production")

            if db_env == "test":
                db_path = os.path.join(os.path.dirname(__file__), '../../..', 'test_negevnerds.db')
            else:
                db_path = os.path.join(os.path.dirname(__file__), '../../..', 'NegevNerds.db')

        db_dir = os.path.dirname(db_path)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

        self.engine = create_engine(f'sqlite:///{db_path}')
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)



    def follow(self, user_id, question_id):
        session = self.Session()
        try:
            existing = session.query(DiscussionFollowModel).filter_by(user_id=user_id, question_id=question_id).first()
            if not existing:
                follow_entry = DiscussionFollowModel(user_id=user_id, question_id=question_id)
                session.add(follow_entry)
                session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def unfollow(self, user_id, question_id):
        session = self.Session()
        try:
            entry = session.query(DiscussionFollowModel).filter_by(user_id=user_id, question_id=question_id).first()
            if entry:
                session.delete(entry)
                session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def is_following(self, user_id, question_id):
        session = self.Session()
        try:
            return session.query(DiscussionFollowModel).filter_by(user_id=user_id, question_id=question_id).first() is not None
        except Exception as e:
            raise e
        finally:
            session.close()

    def get_followed_questions_by_user(self, user_id):
        session = self.Session()
        try:
            entries = session.query(DiscussionFollowModel).filter_by(user_id=user_id).all()
            return [entry.question_id for entry in entries]
        except Exception as e:
            raise e
        finally:
            session.close()

    def get_followers_for_question(self, question_id):
        session = self.Session()
        try:
            entries = session.query(DiscussionFollowModel).filter_by(question_id=question_id).all()
            return [entry.user_id for entry in entries]
        except Exception as e:
            raise e
        finally:
            session.close()
