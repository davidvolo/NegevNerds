from Backend.BusinessLayer.Course.Comment import Comment
from Backend.BusinessLayer.Course.enums import Moed, Semester
from datetime import datetime


class Question:
    def __init__(self, year, question_id, semester, moed, question_number, is_american, link_to_question, link_to_exam, comments=None):
        """
        Initialize a Question instance.
        """
        self.year = year
        self.id = question_id
        self.semester = Semester(semester)  # Ensuring semester is an Enum
        self.moed = Moed(moed)
        self.question_number = question_number
        self.is_american = is_american
        self.link_to_question = link_to_question
        self.link_to_exam = link_to_exam
        self.comments = comments if comments is not None else []  # Default to an empty list

    def add_comment(self, comment_id, writer_name, prev_id, comment_text):
        """
        Add a comment to the comments list.
        """
        comment = Comment(comment_id, writer_name, datetime.now(), prev_id, comment_text)
        self.comments.append(comment)

    def remove_comment(self, comment_id):
        """
        Remove a comment from the comments list if it exists.
        """
        if comment_id in self.comments:
            self.comments.remove(comment_id)
        else:
            print(f"Comment '{comment_id}' not found in the list.")

    def __str__(self):
        """
        String representation of the Question instance.
        """
        return (f"Question(ID: {self.id}, Year: {self.year}, Semester: {self.semester}, Moed: {self.moed}, "
                f"Number: {self.question_number}, IsAmerican: {self.is_american}, "
                f"Comments: {len(self.comments)})")


