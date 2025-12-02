"""Authentication and user management router."""
from fastapi import APIRouter, HTTPException, Depends, status, Request
from typing import Optional
from datetime import datetime, timedelta, timezone
from supabase import Client

from database import get_supabase_admin
from models import (
    RegisterRequest, LoginRequest, RefreshTokenRequest,
    ForgotPasswordRequest, ResetPasswordRequest, VerifyEmailRequest,
    AuthResponse, UserResponse
)
from auth_utils import (
    hash_password, verify_password, create_access_token, create_refresh_token,
    verify_token, generate_token, validate_password_strength
)
from auth_middleware import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: Request,
    register_data: RegisterRequest,
    db: Client = Depends(get_supabase_admin)
):
    """Register a new user account with email and password."""
    try:
        # Validate password strength
        is_valid, error_msg = validate_password_strength(register_data.password)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        # Validate role
        role_upper = register_data.role.upper()
        if role_upper not in ["BUYER", "ORGANIZER", "SCANNER", "RESELLER"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account type must be BUYER, ORGANIZER, SCANNER, or RESELLER"
            )
        
        # Check if email already exists
        existing = db.table("users").select("user_id").eq("email", register_data.email.lower()).execute()
        if existing.data:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Email already registered"
            )
        
        # Hash password
        password_hash = hash_password(register_data.password)
        
        # Generate email verification token
        verification_token = generate_token()
        verification_expires = datetime.now(timezone.utc) + timedelta(days=7)
        
        # Create user record
        user_data = {
            "email": register_data.email.lower(),
            "password_hash": password_hash,
            "username": register_data.username,
            "first_name": register_data.first_name,
            "last_name": register_data.last_name,
            "role": role_upper,
            "is_email_verified": False,
            "verification_token": verification_token,
            "verification_token_expires": verification_expires.isoformat(),
            "is_active": True
        }
        
        result = db.table("users").insert(user_data).execute()
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user"
            )
        
        user = result.data[0]
        user_id = user["user_id"]
        
        # Generate tokens
        access_token = create_access_token({"sub": str(user_id), "email": user["email"], "role": user["role"]})
        refresh_token = create_refresh_token(user_id)
        
        # Store refresh token
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        db.table("refresh_tokens").insert({
            "user_id": user_id,
            "token": refresh_token,
            "expires_at": expires_at.isoformat(),
            "is_valid": True,
            "ip_address": client_ip,
            "user_agent": user_agent
        }).execute()
        
        # TODO: Send verification email
        
        return AuthResponse(
            success=True,
            message="Registration successful. Please verify your email.",
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserResponse(
                user_id=user["user_id"],
                email=user["email"],
                username=user.get("username"),
                first_name=user.get("first_name"),
                last_name=user.get("last_name"),
                role=user["role"],
                is_email_verified=user.get("is_email_verified", False),
                created_at=user["created_at"]
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )


@router.post("/login", response_model=AuthResponse)
async def login(
    request: Request,
    login_data: LoginRequest,
    db: Client = Depends(get_supabase_admin)
):
    """Login user with email and password."""
    try:
        # Get user by email
        response = db.table("users").select("*").eq("email", login_data.email.lower()).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        user = response.data[0]
        
        # Check if account is active
        if not user.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive"
            )
        
        # Check if account is locked
        locked_until = user.get("locked_until")
        if locked_until:
            lock_time = datetime.fromisoformat(locked_until.replace("Z", "+00:00"))
            if lock_time > datetime.now(timezone.utc):
                raise HTTPException(
                    status_code=status.HTTP_423_LOCKED,
                    detail="Account is temporarily locked"
                )
        
        # Verify password
        password_hash = user.get("password_hash")
        if not password_hash or not verify_password(login_data.password, password_hash):
            # Increment failed login attempts
            failed_attempts = user.get("failed_login_attempts", 0) + 1
            update_data = {"failed_login_attempts": failed_attempts}
            
            # Lock account after 5 failed attempts
            if failed_attempts >= 5:
                update_data["locked_until"] = (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat()
            
            db.table("users").update(update_data).eq("user_id", user["user_id"]).execute()
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Reset failed login attempts
        db.table("users").update({
            "failed_login_attempts": 0,
            "locked_until": None,
            "last_login_at": datetime.now(timezone.utc).isoformat()
        }).eq("user_id", user["user_id"]).execute()
        
        # Generate tokens
        access_token = create_access_token({"sub": str(user["user_id"]), "email": user["email"], "role": user["role"]})
        refresh_token = create_refresh_token(user["user_id"])
        
        # Store refresh token
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        client_ip = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        
        db.table("refresh_tokens").insert({
            "user_id": user["user_id"],
            "token": refresh_token,
            "expires_at": expires_at.isoformat(),
            "is_valid": True,
            "ip_address": client_ip,
            "user_agent": user_agent
        }).execute()
        
        return AuthResponse(
            success=True,
            message="Login successful",
            access_token=access_token,
            refresh_token=refresh_token,
            user=UserResponse(
                user_id=user["user_id"],
                email=user["email"],
                username=user.get("username"),
                first_name=user.get("first_name"),
                last_name=user.get("last_name"),
                role=user["role"],
                is_email_verified=user.get("is_email_verified", False),
                created_at=user["created_at"]
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )


@router.post("/refresh-token", response_model=AuthResponse)
async def refresh_token(
    request: Request,
    refresh_data: RefreshTokenRequest,
    db: Client = Depends(get_supabase_admin)
):
    """Refresh access token using refresh token."""
    try:
        # Verify refresh token
        payload = verify_token(refresh_data.refresh_token, token_type="refresh")
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token"
            )
        
        user_id = int(payload.get("sub"))
        
        # Check if refresh token exists in database and is valid
        token_response = db.table("refresh_tokens").select("*").eq("token", refresh_data.refresh_token).eq("is_valid", True).execute()
        
        if not token_response.data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token not found or invalidated"
            )
        
        token_record = token_response.data[0]
        
        # Check expiration
        expires_at = datetime.fromisoformat(token_record["expires_at"].replace("Z", "+00:00"))
        if expires_at < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expired"
            )
        
        # Get user
        user_response = db.table("users").select("*").eq("user_id", user_id).execute()
        if not user_response.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user = user_response.data[0]
        
        # Generate new access token
        access_token = create_access_token({"sub": str(user_id), "email": user["email"], "role": user["role"]})
        
        # Update last_used_at
        db.table("refresh_tokens").update({
            "last_used_at": datetime.now(timezone.utc).isoformat()
        }).eq("token_id", token_record["token_id"]).execute()
        
        return AuthResponse(
            success=True,
            message="Token refreshed",
            access_token=access_token,
            refresh_token=refresh_data.refresh_token,  # Return same refresh token
            user=UserResponse(
                user_id=user["user_id"],
                email=user["email"],
                username=user.get("username"),
                first_name=user.get("first_name"),
                last_name=user.get("last_name"),
                role=user["role"],
                is_email_verified=user.get("is_email_verified", False),
                created_at=user["created_at"]
            )
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh failed: {str(e)}"
        )


