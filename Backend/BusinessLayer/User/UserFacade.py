import smtplib
import random
import datetime
import os
import re
import threading
from email.mime.text import MIMEText
import logging
from Backend.BusinessLayer.User.User import User
from Backend.BusinessLayer.Util.Exceptions import *

# from Util.Exceptions import *
# from BusinessLayer.User.User import User
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class UserFacade:
    def __init__(self):
        self.users = {}
        self.pending_auth_codes = {}  # Stores pending auth codes and their expiry times
        self.auth_lock = threading.Lock()  # Lock for thread-safe access
    
    def generateUserId(self):
        return str(len(self.users) + 1)

    def register(self, email, password, first_name, last_name):
        """
        Unified register function.
        - Sends an authentication code.
        - Verifies the code interactively.
        - Completes the registration.
        """
        if email in self.users:
            raise Exception("User already exists.")

        if not self.is_valid_email(email):
            raise Exception("Invalid email")
        
        if not self.is_valid_password(password):
            raise Exception("Invalid password")

        # Send authentication code
        self.send_auth_code(email, first_name)

        # Interactively verify the code
        for attempt in range(3):  # Allow up to 3 attempts
            try:
                code = int(input(f"Enter the authentication code sent to {email}: "))
                if code ==  self.pending_auth_codes[email][0]:
                    if datetime.datetime.now() <= self.pending_auth_codes[email][1]:
                        # Display Terms of Use
                        with open("/Users/davidvolodarsky/Desktop/Semeters/Semester_G/NegevNerds/NegevNerds/Backend/terms_of_use.txt", "r", encoding="utf-8") as terms_file:
                            terms = terms_file.read()
                            print("\n" + terms + "\n")
                        
                        accept_terms = input("האם אתה מקבל את תנאי השימוש? (כן/לא): ").strip().lower()
                        if accept_terms != "כן":
                            logging.error("User did not accept the terms of use.")
                            raise Exception("Registration aborted: terms of use not accepted.")

                        id = self.generateUserId()
                        user = User(id,email,password,first_name,last_name)
                        user.login()
                        self.users[email] = user
                        logging.info(f"User {first_name} {last_name} registered successfully.")
                        return {"message": f"User {first_name} {last_name} registered successfully."}
                    else:
                        logging.error("Authentication failed. The code has expired.")
                        raise Exception("Authentication code expired.")
                else:
                    logging.error("Incorrect authentication code.")
                    raise Exception("Incorrect authentication code.")
            except Exception as e:
                logging.error(f"Attempt {attempt + 1} failed: {e}")
                if attempt == 2:
                    raise Exception("Failed to authenticate. Registration aborted.")
        return {"message": "Registration process failed."}
    
    
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
        auth_code_expiry = datetime.datetime.now() + datetime.timedelta(minutes=3)
        self.pending_auth_codes[email] = (auth_code,auth_code_expiry)

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
        return "Login successful"
 
    def logout(self, email):
        # Check if the user exists
        user = self.users.get(email)
        if user is None:
            raise UserOrPasswordIncorrectError()
        if not user.loggedIn:
            raise UserIsNotLoggedInError(email)
        user.logout()
        
        logging.info(f"User {email} logged out successfully.")
        return "Logout successful"

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
