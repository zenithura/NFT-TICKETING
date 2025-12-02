# File header: Authentication service module for user registration, login, and token management.
# Implements secure password hashing, JWT token generation, and refresh token management.

"""
Authentication service for NFT Ticketing Platform.
Handles user registration, login, password reset, and JWT token management.
"""

import os
import secrets
import hashlib
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
import bcrypt
import jwt
from supabase import Client
import logging

logger = logging.getLogger(__name__)

# Purpose: JWT configuration from environment variables.
# Side effects: Reads JWT_SECRET and token expiration settings.
JWT_SECRET = os.getenv('JWT_SECRET', secrets.token_urlsafe(32))
JWT_ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '15'))
REFRESH_TOKEN_EXPIRE_DAYS = int(os.getenv('REFRESH_TOKEN_EXPIRE_DAYS', '7'))
MAX_LOGIN_ATTEMPTS = int(os.getenv('MAX_LOGIN_ATTEMPTS', '5'))
LOCKOUT_DURATION_MINUTES = int(os.getenv('LOCKOUT_DURATION_MINUTES', '30'))

# Purpose: Password validation rules.
# Returns: Tuple of (is_valid, error_message).
# Side effects: None - validation only.
def validate_password(password: str) -> tuple[bool, Optional[str]]:
    """
    Validate password strength.
    
    Rules:
    - Minimum 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one digit
    - At least one special character
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"
    
    if not any(c.isupper() for c in password):
        return False, "Password must contain at least one uppercase letter"
    
    if not any(c.islower() for c in password):
        return False, "Password must contain at least one lowercase letter"
    
    if not any(c.isdigit() for c in password):
        return False, "Password must contain at least one digit"
    
    special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
    if not any(c in special_chars for c in password):
        return False, "Password must contain at least one special character"
    
    return True, None

# Purpose: Hash password using bcrypt with salt.
# Params: password (str) — plaintext password.
# Returns: Hashed password string.
# Side effects: None - pure function.
def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    salt = bcrypt.gensalt(rounds=12)
    hashed = bcrypt.hashpw(password.encode('utf-8'), salt)
    return hashed.decode('utf-8')

# Purpose: Verify password against hash.
# Params: password (str) — plaintext password; password_hash (str) — stored hash.
# Returns: True if password matches, False otherwise.
# Side effects: None - pure function.
def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash."""
    try:
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    except Exception as e:
        logger.error(f"Password verification error: {e}")
        return False

# Purpose: Generate JWT access token.
# Params: user_id (int) — user identifier; email (str) — user email; role (str) — user role.
# Returns: Encoded JWT token string.
# Side effects: None - pure function.
def create_access_token(user_id: int, email: str, role: str = 'user') -> str:
    """Create JWT access token."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {
        'sub': str(user_id),
        'email': email,
        'role': role,
        'type': 'access',
        'exp': expire,
        'iat': datetime.now(timezone.utc)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

# Purpose: Generate JWT refresh token.
# Params: user_id (int) — user identifier.
# Returns: Encoded JWT token string.
# Side effects: None - pure function.
def create_refresh_token(user_id: int) -> str:
    """Create JWT refresh token."""
    expire = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
    payload = {
        'sub': str(user_id),
        'type': 'refresh',
        'exp': expire,
        'iat': datetime.now(timezone.utc)
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

# Purpose: Decode and verify JWT token.
# Params: token (str) — JWT token string.
# Returns: Decoded token payload or None if invalid.
# Side effects: None - pure function.
def decode_token(token: str) -> Optional[Dict[str, Any]]:
    """Decode and verify JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        logger.warning("Token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid token: {e}")
        return None

# Purpose: Generate secure random token for email verification or password reset.
# Returns: Random token string.
# Side effects: None - pure function.
def generate_token() -> str:
    """Generate secure random token."""
    return secrets.token_urlsafe(32)

# Purpose: Check if user account is locked due to failed login attempts.
# Params: user (dict) — user record from database.
# Returns: True if account is locked, False otherwise.
# Side effects: None - pure function.
def is_account_locked(user: Dict[str, Any]) -> bool:
    """Check if user account is locked."""
    if not user.get('locked_until'):
        return False
    
    locked_until = user['locked_until']
    if isinstance(locked_until, str):
        locked_until = datetime.fromisoformat(locked_until.replace('Z', '+00:00'))
    
    return datetime.now(timezone.utc) < locked_until

