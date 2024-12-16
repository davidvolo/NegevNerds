from Backend.BusinessLayer.Course.Exam import Exam
from Backend.BusinessLayer.Util.Exceptions import *
from Backend.BusinessLayer.Course.enums import Semester, Moed


class Course:
    def __init__(self, course_id, name, course_topics):
        self.course_id = course_id
        self.name = name
        self.course_topics = course_topics if course_topics is not None else set()  # Default to an empty list
        self.exams = {}  # Dictionary to store exams by years
        self.managers = set() # Dictionary to store managers with manager_id as key
        self.students = []  # List of students for the course

    # Getters
    def get_id(self):
        return self.course_id

    def get_name(self):
        return self.name

    def get_syllabus(self):
        return self.syllabus

    def get_topics(self):
        return self.course_topics

    def get_all_exams(self):
        """Retrieve all exams from the exams dictionary."""
        all_exams = []
        for year_exams in self.exams.values():
            for exam in year_exams:
                all_exams.append(exam)
        return all_exams

    def get_question(self, year, semester, moed, question_id):
        """get a specific question."""
        exam = self.get_exam(year, semester, moed)
        if exam is None:
            raise ExamIsNotExist
        return exam.get_question(question_id)

    def get_questions_by_keywords(self, keywords):
        """get questions by keywords."""
        questions = []
        for exam in self.get_all_exams():
            questions = questions + exam.get_questions_by_keywords(keywords)
        return questions

    def get_exam(self, year, semester, moed, raise_exception=True):
        """
        Retrieves a specific exam by year, semester, and moed.
        Raises an exception if not found, unless raise_exception is False.
        """
        # Convert semester and moed to Enum
        semester = Semester(semester)
        moed = Moed(moed)

        if year in self.exams:
            for exam in self.exams[year]:
                if exam.semester == semester and exam.moed == moed:
                    return exam

        # if raise_exception:
        #     raise ExamIsNotExist(year, semester, moed)
        return None

    # This handles cases where the user didn't specify 'semester' or 'moed' in the search.
    def get_exams(self, year: int, semester=None, moed=None):
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

    def generate_exam_id(self):
        return len(self.exams) + 1

    def add_exam(self, course_name, link, year, semester, moed):
        """
        Adds an exam to the course.
        """
        # Convert semester and moed to Enum
        semester = Semester(semester)
        moed = Moed(moed)

        # Check if exam already exists
        exam = self.get_exam(year, semester, moed, raise_exception=False)
        if exam is None:
            exam_id = self.generate_exam_id()
            exam = Exam(exam_id, course_name, link, year, semester, moed)

            if year not in self.exams:
                self.exams[year] = []
            self.exams[year].append(exam)
        else:
            raise ExamAlreadyExists(f"Exam with year={year}, semester={semester}, moed={moed} already exists.")

    def remove_exam(self, year, semester, moed):
        """Removes an exam from the course."""
        exam = self.get_exam(year, semester, moed)
        if exam is not None:
            self.exams[year].remove(exam)
        else:
            raise ExamIsNotExist(year, semester, moed)

    def add_manager(self, manager_id):
        """Adds a manager to the course."""
        if manager_id not in self.managers:
            self.managers.add(manager_id)
        else:
            raise ManagerAlreadyExists(manager_id)

    def remove_manager(self, manager_id):
        """Removes a manager from the course."""
        if manager_id in self.managers:
            self.managers.remove(manager_id)
        else:
            raise ManagerIsNotExist(manager_id)

    def edit_exam_year(self, year, semester, moed, new_year):
        exam = self.get_exam(year, semester, moed)
        if exam is not None:
            self.exams[year].remove(exam)
            if not self.exams[year]:  # Clean up empty lists
                del self.exams[year]
            exam.edit_year(new_year)
            # Add the exam to the new year's list
            if new_year not in self.exams:
                self.exams[new_year] = []
            self.exams[new_year].append(exam)
        else:
            raise ExamIsNotExist(year, semester, moed)
