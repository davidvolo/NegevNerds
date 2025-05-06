import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from Backend.DataLayer.Base import Base
from Backend.DataLayer.ProfilePicture.ProfilePictureModel import ProfilePictureModel
from Backend.DataLayer.UserData.UserModel import UserModel  # Ensure relationships load

class ProfilePictureRepository:
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

    def update_profile_pic(self, user_id, profile_pic_path):
        """
        Updates or creates a profile picture record for the given user.
        """
        session = self.Session()
        try:
            existing = session.query(ProfilePictureModel).filter_by(user_id=user_id).first()
            if existing:
                existing.link = profile_pic_path
            else:
                new_pic = ProfilePictureModel(user_id=user_id, link=profile_pic_path)
                session.add(new_pic)

            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise Exception(f"Error updating profile picture for user {user_id}: {e}")
        finally:
            session.close()
    
    def get_path_by_user_id(self, user_id):
        """
        Returns the path to the user's profile picture, if exists.

        :param user_id: ID of the user
        :return: Path to profile picture (str) or None
        """
        session = self.Session()
        try:
            record = session.query(ProfilePictureModel).filter_by(user_id=user_id).first()
            return record.link if record else None
        except Exception as e:
            raise Exception(f"Error in get_path_by_user_id: {str(e)}")
        finally:
            session.close()
    
    def delete_pic(self, user_id):
        """
        Deletes the profile picture file and its DB record for the given user_id, if it exists.

        :param user_id: ID of the user
        :return: True if deleted, False if no picture found
        """
        session = self.Session()
        try:
            record = session.query(ProfilePictureModel).filter_by(user_id=user_id).first()
            if not record:
                return False  # No DB entry

            session.delete(record)  # Delete DB row
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise Exception(f"Error deleting profile picture for user {user_id}: {e}")
        finally:
            session.close()

