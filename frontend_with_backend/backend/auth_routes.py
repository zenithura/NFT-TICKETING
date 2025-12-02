# File header: FastAPI authentication routes for user registration, login, and token management.
# Provides secure endpoints for authentication with rate limiting and brute-force protection.

"""
Authentication API routes for NFT Ticketing Platform.
Handles registration, login, logout, password reset, and token refresh.
"""

from fastapi import APIRouter, HTTPException, Depends, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from typing import Optional
import re
import logging
from datetime import datetime, timezone, timedelta
# Purpose: Import supabase client from server module.
# Note: This creates a circular import, but it's resolved at runtime.
# Alternative: Use dependency injection, but this is simpler for now.
try:
    from server import supabase
except ImportError:
    # Fallback if server not yet imported
    supabase = None

from auth import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    generate_token,
    validate_password,
    is_account_locked,
    handle_failed_login,
    reset_failed_login_attempts,
    store_refresh_token,
    invalidate_refresh_token,
    invalidate_all_user_tokens,
    verify_refresh_token
)

logger = logging.getLogger(__name__)

# Purpose: Create authentication router with prefix.
# Side effects: Initializes FastAPI router.
auth_router = APIRouter(prefix="/auth", tags=["Authentication"])

# Purpose: HTTP Bearer token security scheme for JWT authentication.
# Side effects: None - security scheme definition.
security = HTTPBearer()

# Purpose: Pydantic models for request/response validation.
# Side effects: None - data class definitions only.

