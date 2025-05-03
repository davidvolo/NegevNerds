from flask_socketio import SocketIO

# socketio = SocketIO(cors_allowed_origins="*")  # We'll init it with app in app.py
socketio = SocketIO(cors_allowed_origins="*", async_mode="eventlet", logger=True, engineio_logger=True)

