"""
DAV Cloud Solutions - Authentication & Security Module
Tech Stack: Python Flask, Werkzeug, PyMongo
Founder: Akhil V
"""

from functools import wraps
from flask import session, redirect, url_for, flash, current_app
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadTimeSignature

# ==============================================================================
# 1. PASSWORD SECURITY HELPERS
# ==============================================================================

def hash_password(password: str) -> str:
    """
    Hashes a plain text password using Werkzeug security.
    """
    return generate_password_hash(password, method='pbkdf2:sha256')


def check_password(stored_hash: str, password: str) -> bool:
    """
    Verifies a plain text password against the stored password hash.
    """
    return check_password_hash(stored_hash, password)


# ==============================================================================
# 2. EMAIL VERIFICATION TOKEN HELPERS
# ==============================================================================

def generate_verification_token(email: str) -> str:
    """
    Generates a secure, URL-safe verification token containing the user's email.
    """
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    token = serializer.dumps(email, salt=current_app.config.get('SECURITY_PASSWORD_SALT', 'dav-token-salt'))
    return str(token)


def verify_token(token: str, expiration_seconds: int = 86400) -> str | None:
    """
    Verifies the email token. Default expiration is 24 hours (86,400 seconds).
    Returns the email string if valid, or None if expired/invalid.
    """
    serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
    try:
        email = serializer.loads(
            token,
            salt=current_app.config.get('SECURITY_PASSWORD_SALT', 'dav-token-salt'),
            max_age=expiration_seconds
        )
        return email
    except (SignatureExpired, BadTimeSignature):
        return None


# ==============================================================================
# 3. ROUTE DECORATORS (ROLE-BASED ACCESS CONTROL)
# ==============================================================================

def login_required(f):
    """
    Decorator requiring the user to be logged in to access the route.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('user_id'):
            flash('Please log in to access your dashboard portal.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def role_required(role_name: str):
    """
    Decorator requiring a specific user role ('student', 'business', 'admin').
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('user_id'):
                flash('Please log in to view this portal.', 'warning')
                return redirect(url_for('login'))
            
            user_role = session.get('role')
            if user_role != role_name and user_role != 'admin':
                flash('Unauthorized access level for this portal.', 'danger')
                return redirect(url_for('dashboard'))
                
            return f(*args, **kwargs)
        return decorated_function
    return decorator