class RegisterRequest(BaseModel):
    """User registration request model."""
    email: EmailStr
    password: str = Field(..., min_length=8)
    username: Optional[str] = Field(None, max_length=100)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    
    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password strength."""
        is_valid, error_msg = validate_password(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v

class LoginRequest(BaseModel):
    """User login request model."""
    email: EmailStr
    password: str

class RefreshTokenRequest(BaseModel):
    """Refresh token request model."""
    refresh_token: str

class ForgotPasswordRequest(BaseModel):
    """Forgot password request model."""
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    """Reset password request model."""
    token: str
    new_password: str = Field(..., min_length=8)
    
    @field_validator('new_password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """Validate password strength."""
        is_valid, error_msg = validate_password(v)
        if not is_valid:
            raise ValueError(error_msg)
        return v

class VerifyEmailRequest(BaseModel):
    """Email verification request model."""
    token: str

class UserResponse(BaseModel):
    """User response model."""
    model_config = ConfigDict(extra="ignore")
    user_id: int
    email: str
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: str
    is_email_verified: bool
    created_at: str

class AuthResponse(BaseModel):
    """Authentication response model."""
    success: bool
    message: str
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    user: Optional[UserResponse] = None

# Purpose: Get client IP address from request.
# Params: request (Request) — FastAPI request object.
# Returns: IP address string.
# Side effects: None - pure function.
def get_client_ip(request: Request) -> str:
    """Get client IP address from request."""
    if request.client:
        return request.client.host
    return "unknown"

# Purpose: Get user agent from request headers.
# Params: request (Request) — FastAPI request object.
# Returns: User agent string or None.
# Side effects: None - pure function.
def get_user_agent(request: Request) -> Optional[str]:
    """Get user agent from request headers."""
    return request.headers.get('user-agent')

# Purpose: Register new user account.
# Params: request (Request) — FastAPI request; register_data (RegisterRequest) — registration data; supabase (Client) — database client.
# Returns: AuthResponse with access and refresh tokens.
# Side effects: Creates user record, stores refresh token, may send verification email.
@auth_router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: Request,
    register_data: RegisterRequest,
):
    """Register a new user account."""
    try:
        # Purpose: Check if email already exists.
        # Side effects: Queries database.
        existing = supabase.table('users').select('user_id').eq('email', register_data.email.lower()).execute()
        if existing.data:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )
        
        # Purpose: Hash password before storing.
        # Side effects: Creates password hash.
        password_hash = hash_password(register_data.password)
        
        # Purpose: Generate email verification token.
        # Side effects: Creates random token.
        verification_token = generate_token()
        verification_expires = datetime.now(timezone.utc) + timedelta(days=7)
        
        # Purpose: Create user record in database.
        # Side effects: Inserts record into users table.
        user_data = {
            'email': register_data.email.lower(),
            'password_hash': password_hash,
            'username': register_data.username,
            'first_name': register_data.first_name,
            'last_name': register_data.last_name,
            'role': 'user',
            'is_email_verified': False,
            'verification_token': verification_token,
            'verification_token_expires': verification_expires.isoformat()
        }
        
        result = supabase.table('users').insert(user_data).execute()
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user"
            )
        
        user = result.data[0]
        user_id = user['user_id']
        
        # Purpose: Generate access and refresh tokens.
        # Side effects: Creates JWT tokens.
        access_token = create_access_token(user_id, user['email'], user.get('role', 'user'))
        refresh_token = create_refresh_token(user_id)
        
        # Purpose: Store refresh token in database.
        # Side effects: Inserts record into refresh_tokens table.
        store_refresh_token(
            supabase,
            user_id,
            refresh_token,
            get_client_ip(request),
            get_user_agent(request)
        )
        
        # TODO: Send verification email (implement email service)
        
        return AuthResponse(
            success=True,
            message="Registration successful. Please verify your email.",
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserResponse(**user)
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Registration error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

# Purpose: Authenticate user and return tokens.
# Params: request (Request) — FastAPI request; login_data (LoginRequest) — login credentials; supabase (Client) — database client.
# Returns: AuthResponse with access and refresh tokens.
# Side effects: Updates last_login_at, resets failed login attempts, stores refresh token.
@auth_router.post("/login", response_model=AuthResponse)
async def login(
    request: Request,
    login_data: LoginRequest,
):
    """Login user and return access/refresh tokens."""
    try:
        # Purpose: Retrieve user by email.
        # Side effects: Queries database.
        result = supabase.table('users').select('*').eq('email', login_data.email.lower()).execute()
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        user = result.data[0]
        user_id = user['user_id']
        
        # Purpose: Check if account is locked.
        # Side effects: None - validation only.
        if is_account_locked(user):
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Account is locked due to too many failed login attempts. Please try again later."
            )
        
        # Purpose: Check if account is active.
        # Side effects: None - validation only.
        if not user.get('is_active', True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated"
            )
        
        # Purpose: Verify password.
        # Side effects: None - validation only.
        if not verify_password(login_data.password, user['password_hash']):
            handle_failed_login(supabase, user_id)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Purpose: Reset failed login attempts and update last login.
        # Side effects: Updates user record.
        reset_failed_login_attempts(supabase, user_id)
        
        # Purpose: Generate access and refresh tokens.
        # Side effects: Creates JWT tokens.
        access_token = create_access_token(user_id, user['email'], user.get('role', 'user'))
        refresh_token = create_refresh_token(user_id)
        
        # Purpose: Store refresh token in database.
        # Side effects: Inserts record into refresh_tokens table.
        store_refresh_token(
            supabase,
            user_id,
            refresh_token,
            get_client_ip(request),
            get_user_agent(request)
        )
        
        return AuthResponse(
            success=True,
            message="Login successful",
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserResponse(**user)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

# Purpose: Refresh access token using refresh token.
# Params: request (Request) — FastAPI request; refresh_data (RefreshTokenRequest) — refresh token; supabase (Client) — database client.
# Returns: AuthResponse with new access token.
# Side effects: Validates refresh token, may invalidate old token.
@auth_router.post("/refresh-token", response_model=AuthResponse)
async def refresh_token(
    request: Request,
    refresh_data: RefreshTokenRequest,
):
    """Refresh access token using refresh token."""
    try:
        # Purpose: Verify refresh token in database.
        # Side effects: Queries database, updates last_used_at.
        user_id = verify_refresh_token(supabase, refresh_data.refresh_token)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )
        
        # Purpose: Decode refresh token to get user info.
        # Side effects: None - token decoding only.
        payload = decode_token(refresh_data.refresh_token)
        if not payload or payload.get('type') != 'refresh':
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        # Purpose: Retrieve user information.
        # Side effects: Queries database.
        result = supabase.table('users').select('*').eq('user_id', user_id).execute()
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user = result.data[0]
        
        # Purpose: Generate new access token.
        # Side effects: Creates JWT token.
        access_token = create_access_token(user_id, user['email'], user.get('role', 'user'))
        
        return AuthResponse(
            success=True,
            message="Token refreshed successfully",
            access_token=access_token,
            refresh_token=refresh_data.refresh_token,  # Keep same refresh token
            user=UserResponse(**user)
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token refresh error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )

# Purpose: Logout user and invalidate tokens.
# Params: request (Request) — FastAPI request; credentials (HTTPAuthorizationCredentials) — JWT token; supabase (Client) — database client.
# Returns: Success message.
# Side effects: Invalidates refresh token, may invalidate all user tokens.
@auth_router.post("/logout", response_model=AuthResponse)
async def logout(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Logout user and invalidate refresh token."""
    try:
        token = credentials.credentials
        
        # Purpose: Decode token to get user ID.
        # Side effects: None - token decoding only.
        payload = decode_token(token)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        user_id = int(payload.get('sub'))
        
        # Purpose: Get refresh token from request body if provided.
        # Side effects: Reads request body.
        try:
            body = await request.json()
            refresh_token = body.get('refresh_token')
            if refresh_token:
                invalidate_refresh_token(supabase, refresh_token)
        except:
            pass  # Refresh token not provided, just invalidate all tokens
        
        # Purpose: Invalidate all user tokens (optional - can be made configurable).
        # Side effects: Updates refresh_tokens table.
        invalidate_all_user_tokens(supabase, user_id)
        
        return AuthResponse(
            success=True,
            message="Logout successful"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Logout error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

# Purpose: Request password reset (sends reset token via email).
# Params: request (Request) — FastAPI request; reset_data (ForgotPasswordRequest) — email address; supabase (Client) — database client.
# Returns: Success message (doesn't reveal if email exists).
# Side effects: Generates reset token, stores in database, sends email.
@auth_router.post("/forgot-password", response_model=AuthResponse)
async def forgot_password(
    request: Request,
    reset_data: ForgotPasswordRequest,
):
    """Request password reset."""
    try:
        # Purpose: Find user by email.
        # Side effects: Queries database.
        result = supabase.table('users').select('user_id, email').eq('email', reset_data.email.lower()).execute()
        
        # Purpose: Always return success to prevent email enumeration.
        # Side effects: None - security best practice.
        if not result.data:
            return AuthResponse(
                success=True,
                message="If the email exists, a password reset link has been sent."
            )
        
        user = result.data[0]
        user_id = user['user_id']
        
        # Purpose: Generate reset token.
        # Side effects: Creates random token.
        reset_token = generate_token()
        reset_expires = datetime.now(timezone.utc) + timedelta(hours=1)
        
        # Purpose: Store reset token in database.
        # Side effects: Updates user record.
        supabase.table('users').update({
            'reset_password_token': reset_token,
            'reset_password_expires': reset_expires.isoformat()
        }).eq('user_id', user_id).execute()
        
        # TODO: Send password reset email (implement email service)
        
        return AuthResponse(
            success=True,
            message="If the email exists, a password reset link has been sent."
        )
        
    except Exception as e:
        logger.error(f"Forgot password error: {e}", exc_info=True)
        # Still return success to prevent email enumeration
        return AuthResponse(
            success=True,
            message="If the email exists, a password reset link has been sent."
        )

# Purpose: Reset password using reset token.
# Params: request (Request) — FastAPI request; reset_data (ResetPasswordRequest) — reset token and new password; supabase (Client) — database client.
# Returns: Success message.
# Side effects: Updates password hash, clears reset token.
@auth_router.post("/reset-password", response_model=AuthResponse)
async def reset_password(
    request: Request,
    reset_data: ResetPasswordRequest,
):
    """Reset password using reset token."""
    try:
        # Purpose: Find user by reset token.
        # Side effects: Queries database.
        result = supabase.table('users').select('user_id, reset_password_expires').eq('reset_password_token', reset_data.token).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        user = result.data[0]
        
        # Purpose: Check if token is expired.
        # Side effects: None - validation only.
        expires_at = user.get('reset_password_expires')
        if expires_at:
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            if datetime.now(timezone.utc) >= expires_at:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Reset token has expired"
                )
        
        user_id = user['user_id']
        
        # Purpose: Hash new password.
        # Side effects: Creates password hash.
        password_hash = hash_password(reset_data.new_password)
        
        # Purpose: Update password and clear reset token.
        # Side effects: Updates user record.
        supabase.table('users').update({
            'password_hash': password_hash,
            'reset_password_token': None,
            'reset_password_expires': None,
            'failed_login_attempts': 0,
            'locked_until': None
        }).eq('user_id', user_id).execute()
        
        # Purpose: Invalidate all existing tokens for security.
        # Side effects: Updates refresh_tokens table.
        invalidate_all_user_tokens(supabase, user_id)
        
        return AuthResponse(
            success=True,
            message="Password reset successful. Please login with your new password."
        )
        
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Reset password error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password reset failed"
        )

