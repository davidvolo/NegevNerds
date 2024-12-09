import json
from BusinessLayer import NegevNerds

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

    def search_exam_by_specifics(self, course_id, year :int, semester=None, moed=None):
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
        
    def search_all_course_exmas(self, course_id):
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
        
    def edit_exam_course_name(self, course_id, year, semester, moed, new_course_name):
        """Editing exam's course name """
        try:
            # Call the business layer method with the provided arguments
            result = self.negev_nerds.edit_exam_course_name( course_id, year, semester, moed, new_course_name)
            
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
            result = self.negev_nerds.edit_exam_link( course_id, year, semester, moed, new_link)
            
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
            result = self.negev_nerds.edit_exam_year( course_id, year, semester, moed, new_year)
            
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
            result = self.negev_nerds.edit_exam_semester( course_id, year, semester, moed, new_semester)
            
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
            result = self.negev_nerds.edit_exam_moed( course_id, year, semester, moed, new_moed)
            
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

    def add_question(self, course_id, year, semester, moed, question):
        """
        Handles adding a question to an exam.
        :return: JSON response indicating success or failure.
        """
        try:
            result = self.negev_nerds.add_question(course_id, year, semester, moed, question)
            return json.dumps({
                "status": "success",
                "message": result
            })
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": str(e)
            })
