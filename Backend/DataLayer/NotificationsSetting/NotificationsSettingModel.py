from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from ..Base import Base

class NotificationsSettingModel(Base):
    __tablename__ = 'notification_settings'

    # Primary Key - same as user ID (one-to-one relationship)
    user_id = Column(String, ForeignKey('users.user_id'), primary_key=True, nullable=False)

    # Notification preferences
    AppointSystemManager = Column(Boolean, nullable=False, default=True)
    AppointCourseManager = Column(Boolean, nullable=False, default=True)
    CommentToFollowing = Column(Boolean, nullable=False, default=True)
    CommentToComment = Column(Boolean, nullable=False, default=True)
    ReactToComment = Column(Boolean, nullable=False, default=True)
    RemoveCourseManager = Column(Boolean, nullable=False, default=True)

    # Relationship to UserModel
    notification_setting = relationship('UserModel', back_populates='user_notifications')
