import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from Backend.DataLayer.Exam.ExamModel import Base, ExamModel


class ExamRepository:
    """Repository for handling exam database operations"""
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
    def add_exam(self, exam):
        """
        Add a new exam to the database

        Args:
            exam (exam): Business layer exam object

        Returns:
            int: ID of the newly created exam
        """
        session = self.Session()
        try:
            # Convert business model to SQLAlchemy model
            exam_model = ExamModel(
                exam_id=exam.id,
                moed=exam.moed,
                semester=exam.semester,
                year=exam.year,
                link=exam.link,
                course_name=exam.course_name,
            )

            session.add(exam_model)
            session.commit()

            # Get the auto-generated ID
            exam_id = exam_model.exam_id
            return exam_id
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_exam_by_id(self, exam_id):
        """
        Retrieve a exam by their ID

        Args:
            exam_id (int): exam's unique identifier

        Returns:
            exam: Business layer exam object
        """
        session = self.Session()
        try:
            exam_model = session.query(ExamModel).filter_by(exam_id=exam_id).first()
            return exam_model.to_business_model() if exam_model else None
        finally:
            session.close()

    def get_exam_by_date(self, year, semester, moed):
        """
        Retrieve a exam by their email

        Args:
            email (str): exam's email address

        Returns:
            exam: Business layer exam object or None if not found
        """
        session = self.Session()
        try:
            exam_model = session.query(ExamModel).filter_by(year=year, moed=moed, semester=semester).first()
            return exam_model.to_business_model() if exam_model else None
        except Exception as e:
            # Log the exception if needed
            print(f"Error retrieving exam by email: {e}")
            return None
        finally:
            session.close()

    def update_exam(self, exam):
        """
        Update an existing exam's information

        Args:
            exam (exam): Business layer exam object with updated information
        """
        session = self.Session()
        try:
            # Find the existing exam
            exam_model = session.query(ExamModel).filter_by(exam_id=exam.id).first()

            if not exam_model:
                raise ValueError(f"No exam found with ID {exam.id}")

            # Update fields
            exam_model.exam_id = exam.id
            exam_model.course_name = exam.course_name
            exam_model.semester = exam.semester
            exam_model.moed = exam.moed
            exam_model.year = exam.year
            exam_model.link = exam.link

            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def delete_exam(self, year, semester, moed):
        """
        Delete a exam from the database

        """
        session = self.Session()
        try:
            exam_model = session.query(ExamModel).filter_by(year=year, semester=semester, moed=moed).first()

            if not exam_model:
                raise ValueError(f"No exam found with Date {year, moed, semester}")

            session.delete(exam_model)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
