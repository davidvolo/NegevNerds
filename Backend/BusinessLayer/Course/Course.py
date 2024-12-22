from Backend.BusinessLayer.Course.Exam import Exam
from Backend.BusinessLayer.Util.Exceptions import *
from Backend.BusinessLayer.Course.enums import Semester, Moed
from Backend.DataLayer.Course.CourseRepository import CourseRepository
from Backend.DataLayer.CourseManagers.CourseManagersRepository import CourseManagersRepository
from Backend.DataLayer.CourseTopics.CourseTopicsRepository import CourseTopicsRepository
from Backend.DataLayer.Exam.ExamRepository import ExamRepository


class Course:
    def __init__(self, course_id, name, course_topics=None):
        self.course_id = course_id
        self.name = name
        self.course_topics = course_topics if course_topics is not None else set()  # Default to an empty list
        self.exams = {}  # Dictionary to store exams by years
        self.managers = set() # Dictionary to store managers with manager_id as key
        self.students = []  # List of students for the course

    @classmethod
    def create(cls, course_id, name, course_topics=None):
        """
        Class method to create a new user and save to database
        Returns:
            User: Newly created user instance
        """
        course = cls(
            course_id=course_id,
            course_topics=course_topics,
            name=name
        )
        course_repository = CourseRepository()
        course_repository.add_course(course)
        topics_repo = CourseTopicsRepository()

        for topic in course_topics:
            if not topics_repo.is_exist(topic=topic, course_id=course_id):
                topics_repo.add_Topic_to_course(course_id=course_id, topic=topic)
        return course

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

    def get_questions_by_specific(self, year=None, semester=None, moed=None, question_number=None):
        """Get specific questions."""
        print ("in course")
        question_dtos = []
        if year is None:
            all_exams = self.get_all_exams()
            for exam in all_exams:
                # Only include the questions that match the specific number
                question_dtos.extend(exam.get_questions_by_specific(question_number))
        else:
            if year in self.exams:
                year_exams = self.exams[year]
                if semester is None:
                    for exam in year_exams:
                        question_dtos.extend(exam.get_questions_by_specific(question_number))
                elif semester is not None and moed is None:
                    for exam in year_exams:
                        if exam.semester == semester:
                            question_dtos.extend(exam.get_questions_by_specific(question_number))
                else:
                    exam = self.get_exam(year, semester, moed)
                    if exam is not None:
                        question_dtos.extend(exam.get_questions_by_specific(question_number))
        return question_dtos

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
        exam_repo = ExamRepository()
        exam= exam_repo.get_exam_by_date(year, semester, moed)
        return exam
        # if raise_exception:
        #     raise ExamIsNotExist(year, semester, moed)

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
            course_repo = CourseRepository()
            course_repo.update_course(self)
        else:
            raise UserIsNotRegisterToCourse()

    def generate_exam_id(self):
        return len(self.exams) + 1

    def add_exam(self, link, year, semester, moed):
        """
        Adds an exam to the course.
        """
        # Convert semester and moed to Enum
        semester = Semester(semester)
        moed = Moed(moed)

        exam = self.get_exam(year, semester, moed, raise_exception=False)
        if exam is None:
            exam_id = self.generate_exam_id()
            exam = Exam.create(exam_id=exam_id, course_id=self.course_id, link=link, year=year, semester=semester, moed=moed)

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

    def exist_manager(self, manager_id):

        manager_repo = CourseManagersRepository()
        return manager_id in self.managers or manager_repo.is_exist(user_id=manager_id, course_id=self.course_id)

    def add_manager(self, manager_id):
        """Adds a manager to the course."""
        if not self.exist_manager(manager_id):
            self.managers.add(manager_id)
            manager_repo = CourseManagersRepository()
            manager_repo.add_manager_to_course(user_id=manager_id, course_id=self.course_id)
        else:
            raise ManagerAlreadyExists(manager_id)

    def remove_manager(self, manager_id):
        """Removes a manager from the course."""
        if self.exist_manager(manager_id):
            self.managers.remove(manager_id)
            manager_repo = CourseManagersRepository()
            manager_repo.remove_manager_from_course(user_id=manager_id, course_id=self.course_id)
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
        
        
    # def check_valid_question(self, course_id,year,semester, moed, question_number,pdf_question):
    #     currExam = self.get_exam(year,semester,moed)
    #     if currExam is None:
    #         self.add_exam(self.name,pdf_question,  year, semester, moed)
    #         return True
    #     else:
    #         if currExam.semester == semester and currExam.moed == moed:
    #             return currExam.check_add_question_possibility(year, semester, moed, question_number,pdf_question )
    
    # def check_valid_question(self, course_id, year, semester, moed, question_number, pdf_question):
    #     # Get or create the exam
    #     currExam = self.get_exam(year, semester, moed)
    #     if currExam is None:
    #         # Create the exam if it doesn't exist
    #         self.add_exam(self.name, pdf_question, year, semester, moed)
    #         return True
    #     else:
    #         # Validate the question within the exam
    #         # if currExam.semester == semester and currExam.moed == moed:
    #         #     return currExam.check_add_question_possibility(year, semester, moed, question_number, pdf_question)
    #         # raise ValueError(f"No matching exam for semester {semester} and moed {moed}.")
    #         normalized_semester = Semester.get(currExam.semester, currExam.semester)
    #         normalized_moed = Moed.get(currExam.moed, currExam.moed)

    #         if normalized_semester == semester and normalized_moed == moed:
    #             return currExam.check_add_question_possibility(year, semester, moed, question_number, pdf_question)
    #         else:
    #             raise ValueError(f"Exam found, but mismatched semester {semester} or moed {moed}.")

    def check_valid_question(self, year, semester, moed, question_number, pdf_question):
        # Get or create the exam
        currExam = self.get_exam(year, semester, moed)
        if currExam is None:
            # Create the exam if it doesn't exist
            self.add_exam(pdf_question, year, semester, moed)
            return True
        else:
            # Compare normalized values
            if currExam.semester == semester and currExam.moed == moed:
                return currExam.check_add_question_possibility(year, semester, moed, question_number, pdf_question)
            else:
                raise ValueError(f"Exam found, but mismatched semester {semester} or moed {moed}.")

            
                
    def add_question(self, year, semester, moed, question_number,is_american,question_topics,pdf__question_path, pdf__answer_path):
        exam = self.get_exam(year, semester, moed)
        return exam.add_question(question_number,is_american,question_topics, pdf__question_path, pdf__answer_path)

