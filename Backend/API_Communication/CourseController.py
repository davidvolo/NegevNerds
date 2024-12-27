import ast
import json
import os

from flask import Blueprint, request, jsonify, send_file
from flask_cors import cross_origin, CORS

from Backend.BusinessLayer.NegevNerds import NegevNerds
from Backend.BusinessLayer.PDFAnalyzer.FileManager import FileManager
from Backend.BusinessLayer.User.UserFacade import UserFacade
from Backend.DataLayer.DTOs.QuestionDTO import QuestionDTO
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


@course_controller.route('/api/course/get_all_courses', methods=['GET', 'OPTIONS'])
@cross_origin()
def get_all_courses():
    # Handle OPTIONS preflight request
    if request.method == 'OPTIONS':
        response = jsonify(success=True)
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'GET, OPTIONS')
        return response

    try:
        # Get the result from the service layer
        result = serviceLayer.get_all_courses()
        # Parse the JSON string into a dictionary
        result_dict = json.loads(result)
        # Ensure the response has the expected structure
        if result_dict.get("status") != "success":
            return jsonify({
                "success": False,
                "message": result_dict.get("message", "Unknown error")
            }), 500

        # Process the data
        parsed_result = result_dict["data"]
        print(parsed_result)  # Debugging

        # Final response
        return jsonify({
            "success": True,
            "data": parsed_result
        })

    except json.JSONDecodeError:
        # Handle JSON decoding errors
        return jsonify({
            "success": False,
            "message": "Invalid JSON response from service"
        }), 500
    except Exception as e:
        # Handle unexpected errors
        print(f"Error: {str(e)}")
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
        response.headers.add('Access-Control-Allow-Methods', 'GET')
        return response

    try:
        # Extract course_id from query parameters
        course_id = request.args.get('course_id')

        if not course_id:
            return jsonify({
                "status": "error",
                "message": "Course ID is required"
            }), 400

        # Get course topics
        result = serviceLayer.get_course_topics(course_id)

        # Parse the JSON string
        parsed_result = json.loads(result)

        # Check if the result has a success status
        if parsed_result.get('status') == 'success':
            return jsonify({
                "status": "success",
                "data": parsed_result.get('data', [])
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": parsed_result.get('message', 'Unknown error')
            }), 400

    except json.JSONDecodeError:
        return jsonify({
            "status": "error",
            "message": "Invalid JSON response"
        }), 500
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@course_controller.route('/api/course/get_question_pdf', methods=['GET', 'OPTIONS'])
@cross_origin()
def get_question_pdf():
    if request.method == 'OPTIONS':
        response = jsonify(success=True)
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'GET')
        return response
    try:
        # קבלת פרמטרים מ-Query String
        course_id = request.args.get('course_id')
        year = request.args.get('year')
        semester = request.args.get('semester')
        moed = request.args.get('moed')
        question_number = request.args.get('question_number')

        print(
            f"Received parameters: course_id={course_id}, year={year}, semester={semester}, moed={moed}, question_number={question_number}")

        # בדיקת פרמטרים
        if not all([course_id, year, semester, moed, question_number]):
            return jsonify({
                "status": "error",
                "message": "Missing required parameters"
            }), 400

        # בניית הנתיב של הקובץ
        question_path = serviceLayer.get_question_path(course_id, year, semester, moed, question_number)
        print(f"Generated file path: {question_path}")

        # בדיקה אם הקובץ קיים
        if not os.path.exists(question_path):
            return jsonify({
                "status": "error",
                "message": "File not found"
            }), 404

        # שליחת הקובץ ללקוח
        return send_file(question_path, mimetype='application/pdf')
    except Exception as e:
        print(f"Error in get_pdf: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@course_controller.route('/api/course/get_answer_pdf', methods=['GET', 'OPTIONS'])
@cross_origin()
def get_answer_pdf():
    if request.method == 'OPTIONS':
        response = jsonify(success=True)
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'GET')
        return response
    try:
        # קבלת פרמטרים מ-Query String
        course_id = request.args.get('course_id')
        year = request.args.get('year')
        semester = request.args.get('semester')
        moed = request.args.get('moed')
        question_number = request.args.get('question_number')

        print(
            f"Received parameters: course_id={course_id}, year={year}, semester={semester}, moed={moed}, question_number={question_number}")

        # בדיקת פרמטרים
        if not all([course_id, year, semester, moed, question_number]):
            return jsonify({
                "status": "error",
                "message": "Missing required parameters"
            }), 400

        # בניית הנתיב של הקובץ
        answer_path = serviceLayer.get_answer_path(course_id, year, semester, moed, question_number)
        print(f"Generated file path: {answer_path}")

        # בדיקה אם הקובץ קיים
        if not os.path.exists(answer_path):
            return jsonify({
                "status": "error",
                "message": "File not found"
            }), 404

        # שליחת הקובץ ללקוח
        return send_file(answer_path, mimetype='application/pdf')
    except Exception as e:
        print(f"Error in get_pdf: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

@course_controller.route('/api/course/get_course/<course_id>', methods=['GET', 'OPTIONS'])
@cross_origin()
def get_course(course_id):
    # Handle OPTIONS preflight request
    if request.method == 'OPTIONS':
        response = jsonify(success=True)
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'GET')
        return response

    try:
        # Extract course_id from query parameters
        # course_id = request.args.get('course_id')

        print(f"Received course_id from URL: {course_id}")

        if not course_id:
            return jsonify({
                "status": "error",
                "message": "Course ID is required"
            }), 400

        # Get course details from the service layer
        result = serviceLayer.get_course(course_id)

        # Parse the JSON string
        parsed_result = json.loads(result)

        print(f"Received course details: {parsed_result}")

        # Check if the result has a success status
        if parsed_result.get('status') == 'success':
            return jsonify({
                "status": "success",
                "data": parsed_result.get('data', {})
            }), 200
        else:
            return jsonify({
                "status": "error",
                "message": parsed_result.get('message', 'Unknown error')
            }), 400

    except json.JSONDecodeError:
        return jsonify({
            "status": "error",
            "message": "Invalid JSON response"
        }), 500
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# @course_controller.route('/api/course/add_question', methods=['POST', 'OPTIONS'])
# @cross_origin()
# def add_question():
#     if request.method == 'OPTIONS':
#         response = jsonify(success=True)
#         response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
#         response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
#         response.headers.add('Access-Control-Allow-Methods', 'POST')
#         return response

