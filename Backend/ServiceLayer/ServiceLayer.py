import json
from Backend.BusinessLayer import NegevNerds


class ServiceLayer:
    def __init__(self, negev_nerds: NegevNerds):
        self.negev_nerds = negev_nerds

    def register(self, email, password, first_name, last_name):
        """Handle user registration and return JSON."""
        try:
            result = self.negev_nerds.register(email, password, first_name, last_name)

            if "Error" in result:
                return json.dumps({
                    "status": "error",
                    "message": result
                })
            return json.dumps({
                "status": "success",
                "message": result
            })
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": str(e)
            })
    
    def register_authentication_part(self, email, auth_code):
        """Handle user authentication code part in the registration and return JSON."""
        try:
            result = self.negev_nerds.register_authentication_part(email, auth_code)

            if "Error" in result:
                return json.dumps({
                    "status": "error",
                    "message": result
                })
            return json.dumps({
                "status": "success",
                "message": result
            })
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": str(e)
            })
        
    def register_termOfUse_part(self, email, password, first_name, last_name, accept):
        """Handle user acception of the term of use in the registration and return JSON."""
        try:
            result = self.negev_nerds.register_termOfUse_part(email, password, first_name, last_name, accept)

            if "Error" in result:
                return json.dumps({
                    "status": "error",
                    "message": result
                })
            return json.dumps({
                "status": "success",
                "message": result
            })
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": str(e)
            })

    def login(self, email, password):
        """Handle user login and return JSON."""
        try:
            result = self.negev_nerds.login(email, password)

            if "Error" in result:
                return json.dumps({
                    "status": "error",
                    "message": result
                })
            return json.dumps({
                "status": "success",
                "message": result
            })
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": str(e)
            })

    def logout(self, email):
        """Handle user logout and return JSON."""
        try:
            result = self.negev_nerds.logout(email)

            if "Error" in result:
                return json.dumps({
                    "status": "error",
                    "message": result
                })
            return json.dumps({
                "status": "success",
                "message": result
            })
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": str(e)
            })

    def register_to_course(self, course_id, user_id):
        """Handle user registration to a course and return JSON response."""
        try:
            result = self.negev_nerds.registerToCourse(course_id, user_id)

            # If result contains "Error", return it in the JSON response
            if "Error" in result:
                return json.dumps({
                    "status": "error",
                    "message": result
                })

            # Return the success message in JSON format
            return json.dumps({
                "status": "success",
                "message": result
            })
        except Exception as e:
            # In case of exception, return the error message
            return json.dumps({
                "status": "error",
                "message": str(e)
            })

    def remove_student_from_course(self, course_id, user_id):
        """Handle removing a user from a course and return JSON response."""
        try:
            result = self.negev_nerds.removeStudentFromCourse(course_id, user_id)

            # If result contains "Error", return it in the JSON response
            if "Error" in result:
                return json.dumps({
                    "status": "error",
                    "message": result
                })

            # Return the success message in JSON format
            return json.dumps({
                "status": "success",
                "message": result
            })
        except Exception as e:
            # In case of exception, return the error message
            return json.dumps({
                "status": "error",
                "message": str(e)
            })

    def open_course(self, user_id, course_id, name, syllabus_content, course_topics):
        """Handle course creation and save syllabus, return JSON response."""
        try:
            result = self.negev_nerds.open_course(user_id, course_id, name, syllabus_content, course_topics)

            if "Error" in result:
                return json.dumps({
                    "status": "error",
                    "message": result
                })

            return json.dumps({
                "status": "success",
                "message": result
            })

        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": str(e)
            })

    def remove_course(self, course_id, user_id):
        """Handle course removal and return JSON response."""
        try:
            result = self.negev_nerds.remove_course(course_id, user_id)

            if "Error" in result:
                return json.dumps({
                    "status": "error",
                    "message": result
                })
            return json.dumps({
                "status": "success",
                "message": result
            })
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": str(e)
            })

    def search_exam_by_specifics(self, course_id, year: int, semester=None, moed=None):
        """Search for exams by course ID and optionally filter by year, semester, and moed. Return JSON."""
        try:
            # Call the business layer method with the provided arguments
            result = self.negev_nerds.search_exam_by_specifics(course_id, year, semester, moed)

            # Check if any exams are found
            if not result:
                return json.dumps({
                    "status": "error",
                    "message": "No exams found for the given criteria."
                })
            return json.dumps({
                "status": "success",
                "data": result
            })
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": str(e)
            })

    def search_all_course_exams(self, course_id):
        """Search for exams by course ID and optionally filter by year, semester, and moed. Return JSON."""
        try:
            # Call the business layer method with the provided arguments
            result = self.negev_nerds.search_all_course_exmas(course_id)

            # Check if any exams are found
            if not result:
                return json.dumps({
                    "status": "error",
                    "message": "No exams found for the given criteria."
                })
            return json.dumps({
                "status": "success",
                "data": result
            })
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": str(e)
            })

    def edit_exam_course_name(self, user_id, course_id, year, semester, moed, new_course_name):
        """Editing exam's course name """
        try:
            # Call the business layer method with the provided arguments
            result = self.negev_nerds.edit_exam_course_name(user_id, course_id, year, semester, moed, new_course_name)

            # Check if any exams are found
            if not result:
                return json.dumps({
                    "status": "error",
                    "message": "Something went wrong"
                })
            return json.dumps({
                "status": "success",
                "data": result
            })
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": str(e)
            })

    def edit_exam_link(self, course_id, year, semester, moed, new_link):
        """Editing exam's link """
        try:
            # Call the business layer method with the provided arguments
            result = self.negev_nerds.edit_exam_link(course_id, year, semester, moed, new_link)

            # Check if any exams are found
            if not result:
                return json.dumps({
                    "status": "error",
                    "message": "Something went wrong."
                })
            return json.dumps({
                "status": "success",
                "data": result
            })
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": str(e)
            })

    def edit_exam_year(self, course_id, year, semester, moed, new_year):
        """Editing exam's year """
        try:
            # Call the business layer method with the provided arguments
            result = self.negev_nerds.edit_exam_year(course_id, year, semester, moed, new_year)

            # Check if any exams are found
            if not result:
                return json.dumps({
                    "status": "error",
                    "message": "Something went wrong."
                })
            return json.dumps({
                "status": "success",
                "data": result
            })
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": str(e)
            })

    def edit_exam_semester(self, course_id, year, semester, moed, new_semester):
        """Editing exam's semester """
        try:
            # Call the business layer method with the provided arguments
            result = self.negev_nerds.edit_exam_semester(course_id, year, semester, moed, new_semester)

            # Check if any exams are found
            if not result:
                return json.dumps({
                    "status": "error",
                    "message": "Something went wrong."
                })
            return json.dumps({
                "status": "success",
                "data": result
            })
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": str(e)
            })

    def edit_exam_moed(self, course_id, year, semester, moed, new_moed):
        """Editing exam's moed """
        try:
            # Call the business layer method with the provided arguments
            result = self.negev_nerds.edit_exam_moed(course_id, year, semester, moed, new_moed)

            # Check if any exams are found
            if not result:
                return json.dumps({
                    "status": "error",
                    "message": "Something went wrong."
                })
            return json.dumps({
                "status": "success",
                "data": result
            })
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": str(e)
            })

    def add_question_with_pdf(self, course_id, year, semester, moed, pdf_file_content, questionDTO):
        """
        Handles adding a question to an exam.
        :return: JSON response indicating success or failure.
        """
        try:
            result = self.negev_nerds.add_question(course_id, year, semester, moed, pdf_file_content, questionDTO)
            return json.dumps({
                "status": "success",
                "message": result
            })
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": str(e)
            })
