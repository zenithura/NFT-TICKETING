# Supabase Authentication Setup with Role Selection

## Overview

This guide explains how to set up the Supabase database schema for user authentication with role selection (Buyer/Organizer) during signup.

## Database Schema

### SQL File Location
`backend/supabase_auth_schema.sql`

### Tables Created

#### 1. `users` Table
Stores all user account information including:
- **Authentication fields**: `email`, `password_hash`
- **Profile fields**: `username`, `first_name`, `last_name`
- **Role**: `BUYER` or `ORGANIZER` (selected during signup)
- **Email verification**: `is_email_verified`, `verification_token`, `verification_token_expires`
- **Password reset**: `reset_password_token`, `reset_password_expires`
- **Security**: `is_active`, `failed_login_attempts`, `locked_until`
- **Timestamps**: `created_at`, `updated_at`, `last_login_at`
- **Optional**: `wallet_address` (for Web3 integration)

#### 2. `refresh_tokens` Table
Stores JWT refresh tokens for session management:
- `token_id`, `user_id`, `token`, `expires_at`, `is_valid`
- `created_at`, `last_used_at`, `ip_address`, `user_agent`

## Setup Instructions

### Step 1: Run SQL Schema in Supabase

1. Open your Supabase project dashboard
2. Go to **SQL Editor**
3. Click **New Query**
4. Copy and paste the entire contents of `backend/supabase_auth_schema.sql`
5. Click **Run** (or press `Ctrl+Enter`)

### Step 2: Verify Tables Created

Run these queries to verify:

```sql
-- Check if tables exist
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_name IN ('users', 'refresh_tokens');

-- Check users table structure
SELECT column_name, data_type, is_nullable, column_default 
FROM information_schema.columns 
WHERE table_name = 'users' 
ORDER BY ordinal_position;

-- Check role constraint
SELECT conname, contype, pg_get_constraintdef(oid) 
FROM pg_constraint 
WHERE conrelid = 'users'::regclass 
  AND conname LIKE '%role%';
```

### Step 3: Configure Backend

Ensure your backend `.env` file has:

```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-role-key
```

### Step 4: Test Registration

1. Start your backend server
2. Start your frontend
3. Navigate to `/register`
4. Fill in the registration form
5. **Select role**: Choose either "Buyer" or "Organizer"
6. Submit the form

## Frontend Changes

### Registration Form
- Added role selection UI with two buttons:
  - **Buyer**: For purchasing and managing NFT tickets
  - **Organizer**: For creating and managing events
- Role is required and defaults to "BUYER"
- Visual feedback shows selected role

### Data Sent to Backend
```typescript
{
  email: string,
  password: string,
  username?: string,
  first_name?: string,
  last_name?: string,
  role: 'BUYER' | 'ORGANIZER'  // Required
}
```

## Backend Changes

### RegisterRequest Model
- Added `role` field (required)
- Validates role is either `BUYER` or `ORGANIZER`
- Automatically converts to uppercase

### Registration Endpoint
- Accepts `role` from request
- Stores role in database (replaces hardcoded 'user')
- Returns user with selected role

## Database Columns Reference

### Users Table Columns

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| `user_id` | BIGSERIAL | NO | Auto | Primary key |
| `email` | VARCHAR(255) | NO | - | Unique email address |
| `password_hash` | VARCHAR(255) | NO | - | Bcrypt/Argon2 hash |
| `username` | VARCHAR(100) | YES | NULL | Optional username |
| `first_name` | VARCHAR(100) | YES | NULL | First name |
| `last_name` | VARCHAR(100) | YES | NULL | Last name |
| `role` | VARCHAR(20) | NO | 'BUYER' | BUYER or ORGANIZER |
| `is_email_verified` | BOOLEAN | YES | FALSE | Email verification status |
| `verification_token` | VARCHAR(255) | YES | NULL | Email verification token |
| `verification_token_expires` | TIMESTAMPTZ | YES | NULL | Token expiration |
| `reset_password_token` | VARCHAR(255) | YES | NULL | Password reset token |
| `reset_password_expires` | TIMESTAMPTZ | YES | NULL | Reset token expiration |
| `is_active` | BOOLEAN | YES | TRUE | Account active status |
| `failed_login_attempts` | INTEGER | YES | 0 | Failed login counter |
| `locked_until` | TIMESTAMPTZ | YES | NULL | Account lockout time |
| `created_at` | TIMESTAMPTZ | NO | NOW() | Account creation time |
| `updated_at` | TIMESTAMPTZ | NO | NOW() | Last update time |
| `last_login_at` | TIMESTAMPTZ | YES | NULL | Last login time |
| `wallet_address` | VARCHAR(255) | YES | NULL | Optional wallet address |

