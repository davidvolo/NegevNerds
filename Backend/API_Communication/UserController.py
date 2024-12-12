import json

from flask import Flask, request, jsonify, Blueprint
from flask_cors import CORS, cross_origin

from Backend.BusinessLayer.Course.CourseFacade import CourseFacade
from Backend.BusinessLayer.NegevNerds import NegevNerds
from Backend.BusinessLayer.PDFAnalyzer.FileManager import FileManager
from Backend.BusinessLayer.User.UserFacade import UserFacade
from Backend.ServiceLayer.ServiceLayer import ServiceLayer

user_controller = Blueprint('user_controller', __name__)

CORS(user_controller, resources={
    r"/api/*": {
        "origins": "*",  # Or specify exact origin like "http://localhost:3000"
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})


serviceLayer = ServiceLayer(NegevNerds("../"))


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




@user_controller.route('/api/register', methods=['POST', 'OPTIONS'])
@cross_origin()
def register():
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
        result = serviceLayer.register(email, password, first_name, last_name)

        # Parse the JSON string
        parsed_result = json.loads(result)

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

@user_controller.route('/api/register_authentication_part', methods=['POST', 'OPTIONS'])
@cross_origin()
def register_authentication_part():
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
        if not all(key in data for key in ['auth_code', 'email']):
            return jsonify({
                "success": False,
                "message": "Missing required fields"
            }), 400

        # Extract data
        auth_code = data.get('auth_code')

        email = data.get('email')


        # Call the service layer's register method directly
        result = serviceLayer.register_authentication_part(email, auth_code)

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
    
@user_controller.route('/api/register_termOfUse_part', methods=['POST', 'OPTIONS'])
@cross_origin()
def register_termOfUse_part():
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
        result = serviceLayer.register_termOfUse_part(email, password, first_name, last_name)

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

@user_controller.route('/api/login', methods=['POST', 'OPTIONS'])
@cross_origin()
def login_user():
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
        if not all(key in data for key in ['email', 'password']):
            return jsonify({
                "success": False,
                "message": "Missing required fields"
            }), 400

        # Extract data
        email = data.get('email')
        password = data.get('password')

        # Call the service layer's login method directly
        result = serviceLayer.login(email, password)

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
        print(f"Error in login: {str(e)}")
        return jsonify({
            "success": False,
            "message": "An unexpected error occurred",
            "error": str(e)
        }), 500


@user_controller.route('/api/logout', methods=['POST', 'OPTIONS'])
@cross_origin()
def logout_user():
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
        if not all(key in data for key in ['email']):
            return jsonify({
                "success": False,
                "message": "Missing required fields"
            }), 400

        # Extract data
        email = data.get('email')

        # Call the service layer's login method directly
        result = serviceLayer.logout(email)

        # Parse the JSON string
        parsed_result = json.loads(result)

        return parse_jsonify(parsed_result)

    except json.JSONDecodeError:
        # Handle JSON decoding error
        return jsonify({
            "success": False,
            "message": "Invalid JSON response from service"
        }), 500
    except Exception as e:
        print(f"Error in logout: {str(e)}")
        return jsonify({
            "success": False,
            "message": "An unexpected error occurred",
            "error": str(e)
        }), 500


@user_controller.route('/api/get_user_courses', methods=['GET', 'OPTIONS'])
@cross_origin()
def get_user_courses():
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
        if not all(key in data for key in ['user_id']):
            return jsonify({
                "success": False,
                "message": "Missing required fields"
            }), 400

        # Extract data
        user_id = data.get('user_id')

        # Call the service layer's login method directly
        result = serviceLayer.get_user_courser(user_id)

        # Parse the JSON string
        parsed_result = json.loads(result)

        return parse_jsonify(parsed_result)

    except json.JSONDecodeError:
        # Handle JSON decoding error
        return jsonify({
            "success": False,
            "message": "Invalid JSON response from service"
        }), 500
    except Exception as e:
        print(f"Error in logout: {str(e)}")
        return jsonify({
            "success": False,
            "message": "An unexpected error occurred",
            "error": str(e)
        }), 500



