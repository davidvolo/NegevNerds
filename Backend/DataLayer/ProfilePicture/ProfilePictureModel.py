from sqlalchemy import Column, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship

from ..Base import Base

class ProfilePictureModel(Base):
    __tablename__ = 'profile_pictures'

    # Primary Key - same as user ID (one-to-one relationship)
    user_id = Column(String, ForeignKey('users.user_id'), primary_key=True, nullable=False)

    # Notification preferences
    link = Column(String, nullable=False, default=True)
   
    # Relationship to UserModel
    user_profile_pic = relationship('UserModel', back_populates='profile_pictures')
