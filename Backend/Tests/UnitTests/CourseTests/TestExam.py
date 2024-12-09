import unittest
from Backend.BusinessLayer.Course.Exam import Exam
from Backend.BusinessLayer.Course.enums import Semester, Moed
from Backend.BusinessLayer.Util.Exceptions import *
from Backend.DataLayer.QuestionDTO import QuestionDTO


class TestExam(unittest.TestCase):
    def setUp(self):
        """
        Set up an Exam instance and a QuestionDTO instance for testing.
        """
        self.exam = Exam(
            exam_id=1,
            course_name="Algorithms",
            link="http://example.com/exam",
            year=2024,
            semester="Spring",
            moed="A"
        )
        self.question_dto = QuestionDTO(
            question_id=1,
            year=2024,
            semester="Spring",
            moed="A",
            question_number=1,
            question_topics=["Sorting Algorithms"],
            is_american=False,
            link_to_question="http://example.com/question1"
        )

    def test_add_question_success(self):
        """
        Test adding a question to the exam successfully.
        """
        self.exam.add_question(self.question_dto)
        self.assertIn(self.question_dto.question_id, self.exam.questions_list)

    def test_add_question_duplicate(self):
        """
        Test adding a question with a duplicate ID raises an exception.
        """
        self.exam.add_question(self.question_dto)
        with self.assertRaises(QuestionAlreadyInExam):
            self.exam.add_question(self.question_dto)

    def test_add_question_fields_matching(self):
        """
        Test adding a question with matching fields.
        """
        question_dto = QuestionDTO(
            question_id=2,
            year=2024,
            semester="Spring",  # Matching semester
            moed="A",  # Matching moed
            question_number=2,  # This is the key in the dictionary
            question_topics=["Graphs"],
            is_american=True,
            link_to_question="http://example.com/question2"
        )
        self.exam.add_question(question_dto)

        # Verify the question was added under the correct key (question_number)
        self.assertIn(question_dto.question_number, self.exam.questions_list)
        self.assertEqual(self.exam.questions_list[question_dto.question_number], question_dto)

    def test_add_question_fields_not_matching(self):
        """
        Test adding a question with non-matching fields raises an exception.
        """
        question_dto_mismatch = QuestionDTO(
            question_id=2,
            year=2024,
            semester="Fall",  # Non-matching semester
            moed="B",  # Non-matching moed
            question_number=2,
            question_topics=["Graphs"],
            is_american=True,
            link_to_question="http://example.com/question2"
        )
        with self.assertRaises(QuestionDoesNotMeetExamFields) as context:
            self.exam.add_question(question_dto_mismatch)

    def test_remove_question_success(self):
        """
        Test removing a question successfully.
        """
        self.exam.add_question(self.question_dto)
        self.exam.remove_question(self.question_dto.question_id)
        self.assertNotIn(self.question_dto.question_id, self.exam.questions_list)

    def test_remove_question_not_found(self):
        """
        Test removing a question that does not exist raises an exception.
        """
        with self.assertRaises(QuestionNotFound):
            self.exam.remove_question(999)

    def test_edit_exam_year(self):
        """
        Test editing the year of the exam.
        """
        self.exam.edit_year(2025)
        self.assertEqual(self.exam.year, 2025)

    def test_edit_exam_semester(self):
        """
        Test editing the semester of the exam.
        """
        self.exam.edit_semester("Fall")
        self.assertEqual(self.exam.semester, Semester("Fall"))

    def test_edit_exam_moed(self):
        """
        Test editing the moed of the exam.
        """
        self.exam.edit_moed("B")
        self.assertEqual(self.exam.moed, Moed("B"))

    def test_edit_exam_link(self):
        """
        Test editing the exam link.
        """
        new_link = "http://example.com/new_exam"
        self.exam.edit_link(new_link)
        self.assertEqual(self.exam.link, new_link)


if __name__ == "__main__":
    unittest.main()
