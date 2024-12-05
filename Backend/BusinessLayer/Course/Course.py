from Backend.BusinessLayer.Course.Exam import Exam
from Backend.BusinessLayer.Util.Exceptions import *


class Course:
    def __init__(self, course_id, name, syllabus):
        self.id = course_id
        self.name = name
        self.syllabus = syllabus
        self.exams = {}  # Dictionary to store exams with exam_id as key
        self.managers = {}  # Dictionary to store managers with manager_id as key
        self.students = []  # List of students for the course

    # Getters
    def get_id(self):
        return self.id

    def get_name(self):
        return self.name

    def get_syllabus(self):
        return self.syllabus

    def get_exam(self, year, semester, moed):
        """Fetch an exam by ID."""
        if self.exams[year] in self.exams:
            for exam in self.exams[year]:
                if exam.semester == semester and exam.moed == moed:
                    return exam
        else:
            raise ExamIsNotExist(year, semester, moed)

    def get_managers(self):
        return self.managers

    def get_students(self):
        return self.students

    # Methods
    def add_student(self, user_id):
        """Adds a student to the course."""
        if user_id not in self.students:
            self.students.append(user_id)
        else:
            raise UserAlreadyRegisterToCourse()

    def remove_student(self, user_id):
        """Removes a student from the course."""
        if user_id in self.students:
            self.students.remove(user_id)
        else:
            raise UserIsNotRegisterToCourse()

    def add_exam(self,exam_id, course_name, link, year, semester, moed):
        """Adds an exam to the course."""
        if self.exams[year] not in self.exams:
            exam = Exam(exam_id, course_name, link, year, semester, moed)
            self.exams[exam_id] = exam
        else:
            raise ExamAlreadyExists(exam_id)

    def remove_exam(self, year, semester, moed):
        """Removes an exam from the course."""
        exam = self.get_exam(year, semester, moed)
        if exam is not None:
            self.exams[year].remove(exam)
        else:
            raise ExamIsNotExist(year, semester, moed)

    def add_manager(self, manager_id, manager):
        """Adds a manager to the course."""
        if manager_id not in self.managers:
            self.managers[manager_id] = manager
        else:
            raise ManagerAlreadyExists(manager_id)

    def remove_manager(self, manager_id):
        """Removes a manager from the course."""
        if manager_id in self.managers:
            del self.managers[manager_id]
        else:
            raise ManagerIsNotExist(manager_id)

    def add_question(self, exam_id, year, question_id, semester, moed, question_number, is_american, link_to_question):
        """Delegate question addition to the specified Exam."""
        exam = self.get_exam(year,semester,moed)
        exam.add_question(year, question_id, semester, moed, question_number, is_american, link_to_question)

    def remove_question(self, year, semester, moed, question_id):
        """Delegate question removal to the specified Exam."""
        exam = self.get_exam(year, semester, moed)
        exam.remove_question(question_id)

    def add_comment(self, year, semester, moed, question_id, comment_id, writer_name, prev_id, comment_text):
        """Delegate comment addition to the specified Exam and Question."""
        exam = self.get_exam(year, semester, moed)
        exam.add_comment(question_id, comment_id, writer_name, prev_id, comment_text)

    def remove_comment(self, year, semester, moed, question_id, comment_id):
        """Delegate comment removal to the specified Exam and Question."""
        exam = self.get_exam(year, semester, moed)
        exam.remove_comment(question_id, comment_id)


