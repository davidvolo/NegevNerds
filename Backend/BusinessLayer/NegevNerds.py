import json

from Backend.BusinessLayer.Util.Exceptions import *

class NegevNerds:
    def __init__(self, userController, courseController):
        self.userController = userController
        self.courseController = courseController
        
    def register(self, email, password, first_name, last_name):
        """Register a new user."""
        try:
            success = self.userController.register(email, password, first_name, last_name)

            if success:
                return "User registered successfully."
        except Exception as e:
            return f"Error: {e}"

    def login(self, email, password):
        """Log the user in."""
        try:
            result = self.userController.login(email, password)
            return result  # Return the result from the controller
        except Exception as e:
            return f"Error: {e}"

    def logout(self, email):
        """Log the user out."""
        try:
            result = self.userController.logout(email)
            return result  # Return the result from the controller
        except Exception as e:
            return f"Error: {e}"
        
    def editProfile(self, email, **kwargs):
        """Edit the user's profile."""
        try:
            result = self.userController.editUserProfile(email, **kwargs)
            return result
        except Exception as e:
            return f"Error: {e}"
        
    def registerToCourse(self, courseId, userId):
        """Add the user to course and add the course to user."""
        try:
            # Register the user to the course using CourseController
            self.courseController.registerToCourse(courseId, userId)
            # Register the course to the user using UserController
            self.userController.registerToCourse(courseId,userId)
            return "User successfully registered to the course."
        except Exception as e:
            return f"Error: {e}"
        
    def removeStudentFromCourse(self, courseId, userId):
        """Remove the user from the course and remove the course from user."""
        try:
            # Remove the user from the course using CourseController
            self.courseController.removeStudentFromCourse(courseId, userId)
            # Remove the course from the user using UserController
            user = self.userController.users.get(userId)
            if user:
                user.removeCourse(courseId)
            else:
                raise UserDoesnotExistsError()
            return "User successfully removed from the course."
        except Exception as e:
            return f"Error: {e}"