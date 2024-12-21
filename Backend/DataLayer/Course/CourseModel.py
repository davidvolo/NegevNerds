from sqlalchemy import Column, Integer, String, Boolean, PickleType, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


from ..Base import Base


class CourseModel(Base):
    from Backend.DataLayer.UserCourses.UserCoursesModel import UserCoursesModel
    __tablename__ = 'courses'

    # Primary key
    course_id = Column(String(50),  primary_key=True,)
    name = Column(String,nullable=False)

    users = relationship('UserCoursesModel', back_populates='course', cascade='all, delete-orphan')


    def to_business_model(self):
        from Backend.BusinessLayer.Course.Course import Course

        course = Course(
            course_id=self.course_id,
            name=self.name,
        )
        return course

    @classmethod
    def from_business_model(cls, course):

        return cls(
            course_id=course.course_id,
            name=course.name,
        )
