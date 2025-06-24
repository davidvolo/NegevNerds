import threading

import numpy as np
import json
from Backend.BusinessLayer.Course.Exam import Exam
from Backend.BusinessLayer.Util.Exceptions import *
from Backend.BusinessLayer.Course.enums import Semester, Moed
from Backend.DataLayer.CourseData.CourseRepository import CourseRepository
from Backend.DataLayer.CourseManagers.CourseManagersRepository import CourseManagersRepository
from Backend.DataLayer.ExamData.ExamRepository import ExamRepository
from Backend.DataLayer.CourseTopics.CourseTopicsRepository import CourseTopicsRepository
from Backend.BusinessLayer.Util.LLMutil import LLMutil






# tokenizer = AutoTokenizer.from_pretrained("BAAI/bge-reranker-v2-m3")
# model = AutoModelForSequenceClassification.from_pretrained("BAAI/bge-reranker-v2-m3")


class Course:
    def __init__(self, course_id, name, course_topics=None):
        self.course_id = course_id
        self.name = name
        self.course_topics = course_topics if course_topics is not None else set()  # Default to an empty list
        self.exams = {}  # Dictionary to store exams by years
        self.managers = set()  # Dictionary to store managers with manager_id as key
        self.users = []  # List of users for the course

        self.course_topics_lock = threading.Lock()
        self.exams_lock = threading.Lock()
        self.managers_lock = threading.Lock()
        self.users_lock = threading.Lock()
        # self.token = "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"  # Hugging Face token for authentication
        # self.model_api_url = "https://api-inference.huggingface.co/models/HuggingFaceH4/zephyr-7b-beta"
        self.course_topics_repository = CourseTopicsRepository()
        self.llmUtil = LLMutil()

    @classmethod
    def create(cls, course_id, name, course_topics=None):
        """
        Class method to create a new user and save to database
        Returns:
            UserData: Newly created user instance
        """
        course = cls(
            course_id=course_id,
            course_topics=course_topics,
            name=name
        )
        course_repository = CourseRepository()
        course_repository.add_course(course)
        topics_repo = CourseTopicsRepository()
        return course

    # Getters
    def get_id(self):
        return self.course_id

    def get_exams_by_year(self, year):
        exam_repo = ExamRepository()
        return exam_repo.get_all_exams_by_year_and_course(year=year, course_id=self.course_id)

    def get_name(self):
        return self.name

    def get_syllabus(self):
        return self.syllabus

    def get_topics(self):
        with self.course_topics_lock:
            return self.course_topics
    
    def get_course_manager_count(self):
        managers_Repo = CourseManagersRepository()
        return managers_Repo.get_course_manager_count(self.course_id)

    def get_all_exams(self):
        """Retrieve all exams from the exams dictionary."""
        exam_repo = ExamRepository()
        return exam_repo.get_exam_by_course(course_id=self.course_id)

    def get_questions_by_specific(self, year=None, semester=None, moed=None, question_number=None):
        """Get specific questions."""
        question_dtos = []
        if year is None:
            all_exams = self.get_all_exams()
            if all_exams is not None:
                for exam in all_exams:
                    # Only include the questions that match the specific number
                    question_dtos.extend(exam.get_questions_by_specific(question_number))
        else:
            year_exams = self.get_exams_by_year(year)
            if year_exams is not None and len(year_exams) > 0:
                # year_exams = self.exams[year]
                if semester is None:
                    for exam in year_exams:
                        question_dtos.extend(exam.get_questions_by_specific(question_number))
                elif semester is not None and moed is None:
                    for exam in year_exams:
                        if exam.semester.__str__() == semester:
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
    
    def get_allExams_Link_and_name(self):
        exam_repo = ExamRepository()
        exams = exam_repo.get_allExams_Link_and_name(self.course_id)
        return exams

    def get_exam(self, year, semester, moed, raise_exception=True):
        """
        Retrieves a specific exam by year, semester, and moed.
        Raises an exception if not found, unless raise_exception is False.
        """
        # Convert semester and moed to Enum
        semester = Semester(semester)
        moed = Moed(moed)

        # if year in self.exams:
        #     for exam in self.exams[year]:
        #         if exam.semester == semester and exam.moed == moed:
        #             return exam
        exam_repo = ExamRepository()
        exam = exam_repo.get_exam_by_date(year=year, semester=semester, moed=moed, course_id=self.course_id)
        if exam:
            if year not in self.exams:
                self.exams[year] = []  # Create a new list for this year if it doesn't exist
            self.exams[year].append(exam)
        return exam

    # This handles cases where the user didn't specify 'semester' or 'moed' in the search.
    def get_exams(self, year: int, semester=None, moed=None):
        """Fetch exams by year, and optionally filter by semester and moed."""
        with self.exams_lock:
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
        with self.managers_lock:
            return self.managers

    def get_course_managers(self):
        repo = CourseManagersRepository()
        managers_id = repo.get_course_manager_ids(self.course_id)
        return managers_id
    
    def get_users(self):
        with self.users_lock:
            return self.users

    # Setters
    def set_syllabus(self, syllabus):
        self.syllabus = syllabus

    # Methods
    def add_course_topic(self, course_topic):
        """Add a topic to the course."""
        with self.course_topics_lock:
            if course_topic not in self.course_topics:
                self.course_topics.add(course_topic)
                course_topics_repo = CourseTopicsRepository()
                course_topics_repo.add_Topic_to_course(course_id=self.course_id, topic=course_topic)
            else:
                raise TopicAlreadyExist(course_topic)

    def remove_course_topic(self, course_topic):
        """Remove a topic from the course."""
        with self.course_topics_lock:
            if course_topic in self.course_topics:
                self.course_topics.remove(course_topic)
                course_topics_repo = CourseTopicsRepository()
                course_topics_repo.remove_topic_from_course(course_id=self.course_id, topic=course_topic)
            else:
                raise TopicNotFound(course_topic)

    def add_student(self, user_id):
        """Adds a student to the course."""
        with self.users_lock:
            if user_id not in self.users:
                self.users.append(user_id)
            else:
                raise UserAlreadyRegisterToCourse()

    def remove_student(self, user_id):
        """Removes a student from the course."""
        with self.users_lock:
            if user_id in self.users:
                self.users.remove(user_id)
                course_repo = CourseRepository()
                course_repo.update_course(self)
            else:
                raise UserIsNotRegisterToCourse()

    def generate_exam_id(self, year, semester, moed):
        return f"EXAM-{self.course_id}-{year}-{semester}-{moed}"

    def add_exam(self, year, semester, moed, link=""):
        """
        Adds an exam to the course.
        """
        with self.exams_lock:
            # Convert semester and moed to Enum
            semester = Semester(semester)
            moed = Moed(moed)

            exam = self.get_exam(year, semester, moed, raise_exception=False)
            if exam is None:
                exam_id = self.generate_exam_id(year=year, semester=semester.value, moed=moed.value)
                exam = Exam.create(exam_id=exam_id, course_id=self.course_id, link=link, year=year, semester=semester,
                                   moed=moed)
                if exam is not None:
                    if year not in self.exams:
                        self.exams[year] = []
                    self.exams[year].append(exam)
            else:
                raise ExamAlreadyExists(f"ExamData with year={year}, semester={semester}, moed={moed} already exists.")

    def remove_exam(self, year, semester, moed):
        """Removes an exam from the course."""
        with self.exams_lock:
            exam = self.get_exam(year, semester, moed)
            if exam is not None:
                self.exams[year].remove(exam)
                exam_repo = ExamRepository()
                exam_repo.delete_exam(self.course_id, year, semester, moed)
            else:
                raise ExamIsNotExist(year, semester, moed)

    def get_relevant_topics(self, question_text, threshold=0.3):
        topics_list = list(self.course_topics)
        scored = self.score_pairs(question_text, topics_list)
        relevant = [topic for topic, score in scored if score >= threshold]
        return relevant

    def get_exam_full_pdf(self, year, semester, moed):
        """
        Checks if the full exam PDF exists and returns the result.

        Args:
            year (int): Year of the exam.
            semester (str): Semester of the exam.
            moed (str): ExamData session.

        Returns:
            dict: Result indicating if the PDF link exists or not.

        Raises:
            ExamIsNotExist: If the exam does not exist.
        """
        exam = self.get_exam(year, semester, moed)  # Retrieve the exam
        if not exam:
            raise ExamIsNotExist(year, semester, moed)
        return exam.link  # Check for the exam link
        #
        # return exam_pdf_link
        # else:
        #     raise Exception("exam did not uploaded yet")

    def check_exam_full_pdf(self, year, semester, moed):
        """
        Checks if the full exam PDF exists and returns the result.
        
        Args:
            year (int): Year of the exam.
            semester (str): Semester of the exam.
            moed (str): ExamData session.
        
        Returns:
            dict: Result indicating if the PDF link exists or not.
        
        Raises:
            ExamIsNotExist: If the exam does not exist.
        """
        exam = self.get_exam(year, semester, moed)  # Retrieve the exam
        if not exam:
            return False
        exam_pdf_link = exam.link  # Check for the exam link
        if exam_pdf_link != "":
            return True
        else:
            return False

    def get_full_exam_solution(self, year, semester, moed):
        """
        Checks if the full exam solution PDF exists and returns the result.

        Args:
            year (int): Year of the exam.
            semester (str): Semester of the exam.
            moed (str): ExamData session.

        Returns:
            dict: Result indicating if the PDF link exists or not.

        Raises:
            ExamIsNotExist: If the exam does not exist.
        """
        exam = self.get_exam(year, semester, moed)
        if not exam:
            raise ExamIsNotExist(f"ExamData for year {year}, semester {semester}, moed {moed} does not exist.")
        return exam.link_to_solution

    def existFullExamSolution(self, year, semester, moed):
        """
        Checks if the full exam solution PDF exists and returns the result.

        Args:
            year (int): Year of the exam.
            semester (str): Semester of the exam.
            moed (str): ExamData session.

        Returns:
            dict: Result indicating if the PDF link exists or not.

        Raises:
            ExamIsNotExist: If the exam does not exist.
        """
        exam = self.get_exam(year, semester, moed)
        if not exam:
            raise ExamIsNotExist(f"ExamData for year {year}, semester {semester}, moed {moed} does not exist.")
        return exam.existFullExamSolution()  # Check for the exam link
    
    def checkExistSolution(self, year, semester, moed, question_number):
        exam = self.get_exam(year, semester, moed)  # Retrieve the exam
        if not exam:
            raise ExamIsNotExist(f"ExamData for year {year}, semester {semester}, moed {moed} does not exist.")
        question = exam.get_question(question_number)
        question_answer_pdf_link = question.link_to_answer  # Check for the exam link
        if question_answer_pdf_link != "":
            return True
        else:
            return False

    def checkExistQuestion(self, year, semester, moed, question_number):
        exam = self.get_exam(year, semester, moed)  # Retrieve the exam
        if not exam:
            raise ExamIsNotExist(f"ExamData for year {year}, semester {semester}, moed {moed} does not exist.")
        question = exam.get_question(question_number)
        question_details = question.generate_question_details_name()
        if not question:
            return False
        return question.id, question_details, question.link_to_question, question.link_to_answer

    def upload_full_exam_pdf(self, year, semester, moed, exam_path):
        exam = self.get_exam(year, semester, moed)
        if not exam:
            raise Exception(f"ExamData for year {year}, semester {semester}, moed {moed} does not exist.")
        return exam.upload_full_exam_pdf(exam_path)

    def upload_full_exam_solution(self, year, semester, moed, solution_path):
        exam = self.get_exam(year, semester, moed)
        if not exam:
            raise Exception(f"ExamData for year {year}, semester {semester}, moed {moed} does not exist.")
        return exam.upload_full_exam_solution(solution_path)

    def uploadSolution(self, year, semester, moed, question_number, answer_path_path):
        exam = self.get_exam(year, semester, moed)
        if not exam:
            raise Exception(f"ExamData for year {year}, semester {semester}, moed {moed} does not exist.")
        question = exam.get_question(question_number)
        return question.uploadSolution(answer_path_path)
    
    def exist_manager(self, manager_id):
        manager_repo = CourseManagersRepository()
        return manager_id in self.managers or manager_repo.is_exist(user_id=manager_id, course_id=self.course_id)

    def add_manager(self, manager_id):
        """Adds a manager to the course."""
        with self.managers_lock:
            if not self.exist_manager(manager_id):
                self.managers.add(manager_id)
                manager_repo = CourseManagersRepository()
                manager_repo.add_manager_to_course(user_id=manager_id, course_id=self.course_id)
            else:
                raise ManagerAlreadyExists(manager_id)

    def remove_manager(self, manager_id):
        """Removes a manager from the course."""
        with self.managers_lock:
            if self.exist_manager(manager_id):
                self.managers.remove(manager_id)
                manager_repo = CourseManagersRepository()
                manager_repo.remove_manager_from_course(user_id=manager_id, course_id=self.course_id)
            else:
                raise ManagerIsNotExist(manager_id)

    def edit_exam_year(self, year, semester, moed, new_year):
        with self.exams_lock:
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
                exam_repo = ExamRepository()
                exam_repo.update_exam(
                    exam
                )
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
    #             raise ValueError(f"ExamData found, but mismatched semester {semester} or moed {moed}.")

    def check_valid_question(self, year, semester, moed, question_number):
        # Get or create the exam
        currExam = self.get_exam(year, semester, moed)
        if currExam is None:
            # Create the exam if it doesn't exist
            self.add_exam(year=year, semester=semester, moed=moed)
            return True
        else:
            if currExam.semester == semester and currExam.moed == moed:
                return currExam.check_add_question_possibility(year=year, semester=semester, moed=moed,
                                                               question_number=question_number)
            else:
                raise ValueError(f"ExamData found, but mismatched semester {semester} or moed {moed}.")

    def add_comment(self, year, semester, moed, question_number, comment_id, writer_name, writer_id, prev_id,
                    comment_text, link_to_media):
        """
        Add a CommentData to specific question.
        """
        exam = self.get_exam(year, semester, moed)
        if exam is None:
            raise ExamIsNotExist
        question = exam.get_question(question_number)
        if question is None:
            raise QuestionNotFound
        return question.add_comment(comment_id, writer_name, writer_id, prev_id, comment_text, False, False,
                                    link_to_media)

    def get_question_path(self, year, semester, moed, question_number):
        exam = self.get_exam(year=year, semester=semester, moed=moed)
        if exam is not None:
            return exam.get_question_path(question_number)
        else:
            raise ExamIsNotExist

    def get_answer_path(self, year, semester, moed, question_number):
        exam = self.get_exam(year=year, semester=semester, moed=moed)
        if exam is not None:
            return exam.get_answer_path(question_number)
        else:
            raise ExamIsNotExist
    
    def get_question_id(self, year, semester, moed, question_number):
        exam = self.get_exam(year=year, semester=semester, moed=moed)
        if exam is not None:
            return exam.get_question_id(question_number)
        else:
            raise ExamIsNotExist

    def get_question_id_and_path(self, year, semester, moed, question_number):
        exam = self.get_exam(year=year, semester=semester, moed=moed)
        if exam is not None:
            return exam.get_question_id_and_path(question_number)
        else:
            raise ExamIsNotExist(year, semester, moed)
        
    def add_reaction(self, year, semester, moed, question_number, comment_id, user_id, emoji):
        """
        Add a reaction to specific question.
        """
        exam = self.get_exam(year, semester, moed)
        if exam is None:
            raise ExamIsNotExist
        question = exam.get_question(question_number)
        if question is None:
            raise QuestionNotFound
        return question.add_reaction(comment_id, user_id, emoji)

    def delete_comment(self, year, semester, moed, question_number, comment_id):
        """
        Add a reaction to specific question.
        """
        exam = self.get_exam(year, semester, moed)
        if exam is None:
            raise ExamIsNotExist
        question = exam.get_question(question_number)
        if question is None:
            raise QuestionNotFound(question_number)
        question.delete_comment(comment_id)

    def edit_comment_text(self, year, semester, moed, question_number, comment_id, new_text):
        """
        Add a reaction to specific question.
        """
        exam = self.get_exam(year, semester, moed)
        if exam is None:
            raise ExamIsNotExist
        question = exam.get_question(question_number)
        if question is None:
            raise QuestionNotFound
        question.edit_comment_text(comment_id, new_text)

    def remove_reaction(self, year, semester, moed, question_number, comment_id, reaction_id):
        exam = self.get_exam(year, semester, moed)
        if exam is None:
            raise ExamIsNotExist(year, semester, moed)
        question = exam.get_question(question_number)
        if question is None:
            raise QuestionNotFound(f"Question {question_number} not found.")
        return question.remove_reaction(comment_id, reaction_id)

    def handleDownloadAllExamsZip(self):
        exams = self.get_allExams_Link_and_name()
        folder_name = f"{self.course_id}_{self.name}_NegevNerds_מבחנים"
        return folder_name, exams

    def add_question(self, year, semester, moed, question_number, is_american, question_topics, pdf__question_path,
                     pdf__answer_path, question_text):
        if question_topics is None:
            question_topics = self.llmUtil.find_question_topics_by_text_cloud(question_text=question_text, course_topics=list(self.course_topics))
            print(f"Found topics for question : {question_topics}")
        exam = self.get_exam(year, semester, moed)
        return exam.add_question(question_number, is_american, question_topics, pdf__question_path,
                                 pdf__answer_path, question_text)

    # def find_question_topics_by_text(self, question_text):
    #
    #     # טען מודל תומך בעברית
    #     model = SentenceTransformer('sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2')
    #     topics_list = list(self.course_topics)
    #     # הפקת embedding
    #     question_embedding = model.encode(question_text, convert_to_tensor=True)
    #     topics_embeddings = model.encode(topics_list, convert_to_tensor=True)
    #
    #     # חישוב דמיון קוסיני
    #     cosine_scores = util.cos_sim(question_embedding, topics_embeddings)[0]
    #     scores_array = cosine_scores.cpu().numpy()
    #     print("Cosine Scores:", cosine_scores)
    #     print("Topics embeddings:", topics_embeddings)
    #     print("Question Embedding:", question_embedding)
    #     print("Scores Array:", scores_array)
    #
    #     MIN_ABSOLUTE_THRESHOLD = 0.3
    #     HIGH_ALL_RELEVANT_THRESHOLD = 0.7
    #     GAP_FROM_MAX_SCORE = 0.25
    #
    #     if np.max(scores_array) < MIN_ABSOLUTE_THRESHOLD:
    #         return []
    #
    #     if np.min(scores_array) >= HIGH_ALL_RELEVANT_THRESHOLD:
    #         return topics_list
    #
    #     dynamic_threshold = np.max(scores_array) - GAP_FROM_MAX_SCORE
    #     final_threshold = max(dynamic_threshold, MIN_ABSOLUTE_THRESHOLD)
    #
    #     results = []
    #     for topic, score in zip(topics_list, scores_array):
    #         if score >= final_threshold:
    #             results.append(topic)
    #
    #     return results
    #
    #
    # def score_pairs(self, question_text, topics_list):
    #     inputs = tokenizer(
    #         [(question_text, topic) for topic in topics_list],
    #         padding=True,
    #         truncation=True,
    #         return_tensors="pt"
    #     )
    #     with torch.no_grad():
    #         scores = model(**inputs).logits.squeeze(-1).numpy()
    #     return list(zip(topics_list, scores))
    #
    # def find_question_topics_by_text_cloud(self, question_text):
    #     topics_list = list(self.course_topics)
    #     if not question_text or not topics_list:
    #         print("קלט טקסט שאלה ריק או רשימת נושאים ריקה. מחזיר רשימה ריקה.")
    #         return []
    #
    #     topics_formatted = "\n".join([f"- {topic}" for topic in topics_list])
    #
    #     # פרומפט משופר: מדויק יותר בבקשת הפורמט
    #     prompt = f"""
    #      Given the following exam question:
    #      "{question_text}"
    #
    #      And the following list of potential topics:
    #      {topics_formatted}
    #
    #      Please identify only the most relevant topics from the list that directly relate to the question.
    #      Return your answer as a Python list of strings. Do not include any other text or explanation, just the list.
    #      For example: ['Topic 1', 'Topic 2']
    #
    #      Relevant topics:
    #      """
    #
    #     headers = {
    #         "Authorization": f"Bearer {self.token}",  # הוספת טוקן האימות
    #         "Content-Type": "application/json"  # חשוב להגדיר Content-Type
    #     }
    #
    #     payload = {
    #         "inputs": prompt,
    #         "parameters": {
    #             "max_new_tokens": 100,  # הגבלת אורך התשובה
    #             "return_full_text": False,  # רק הטקסט שנוצר, לא כל הפרומפט
    #             "do_sample": False,  # כדי לקבל תשובה דטרמיניסטית יותר (פחות יצירתית)
    #             # "temperature": 0.1 # יכול לעזור לדטרמיניסטיות, אבל לפעמים מודלים לא תומכים בזה
    #         }
    #     }
    #
    #     print(f"שולח בקשה ל-Hugging Face Inference API בכתובת:...")
    #     try:
    #         response = requests.post(
    #             self.model_api_url,
    #             headers=headers,
    #             data=json.dumps(payload)  # השתמש ב-data=json.dumps(payload)
    #         )
    #         response.raise_for_status()  # יזרוק שגיאה עבור 4xx/5xx responses
    #
    #         result = response.json()
    #         print("תגובת API מלאה:", json.dumps(result, indent=2, ensure_ascii=False))
    #
    #         # ניתוח הפלט: צריך להיות זהיר עם eval
    #         # תגובה אופיינית היא רשימה עם אובייקט אחד: [{"generated_text": "['Topic 1', 'Topic 2']"}]
    #         if isinstance(result, list) and result and 'generated_text' in result[0]:
    #             output_text = result[0]['generated_text'].strip()
    #         elif isinstance(result, dict) and 'generated_text' in result:
    #             output_text = result['generated_text'].strip()
    #         else:
    #             print("שגיאה: מבנה תגובה לא צפוי מה-API.")
    #             return []
    #
    #         match = re.search(r"\[.*?\]", output_text)
    #         if match:
    #             list_str = match.group(0)
    #             try:
    #                 extracted_list = eval(list_str)
    #                 if isinstance(extracted_list, list) and all(isinstance(item, str) for item in extracted_list):
    #                     return [topic for topic in extracted_list if topic in topics_list]
    #             except Exception as e:
    #                 print(f"שגיאה בניתוח עם eval: {e}")
    #                 print(f"פלט המודל שניסה לנתח: {list_str}")
    #
    #             # שלב 2: fallback - נסה לפרסר רשימה עם מקפים
    #         fallback_matches = re.findall(r"-\s+(.*)", output_text)
    #         if fallback_matches:
    #             extracted_list = [item.strip() for item in fallback_matches]
    #             return [topic for topic in extracted_list if topic in topics_list]
    #
    #         print("שגיאה: לא נמצאה רשימה תקינה בפלט המודל.")
    #         print(f"פלט המודל המלא: {output_text}")
    #
    #     except requests.exceptions.RequestException as e:
    #         print(f"שגיאת בקשת HTTP: {e}")
    #         return []
    #     except json.JSONDecodeError as e:
    #         print(f"שגיאת ניתוח JSON מהתגובה: {e}. התגובה כטקסט: {response.text}")
    #         return []
    #     except Exception as e:
    #         print(f"שגיאה בלתי צפויה: {e}")
    #         return []


    def edit_question_topic(self, year, semester, moed, question_number, topics):
        for topic in topics:
            if not self.course_topics_repository.is_exist(topic, self.course_id):
                return False
        exam = self.get_exam(year, semester, moed)
        if exam is not None:
            return exam.edit_question_topic(question_number, topics)
        else:
            raise ExamIsNotExist(year, semester, moed)

    def checkQuestionAvailability(self, new_year, new_semester, new_moed, new_question_number):
        exam = self.get_exam(new_year, new_semester, new_moed)
        if exam is None:
            exam_id = self.generate_exam_id(year=new_year, semester=new_semester, moed=new_moed)
            exam = Exam.create(exam_id=exam_id, course_id=self.course_id, link="", year=new_year, semester=new_semester,
                               moed=new_moed)
            if exam is not None:
                if new_year not in self.exams:
                    self.exams[new_year] = []
                self.exams[new_year].append(exam)
            return True, exam.id
        else:
            return exam.checkQuestionAvailability(new_question_number), exam.id

    def edit_question_details(self, old_year, old_semester, old_moed, old_question_number, new_year, new_semester,
                              new_moed, new_question_number, exam_id, question_new_path, solution_new_path):
        exam = self.get_exam(old_year, old_semester, old_moed)
        return exam.edit_question_details(old_question_number, new_year, new_semester, new_moed, new_question_number,
                                          exam_id, question_new_path, solution_new_path)

    def set_question_pate(self, year, semester, moed, question_number, link_to_question):
        exam = self.get_exam(year=year, semester=semester, moed=moed)
        if exam is None:
            raise ExamIsNotExist(year, semester, moed)
        exam.set_question_path(question_number, link_to_question)

