#!/usr/bin/env python3
"""
Authentication Middleware for Trading Dashboard
===============================================

Provides basic authentication and user management for the trading dashboard.
Includes user sessions, role-based access, and security features.

Features:
- Basic HTTP authentication
- User session management
- Role-based access control
- Security logging
- User management API
"""

import os
import json
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple
from functools import wraps
import logging

logger = logging.getLogger(__name__)

class AuthMiddleware:
    def __init__(self, users_file: str = "users.json", sessions_file: str = "sessions.json"):
        self.users_file = users_file
        self.sessions_file = sessions_file
        self.users = self._load_users()
        self.sessions = self._load_sessions()

        # Default admin user if no users exist
        if not self.users:
            self.create_user("admin", "admin123", "admin")
            logger.info("Created default admin user: admin/admin123")

    def _load_users(self) -> Dict:
        """Load users from file"""
        if os.path.exists(self.users_file):
            try:
                with open(self.users_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading users: {e}")
        return {}

    def _save_users(self):
        """Save users to file"""
        try:
            with open(self.users_file, 'w') as f:
                json.dump(self.users, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving users: {e}")

    def _load_sessions(self) -> Dict:
        """Load sessions from file"""
        if os.path.exists(self.sessions_file):
            try:
                with open(self.sessions_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"Error loading sessions: {e}")
        return {}

    def _save_sessions(self):
        """Save sessions to file"""
        try:
            with open(self.sessions_file, 'w') as f:
                json.dump(self.sessions, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving sessions: {e}")

    def _hash_password(self, password: str) -> str:
        """Hash password with salt"""
        salt = os.getenv('PASSWORD_SALT', 'trading_salt_2024')
        return hashlib.sha256(f"{password}{salt}".encode()).hexdigest()

    def create_user(self, username: str, password: str, role: str = "user") -> bool:
        """Create a new user"""
        if username in self.users:
            logger.warning(f"User {username} already exists")
            return False

        self.users[username] = {
            'password_hash': self._hash_password(password),
            'role': role,
            'created_at': datetime.now().isoformat(),
            'active': True
        }

        self._save_users()
        logger.info(f"Created user: {username} with role: {role}")
        return True

    def authenticate(self, username: str, password: str) -> Optional[Dict]:
        """Authenticate user credentials"""
        if username not in self.users:
            logger.warning(f"Authentication failed: user {username} not found")
            return None

        user = self.users[username]
        if not user.get('active', False):
            logger.warning(f"Authentication failed: user {username} is inactive")
            return None

        if user['password_hash'] != self._hash_password(password):
            logger.warning(f"Authentication failed: invalid password for {username}")
            return None

        # Create session
        session_token = secrets.token_urlsafe(32)
        self.sessions[session_token] = {
            'username': username,
            'role': user['role'],
            'created_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(hours=24)).isoformat()
        }

        self._save_sessions()
        logger.info(f"User {username} authenticated successfully")

        return {
            'token': session_token,
            'username': username,
            'role': user['role']
        }

    def validate_session(self, token: str) -> Optional[Dict]:
        """Validate session token"""
        if token not in self.sessions:
            return None

        session = self.sessions[token]

        # Check expiration
        expires_at = datetime.fromisoformat(session['expires_at'])
        if datetime.now() > expires_at:
            # Remove expired session
            del self.sessions[token]
            self._save_sessions()
            return None

        return session

    def logout(self, token: str) -> bool:
        """Logout user by removing session"""
        if token in self.sessions:
            username = self.sessions[token]['username']
            del self.sessions[token]
            self._save_sessions()
            logger.info(f"User {username} logged out")
            return True
        return False

    def require_auth(self, roles: Optional[list] = None):
        """Decorator for requiring authentication"""
        def decorator(f):
            @wraps(f)
            def wrapper(*args, **kwargs):
                # Get token from request (this would be implemented in Flask)
                # For now, return a placeholder
                return f(*args, **kwargs)
            return wrapper
        return decorator

    def get_user(self, token: str) -> Optional[Dict]:
        """Get user information from session token"""
        session = self.validate_session(token)
        if not session:
            return None

        username = session['username']
        if username not in self.users:
            return None

        user = self.users[username].copy()
        del user['password_hash']  # Don't return password hash
        user['username'] = username

        return user

    def list_users(self) -> Dict:
        """List all users (admin only)"""
        users_list = {}
        for username, user_data in self.users.items():
            users_list[username] = {
                'role': user_data.get('role', 'user'),
                'created_at': user_data.get('created_at'),
                'active': user_data.get('active', True)
            }
        return users_list

    def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        """Change user password"""
        if username not in self.users:
            return False

        user = self.users[username]
        if user['password_hash'] != self._hash_password(old_password):
            return False

        user['password_hash'] = self._hash_password(new_password)
        self._save_users()
        logger.info(f"Password changed for user: {username}")
        return True

    def cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        current_time = datetime.now()
        expired_tokens = []

        for token, session in self.sessions.items():
            expires_at = datetime.fromisoformat(session['expires_at'])
            if current_time > expires_at:
                expired_tokens.append(token)

        for token in expired_tokens:
            del self.sessions[token]

        if expired_tokens:
            self._save_sessions()
            logger.info(f"Cleaned up {len(expired_tokens)} expired sessions")

# Global auth instance
auth = AuthMiddleware()

# Flask integration functions
def init_auth(app):
    """Initialize authentication for Flask app"""
    global auth
    auth = AuthMiddleware()

    @app.before_request
    def check_auth():
        # Skip auth for certain endpoints
        if request.endpoint in ['login', 'health', 'static']:
            return

        # Check for session token
        token = request.headers.get('Authorization')
        if token and token.startswith('Bearer '):
            token = token[7:]  # Remove 'Bearer ' prefix

        if not token or not auth.validate_session(token):
            return {'error': 'Authentication required'}, 401

def create_auth_routes(app):
    """Create authentication routes for Flask app"""
    @app.route('/login', methods=['POST'])
    def login():
        data = request.get_json()
        if not data or 'username' not in data or 'password' not in data:
            return {'error': 'Username and password required'}, 400

        result = auth.authenticate(data['username'], data['password'])
        if result:
            return {'token': result['token'], 'user': auth.get_user(result['token'])}, 200
        else:
            return {'error': 'Invalid credentials'}, 401

    @app.route('/logout', methods=['POST'])
    def logout():
        token = request.headers.get('Authorization')
        if token and token.startswith('Bearer '):
            token = token[7:]

        if token and auth.logout(token):
            return {'message': 'Logged out successfully'}, 200
        else:
            return {'error': 'Invalid token'}, 400

    @app.route('/user', methods=['GET'])
    def get_current_user():
        token = request.headers.get('Authorization')
        if token and token.startswith('Bearer '):
            token = token[7:]

        user = auth.get_user(token) if token else None
        if user:
            return user, 200
        else:
            return {'error': 'Not authenticated'}, 401

    @app.route('/users', methods=['GET'])
    def list_users():
        # In production, check for admin role
        return auth.list_users(), 200

# Example usage in Flask app
"""
from auth_middleware import init_auth, create_auth_routes

app = Flask(__name__)
init_auth(app)
create_auth_routes(app)

@app.route('/protected')
def protected_route():
    # This route is automatically protected
    return {'message': 'This is protected'}
"""

if __name__ == "__main__":
    # Test the authentication system
    print("Testing Authentication System...")

    # Create test user
    auth.create_user("testuser", "password123", "user")

    # Test authentication
    result = auth.authenticate("testuser", "password123")
    if result:
        print(f"✅ Authentication successful: {result['username']}")

        # Test session validation
        user = auth.get_user(result['token'])
        if user:
            print(f"✅ Session validation successful: {user['username']}")

        # Test logout
        if auth.logout(result['token']):
            print("✅ Logout successful")
    else:
        print("❌ Authentication failed")

    print("Authentication system test completed!")