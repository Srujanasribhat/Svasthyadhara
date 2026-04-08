"""Authentication and authorization system."""

import bcrypt
import jwt
import streamlit as st
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import secrets
import string

from config import JWT_SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRATION, HEALTH_ID_PREFIX
from database import get_db

def generate_health_id() -> str:
    """Generate unique Health ID."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
    
    # Format: HC-YYYYMMDD-XXXXX (prefix-date-sequence)
    date_part = datetime.now().strftime("%Y%m%d")
    sequence = str(count + 1).zfill(5)
    return f"{HEALTH_ID_PREFIX}-{date_part}-{sequence}"

def generate_unique_id(prefix: str) -> str:
    """Generate unique ID with given prefix."""
    random_part = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"{prefix}-{timestamp}-{random_part}"

def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    """Verify password against hash."""
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_token(user_data: Dict[str, Any]) -> str:
    """Create JWT token."""
    payload = {
        "user_id": user_data["id"],
        "email": user_data["email"],
        "role": user_data["role"],
        "health_id": user_data.get("health_id"),
        "exp": datetime.utcnow() + JWT_EXPIRATION
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)

def verify_token(token: str) -> Optional[Dict[str, Any]]:
    """Verify and decode JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None

def register_user(
    email: str,
    password: str,
    role: str,
    first_name: str,
    last_name: str,
    **kwargs
) -> Dict[str, Any]:
    """Register a new user."""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Check if email exists
        cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cursor.fetchone():
            return {"success": False, "message": "Email already registered"}
        
        # Generate Health ID for patients
        health_id = generate_health_id() if role == "patient" else None
        
        # Hash password
        password_hash = hash_password(password)
        
        # Insert user
        cursor.execute('''
            INSERT INTO users (
                health_id, email, password_hash, role, first_name, last_name,
                phone, date_of_birth, gender, blood_group, address, city,
                state, pincode, emergency_contact, emergency_phone
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            health_id, email, password_hash, role, first_name, last_name,
            kwargs.get('phone'), kwargs.get('date_of_birth'), kwargs.get('gender'),
            kwargs.get('blood_group'), kwargs.get('address'), kwargs.get('city'),
            kwargs.get('state'), kwargs.get('pincode'), kwargs.get('emergency_contact'),
            kwargs.get('emergency_phone')
        ))
        
        user_id = cursor.lastrowid
        
        # Create health profile for patients
        if role == "patient":
            cursor.execute('''
                INSERT INTO health_profiles (user_id) VALUES (?)
            ''', (user_id,))
        
        conn.commit()
        
        return {
            "success": True,
            "message": "Registration successful",
            "health_id": health_id,
            "user_id": user_id
        }

def login_user(email: str, password: str) -> Dict[str, Any]:
    """Authenticate user and return token."""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, health_id, email, password_hash, role, first_name, last_name, is_active
            FROM users WHERE email = ?
        ''', (email,))
        user = cursor.fetchone()
        
        if not user:
            return {"success": False, "message": "Invalid email or password"}
        
        if not user["is_active"]:
            return {"success": False, "message": "Account is deactivated"}
        
        if not verify_password(password, user["password_hash"]):
            return {"success": False, "message": "Invalid email or password"}
        
        # Create token
        token = create_token(dict(user))
        
        return {
            "success": True,
            "message": "Login successful",
            "token": token,
            "user": {
                "id": user["id"],
                "health_id": user["health_id"],
                "email": user["email"],
                "role": user["role"],
                "first_name": user["first_name"],
                "last_name": user["last_name"]
            }
        }

def get_current_user() -> Optional[Dict[str, Any]]:
    """Get current logged-in user from session."""
    if "user" in st.session_state and st.session_state.user:
        return st.session_state.user
    return None

def require_auth(allowed_roles: list = None):
    """Decorator/check for requiring authentication."""
    user = get_current_user()
    if not user:
        return False
    if allowed_roles and user.get("role") not in allowed_roles:
        return False
    return True

def logout():
    """Logout current user."""
    if "user" in st.session_state:
        del st.session_state.user
    if "token" in st.session_state:
        del st.session_state.token