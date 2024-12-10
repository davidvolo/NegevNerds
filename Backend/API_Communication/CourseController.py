import json

from flask import Blueprint, request, jsonify
from flask_cors import cross_origin

from Backend.BusinessLayer.Course.CourseFacade import CourseFacade
from Backend.BusinessLayer.NegevNerds import NegevNerds
from Backend.BusinessLayer.PDFAnalyzer.FileManager import FileManager
from Backend.BusinessLayer.User.UserFacade import UserFacade
from Backend.ServiceLayer.ServiceLayer import ServiceLayer

course_controller = Blueprint('course_controller', __name__)


serviceLayer = ServiceLayer(NegevNerds(UserFacade(), CourseFacade(), FileManager("../")))
@course_controller.route('/api/courses', methods=['POST', 'GET', 'OPTIONS'])
@cross_origin()
def register_user():
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
        if not all(key in data for key in ['email', 'password', 'first_name', 'last_name']):
            return jsonify({
                "success": False,
                "message": "Missing required fields"
            }), 400

        # Extract data
        email = data.get('email')
        password = data.get('password')
        first_name = data.get('first_name')
        last_name = data.get('last_name')

        # Call the service layer's register method directly
        result = serviceLayer.regis(email, password, first_name, last_name)

        # Parse the JSON string
        parsed_result = json.loads(result)

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
