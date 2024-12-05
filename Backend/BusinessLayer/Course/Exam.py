from Backend.BusinessLayer.Course.Question import Question
from Backend.BusinessLayer.Course.enums import Moed, Semester
from Backend.BusinessLayer.Util.Exceptions import QuestionAlreadyInExam, QuestionDoesNotMeetExamFields, QuestionNotFound


class Exam:
    def __init__(self, exam_id, course_name, link, year, semester, moed):
        """
        Initialize an Exam instance.
        """
        self.id = exam_id
        self.course_name = course_name
        self.link = link
        self.year = year
        self.semester = Semester(semester)  # Ensuring semester is an Enum
        self.moed = Moed(moed)
        self.questions_list = {}  # Default to an empty list

    def add_question(self, year, questionId, semester, moed, question_number, is_american, link_to_question):
        """
        Add a question to the questions list.

        :param question: The question to add.
        """
        if year == self.year and semester == self.semester and moed == self.moed:
            if self.questions_list[question_number] is None:
                question = Question(year, questionId, semester, moed, question_number, is_american,
                                    link_to_question, self.link)
                self.questions_list[question_number] = question
            else:
                raise QuestionAlreadyInExam
        else:
            raise QuestionDoesNotMeetExamFields

    def remove_question(self, question_id):
        """
        Remove a question from the questions list if it exists.

        """
        if question_id in self.questions_list.keys():
            self.questions_list[question_id] = None
        else:
            raise QuestionNotFound

    def get_question(self, question_id):
        return self.questions_list[question_id]

    def add_comment(self, question_id, comment_id, writer_name, prev_id, comment_text):
        """
        Add a comment to the comments list.
        """
        self.get_question(question_id).add_comment(comment_id, writer_name, prev_id, comment_text)

    def remove_comment(self, question_id,  comment_id):
        """
        Remove a comment from the comments list if it exists.
        """
        self.get_question(question_id).remove_comment(comment_id)


    def __str__(self):
        """
        String representation of the Exam instance.
        """
        return (f"Exam(ID: {self.id}, Course: {self.course_name}, Year: {self.year}, "
                f"Semester: {self.semester}, Moed: {self.moed}, "
                f"Questions: {len(self.questions_list)})")
