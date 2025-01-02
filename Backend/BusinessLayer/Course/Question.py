import uuid

from flask_sqlalchemy.session import Session

from Backend.BusinessLayer.Course.Comment import Comment
from Backend.BusinessLayer.Course.enums import Moed, Semester
from datetime import datetime
from Backend.DataLayer.DTOs.QuestionDTO import QuestionDTO
from Backend.BusinessLayer.Util.Exceptions import *
from Backend.DataLayer.QuestionTopics.QuestionTopicsRepository import QuestionTopicsRepository
from Backend.DataLayer.Questions.QuestionRepository import QuestionRepository


class Question:
    def __init__(self, year, semester, moed, question_number, is_american,
                 link_to_question, link_to_answer, link_to_exam, question_topics=None, question_id=None, comments=None, text = ""):
        """
        Initialize a Question instance.
        """
        self.year = year
        self.semester = Semester(semester)  # Ensuring semester is an Enum
        self.moed = Moed(moed)
        self.question_number = question_number
        self.is_american = is_american
        self.question_topics = question_topics if question_topics is not None else []  # Default to an empty list
        self.link_to_question = link_to_question
        self.link_to_answer = link_to_answer
        self.link_to_exam = link_to_exam
        self.id = question_id
        self.comments = comments if comments is not None else []# Default to an empty list
        self.text = text

    @classmethod
    def create(cls, year, semester, moed, question_number, is_american,
               link_to_question, link_to_answer, link_to_exam,exam_id, question_id=None,
               question_topics=None, question_text=""):
        """
        Class method to create a new user and save to database
        Returns:
            User: Newly created user instance
        """

        question = cls(
            year=year,
            semester=semester,
            moed=moed,
            question_number=question_number,
            is_american=is_american,
            link_to_question=link_to_question,
            link_to_exam=link_to_exam,
            link_to_answer=link_to_answer,
            question_id=question_id,
            question_topics=question_topics,
            text=question_text

        )
        question_repo = QuestionRepository()
        question_repo.add_question(question, exam_id)
        # question_topics_repo = QuestionTopicsRepository()

        # for topic in question_topics:
        #     if not question_topics_repo.is_exist(topic=topic, question_id=question_id):
        #         question_topics_repo.add_Topic_to_Question(topic=topic, question_id=question_id)

        return question

    def to_dto(self):
        """
        Converts the Question instance to a QuestionDTO.
        :return: QuestionDTO instance.
        """
        comment_dtos = [comment.to_dto() for comment in self.comments]
        return QuestionDTO(
            question_id=self.id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=self.question_number,
            question_topics=self.question_topics,
            is_american=self.is_american,
            link_to_question=self.link_to_question,
            comments_list=comment_dtos
        )

    def generate_comment_id(self):
        return "comment" + str(uuid.uuid4())

    def get_question_topics(self):
        return self.question_topics

    def add_question_topic(self, question_topic):
        """
        Add a topic for the question from it's course_topics.
        """
        self.question_topics.append(question_topic)

    def generate_question_details_name(self):
        return f"E-{self.year}-{self.semester}-{self.moed}-Q{self.question_number}"

    def remove_question_topic(self, question_topic):
        """
        Remove a topic.
        """
        if question_topic in self.question_topics:
            self.question_topics.remove(question_topic)
        else:
            print(f"Keyword '{question_topic}' not found in the list.")

    def add_comment(self, writer_name, prev_id, comment_text):
        """
        Add a Comment to the comments list.
        """
        comment = Comment.create(comment_id=self.generate_comment_id(),
                                 writer_name=writer_name,
                                 date=datetime.now(), 
                                 prev_id=prev_id,
                                 comment_text=comment_text,
                                 question_id=self.id)
        if comment is not None:
            self.comments.append(comment)
        else:
            raise Exception("Problem to create comment")

    def remove_comment(self, comment_id):
        """
        Remove a Comment from the comments list if it exists.
        Raise an exception if the Comment is not found.
        """
        for comment in self.comments:
            if comment.comment_id == comment_id:
                self.comments.remove(comment)
                return
        raise CommentNotFound(comment_id)

    def add_reaction(self, comment_id, user_id, emoji):
        for comment in self.comments:
            if comment.comment_id == comment_id:
                comment.add_reaction(user_id, emoji)
                return
        raise CommentNotFound
    
    def uploadSolution(self, answer_path_path):
        try:
            # Update the in-memory link property
            self.link_to_answer = answer_path_path

            # Update the record in the database
            question_repo = QuestionRepository()  # Assuming you have an ExamRepository for database operations
            question_repo.uploadSolution(self.id, self.link_to_answer)

            return {"status": "success", "message": "File uploaded successfully and database updated.", "link": self.link}
        except Exception as e:
            print(f"Error in Exam.upload_full_exam_pdf: {str(e)}")
            return {"status": "error", "message": str(e)}

    def remove_reaction(self, comment_id, reaction_id):
        for comment in self.comments:
            if comment.comment_id == comment_id:
                comment.remove_reaction(reaction_id)
                return
        raise CommentNotFound

    def __str__(self):
        """
        String representation of the Question instance.
        """
        return (f"Question(ID: {self.id}, Year: {self.year}, Semester: {self.semester}, Moed: {self.moed}, "
                f"Number: {self.question_number}, IsAmerican: {self.is_american}, "
                f"Comments: {len(self.comments)})")
