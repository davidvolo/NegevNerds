class BaseError(Exception):
    """Base class for all custom exceptions."""
    def __init__(self, message="An error occurred", code=None):
        self.message = message
        self.code = code  # Optionally, you can include a code for each error
        super().__init__(self.message)

class UserAlreadyExistsError(BaseError):
    """Exception raised when the user already exists."""
    def __init__(self, email):
        message = f"User with email {email} already exists."
        super().__init__(message, code=409)  # 409 is commonly used for conflict errors

class InvalidEmailDomainError(BaseError):
    """Exception raised for invalid email domain."""
    def __init__(self, email):
        message = f"Invalid email domain for {email}. Please use a @post.bgu.ac.il or @bgu.ac.il email."
        super().__init__(message, code=400)  # 400 is commonly used for bad requests

class AuthenticationCodeError(BaseError):
    """Exception raised for authentication code errors."""
    def __init__(self, message="Authentication failed. Invalid or expired code."):
        super().__init__(message, code=401)  # 401 is commonly used for unauthorized errors

class EmailSendingError(BaseError):
    """Exception raised when email sending fails."""
    def __init__(self, message="Failed to send authentication code"):
        super().__init__(message, code=500)  # 500 can be used for server errors
        
class UserOrPasswordIncorrectError(BaseError):
    """Exception raised when password or email is incorrect."""
    def __init__(self):
        message = f"Invalid email or password. Please try again."
        super().__init__(message, code=409)  # 409 is commonly used for conflict errors
        
class UserDoesnotExistsError(BaseError):
    """Exception raised when the user is not exist."""
    def __init__(self, email):
        message = f"User with email {email} not exists."
        super().__init__(message, code=409)  # 409 is commonly used for conflict errors
        
class UserAlreadyRegisterToCourse(BaseError):
    """Exception raised when the user is already register to course."""
    def __init__(self):
        message = f"User is already registered to course."
        super().__init__(message, code=409)  # 409 is commonly used for conflict errors
        
class UserIsNotRegisterToCourse(BaseError):
    """Exception raised when the user is not register to course."""
    def __init__(self):
        message = f"User is not registered to course."
        super().__init__(message, code=409)  # 409 is commonly used for conflict errors
        
class CourseIsNotExist(BaseError):
    """Exception raised when the user is not exist."""
    def __init__(self, course_Id):
        message = f"Cousre {course_Id} is not exist."
        super().__init__(message, code=409)  # 409 is commonly used for conflict errors