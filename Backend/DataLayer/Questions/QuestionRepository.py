import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from Backend.DataLayer.Questions.QuestionModel import Base, QuestionModel


class QuestionRepository:

    def __init__(self, db_path=None):
        """
        Initialize the database engine.

        :param db_path: Path to the SQLite database. If None, uses the default path.
        """
        if db_path is None:
            # Default to a local SQLite database file in the parent directory
            db_path = os.path.join(os.path.dirname(__file__), '../../..', 'NegevNerds.db')

        # Ensure the directory exists
        db_dir = os.path.dirname(db_path)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

        # Use the full path to create the SQLite engine
        #print(f"Resolved database path: {db_path}")
        self.engine = create_engine(f'sqlite:///{db_path}')

        # Ensure all tables are created

        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
    def add_question(self, question):

        session = self.Session()
        try:
            # Convert business model to SQLAlchemy model
            question_model = QuestionModel(
                question_id=question.question_id,
                year=question.year,
                is_american=question.is_american,
                link_to_question=question.link_to_question,
                link_to_exam=question.link_to_question,
                semester=question.semester,
                moed=question.moed,
                question_number=question.question_number,
            )

            session.add(question_model)
            session.commit()

            # Get the auto-generated ID

        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_question_by_id(self, question_id):

        session = self.Session()
        try:
            question_model = session.query(QuestionModel).filter_by(question_id=question_id).first()
            return question_model.to_business_model() if question_model else None
        finally:
            session.close()


    def update_question(self, question):

        session = self.Session()
        try:
            question_model = session.query(QuestionModel).filter_by(question_id=question.question_id).first()

            if not question_model:
                raise ValueError(f"No question found with ID {question.id}")

            # Update fields
            question_model.question_id = question.id,
            question_model.year = question.year,
            question_model.is_american = question.is_american,
            question_model.link_to_question = question.link_to_question,
            question_model.link_to_exam = question.link_to_question,
            question_model.semester = question.semester,
            question_model.moed = question.moed,
            question_model.question_number = question.question_number,

            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def delete_question(self, question_id):

        session = self.Session()
        try:
            question_model = session.query(QuestionModel).filter_by(question_id=question_id).first()

            if not question_model:
                raise ValueError(f"No question found with ID {question_id}")

            session.delete(question_model)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
