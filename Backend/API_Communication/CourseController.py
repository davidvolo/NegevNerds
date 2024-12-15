import json

from flask import Blueprint, request, jsonify
from flask_cors import cross_origin, CORS

from Backend.BusinessLayer.Course.CourseFacade import CourseFacade
from Backend.BusinessLayer.NegevNerds import NegevNerds
from Backend.BusinessLayer.PDFAnalyzer.FileManager import FileManager
from Backend.BusinessLayer.User.UserFacade import UserFacade
from Backend.ServiceLayer.ServiceLayer import ServiceLayer

course_controller = Blueprint('course_controller', __name__)

CORS(course_controller, resources={
    r"/api/*": {
        "origins": "*",  # Or specify exact origin like "http://localhost:3000"
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})


serviceLayer = ServiceLayer("../")


def parse_jsonify(parsed_result):
    # Check the status and return appropriate response
    if parsed_result['status'] == 'success':
        return jsonify({
            "success": True,
            "message": parsed_result['message']
        }), 200
    else:
        return jsonify({
            "success": False,
            "message": parsed_result['message']
        }), 400


@course_controller.route('/api/course/register_to_course', methods=['POST', 'GET', 'OPTIONS'])
@cross_origin()
def register_to_course():
    # Handle OPTIONS preflight request
    if request.method == 'OPTIONS':
        response = jsonify(success=True)
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response

    try:
        # Extract data from the request
        data = request.get_json()

        # Validate input
        if not all(key in data for key in ['course_id', 'user_id']):
            return jsonify({
                "success": False,
                "message": "Missing required fields"
            }), 400


        # Extract data
        course_id = data.get('course_id')
        user_id = data.get('user_id')


        # Call the service layer's register method directly
        result = serviceLayer.register_to_course(course_id, user_id)

        # Parse the JSON string
        parsed_result = json.loads(result)

        # Check the status and return appropriate response
        return parse_jsonify(parsed_result)

    except json.JSONDecodeError:
        # Handle JSON decoding error
        return jsonify({
            "success": False,
            "message": "Invalid JSON response from service"
        }), 500
    except Exception as e:
        print(f"Error in registration: {str(e)}")
        return jsonify({
            "success": False,
            "message": "An unexpected error occurred",
            "error": str(e)
        }), 500

@course_controller.route('/api/course/open_course', methods=['POST', 'OPTIONS'])
@cross_origin()
def open_course():
    if request.method == 'OPTIONS':
        response = jsonify(success=True)
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response

    try:
        print("Received a request to open_course.")

        # Check if all required form data is present
        if 'course_id' not in request.form or 'user_id' not in request.form or 'name' not in request.form:
            print("Missing required form fields.")
            return jsonify({"success": False, "message": "Missing required fields"}), 400

        if 'syllabus_content_pdf' not in request.files:
            print("Syllabus file not found in request.")
            return jsonify({"success": False, "message": "Syllabus file is required"}), 400

        # Extract data
        course_id = request.form.get('course_id')
        user_id = request.form.get('user_id')
        name = request.form.get('name')
        syllabus_file = request.files['syllabus_content_pdf']

        # Save file
        file_path = f"/Users/davidvolodarsky/Desktop/Semeters/Semester_G/NegevNerds/sylbus_analyzer/uplods/{syllabus_file.filename}"
        syllabus_file.save(file_path)
        print(f"File saved to {file_path}")
        print(f"user id {user_id}")

        # Call the service layer
        result = serviceLayer.open_course(user_id, course_id, name, file_path)
        parsed_result = json.loads(result)
        print(f"Service layer response: {parsed_result}")

        # Construct and return response
        return jsonify({
            "success": parsed_result.get("status") == "success",  # Set success as boolean
            "message": parsed_result.get("message")  # Return message from service layer
        }), 200

    except Exception as e:
        print(f"Error in open_course: {str(e)}")
        return jsonify({
            "success": False,
            "message": "An unexpected error occurred",
            "error": str(e)
        }), 500


@course_controller.route('/api/course/remove_course', methods=['POST', 'GET', 'OPTIONS'])
@cross_origin()
def remove_course():
    # Handle OPTIONS preflight request
    if request.method == 'OPTIONS':
        response = jsonify(success=True)
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response

    try:
        # Extract data from the request
        data = request.get_json()

        # Validate input
        if not all(key in data for key in ['course_id', 'user_id']):
            return jsonify({
                "success": False,
                "message": "Missing required fields"
            }), 400

        # Extract data
        course_id = data.get('course_id')
        user_id = data.get('user_id')


        # Call the service layer's register method directly
        result = serviceLayer.remove_course(course_id, user_id)

        # Parse the JSON string
        parsed_result = json.loads(result)

        # Check the status and return appropriate response
        return parse_jsonify(parsed_result)

    except json.JSONDecodeError:
        # Handle JSON decoding error
        return jsonify({
            "success": False,
            "message": "Invalid JSON response from service"
        }), 500
    except Exception as e:
        print(f"Error in registration: {str(e)}")
        return jsonify({
            "success": False,
            "message": "An unexpected error occurred",
            "error": str(e)
        }), 500


@course_controller.route('/api/course/remove_student_from_course', methods=['POST', 'GET', 'OPTIONS'])
@cross_origin()
def remove_student_from_course():
    # Handle OPTIONS preflight request
    if request.method == 'OPTIONS':
        response = jsonify(success=True)
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response

    try:
        # Extract data from the request
        data = request.get_json()

        # Validate input
        if not all(key in data for key in ['course_id', 'user_id']):
            return jsonify({
                "success": False,
                "message": "Missing required fields"
            }), 400

        # Extract data
        course_id = data.get('course_id')
        user_id = data.get('user_id')


        # Call the service layer's register method directly
        result = serviceLayer.remove_student_from_course(course_id, user_id)

        # Parse the JSON string
        parsed_result = json.loads(result)

        # Check the status and return appropriate response
        return parse_jsonify(parsed_result)

    except json.JSONDecodeError:
        # Handle JSON decoding error
        return jsonify({
            "success": False,
            "message": "Invalid JSON response from service"
        }), 500
    except Exception as e:
        print(f"Error in registration: {str(e)}")
        return jsonify({
            "success": False,
            "message": "An unexpected error occurred",
            "error": str(e)
        }), 500


@course_controller.route('/api/course/get_all_courses', methods=[ 'GET', 'OPTIONS'])
@cross_origin()
def get_all_courses():
    # Handle OPTIONS preflight request
    if request.method == 'OPTIONS':
        response = jsonify(success=True)
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response

    try:
        # Extract data from the request

        result = serviceLayer.get_all_courses()

        # Parse the JSON string
        parsed_result = json.loads(result)

        # Check the status and return appropriate response
        return parse_jsonify(parsed_result)

    except json.JSONDecodeError:
        # Handle JSON decoding error
        return jsonify({
            "success": False,
            "message": "Invalid JSON response from service"
        }), 500
    except Exception as e:
        print(f"Error in registration: {str(e)}")
        return jsonify({
            "success": False,
            "message": "An unexpected error occurred",
            "error": str(e)
        }), 500


@course_controller.route('/api/course/get_course_topics', methods=['GET', 'OPTIONS'])
@cross_origin()
def get_course_topics():
    # Handle OPTIONS preflight request
    if request.method == 'OPTIONS':
        response = jsonify(success=True)
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response

    try:
        # Extract data from the request

        data = request.get_json()

        # Validate input
        if not all(key in data for key in ['course_id']):
            return jsonify({
                "success": False,
                "message": "Missing required fields"
            }), 400

        # Extract data
        course_id = data.get('course_id')

        result = serviceLayer.get_course_topics(course_id)

        # Parse the JSON string
        parsed_result = json.loads(result)

        # Check the status and return appropriate response
        return parse_jsonify(parsed_result)

    except json.JSONDecodeError:
        # Handle JSON decoding error
        return jsonify({
            "success": False,
            "message": "Invalid JSON response from service"
        }), 500
    except Exception as e:
        print(f"Error in registration: {str(e)}")
        return jsonify({
            "success": False,
            "message": "An unexpected error occurred",
            "error": str(e)
        }), 500
