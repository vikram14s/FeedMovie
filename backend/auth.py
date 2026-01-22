"""
Authentication module for FeedMovie.
Handles user registration, login, and JWT token management.
"""

import bcrypt
import jwt
import os
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from functools import wraps
from flask import request, jsonify

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'feedmovie-dev-secret-change-in-production')
JWT_EXPIRY_DAYS = 7


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))


def create_token(user_id: int, email: str, username: str) -> str:
    """Create a JWT token for a user."""
    payload = {
        'user_id': user_id,
        'email': email,
        'username': username,
        'exp': datetime.utcnow() + timedelta(days=JWT_EXPIRY_DAYS),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, JWT_SECRET, algorithm='HS256')


def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and verify a JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_current_user() -> Optional[Dict[str, Any]]:
    """Get the current user from the request's Authorization header."""
    auth_header = request.headers.get('Authorization')
    if not auth_header:
        return None

    # Expect "Bearer <token>"
    parts = auth_header.split()
    if len(parts) != 2 or parts[0].lower() != 'bearer':
        return None

    token = parts[1]
    return decode_token(token)


def require_auth(f):
    """Decorator to require authentication for a route."""
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        if not user:
            return jsonify({'success': False, 'error': 'Authentication required'}), 401
        # Add user to kwargs so the route can access it
        kwargs['current_user'] = user
        return f(*args, **kwargs)
    return decorated


def optional_auth(f):
    """Decorator to optionally get user if authenticated."""
    @wraps(f)
    def decorated(*args, **kwargs):
        user = get_current_user()
        kwargs['current_user'] = user  # Can be None
        return f(*args, **kwargs)
    return decorated
