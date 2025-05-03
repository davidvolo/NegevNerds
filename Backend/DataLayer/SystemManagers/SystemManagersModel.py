from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.orm import relationship

from ..Base import Base

class SystemManagersModel(Base):
    __tablename__ = 'system_managers'

    # Primary key
    user_id = Column(String, ForeignKey('users.user_id'), primary_key=True, nullable=False)

    # Relationship to UserModel
    manager = relationship('UserModel', back_populates='system_manager')
