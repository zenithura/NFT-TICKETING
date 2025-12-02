# Admin Login System Setup Guide

## Overview

A secure admin login system has been implemented with the following features:
- Dedicated `/admin/login` page
- Secure authentication with JWT tokens stored in HTTP-only cookies
- Rate limiting (5 attempts per 10 minutes)
- Account lockout after failed attempts
- Security event logging
- Protected admin dashboard routes

## Default Admin Credentials

**Username:** `admin`  
**Password:** `Admin123!`

⚠️ **IMPORTANT:** Change these credentials in production!

## Setup Instructions

### 1. Configure Admin Password

Add to your `.env` file:

```bash
# Admin credentials
ADMIN_USERNAME=admin
ADMIN_PASSWORD_HASH=<hashed_password>

# Admin JWT settings (optional)
ADMIN_TOKEN_EXPIRE_MINUTES=480  # 8 hours
```

To generate a password hash, run this in Python:

```python
from passlib.context import CryptContext
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
hash = pwd_context.hash("YourNewPassword123!")
print(hash)
```

Then add the hash to `.env` as `ADMIN_PASSWORD_HASH`.

### 2. Update Database

The admin login system uses the existing `admin_actions` table for logging. Make sure you've run the `admin_security_schema.sql` file.

### 3. Restart Backend

After updating `.env`, restart your backend server:

```bash
cd backend
source venv/bin/activate
python main.py
```

## Routes

### Frontend Routes

- `/admin/login` - Admin login page
- `/admin/dashboard` - Admin dashboard (protected)
- `/admin` - Redirects to `/admin/login`

### Backend API Routes

- `POST /api/admin/login` - Admin login
- `GET /api/admin/session` - Check admin session
- `POST /api/admin/logout` - Admin logout

All `/api/admin/*` routes (except login/session/logout) require admin authentication.

## Security Features

### 1. Rate Limiting
- Maximum 5 login attempts per 10 minutes per IP
- After 5 failed attempts, IP is locked for 10 minutes

### 2. Secure Cookies
- JWT tokens stored in HTTP-only cookies
- Secure flag enabled (HTTPS only)
- SameSite=strict to prevent CSRF
- 8-hour expiration (configurable)

### 3. Security Logging
- All failed login attempts logged to `security_alerts` table
- Successful logins logged to `admin_actions` table
- IP address tracking for all login attempts

### 4. Password Security
- Passwords hashed with bcrypt
- Never stored in plain text
- Configurable via environment variables

## Usage

### Login Flow

1. Navigate to `/admin/login`
2. Enter username: `admin`
3. Enter password: `Admin123!`
4. Click "Login"
5. On success, redirected to `/admin/dashboard`

### Logout

Click the "Logout" button in the admin dashboard header. This will:
- Clear the admin session cookie
- Redirect to `/admin/login`

### Session Management

- Sessions are automatically checked on page load
- Expired sessions redirect to login
- Invalid tokens are rejected

## Troubleshooting

### Can't Login

1. **Check credentials**: Verify username and password are correct
2. **Check rate limit**: If locked, wait 10 minutes or restart backend
3. **Check backend logs**: Look for authentication errors
4. **Verify .env**: Ensure `ADMIN_USERNAME` and `ADMIN_PASSWORD_HASH` are set

### Redirect Loop

If you're stuck in a redirect loop:
1. Clear browser cookies for your domain
2. Check that `/api/admin/session` returns `{"authenticated": false}`
3. Verify backend is running

### Token Not Working

1. Check cookie is being set (browser DevTools → Application → Cookies)
2. Verify `JWT_SECRET_KEY` in `.env` matches backend
3. Check token expiration time

## Production Checklist

- [ ] Change default admin password
- [ ] Set `ADMIN_PASSWORD_HASH` in `.env`
- [ ] Use strong `JWT_SECRET_KEY`
- [ ] Enable HTTPS (required for secure cookies)
- [ ] Configure IP whitelist (optional)
- [ ] Set up monitoring for failed login attempts
- [ ] Review security logs regularly
- [ ] Consider implementing 2FA

## API Examples

### Login

```bash
curl -X POST http://localhost:8000/api/admin/login \
  -H "Content-Type: application/json" \
  -c cookies.txt \
  -d '{"username":"admin","password":"Admin123!"}'
```

### Check Session

```bash
curl -X GET http://localhost:8000/api/admin/session \
  -b cookies.txt
```

### Logout

```bash
curl -X POST http://localhost:8000/api/admin/logout \
  -b cookies.txt \
  -c cookies.txt
```

## Security Best Practices

1. **Never commit `.env` file** with real credentials
2. **Use strong passwords** (minimum 12 characters, mixed case, numbers, symbols)
3. **Rotate passwords** regularly
4. **Monitor failed login attempts** in the admin dashboard
5. **Use HTTPS in production** (required for secure cookies)
6. **Limit admin access** to specific IPs if possible
7. **Enable 2FA** for additional security (future enhancement)

## Future Enhancements

- [ ] Two-factor authentication (2FA)
- [ ] IP whitelist configuration
- [ ] Email notifications for failed login attempts
- [ ] Session management (view active sessions)
- [ ] Password change functionality
- [ ] Login history page

