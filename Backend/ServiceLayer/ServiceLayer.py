import json
from Backend.BusinessLayer import NegevNerds


import threading

from Backend.BusinessLayer.Course import enums
from Backend.DataLayer.QuestionDTO import QuestionDTO


class ServiceLayer:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, negev_nerds: NegevNerds):
        if cls._instance is None:
            with cls._lock:  # Ensure thread-safe instance creation
                if cls._instance is None:  # Double-checked locking
                    cls._instance = super().__new__(cls)
                    # Initialize attributes in __new__
                    cls._instance.negev_nerds = negev_nerds
                    cls._instance._initialized = True
        return cls._instance

    def __init__(self, negev_nerds: NegevNerds = None):
        # Prevent reinitialization
        if not hasattr(self, '_initialized'):
            if negev_nerds is None:
                negev_nerds = NegevNerds.NegevNerds("../")
            self.negev_nerds = negev_nerds
            self._initialized = True

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

    def registerWithoutAuth(self, email, password, first_name, last_name):
        """Handle user registration and return JSON."""
        user_id = None
        try:
            user_id, result = self.negev_nerds.registerWithoutAuth(email, password, first_name, last_name)

            if "Error" in result:
                return json.dumps({
                    "status": "error",
                    "message": result
                })
            return user_id, json.dumps({
                "status": "success",
                "message": result
            })
        except Exception as e:
            return user_id , json.dumps({
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
        
    def register_termOfUse_part(self, email, password, first_name, last_name):
        """Handle user acception of the term of use in the registration and return JSON."""
        try:
            userid ,result = self.negev_nerds.register_termOfUse_part(email, password, first_name, last_name)

            if "Error" in result:
                return json.dumps({
                    "status": "error",
                    "message": result ,
                    "user_id": userid
            
                })
            return json.dumps({
                "status": "success",
                "message": result,
                "user_id": userid

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

    def open_course(self, user_id, course_id, course_name, syllabus_content_pdf):
        """Handle course creation and save syllabus, return JSON response."""
        try:
            result = self.negev_nerds.open_course(user_id, course_id, course_name, syllabus_content_pdf )

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
            result = self.negev_nerds.add_question_with_pdf(course_id, year, semester, moed, pdf_file_content, questionDTO)
            return json.dumps({
                "status": "success",
                "message": result
            })
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": str(e)
            })





    def get_user_courses(self, user_id):
        """Editing exam's year """
        try:
            # Call the business layer method with the provided arguments
            result = self.negev_nerds.get_user_courses(user_id)

            return json.dumps({
                "status": "success",
                "data": result
            })
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": str(e)
            })

    def get_course_topics(self, course_id):
        """Editing exam's year """
        try:
            # Call the business layer method with the provided arguments
            result = self.negev_nerds.get_course_topics(course_id)

            print("res", result)
            return json.dumps({
                "status": "success",
                "data": list(result)
            }, ensure_ascii= False)
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": str(e)
            })

    def get_all_courses(self):
        """Fetches all courses and returns them in JSON format."""
        try:
            # Call the business layer to get the list of courses
            courses = self.negev_nerds.get_all_courses()

            # Return the result as a dictionary, serialized to JSON
            return json.dumps({
                "status": "success",
                "data": [course.to_dict() for course in courses]
            })
        except Exception as e:
            # Return an error response as a JSON string
            return json.dumps({
                "status": "error",
                "message": str(e)
            })



    def initialize_system(self, file_path="init.json"):
        """
        Initialize the system with predefined data from a JSON file.
        """
        print("Initializing the system with predefined data...")

        # Load initialization data from the JSON file
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                init_data = json.load(file)

            # Extract users and courses
            users = init_data.get("users", [])
            courses = init_data.get("courses", [])

            usersId = []

            # Register users
            for i in range(len(users)):
                curr_user_id, _ = self.registerWithoutAuth(users[i]['email'], users[i]['password'], users[i]['first_name'], users[i]['last_name'])
                usersId.append(curr_user_id)
                print(f"Registering user {users[i]['email']}: {curr_user_id}")

            # Create courses and enroll users
            for i in range(len(courses)):
                # Create the course
                course = courses[i]
                response = self.open_course(usersId[i], course['courseId'], course['name'], course['syllabus_content_pdf'])
                print(f"Creating course {course['name']}: {response}")

            res = self.register_to_course(courses[1]["courseId"], usersId[0])
            print(f"register {users[0]['first_name']} to course  {courses[1]['name']}: {res}")

            res = self.register_to_course(courses[0]["courseId"], usersId[1])
            print(f"register {users[1]['first_name']} to course  {courses[0]['name']}: {res}")

            res = self.register_to_course(courses[0]["courseId"], usersId[3])
            print(f"register {users[3]['first_name']} to course  {courses[0]['name']}: {res}")

            res = self.register_to_course(courses[1]["courseId"], usersId[2])
            print(f"register {users[2]['first_name']} to course  {courses[1]['name']}: {res}")

            res = self.register_to_course(courses[1]["courseId"], usersId[3])
            print(f"register {users[3]['first_name']} to course  {courses[1]['name']}: {res}")

            res = self.add_question_with_pdf(courses[0]["courseId"], 2023, enums.Semester.SPRING, enums.Moed.B, "ex2.pdf",
                                       QuestionDTO("question1", 2023, enums.Semester.SPRING, enums.Moed.B,
                                                   3, ["binaryTree, Math"], False, "ex2.pdf"))
            print(" add question -", res)
            print("System initialization complete.")
        except FileNotFoundError:
            print(f"Error: Initialization file {file_path} not found.")
        except json.JSONDecodeError:
            print("Error: Failed to parse the initialization file.")
        except Exception as e:
            print(f"An unexpected error occurred during initialization: {e}")



