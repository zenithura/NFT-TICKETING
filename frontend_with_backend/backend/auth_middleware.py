# File header: Authentication middleware for protecting routes and extracting user information.
# Provides dependency injection for authenticated routes and role-based access control.

"""
Authentication middleware for FastAPI.
Provides dependency injection for protected routes and role-based access control.
"""

from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
import logging

from auth import decode_token
from server import supabase

logger = logging.getLogger(__name__)

# Purpose: HTTP Bearer token security scheme.
# Side effects: None - security scheme definition.
security = HTTPBearer()

# Purpose: Get current authenticated user from JWT token.
# Params: credentials (HTTPAuthorizationCredentials) — JWT token from Authorization header.
# Returns: Dictionary with user information.
# Side effects: Queries database to get user details.
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> Dict[str, Any]:
    """
    Get current authenticated user from JWT token.
    Raises HTTPException if token is invalid or user not found.
    """
    try:
        token = credentials.credentials
        
        # Purpose: Decode and verify JWT token.
        # Side effects: None - token decoding only.
        payload = decode_token(token)
        if not payload or payload.get('type') != 'access':
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        
        user_id = int(payload.get('sub'))
        
        # Purpose: Retrieve user from database.
        # Side effects: Queries database.
        result = supabase.table('users').select('*').eq('user_id', user_id).execute()
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user = result.data[0]
        
        # Purpose: Check if user account is active.
        # Side effects: None - validation only.
        if not user.get('is_active', True):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is deactivated"
            )
        
        return user
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Authentication error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed"
        )

# Purpose: Get current user ID from JWT token (lightweight version).
# Params: credentials (HTTPAuthorizationCredentials) — JWT token.
# Returns: User ID integer.
# Side effects: None - token decoding only.
async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> int:
    """
    Get current user ID from JWT token (lightweight, no DB query).
    """
    try:
        token = credentials.credentials
        payload = decode_token(token)
        if not payload or payload.get('type') != 'access':
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired token"
            )
        return int(payload.get('sub'))
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Token decode error: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

# Purpose: Require specific role for route access.
# Params: required_role (str) — required role ('admin', 'organizer', 'user').
# Returns: Dependency function that checks user role.
# Side effects: Queries database if user not already loaded.
def require_role(required_role: str):
    """
    Create dependency that requires specific role.
    Usage: @router.get("/admin", dependencies=[Depends(require_role("admin"))])
    """
    async def role_checker(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        user_role = user.get('role', 'user')
        
        # Purpose: Check role hierarchy (admin > organizer > user).
        # Side effects: None - validation only.
        role_hierarchy = {'admin': 3, 'organizer': 2, 'user': 1}
        user_level = role_hierarchy.get(user_role, 0)
        required_level = role_hierarchy.get(required_role, 0)
        
        if user_level < required_level:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires {required_role} role"
            )
        
        return user
    
    return role_checker

# Purpose: Require admin role.
# Returns: Dependency function.
# Side effects: None - wrapper function.
def require_admin():
    """Require admin role."""
    return require_role('admin')

# Purpose: Require organizer or admin role.
# Returns: Dependency function.
# Side effects: None - wrapper function.
def require_organizer():
    """Require organizer or admin role."""
    async def role_checker(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
        user_role = user.get('role', 'user')
        if user_role not in ['admin', 'organizer']:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Requires organizer or admin role"
            )
        return user
    return role_checker

# Purpose: Optional authentication - returns user if token valid, None otherwise.
# Params: credentials (Optional[HTTPAuthorizationCredentials]) — optional JWT token.
# Returns: User dictionary or None.
# Side effects: Queries database if token provided.
async def get_optional_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False))
) -> Optional[Dict[str, Any]]:
    """
    Get current user if authenticated, None otherwise.
    Useful for routes that work both authenticated and unauthenticated.
    """
    if not credentials:
        return None
    
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None

