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


@course_controller.route('/api/course/open_course', methods=['POST', 'GET', 'OPTIONS'])
@cross_origin()
def open_course():
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
        if not all(key in data for key in ['course_id', 'user_id',  'name', 'syllabus_content', 'course_topics']):
            return jsonify({
                "success": False,
                "message": "Missing required fields"
            }), 400

        # Extract data
        course_id = data.get('course_id')
        user_id = data.get('user_id')
        name = data.get('name')
        syllabus_content = data.get('syllabus_content')
        course_topics = data.get('course_topics')

        # Call the service layer's register method directly
        result = serviceLayer.open_course(user_id, course_id, name, syllabus_content, course_topics)

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