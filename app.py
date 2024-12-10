from flask import Flask
from flask_cors import CORS
from Backend.API_Communication.UserController import user_controller
from Backend.API_Communication.CourseController import course_controller


app = Flask(__name__)
CORS(app, resources={
    r"/api/*": {
        "origins": "*",  # Or specify exact origin like "http://localhost:3000"
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})
# Register controllers
app.register_blueprint(user_controller)
app.register_blueprint(course_controller)

def main():
    """
    Entry point for the application.
    """
    print("Starting the Exam Preparation System API...")
    app.run(debug=True, host='0.0.0.0', port=5000)


if __name__ == "__main__":
    main()


