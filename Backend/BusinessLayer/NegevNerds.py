from Backend.BusinessLayer.Util.Exceptions import *


class NegevNerds:
    def __init__(self, user_facade, course_facade, file_manager):
        self.userFacade = user_facade
        self.courseFacade = course_facade
        self.fileManager = file_manager
        self.system_managers = []

    def is_system_manager(self, user_id):
        """Checks if the user is a system manager."""
        return user_id in self.system_managers

    def register(self, email, password, first_name, last_name):
        """Register a new user."""
        try:
            return self.userFacade.register(email, password, first_name, last_name)

        except Exception as e:
            return f"Error: {e}"
        
    def register_authentication_part(self, email, auth_code):
        """Register a new user."""
        try:
            return self.userFacade.register_authentication_part(email, auth_code)
        except Exception as e:
            return f"Error: {e}"
        
    def register_termOfUse_part(self,email, password, first_name, last_name, accept):
        """Register a new user."""
        try:
            return self.userFacade.register_termOfUse_part(email, password, first_name, last_name, accept)
        except Exception as e:
            return f"Error: {e}"

    def login(self, email, password):
        """Log the user in."""
        try:
            result = self.userFacade.login(email, password)
            return result  # Return the result from the facade
        except Exception as e:
            return f"Error: {e}"

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
            self.courseFacade.registerToCourse(course_id, user_id)
            # Register the course to the user using Userfacade
            self.userFacade.registerToCourse(course_id, user_id)
            return "User successfully registered to the course."
        except Exception as e:
            return f"Error: {e}"

    def removeStudentFromCourse(self, course_id, user_id):
        """Remove the user from the course and remove the course from user."""
        try:
            # Remove the user from the course using Coursefacade
            self.courseFacade.removeStudentFromCourse(course_id, user_id)
            # Remove the course from the user using Userfacade
            user = self.userFacade.users.get(user_id)
            if user:
                user.removeCourse(course_id)
            else:
                raise UserDoesnotExistsError(user_id)
            return "User successfully removed from the course."
        except Exception as e:
            return f"Error: {e}"

    def open_course(self, user_id, course_id, name, syllabus_content, course_topics):
        """Opens a new course in the system and saves the syllabus file."""
        try:
            # Check if the course already exists using CourseFacade
            if self.courseFacade.open_course(course_id, name, course_topics):
                # Save the syllabus to the course folder using FileManager
                syllabus_file_path = self.fileManager.save_syllabus_file(course_id, syllabus_content)
                self.courseFacade.set_syllabus_of_course(course_id, syllabus_file_path)
                self.courseFacade.add_manager_to_course(course_id, user_id)  # Add the user as a manager
                self.userFacade.registerToCourse(course_id, user_id)  # Add the user as a student
                return f"Course {name} opened successfully with syllabus at {syllabus_file_path}"
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

    def add_question_with_pdf(self, course_id, year, semester, moed, pdf_file_content, question_dto):
        """
        Add a question to a course exam with an associated PDF file.

        :param course_id: ID of the course.
        :param year: Year of the exam.
        :param semester: Semester of the exam.
        :param moed: Moed of the exam.
        :param pdf_file_content: Content of the PDF file.
        :param question_dto: QuestionDTO containing question details.
        :return: Path to the saved PDF file.
        """
        try:
            # Get course name for filename generation
            course = self.courseFacade.get_course(course_id)
            course_name = course.get_name()

            # Save the PDF file with a custom name
            pdf_path = self.fileManager.save_file_question(
                file_content=pdf_file_content,
                course_name=course_name,
                year=year,
                semester=semester,
                moed=moed,
                question_number=question_dto.question_number
            )

            # Update the link_to_question in the QuestionDTO
            question_dto.link_to_question = pdf_path

            # Add the question to the course
            self.courseFacade.add_question(course_id, year, semester, moed, question_dto)

            return "Question added successfully."
        except (CourseIsNotExist, ExamIsNotExist, TopicNotFound, QuestionAlreadyInExam) as e:
            raise e
        except Exception as e:
            raise Exception(f"Failed to add question with PDF: {e}")

    # def add_question(self, course_id, year, semester, moed, questionDTO):
    #     """Adds a question to an exam in the specified course.
    #     If the exam does not exist, it creates a new one."""
    #     try:
    #         self.coursefacade.add_question(
    #             course_id, year, semester, moed, questionDTO)
    #         return "Question added successfully."
    #     except Exception as e:
    #         raise Exception(f"Failed to add question: {e}")
