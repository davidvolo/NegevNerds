import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from Backend.DataLayer.Comment.CommentModel import Base, CommentModel


class CommentRepository:

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

    def add_Comment(self, comment, question_id):

        session = self.Session()
        try:
            # Convert business model to SQLAlchemy model
            comment_model = CommentModel(
                comment_id=comment.comment_id,
                writer_name=comment.writer_name,
                date=comment.date,
                prev_id=comment.prev_id,
                text=comment.comment_text,
                question_id=question_id
            )

            session.add(comment_model)
            session.commit()

            # Get the auto-generated ID

            return
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_comment_by_id(self, comment_id):

        session = self.Session()
        try:
            comment_model = session.query(CommentModel).filter_by(comment_id=comment_id).first()
            return comment_model.to_business_model() if comment_model else None
        finally:
            session.close()



    def update_comment(self, comment):

        session = self.Session()
        try:

            comment_model = session.query(CommentModel).filter_by(comment_id=comment.id).first()

            if not comment_model:
                raise ValueError(f"No comment found with ID {comment.id}")

            # Update fields
            comment_model.comment_id = comment.id
            comment_model.writer_name = comment.writer_name
            comment_model.date = comment.date
            comment_model.prev_id = comment.prev_id
            comment_model.text = comment.text

            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def delete_comment(self, comment_id):

        session = self.Session()
        try:
            comment_model = session.query(CommentModel).filter_by(comment_id=comment_id).first()

            if not comment_model:
                raise ValueError(f"No comment found with ID {comment_id}")

            session.delete(comment_model)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()
