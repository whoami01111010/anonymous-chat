import eventlet
import threading
import sys
import time
import socket  
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_socketio import SocketIO, send, emit
from flask_cors import CORS
import datetime
import hashlib
from tabulate import tabulate

app = Flask(__name__)
app.secret_key = "supersecretkey"
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

users = {}  # Store registered users (username -> hashed password)
message_logs = []  # Store chat history
user_activity_logs = []  # Store user login/register activities

# Get system's local IP address automatically
def get_local_ip():
    try:
        # Create a dummy socket to get the local network IP
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))  # Connect to an external server (Google's DNS)
        ip = s.getsockname()[0]  # Get local IP from the socket
        s.close()
        return ip
    except Exception as e:
        print(f"[ERROR] Could not fetch local IP: {e}")
        return "127.0.0.1"  # Fallback to localhost

# Hash function for passwords
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

@app.route('/')
def login_page():
    return render_template("login.html")

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")

    if username in users:
        return jsonify({"status": "error", "message": "Username already exists!"})

    hashed_password = hash_password(password)
    users[username] = hashed_password

    # Log registration
    user_activity_logs.append({"time": timestamp, "username": username, "action": "Registered", "password": hashed_password})

    return jsonify({"status": "success", "message": "Registered successfully!"})

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")

    if username in users and users[username] == hash_password(password):
        session['username'] = username
        
        # Log login
        user_activity_logs.append({"time": timestamp, "username": username, "action": "Logged In", "password": users[username]})

        return jsonify({"status": "success", "message": "Login successful!"})
    
    return jsonify({"status": "error", "message": "Invalid credentials!"})

@app.route('/chat')
def chat_room():
    if 'username' not in session:
        return redirect(url_for('login_page'))
    return render_template("index.html", username=session['username'])

@app.route('/traffic')
def traffic():
    return render_template("traffic.html", users=len(users), user_logs=user_activity_logs, message_logs=message_logs)

@app.route('/traffic_data')
def traffic_data():
    return jsonify({
        "users": len(users),
        "user_logs": user_activity_logs,
        "message_logs": message_logs
    })

@socketio.on('connect')
def handle_connect():
    print(f"User connected. Total users: {len(users)}")
    emit("update_traffic", {"users": len(users)}, broadcast=True)

@socketio.on('disconnect')
def handle_disconnect():
    print(f"User disconnected. Total users: {len(users)}")
    emit("update_traffic", {"users": len(users)}, broadcast=True)

@socketio.on('message')
def handle_message(data):
    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
    log_entry = {"time": timestamp, "user": data['user'], "message": data['message']}
    message_logs.append(log_entry)
    
    # Print logs in a tabular format
    print("\n========== Message Logs ==========")
    print(tabulate(message_logs, headers="keys", tablefmt="grid"))
    
    send(log_entry, broadcast=True)

local_ip = get_local_ip()
print(f"[INFO] Server running on: http://{local_ip}:5000")

# Run server in a separate thread
if __name__ == '__main__':
    #Use eventlet to run the app
    eventlet.wsgi.server(eventlet.listen(('0.0.0.0', 5000)), app)
    # socketio.run(app, host=local_ip, port=5000, debug=False)
