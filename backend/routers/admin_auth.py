"""Admin authentication router for admin login and session management."""
import os
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends, status, Request, Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, Field
from supabase import Client
from jose import JWTError, jwt
from dotenv import load_dotenv

from database import get_supabase_admin
from auth_utils import hash_password, verify_password

load_dotenv()

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin Auth"])

# Admin credentials from environment (default fallback)
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD_HASH = os.getenv("ADMIN_PASSWORD_HASH", "")

# JWT Configuration for admin tokens
JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", os.getenv("ADMIN_JWT_SECRET", "change-this-secret-key"))
JWT_ALGORITHM = "HS256"
ADMIN_TOKEN_EXPIRE_MINUTES = int(os.getenv("ADMIN_TOKEN_EXPIRE_MINUTES", "480"))  # 8 hours

# Rate limiting for login attempts (in-memory, use Redis in production)
login_attempts: dict[str, list[datetime]] = {}
failed_login_count: dict[str, int] = {}
locked_ips: dict[str, datetime] = {}

# Default admin password hash (Admin123!)
# This should be set in .env as ADMIN_PASSWORD_HASH
DEFAULT_ADMIN_PASSWORD = "Admin123!"
if not ADMIN_PASSWORD_HASH:
    # Hash the default password on first run
    ADMIN_PASSWORD_HASH = hash_password(DEFAULT_ADMIN_PASSWORD)
    logger.warning("Using default admin password. Please set ADMIN_PASSWORD_HASH in .env!")


class AdminLoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1, max_length=200)


class AdminLoginResponse(BaseModel):
    success: bool
    message: str
    admin: Optional[dict] = None


class AdminSessionResponse(BaseModel):
    authenticated: bool
    admin: Optional[dict] = None


def create_admin_token(username: str) -> str:
    """Create JWT token for admin session."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=ADMIN_TOKEN_EXPIRE_MINUTES)
    payload = {
        "sub": username,
        "role": "ADMIN",
        "type": "admin",
        "exp": expire,
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def verify_admin_token(token: str) -> Optional[dict]:
    """Verify admin JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        if payload.get("type") != "admin" or payload.get("role") != "ADMIN":
            return None
        return payload
    except JWTError:
        return None


def check_rate_limit(ip_address: str) -> tuple[bool, Optional[str]]:
    """Check if IP is rate limited or locked."""
    now = datetime.now(timezone.utc)
    
    # Check if IP is locked
    if ip_address in locked_ips:
        lock_until = locked_ips[ip_address]
        if now < lock_until:
            remaining = (lock_until - now).total_seconds() / 60
            return False, f"Account locked. Try again in {int(remaining)} minutes."
        else:
            # Lock expired, remove it
            del locked_ips[ip_address]
            if ip_address in failed_login_count:
                del failed_login_count[ip_address]
    
    # Check rate limit (5 attempts per 10 minutes)
    if ip_address in login_attempts:
        # Remove attempts older than 10 minutes
        login_attempts[ip_address] = [
            attempt for attempt in login_attempts[ip_address]
            if now - attempt < timedelta(minutes=10)
        ]
        
        if len(login_attempts[ip_address]) >= 5:
            # Lock IP for 10 minutes
            locked_ips[ip_address] = now + timedelta(minutes=10)
            failed_login_count[ip_address] = 0
            return False, "Too many login attempts. Account locked for 10 minutes."
    
    return True, None


def record_failed_login(ip_address: str, db: Client, username: str):
    """Record failed login attempt with deduplication and track attacks."""
    now = datetime.now(timezone.utc)
    
    # Track attempts
    if ip_address not in login_attempts:
        login_attempts[ip_address] = []
    login_attempts[ip_address].append(now)
    
    # Increment failed count
    failed_login_count[ip_address] = failed_login_count.get(ip_address, 0) + 1
    
    # DEDUPLICATION: Check for duplicate alert in last 5 seconds
    # This prevents multiple alerts for rapid failed login attempts
    try:
        five_seconds_ago = now - timedelta(seconds=5)
        duplicate_check = db.table("security_alerts").select("alert_id").eq(
            "ip_address", ip_address
        ).eq("attack_type", "BRUTE_FORCE").eq("endpoint", "/api/admin/login").gte(
            "created_at", five_seconds_ago.isoformat()
        ).limit(1).execute()
        
        if duplicate_check.data:
            # Duplicate alert detected - skip insertion
            logger.debug(
                f"Skipping duplicate BRUTE_FORCE alert from {ip_address} "
                f"(duplicate found within 5 seconds)"
            )
            return
        
        # ALWAYS get user_id from username/email (for attack tracking)
        # This ensures blocking by email account, not IP
        user_id = None
        user_role = None
        try:
            # Try email first
            user_lookup = db.table("users").select("user_id, role").eq("email", username.lower()).limit(1).execute()
            if not user_lookup.data:
                # Try username
                user_lookup = db.table("users").select("user_id, role").eq("username", username).limit(1).execute()
            
            if user_lookup.data:
                user_data = user_lookup.data[0]
                user_id = user_data.get("user_id")
                user_role = user_data.get("role", "")
                
                # Skip tracking for admin users
                if user_role == "ADMIN":
                    return
        except Exception as lookup_error:
            logger.error(f"Error looking up user: {lookup_error}")
        
        # Log security alert directly to database
        result = db.table("security_alerts").insert({
            "user_id": user_id,  # Now includes user_id if found
            "ip_address": ip_address,
            "attack_type": "BRUTE_FORCE",
            "payload": f"Failed admin login attempt for username: {username}",
            "endpoint": "/api/admin/login",
            "severity": "MEDIUM",
            "risk_score": 50,
            "status": "NEW",
            "user_agent": "Admin Login",
            "metadata": json.dumps({
                "username": username,
                "failed_attempts": failed_login_count[ip_address],
            })
        }).execute()
        
        # Track attack and check for auto-suspension/ban
        if user_id:
            try:
                from attack_tracking import track_attack_and_check_suspension
                import asyncio
                
                alert_id = result.data[0].get("alert_id") if result.data else None
                
                # Run async function
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                suspension_result = loop.run_until_complete(
                    track_attack_and_check_suspension(
                        db, user_id, ip_address, "BRUTE_FORCE", alert_id
                    )
                )
                loop.close()
                
                if suspension_result.get("action"):
                    logger.warning(
                        f"User {user_id} {suspension_result['action']} after failed login attempts"
                    )
            except Exception as e:
                logger.error(f"Error tracking attack: {e}")
                
    except Exception as e:
        logger.error(f"Error logging security alert: {e}")


