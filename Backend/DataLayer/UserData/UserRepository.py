import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from Backend.DataLayer.Base import Base

from Backend.BusinessLayer.Course.Course import Course
from Backend.DataLayer.UserData.UserModel import  UserModel
from Backend.DataLayer.UserCourses.UserCoursesModel import UserCoursesModel


class UserRepository:

    _instance = None  # Singleton pattern

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance
    """Repository for handling UserData database operations"""
    def __init__(self, db_path=None):
        """
        Initialize the database engine.

        :param db_path: Path to the SQLite database. If None, uses the default path.
        """
        if db_path is None:
            # Check for environment variable or default to the application's db path
            db_env = os.getenv("APP_ENV", "production")  # Set the environment variable for app environment (prod/test)

            if db_env == "test":
                db_path = os.path.join(os.path.dirname(__file__), '../../..', 'test_negevnerds.db')
            else:
                # Default to production database
                db_path = os.path.join(os.path.dirname(__file__), '../../..', 'NegevNerds.db')

        # Ensure the directory exists
        db_dir = os.path.dirname(db_path)
        if not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)

        # Use the full path to create the SQLite engine
        #print(f"Resolved database path: {db_path}")
        self.engine = create_engine(f'sqlite:///{db_path}')
        # print("Tables SQLAlchemy knows:", Base.metadata.tables.keys())

        # Ensure all tables are created

        # Ensure all tables are created
        Base.metadata.create_all(self.engine)
        self.Session = sessionmaker(bind=self.engine)
    def add_user(self, user):
        """
        Add a new user to the database

        Args:
            user (UserData): Business layer UserData object

        Returns:
            int: ID of the newly created user
        """
        session = self.Session()
        try:
            # Convert business model to SQLAlchemy model
            user_model = UserModel(
                user_id=user.user_id,
                email=user.email,
                password=user.password,
                first_name=user.first_name,
                last_name=user.last_name,
                logged_in=user.loggedIn,
            )

            session.add(user_model)
            session.commit()

            # Get the auto-generated ID
            user_id = user_model.user_id
            return user_id
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_user_by_id(self, user_id):
        """
        Retrieve a user by their ID

        Args:
            user_id (int): UserData's unique identifier

        Returns:
            UserData: Business layer UserData object
        """
        session = self.Session()
        try:
            user_model = session.query(UserModel).filter_by(user_id=user_id).first()
            return user_model.to_business_model() if user_model else None
        except Exception as e:
            raise e
        finally:
            session.close()
    
    def update_user_password_by_email(self, email, new_password):
        """
        Update the password for a user identified by their email.

        Args:
            email (str): The email of the user
            new_password (str): The encrypted new password 

        Returns:
            bool: True if updated successfully, False if user not found
        """
        session = self.Session()
        try:
            user_model = session.query(UserModel).filter_by(email=email).first()
            if not user_model:
                return False  # user not found

            # Hash the new password

            # Update password
            user_model.password = new_password
            session.commit()
            return True

        except Exception as e:
            session.rollback()
            raise e

        finally:
            session.close()

    def get_user_by_email(self, email):
        """
        Retrieve a user by their email

        Args:
            email (str): UserData's email address

        Returns:
            UserData: Business layer UserData object or None if not found
        """
        session = self.Session()
        try:
            user_model = session.query(UserModel).filter_by(email=email).first()
            return user_model.to_business_model() if user_model else None
        except Exception as e:
            # Log the exception if needed
            print(f"Error retrieving user by email: {e}")
            return None
        finally:
            session.close()

    def update_user(self, user):
        """
        Update an existing user's information

        Args:
            user (UserData): Business layer UserData object with updated information
        """
        session = self.Session()
        try:
            # Find the existing user
            user_model = session.query(UserModel).filter_by(user_id=user.user_id).first()

            if not user_model:
                raise ValueError(f"No user found with ID {user.id}")

            # Update fields
            user_model.user_id = user.user_id
            user_model.email = user.email
            user_model.password = user.password
            user_model.first_name = user.first_name
            user_model.last_name = user.last_name
            user_model.logged_in = user.loggedIn
            user_model.courses = [
                UserCoursesModel(user_id=user.user_id, course_id=course.course_id)
                if isinstance(course, Course) else UserCoursesModel(user_id=user.user_id, course_id=course)
                for course in user.courses
            ]

            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def delete_user(self, user_id):
        """
        Delete a user from the database

        Args:
            user_id (int): ID of the user to delete
        """
        session = self.Session()
        try:
            user_model = session.query(UserModel).filter_by(user_id=user_id).first()

            if not user_model:
                raise ValueError(f"No user found with ID {user_id}")

            session.delete(user_model)
            session.commit()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_user_email_by_id(self, user_id):
        """
        Retrieve a user's email by their ID

        Args:
            user_id (str): User's unique identifier

        Returns:
            str: Email address of the user, or None if not found
        """
        session = self.Session()
        try:
            user_model = session.query(UserModel).filter_by(user_id=user_id).first()
            return user_model.email if user_model else None
        except Exception as e:
            raise e
        finally:
            session.close()

    def get_user_full_name_by_id(self, user_id):
        """
        Retrieve a user's full name by their ID

        Args:
            user_id (str): User's unique identifier

        Returns:
            str: Full name in the format "First Last", or None if not found
        """
        session = self.Session()
        try:
            user_model = session.query(UserModel).filter_by(user_id=user_id).first()
            if user_model:
                return f"{user_model.first_name} {user_model.last_name}"
            return None
        except Exception as e:
            raise e
        finally:
            session.close()

    def get_user_full_name__email_by_id(self, user_id):
        """
        Retrieve a user's full name by their ID

        Args:
            user_id (str): User's unique identifier

        Returns:
            str: Full name in the format "First Last", or None if not found
        """
        session = self.Session()
        try:
            user_model = session.query(UserModel).filter_by(user_id=user_id).first()
            if user_model:
                return f"{user_model.first_name} {user_model.last_name}", user_model.email
            return None
        except Exception as e:
            raise e
        finally:
            session.close()
    
    def update_user_name(self, user_id, first_name, last_name):
        session = self.Session()
        try:
            user = session.query(UserModel).filter_by(user_id=user_id).first()
            if not user:
                return False

            user.first_name = first_name
            user.last_name = last_name
            session.commit()
            return True

        except Exception as e:
            session.rollback()
            print(f"❌ Error updating user name: {e}")
            return False
        finally:
            session.close()

