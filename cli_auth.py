import os
import json
import webbrowser
import time
import uuid
from datetime import datetime, timezone
from functools import wraps
import requests

BASE_URL = 'http://localhost:3000'

# Define the path for the session file in a hidden directory
SESSION_DIR = os.path.join(os.path.expanduser("~"), '.config', 'my_cli')
SESSION_FILE = os.path.join(SESSION_DIR, 'cli_session.json')

# Ensure the directory exists
os.makedirs(SESSION_DIR, exist_ok=True)

class AuthenticationError(Exception):
    """Custom exception for authentication-related errors.

    Attributes:
        message (str): The error message
        timestamp (str): The timestamp when the error occurred
        error_code (str, optional): A specific error code if applicable
    """
    def __init__(self, message, error_code=None):
        self.message = message
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.error_code = error_code
        super().__init__(self.message)

    def __str__(self):
        error_info = f"Authentication Error: {self.message}"
        if self.error_code:
            error_info += f" (Error Code: {self.error_code})"
        error_info += f" | Timestamp: {self.timestamp}"
        return error_info

def save_session(session_data):
    os.makedirs(SESSION_DIR, exist_ok=True)  # Ensure the directory exists
    with open(SESSION_FILE, 'w') as f:
        json.dump(session_data, f)
    print("Session data saved.")

def load_session():
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE, 'r') as f:
            print("Session data loaded.")
            return json.load(f)
    return None

def authenticate():
    # Generate unique device code
    device_code = str(uuid.uuid4())
    is_cli = True

    # Open browser for authentication
    auth_url = f"{BASE_URL}/cli?device_code={device_code}&is_cli={is_cli}"
    print(f"Opening browser for authentication: {auth_url}")
    webbrowser.open(auth_url)

    print("Browser opened for authentication. Please complete the process there.")

    # Poll for session (implement polling endpoint in your frontend)
    max_attempts = 60 # Adjust as needed
    for _ in range(max_attempts):
        try:
            response = requests.get(
                f"{BASE_URL}/cli/poll-session?device_code={device_code}"
            )
            if response.status_code == 200:
                return response.json()
        except:
            pass
        time.sleep(3)

    raise AuthenticationError("Authentication timeout")

def require_auth(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            # if os.path.exists(SESSION_FILE):
            #     session_data = load_session()
            #     print("Authentication successful!")
            #     return func(*args, **kwargs)
            # else:
                session_data = authenticate()
                # save_session(session_data)
                print("Authentication successful!")

        except AuthenticationError as e:
            print(f"Authentication failed: {str(e)}")
            return

        return func(*args, **kwargs)

    return wrapper