# Purpose: Increment failed login attempts and lock account if threshold reached.
# Params: supabase (Client) — database client; user_id (int) — user identifier.
# Returns: True if account was locked, False otherwise.
# Side effects: Updates user record in database.
def handle_failed_login(supabase: Client, user_id: int) -> bool:
    """Handle failed login attempt and lock account if necessary."""
    try:
        # Get current user record
        result = supabase.table('users').select('failed_login_attempts').eq('user_id', user_id).execute()
        if not result.data:
            return False
        
        current_attempts = result.data[0].get('failed_login_attempts', 0)
        new_attempts = current_attempts + 1
        
        update_data = {'failed_login_attempts': new_attempts}
        
        # Lock account if max attempts reached
        if new_attempts >= MAX_LOGIN_ATTEMPTS:
            locked_until = datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_DURATION_MINUTES)
            update_data['locked_until'] = locked_until.isoformat()
            supabase.table('users').update(update_data).eq('user_id', user_id).execute()
            logger.warning(f"Account locked for user_id: {user_id}")
            return True
        
        supabase.table('users').update(update_data).eq('user_id', user_id).execute()
        return False
        
    except Exception as e:
        logger.error(f"Error handling failed login: {e}")
        return False

# Purpose: Reset failed login attempts after successful login.
# Params: supabase (Client) — database client; user_id (int) — user identifier.
# Side effects: Updates user record in database.
def reset_failed_login_attempts(supabase: Client, user_id: int) -> None:
    """Reset failed login attempts after successful login."""
    try:
        supabase.table('users').update({
            'failed_login_attempts': 0,
            'locked_until': None,
            'last_login_at': datetime.now(timezone.utc).isoformat()
        }).eq('user_id', user_id).execute()
    except Exception as e:
        logger.error(f"Error resetting failed login attempts: {e}")

# Purpose: Store refresh token in database.
# Params: supabase (Client) — database client; user_id (int) — user identifier; token (str) — refresh token; ip_address (str) — client IP; user_agent (str) — client user agent.
# Returns: True if stored successfully, False otherwise.
# Side effects: Inserts record into refresh_tokens table.
def store_refresh_token(supabase: Client, user_id: int, token: str, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> bool:
    """Store refresh token in database."""
    try:
        expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)
        token_data = {
            'user_id': user_id,
            'token': token,
            'expires_at': expires_at.isoformat(),
            'is_valid': True,
            'ip_address': ip_address,
            'user_agent': user_agent
        }
        supabase.table('refresh_tokens').insert(token_data).execute()
        return True
    except Exception as e:
        logger.error(f"Error storing refresh token: {e}")
        return False

# Purpose: Invalidate refresh token.
# Params: supabase (Client) — database client; token (str) — refresh token to invalidate.
# Side effects: Updates refresh_tokens table.
def invalidate_refresh_token(supabase: Client, token: str) -> None:
    """Invalidate refresh token."""
    try:
        supabase.table('refresh_tokens').update({'is_valid': False}).eq('token', token).execute()
    except Exception as e:
        logger.error(f"Error invalidating refresh token: {e}")

# Purpose: Invalidate all refresh tokens for a user.
# Params: supabase (Client) — database client; user_id (int) — user identifier.
# Side effects: Updates refresh_tokens table.
def invalidate_all_user_tokens(supabase: Client, user_id: int) -> None:
    """Invalidate all refresh tokens for a user."""
    try:
        supabase.table('refresh_tokens').update({'is_valid': False}).eq('user_id', user_id).execute()
    except Exception as e:
        logger.error(f"Error invalidating user tokens: {e}")

# Purpose: Verify refresh token is valid in database.
# Params: supabase (Client) — database client; token (str) — refresh token.
# Returns: User ID if valid, None otherwise.
# Side effects: Updates last_used_at timestamp.
def verify_refresh_token(supabase: Client, token: str) -> Optional[int]:
    """Verify refresh token is valid in database."""
    try:
        result = supabase.table('refresh_tokens').select('user_id, expires_at, is_valid').eq('token', token).execute()
        
        if not result.data:
            return None
        
        token_record = result.data[0]
        
        # Check if token is valid
        if not token_record.get('is_valid'):
            return None
        
        # Check if token is expired
        expires_at = token_record.get('expires_at')
        if expires_at:
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            if datetime.now(timezone.utc) >= expires_at:
                return None
        
        # Update last used timestamp
        supabase.table('refresh_tokens').update({
            'last_used_at': datetime.now(timezone.utc).isoformat()
        }).eq('token', token).execute()
        
        return token_record['user_id']
        
    except Exception as e:
        logger.error(f"Error verifying refresh token: {e}")
        return None

