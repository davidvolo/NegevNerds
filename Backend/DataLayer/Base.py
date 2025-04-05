from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import inspect

from sqlalchemy.exc import SQLAlchemyError


Base = declarative_base()

# def get_test_engine():
#     return create_engine('sqlite:///:memory:')

def get_test_session(engine):
    Session = sessionmaker(bind=engine)
    return Session()


def delete_all_data(engine, session):
    # Disable foreign key checks temporarily
    session.execute(text("PRAGMA foreign_keys = OFF"))

    try:
        # Rollback any pending transactions to ensure the session is clean
        session.rollback()

        # Begin a new session for the operation
        session = sessionmaker(bind=engine)()

        # Clear all data from tables in the database
        meta = Base.metadata
        for table in reversed(meta.sorted_tables):
            try:
                session.execute(table.delete())  # Delete all records from each table
            except SQLAlchemyError as e:
                session.rollback()  # Rollback in case of an error during table deletion
                print(f"Error deleting from table {table.name}: {e}")
                raise  # Re-raise the exception to propagate it

        session.commit()  # Commit the transaction
    except SQLAlchemyError as e:
        session.rollback()  # Ensure that the session is rolled back in case of an error
        print(f"An error occurred while deleting data: {e}")
        raise  # Re-raise the exception to propagate it
    finally:
        # Re-enable foreign key checks
        session.execute(text("PRAGMA foreign_keys = ON"))
        session.close()  # Always close the session at the end