import logging
import mimetypes
import uuid
import base64
from Backend.BusinessLayer.Course.CourseFacade import CourseFacade
from Backend.BusinessLayer.Notifications.NotificationFacade import NotificationFacade
from Backend.BusinessLayer.FileManager.FileManager import FileManager
from Backend.BusinessLayer.User.UserFacade import UserFacade
from Backend.BusinessLayer.Util import Exceptions
from Backend.BusinessLayer.Util.Exceptions import *
from Backend.BusinessLayer.Analyzer.AnalyzerFacade import AnalyzerFacade
from Backend.DataLayer.CourseManagers.CourseManagersRepository import CourseManagersRepository
from Backend.DataLayer.CommentData.CommentRepository import CommentRepository
from Backend.DataLayer.QuestionTopics.QuestionTopicsRepository import QuestionTopicsRepository
from Backend.DataLayer.WordsQuestions.WordsQuestionsRepository import WordsQuestionsRepository
from Backend.DataLayer.Questions.QuestionRepository import QuestionRepository
from Backend.DataLayer.ReactionData.ReactionRepository import ReactionRepository
from Backend.DataLayer.ExamData.ExamRepository import ExamRepository
from Backend.DataLayer.CourseTopics.CourseTopicsRepository import CourseTopicsRepository 
from Backend.DataLayer.UserCourses.UserCoursesRepository import UserCoursesRepository
from Backend.DataLayer.DiscussionFollow.DiscussionFollowRepository import DiscussionFollowRepository
from Backend.DataLayer.Noitifications.NotificationRepository import NotificationRepository
from Backend.DataLayer.UserData.UserRepository import UserRepository
from Backend.DataLayer.SystemManagers.SystemManagersRepository import SystemManagersRepository
from Backend.DataLayer.CourseData.CourseRepository import CourseRepository
from Backend.DataLayer.NotificationsSetting.NotificationsSettingRepository import NotificationsSettingRepository
from Backend.DataLayer.ProfilePicture.ProfilePictureRepository import ProfilePictureRepository
import re
import json
from datetime import datetime, timedelta

from flask_jwt_extended import create_access_token


