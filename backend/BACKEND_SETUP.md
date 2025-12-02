# Backend Setup and Authentication Guide

## Overview

The backend has been updated to support complete email/password authentication with JWT tokens, matching the frontend requirements.

## What's New

### 1. Authentication System
- **Email/Password Registration**: Users can register with email, password, and role (BUYER/ORGANIZER)
- **JWT Tokens**: Access tokens (15 min) and refresh tokens (7 days)
- **Password Security**: Bcrypt hashing with strength validation
- **Account Security**: Failed login attempts tracking, account lockout
- **Email Verification**: Token-based email verification
- **Password Reset**: Secure password reset flow

### 2. New Files
- `auth_utils.py` - JWT token management, password hashing
- `auth_middleware.py` - Authentication middleware and dependencies
- `routers/auth.py` - Complete authentication endpoints

### 3. Updated Files
- `main.py` - Added `/api` prefix to all routes
- `models.py` - Added authentication models matching frontend
- `requirements.txt` - Added JWT and password hashing libraries
- `routers/events.py` - Updated to use authentication

## Installation

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

New dependencies:
- `python-jose[cryptography]` - JWT token handling
- `passlib[bcrypt]` - Password hashing
- `bcrypt` - Password hashing algorithm

### 2. Environment Variables

Create or update `.env` file:

```bash
# Supabase
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key

# JWT Configuration
JWT_SECRET_KEY=your-secret-key-here  # Generate with: python -c "import secrets; print(secrets.token_urlsafe(32))"
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7

# CORS
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
```

### 3. Database Setup

Make sure you've run the complete database schema:
```bash
# Run in Supabase SQL Editor
backend/complete_database_schema.sql
```

## API Endpoints

### Authentication Endpoints (All under `/api/auth`)

#### POST `/api/auth/register`
Register a new user.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "username": "johndoe",
  "first_name": "John",
  "last_name": "Doe",
  "role": "BUYER"  // or "ORGANIZER"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Registration successful. Please verify your email.",
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "user": {
    "user_id": 1,
    "email": "user@example.com",
    "username": "johndoe",
    "first_name": "John",
    "last_name": "Doe",
    "role": "BUYER",
    "is_email_verified": false,
    "created_at": "2025-01-XX..."
  }
}
```

#### POST `/api/auth/login`
Login user.

**Request:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response:** Same as register

#### POST `/api/auth/refresh-token`
Refresh access token.

**Request:**
```json
{
  "refresh_token": "eyJ..."
}
```

**Response:** New access token and user info

#### POST `/api/auth/logout`
Logout user.

**Request:**
```json
{
  "refresh_token": "eyJ..."
}
```

#### POST `/api/auth/forgot-password`
Request password reset.

**Request:**
```json
{
  "email": "user@example.com"
}
```

#### POST `/api/auth/reset-password`
Reset password.

**Request:**
```json
{
  "token": "reset-token-from-email",
  "new_password": "NewSecurePass123!"
}
```

#### POST `/api/auth/verify-email`
Verify email address.

**Request:**
```json
{
  "token": "verification-token-from-email"
}
```

#### GET `/api/auth/me`
Get current user (requires authentication).

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "user_id": 1,
  "email": "user@example.com",
  "username": "johndoe",
  "first_name": "John",
  "last_name": "Doe",
  "role": "BUYER",
  "is_email_verified": true,
  "created_at": "2025-01-XX..."
}
```

## Using Authentication in Routes

### Protect a route (require authentication):

```python
from auth_middleware import get_current_user

@router.get("/protected")
async def protected_route(user: dict = Depends(get_current_user)):
    return {"user_id": user["user_id"], "email": user["email"]}
```

### Require specific role:

```python
from auth_middleware import require_role

@router.post("/events")
async def create_event(
    event: EventCreate,
    user: dict = Depends(require_role("ORGANIZER"))
):
    # Only ORGANIZER role can access
    ...
```

### Optional authentication:

```python
from auth_middleware import get_current_user_optional

@router.get("/public")
async def public_route(user: Optional[dict] = Depends(get_current_user_optional)):
    if user:
        return {"message": f"Hello {user['email']}"}
    return {"message": "Hello anonymous"}
```

## Password Requirements

- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- At least one special character

## Security Features

1. **Password Hashing**: Bcrypt with automatic salt
2. **JWT Tokens**: Secure token generation and validation
3. **Account Lockout**: After 5 failed login attempts, account locked for 30 minutes
4. **Token Expiration**: Access tokens expire in 15 minutes, refresh tokens in 7 days
5. **Token Revocation**: Refresh tokens can be invalidated on logout
6. **Email Verification**: Required for account activation (optional, can be disabled)

## Testing

### Test Registration:
```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!",
    "role": "BUYER"
  }'
```

### Test Login:
```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "TestPass123!"
  }'
```

### Test Protected Route:
```bash
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer <access_token>"
```

## Frontend Integration

The backend now matches the frontend's `authService.ts` expectations:

- All endpoints under `/api/auth`
- Same request/response formats
- JWT tokens in `Authorization: Bearer <token>` header
- Automatic token refresh on 401 errors

## Troubleshooting

### Issue: "Invalid authentication credentials"
- Check JWT_SECRET_KEY is set in .env
- Verify token hasn't expired
- Ensure token is sent in `Authorization: Bearer <token>` header

### Issue: "Email already registered"
- Email must be unique
- Check if user already exists in database

### Issue: "Account is temporarily locked"
- Too many failed login attempts
- Wait 30 minutes or reset password

### Issue: "Invalid or expired reset token"
- Reset tokens expire after 1 hour
- Request a new reset token

## Next Steps

1. **Email Service**: Implement email sending for verification and password reset
2. **Rate Limiting**: Add rate limiting to prevent brute force attacks
3. **2FA**: Add two-factor authentication (optional)
4. **OAuth**: Add social login (Google, GitHub, etc.)

## Files Modified

- ✅ `main.py` - Added `/api` prefix, CORS configuration
- ✅ `models.py` - Added authentication models
- ✅ `routers/auth.py` - Complete rewrite with email/password auth
- ✅ `routers/events.py` - Updated to use authentication
- ✅ `requirements.txt` - Added JWT and password libraries
- ✅ Created `auth_utils.py` - Authentication utilities
- ✅ Created `auth_middleware.py` - Authentication middleware

