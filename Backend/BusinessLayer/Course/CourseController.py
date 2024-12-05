from Backend.BusinessLayer.Util.Exceptions import *


class CourseController:
    def __init__(self):
        self.courses = {} #courseId, Course
        
    
    def registerToCourse(self, courseId, userId):
        if (courseId) not in self.courses:
            raise CourseIsNotExist()
        else:
            self.courses[courseId].addStudent(userId)
            
    def removeStudentFromCourse(self, courseId, userId):
        """Removes a student from the course."""
        course = self.courses.get(courseId)
        if course:
            course.removeStudent(userId)
        else:
            raise CourseIsNotExist()
