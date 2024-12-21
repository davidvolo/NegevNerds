from Backend.BusinessLayer.Course.Comment import Comment
from Backend.BusinessLayer.Course.enums import Moed, Semester
from datetime import datetime
from Backend.DataLayer.DTOs.QuestionDTO import QuestionDTO
from Backend.BusinessLayer.Util.Exceptions import *


class Question:
    def __init__(self, year, semester, moed, question_number, is_american,question_topics, 
                  link_to_question, link_to_answer,link_to_exam, question_id=None, comments=None):
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
        self.comments = comments if comments is not None else []  # Default to an empty list

    def to_dto(self):
        """
        Converts the Question instance to a QuestionDTO.
        :return: QuestionDTO instance.
        """
        return QuestionDTO(
            question_id=self.id,
            year=self.year,
            semester=self.semester,
            moed=self.moed,
            question_number=self.question_number,
            question_topics=self.question_topics,
            is_american=self.is_american,
            link_to_question=self.link_to_question
        )

    def get_question_topics(self):
        return self.question_topics

    def add_question_topic(self, question_topic):
        """
        Add a topic for the question from it's course_topics.
        """
        self.question_topics.append(question_topic)
        
    def remove_question_topic(self, question_topic):
        """
        Remove a topic.
        """
        if question_topic in self.question_topics:
            self.question_topics.remove(question_topic)
        else:
            print(f"Keyword '{question_topic}' not found in the list.")
        
    def add_comment(self, comment_id, writer_name, prev_id, comment_text):
        """
        Add a Comment to the comments list.
        """
        comment = Comment(comment_id, writer_name, datetime.now(), prev_id, comment_text)
        self.comments.append(comment)

    def remove_comment(self, comment_id):
        """
        Remove a Comment from the comments list if it exists.
        Raise an exception if the Comment is not found.
        """
        for comment in self.comments:
            if comment.id == comment_id:
                self.comments.remove(comment)
                return
        raise CommentNotFound(comment_id)

    def __str__(self):
        """
        String representation of the Question instance.
        """
        return (f"Question(ID: {self.id}, Year: {self.year}, Semester: {self.semester}, Moed: {self.moed}, "
                f"Number: {self.question_number}, IsAmerican: {self.is_american}, "
                f"Comments: {len(self.comments)})")
