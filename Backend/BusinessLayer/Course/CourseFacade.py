from Backend.BusinessLayer.Course.Course import Course
from Backend.BusinessLayer.Util.Exceptions import *
from Backend.DataLayer.CourseDTO import CourseDTO
import re


class CourseFacade:
    _instance = None  # Class-level attribute to hold the single instance

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'courses'):
            self.courses = {}  # courseId, Course

    """--------------course functionality--------------"""

    def register_to_course(self, course_id, user_id):
        course = self.get_course(course_id)
        if course is not None:
            course.add_student(user_id)

    def remove_student_from_course(self, course_id, user_id):
        """Removes a student from the course."""
        course = self.courses.get(course_id)
        if course:
            course.removeStudent(user_id)
        else:
            raise CourseIsNotExist(course_id)
    

    def open_course(self, course_id, name, course_topics):
        """Opens a new course"""

        course = Course(course_id, name, course_topics)
        self.courses[course_id] = course

    
    def open_course_possibility(self, course_id):
        """Opens a new course"""

        if course_id in self.courses:
            raise CourseAlreadyExists(course_id)
        
        if not self.is_valid_courseID(course_id):
            raise InvalidCourseIdFormat(course_id)

        return True

    def remove_course(self, course_id):
        """Remove an existing course along with its folder."""
        if course_id in self.courses:
            del self.courses[course_id]
        else:
            raise CourseIsNotExist(course_id)

    def get_course(self, course_id):
        """
        Retrieves a course by its ID.
        """
        course = self.courses[course_id]
        if not course:
            raise CourseIsNotExist(course_id)
        return course

    def set_syllabus_of_course(self, course_id, syllabus):
        """Set syllabus of an existing course"""

        if course_id in self.courses.keys():
            self.get_course(course_id).set_syllabus(syllabus)
        else:
            raise CourseIsNotExist(course_id)

    def is_course_manager(self, course_id, user_id):
        """Checks if the user is a manager of the given course."""
        course = self.get_course(course_id)
        return user_id in course.managers

    def add_manager_to_course(self, course_id, manager_id):
        """
        Adds a manager to a course.

        :param course_id: The ID of the course.
        :param manager_id: The ID of the manager to add.
        """
        course = self.get_course(course_id)
        course.add_manager(manager_id)

    def remove_manager_from_course(self, course_id, manager_id):
        """
        Removes a manager from a course.
        """
        course = self.get_course(course_id)
        course.remove_manager(manager_id)

    def add_course_topic(self, course_id, course_topic):
        course = self.get_course(course_id)
        course.add_course_topic(course_topic)

    def remove_course_topic(self, course_id, course_topic):
        course = self.get_course(course_id)
        course.remove_course_topic(course_topic)

    """--------------exams functionality--------------"""

    def add_exam_to_course(self, course_id, course_name, link, year, semester, moed):
        """
        Adds an exam to a course.
        """
        course = self.get_course(course_id)
        course.add_exam(course_name, link, year, semester, moed)

    def remove_exam_from_course(self, course_id, year, semester, moed):
        """
        Removes an exam from a course.
        """
        course = self.get_course(course_id)
        course.remove_exam(year, semester, moed)

    def sort_exams(self, exams):
        """Sort exams by year (descending), semester (ascending), and moed (ascending)."""
        return sorted(
            exams,
            key=lambda exam: (-exam.get("year", 0), exam.get("semester", ""), exam.get("moed", ""))
        )

    def search_exam_by_specifics(self, course_id, year: int, semester=None, moed=None):
        """
        Retrieves all exams for a course in specific year and optionally filters by semester and moed.

        :param course_id: The ID of the course.
        :param year: Optional filter by year.
        :param semester: Optional filter by semester.
        :param moed: Optional filter by moed.
        :return: List of exams matching the criteria.
        """
        course = self.get_course(course_id)
        exams = course.get_exams(year, semester, moed)  # Assuming Course class has this method

        sorted_exams = self.sort_exams(exams)

        return sorted_exams
    
    def is_valid_courseID(self,courseId):
        """
        Validates if a course ID is in the correct format: xxx.x.xxxx
        where x is a digit.

        Args:
            courseId (str): The course ID to validate.

        Returns:
            bool: True if valid, False otherwise.
        """
        pattern = r"^\d{3}\.\d\.\d{4}$"
        return bool(re.match(pattern, courseId))

    def search_all_course_exams(self, course_id):
        """
        Retrieves all exams for a specific course

        :param course_id: The ID of the course.
        :return: List of exams matching the criteria.
        """
        course = self.get_course(course_id)
        exams = course.get_all_exams()  # Assuming Course class has this method
        sorted_exams = self.sort_exams(exams)

        return sorted_exams

    def edit_exam_course_name(self, course_id, year, semester, moed, new_course_name):
        course = self.get_course(course_id)
        course.get_exam(year, semester, moed).edit_course_name(new_course_name)

    def edit_exam_link(self, course_id, year, semester, moed, new_link):
        course = self.get_course(course_id)
        course.get_exam(year, semester, moed).edit_link(new_link)

    def edit_exam_year(self, course_id, year, semester, moed, new_year):
        course = self.get_course(course_id)
        course.edit_exam_year(year, semester, moed, new_year)

    def edit_exam_semester(self, course_id, year, semester, moed, new_semester):
        course = self.get_course(course_id)
        course.get_exam(year, semester, moed).edit_semester(new_semester)

    def edit_exam_moed(self, course_id, year, semester, moed, new_moed):
        course = self.get_course(course_id)
        course.get_exam(year, semester, moed).edit_moed(new_moed)

    """--------------question functionality--------------"""

    def add_question(self, course_id, year, semester, moed, questionDTO):
        """
        Delegates question addition to the specified Exam.
        """
        course = self.get_course(course_id)
        currExam = course.get_exam(year, semester,moed)
        if currExam is None:
            self.add_exam_to_course(course_id,course.get_name(), None , year, semester, moed)
        course.get_exam(year, semester, moed).add_question(questionDTO)

    def remove_question(self, course_id, year, semester, moed, question_number):
        """
        Delegates question removal to the specified Exam.
        """
        course = self.get_course(course_id)
        course.get_exam(year, semester, moed).remove_question(question_number)

    def add_topic_to_question(self, course_id, year, semester, moed, question_number, question_topic):
        course = self.get_course(course_id)
        course.get_exam(year, semester, moed).get_question(question_number).add_topic_to_question(question_topic)

    def remove_topic_from_question(self, course_id, year, semester, moed, question_number, question_topic):
        course = self.get_course(course_id)
        course.get_exam(year, semester, moed).get_question(question_number).remove_topic_from_question(question_topic)




    def search_question_by_specifics(self, course_id, year, semester, moed, question_id):
        course = self.get_course(course_id)
        return course.get_question(year, semester, moed, question_id)

    def get_questions_by_keywords(self, course_id, keywords):
        course = self.get_course(course_id)
        return course.get_questions_by_keywords(keywords)

    """--------------comment functionality--------------"""

    def add_comment(self, course_id, year, semester, moed, question_number, comment_id, writer_name, prev_id, comment_text):
        """
        Delegates comment addition to the specified Exam and Question.
        """
        course = self.get_course(course_id)
        course.get_exam(year, semester, moed).get_question(question_number).add_comment(comment_id, writer_name, prev_id, comment_text)

    def remove_comment(self, course_id, year, semester, moed, question_number, comment_id):
        """
        Delegates comment removal to the specified Exam and Question.
        """
        course = self.get_course(course_id)
        course.get_exam(year, semester, moed).get_question(question_number).remove_comment(comment_id)

    def get_all_courses(self):
        course_list = []
        for course in self.courses.values():
            course_list.append(CourseDTO(course=course))
        return course_list

    def get_course_DTO(self, course_id):
        if self.get_course(course_id) is not None:
            return CourseDTO(self.courses[course_id])
        return None

    def get_courses_DTO(self, courses_ids):
        dtos = []
        for course_id in courses_ids:
            course = self.get_course(course_id)
            if course is not None:
                course_dto = CourseDTO(course_id, course.get_name())
                dtos.append(course_dto)
        return dtos

    def get_course_topics(self, course_id):
        if self.get_course(course_id) is None:
            return None
        else:
            return self.get_course(course_id).get_topics()
