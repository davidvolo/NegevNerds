import json
from datetime import timedelta
import os
from flask import Flask, request, jsonify, Blueprint, send_file
from flask_cors import CORS, cross_origin
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity

from Backend.BusinessLayer.NegevNerds import NegevNerds
from Backend.ServiceLayer.ServiceLayer import ServiceLayer
import logging

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
        print("here")
        print(parsed_result)
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
        if not all(key in data for key in ['email', 'password','password_confirm', 'first_name', 'last_name']):
            return jsonify({
                "success": False,
                "message": "Missing required fields"
            }), 400

        # Extract data
        email = data.get('email')
        email = email.lower()
        password = data.get('password')
        first_name = data.get('first_name')
        last_name = data.get('last_name')
        password_confirm = data.get('password_confirm')

        # Call the service layer's register method directly
        result = serviceLayer.register(email, password,password_confirm, first_name, last_name)

        # Parse the JSON string
        # parsed_result = json.loads(result)

        # # return parse_jsonify(parsed_result)
    
        # if result['status'] == "success":
        #     return jsonify({
        #         "success": True,
        #         "message": parsed_result['message'],
        #         "password": parsed_result['password']  # Include password if needed
        #     }),200
        
        if result['status'] == "success":
            return jsonify({"success": True, "message": result["message"], "password": result["password"]}), 200
        return jsonify({"success": False, "message": result["message"]}), 400

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
            user_id = parsed_result.get('user_id')  # assuming user_id is returned from your service layer
            access_token = create_access_token(identity=user_id, expires_delta=timedelta(hours=10))
            print("token: ", access_token)
            return jsonify({
                "success": True,
                "message": parsed_result['message'],
                "user_id": parsed_result['user_id'],  # Explicitly fetch user_id
                "access_token": access_token,  # Include the generated token in the response
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

# @user_controller.route('/api/login', methods=['POST', 'OPTIONS'])
# @cross_origin()
# def login_user():
#     # Handle OPTIONS preflight request
#     if request.method == 'OPTIONS':
#         response = jsonify(success=True)
#         response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
#         response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
#         response.headers.add('Access-Control-Allow-Methods', 'POST')
#         return response

#     try:
#         # Extract data from the request
#         data = request.get_json()

#         # Validate input
#         if not all(key in data for key in ['email', 'password']):
#             return jsonify({
#                 "success": False,
#                 "message": "Missing required fields"
#             }), 400

#         # Extract data
#         email = data.get('email')
#         password = data.get('password')

#         # Call the service layer's login method directly
#         result = serviceLayer.login(email, password)

#         # Parse the JSON string
#         parsed_result = json.loads(result)

#         # Check the status and return appropriate response
#         if parsed_result['status'] == 'success':
#             return jsonify({
#                 "success": True,
#                 "message": parsed_result['message'],
#                 "user_id": parsed_result['user_id'] , # Explicitly fetch user_id
#                 "first_name": parsed_result['first_name'],
#                 "last_name": parsed_result['last_name'],
#             }), 200
#         else:
#             return jsonify({
#                 "success": False,
#                 "message": parsed_result['message']
#             }), 400

#     except json.JSONDecodeError:
#         # Handle JSON decoding error
#         return jsonify({
#             "success": False,
#             "message": "Invalid JSON response from service"
#         }), 500
#     except Exception as e:
#         print(f"Error in login: {str(e)}")
#         return jsonify({
#             "success": False,
#             "message": "An unexpected error occurred",
#             "error": str(e)
#         }), 500
# @user_controller.route('/api/login', methods=['POST', 'OPTIONS'])
# @cross_origin()
# def login_user():
#     # Handle OPTIONS preflight request
#     if request.method == 'OPTIONS':
#         response = jsonify(success=True)
#         response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
#         response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
#         response.headers.add('Access-Control-Allow-Methods', 'POST')
#         return response

#     try:
#         # Extract data from the request
#         data = request.get_json()

#         # Validate input
#         if not data or not all(key in data for key in ['email', 'password']):
#             print("Login failed: Missing required fields")
#             return jsonify({
#                 "success": False,
#                 "message": "Missing required fields"
#             }), 400

#         # Extract email and password
#         email = data.get('email')
#         password = data.get('password')

#         # Log the login attempt
#         print(f"Login attempt: email={email}")

#         # Call the service layer's login method
#         result = serviceLayer.login(email, password)

#         # Parse the JSON string
#         parsed_result = json.loads(result)

#         # Check the status and return appropriate response
#         if parsed_result.get('status') == 'success':
#             print(f"Login successful for user: {email}")
#             return jsonify({
#                 "success": True,
#                 "message": parsed_result.get('message'),
#                 "user_id": parsed_result.get('user_id'),
#                 "first_name": parsed_result.get('first_name'),
#                 "last_name": parsed_result.get('last_name'),
#             }), 200
#         else:
#             print(f"Login failed for user: {email} - Reason: {parsed_result.get('message')}")
#             return jsonify({
#                 "success": False,
#                 "message": parsed_result.get('message', 'Login failed')
#             }), 400

#     except json.JSONDecodeError as e:
#         print(f"JSON Decode Error in login: {str(e)}")
#         return jsonify({
#             "success": False,
#             "message": "Invalid JSON response from service"
#         }), 500
#     except Exception as e:
#         print(f"Unexpected error in login: {str(e)}")
#         return jsonify({
#             "success": False,
#             "message": "An unexpected error occurred",
#             "error": str(e)
#         }), 500


@user_controller.route('/api/login', methods=['POST', 'OPTIONS'])
@cross_origin()
def login_user():
    if request.method == 'OPTIONS':
        response = jsonify(success=True)
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response

    try:
        data = request.get_json()

        # Validate input
        if not all(key in data for key in ['email', 'password']):
            print("Invalid request")
            return jsonify({
                "success": False,
                "message": "Missing required fields"
            }), 400

        email = data.get('email')
        password = data.get('password')

        # Call service layer
        result = serviceLayer.login(email, password)
        print("Raw result from serviceLayer:", result)

        parsed_result = json.loads(result)
        print("Parsed result:", parsed_result)

        # Validate parsed_result structure
        if not parsed_result or parsed_result.get('status') != 'success':
            print("Invalid request2")
            return jsonify({
                "success": False,
                "message": parsed_result.get('message', 'Login failed')
            }), 400

        user_id = parsed_result.get('user_id')  # assuming user_id is returned from your service layer
        access_token = create_access_token(identity=user_id, expires_delta=timedelta(hours=10))
        print("token: ", access_token)

        # Successful login response
        return jsonify({
            "success": True,
            "message": parsed_result.get('message'),
            "user_id": parsed_result.get('user_id'),
            "first_name": parsed_result.get('first_name'),
            "last_name": parsed_result.get('last_name'),
            "access_token": access_token,
        }), 200

    except Exception as e:
        print(f"Error in login: {str(e)}")
        return jsonify({
            "success": False,
            "message": "An unexpected error occurred",
            "error": str(e)
        }), 500


@user_controller.route('/api/logout', methods=['POST', 'OPTIONS'])
@cross_origin()
@jwt_required()
def logout_user():
    # Handle OPTIONS preflight request
    if request.method == 'OPTIONS':
        response = jsonify(success=True)
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response

    try:
        # Get user identity from the JWT token
        current_user = get_jwt_identity()  # שמור את המידע מתוך ה-JWT
        print(f"Current user from JWT: {current_user}")  # הדפסת המידע שנמצא בטוקן

        # Call the service layer's logout method directly
        result = serviceLayer.logout(current_user)
        print(f"Logout result from service layer: {result}")  # הדפסת תוצאת פעולת ה-logout

        # Parse the JSON string
        parsed_result = json.loads(result)
        print(f"Parsed result: {parsed_result}")  # הדפסת התוצאה אחרי הפענוח

        return parse_jsonify(parsed_result)

    except json.JSONDecodeError:
        # Handle JSON decoding error
        print("Error decoding JSON")  # הדפסת הודעה אם יש בעיה בפענוח ה-JSON
        return jsonify({
            "success": False,
            "message": "Invalid JSON response from service"
        }), 500
    except Exception as e:
        print(f"Error in logout: {str(e)}")  # הדפסת שגיאה במקרה של בעיה אחרת
        return jsonify({
            "success": False,
            "message": "An unexpected error occurred",
            "error": str(e)
        }), 500


@user_controller.route('/api/get_user_courses', methods=['GET', 'OPTIONS'])
@cross_origin()
@jwt_required()
def get_user_courses():
    # Handle OPTIONS preflight request
    if request.method == 'OPTIONS':
        response = jsonify(success=True)
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'GET')
        return response

    try:
        current_user = get_jwt_identity()

        # Fetch the user courses from the service layer
        result = serviceLayer.get_user_courses(current_user)  # השתמש במידע מתוך הטוקן

        result = json.loads(result)  # Convert the JSON string to a Python dict

        if 'data' in result:
            parsed_result = result["data"]  # Now we're getting only the courses list

        # Return the courses as JSON response
        return jsonify({
            "success": True,
            "courses": parsed_result
        }), 200

    except Exception as e:
        print(f"Error in getting user courses: {str(e)}")
        return jsonify({
            "success": False,
            "message": "An unexpected error occurred",
            "error": str(e)
        }), 500

    except json.JSONDecodeError:
        # Handle JSON decoding error
        return jsonify({
            "success": False,
            "message": "Invalid JSON response from service"
        }), 500
    except Exception as e:
        print(f"Error in get user courses: {str(e)}")
        return jsonify({
            "success": False,
            "message": "An unexpected error occurred",
            "error": str(e)
        }), 500


@user_controller.route('/api/get_user_name', methods=['GET', 'OPTIONS'])
@cross_origin()
@jwt_required()
def get_user_name():
    # Handle OPTIONS preflight request
    if request.method == 'OPTIONS':
        response = jsonify(success=True)
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'GET')
        return response

    try:
        user_id = request.args.get('user_id')  # Get the user_id from query parameters

        # Fetch the user courses from the service layer
        result = serviceLayer.get_user_name(user_id)

        result = json.loads(result)  # Convert the JSON string to a Python dict

        if 'data' in result:
            parsed_result = result["data"]  # Now we're getting only the courses list

        # Return the courses as JSON response
        return jsonify({
            "success": True,
            "data": parsed_result
        }), 200

    except Exception as e:
        print(f"Error in getting user name: {str(e)}")
        return jsonify({
            "success": False,
            "message": "An unexpected error occurred",
            "error": str(e)
        }), 500

    except json.JSONDecodeError:
        # Handle JSON decoding error
        return jsonify({
            "success": False,
            "message": "Invalid JSON response from service"
        }), 500
    
