import os
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from Backend.DataLayer.Noitifications.NotificationModel import Base
from Backend.DataLayer.Noitifications.NotificationModel import NotificationModel


class NotificationRepository:
    """Repository for handling notification database operations"""

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

    def add_notification(self, notification):
        session = self.Session()

        try:
            notification_model = NotificationModel(
                notification_id=notification.notification_id,
                sender_user_id=notification.sender_user_id,
                receiver_user_id=notification.receiver_user_id,
                message=notification.message,
                time=notification.timestamp,
                link = notification.link,
                IsApproved=notification.isApproved,
                AppointSystemManager=notification.appoint_system_manager,
                AppointCourseManager=notification.appoint_course_manager,
                CommentToFollowing=notification.comment_to_following,
                CommentToComment=notification.comment_to_comment,
                ReactToComment=notification.react_to_comment,
                RemoveCourseManager=notification.remove_course_manager
            )
            session.add(notification_model)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_notifications_by_user_id(self, user_id):
        session = self.Session()
        notifications = []
        try:
            notification_models = (
                session.query(NotificationModel)
                .filter_by(receiver_user_id=user_id)
                .order_by(desc(NotificationModel.timestamp))
                .all()
            )
            for notification in notification_models:
                notifications.append(notification.to_business_model())
            return notifications
        finally:
            session.close()

    def get_last_notifications_by_user_id(self, user_id: str, number_of_notifications: int):
        session = self.Session()
        notifications = []
        try:
            notification_models = (
                session.query(NotificationModel)
                .filter_by(receiver_user_id=user_id)
                .order_by(desc(NotificationModel.timestamp))
                .limit(number_of_notifications)
                .all()
            )
            for notification in notification_models:
                notifications.append(notification.to_business_model())
            return notifications
        finally:
            session.close()

    def delete_notification(self, notification_id):
        session = self.Session()
        try:
            notification_model = session.query(NotificationModel).filter_by(notification_id=notification_id).first()
            if not notification_model:
                raise ValueError(f"No notification found with ID {notification_id}")
            session.delete(notification_model)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def delete_notifications_by_user(self, user_id):
        session = self.Session()
        try:
            notification_models = session.query(NotificationModel).filter_by(receiver_user_id=user_id).all()
            if not notification_models:
                raise ValueError(f"No notifications found for user {user_id}")
            for notification in notification_models:
                session.delete(notification)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_unapproved_notifications(self, user_id):
        session = self.Session()
        try:
            return (
                session.query(NotificationModel)
                .filter_by(receiver_user_id=user_id, IsApproved=False)
                .order_by(NotificationModel.time.desc())  # 👈 Order by newest first
                .all()
            )
        finally:
            session.close()
    
    def mark_as_seen(self, notification_id):
        session = self.Session()
        try:
            notification_model = session.query(NotificationModel).filter_by(notification_id=notification_id).first()
            if not notification_model:
                raise ValueError(f"No notification found with ID {notification_id}")

            notification_model.IsApproved = True  # Update the status
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
    
    def get_notification_by_id(self, notification_id):
        session = self.Session()
        try:
            return session.query(NotificationModel).filter_by(notification_id=notification_id).first()
        except Exception as e:
            raise e
        finally:
            session.close()


