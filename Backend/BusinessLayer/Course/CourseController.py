from Backend.BusinessLayer.Course.Course import Course
from Backend.BusinessLayer.Util.Exceptions import *


class CourseController:
    def __init__(self):
        self.courses = {} #courseId, Course
        
    
    def register_to_course(self, courseId, userId):
        course = self.get_course(courseId)
        if course is not None:
            self.courses[courseId].addStudent(userId)
            
    def remove_student_from_course(self, course_id, user_id):
        """Removes a student from the course."""
        course = self.courses.get(course_id)
        if course:
            course.removeStudent(user_id)
        else:
            raise CourseIsNotExist(course_id)

    def open_course(self, course_id, name, syllabus):
        """Opens a new course"""

        if course_id in self.courses:
            raise CourseAlreadyExists(course_id)
        self.courses[course_id] = Course(course_id, name, syllabus)

    def get_course(self, course_id):
        """
        Retrieves a course by its ID.
        """
        course = self.courses.get(course_id)
        if not course:
            raise CourseIsNotExist(course_id)
        return course

    def add_exam_to_course(self, course_id , course_name, link, year, semester, moed):
        """
        Adds an exam to a course.
        """
        course = self.get_course(course_id)
        course.add_exam(course_name, link, year, semester, moed)

    def remove_exam_from_course(self, course_id,  year, semester, moed):
        """
        Removes an exam from a course.
        """
        course = self.get_course(course_id)
        course.remove_exam( year, semester, moed)

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

    def add_question(self, course_id,  year, question_id, semester, moed, question_number, is_american, link_to_question):
        """
        Delegates question addition to the specified Exam.
        """
        course = self.get_course(course_id)
        course.add_question(year, question_id, semester, moed, question_number, is_american, link_to_question)

    def remove_question(self, course_id,  year, semester, moed, question_id):
        """
        Delegates question removal to the specified Exam.
        """
        course = self.get_course(course_id)
        course.remove_question( year, semester, moed, question_id)

    def add_comment(self, course_id, year, semester, moed, question_id, comment_id, writer_name, prev_id, comment_text):
        """
        Delegates comment addition to the specified Exam and Question.
        """
        course = self.get_course(course_id)
        course.add_comment( year, semester, moed, question_id, comment_id, writer_name, prev_id, comment_text)

    def remove_comment(self,course_id, year, semester, moed, question_id, comment_id):
        """
        Delegates comment removal to the specified Exam and Question.
        """
        course = self.get_course(course_id)
        course.remove_comment( year, semester, moed, question_id, comment_id)

    def sort_exams(self,exams):
        """Sort exams by year (descending), semester (ascending), and moed (ascending)."""
        return sorted(
            exams,
            key=lambda exam: (-exam.get("year", 0), exam.get("semester", ""), exam.get("moed", ""))
        )


    def search_exam_by_specifics(self, course_id, year : int, semester=None, moed=None):
        """
        Retrieves all exams for a course  in spefici year and optionally filters by semester and moed.

        :param course_id: The ID of the course.
        :param year: Optional filter by year.
        :param semester: Optional filter by semester.
        :param moed: Optional filter by moed.
        :return: List of exams matching the criteria.
        """
        course = self.get_course(course_id)
        exams = course.get_exams(year,semester,moed)  # Assuming Course class has this method

        sorted_exmas = self.sort_exams(exams)
        
        return sorted_exmas
    
    def search_all_course_exmas(self, course_id):
        """
        Retrieves all exams for a specifiv course

        :param course_id: The ID of the course.
        :return: List of exams matching the criteria.
        """
        course = self.get_course(course_id)
        exams = course.get_all_exams()  # Assuming Course class has this method
        sorted_exmas = self.sort_exams(exams)
        
        return sorted_exmas
    
    def edit_exam_course_name(self, course_id, year, semester, moed, new_course_name):
        course = self.get_course(course_id)
        course.edit_exam_course_name(year, semester, moed, new_course_name)
    
    def edit_exam_link(self, course_id, year, semester, moed, new_link):
        course = self.get_course(course_id)
        course.edit_exam_link(year, semester, moed, new_link)
        
    def edit_exam_year(self, course_id, year, semester, moed, new_year):
        course = self.get_course(course_id)
        course.edit_exam_year(year, semester, moed, new_year)

    def edit_exam_semester(self, course_id, year, semester, moed, new_semester):
        course = self.get_course(course_id)
        course.edit_exam_semester(year, semester, moed, new_semester)

    def edit_exam_moed(self, course_id, year, semester, moed, new_moed):
        course = self.get_course(course_id)
        course.edit_exam_moed(year, semester, moed, new_moed)
