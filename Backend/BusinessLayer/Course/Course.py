from Backend.BusinessLayer.Course.Exam import Exam
from Backend.BusinessLayer.Util.Exceptions import *


class Course:
    def __init__(self, course_id, name, syllabus, course_topics):
        self.id = course_id
        self.name = name
        self.syllabus = syllabus
        self.course_topics = course_topics if course_topics is not None else []  # Default to an empty list
        self.exams = {}  # Dictionary to store exams by years
        self.managers = {}  # Dictionary to store managers with manager_id as key
        self.students = []  # List of students for the course

    # Getters
    def get_id(self):
        return self.id

    def get_name(self):
        return self.name

    def get_syllabus(self):
        return self.syllabus
    
    def get_topics(self):
        return self.course_topics
    
    # to delete:
    # def get_all_exams(self):
    #     """Retrieve all exam IDs from the exams dictionary."""
    #     exams_id = []
    #     for exam_id in self.exams.keys():  # Explicitly iterating over the keys
    #         exams_id.append(exam_id)
    #     return exams_id
    
    def get_all_exams(self):
        """Retrieve all exams from the exams dictionary."""
        all_exams = []
        for year_exams in self.exams.values():
            for exam in year_exams:
                all_exams.append(exam)
        return all_exams

    def get_question(self, year, semester, moed, question_id):
        """get a specific question."""
        return self.get_exam(year, semester, moed).get_question(question_id)

    def get_questions_by_keywords(self, keywords):
        """get questions by keywords."""
        questions = []
        for exam in self.get_all_exams:
            questions = questions + exam.get_questions_by_keywords(keywords)
        return questions

    def get_exam(self, year, semester, moed):
        """get a specific exam."""
        if self.exams[year] in self.exams:
            for exam in self.exams[year]:
                if exam.semester == semester and exam.moed == moed:
                    return exam
        raise ExamIsNotExist(year, semester, moed)

    # This handles cases where the user didn't specify 'semester' or 'moed' in the search.
    def get_exams(self, year : int, semester=None, moed=None):
        """Fetch exams by year, and optionally filter by semester and moed."""
        exams = []
        
        if year in self.exams:
            # Iterate through exams for the specified year
            for exam in self.exams[year]:
                # Case 1: Neither semester nor moed specified
                if semester is None and moed is None:
                    exams.append(exam)
                # Case 2: Only moed specified
                elif semester is None and moed is not None:
                    if exam.moed == moed:
                        exams.append(exam)
                # Case 3: Only semester specified
                elif semester is not None and moed is None:
                    if exam.semester == semester:
                        exams.append(exam)
                # Case 4: Both semester and moed specified
                elif exam.semester == semester and exam.moed == moed:
                    exams.append(exam)
        else:
            raise ExamIsNotExist(year, semester, moed)
        
        return exams


    def get_managers(self):
        return self.managers

    def get_students(self):
        return self.students

    # Setters
    def set_syllabus(self, syllabus):
        self.syllabus = syllabus
    
    # Methods
    def add_course_topic(self, course_topic):
        """Add a topic to the course."""
        if course_topic not in self.course_topics:
            self.course_topics.append(course_topic)
        else:
            raise TopicAlreadyExist(course_topic)

    def remove_course_topic(self, course_topic):
        """Remove a topic from the course."""
        if course_topic in self.course_topics:
            self.course_topics.remove(course_topic)
        else:
            raise TopicNotFound(course_topic)
    
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

    def add_question(self, exam_id, year, question_id, semester, moed, question_number, question_topic, is_american, link_to_question):
        """Delegate question addition to the specified Exam."""
        exam = self.get_exam(year,semester,moed)
        if question_topic not in self.course_topics:
            raise TopicNotFound(question_topic)
        else:
            exam.add_question(year, question_id, semester, moed, question_number, question_topic, is_american, link_to_question)

    def remove_question(self, year, semester, moed, question_id):
        """Delegate question removal to the specified Exam."""
        exam = self.get_exam(year, semester, moed)
        exam.remove_question(question_id)

    def add_topic_to_question(self, year, semester, moed, question_id, question_topic):
        if question_topic not in self.course_topics:
            raise TopicNotFound(question_topic)
        else:
            self.get_question(year, semester, moed, question_id).add_question_topic(question_topic)
            
    def remove_topic_from_question(self, year, semester, moed, question_id, question_topic):
        if question_topic not in self.course_topics:
            raise TopicNotFound(question_topic)
        else:
            self.get_question(year, semester, moed, question_id).remove_question_topic(question_topic)

    def add_comment(self, year, semester, moed, question_id, comment_id, writer_name, prev_id, comment_text):
        """Delegate comment addition to the specified Exam and Question."""
        exam = self.get_exam(year, semester, moed)
        exam.add_comment(question_id, comment_id, writer_name, prev_id, comment_text)

    def remove_comment(self, year, semester, moed, question_id, comment_id):
        """Delegate comment removal to the specified Exam and Question."""
        exam = self.get_exam(year, semester, moed)
        exam.remove_comment(question_id, comment_id)

    def edit_exam_course_name(self,year, semester, moed, new_course_name):
        exam = self.get_exam(year,semester,moed)
        exam.edit_course_name(new_course_name)
    
    def edit_exam_link(self,year, semester, moed, new_link):
        exam = self.get_exam(year,semester,moed)
        exam.edit_link(new_link)

    def edit_exam_year(self,year, semester, moed, new_year):
        exam = self.get_exam(year,semester,moed)
        exam.edit_link(new_year)
    
    def edit_exam_semester(self,year, semester, moed, new_semester):
        exam = self.get_exam(year,semester,moed)
        exam.edit_semester(new_semester)
    
    def edit_exam_moed(self,year, semester, moed, new_moed):
        exam = self.get_exam(year,semester,moed)
        exam.edit_moed(new_moed)