@router.post("/logout")
async def logout(
    refresh_data: RefreshTokenRequest,
    db: Client = Depends(get_supabase_admin)
):
    """Logout user by invalidating refresh token."""
    try:
        # Invalidate refresh token
        db.table("refresh_tokens").update({"is_valid": False}).eq("token", refresh_data.refresh_token).execute()
        
        return {"success": True, "message": "Logged out successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Logout failed: {str(e)}"
        )


@router.post("/forgot-password", response_model=AuthResponse)
async def forgot_password(
    forgot_data: ForgotPasswordRequest,
    db: Client = Depends(get_supabase_admin)
):
    """Request password reset email."""
    try:
        # Get user by email
        response = db.table("users").select("*").eq("email", forgot_data.email.lower()).execute()
        
        if not response.data:
            # Don't reveal if email exists
            return AuthResponse(
                success=True,
                message="If the email exists, a password reset link has been sent"
            )
        
        user = response.data[0]
        
        # Generate reset token
        reset_token = generate_token()
        reset_expires = datetime.now(timezone.utc) + timedelta(hours=1)
        
        # Store reset token
        db.table("users").update({
            "reset_password_token": reset_token,
            "reset_password_expires": reset_expires.isoformat()
        }).eq("user_id", user["user_id"]).execute()
        
        # TODO: Send password reset email
        
        return AuthResponse(
            success=True,
            message="If the email exists, a password reset link has been sent"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process request: {str(e)}"
        )


@router.post("/reset-password", response_model=AuthResponse)
async def reset_password(
    reset_data: ResetPasswordRequest,
    db: Client = Depends(get_supabase_admin)
):
    """Reset password using reset token."""
    try:
        # Validate password strength
        is_valid, error_msg = validate_password_strength(reset_data.new_password)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )
        
        # Find user by reset token
        response = db.table("users").select("*").eq("reset_password_token", reset_data.token).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired reset token"
            )
        
        user = response.data[0]
        
        # Check token expiration
        reset_expires = user.get("reset_password_expires")
        if reset_expires:
            expires_at = datetime.fromisoformat(reset_expires.replace("Z", "+00:00"))
            if expires_at < datetime.now(timezone.utc):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Reset token expired"
                )
        
        # Hash new password
        password_hash = hash_password(reset_data.new_password)
        
        # Update password and clear reset token
        db.table("users").update({
            "password_hash": password_hash,
            "reset_password_token": None,
            "reset_password_expires": None,
            "failed_login_attempts": 0,
            "locked_until": None
        }).eq("user_id", user["user_id"]).execute()
        
        # Invalidate all refresh tokens
        db.table("refresh_tokens").update({"is_valid": False}).eq("user_id", user["user_id"]).execute()
        
        return AuthResponse(
            success=True,
            message="Password reset successful"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Password reset failed: {str(e)}"
        )


@router.post("/verify-email", response_model=AuthResponse)
async def verify_email(
    verify_data: VerifyEmailRequest,
    db: Client = Depends(get_supabase_admin)
):
    """Verify email address using verification token."""
    try:
        # Find user by verification token
        response = db.table("users").select("*").eq("verification_token", verify_data.token).execute()
        
        if not response.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid verification token"
            )
        
        user = response.data[0]
        
        # Check if already verified
        if user.get("is_email_verified", False):
            return AuthResponse(
                success=True,
                message="Email already verified"
            )
        
        # Check token expiration
        verification_expires = user.get("verification_token_expires")
        if verification_expires:
            expires_at = datetime.fromisoformat(verification_expires.replace("Z", "+00:00"))
            if expires_at < datetime.now(timezone.utc):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Verification token expired"
                )
        
        # Mark email as verified
        db.table("users").update({
            "is_email_verified": True,
            "verification_token": None,
            "verification_token_expires": None
        }).eq("user_id", user["user_id"]).execute()
        
        return AuthResponse(
            success=True,
            message="Email verified successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Email verification failed: {str(e)}"
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    user: dict = Depends(get_current_user)
):
    """Get current authenticated user information."""
    return UserResponse(
        user_id=user["user_id"],
        email=user["email"],
        username=user.get("username"),
        first_name=user.get("first_name"),
        last_name=user.get("last_name"),
        role=user["role"],
        is_email_verified=user.get("is_email_verified", False),
        created_at=user["created_at"]
    )
