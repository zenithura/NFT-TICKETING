# Admin Dashboard Setup Guide

## Quick Start

### 1. Update Database Schema

Run the updated `backend/complete_database_schema.sql` in your Supabase SQL Editor. This will create:
- `security_alerts` table
- `bans` table  
- `user_activity_logs` table
- `admin_actions` table

### 2. Create Admin User

To access the admin dashboard, you need a user with `role = 'ADMIN'`:

```sql
-- Update existing user to admin
UPDATE users SET role = 'ADMIN' WHERE email = 'your-email@example.com';

-- Or create new admin user (use registration endpoint first, then update role)
UPDATE users SET role = 'ADMIN' WHERE user_id = 1;
```

### 3. Restart Backend

The security middleware is automatically enabled. Restart your backend server:

```bash
cd backend
source venv/bin/activate
python main.py
```

### 4. Access Dashboard

1. Login with your admin account
2. Navigate to `/admin` in the frontend
3. You should see the Security Admin Dashboard

## Testing the System

### Test XSS Detection

Try making a request with XSS payload:

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"<script>alert(1)</script>"}'
```

This should:
1. Be blocked (403 Forbidden)
2. Create a security alert in the database
3. Show up in the admin dashboard

### Test SQL Injection Detection

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"'\'' OR 1=1 --"}'
```

### View Alerts

1. Go to Admin Dashboard
2. Click "Alerts" tab
3. You should see the detected attacks

## Features Checklist

- ✅ Security detection middleware
- ✅ Admin dashboard UI
- ✅ Alerts management
- ✅ Ban/unban system
- ✅ Charts and analytics
- ✅ Real-time updates (auto-refresh)
- ✅ Export functionality
- ✅ Auto-ban rules

## Next Steps

1. **Monitor Alerts**: Check the dashboard regularly for new security threats
2. **Review Critical Alerts**: Investigate all CRITICAL severity alerts
3. **Adjust Thresholds**: Modify auto-ban rules in `security_middleware.py` if needed
4. **Customize Detection**: Add more patterns to detection functions

## Troubleshooting

**Can't access dashboard:**
- Verify user has `role = 'ADMIN'` in database
- Check authentication token is valid
- Verify backend is running

**No alerts showing:**
- Check if security middleware is enabled in `main.py`
- Verify database tables exist
- Check browser console for errors

**Auto-ban not working:**
- Check `check_auto_ban_conditions` function in `security_middleware.py`
- Verify database triggers
- Check backend logs

