from BusinessLayer.Util.Exceptions import *


class User:
    def __init__(self, id, email, password, first_name, last_name, loggedIn = False, courses = []):
        self.id = id
        self.email = email
        self.password = password
        self.first_name = first_name
        self.last_name = last_name
        self.loggedIn = loggedIn
        self.courses = courses
    
    
    def login(self):
        self.loggedIn = True
    
    def logout(self):
        self.loggedIn = False
        
    def registerToCourse(self, course_id):
        if course_id not in self.courses:
            self.courses.append(course_id)
        else:
           raise UserAlreadyRegisterToCourse()
       
    def removeCourse(self, course_id):
        """Removes the user from a course."""
        if course_id in self.courses:
            self.courses.remove(course_id)
        else:
            raise UserIsNotRegisterToCourse()
        
    def editProfile(self, email=None, password=None, first_name=None, last_name=None):
        """Edit the user's profile details."""
        if email:
            self.email = email
        if password:
            self.password = password
        if first_name:
            self.first_name = first_name
        if last_name:
            self.last_name = last_name
        #print(f"Profile updated: {self.first_name} {self.last_name}, {self.email}")
