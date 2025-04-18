import datetime

from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime
from ..Base import Base


class NotificationModel(Base):
    __tablename__ = 'notifications'

    # Primary Key
    notification_id = Column(String, primary_key=True, nullable=False)

    # User Relationships
    receiver_user_id = Column(String, ForeignKey('users.user_id'), nullable=False)
    sender_user_id = Column(String, ForeignKey('users.user_id'), nullable=False)

    # Notification Details
    message = Column(String, nullable=False)
    time = Column(DateTime, default=datetime.datetime.now, nullable=False)
    link = Column(String, nullable=False)
    IsApproved = Column(Boolean, nullable=False, default=False)

    # Notification Types (Flags)
    AppointSystemManager = Column(Boolean, nullable=False, default=False)
    AppointCourseManager = Column(Boolean, nullable=False, default=False)
    CommentToFollowing = Column(Boolean, nullable=False, default=False)
    CommentToComment = Column(Boolean, nullable=False, default=False)
    ReactToComment = Column(Boolean, nullable=False, default=False)
    RemoveCourseManager = Column(Boolean, nullable=False, default=False)

    def to_business_model(self):
        from Backend.BusinessLayer.Notifications.Notification import Notification

        timestamp_str = None
        if isinstance(self.time, str):
            timestamp_str = self.time
        elif self.time:
            try:
                timestamp_str = self.time.strftime('%Y-%m-%d %H:%M:%S')
            except AttributeError:
                timestamp_str = str(self.time)

        return Notification(
            notification_id=self.notification_id,
            receiver_user_id=self.receiver_user_id,
            sender_user_id=self.sender_user_id,
            message=self.message,
            timestamp=timestamp_str,
            link = self.link,
            IsApproved = self.IsApproved,
            AppointSystemManager=self.AppointSystemManager,
            AppointCourseManager=self.AppointCourseManager,
            CommentToFollowing=self.CommentToFollowing,
            CommentToComment=self.CommentToComment,
            ReactToComment=self.ReactToComment,
            RemoveCourseManager=self.RemoveCourseManager
        )

    @classmethod
    def from_business_model(cls, notification):
        return cls(
            notification_id=notification.notification_id,
            receiver_user_id=notification.receiver_user_id,
            sender_user_id=notification.sender_user_id,
            message=notification.message,
            time=notification.timestamp,
            link = notification.link,
            IsApproved = notification.IsApproved,
            AppointSystemManager=notification.AppointSystemManager,
            AppointCourseManager=notification.AppointCourseManager,
            CommentToFollowing=notification.CommentToFollowing,
            CommentToComment=notification.CommentToComment,
            ReactToComment=notification.ReactToComment,
            RemoveCourseManager=notification.RemoveCourseManager
        )
