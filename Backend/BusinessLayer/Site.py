import json

class Site:
    def __init__(self, userController):
        self.userController = userController

    def register(self, email, password, first_name, last_name):
        """Register a new user."""
        try:
            success = self.userController.register(email, password, first_name, last_name)

            if success:
                return "User registered successfully."
        except Exception as e:
            return f"Error: {e}"

    def login(self, email, password):
        """Log the user in."""
        try:
            result = self.userController.login(email, password)
            return result  # Return the result from the controller
        except Exception as e:
            return f"Error: {e}"

    def logout(self, email):
        """Log the user out."""
        try:
            result = self.userController.logout(email)
            return result  # Return the result from the controller
        except Exception as e:
            return f"Error: {e}"