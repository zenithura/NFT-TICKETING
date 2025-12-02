# Authentication System - Quick Setup Guide

**Date**: 2025-01-28  
**Version**: 1.0

---

## Quick Start

### 1. Database Setup

Run the authentication schema migration:

```bash
cd frontend_with_backend/backend
psql -h your-supabase-host -U postgres -d postgres -f auth_schema.sql
```

Or via Supabase Dashboard:
1. Go to SQL Editor
2. Copy contents of `auth_schema.sql`
3. Execute the SQL

---

### 2. Environment Variables

Add to `.env` file in `frontend_with_backend/backend/`:

```bash
# Required
JWT_SECRET=your-very-secure-random-secret-key-min-32-characters-long
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key

# Optional (with defaults)
ACCESS_TOKEN_EXPIRE_MINUTES=15
REFRESH_TOKEN_EXPIRE_DAYS=7
MAX_LOGIN_ATTEMPTS=5
LOCKOUT_DURATION_MINUTES=30
```

**Generate JWT Secret**:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

---

### 3. Frontend Configuration

Add to `.env` file in `frontend/` (or `frontend/.env.local`):

```bash
VITE_API_URL=http://localhost:8000/api
```

For production:
```bash
VITE_API_URL=https://api.yourdomain.com/api
```

---

### 4. Install Dependencies

Backend dependencies are already in `requirements.txt`:
- `bcrypt` - Password hashing
- `PyJWT` - JWT token management

Frontend dependencies are already in `package.json`:
- `react-router-dom` - Routing (already installed)
- `react-hot-toast` - Notifications (already installed)

---

### 5. Start Services

**Backend**:
```bash
cd frontend_with_backend/backend
source venv/bin/activate  # or .venv/bin/activate
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```

**Frontend**:
```bash
cd frontend
npm install
npm run dev
```

---

## Testing the Authentication System

### 1. Test Registration

```bash
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test1234!",
    "username": "testuser",
    "first_name": "Test",
    "last_name": "User"
  }'
```

**Expected Response**:
```json
{
  "success": true,
  "message": "Registration successful. Please verify your email.",
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "user": {
    "user_id": 1,
    "email": "test@example.com",
    "username": "testuser",
    "role": "user",
    "is_email_verified": false
  }
}
```

---

### 2. Test Login

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "Test1234!"
  }'
```

**Expected Response**:
```json
{
  "success": true,
  "message": "Login successful",
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "user": {...}
}
```

---

### 3. Test Protected Route

```bash
curl -X GET http://localhost:8000/api/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

**Expected Response**:
```json
{
  "user_id": 1,
  "email": "test@example.com",
  "username": "testuser",
  "role": "user",
  "is_email_verified": false
}
```

---

### 4. Test Token Refresh

```bash
curl -X POST http://localhost:8000/api/auth/refresh-token \
  -H "Content-Type: application/json" \
  -d '{
    "refresh_token": "YOUR_REFRESH_TOKEN"
  }'
```

---

## Frontend Testing

1. **Navigate to Login**: `http://localhost:3000/login`
2. **Test Registration**: Click "Sign up" link
3. **Test Login**: Enter credentials and submit
4. **Test Protected Routes**: Try accessing `/dashboard` (should redirect to login if not authenticated)
5. **Test Logout**: Click logout button in navbar

---

## Common Issues

### Issue: "JWT_SECRET not set"
**Solution**: Add `JWT_SECRET` to `.env` file

### Issue: "Failed to initialize Supabase"
**Solution**: Check `SUPABASE_URL` and `SUPABASE_KEY` in `.env`

### Issue: "Table 'users' does not exist"
**Solution**: Run `auth_schema.sql` migration

### Issue: "Invalid token" on frontend
**Solution**: Check `VITE_API_URL` matches backend URL

### Issue: CORS errors
**Solution**: Ensure backend CORS configuration includes frontend URL

---

## Security Checklist

- [ ] `JWT_SECRET` is strong and random (32+ characters)
- [ ] `JWT_SECRET` is different for production
- [ ] Database has proper indexes
- [ ] Rate limiting is configured
- [ ] HTTPS enabled in production
- [ ] Email service configured (for verification/reset)
- [ ] Environment variables not committed to git

---

## Next Steps

1. **Configure Email Service** (SendGrid, AWS SES, etc.)
   - Update `auth_routes.py` to send verification emails
   - Update `auth_routes.py` to send password reset emails

2. **Add 2FA** (Optional)
   - Implement TOTP support
   - Add SMS verification

3. **Social Login** (Optional)
   - Google OAuth
   - Meta OAuth

---

**Status**: ✅ Ready for Use