@user_controller.route('/api/auth/forgot-password', methods=['POST', 'OPTIONS'])
@cross_origin()
def forgot_password():
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
        email = data.get('email')

        if not email:
            return jsonify({
                "success": False,
                "message": "כתובת אימייל נדרשת"
            }), 400

        # Call the service layer method to handle logic
        result = serviceLayer.forgot_password(email)

        # Parse response from service
        parsed_result = json.loads(result)

        if parsed_result.get("status") == "success":
            return jsonify({
                "success": True,
                "message": parsed_result.get("message")
            }), 200
        else:
            return jsonify({
                "success": False,
                "message": parsed_result.get("message")
            }), 404

    except json.JSONDecodeError:
        return jsonify({
            "success": False,
            "message": "שגיאה פנימית: פורמט JSON לא תקין"
        }), 500

    except Exception as e:
        print(f"Error in forgot_password: {str(e)}")
        return jsonify({
            "success": False,
            "message": "שגיאה לא צפויה התרחשה",
            "error": str(e)
        }), 500

@user_controller.route('/api/auth/verify-reset-code', methods=['POST', 'OPTIONS'])
@cross_origin()
def verify_reset_code():
    if request.method == 'OPTIONS':
        response = jsonify(success=True)
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response

    try:
        data = request.get_json()
        email = data.get('email')
        code = data.get('code')

        if not email or not code:
            return jsonify({
                "success": False,
                "message": "יש למלא גם אימייל וגם קוד אימות."
            }), 400

        result = serviceLayer.verify_reset_code(email, code)
        parsed_result = json.loads(result)

        if parsed_result.get("status") == "success":
            return jsonify({
                "success": True,
                "token": parsed_result["token"]
            }), 200
        else:
            return jsonify({
                "success": False,
                "message": parsed_result.get("message")
            }), 400

    except Exception as e:
        print(f"Error in verify_reset_code: {str(e)}")
        return jsonify({
            "success": False,
            "message": "שגיאה באימות הקוד.",
            "error": str(e)
        }), 500