def record_successful_login(ip_address: str, db: Client, username: str):
    """Record successful login."""
    # Clear failed attempts on success
    if ip_address in login_attempts:
        del login_attempts[ip_address]
    if ip_address in failed_login_count:
        del failed_login_count[ip_address]
    if ip_address in locked_ips:
        del locked_ips[ip_address]
    
    # Log successful login
    try:
        db.table("admin_actions").insert({
            "admin_id": 1,  # System admin
            "action_type": "ADMIN_LOGIN",
            "target_type": "SYSTEM",
            "target_id": None,
            "details": {
                "username": username,
                "ip_address": ip_address,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            "ip_address": ip_address,
        }).execute()
    except Exception as e:
        logger.error(f"Error logging admin action: {e}")


def get_client_ip(request: Request) -> str:
    """Get client IP address from request."""
    # Check for forwarded IP (from proxy/load balancer)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    if request.client:
        return request.client.host
    
    return "unknown"


@router.post("/login", response_model=AdminLoginResponse)
async def admin_login(
    login_data: AdminLoginRequest,
    request: Request,
    response: Response,
    db: Client = Depends(get_supabase_admin)
):
    """Admin login endpoint with rate limiting and security logging."""
    ip_address = get_client_ip(request)
    
    # Check rate limit
    allowed, error_msg = check_rate_limit(ip_address)
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=error_msg
        )
    
    # Validate credentials
    username = login_data.username.strip()
    password = login_data.password.strip()
    
    if not username or not password:
        record_failed_login(ip_address, db, username)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username and password are required"
        )
    
    # Verify credentials
    is_valid = False
    
    # Check against configured admin credentials
    if username == ADMIN_USERNAME:
        # Verify password against hash
        if ADMIN_PASSWORD_HASH:
            is_valid = verify_password(password, ADMIN_PASSWORD_HASH)
        else:
            # Fallback to default password (for initial setup)
            is_valid = (password == DEFAULT_ADMIN_PASSWORD)
    
    if not is_valid:
        record_failed_login(ip_address, db, username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    # Success - create token and set cookie
    token = create_admin_token(username)
    
    # Set secure HTTP-only cookie
    # In production, set secure=True (HTTPS only)
    # In development, set secure=False for localhost
    is_production = os.getenv("ENVIRONMENT", "development") == "production"
    response.set_cookie(
        key="admin_token",
        value=token,
        httponly=True,
        secure=is_production,  # HTTPS only in production
        samesite="lax" if not is_production else "strict",  # Use "lax" for cross-origin in dev
        max_age=ADMIN_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    
    # Record successful login
    record_successful_login(ip_address, db, username)
    
    return AdminLoginResponse(
        success=True,
        message="Login successful",
        admin={
            "username": username,
            "role": "ADMIN",
        }
    )


@router.get("/session", response_model=AdminSessionResponse)
async def check_admin_session(
    request: Request,
    db: Client = Depends(get_supabase_admin)
):
    """Check if admin session is valid."""
    # Get token from cookie
    token = request.cookies.get("admin_token")
    
    if not token:
        return AdminSessionResponse(authenticated=False)
    
    # Verify token
    payload = verify_admin_token(token)
    if not payload:
        return AdminSessionResponse(authenticated=False)
    
    return AdminSessionResponse(
        authenticated=True,
        admin={
            "username": payload.get("sub"),
            "role": payload.get("role"),
        }
    )


@router.post("/logout")
async def admin_logout(response: Response):
    """Admin logout endpoint."""
    # Clear admin token cookie
    is_production = os.getenv("ENVIRONMENT", "development") == "production"
    response.delete_cookie(
        key="admin_token",
        httponly=True,
        secure=is_production,
        samesite="lax" if not is_production else "strict",  # Use "lax" for cross-origin in dev
        path="/",
    )
    
    return {"success": True, "message": "Logged out successfully"}


def get_admin_user(request: Request) -> dict:
    """Dependency to get current admin user from session."""
    token = request.cookies.get("admin_token")
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    payload = verify_admin_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    return {
        "username": payload.get("sub"),
        "role": payload.get("role"),
    }


def require_admin_auth(admin: dict = Depends(get_admin_user)) -> dict:
    """Dependency to require admin authentication."""
    if admin.get("role") != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return admin

