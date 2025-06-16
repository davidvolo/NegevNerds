import threading

from Backend.BusinessLayer.Util.Exceptions import *
from Backend.DataLayer.UserData.UserRepository import UserRepository  # Import the repository
from Backend.DataLayer.UserCourses.UserCoursesRepository import UserCoursesRepository
from Backend.DataLayer.NotificationsSetting.NotificationsSettingRepository import NotificationsSettingRepository


class User:
    def __init__(self, user_id, email, password, first_name, last_name, loggedIn=False):
        self.user_id = user_id
        self.email = email
        self.password = password
        self.first_name = first_name
        self.last_name = last_name
        self.loggedIn = loggedIn
        self.courses = []

        self.courses_lock = threading.Lock()

        # Create a repository instance for database operations
        self._repo = UserRepository()
        self.notification_settings = {
            "AppointSystemManager": True,
            "AppointCourseManager": True,
            "CommentToFollowing": True,
            "CommentToComment": True,
            "ReactToComment": True,
            "RemoveCourseManager": True
        }

    @classmethod
    def create(cls, user_id, email, password, first_name, last_name):
        """
        Class method to create a new user and save to database

        Returns:
            User: Newly created user instance
        """
        user = cls(
            user_id=user_id,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name
        )
        user_repository = UserRepository()
        user_repository.add_user(user)
        settings_repository = NotificationsSettingRepository()
        settings_repository.save_or_update_settings(user_id, user.notification_settings)



        # db.session.add(user)
        # db.session.commit()

        # Save to database and get the generated ID
        return user

    @classmethod
    def get_by_id(cls, user_id):
        """
        Retrieve a user by their ID

        Args:
            user_id (int): UserData's unique identifier

        Returns:
            User: UserData instance or None if not found
        """
        repo = UserRepository()
        user = repo.get_user_by_id(user_id)
        settings_repo = NotificationsSettingRepository()
        user.notification_settings = settings_repo.get_settings_by_user_id(user_id)
        return user
    

    def login(self):
        """
        Log in the user and update the database
        """
        self.loggedIn = True
        self._repo.update_user(self)

    def logout(self):
        """
        Log out the user and update the database
        """
        self.loggedIn = False
        self._repo.update_user(self)
    
    def reset_new_password(self, email, new_password):
        self.password = new_password
        return self._repo.update_user_password_by_email(email,new_password)

    def registerToCourse(self, course_id):
        """
        Register user to a course and update the database

        Raises:
            UserAlreadyRegisterToCourse: If user is already registered
        """
        with self.courses_lock:
            user_courses_repo = UserCoursesRepository()
            if course_id not in self.courses and not user_courses_repo.is_exist(user_id=self.user_id, course_id=course_id):
                self.courses.append(course_id)
                user_courses_repo.add_user_to_course(user_id=self.user_id, course_id=course_id)
                self._repo.update_user(self)
            else:
                raise UserAlreadyRegisterToCourse()
    
    def is_registerToCourse(self, course_id):
        """
        Register user to a course and update the database

        Raises:
            UserAlreadyRegisterToCourse: If user is already registered
        """
        with self.courses_lock:
            if course_id in self.courses:
                return True
            user_courses_repo = UserCoursesRepository()
            if user_courses_repo.is_exist(user_id=self.user_id, course_id=course_id):
                return True
            return False

    def removeCourse(self, course_id):
        with self.courses_lock:
            courses_repo = UserCoursesRepository()
            if course_id in self.courses or courses_repo.is_exist(user_id=self.user_id, course_id=course_id):
                if course_id in self.courses:
                    self.courses.remove(course_id)
                    courses_repo.remove_user_from_course(user_id=self.user_id, course_id=course_id)
                self._repo.update_user(self)
            else:
                raise UserIsNotRegisterToCourse()
    
    def update_user_name(self, first_name, last_name):
        self.first_name = first_name
        self.last_name = last_name
        return self._repo.update_user_name(self.user_id, first_name,last_name)


    def editProfile(self, email=None, password=None, first_name=None, last_name=None):
        """
        Edit user profile and update the database

        Args:
            email (str, optional): New email address
            password (str, optional): New password
            first_name (str, optional): New first name
            last_name (str, optional): New last name
        """
        if email:
            self.email = email
        if password:
            self.password = password
        if first_name:
            self.first_name = first_name
        if last_name:
            self.last_name = last_name

        # Update the user in the database
        self._repo.update_user(self)

    def delete(self):
        """
        Delete the user from the database
        """
        if self.user_id:
            self._repo.delete_user(self.user_id)
            # Optionally, you might want to reset the user's attributes
            self.user_id = None

    def get_courses(self):
        """
        Get the list of courses the user is registered to

        Returns:
            list: List of course IDs
        """
        with self.courses_lock:
            return self.courses

    def get_first_name(self):
        return self.first_name

    def get_user_id(self):
        return self.user_id

    def get_last_name(self):
        return self.last_name

    def update_notification_settings(self, settings_dict):
        repo = NotificationsSettingRepository()
        success = repo.update_settings(self.user_id, settings_dict)
        if success:
            if self.notification_settings is None:
                self.notification_settings = settings_dict.copy()
            else:
                self.notification_settings.update(settings_dict)
        return success

    
    def should_send_notification(self, notification_type):
        """
        Checks whether this user has enabled a specific type of notification.
        Prefers in-memory settings; falls back to DB if needed.
        """
        if self.notification_settings and notification_type in self.notification_settings:
            return self.notification_settings[notification_type]

        # Fallback to repository check
        setting_repo = NotificationsSettingRepository()
        result = setting_repo.is_notification_enabled(self.user_id, notification_type)

        # 🔄 Cache the result in memory for next time
        if self.notification_settings is None:
            self.notification_settings = {}
        self.notification_settings[notification_type] = result

        return result




