import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from flask import Flask, request, jsonify
from flask_cors import CORS
from Users.user import User

app = Flask(__name__)
CORS(app)

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()

    user = User(data['email'], data['first_name'], data['last_name'])
    if user.register():
        return jsonify({"message": f"User {user.first_name} {user.last_name} registered successfully!"}), 201
    else:
        return jsonify({"message": "Registration failed"}), 400

if __name__ == '__main__':
    app.run(debug=True)