#     try:
#         # Parse the JSON data from the request
#         data = request.get_json()

#         # Validate input fields
#         required_fields = ['course_id', 'year', 'semester', 'moed', 'question_number', 'is_american', 'question_topics', 'pdf_question']
#         missing_fields = [field for field in required_fields if field not in data]
#         if missing_fields:
#             return jsonify({
#                 "success": False,
#                 "message": f"Missing required fields: {', '.join(missing_fields)}"
#             }), 400

#         # Extract the fields
#         course_id = data.get('course_id')
#         year = data.get('year')
#         semester = data.get('semester')
#         moed = data.get('moed')
#         question_number = data.get('question_number')
#         is_american = data.get('is_american')
#         question_topics = data.get('question_topics')
#         pdf_question = data.get('pdf_question')
#         pdf_answer = data.get('pdf_answer')  # Optional

#         # Call the service layer function
#         result = serviceLayer.add_question(
#             course_id, year, semester, moed, question_number,
#             is_american, question_topics, pdf_question, pdf_answer
#         )

#         # Parse the service response
#         parsed_result = json.loads(result)
#         return parse_jsonify(parsed_result)

#     except json.JSONDecodeError:
#         return jsonify({
#             "success": False,
#             "message": "Invalid JSON in request or response"
#         }), 500
#     except Exception as e:
#         return jsonify({
#             "success": False,
#             "message": "An unexpected error occurred",
#             "error": str(e)
#         }), 500

@course_controller.route('/api/course/add_question', methods=['POST', 'OPTIONS'])
@cross_origin()
def add_question():
    if request.method == 'OPTIONS':
        response = jsonify(success=True)
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response

    try:
        # Extract required fields from form data
        course_id = request.form.get('course_id')
        year = int(request.form.get('year'))
        semester = request.form.get('semester')
        moed = request.form.get('moed')
        question_number = int(request.form.get('question_number'))
        is_american = request.form.get('is_american')
        is_american_boolean = is_american.lower() == 'true'
        question_topics = request.form.get('question_topics')
        pdf_question = request.files.get('pdf_question')
        pdf_answer = request.files.get('pdf_answer')  # Optional

        # Validate required fields
        required_fields = [course_id, year, semester, moed, question_number, is_american, question_topics, pdf_question]
        if any(field is None for field in required_fields):
            return jsonify({
                "success": False,
                "message": "Missing required fields."
            }), 400

        if isinstance(question_topics, str):
            try:
                question_topics = ast.literal_eval(question_topics)  # Safely convert string to list
                if not isinstance(question_topics, list):  # Ensure it's a list after conversion
                    question_topics = [question_topics]
            except (ValueError, SyntaxError):
                return jsonify({
                    "success": False,
                    "message": "Invalid format for question_topics."
                }), 400

        # Call the service layer
        result = serviceLayer.add_question(
            course_id, year, semester, moed, question_number,
            is_american_boolean, question_topics, pdf_question, pdf_answer
        )

        # Parse the service response
        parsed_result = json.loads(result)
        return jsonify({
            "success": parsed_result.get("status") == "success",
            "message": parsed_result.get("message")
        }), 200

    except Exception as e:
        print(f"Error in add_question: {str(e)}")
        return jsonify({
            "success": False,
            "message": "An unexpected error occurred.",
            "error": str(e)
        }), 500

