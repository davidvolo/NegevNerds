import smtplib
import random
import datetime
import os
import re
import threading
import uuid
from email.mime.text import MIMEText
import logging
from Backend.BusinessLayer.User.User import User
from Backend.BusinessLayer.Util.Exceptions import *

# from Util.Exceptions import *
# from BusinessLayer.User.User import User
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class UserFacade:
    _instance = None  # Class-level attribute to hold the single instance

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls, *args, **kwargs)
        return cls._instance

    def __init__(self):
        if not hasattr(self, 'users'):  # Initialize only once
            self.users = {}
            self.pending_auth_codes = {}  # Stores pending auth codes and their expiry times
            self.auth_lock = threading.Lock()  # Lock for thread-safe access

    def generateUserId(self):
        return "user" + str(uuid.uuid4())

    def register(self, email, password, first_name, last_name):
        """
        Unified register function.
        - Sends an authentication code.
        - Verifies the code interactively.
        - Completes the registration.
        """
        if email in self.users:
            raise Exception("המשתמש כבר קיים במערכת.")

        if not self.is_valid_email(email):
            raise Exception("האימייל אינו תקין.")

        if not self.is_valid_password(password):
            raise Exception("הסיסמה אינה תקינה.")

        # Send authentication code
        self.send_auth_code(email, first_name)
        return {"message": f"קוד אימות נשלח למייל {email}"}

    def register_authentication_part(self, email, auth_code: str):
        # Interactively verify the code # Allow up to 3 attempts
        try:
            stored_code, expiry_time = self.pending_auth_codes[email]
            if auth_code == stored_code:
                if datetime.datetime.now() <= expiry_time:
                    return {"message": "עוברים למעבר על תנאי השימוש"}
                else:
                    logging.error("Authentication failed. The code has expired.")
                    raise Exception("אימות נכשל. הקוד פג תוקף.")
            else:
                logging.error("Incorrect authentication code.")
                raise Exception("קוד אימות שגוי.")
        except Exception as e:
            logging.error(f"Attempt  failed: {e}")
            raise Exception("האימות נכשל. הרשמה בוטלה.")


    def register_termOfUse_part(self, email, password, first_name, last_name):
        # Interactively verify the code
        try:
                id = self.generateUserId()
                user = User(id, email, password, first_name, last_name)
                user.login()
                self.users[email] = user
                logging.info(f"User {first_name} {last_name} registered successfully.")
                return {"message": f"User {first_name} {last_name} registered successfully."}
        except Exception as e:
                raise Exception("האישור נכשל. הרשמה בוטלה.")

    def get_user_courses(self, user_id):
        curr_user = self.users[user_id]
        if curr_user is None:
            return []
        return curr_user.getCourses()


    def is_valid_email(self,email):
        """Validate email domain."""
        return bool(re.match(r".+@(post\.bgu\.ac\.il|bgu\.ac\.il)$", email))

    def is_valid_password(self,password):
        """
        Validate the password.
        Password must:
        - Be at least 8 characters long
        - Contain at least one uppercase letter
        - Contain at least one lowercase letter
        - Contain at least one number
        - Contain at least one special character: {, }, [, ], !, @, $, %, ^, &, *, (, ), +
        """
        # Check for minimum length
        if len(password) < 8:
            return False

        # Regular expressions for each condition
        has_uppercase = re.search(r"[A-Z]", password)
        has_lowercase = re.search(r"[a-z]", password)
        has_number = re.search(r"[0-9]", password)
        has_special = re.search(r"[{}\[\]!@\$%\^&\*\(\)\+]", password)

        # Return True only if all conditions are met
        return bool(has_uppercase and has_lowercase and has_number and has_special)

    def send_auth_code(self,email, first_name):
        """Generate and send an authentication code via email."""
        auth_code = random.randint(100000, 999999)
        auth_code = str(auth_code)
        auth_code_expiry = datetime.datetime.now() + datetime.timedelta(minutes=3)
        self.pending_auth_codes[email] =(auth_code, auth_code_expiry)

        sender_email = os.getenv("EMAIL_ADDRESS")
        sender_password = os.getenv("EMAIL_PASSWORD")
        smtp_server = "smtp.gmail.com"
        smtp_port = 587

        subject = "קוד האימות שלך"
        message = (f"שלום {first_name},\n\n"
                   f"קוד האימות שלך עבור NegevNerds הוא: {auth_code}\n"
                   f"הקוד תקף למשך 3 דקות.\n\n"
                   f"תודה רבה!")
        msg = MIMEText(message)
        msg["Subject"] = subject
        msg["From"] = sender_email
        msg["To"] = email

        try:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)
            logging.info(f"Authentication code sent to {email}")
        except Exception as e:
            logging.error(f"Failed to send authentication code: {e}")
            raise Exception("Failed to send authentication code.")
    
    
    def login(self, email, password):
        """Authenticate the user by checking the email and password."""
        
        # Check if the email exists in the system
        user = self.users.get(email)  # Use .get() to avoid KeyError
        if user is None:
            raise UserOrPasswordIncorrectError()
        
        # Check if the password matches
        if user.password != password:
            raise UserOrPasswordIncorrectError()
        
        user.login()
        logging.info(f"Login successful for user: {email}")
        message = "התחברות בוצעה בהצלחה"
        return message
 
    def logout(self, email):
        # Check if the user exists
        user = self.users.get(email)
        if user is None:
            raise UserOrPasswordIncorrectError()
        if not user.loggedIn:
            raise UserIsNotLoggedInError(email)
        user.logout()
        
        logging.info(f"User {email} logged out successfully.")
        message = "התנתקות בוצעה בהצלחה"
        return message

    def registerToCourse(self, courseId, userId):
        """Add user to course (through User object)."""
        user = self.users.get(userId)
        if user:
            user.registerToCourse(courseId)
        else:
            raise UserDoesnotExistsError()
        
    def editUserProfile(self, email, **kwargs):
        """Edit the user's profile details."""
        user = self.users.get(email)
        if user:
            user.editProfile(**kwargs)
            return "Profile updated successfully"
        else:
            raise UserDoesnotExistsError()


    def getUser(self, user_id):
        return self.users[user_id]
