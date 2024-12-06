import random
import re
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv
import os
import datetime

# Load environment variables from .env file
load_dotenv()

class User:
    def __init__(self, first_name, last_name, email, password):
        self.first_name = first_name
        self.last_name = last_name
        self.email = email
        self.password = password
        self.is_authenticated = False
        self.is_logged_in = False
        self.auth_code = None
        self.auth_code_expiry = None  # To store the expiration time of the auth code

    @staticmethod
    def is_valid_email(email):
        """Validate email domain."""
        return re.match(r".+@(post\.bgu\.ac\.il|bgu\.ac\.il)$", email)

    def send_auth_code(self):
        """Generate and send an authentication code via email."""
        self.auth_code = random.randint(100000, 999999)  # Generate a 6-digit code
        self.auth_code_expiry = datetime.datetime.now() + datetime.timedelta(minutes=3)  # Set expiry time

        # Email configuration
        sender_email = os.getenv("EMAIL_ADDRESS")
        sender_password = os.getenv("EMAIL_PASSWORD")
        smtp_server = "smtp.gmail.com"
        smtp_port = 587

        subject = "קוד האימות שלך"
        message = ("\u202B"  # Right-to-Left Embedding (RLE)
                    f"שלום {self.first_name},\n\n"
                    f"קוד האימות שלך עבור NegevNerds הוא: {self.auth_code}\n"
                    f"הקוד תקף למשך 3 דקות.\n\n"
                    f"תודה רבה!")
        msg = MIMEText(message)
        msg["Subject"] = subject
        msg["From"] = sender_email
        msg["To"] = self.email

        # Send the email
        try:
            with smtplib.SMTP(smtp_server, smtp_port) as server:
                server.starttls()
                server.login(sender_email, sender_password)
                server.send_message(msg)
            print("Authentication code sent successfully.")
        except Exception as e:
            print(f"Failed to send authentication code: {e}")


    def register(self):
        """Register the user."""
        if not self.is_valid_email(self.email):
            print("Invalid email domain. Please use a @post.bgu.ac.il or @bgu.ac.il email.")
            return False
        
        print("Registering user...")
        self.send_auth_code()  # Send an authentication code
        code = int(input("Enter the authentication code sent to your email: "))
        if code == self.auth_code:
            if datetime.datetime.now() <= self.auth_code_expiry:
                self.is_authenticated = True
                print(f"User {self.first_name} {self.last_name} registered successfully!")
                return True
            else:
                print("Authentication failed. The code has expired.")
                return False
        else:
            print("Authentication failed. Incorrect code.")
            return False

    def login(self, password):
        """Log in the user."""
        if not self.is_authenticated:
            print("User not authenticated. Please register first.")
            return False

        if self.password == password:
            self.is_logged_in = True
            print(f"User {self.first_name} logged in successfully!")
            return True
        else:
            print("Login failed. Incorrect password.")
            return False

    def logout(self):
        """Log out the user."""
        if self.is_logged_in:
            self.is_logged_in = False
            print(f"User {self.first_name} logged out successfully.")
        else:
            print("User is not logged in.")


# Example Usage
if __name__ == "__main__":
    # Create a new user
    user = User(first_name="David", last_name="Volodarsky", email="volodavi@post.bgu.ac.il", password="securepassword123")
    
    # Register the user
    if user.register():
        # Log in the user
        user.login(password="securepassword123")
        
        # Log out the user
        user.logout()