import threading
import os

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class NegevNerds:

    _instance = None
    _lock = threading.Lock()
    _initialized = False  # Class-level flag for initialization status

    def __new__(cls, mkdir):
        if cls._instance is None:
            with cls._lock:
                # Double-checked locking to ensure only one thread creates the instance
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, mkdir):
        # Only initialize if it hasn't been initialized before for this instance
        if not self._initialized:
            with self._lock:  # Optional: Add lock here if init operations are sensitive to race conditions on first run
                if not self._initialized:  # Double-check after acquiring lock
                    print("Initializing NegevNerds instance attributes...")
                    # Resolve directory path once
                    resolved_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), mkdir, "files"))
                    print(f"Resolved base directory for NegevNerds: {resolved_dir}")

                    # Initialize all facades and managers
                    self._user_facade = UserFacade()
                    self._course_facade = CourseFacade()
                    self._pdfFacade = AnalyzerFacade()
                    self._file_manager = FileManager(resolved_dir)
                    self._notification_facade = NotificationFacade()

                    # Initialize locks
                    self.open_course_lock = threading.Lock()
                    self.add_question_lock = threading.Lock()
                    self.upload_exam_lock = threading.Lock()
                    self.upload_question_solution_lock = threading.Lock()

                    # Initialize system managers
                    system_managers_repo = SystemManagersRepository()
                    print("Fetching system managers...")
                    self._system_managers = system_managers_repo.get_all_system_manager_ids()
                    print(f"Initialized system managers: {self._system_managers}")

                    # Mark as initialized
                    self._initialized = True
                    print("NegevNerds instance initialization complete.")
        else:
            print("NegevNerds instance already initialized, skipping re-initialization.")

    # Getter methods for accessing the facades and file manager
    @property
    def userFacade(self):
        return self._user_facade

    @userFacade.setter
    def userFacade(self, value):
        """Sets the UserFacade instance."""
        # You might want to add type checking or validation here
        if not isinstance(value, UserFacade):
             raise TypeError("userFacade must be an instance of UserFacade")
        self._user_facade = value

    @property
    def courseFacade(self):
        return self._course_facade

    @courseFacade.setter
    def courseFacade(self, value):
        """Sets the CourseFacade instance."""
        # You might want to add type checking or validation here
        if not isinstance(value, CourseFacade):
            raise TypeError("courseFacade must be an instance of CourseFacade")
        self._course_facade = value

    @property
    def fileManager(self):
        return self._file_manager

    @property
    def system_managers(self):
        return self._system_managers

    def is_system_manager(self, user_id):
        """Checks if the user is a system manager."""
        # return user_id in self.system_managers
        if user_id in self._system_managers:
            return True
        system_managers_repo = SystemManagersRepository()
        return system_managers_repo.is_system_manager(user_id)

    def register(self, email, password, password_confirm, first_name, last_name):
        """Register a new user - first phase"""
        try:
            return self.userFacade.register(email, password, password_confirm, first_name, last_name)
        except Exception as e:
            return None, {"Error": str(e)}  # Always return a tuple

    def registerWithoutAuth(self, email, password, first_name, last_name):
        """Register a new user without sending authentication mail"""
        try:
            return self.userFacade.registerWithoutAuth(email, password, first_name, last_name)
        except Exception as e:
            return f"Error: {e}"

    def register_authentication_part(self, email, auth_code):
        """Register a new user - check the authentication code"""
        try:
            return self.userFacade.register_authentication_part(email, auth_code)
        except Exception as e:
            return f"Error: {e}"
        
    def register_termOfUse_part(self, email, password, first_name, last_name, profile_picture_file):
        """Register a new user - user approve the terms"""
        try:
            user_id, message = self.userFacade.register_termOfUse_part(email, password, first_name, last_name)
            if profile_picture_file is not None:
                self.upload_profile_picture(user_id, profile_picture_file)
            return user_id, message
        except Exception as e:
            return f"Error: {e}"
    
    def login(self, email, password):
        """login user """
        try:
            user_firstName, user_lastName, user_id, message = self.userFacade.login(email, password)
            if user_firstName is None or user_lastName is None or user_id is None:
                return None, None, None, {"status": "error", "message": "Incorrect email or password."}

            return user_firstName, user_lastName, user_id, {"status": "success", "message": message}
        except UserOrPasswordIncorrectError as e:
            return None, None, None, {"status": "error", "message": e.message}
        except Exception as e:
            return None, None, None, {"status": "error", "message": str(e)}

    def logout(self, user_id):
        """Log the user out."""
        try:
            result = self.userFacade.logout(user_id)
            return result
        except Exception as e:
            return f"Error: {e}"

    def forgot_password(self, email):
        valid_bgu_mail = self._user_facade.is_valid_email(email)
        if not valid_bgu_mail:
            return json.dumps({
                "status": "error",
                "message": "האימייל חייב להיות של אוניברסיטת בן גוריון (@bgu.ac.il / @post.bgu.ac.il )"
            })

        user = self._user_facade.getUser_by_email(email)
        if user is None:
            return json.dumps({
                "status": "error",
                "message": "כתובת אימייל לא נמצאה במערכת."
            })

        try:
            self._user_facade.send_reset_password_code(email)
            return json.dumps({
                "status": "success",
                "message": "מייל אימות נשלח לאימייל שסיפקת."
            })
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": "שליחת הקוד נכשלה. נסה שוב מאוחר יותר.",
                "error": str(e)
            })

    def verify_reset_code(self, email, code):
        try:
            # Check if code exists for the email
            stored = self._user_facade.pending_reset_codes.get(email)

            if not stored:
                return json.dumps({
                    "status": "error",
                    "message": "לא נמצא קוד אימות עבור אימייל זה. בקש קוד חדש."
                })

            stored_code, expiry_time = stored

            if datetime.now() > expiry_time:
                return json.dumps({
                    "status": "error",
                    "message": "הקוד פג תוקף. בקש קוד חדש."
                })

            if code != stored_code:
                return json.dumps({
                    "status": "error",
                    "message": "קוד אימות שגוי."
                })

            # Optional: delete code after success
            del self._user_facade.pending_reset_codes[email]

            # Generate temporary access token for reset-password flow
            access_token = create_access_token(identity=email, expires_delta=timedelta(minutes=3))

            return json.dumps({
                "status": "success",
                "token": access_token
            })

        except Exception as e:
            print(f"Error verifying reset code: {str(e)}")
            return json.dumps({
                "status": "error",
                "message": "שגיאה פנימית באימות הקוד.",
                "error": str(e)
            })

    def reset_new_password(self, email, password):
        # Check if the password meets security requirements
        valid_password = self._user_facade.is_valid_password(password)
        if not valid_password:
            return json.dumps({
                "status": "error",
                "message": "הסיסמה אינה עומדת בדרישות האבטחה"
            })

        # Try to update the password in the database
        updated_successfully = self._user_facade.reset_new_password(email, password)

        if updated_successfully:
            return json.dumps({
                "status": "success",
                "message": "הסיסמה עודכנה בהצלחה"
            })
        else:
            return json.dumps({
                "status": "error",
                "message": "אירעה שגיאה בעדכון הסיסמה. ייתכן שהמשתמש לא קיים"
            })

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
            self.courseFacade.register_to_course(course_id, user_id)
            self.userFacade.registerToCourse(course_id, user_id)
            return "UserData successfully registered to the course."
        except Exception as e:
            return f"Error: {e}"

    def removeStudentFromCourse(self, course_id, user_id):
        """Remove the user from the course and remove the course from user."""
        try:
            self.courseFacade.remove_student_from_course(course_id, user_id)
            user = self.userFacade.getUser_by_id(user_id)
            if user:
                user.removeCourse(course_id)
            else:
                raise UserDoesnotExistsError(user_id)
            return "UserData successfully removed from the course."
        except Exception as e:
            return f"Error: {e}"

    def get_user_courses(self, user_id):
        courses_ids = self.userFacade.get_user_courses(user_id)
        return self._course_facade.get_courses_DTO(courses_ids)

    def get_user_name(self, user_id):
        """Get the user full name."""
        try:
            result = self.userFacade.get_user_name(user_id)
            return result
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def is_user_manager(self, course_id, user_id):
        """Delegates to CourseManagersRepository to check if user is a course manager."""
        try:
            return self._course_facade.is_course_manager(course_id,user_id )
        except Exception as e:
            raise Exception(f"Error in NegevNerds.is_user_manager: {str(e)}")

    def open_course(self, user_id, course_id, name, syllabus_content_pdf):
        """Opens a new course in the system and saves the syllabus file."""
        with self.open_course_lock:
            try:
                # Check if the course already exists using CourseFacade
                if self.courseFacade.open_course_possibility(course_id, name):
                    syllabus = self._pdfFacade.extract_syllabus_topic_total(syllabus_content_pdf, name)
                    self.courseFacade.open_course(course_id,name,syllabus )
                    self.courseFacade.add_manager_to_course(course_id, user_id)  # Add the user as a manager
                    self.userFacade.registerToCourse(course_id, user_id)  # Add the user as a student
                    return f"Course {name} opened successfully "
                else:
                    raise Exception("Failed to create course.")
            except Exception as e:
                return f"Error: {e}"

    def get_course_topics(self, course_id):
        return self._course_facade.get_course_topics(course_id)

    def get_all_courses(self):
        return self._course_facade.get_all_courses()

    def get_course(self, course_id):
        return self._course_facade.get_course_DTO(course_id)

    def get_courses_by_name(self, name_part):
        return self._course_facade.get_courses_by_name(name_part)

    def isCourseExists(self, new_course_id):
       course = self._course_facade.get_course(new_course_id)
       if course is not None:
           return True
       else:
           return False

    def get_exam_full_pdf(self, course_id, year, semester, moed):
        try:
            return self.courseFacade.get_exam_full_pdf(course_id, year, semester, moed)
        except Exception as e:
            return f"Error: {e}"

    def check_exam_full_pdf(self, course_id, year, semester, moed):
        try:
            return self.courseFacade.check_exam_full_pdf(course_id, year, semester, moed)
        except Exception as e:
            return f"Error: {e}"

    def checkExistSolution(self, course_id, year, semester, moed,question_number):
        try:
            return self.courseFacade.checkExistSolution(course_id, year, semester, moed,question_number)
        except Exception as e:
            return f"Error: {e}"
    
    def get_exam_pdf_link(self, course_id, year, semester, moed):
        try:
            result = self.courseFacade.get_exam_full_pdf(course_id, year, semester, moed)
            return result
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def splitPDF(self, course_id, year, semester, moed, pdf_file, line_data):
        question_number = 1
        question_files = self._pdfFacade.splitPDF(pdf_file, line_data)
        added_successfully = 0
        for curr_question in question_files:
            try :
                if self.courseFacade.check_valid_question(course_id, year, semester, moed, question_number):
                    self.add_question(course_id, year, semester, moed, question_number, False, None, curr_question, None)
                added_successfully += 1
            except Exception as e:
                print(f"Error adding question {question_number}: {str(e)}")
            question_number += 1
        if added_successfully == 0:
            raise Exception("No questions were added from the split PDF.")

    def split_solution_PDF(self, course_id, year, semester, moed, solution, line_data):
        if self._course_facade.existFullExamSolution(course_id=course_id, year=year, semester=semester, moed=moed):
            raise Exceptions.ExamAlreadyExists
        question_number = 1
        solution_files = self._pdfFacade.splitPDF(solution, line_data)
        added_successfully = 0
        for curr_solution in solution_files:
            try:
                if self.courseFacade.checkExistQuestion(course_id, year, semester, moed, question_number):
                    if not self.courseFacade.checkExistSolution(course_id=course_id, year=year, semester=semester, moed=moed, question_number=question_number):
                        self.uploadSolution(course_id=course_id, year=year, semester=semester, moed=moed, question_number=question_number, solution_file=curr_solution)
                added_successfully+=1
            except Exception as e:
                print(f"Error upload solution {question_number}: {str(e)}")
            question_number = question_number+1
        if added_successfully == 0:
            raise Exception("No questions were added from the split solution PDF.")

    def upload_full_exam_pdf(self, course_id, year, semester, moed, pdf_file):
        try:

            with self.upload_exam_lock:
                if self._course_facade.check_exam_full_pdf(course_id=course_id, year=year , semester=semester, moed=moed):
                    course = self._course_facade.get_course(course_id)
                    exam_id = course.get_exam(year, semester, moed).id
                    raise Exceptions.ExamAlreadyExists(exam_id)
                if pdf_file.content_type != 'application/pdf':
                    raise ValueError("The uploaded file is not a valid PDF.")
                exam_path = self._file_manager.save_exam_file(course_id, year, semester, moed, pdf_file)
                result = self.courseFacade.upload_full_exam_pdf(course_id, year, semester, moed, exam_path)
                return {"status": "success", "message": "File uploaded and saved successfully.", "link": exam_path}
        except Exception as e:
            print(f"Error in NegevNerds.upload_full_exam_pdf: {str(e)}")
            return {"status": "error", "message": str(e)}

    def existFullExamSolution(self, course_id, year, semester, moed):
        return self.courseFacade.existFullExamSolution(course_id, year, semester, moed)

    def get_exam_solution_pdf_link(self, course_id, year, semester, moed):
        try:
            link_to_solution = self.courseFacade.get_full_exam_solution(course_id, year, semester, moed)
            return link_to_solution
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def add_exam_solution(self, course_id, year, semester, moed, solution):
        try:
            with self.upload_exam_lock:
                print(f"[DEBUG] Checking file type: {solution.content_type}")
                print(f"[DEBUG] Semester={semester} ({type(semester)}), Moed={moed} ({type(moed)})")

                if self._course_facade.existFullExamSolution(course_id, year, semester, moed):
                    raise Exceptions.ExamAlreadyExists

                if solution.content_type != 'application/pdf':
                    raise ValueError("The uploaded file is not a valid PDF.")

                solution_path = self._file_manager.save_exam_solution_file(course_id, year, semester, moed, solution)
                self.courseFacade.upload_full_exam_solution(course_id, year, semester, moed, solution_path)

                return {
                    "status": "success",
                    "message": "File uploaded and saved successfully.",
                    "link": solution_path
                }
        except Exception as e:
            print(f"Error in NegevNerds.upload_full_exam_pdf: {str(e)}")
            return {"status": "error", "message": str(e)}

    def uploadSolution(self, course_id, year, semester, moed, question_number, solution_file):
        """add solution to question"""
        with self.upload_question_solution_lock:
            try:
                print("uploadSolution 1", flush=True)
                if self._course_facade.checkExistSolution(course_id=course_id, year=year , semester=semester, moed=moed,question_number=question_number):
                    raise Exceptions.CourseAlreadyExists(course_id)
                answer_path = ""
                print("uploadSolution 2", flush=True)
                if solution_file is not None:
                    if self.is_photo(solution_file):
                        print("type:photo", flush=True)
                        answer_path = self.fileManager.save_photo_answer_file(
                            course_id=course_id,
                            year=year,
                            semester=semester,
                            moed=moed,
                            question_number=question_number,
                            photo_file=solution_file
                        )
                    else:
                        print("type:pdf", flush=True)
                        answer_path = self.fileManager.save_answer_file_pdf(
                            course_id=course_id,
                            year=year,
                            semester=semester,
                            moed=moed,
                            question_number=question_number,
                            pdf_answer=solution_file
                        )
                result = self.courseFacade.uploadSolution(course_id, year, semester, moed, question_number, answer_path)
                return {"status": "success", "message": "File uploaded and saved successfully.", "link": answer_path}
            except Exception as e:
                print(f"Error in NegevNerds.upload_full_exam_pdf: {str(e)}")
                return {"status": "error", "message": str(e)}

    def remove_course(self, course_id, user_id):
            """Remove an existing course from the system and delete its corresponding folder."""
            try:
                # Check if the user is a system manager or the course manager
                if self.is_system_manager(user_id):
                    # Remove the course using CourseFacade
                    exams = self._course_facade.get_course(course_id).get_all_exams()
                    for exam in exams:
                        questions = exam.get_all_exam_question()
                        for question in questions:
                            self.delete_question(course_id, exam.year, exam.semester,exam.moed, question.question_number)
                        self.delete_exam(exam.id,course_id, exam.year, exam.semester,exam.moed)
                    course_topics_repo = CourseTopicsRepository()
                    course_topics_repo.remove_all_topics_from_course(course_id)
                    course_managers_repo = CourseManagersRepository()
                    course_managers_repo.remove_all_managers_from_course(course_id)
                    user_courses_repo = UserCoursesRepository()
                    # user_courses_repo.remove_all_user_courses_by_course_id(course_id)
                    course_users = user_courses_repo.get_users_for_course(course_id)
                    for user in course_users:
                        user.removeCourse(course_id)
                    if self.courseFacade.remove_course(course_id):
                        # Delete the course folder using FileManager
                        self.fileManager.delete_course_folder(course_id)
                        return {
                        "status": "success",
                        "message": f"Course {course_id} removed successfully."
                    }
                    else:
                        return {
                            "status": "error",
                            "message": "Failed to remove course."
                        }
                else:
                    return {
                    "status": "error",
                    "message": f"User {user_id} is not a system manager."
                }
            except Exception as e:
                return {
                    "status": "error",
                    "message": str(e)
                }

    # def search_exam_by_specifics(self, course_id, year: int, semester=None, moed=None):
    #     """Search for exams by course ID and optionally filter by year, semester, and moed."""
    #     try:
    #         # Fetch all exams for the course from coursefacade
    #         exams = self.courseFacade.search_exam_by_specifics(course_id, year, semester, moed)
    #         return exams
    #     except Exception as e:
    #         raise Exception(f"Failed to search exams: {e}")

    # def search_all_course_exams(self, course_id):
    #     """Search for all the exams in the system for specific course"""
    #     try:
    #         # Fetch all exams for the course from coursefacade
    #         exams = self.courseFacade.search_all_course_exams(course_id)
    #         return exams
    #     except Exception as e:
    #         raise Exception(f"Failed to search exams: {e}")

    # def edit_exam_link(self, course_id, year, semester, moed, new_link):
    #     """Editing exam's link """
    #     try:
    #         self.courseFacade.edit_exam_link(course_id, year, semester, moed, new_link)
    #         return "The exams' link was updated successfully."
    #     except Exception as e:
    #         raise Exception(f"Failed to edit exam's link {e}")

    # def add_question(self, course_id, year, semester, moed, question_number, is_american, question_topics,  question_file, answer_file):
    #     """
    #     Add a question to a course exam with an associated PDF file.
    #
    #     ining question details.
    #     :return: Path to the saved PDF file.
    #     """
    #
    #     try:
    #         return self.courseFacade.get_link_to_answer(course_id, year, semester, moed, question_number)
    #     except (CourseIsNotExist, ExamIsNotExist) as e:
    #         raise e
    #     except Exception as e:
    #         raise Exception(f"Failed to get path: {e}")

    def generate_comment_id(self):
        return "comment" + str(uuid.uuid4())

    def add_comment(self, course_id, year, semester, moed, question_number, writer_name, writer_id,prev_id,
                    comment_text, photo_file, question_id):
        """
                Add a comment to a question discussion.
        """
        try:
            comment_id = self.generate_comment_id()
            link_to_media = ""
            if photo_file is not None:
                link_to_media = self.fileManager.save_media_for_comment(
                    course_id=course_id,
                    year=year,
                    semester=semester,
                    moed=moed,
                    question_number=question_number,
                    comment_id=comment_id,
                    photo_file=photo_file
            )
            father_comment_id = self.courseFacade.add_comment(course_id=course_id, year=year, semester=semester,
                                                           moed=moed, question_number=question_number, comment_id=comment_id,
                                                          writer_name=writer_name, 
                                                          writer_id=writer_id,prev_id=prev_id, comment_text=comment_text,
                                                              link_to_media=link_to_media)
            # for commenter in comment_writers:
            #     self._notification_facade.send_notification(sender_id=writer_id, receiver_id=commenter,message=f"{writer_id}- add comment in discussion which you take part in the past", need_approval=False)
            frontend_base_url = os.getenv("FRONTEND_BASE_URL", "http://localhost:3000")  # default for safety
            question_link = f"{frontend_base_url}/question/{course_id}/{year}/{semester}/{moed}/{question_number}"
            if father_comment_id != "0" and father_comment_id != writer_id:
                send_email = self._user_facade.should_send_notification(father_comment_id,"CommentToComment")
                message = f"{writer_name} הגיב/ה על תגובה שלך בדיון "
                self._notification_facade.send_notification(receiver_id=father_comment_id, sender_id=writer_id, message = message, isApproved=False,
                                                                link=question_link,appoint_system_manager=False, appoint_course_manager=False, comment_to_following=False,
                    comment_to_comment=True, react_to_comment=False, remove_course_manager=False, send_email =send_email )

            discussion_following_repo =  DiscussionFollowRepository()
            get_user_following_discuussion = discussion_following_repo.get_followers_for_question(question_id)

            for user_id in get_user_following_discuussion:
                if user_id != writer_id and user_id != father_comment_id:
                    message = f"{writer_name} הוסיפ/ה תגובה בדיון שאת/ה עוקב/ת אחריו"
                    send_email = self._user_facade.should_send_notification(user_id,"CommentToFollowing")
                    self._notification_facade.send_notification(receiver_id=user_id, sender_id=writer_id, message = message, isApproved=False,
                                                                link=question_link,appoint_system_manager=False, appoint_course_manager=False, comment_to_following=True,
                    comment_to_comment=False, react_to_comment=False, remove_course_manager=False, send_email =send_email)
            
            return "CommentData added successfully."
        except (CourseIsNotExist, ExamIsNotExist, QuestionNotFound) as e:
            raise e
        except Exception as e:
            raise Exception(f"Failed to add comment: {e}")

    def add_reaction(self, course_id, year, semester, moed, question_number, comment_id, user_id, emoji):
        """
            Add a reaction to a comment.
        """
        try:
            receiver_id = self.courseFacade.add_reaction(course_id=course_id, year=year, semester=semester,
                                          moed=moed, question_number=question_number,
                                          comment_id=comment_id, user_id=user_id, emoji=emoji)
            frontend_base_url = os.getenv("FRONTEND_BASE_URL", "http://localhost:3000")  # default for safety
            question_link = f"{frontend_base_url}/question/{course_id}/{year}/{semester}/{moed}/{question_number}"
            if receiver_id != "0" and receiver_id != user_id:
                user_repo = UserRepository()
                writer_name =user_repo.get_user_full_name_by_id(user_id)
                message = f"{writer_name} הוסיפ/ה רגש על תגובה שלך בדיון "
                send_email = self._user_facade.should_send_notification(receiver_id, "ReactToComment")
                self._notification_facade.send_notification(receiver_id=receiver_id, sender_id=user_id, message = message, isApproved=False,
                                                                link=question_link,appoint_system_manager=False, appoint_course_manager=False, comment_to_following=False,
                    comment_to_comment=False, react_to_comment=True, remove_course_manager=False, send_email = send_email)

            #self._notification_facade.send_notification(sender_id=user_id, receiver_id=receiver_id ,message= f"{user_id} add reaction to your comment- {comment_id}", need_approval=False )
            return "ReactionData added successfully."
        except (CourseIsNotExist, ExamIsNotExist, QuestionNotFound, CommentNotFound) as e:
            raise e
        except Exception as e:
            raise Exception(f"Failed to add reaction: {e}")
        
    def format_relative_time(self, past_time):
        now = datetime.now()
        delta = now - past_time

        seconds = int(delta.total_seconds())
        minutes = seconds // 60
        hours = minutes // 60
        days = delta.days
        weeks = days // 7
        months = days // 30
        years = days // 365

        if seconds < 60:
            return f"לפני {seconds} שניות"
        elif minutes < 60:
            return f"לפני {minutes} דקות"
        elif hours < 24:
            return f"לפני {hours} שעות"
        elif days < 7:
            return f"לפני {days} ימים"
        elif weeks < 4:
            return f"לפני {weeks} שבועות"
        else:
            return f"לפני {years} שנים"
        
    def get_unapproved_notification_list(self, user_id):
        try:
            repo = NotificationRepository()
            notifications = repo.get_unapproved_notifications(user_id)

            # Format response
            response = []
            for notif in notifications:
                # Determine the type based on which boolean is True
                notif_type = None
                if notif.AppointSystemManager:
                    notif_type = "AppointSystemManager"
                elif notif.AppointCourseManager:
                    notif_type = "AppointCourseManager"
                elif notif.CommentToFollowing:
                    notif_type = "CommentToFollowing"
                elif notif.CommentToComment:
                    notif_type = "CommentToComment"
                elif notif.ReactToComment:
                    notif_type = "ReactToComment"
                elif notif.RemoveCourseManager:
                    notif_type = "RemoveCourseManager"
                
                time_str = self.format_relative_time(notif.time) if notif.time else None
                
                response.append({ 
                    "type": notif_type,
                    "message": notif.message,
                    "notification_id": notif.notification_id,
                    "timestamp": time_str ,
                    "link": notif.link
                })
            return json.dumps({
            "success": True,
            "notifications": response})

        except Exception as e:
            return json.dumps({
                "success": False,
                "message": "Failed to fetch notifications",
                "error": str(e) })
    #
    # def remove_reaction(self, course_id, year, semester, moed, question_number, comment_id, reaction_id):
    #     """
    #         Remove a reaction from a comment.
    #     """
    #     try:
    #         self.courseFacade.remove_reaction(course_id=course_id, year=year, semester=semester,
    #                                       moed=moed, question_number=question_number,
    #                                       comment_id=comment_id, reaction_id=reaction_id)
    #         return "ReactionData removed successfully."
    #     except (CourseIsNotExist, ExamIsNotExist, QuestionNotFound, CommentNotFound, ReactionNotFound) as e:
    #         raise e
    #     except Exception as e:
    #         raise Exception(f"Failed to remove reaction: {e}")

    def search_free_text(self , text, course_id = None):
        search_dtos, suggestion= self._pdfFacade.search_free_text_from_course(text=text, course_id=course_id)
        ques_dtos = self.courseFacade.get_questions_dto_by_search_dtos(dtos=search_dtos)
        return ques_dtos, suggestion

    def add_question(self, course_id, year, semester, moed, question_number, is_american, question_topics,  question_file, answer_file):
        """
        Add a question to a course exam with an associated PDF file.

        ining question details.
        :return: Path to the saved PDF file.
        """

        try:
            # Get course name for filename generation
            # question_analyzer = QuestionAnalyzer()
            if self.is_photo(question_file):
                question_text= self._pdfFacade.extract_text_from_image(question_file)
            else:
                question_text = self._pdfFacade.extract_text_from_pdf_file(question_file)
            with self.add_question_lock:
                if self.courseFacade.check_valid_question(course_id=course_id,year=year,semester=semester, moed=moed, question_number=question_number):
                    # Save the PDF file with a custom name
                    print(f"Base directory: {self.fileManager._base_dir}")

                    if self.is_photo(question_file):
                        question_path= self.fileManager.save_photo_question_file(
                            course_id=course_id,
                            year=year,
                            semester=semester,
                            moed=moed,
                            question_number=question_number,
                            photo_file=question_file
                        )

                    else :
                        question_path = self.fileManager.save_question_file_pdf(
                            course_id=course_id,
                            year=year,
                            semester=semester,
                            moed=moed,
                            question_number=question_number,
                            pdf_question=question_file
                        )
                    answer_path = ""
                    if answer_file is not None:
                        if self.is_photo(answer_file):
                            answer_path = self.fileManager.save_photo_answer_file(
                                course_id=course_id,
                                year=year,
                                semester=semester,
                                moed=moed,
                                question_number=question_number,
                                photo_file=answer_file
                            )
                        else:
                            answer_path = self.fileManager.save_answer_file_pdf(
                                course_id=course_id,
                                year=year,
                                semester=semester,
                                moed=moed,
                                question_number=question_number,
                                pdf_answer=answer_file
                            )
                    # Add the question to the course
                    question_id = self.courseFacade.add_question(course_id=course_id, year=year, semester=semester, moed=moed,
                                                                 question_number=question_number,is_american=is_american,
                                                                 question_topics=question_topics,pdf_question_path=question_path, pdf_answer_path=answer_path, question_text=question_text)
                    if self.is_photo(question_file):
                        self._pdfFacade.perform_information_retrieval_question_photo(text=question_text, question_id=question_id, course_id = course_id)
                    else:
                        self._pdfFacade.perform_information_retrieval_question_pdf(pdf_question_path=question_path, question_id=question_id, course_id = course_id)

                return "Question added successfully."
        except (CourseIsNotExist, ExamIsNotExist, TopicNotFound, QuestionAlreadyInExam) as e:
            raise e
        except Exception as e:
            raise Exception(f"Failed to add question with PDF: {e}")

    def delete_question(self, course_id, year, semester, moed, question_number):
        """
        Deletes a question from the course, ensuring all related data is removed.
        """
        try:
            # Get the course and ensure it exists
            question_id, question_details, pathQuestion, pathAnswer = self.courseFacade.checkExistQuestion(course_id, year, semester, moed, question_number)
            if not question_id:
                raise Exception(
                    f"Question {question_number} does not exist in the exam for course {course_id}, "
                    f"Year: {year}, Semester: {semester}, Moed: {moed}."
                )
            comment_repo = CommentRepository()
            comments_Ids = comment_repo.get_comment_ids_by_question_id(question_id)
            reactions_repo = ReactionRepository()
            reactions_repo.delete_reactions_by_comment_ids(comments_Ids)
            comment_repo.delete_comments_by_question_id(question_id)
            words_questions_repo = WordsQuestionsRepository()
            words_questions_repo.delete_question_words_from_all_tables(question_id)
            self._pdfFacade.remove_question_from_search(course_id=course_id, question_id=question_id)
            question_topics_repo = QuestionTopicsRepository()
            question_topics_repo.delete_topics_by_question_id(question_id)
            question_repo = QuestionRepository()
            question_repo.delete_question(question_id)
            self.fileManager.delete_file(pathQuestion)
            if pathAnswer != "":
                self.fileManager.delete_file(pathAnswer)
            try:
                elastic_id = f"{course_id}_{question_id}"
                info_retrieval = self._pdfFacade.information_retrieval
                info_retrieval.elastic_search.delete(index=info_retrieval.index_name, id=elastic_id)
                print(f"Deleted question {elastic_id} from ElasticSearch successfully.")
            except Exception as e:
                print(f"Warning: Failed to delete question {question_id} from ElasticSearch: {str(e)}")

        except Exception as e:
            raise Exception(f"Error in NegevNerds delete_question: {str(e)}")
        
    def search_by_topic(self, course_id, topic):
        """Search for questions by topic in a specific course."""
        try:
            # Fetch all questions for the given course from the course facade
            questions = self.courseFacade.search_questions_by_topic(course_id, topic)

            return questions
        except Exception as e:
            raise Exception(f"Error while searching by topic: {str(e)}")

    def update_user_name(self,user_id, first_name, last_name):
        success =  self._user_facade.update_user_name(user_id, first_name, last_name)
        if success:
            comments_repo = CommentRepository()
            return comments_repo.update_user_name(user_id, first_name, last_name)

    def get_comment_media_link(self, course_id, year, semester, moed, question_number, comment_id):
        try:
            return self.courseFacade.get_comment_media_link(course_id, year, semester, moed, question_number, comment_id)
        except (CourseIsNotExist, ExamIsNotExist, CommentNotFound, QuestionNotFound) as e:
            raise e
        except Exception as e:
            raise Exception(f"Failed to get path: {e}")

    def get_question_path(self, course_id, year, semester, moed, question_number):
        try:
            return self.courseFacade.get_link_to_question(course_id, year, semester, moed, question_number)
        except (CourseIsNotExist, ExamIsNotExist) as e:
            raise e
        except Exception as e:
            raise Exception(f"Failed to get path: {e}")

    def get_answer_path(self, course_id, year, semester, moed, question_number):
        """answer for question"""
        try:
            return self.courseFacade.get_link_to_answer(course_id, year, semester, moed, question_number)
        except (CourseIsNotExist, ExamIsNotExist) as e:
            raise e
        except Exception as e:
            raise Exception(f"Failed to get path: {e}")

    def remove_reaction(self, course_id, year, semester, moed, question_number, comment_id, reaction_id):
        """Remove a reaction from a comment."""
        try:
            self.courseFacade.remove_reaction(course_id=course_id, year=year, semester=semester,

                                          moed=moed, question_number=question_number,
                                          comment_id=comment_id, reaction_id=reaction_id)
            return "ReactionData removed successfully."
        except (CourseIsNotExist, ExamIsNotExist, QuestionNotFound, CommentNotFound, ReactionNotFound) as e:
            raise e
        except Exception as e:
            raise Exception(f"Failed to remove reaction: {e}")

    def is_photo(self, file):
        """Check if the given file is a valid photo (JPEG, JPG, PNG).

        :param file: The uploaded file object.
        :return: True if the file is a valid photo, False otherwise.
        """
        if file:
            # Get the MIME type of the file
            mime_type, _ = mimetypes.guess_type(file.filename)
            # Allowed photo MIME types
            allowed_photo_types = {"image/jpeg", "image/png"}  # Covers JPG, JPEG, and PNG
            return mime_type in allowed_photo_types
        return False

    def get_comments_metadata(self, question_id):
        """
        Returns a list of metadata dicts for each comment, including profile picture in base64.
        """
        try:
            comment_repo = CommentRepository()
            comments_metaData = comment_repo.get_comments_metadata_by_question_id(question_id)

            print(f"[DEBUG] Found {len(comments_metaData)} comments metadata for question_id={question_id}")

            # Add base64 image for each comment
            # Add base64 image for each comment
            for item in comments_metaData:
                image_path = item.get("profile_picture_path")
                print(f'image_path: {image_path}')
                if image_path and os.path.exists(image_path):
                    try:
                        with open(image_path, "rb") as img_file:
                            encoded = base64.b64encode(img_file.read()).decode("utf-8")
                            item["profile_picture_base64"] = encoded
                    except Exception:
                        item["profile_picture_base64"] = None
                else:
                    item["profile_picture_base64"] = None  # ⬅️ Good: blank if no image

                item.pop("profile_picture_path", None)

            return comments_metaData

        except Exception as e:
            print(f"[FATAL] Could not fetch comments metadata: {e}")
            return []

        except Exception as e:
            raise Exception(f"Error in NegevNerds get_comments_metadata: {str(e)}")

    def delete_comment(self, course_id, year, semester, moed, question_number, comment_id):
        """delete comment."""
        try:
            self.courseFacade.delete_comment(course_id=course_id, year=year, semester=semester,
                                           moed=moed, question_number=question_number,
                                           comment_id=comment_id)
            return "CommentData deleted successfully."
        except (CourseIsNotExist, ExamIsNotExist, QuestionNotFound, CommentNotFound) as e:
            raise e
        except Exception as e:
            raise Exception(f"Failed to delete comment: {e}")

    def edit_comment_text(self, course_id, year, semester, moed, question_number, comment_id, new_text):
        """edit comment text."""
        try:
            self.courseFacade.edit_comment_text(course_id=course_id, year=year, semester=semester,
                                           moed=moed, question_number=question_number,
                                           comment_id=comment_id, new_text=new_text)
            return "CommentData edited successfully."
        except (CourseIsNotExist, ExamIsNotExist, QuestionNotFound, CommentNotFound) as e:
            raise e
        except Exception as e:
            raise Exception(f"Failed to edit comment: {e}")

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

    # def get_user_last_notifications(self, user_id, number_of_notifications):
    #     """Search for questions based on the provided specifics for the course."""
    #     # try:
    #     pass
    #
    #         Fetch questions based on the specifics from the course
    #     notifications = self._notification_facade.get_user_last_notifications(user_id=user_id, number_of_notifications=number_of_notifications)
    #     return notifications
    #     except Exception as e:
    #         print(f"Error occurred: {str(e)}")
    #         raise Exception(f"Failed to search questions: {e}")

    def handleDownloadAllExamsZip(self, course_id):
        """Download a zip file of the examsof the specific course."""
        try:
            # Fetch questions based on the specifics from the course
            folderName , exams = self._course_facade.handleDownloadAllExamsZip(course_id)

            return folderName, exams
        except Exception as e:
            print(f"Error occurred: {str(e)}")
            raise Exception(f"Failed to search questions: {e}")

    def edit_question_topic(self,course_id, year, semester, moed, question_number, topics):
        res = self._course_facade.edit_question_topic(course_id, year, semester, moed, question_number, topics)

        if res:
            return json.dumps({
                "status": "success",
                "message": "נושאי השאלה עודכנו בהצלחה"
            })
        else:
            return json.dumps({
                "status": "error",
                "message": "אירעה שגיאה בעדכון נושאי השאלה"
        })

    def checkSameExams(self, old_course_id, old_year, old_semester, old_moed,
                        new_course_id, new_year, new_semester, new_moed):
        if old_course_id == new_course_id:
            if old_year == new_year:
                if old_semester == new_semester:
                    if old_moed == new_moed:
                        return True
                    else:
                        return False
                else:
                    return False
            else:
                return False
        else:
            return False
    
    def delete_exam(self, exam_id, old_course_id, old_year, old_semester, old_moed):
        exam_link = self._course_facade.get_exam_full_pdf(old_course_id, old_year, old_semester, old_moed)
        if exam_link != "":
            self.fileManager.delete_file(exam_link)
        exam_repo = ExamRepository()
        exam_repo.delete_exam_by_id(exam_id)
        
    def delete_question_solution(self, course_id,year, semester, moed, question_number):
        solution_path, question_id = self._course_facade.get_question_id_and_path(course_id,year, semester, moed, question_number)
        if solution_path != "":
            self.fileManager.delete_file(solution_path)
            question_repo = QuestionRepository()
            question_repo.uploadSolution(question_id, "")
            return True
        return False
    
    def update_course_topics(self,course_id, added_topics, removed_topics):
        course_topics = CourseTopicsRepository()
        for added_topic in added_topics:
            if course_topics.is_exist(added_topic,course_id):
                return json.dumps({
                        "status": "error",
                        "message": f"לא ניתן להוסיף את הנושא: {added_topic} מכיוון שהוא כבר קיים בקורס"
                    })
        for remove_topic in removed_topics:
            if not course_topics.is_exist(remove_topic,course_id):
                return json.dumps({
                        "status": "error",
                        "message": f"לא ניתן למחוק את הנושא: {remove_topic} מכיוון שהוא כבר לא קיים בקורס"
                    })
        questions_topics_repo = QuestionTopicsRepository()
        questions_repo = QuestionRepository()
        for to_remove in removed_topics:
            questions_id = questions_topics_repo.get_questions_byTopic(to_remove)
            for question_id in questions_id:

                exam_id = questions_repo.get_exam_id_by_question_id(question_id)
                match = re.search(r"EXAM-(\d+\.\d+\.\d+)", exam_id)
                if match:
                    courseID = match.group(1)
                    if courseID == course_id:
                        return json.dumps({
                            "status": "error",
                            "message": f"לא ניתן למחוק את הנושא: {to_remove} מכיוון שהוא משוייך לשאלה בקורס"
                        })
        self._course_facade.add_course_topics(course_id,added_topics)
        self._course_facade.remove_course_topics(course_id,removed_topics)
        return json.dumps({
                    "status": "success",
                    "message": "נושאי הקורס עודכנו בהצלחה"
                })
    
    # def delete_question_solution(self, course_id,year, semester, moed, question_number):
    #     solution_path, question_id = self._course_facade.get_question_id_and_path(course_id,year, semester, moed, question_number)
    #     if solution_path is not None:
    #         self.fileManager.delete_file(solution_path)
    #         question_repo = QuestionRepository()
    #         question_repo.uploadSolution(question_id, "")
    #         return True
    #     return False
    
    # def remove_course(self,course_id):
       
    #     self._course_facade.ge
    #     return json.dumps({
    #                 "status": "success",
    #                 "message": "נושאי הקורס עודכנו בהצלחה"
    #             })
    
    def is_following(self,user_id, question_id):
        repo = DiscussionFollowRepository()
        return repo.is_following(user_id=user_id, question_id=question_id)

    def follow_question(self, user_id, question_id):
        repo = DiscussionFollowRepository()
        repo.follow(user_id, question_id)

    def unfollow_question(self, user_id, question_id):
        repo = DiscussionFollowRepository()
        repo.unfollow(user_id, question_id)

    def swap_question_file(self, course_id, year, semester, moed, question_number, new_file):
        try:
            question_link = self._course_facade.get_link_to_question(course_id, year, semester, moed, question_number)

            if question_link is not None:
                self.fileManager.delete_file(question_link)

                if self.is_photo(new_file):
                    new_path = self.fileManager.save_photo_question_file(course_id, year, semester, moed, question_number, new_file)
                else:
                    new_path = self.fileManager.save_question_file_pdf(course_id, year, semester, moed, question_number, new_file)

                return json.dumps({
                    "status": "success",
                    "message": "Question file successfully swapped",
                    "has_link": True,
                    "link": new_path
                })

            return json.dumps({
                "status": "error",
                "message": "No existing question file to replace"
            })

        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": str(e)
            })

    def edit_question_details(self, old_course_id, old_year, old_semester, old_moed, old_question_number, new_course_id,
                              new_year, new_semester, new_moed, new_question_number):
        try:
            self.courseFacade.valid_question_parameters(new_course_id, new_year, new_semester, new_moed,
                                                        new_question_number)

            res, exam_id = self._course_facade.checkQuestionAvailability(new_course_id, new_year, new_semester,
                                                                         new_moed, new_question_number)
            parsed_result = json.loads(res)
            if parsed_result.get("status") == "success":
                question_old_path = self._course_facade.get_question_path(old_course_id, old_year, old_semester,
                                                                          old_moed, old_question_number)
                question_new_path = self.fileManager.move_question_file(question_old_path, new_course_id, new_year,
                                                                        new_semester, new_moed, new_question_number)
                solution_old_path = self._course_facade.get_answer_path(old_course_id, old_year, old_semester, old_moed,
                                                                        old_question_number)
                solution_new_path = ""
                if solution_old_path != "":
                    solution_new_path = self.fileManager.move_solution_file(solution_old_path, new_course_id, new_year,
                                                                            new_semester, new_moed, new_question_number)
                res = self._course_facade.edit_question_details(old_course_id, old_year, old_semester, old_moed,
                                                                old_question_number,
                                                                new_year, new_semester, new_moed, new_question_number,
                                                                exam_id, question_new_path, solution_new_path)
                if res:
                    same_exams = self.checkSameExams(old_course_id, old_year, old_semester, old_moed,
                                                     new_course_id, new_year, new_semester, new_moed)
                    if not same_exams:
                        questions_left, exam_id = self._course_facade.checkQuestionLeft(old_course_id, old_year,
                                                                                        old_semester, old_moed)
                        if not questions_left:
                            self.delete_exam(exam_id, old_course_id, old_year, old_semester, old_moed)

                    return json.dumps({
                        "status": "success",
                        "message": "אירעה שגיאה בעדכון נושאי השאלה"
                    })
                else:
                    return json.dumps({
                        "status": "error",
                        "message": "אירעה שגיאה בעדכון נושאי השאלה"
                    })
            else:
                return res
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": f"Error: {str(e)}"
            })

    def mark_notification_as_seen(self, notification_id):
        notification_repo = NotificationRepository()
        return notification_repo.mark_as_seen(notification_id)

    def appoint_system_manager(self,nominee_email, nominator_user_id):
        print(nominator_user_id)
        if self.userFacade.is_valid_email(nominee_email):
            user_nominee = self.userFacade.getUser_by_email(nominee_email)
            if user_nominee is not None:
                if user_nominee.user_id in self._system_managers:
                    return json.dumps({
                        "status": "error",
                        "message": " משתמש זה כבר הינו מנהל מערכת"
                        })
                user_nominator = self.userFacade.getUser_by_id(nominator_user_id)
                system_manager_repo = SystemManagersRepository()
                if not system_manager_repo.is_system_manager(user_nominee.user_id):
                    message = f"{user_nominator.get_first_name() + ' ' +user_nominator.get_last_name()} מעוניינ/ת לקדם אותך לתפקיד מנהל מערכת "
                    send_email = self._user_facade.should_send_notification(user_nominee.user_id, "AppointSystemManager")
                    self._notification_facade.send_notification(receiver_id=user_nominee.user_id, sender_id=nominator_user_id, message = message, isApproved=False,
                                                                link="",appoint_system_manager=True, appoint_course_manager=False, comment_to_following=False,
                    comment_to_comment=False, react_to_comment=False, remove_course_manager=False, send_email = send_email)
                    return json.dumps({
                    "status": "success",
                    "message": "The nomination request was sent successfully."
                })
                else:
                    return json.dumps({
                        "status": "error",
                        "message": " משתמש זה כבר הינו מנהל מערכת"
                        })
                    
            else:
                 return json.dumps({
                        "status": "error",
                        "message": " אימייל זה לא קיים במערכת"
                        })
        else:
            return json.dumps({
                        "status": "error",
                        "message": " נא להקליד אימייל חוקי"
                        })

    def appoint_course_manager(self,nominee_email, nominator_user_id, course_id):
        if self.userFacade.is_valid_email(nominee_email):
            user_nominee = self.userFacade.getUser_by_email(nominee_email)
            if user_nominee is not None:
                user_nominator = self.userFacade.getUser_by_id(nominator_user_id)
                course_manager_repo = CourseManagersRepository()
                if not course_manager_repo.is_exist(course_id,user_nominee.user_id):
                    course_repo = CourseRepository()
                    course = course_repo.get_course_by_id(course_id)
                    message = f"{user_nominator.get_first_name() + ' ' +user_nominator.get_last_name()} מעוניינ/ת לקדם אותך לתפקיד מנהל קורס, בקורס ״{course.name}״ {course_id} "
                    frontend_base_url = os.getenv("FRONTEND_BASE_URL", "http://localhost:3000")  # default for safety
                    course_link = f"{frontend_base_url}/course/{course_id}"
                    send_email = self._user_facade.should_send_notification(user_nominee.user_id, "AppointCourseManager")
                    self._notification_facade.send_notification(receiver_id=user_nominee.user_id, sender_id=nominator_user_id, message = message, isApproved=False,
                                                                link=course_link,appoint_system_manager=False, appoint_course_manager=True, comment_to_following=False,
                    comment_to_comment=False, react_to_comment=False, remove_course_manager=False, send_email=send_email)
                    return json.dumps({
                    "status": "success",
                    "message": "The nomination request was sent successfully."
                })
                else:
                    return json.dumps({
                        "status": "error",
                        "message": " משתמש זה כבר הינו מנהל קורס"
                        })
                    
            else:
                 return json.dumps({
                        "status": "error",
                        "message": " אימייל זה לא קיים במערכת"
                        })
        else:
            return json.dumps({
                        "status": "error",
                        "message": " נא להקליד אימייל חוקי"
                        })

    def remove_course_manager(self, remove_user_email, nominator_user_id, course_id):
        if self.userFacade.is_valid_email(remove_user_email):
            user_nominee = self.userFacade.getUser_by_email(remove_user_email)
            if user_nominee is not None:
                user_nominator = self.userFacade.getUser_by_id(nominator_user_id)

                is_manager = self._course_facade.is_course_manager(course_id, user_nominee.user_id)

                if is_manager:
                    manager_count = self._course_facade.get_course(course_id).get_course_manager_count()

                    if manager_count > 1:
                        self._course_facade.remove_manager_from_course(course_id, user_nominee.user_id)
                        course = self._course_facade.get_course(course_id)
                        message = f"{user_nominator.get_first_name()} {user_nominator.get_last_name()} הסיר/ת אותך מתפקיד מנהל קורס, בקורס ״{course.name}״ {course_id}"
                        frontend_base_url = os.getenv("FRONTEND_BASE_URL", "http://localhost:3000")
                        course_link = f"{frontend_base_url}/course/{course_id}"
                        send_email = self._user_facade.should_send_notification(user_nominee.user_id,
                                                                                "RemoveCourseManager")

                        self._notification_facade.send_notification(
                            receiver_id=user_nominee.user_id,
                            sender_id=nominator_user_id,
                            message=message,
                            isApproved=False,
                            link=course_link,
                            appoint_system_manager=False,
                            appoint_course_manager=False,
                            comment_to_following=False,
                            comment_to_comment=False,
                            react_to_comment=False,
                            remove_course_manager=True,
                            send_email=send_email
                        )

                        return json.dumps({
                            "status": "success",
                            "message": "The removal request was sent successfully."
                        })

                    else:
                        return json.dumps({
                            "status": "error",
                            "message": "משתמש זה הינו מנהל הקורס היחיד כרגע.\nנא למנות קודם כל מנהל קורס חדש"
                        })
                else:
                    return json.dumps({
                        "status": "error",
                        "message": " משתמש זה אינו מנהל קורס"
                    })
            else:
                return json.dumps({
                    "status": "error",
                    "message": " אימייל זה לא קיים במערכת"
                })
        else:
            return json.dumps({
                "status": "error",
                "message": " נא להקליד אימייל חוקי"
            })

    def disapprove_system_manager_appoint(self, notification_id, sender_id):
        notification_repo = NotificationRepository()
        try:
            reciever_id, message = notification_repo.get_notification_by_id_and_mark_as_seen(notification_id)
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": str(e)
            })

        if not reciever_id:
            return json.dumps({
                "status": "error",
                "message": "Notification not found"
            })

        user_sender = self.userFacade.getUser_by_id(sender_id)
        message = f"{user_sender.get_first_name()} {user_sender.get_last_name()} סירב/ה להצעה שלך להתמנות לתפקיד מנהל מערכת"

        self._notification_facade.send_notification(
            receiver_id=reciever_id,
            sender_id=sender_id,
            message=message,
            isApproved=False,
            link="",
            appoint_system_manager=False,
            appoint_course_manager=False,
            comment_to_following=False,
            comment_to_comment=False,
            react_to_comment=False,
            remove_course_manager=False
        )

        return json.dumps({
            "status": "success",
            "message": "הבקשה נדחתה בהצלחה"
        })

    def approve_system_manager_appoint(self, notification_id, sender_id):
        notification_repo = NotificationRepository()
        reciever_id, message = notification_repo.get_notification_by_id_and_mark_as_seen(notification_id)
        if not reciever_id:
            return json.dumps({
                "status": "error",
                "message": "Notification not found"
            })
        # reciever_id = notification.sender_user_id
        notification_repo.mark_as_seen_all_system_manager_appoints(sender_id)
        system_managers_repo = SystemManagersRepository()
        system_managers_repo.add_system_manager(sender_id)
        self._system_managers.add(sender_id)
        user_sender = self.userFacade.getUser_by_id(sender_id)
        message = f"{user_sender.get_first_name() + ' ' +user_sender.get_last_name()} הסכימ/ה להצעה שלך להתמנות לתפקיד מנהל מערכת "
        self._notification_facade.send_notification(receiver_id=reciever_id, sender_id=sender_id, message = message, isApproved=False,
                            link="",appoint_system_manager=False, appoint_course_manager=False, comment_to_following=False,
                            comment_to_comment=False, react_to_comment=False, remove_course_manager=False)
        return json.dumps({
        "status": "success",
        "message": "הבקשה נדחתה בהצלחה"
            })

    def disapprove_course_manager_appoint(self, notification_id, sender_id):
        notification_repo = NotificationRepository()
        try:
            reciever_id, _ = notification_repo.get_notification_by_id_and_mark_as_seen(notification_id)
        except Exception as e:
            return json.dumps({
                "status": "error",
                "message": str(e)
            })

        message = "הבקשה נדחתה."
        self._notification_facade.send_notification(
            receiver_id=reciever_id,
            sender_id=sender_id,
            message=message,
            isApproved=False,
            link="",
            appoint_system_manager=False,
            appoint_course_manager=False,
            comment_to_following=False,
            comment_to_comment=False,
            react_to_comment=False,
            remove_course_manager=False
        )

        return json.dumps({
            "status": "success",
            "message": message
        })

    def approve_course_manager_appoint(self, notification_id, sender_id):
        notification_repo = NotificationRepository()
        reciever_id, message = notification_repo.get_notification_by_id_and_mark_as_seen(notification_id)
        if not reciever_id:
            return json.dumps({
                "status": "error",
                "message": "Notification not found"
            })
        # reciever_id = notification.sender_user_id
        match = re.search(r'״(.+?)״\s+([\d.]+)', message)
        course_name = match.group(1)
        course_id = match.group(2)
        if not self._course_facade.is_course_manager(course_id,sender_id ):
            self._course_facade.add_manager_to_course(course_id, sender_id)
        if not self._user_facade.is_registerToCourse(course_id, sender_id):
            self._user_facade.registerToCourse(course_id, sender_id)
        user_sender = self.userFacade.getUser_by_id(sender_id)
        message = f"{user_sender.get_first_name() + ' ' +user_sender.get_last_name()} הסכימ/ה להצעה שלך להתמנות לתפקיד מנהל קורס, בקורס ״{course_name}״ {course_id} "
        self._notification_facade.send_notification(receiver_id=reciever_id, sender_id=sender_id, message = message, isApproved=False,
                            link="",appoint_system_manager=False, appoint_course_manager=False, comment_to_following=False,
                            comment_to_comment=False, react_to_comment=False, remove_course_manager=False)
        return json.dumps({
        "status": "success",
        "message": "הבקשה נדחתה בהצלחה"
            })

    def get_notification_settings(self, user_id):
        repo = NotificationsSettingRepository()
        return repo.get_settings_by_user_id(user_id)
    
    def update_notification_settings(self, user_id, settings_dict):
            return self._user_facade.update_notification_settings(user_id, settings_dict)
            
    def upload_profile_picture(self, user_id, file):
        try:
            profile_pic_path = self._file_manager.save_profile_picture(user_id, file)
            profile_pic_repo = ProfilePictureRepository()
            success =  profile_pic_repo.update_profile_pic(user_id, profile_pic_path) 
            if success:
                return profile_pic_path
        except Exception as e:
            raise Exception(f"Failed to upload profile picture: {str(e)}")

    def get_profile_picture_path(self, user_id):
        """
        Fetch the saved profile picture path for a given user.

        :param user_id: ID of the user
        :return: Relative path to the profile picture (str) or None if not found
        """
        try:
            profile_pic_repo = ProfilePictureRepository()
            return profile_pic_repo.get_path_by_user_id(user_id)
        except Exception as e:
            raise Exception(f"Error retrieving profile picture path: {str(e)}")

    def delete_profile_picture(self, user_id):
        succuess = self.fileManager.delete_profile_picture(user_id)
        if succuess:
            repo = ProfilePictureRepository()
            return repo.delete_pic(user_id)
    
    def get_course_managers(self, course_id):
        managers_id = self._course_facade.get_course_managers(course_id)
        res = []
        for manager_id in managers_id:
            full_name, email = self._user_facade.get_user_name_email(manager_id)
            res.append((full_name, email))
        return res 
    
    def get_system_managers(self):
        res = []
        for id in self._system_managers:
            full_name, email = self._user_facade.get_user_name_email(id)
            res.append((full_name, email))
        return res
        



