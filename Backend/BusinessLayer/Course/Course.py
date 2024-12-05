from Backend.BusinessLayer.Util.Exceptions import *


class Course:
    def __init__(self, course_id, name, syllabus):
        self.id = course_id

        self.students = []  # List of students for the course
        
        
    def addStudent(self, user_Id):
        """Adds a student to the course."""
        if user_Id not in self.students:
            self.students.append(user_Id)
        else:
            raise UserAlreadyRegisterToCourse()
        
    def removeStudent(self, user_Id):
        """Removes a student from the course."""
        if user_Id in self.students:
            self.students.remove(user_Id)
        else:
            raise UserIsNotRegisterToCourse()