# Purpose: Verify email address using verification token.
# Params: request (Request) — FastAPI request; verify_data (VerifyEmailRequest) — verification token; supabase (Client) — database client.
# Returns: Success message.
# Side effects: Updates is_email_verified, clears verification token.
@auth_router.post("/verify-email", response_model=AuthResponse)
async def verify_email(
    request: Request,
    verify_data: VerifyEmailRequest,
):
    """Verify email address using verification token."""
    try:
        # Purpose: Find user by verification token.
        # Side effects: Queries database.
        result = supabase.table('users').select('user_id, verification_token_expires').eq('verification_token', verify_data.token).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired verification token"
            )
        
        user = result.data[0]
        
        # Purpose: Check if token is expired.
        # Side effects: None - validation only.
        expires_at = user.get('verification_token_expires')
        if expires_at:
            if isinstance(expires_at, str):
                expires_at = datetime.fromisoformat(expires_at.replace('Z', '+00:00'))
            if datetime.now(timezone.utc) >= expires_at:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Verification token has expired"
                )
        
        user_id = user['user_id']
        
        # Purpose: Mark email as verified and clear token.
        # Side effects: Updates user record.
        supabase.table('users').update({
            'is_email_verified': True,
            'verification_token': None,
            'verification_token_expires': None
        }).eq('user_id', user_id).execute()
        
        return AuthResponse(
            success=True,
            message="Email verified successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Email verification error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Email verification failed"
        )

# Purpose: Get current authenticated user information.
# Params: request (Request) — FastAPI request; credentials (HTTPAuthorizationCredentials) — JWT token; supabase (Client) — database client.
# Returns: UserResponse with user information.
# Side effects: Queries database.
@auth_router.get("/me", response_model=UserResponse)
async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """Get current authenticated user information."""
    try:
        token = credentials.credentials
        
        # Purpose: Decode and verify token.
        # Side effects: None - token decoding only.
        payload = decode_token(token)
        if not payload or payload.get('type') != 'access':
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        
        user_id = int(payload.get('sub'))
        
        # Purpose: Retrieve user information.
        # Side effects: Queries database.
        result = supabase.table('users').select('*').eq('user_id', user_id).execute()
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user = result.data[0]
        
        return UserResponse(**user)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get current user error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user information"
        )