# def edit_exam_year(self, course_id, year, semester, moed, new_year):
#     """Editing exam's year """
#     try:
#         self.courseFacade.edit_exam_year(course_id, year, semester, moed, new_year)
#         return "The exams' year was updated successfully."
#     except Exception as e:
#         raise Exception(f"Failed to edit exam's link {e}")
#
# def edit_exam_semester(self, course_id, year, semester, moed, new_semester):
#     """Editing exam's semester """
#     try:
#         self.courseFacade.edit_exam_semester(course_id, year, semester, moed, new_semester)
#         return "The exams' semester was updated successfully."
#     except Exception as e:
#         raise Exception(f"Failed to edit exam's link {e}")
#
# def edit_exam_moed(self, course_id, year, semester, moed, new_moed):
#     """Editing exam's moed """
#     try:
#         self.courseFacade.edit_exam_moed(course_id, year, semester, moed, new_moed)
#         return "The exams' moed was updated successfully."
#     except Exception as e:
#         raise Exception(f"Failed to edit exam's link {e}")

    # def delete_comment(self, comment_id):
    #     """
    #     Deletes a comment from the question, ensuring all related data is removed.
    #     """
    #     try:
    #         # Get the course and ensure it exists
    #         # question_id, question_details = self.courseFacade.checkExistQuestion(course_id, year, semester, moed, question_number)
    #         # if not question_id:
    #         #     raise Exception(
    #         #         f"Question {question_number} does not exist in the exam for course {course_id}, "
    #         #         f"Year: {year}, Semester: {semester}, Moed: {moed}."
    #         #     )
    #         reactions_repo = ReactionRepository()
    #         reactions_repo.delete_reactions_by_comment_id(comment_id)
    #         comment_repo = CommentRepository()
    #         replies_to_comment = comment_repo.get_replies_by_comment_id(comment_id)
    #         comment_prev = comment_repo.get_prev_id_by_comment_id(comment_id)
    #         comment_repo.update_replies_prev_id(replies_to_comment, comment_prev)
    #         comment_repo.delete_comment(comment_id)
    #
    #
    #     except Exception as e:
    #         raise Exception(f"Error in NegevNerds delete_question: {str(e)}")

    # def add_comment(self, course_id, year, semester, moed, question_number, writer_name, writer_id,prev_id,
    #                 comment_text):
    #     """
    #             Add a comment to a question discussion.
    #     """
    #     try:
    #         comment_writers = self.courseFacade.add_comment(course_id=course_id, year=year, semester=semester,
    #                                                        moed=moed, question_number=question_number,
    #                                                       writer_name=writer_name,
    #                                                       writer_id=writer_id,prev_id=prev_id, comment_text=comment_text)
    #         # for commenter in comment_writers:
    #         #     self._notification_facade.send_notification(sender_id=writer_id, receiver_id=commenter,message=f"{writer_id}- add comment in discussion which you take part in the past", need_approval=False)
    #         return "CommentData added successfully."
    #     except (CourseIsNotExist, ExamIsNotExist, QuestionNotFound) as e:
    #         raise e
    #     except Exception as e:
    #         raise Exception(f"Failed to add comment: {e}")

    # def search_free_text(self , text, course_id = None):
    #     if course_id is None:
    #         search_dtos = self._pdfFacade.search_free_text(text=text)
    #         ques_dtos = self.courseFacade.get_questions_dto_by_search_dtos(dtos=search_dtos)
    #         return ques_dtos
    #     else:
    #         ids = self._pdfFacade.search_free_text_from_course(text=text, course_id=course_id)
    #         dtos = self.courseFacade.get_questions_dto_by_ids(ids, course_id)
    #         return dtos