@user_controller.route('/api/auth/reset-new-password', methods=['POST'])
@jwt_required()
def reset_new_password():
    try:
        data = request.get_json()
        password = data.get('password')
        confirm_password = data.get('confirm_password')
        email = data.get('email')

        if not password or not confirm_password or not email:
            return jsonify({
                "success": False,
                "message": "חסרים שדות"
            }), 400

        if password != confirm_password:
            return jsonify({
                "success": False,
                "message": "הסיסמאות אינן תואמות"
            }), 400


        return serviceLayer.reset_new_password(email, password)

       

    except Exception as e:
        print("Reset password error:", e)
        return jsonify({
            "success": False,
            "message": "שגיאה בשרת",
            "error": str(e)
        }), 500

@user_controller.route('/api/user/disapprove_system_manager_appoint', methods=['POST'])
@cross_origin()
@jwt_required()
def disapprove_system_manager_appoint():
    try:
        data = request.get_json()
        notification_id = data.get('notification_id')

        if not notification_id:
            return jsonify({
                "success": False,
                "message": "Missing required parameter: notification_id"
            }), 400

        user_id = get_jwt_identity()  # The user who is disapproving

        result = serviceLayer.disapprove_system_manager_appoint(notification_id, user_id)
        parsed_result = json.loads(result)

        if parsed_result.get("status") == "success":
            return jsonify({
                "success": True,
                "message": parsed_result.get("message", "הסירוב נקלט בהצלחה.")
            }), 200
        else:
            return jsonify({
                "success": False,
                "message": parsed_result.get("message", "שגיאה בעיבוד הסירוב")
            }), 400

    except Exception as e:
        print(f"Error in disapprove_system_manager_appoint: {str(e)}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@user_controller.route('/api/user/approve_system_manager_appoint', methods=['POST'])
@cross_origin()
@jwt_required()
def approve_system_manager_appoint():
    try:
        data = request.get_json()
        notification_id = data.get('notification_id')

        if not notification_id:
            return jsonify({
                "success": False,
                "message": "Missing required parameter: notification_id"
            }), 400

        user_id = get_jwt_identity()  # The user who is disapproving

        result = serviceLayer.approve_system_manager_appoint(notification_id, user_id)
        parsed_result = json.loads(result)

        if parsed_result.get("status") == "success":
            return jsonify({
                "success": True,
                "message": parsed_result.get("message", "הסירוב נקלט בהצלחה.")
            }), 200
        else:
            return jsonify({
                "success": False,
                "message": parsed_result.get("message", "שגיאה בעיבוד הסירוב")
            }), 400

    except Exception as e:
        print(f"Error in approve_system_manager_appoint: {str(e)}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@user_controller.route('/api/user/disapprove_course_manager_appoint', methods=['POST'])
@cross_origin()
@jwt_required()
def disapprove_course_manager_appoint():
    try:
        data = request.get_json()
        notification_id = data.get('notification_id')

        if not notification_id:
            return jsonify({
                "success": False,
                "message": "Missing required parameter: notification_id"
            }), 400

        user_id = get_jwt_identity()  # The user who is disapproving

        result = serviceLayer.disapprove_course_manager_appoint(notification_id, user_id)
        parsed_result = json.loads(result)

        if parsed_result.get("status") == "success":
            return jsonify({
                "success": True,
                "message": parsed_result.get("message", "הסירוב נקלט בהצלחה.")
            }), 200
        else:
            return jsonify({
                "success": False,
                "message": parsed_result.get("message", "שגיאה בעיבוד הסירוב")
            }), 400

    except Exception as e:
        print(f"Error in disapprove_course_manager_appoint: {str(e)}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500
    

@user_controller.route('/api/user/approve_course_manager_appoint', methods=['POST'])
@cross_origin()
@jwt_required()
def approve_course_manager_appoint():
    try:
        data = request.get_json()
        notification_id = data.get('notification_id')

        if not notification_id:
            return jsonify({
                "success": False,
                "message": "Missing required parameter: notification_id"
            }), 400

        user_id = get_jwt_identity()  # The user who is approving

        result = serviceLayer.approve_course_manager_appoint(notification_id, user_id)
        parsed_result = json.loads(result)

        if parsed_result.get("status") == "success":
            return jsonify({
                "success": True,
                "message": parsed_result.get("message", "הסירוב נקלט בהצלחה.")
            }), 200
        else:
            return jsonify({
                "success": False,
                "message": parsed_result.get("message", "שגיאה בעיבוד הסירוב")
            }), 400

    except Exception as e:
        print(f"Error in approve_course_manager_appoint: {str(e)}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@user_controller.route('/api/user/get_notification_settings', methods=['GET'])
@cross_origin()
@jwt_required()
def get_notification_settings():
    try:
        user_id = get_jwt_identity()
        settings = serviceLayer.get_notification_settings(user_id)
        if settings:
            return jsonify({
                "success": True,
                "settings": settings
            }), 200
        else:
            return jsonify({
                "success": True,
                "settings": {
                    "AppointSystemManager": False,
                    "AppointCourseManager": False,
                    "CommentToFollowing": False,
                    "CommentToComment": False,
                    "ReactToComment": False,
                    "RemoveCourseManager": False
                }
            }), 200

    except Exception as e:
        print(f"Error in get_notification_settings: {str(e)}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

@user_controller.route('/api/user/update_notification_settings', methods=['POST'])
@cross_origin()
@jwt_required()
def update_notification_settings():
    try:
        user_id = get_jwt_identity()
        data = request.get_json()

        expected_keys = [
            "AppointSystemManager", "AppointCourseManager", "CommentToFollowing",
            "CommentToComment", "ReactToComment", "RemoveCourseManager"
        ]

        # Make sure all expected keys exist
        for key in expected_keys:
            if key not in data:
                return jsonify({
                    "success": False,
                    "message": f"Missing key: {key}"
                }), 400

        result = serviceLayer.update_notification_settings(user_id, data)
        if result:
            return jsonify({
                "success": True,
                "message": "Settings updated successfully"
            }), 200
        else:
            return jsonify({
                "success": False,
                "message": "Failed to update settings"
            }), 400

    except Exception as e:
        print(f"Error in update_notification_settings: {str(e)}")
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500

@user_controller.route('/api/user/update_name', methods=['POST'])
@cross_origin()
@jwt_required()
def update_name():
    try:
        data = request.get_json()
        first_name = data.get("first_name")
        last_name = data.get("last_name")
        user_id = get_jwt_identity()

        if not first_name or not last_name:
            return jsonify({"success": False, "message": "Missing name fields"}), 400

        success = serviceLayer.update_user_name(user_id, first_name, last_name)

        if success:
            return jsonify({"success": True, "message": "Name updated successfully"}), 200
        else:
            return jsonify({"success": False, "message": "Failed to update name"}), 400

    except Exception as e:
        print(f"Error updating name: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500


@user_controller.route('/api/user/upload_profile_picture', methods=['POST'])
@jwt_required()
def upload_profile_picture():
    try:
        user_id = get_jwt_identity()
        if 'profile_picture' not in request.files:
            return jsonify({"success": False, "message": "Missing file."}), 400

        file = request.files['profile_picture']

        file_path = serviceLayer.upload_profile_picture(user_id, file)
        return jsonify({"success": True, "profile_picture_path": file_path}), 200
    except Exception as e:
        print(f"Error in upload_profile_picture: {e}")
        return jsonify({"success": False, "message": str(e)}), 500


@user_controller.route('/api/user/get_profile_picture', methods=['GET'])
@jwt_required()
def get_profile_picture():
    try:
        # DEBUG: log incoming request
        logging.warning(f"🔍 Incoming request: {request.method} {request.path}")
        logging.warning(f"Headers: {dict(request.headers)}")

        user_id = get_jwt_identity()
        profile_pic_path = serviceLayer.get_profile_picture_path(user_id)

        if not profile_pic_path or not os.path.exists(profile_pic_path):
            logging.warning("⚠️ No profile picture found, returning default.")
            return send_file('files/default-avatar.png', mimetype='image/png')

        # Determine MIME type
        extension = profile_pic_path.rsplit('.', 1)[-1].lower()
        mimetype = f"image/{'jpeg' if extension == 'jpg' else extension}"
        logging.warning(f"✅ Serving image: {profile_pic_path} with mimetype {mimetype}")
        return send_file(profile_pic_path, mimetype=mimetype)

    except Exception as e:
        logging.error(f"❌ Exception: {str(e)}")
        return jsonify({"success": False, "message": str(e)}), 500

