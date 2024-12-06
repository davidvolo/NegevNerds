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
        

    def search_exam_by_specifics(self, course_id, year : int, semester=None, moed=None):
        """Search for exams by course ID and optionally filter by year, semester, and moed."""
        try:
            # Fetch all exams for the course from courseController
            exams = self.courseController.search_exam_by_specifics(course_id,year,semester,moed)
            return exams
        except Exception as e:
            raise Exception(f"Failed to search exams: {e}")
        
    def search_all_course_exmas(self, course_id):
        """Search for all the exams in the system for specific course"""
        try:
            # Fetch all exams for the course from courseController
            exams = self.courseController.search_all_course_exmas(course_id)
            return exams
        except Exception as e:
            raise Exception(f"Failed to search exams: {e}")
        
    def edit_exam_course_name(self, course_id, year, semester, moed, new_course_name):
        """Editing exam's course name """
        try:
            self.courseController.edit_exam_course_name(course_id, year, semester, moed, new_course_name)
            return "The exams' course name was updated successfully."
        except Exception as e:
            raise Exception(f"Failed to edit exam's course name {e}")
        
    def edit_exam_link(self, course_id, year, semester, moed, new_link):
        """Editing exam's link """
        try:
            self.courseController.edit_exam_link(course_id, year, semester, moed, new_link)
            return "The exams' link was updated successfully."
        except Exception as e:
            raise Exception(f"Failed to edit exam's link {e}")
    
    def edit_exam_year(self, course_id, year, semester, moed, new_year):
        """Editing exam's year """
        try:
            self.courseController.edit_exam_year(course_id, year, semester, moed, new_year)
            return "The exams' year was updated successfully."
        except Exception as e:
            raise Exception(f"Failed to edit exam's link {e}")
    
    def edit_exam_semester(self, course_id, year, semester, moed, new_semester):
        """Editing exam's semester """
        try:
            self.courseController.edit_exam_semester(course_id, year, semester, moed, new_semester)
            return "The exams' semester was updated successfully."
        except Exception as e:
            raise Exception(f"Failed to edit exam's link {e}")
    
    def edit_exam_moed(self, course_id, year, semester, moed, new_moed):
        """Editing exam's moed """
        try:
            self.courseController.edit_exam_moed(course_id, year, semester, moed, new_moed)
            return "The exams' moed was updated successfully."
        except Exception as e:
            raise Exception(f"Failed to edit exam's link {e}")