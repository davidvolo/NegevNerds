import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from Backend.DataLayer.Base import Base
from Backend.DataLayer.NotificationsSetting.NotificationsSettingModel import NotificationsSettingModel
from Backend.DataLayer.UserData.UserModel import UserModel  # Ensure relationships load

class NotificationsSettingRepository:
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
        print("Tables SQLAlchemy knows:", Base.metadata.tables.keys())
        Base.metadata.create_all(self.engine)

        self.Session = sessionmaker(bind=self.engine)

    def get_settings_by_user_id(self, user_id):
        session = self.Session()
        try:
            settings = session.query(NotificationsSettingModel).filter_by(user_id=user_id).first()

            if not settings:
                # Create default settings with all True
                settings = NotificationsSettingModel(
                    user_id=user_id,
                    AppointSystemManager=True,
                    AppointCourseManager=True,
                    CommentToFollowing=True,
                    CommentToComment=True,
                    ReactToComment=True,
                    RemoveCourseManager=True
                )
                session.add(settings)
                session.commit()

            return {
                "AppointSystemManager": settings.AppointSystemManager,
                "AppointCourseManager": settings.AppointCourseManager,
                "CommentToFollowing": settings.CommentToFollowing,
                "CommentToComment": settings.CommentToComment,
                "ReactToComment": settings.ReactToComment,
                "RemoveCourseManager": settings.RemoveCourseManager
            }

        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()


    def create_default_settings_for_user(self, user_id):
        session = self.Session()
        try:
            settings = NotificationsSettingModel(user_id=user_id)
            session.add(settings)
            session.commit()
            return settings
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def update_settings(self, user_id, settings_dict):
        session = self.Session()
        try:
            # Check if settings exist
            settings = session.query(NotificationsSettingModel).filter_by(user_id=user_id).first()
            if not settings:
                # If not, create new
                settings = NotificationsSettingModel(user_id=user_id, **settings_dict)
                session.add(settings)
            else:
                # If exists, update values
                for key, value in settings_dict.items():
                    setattr(settings, key, value)

            session.commit()
            return True
        except Exception as e:
            session.rollback()
            print(f"Error updating notification settings: {e}")
            return False
        finally:
            session.close()


    def delete_settings(self, user_id):
        session = self.Session()
        try:
            settings = session.query(NotificationsSettingModel).filter_by(user_id=user_id).first()
            if settings:
                session.delete(settings)
                session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def save_or_update_settings(self, user_id, settings):
        session = self.Session()
        try:
            existing = session.query(NotificationsSettingModel).filter_by(user_id=user_id).first()
            if existing:
                for key, value in settings.items():
                    setattr(existing, key, value)
            else:
                new_settings = NotificationsSettingModel(user_id=user_id, **settings)
                session.add(new_settings)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def is_notification_enabled(self, user_id, notification_type):
        session = self.Session()
        try:
            settings = session.query(NotificationsSettingModel).filter_by(user_id=user_id).first()

            if not settings:
                # 🟡 If settings don't exist yet, assume default is True
                return True

            # 🟢 Check if the column exists on the model
            if not hasattr(settings, notification_type):
                raise ValueError(f"Invalid notification type: {notification_type}")

            return getattr(settings, notification_type)

        finally:
            session.close()

