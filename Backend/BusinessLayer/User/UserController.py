import smtplib
import random
import datetime
import os
import re
from email.mime.text import MIMEText
import logging
from Backend.BusinessLayer.Util.Exceptions import *
from Users.user import User

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class UserController:
    def __init__(self):
        self.users = {}  # This will store users with email as the key
        self.pending_auth_codes = {}  # To store pending auth codes and their expiry times
        
    
    def generateUserId(self):
        return len(self.users) + 1
    
    def register_step1(self, email, password, first_name, last_name):
        """Step 1: Send authentication code to the user's email."""
        # Check if the user already exists
        if email in self.users:
            raise UserAlreadyExistsError()
        
        # Validate email domain
        if not self.check_valid_email(email):
            raise InvalidEmailDomainError()

        # Send authentication code and store it in the system
        auth_code, auth_code_expiry = self.send_auth_code(email, first_name)
        self.pending_auth_codes[email] = {'code': auth_code, 'expiry': auth_code_expiry}

        logging.info("Authentication code sent. Please enter the code to complete the registration.")
        return True
    
    def register_step2(self, email, entered_code, password, first_name, last_name):
        """Step 2: Verify the authentication code and complete the registration."""
        # Check if the auth code exists and is still valid
        if email not in self.pending_auth_codes:
            logging.error("No pending authentication code found for this email.")
            raise AuthenticationCodeError()

        # Get the stored auth code and expiry time
        stored_data = self.pending_auth_codes[email]
        auth_code = stored_data['code']
        auth_code_expiry = stored_data['expiry']

        # Verify the authentication code
        if not self.verify_auth_code(auth_code, auth_code_expiry, entered_code):
            raise AuthenticationCodeError()

        # Add the user to the system if everything is valid
        user_id = self.generateUserId(self)
        user = User(user_id, email, password, first_name, last_name)
        self.users[email] = user
        del self.pending_auth_codes[email]  # Remove the pending auth code after successful registration

        logging.info(f"User {first_name} {last_name} registered successfully!")
        return True
    
    def is_valid_email(self, email):
        """Validate email domain."""
        return re.match(r".+@(post\.bgu\.ac\.il|bgu\.ac\.il)$", email)
    
    def send_auth_code(self, email, first_name):
        """Generate and send an authentication code via email."""
        auth_code = random.randint(100000, 999999)  # Generate a 6-digit code
        auth_code_expiry = datetime.datetime.now() + datetime.timedelta(minutes=3)  # Set expiry time

        # Email configuration
        sender_email = os.getenv("EMAIL_ADDRESS")
        sender_password = os.getenv("EMAIL_PASSWORD")
        smtp_server = "smtp.gmail.com"
        smtp_port = 587

        subject = "Your Authentication Code"
        message = (f"Hello {first_name},\n\n"
                   f"Your authentication code for NegevNerds is: {auth_code}\n"
                   f"This code is valid for 3 minutes.\n\n"
                   f"Thank you!")
        msg = MIMEText(message)
        msg["Subject"] = subject
        msg["From"] = sender_email
        msg["To"] = email

        try:
            # Connect to the SMTP server and send email
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()  # Secure the connection
                server.login(sender_email, sender_password)
                server.sendmail(sender_email, email, msg.as_string())
            logging.info(f"Authentication code sent to {email}.")
            return auth_code, auth_code_expiry
        except Exception as e:
            logging.error(f"Failed to send authentication code. Error: {e}")
            raise EmailSendingError() 
        
    def verify_auth_code(self, auth_code, auth_code_expiry, entered_code):
            """Verify the authentication code entered by the user."""
            try:
                entered_code = int(entered_code)  # Convert entered code to integer if necessary

                # Check if the entered code matches the generated auth code
                if entered_code != auth_code:
                    logging.error("Authentication failed. Incorrect code.")
                    return False

                # Check if the code has expired
                if datetime.datetime.now() > auth_code_expiry:
                    logging.error("Authentication failed. The code has expired.")
                    return False

                return True  # Code is correct and not expired

            except ValueError:
                logging.error("Invalid input. Please enter a valid number.")
                return False
    
    def login(self, email, password):
        """Authenticate the user by checking the email and password."""
        
        # Check if the email exists in the system
        user = self.users.get(email)
        if user is None:
            raise UserOrPasswordIncorrectError()
        
        # Check if the password matches
        if user["password"] != password:
            raise UserOrPasswordIncorrectError()
        
        user.login()
        logging.info(f"Login successful for user: {email}")
        return "Login successful"
 
    def logout(self, email):
        # Check if the user exists
        user = self.users.get(email)
        if user is None:
            raise UserDoesnotExistsError()
        
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
