class QuestionDTO:
    def __init__(self, question_id, year, semester, moed, question_number, question_topics, is_american, link_to_question):
        """
        Data Transfer Object for the Question class.
        """
        self.question_id = question_id
        self.year = year
        self.semester = semester
        self.moed = moed
        self.question_number = question_number
        self.question_topics = question_topics
        self.is_american = is_american
        self.link_to_question = link_to_question

    def to_dict(self):
        """
        Converts the QuestionDTO instance to a dictionary.

        :return: Dictionary representation of the QuestionDTO.
        """
        return {
            "question_id": self.question_id,
            "year": self.year,
            "semester": self.semester,
            "moed": self.moed.name if hasattr(self.moed, 'name') else self.moed,
            "question_number": self.question_number,
            "question_topics": self.question_topics,
            "is_american": self.is_american,
            "link_to_question": self.link_to_question,
        }