@course_controller.route('/api/course/add_comment', methods=['POST', 'OPTIONS'])
@cross_origin()
def add_comment():
    if request.method == 'OPTIONS':
        response = jsonify(success=True)
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response

    try:
        # Extract required fields from form data
        course_id = request.form.get('course_id')
        year = int(request.form.get('year'))
        semester = request.form.get('semester')
        moed = request.form.get('moed')
        question_number = int(request.form.get('question_number'))
        writer_name = request.form.get('writer_name')
        prev_id = request.form.get('prev_id')
        comment_text = request.form.get('comment_text')  # Optional

        # Validate required fields
        required_fields = [course_id, year, semester, moed, question_number, writer_name, prev_id, comment_text]
        if any(field is None for field in required_fields):
            return jsonify({
                "success": False,
                "message": "Missing required fields."
            }), 400

        # Call the service layer
        result = serviceLayer.add_comment(
            course_id, year, semester, moed, question_number,
            writer_name, prev_id, comment_text
        )

        # Parse the service response
        parsed_result = json.loads(result)
        return jsonify({
            "success": parsed_result.get("status") == "success",
            "message": parsed_result.get("message")
        }), 200

    except Exception as e:
        print(f"Error in add_comment: {str(e)}")
        return jsonify({
            "success": False,
            "message": "An unexpected error occurred.",
            "error": str(e)
        }), 500

@course_controller.route('/api/course/search_exam_by_specifics', methods=['OPTIONS', 'POST'])
@cross_origin()
def search_question_by_specifics():
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

        # הדפסת המידע שהתקבל מהלקוח
        print("Received data:", data)

        # Validate input
        if not all(key in data for key in ['course_id']):
            return jsonify({
                "success": False,
                "message": "Missing required fields"
            }), 400

        # Extract the data
        course_id = data.get('course_id')
        year = data.get('year')
        semester = data.get('semester') if data.get('semester') else None
        moed = data.get('moed') if data.get('moed') else None
        question_number = data.get('question_number') if data.get('question_number') else None

        # טיפול עם None על מנת למנוע שגיאות

        # הדפסת הנתונים שמתקבלים
        print(
            f"Extracted values: course_id={course_id}, year={year}, semester={semester}, moed={moed}, question_number={question_number}")

        # Call the service layer's search_question_by_specifics method
        if question_number is not None:
            question_number = int(question_number)  # המרת מספר אם קיים
        else:
            question_number = None  # או להשתמש בערך ברירת מחדל אם אין

        if year is not None:
            year = int(year)  # המרת מספר אם קיים
        else:
            year = None  # או להשתמש בערך ברירת מחדל אם אין
        result = serviceLayer.search_question_by_specifics(course_id, year, semester, moed, question_number)
        print(f"Service Layer Result: {result}")

        # Parse the JSON string
        if isinstance(result, list):
            result = [question.to_dict() if isinstance(question, QuestionDTO) else question for question in result]
        else:
            result = result.to_dict() if isinstance(result, QuestionDTO) else result

        # Return the response
        print(f"Formatted result: {result}")

        # Return the response
        return jsonify({
            "success": True,
            "data": result
        }), 200

    except json.JSONDecodeError:
        return jsonify({
            "success": False,
            "message": "Invalid JSON response"
        }), 500
    except Exception as e:
        print(f"Error: {str(e)}")  # הדפסת שגיאה אם התרחשה
        return jsonify({
            "success": False,
            "message": str(e)
        }), 500


@course_controller.route('/api/course/upload_answer', methods=['POST', 'OPTIONS'])
@cross_origin()
def upload_answer():
    if request.method == 'OPTIONS':
        response = jsonify(success=True)
        response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response

    try:
        # Extract required fields from form data
        course_id = request.form.get('course_id')
        year = int(request.form.get('year'))
        semester = request.form.get('semester')
        moed = request.form.get('moed')
        question_number = int(request.form.get('question_number'))
        pdf_answer = request.files.get('pdf_answer')  # Optional

        if not all([course_id, year, semester, moed, question_number, pdf_answer]):
            return jsonify({
                "status": "error",
                "message": "Missing required parameters"
            }), 400

        # Call the service layer
        result = serviceLayer.upload_answer(
            course_id, year, semester, moed, question_number, pdf_answer
        )

        # Parse the service response
        parsed_result = json.loads(result)
        return jsonify({
            "success": parsed_result.get("status") == "success",
            "message": parsed_result.get("message")
        }), 200

    except Exception as e:
        print(f"Error in upload_answer: {str(e)}")
        return jsonify({
            "success": False,
            "message": "An unexpected error occurred.",
            "error": str(e)
        }), 500





