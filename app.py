# import eventlet
# eventlet.monkey_patch()
from gevent import monkey
monkey.patch_all()
import threading

from flask_socketio import SocketIO, emit, join_room
import jwt as pyjwt  # Rename to avoid collision with Flask-JWT-Extended

from waitress import serve
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from multiprocessing import cpu_count

from Backend.API_Communication.UserController import user_controller
from Backend.API_Communication.CourseController import course_controller
from Backend.BusinessLayer.NegevNerds import NegevNerds
from Backend.ServiceLayer.ServiceLayer import ServiceLayer
import os
import sys

import subprocess
import psutil
import time
from socketio_instance import socketio  # ✅ Import the shared instance

sys.path.append('/home/david/backend/NegevNerds')


app = Flask(__name__)

app.config['JWT_SECRET_KEY'] = 'negev_nerds'  # סוד ה-JWT שלך
jwt = JWTManager(app)

db = SQLAlchemy()


app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///NegevNerds.db'  # Main DB
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
migrate = Migrate(app, db)

CORS(app, resources={
    r"/api/*": {
        "origins": [
            "http://localhost:3000",
            "http://132.72.116.86:3000",
            "https://132.72.116.86:3000",
            "https://negevnerds.cs.bgu.ac.il",  # Add your production domain
            "https://api.negevnerds.cs.bgu.ac.il"  # Add your API subdomain
        ],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# socketio.init_app(app)  # ✅ Hook into Flask app
# socketio.init_app(app, cors_allowed_origins=[
#     "http://localhost:3000",
#     "http://132.72.116.86:3000",
#     "https://132.72.116.86:3000",
#     "https://negevnerds.cs.bgu.ac.il",
#     "https://api.negevnerds.cs.bgu.ac.il"
# ])
socketio.init_app(app, cors_allowed_origins="*")


def verify_token(token):
    try:
        decoded = pyjwt.decode(token, app.config['JWT_SECRET_KEY'], algorithms=["HS256"])
        return decoded.get("sub")  # <-- ✅ Match your payload
    except pyjwt.ExpiredSignatureError:
        print("Token expired")
    except pyjwt.InvalidTokenError:
        print("Invalid token")
    return None
    

@socketio.on("connect")
def handle_connect():
    token = request.args.get("token")
    # print("Received token:", token)
    user_id = verify_token(token)
    if user_id:
        join_room(user_id)
        # print(f"✅ User {user_id} joined their room")
    else:
        print("❌ Invalid or missing token — connection rejected")


# Register controllers
app.register_blueprint(user_controller)
app.register_blueprint(course_controller)


@app.route('/api/<path:path>', methods=['OPTIONS'])
def handle_options(path):
    response = app.make_response('')
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS, PUT, DELETE'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    return response


@app.errorhandler(401)
def custom_401(error):
    return jsonify({
        "success": False,
        "message": "Unauthorized access, please provide a valid token"
    }), 401



def is_elasticsearch_running():
    for proc in psutil.process_iter(['name', 'cmdline']):
        if 'elasticsearch' in ' '.join(proc.info['cmdline']):
            return True
    return False


# Function to check if Elasticsearch is running
def is_elasticsearch_running():
    for process in psutil.process_iter(['pid', 'name']):
        if 'elasticsearch' in process.info['name'].lower():
            return True
    return False

# Function to start Elasticsearch
def start_elasticsearch():
    # Update this path to where your Elasticsearch is located
    elasticsearch_path = r"C:\Users\ktnad\Downloads\elasticsearch-9.0.0-windows-x86_64\elasticsearch-9.0.0\bin\elasticsearch.bat"

    # Run the elasticsearch.bat file using subprocess
    subprocess.Popen([elasticsearch_path], shell=True)
    print("Elasticsearch is starting...")
    time.sleep(10)  # Wait a few seconds for Elasticsearch to start

def initialize():
    service_layer = ServiceLayer(NegevNerds("../"))
    service_layer.initialize_system()

def main():

    if not is_elasticsearch_running():
        print("Elasticsearch is not running. Starting it now...")
        start_elasticsearch()
    else:
        print("Elasticsearch is already running.")

    print("Starting the Preparation System API...")


    # service_layer = ServiceLayer(NegevNerds("../"))
    # service_layer.initialize_system()
    print("Starting the ExamData Preparation System API...")
    threading.Thread(target=initialize).start()
    # Run with werkzeug (development server)
#    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
#     context.load_cert_chain(
#         certfile="/etc/letsencrypt/live/negevnerds.cs.bgu.ac.il/fullchain.pem",
#         keyfile="/etc/letsencrypt/live/negevnerds.cs.bgu.ac.il/privkey.pem"
#     )

    # Start the server with HTTPS
#     http_server = WSGIServer(('0.0.0.0', 5001), app)
#     http_server.serve_forever()

    # threads = (cpu_count() * 2) + 1
    # serve(app, host='0.0.0.0', port=5001, threads=threads)  # ❌ WSGI (Waitress, no WebSocket support)
    print("📢 About to start the SocketIO server...")
    # socketio.run(app, host="0.0.0.0", port=5001)  # ✅ ASGI (eventlet-based WebSocket server)
    socketio.run(app, host="0.0.0.0", port=5001)


#     app.run(host='0.0.0.0', port=5001)

if __name__ == "__main__":
    main()