## Role Values

### Supported Roles
- `BUYER` - Default role for ticket purchasers
- `ORGANIZER` - For event creators and managers
- `ADMIN` - For platform administrators (not selectable during signup)
- `RESELLER` - For ticket resellers (future use)
- `SCANNER` - For event scanners (future use)

### Role Selection
- Users can only select `BUYER` or `ORGANIZER` during signup
- Other roles must be assigned by administrators
- Role is validated on both frontend and backend

## Security Features

1. **Password Hashing**: Passwords are hashed using bcrypt/Argon2
2. **Email Verification**: Tokens expire after 7 days
3. **Account Lockout**: After failed login attempts
4. **Token Management**: Refresh tokens can be revoked
5. **Row Level Security**: Enabled (configure policies as needed)

## Indexes

Performance indexes created:
- `idx_users_email` - Fast email lookups
- `idx_users_role` - Fast role filtering
- `idx_users_verification_token` - Fast token lookups
- `idx_users_reset_token` - Fast reset token lookups
- `idx_refresh_tokens_user_id` - Fast user token queries
- `idx_refresh_tokens_token` - Fast token validation
- `idx_refresh_tokens_expires` - Fast expired token cleanup

## Testing

### Test Registration Flow

1. **Test Buyer Registration**:
   ```bash
   curl -X POST http://localhost:8000/api/auth/register \
     -H "Content-Type: application/json" \
     -d '{
       "email": "buyer@example.com",
       "password": "SecurePass123!",
       "first_name": "John",
       "last_name": "Doe",
       "role": "BUYER"
     }'
   ```

2. **Test Organizer Registration**:
   ```bash
   curl -X POST http://localhost:8000/api/auth/register \
     -H "Content-Type: application/json" \
     -d '{
       "email": "organizer@example.com",
       "password": "SecurePass123!",
       "first_name": "Jane",
       "last_name": "Smith",
       "role": "ORGANIZER"
     }'
   ```

3. **Test Invalid Role** (should fail):
   ```bash
   curl -X POST http://localhost:8000/api/auth/register \
     -H "Content-Type: application/json" \
     -d '{
       "email": "test@example.com",
       "password": "SecurePass123!",
       "role": "INVALID"
     }'
   ```

### Verify Database Records

```sql
-- Check registered users
SELECT user_id, email, role, is_email_verified, created_at 
FROM users 
ORDER BY created_at DESC;

-- Check role distribution
SELECT role, COUNT(*) as count 
FROM users 
GROUP BY role;
```

## Troubleshooting

### Issue: "Role must be one of: BUYER, ORGANIZER"
- **Cause**: Invalid role value sent
- **Solution**: Ensure frontend sends exactly 'BUYER' or 'ORGANIZER'

### Issue: "Email already registered"
- **Cause**: Email exists in database
- **Solution**: Use different email or check existing users

### Issue: "Failed to create user"
- **Cause**: Database constraint violation or connection issue
- **Solution**: Check Supabase connection, verify schema is applied

### Issue: Role not saved correctly
- **Cause**: Backend not using role from request
- **Solution**: Verify `auth_routes.py` uses `register_data.role` not hardcoded value

## Next Steps

1. **Email Verification**: Implement email sending service
2. **Password Reset**: Implement password reset email
3. **Role-Based Access**: Add middleware to check user roles
4. **Admin Panel**: Create admin interface for role management
5. **Analytics**: Track user registrations by role

## Files Modified

### Created:
- `backend/supabase_auth_schema.sql` - Complete database schema

### Modified:
- `frontend/pages/Register.tsx` - Added role selection UI
- `frontend/services/authService.ts` - Added role to RegisterData interface
- `frontend/locales/en/translation.json` - Added role translations
- `frontend/locales/az/translation.json` - Added role translations
- `backend/auth_routes.py` - Added role validation and storage

## Support

For issues or questions:
1. Check Supabase logs in dashboard
2. Check backend logs for errors
3. Verify SQL schema was applied correctly
4. Test API endpoints directly with curl/Postman

