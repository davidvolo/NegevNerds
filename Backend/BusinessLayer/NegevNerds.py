from Backend.BusinessLayer.Course.CourseFacade import CourseFacade
from Backend.BusinessLayer.PDFAnalyzer.FileManager import FileManager
from Backend.BusinessLayer.User.UserFacade import UserFacade
from Backend.BusinessLayer.Util.Exceptions import *
from Backend.BusinessLayer.PDFAnalyzer.PDFAnalyzerFacade import PDFAnalyzerFacade
from Backend.BusinessLayer.Course.enums import Semester, Moed




import threading

class NegevNerds:

    _instance = None
    _lock = threading.Lock()

    def __new__(cls, mkdir):
        if cls._instance is None:
            with cls._lock:  # Ensure thread-safe instance creation
                if cls._instance is None:  # Double-checked locking
                    cls._instance = super().__new__(cls)
                    # Initialize critical attributes in __new__
                    cls._instance._user_facade = UserFacade()
                    cls._instance._course_facade = CourseFacade()
                    cls._instance._pdfFacade = PDFAnalyzerFacade()
                    cls._instance._file_manager = FileManager(mkdir)
                    cls._instance._system_managers = []
                    cls._instance._initialized = True
        return cls._instance

    def __init__(self, mkdir):
        # Prevent reinitialization
        if not hasattr(self, '_initialized'):
            self._user_facade = UserFacade()
            self._course_facade = CourseFacade()
            self._pdfFacade = PDFAnalyzerFacade()
            self._file_manager = FileManager(mkdir)
            self._system_managers = []
            self._initialized = True

    # Getter methods for accessing the facades and file manager
    @property
    def userFacade(self):
        return self._user_facade

    @property
    def courseFacade(self):
        return self._course_facade

    @property
    def fileManager(self):
        return self._file_manager

    @property
    def system_managers(self):
        return self._system_managers


    def is_system_manager(self, user_id):
        """Checks if the user is a system manager."""
        return user_id in self.system_managers

    def register(self, email, password, password_confirm, first_name, last_name):
        try:
            return self.userFacade.register(email, password, password_confirm, first_name, last_name)
        except Exception as e:
            return None, {"Error": str(e)}  # Always return a tuple



    def registerWithoutAuth(self, email, password, first_name, last_name):
        """Register a new user."""
        try:
            return self.userFacade.registerWithoutAuth(email, password, first_name, last_name)

        except Exception as e:
            return f"Error: {e}"


    def register_authentication_part(self, email, auth_code):
        """Register a new user."""
        try:
            return self.userFacade.register_authentication_part(email, auth_code)
        except Exception as e:
            return f"Error: {e}"
        
    def register_termOfUse_part(self,email, password, first_name, last_name):
        """Register a new user."""
        try:
            return self.userFacade.register_termOfUse_part(email, password, first_name, last_name)
        except Exception as e:
            return f"Error: {e}"

    # def login(self, email, password):
    #     """Log the user in."""
    #     try:
    #         user_firstName, user_lastName, user_id, message = self.userFacade.login(email, password)
    #         return user_firstName, user_lastName, user_id, message  # Return the result from the facade
    #     except Exception as e:
    #         return f"Error: {e}"

    # def login(self, email, password):
    #     """Log the user in."""
    #     try:
    #         user_firstName, user_lastName, user_id, message = self.userFacade.login(email, password)
    #         return user_firstName, user_lastName, user_id, {"status": "success", "message": message}
    #     except Exception as e:
    #         # logging.error(f"Unexpected error during login: {str(e)}")
    #         return None, None, None, {"status": "error", "message": str(e)}
    
    def login(self, email, password):
        try:
            user_firstName, user_lastName, user_id, message = self.userFacade.login(email, password)
            if user_firstName is None or user_lastName is None or user_id is None:
                return None, None, None, {"status": "error", "message": "Incorrect email or password."}

            return user_firstName, user_lastName, user_id, {"status": "success", "message": message}
        except UserOrPasswordIncorrectError:
            # return None, None, None, {"status": "error", "message": "Incorrect email or password."}
            return None, None, None, {"status": "error", "message": message}

        except Exception as e:
            return None, None, None, {"status": "error", "message": str(e)}



    def logout(self, email):
        """Log the user out."""
        try:
            result = self.userFacade.logout(email)
            return result  # Return the result from the facade
        except Exception as e:
            return f"Error: {e}"

    def edit_profile(self, email, **kwargs):
        """Edit the user's profile."""
        try:
            result = self.userFacade.editUserProfile(email, **kwargs)
            return result
        except Exception as e:
            return f"Error: {e}"

    def registerToCourse(self, course_id, user_id):
        """Add the user to course and add the course to user."""
        try:
            # Register the user to the course using Coursefacade
            self.courseFacade.register_to_course(course_id, user_id)
            # Register the course to the user using Userfacade
            self.userFacade.registerToCourse(course_id, user_id)
            print("User successfully registered to the course", user_id, course_id)
            return "User successfully registered to the course."
        except Exception as e:
            return f"Error: {e}"

    def removeStudentFromCourse(self, course_id, user_id):
        """Remove the user from the course and remove the course from user."""
        try:
            # Remove the user from the course using Coursefacade
            self.courseFacade.remove_student_from_course(course_id, user_id)
            # Remove the course from the user using Userfacade
            user = self.userFacade.users_byId.get(user_id)
            if user:
                user.removeCourse(course_id)
            else:
                raise UserDoesnotExistsError(user_id)
            return "User successfully removed from the course."
        except Exception as e:
            return f"Error: {e}"

    def open_course(self, user_id, course_id, name, syllabus_content_pdf):
        """Opens a new course in the system and saves the syllabus file."""
        try:
            # Check if the course already exists using CourseFacade
            if self.courseFacade.open_course_possibility(course_id, name):
                # Save the syllabus to the course folder using FileManager
                syllabus = self._pdfFacade.extract_syllabus_topic_total(syllabus_content_pdf)
                # syllabus_file_path = self.fileManager.save_syllabus_file(course_id, syllabus_content)
                # self.courseFacade.set_syllabus_of_course(course_id, syllabus_file_path)
                self.courseFacade.open_course(course_id,name,syllabus )
                self.courseFacade.add_manager_to_course(course_id, user_id)  # Add the user as a manager
                self.userFacade.registerToCourse(course_id, user_id)  # Add the user as a student
                return f"Course {name} opened successfully "
            else:
                raise Exception("Failed to create course.")
        except Exception as e:
            return f"Error: {e}"

    def remove_course(self, course_id, user_id):
        """Remove an existing course from the system and delete its corresponding folder."""
        try:
            # Check if the user is a system manager or the course manager
            if self.is_system_manager(user_id) or self.courseFacade.is_course_manager(course_id, user_id):
                # Remove the course using CourseFacade
                if self.courseFacade.remove_course(course_id):
                    # Delete the course folder using FileManager
                    self.fileManager.delete_course_folder(course_id)
                    return f"Course {course_id} removed successfully."
                else:
                    raise Exception("Failed to remove course.")
            else:
                raise UserIsNotCourseManager(course_id)
        except Exception as e:
            return f"Error: {e}"

    def search_exam_by_specifics(self, course_id, year: int, semester=None, moed=None):
        """Search for exams by course ID and optionally filter by year, semester, and moed."""
        try:
            # Fetch all exams for the course from coursefacade
            exams = self.courseFacade.search_exam_by_specifics(course_id, year, semester, moed)
            return exams
        except Exception as e:
            raise Exception(f"Failed to search exams: {e}")

    def search_all_course_exams(self, course_id):
        """Search for all the exams in the system for specific course"""
        try:
            # Fetch all exams for the course from coursefacade
            exams = self.courseFacade.search_all_course_exmas(course_id)
            return exams
        except Exception as e:
            raise Exception(f"Failed to search exams: {e}")

    def edit_exam_course_name(self, course_id, year, semester, moed, new_course_name):
        """Editing exam's course name """
        try:
            self.courseFacade.edit_exam_course_name(course_id, year, semester, moed, new_course_name)
            return "The exams' course name was updated successfully."
        except Exception as e:
            raise Exception(f"Failed to edit exam's course name {e}")

    def edit_exam_link(self, course_id, year, semester, moed, new_link):
        """Editing exam's link """
        try:
            self.courseFacade.edit_exam_link(course_id, year, semester, moed, new_link)
            return "The exams' link was updated successfully."
        except Exception as e:
            raise Exception(f"Failed to edit exam's link {e}")

    def edit_exam_year(self, course_id, year, semester, moed, new_year):
        """Editing exam's year """
        try:
            self.courseFacade.edit_exam_year(course_id, year, semester, moed, new_year)
            return "The exams' year was updated successfully."
        except Exception as e:
            raise Exception(f"Failed to edit exam's link {e}")

    def edit_exam_semester(self, course_id, year, semester, moed, new_semester):
        """Editing exam's semester """
        try:
            self.courseFacade.edit_exam_semester(course_id, year, semester, moed, new_semester)
            return "The exams' semester was updated successfully."
        except Exception as e:
            raise Exception(f"Failed to edit exam's link {e}")

    def edit_exam_moed(self, course_id, year, semester, moed, new_moed):
        """Editing exam's moed """
        try:
            self.courseFacade.edit_exam_moed(course_id, year, semester, moed, new_moed)
            return "The exams' moed was updated successfully."
        except Exception as e:
            raise Exception(f"Failed to edit exam's link {e}")

    def get_question_path(self, course_id, year, semester, moed, question_number):
        try:
            return self.fileManager.get_question_path(course_id, year, semester, moed, question_number)
        except (CourseIsNotExist, ExamIsNotExist) as e:
            raise e
        except Exception as e:
            raise Exception(f"Failed to get path: {e}")

    def get_answer_path(self, course_id, year, semester, moed, question_number):
        try:
            return self.fileManager.get_answer_path(course_id, year, semester, moed, question_number)
        except (CourseIsNotExist, ExamIsNotExist) as e:
            raise e
        except Exception as e:
            raise Exception(f"Failed to get path: {e}")

    def add_question(self, course_id, year, semester, moed,question_number,is_american,question_topics,  pdf_question, pdf_answer):
        """
        Add a question to a course exam with an associated PDF file.

        ining question details.
        :return: Path to the saved PDF file.
        """
        try:
            # Get course name for filename generation
            
            if self.courseFacade.check_valid_question(course_id,year,semester, moed, question_number,pdf_question):

                # Save the PDF file with a custom name
                pdf__question_path = self.fileManager.save_question_file(
                    course_id,
                    year,
                    semester,
                    moed,
                    question_number,
                    pdf_question
                )
                pdf__answer_path = None
                if pdf_answer is not None:
                    pdf__answer_path = self.fileManager.save_answer_file(
                        course_id,
                        year,
                        semester,
                        moed,
                        question_number,
                        pdf_answer
                )

                # Add the question to the course
                question_dto =self.courseFacade.add_question(course_id, year, semester, moed, question_number,
                                            is_american, question_topics,pdf__question_path, pdf__answer_path )
                
                self._pdfFacade.perform_information_retrival_question(pdf__question_path,question_dto)
            

            return "Question added successfully."
        except (CourseIsNotExist, ExamIsNotExist, TopicNotFound, QuestionAlreadyInExam) as e:
            raise e
        except Exception as e:
            raise Exception(f"Failed to add question with PDF: {e}")

    def get_user_courses(self, user_id):
        courses_ids = self.userFacade.get_user_courses(user_id)
        return self._course_facade.get_courses_DTO(courses_ids)

    def get_course_topics(self, course_id):
        return self._course_facade.get_course_topics(course_id)

    def get_all_courses(self):
        return self._course_facade.get_all_courses()

    def get_course(self, course_id):
        return self._course_facade.get_course_DTO(course_id)

    # def add_question(self, course_id, year, semester, moed, questionDTO):
    #     """Adds a question to an exam in the specified course.
    #     If the exam does not exist, it creates a new one."""
    #     try:
    #         self.coursefacade.add_question(
    #             course_id, year, semester, moed, questionDTO)
    #         return "Question added successfully."
    #     except Exception as e:
    #         raise Exception(f"Failed to add question: {e}")

    def upload_answer(self, course_id, year, semester, moed, question_number, pdf_answer):
        try:
            self.fileManager.save_answer_file(
                course_id,
                year,
                semester,
                moed,
                question_number,
                pdf_answer
            )
            return "Answer added successfully to the question."
        except (CourseIsNotExist, ExamIsNotExist) as e:
            raise e
        except Exception as e:
            raise Exception(f"Failed to upload answer: {e}")



    def search_question_by_specifics(self, course_id, year=None, semester=None, moed=None, question_number=None):
        """Search for questions based on the provided specifics for the course."""
        try:
            print(
                f"Received data: {{'course_id': '{course_id}', 'year': '{year}', 'semester': '{semester}', 'moed': '{moed}', 'question_number': '{question_number}'}}")

            # Fetch questions based on the specifics from the course
            questions = self._course_facade.search_question_by_specifics(course_id,year, semester, moed, question_number)

            print(f"Found questions: {questions}")

            return questions
        except Exception as e:
            print(f"Error occurred: {str(e)}")
            raise Exception(f"Failed to search questions: {e}")