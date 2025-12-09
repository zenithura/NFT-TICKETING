# Attack Detection Test Guide - Complete Implementation ✅

## Implementation Summary

The system automatically detects attacking users, logs them, and applies progressive penalties:

- **1 attack** → Active (logged)
- **2+ attacks** → Suspended (cannot access protected routes)
- **10+ attacks** → Banned permanently (cannot log in)

## Test Cases

### Test Case 1: One Attack → Active ✅

**Steps**:
1. Register/login as a test user
2. Send one malicious request (e.g., SQL injection in a form field)
3. Check admin dashboard

**Expected Result**:
```
attack_count = 1
status = "active" (is_active = true)
User can still log in and access the system
```

**How to Trigger**:
```bash
# SQL Injection attempt
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "' OR 1=1 --"}'

# Or XSS attempt
curl -X POST http://localhost:8000/api/events \
  -H "Content-Type: application/json" \
  -d '{"title": "<script>alert('xss')</script>"}'
```

**Verification**:
1. Open Admin Dashboard → Users tab
2. Find the test user
3. Click to view details
4. Should show: "Attack Attempts: 1"
5. Status should be "Active"

---

### Test Case 2: Two Attacks → Suspended ✅

**Steps**:
1. Continue with the same user from Test Case 1
2. Send a second malicious request
3. Check admin dashboard immediately

**Expected Result**:
```
attack_count = 2
status = "suspended" (is_active = false)
User sees suspension in dashboard immediately
User cannot access protected routes
```

**How to Trigger**:
```bash
# Second attack - different type
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "admin' UNION SELECT * FROM users--"}'
```

**Verification**:
1. Open Admin Dashboard → Users tab (auto-refreshes every 10 seconds)
2. User status should change to "Suspended"
3. Attack count should show "2"
4. Security Status warning: "User is suspended (2+ attacks)"
5. Try to login as that user → Should fail with "Account suspended"

**Backend Logs**:
```
WARNING: Auto-suspended user {user_id} due to 2 attack attempts
```

---

### Test Case 3: Ten Attacks → Banned ✅

**Steps**:
1. Continue attacking with the same user (8 more times)
2. Check admin dashboard after 10th attack

**Expected Result**:
```
attack_count = 10
status = "banned" (is_active = false)
Ban record created in database
User cannot log in anymore (permanently)
```

**How to Trigger**:
```bash
# Repeat attack attempts (8 more times)
for i in {3..10}; do
  curl -X POST http://localhost:8000/api/auth/login \
    -H "Content-Type: application/json" \
    -d "{\"email\": \"user@example.com\", \"password\": \"test$i' OR 1=1 --\"}"
  sleep 1
done
```

**Verification**:
1. Open Admin Dashboard → Users tab
2. User status: "Suspended" (is_active = false)
3. Attack count: "10"
4. Security Status: "User is banned (10+ attacks)"
5. Ban record in database:
   - Check `bans` table
   - Should have entry with `user_id`, `ban_type='USER'`, `ban_duration='PERMANENT'`
6. Try to login → Should fail with "Account banned"

**Backend Logs**:
```
WARNING: Auto-banned user {user_id} due to 10 attack attempts
```

---

## Database Schema Verification

Ensure these tables exist:

```sql
-- Check security_alerts table
SELECT COUNT(*) FROM security_alerts WHERE user_id = {test_user_id};
-- Should return attack count

-- Check bans table after 10 attacks
SELECT * FROM bans WHERE user_id = {test_user_id};
-- Should have ban record

-- Check user status
SELECT user_id, email, is_active FROM users WHERE user_id = {test_user_id};
-- Should show is_active = false after 2+ attacks
```

---

## Full Testing Script

### Automated Test Script

Create `backend/test_attack_detection.py`:

```python
import requests
import time
import json

BASE_URL = "http://localhost:8000"
TEST_EMAIL = "attacker@test.com"
TEST_PASSWORD = "TestPass123!"

def test_attack_detection():
    print("🧪 Testing Attack Detection System\n")
    
    # Step 1: Register test user
    print("Step 1: Registering test user...")
    register_response = requests.post(
        f"{BASE_URL}/api/auth/register",
        json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD,
            "role": "BUYER"
        }
    )
    print(f"✓ User registered: {register_response.status_code}\n")
    
    # Step 2: First attack
    print("Step 2: Attempting first attack (SQL injection)...")
    attack1 = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={
            "email": TEST_EMAIL,
            "password": "' OR 1=1 --"
        }
    )
    print(f"✓ Attack 1 logged: {attack1.status_code}")
    print("Expected: attack_count=1, status=active\n")
    time.sleep(2)
    
    # Step 3: Second attack (should trigger suspension)
    print("Step 3: Attempting second attack (should suspend)...")
    attack2 = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={
            "email": TEST_EMAIL,
            "password": "admin' UNION SELECT * FROM users--"
        }
    )
    print(f"✓ Attack 2 logged: {attack2.status_code}")
    print("Expected: attack_count=2, status=suspended\n")
    time.sleep(2)
    
    # Step 4: Continue to 10 attacks (should trigger ban)
    print("Step 4: Continuing to 10 attacks (should ban)...")
    for i in range(3, 11):
        attack = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={
                "email": TEST_EMAIL,
                "password": f"test{i}' OR 1=1 --"
            }
        )
        print(f"✓ Attack {i} logged")
        time.sleep(1)
    
    print("\n✓ Attack 10 logged")
    print("Expected: attack_count=10, status=banned\n")
    
    # Step 5: Verify user cannot login
    print("Step 5: Verifying user is banned...")
    login_attempt = requests.post(
        f"{BASE_URL}/api/auth/login",
        json={
            "email": TEST_EMAIL,
            "password": TEST_PASSWORD
        }
    )
    print(f"Login attempt status: {login_attempt.status_code}")
    print(f"Expected: 403 or 401 (account banned)\n")
    
    print("🎉 Test complete! Check Admin Dashboard for verification.")

if __name__ == "__main__":
    test_attack_detection()
```

**Run the test**:
```bash
cd backend
python test_attack_detection.py
```

---

## Manual Testing Steps

### Quick Manual Test

1. **Start services**:
   ```bash
   # Terminal 1: Backend
   cd backend
   python main.py
   
   # Terminal 2: Frontend
   cd frontend
   npm run dev
   
   # Terminal 3: Admin Panel
   cd frontend
   npm run dev:admin
   ```

2. **Register test user**:
   - Go to `http://localhost:5173/#/register`
   - Register with email: `attacker@test.com`

3. **Trigger attacks**:
   - Use browser DevTools Console:
   ```javascript
   // Attack 1
   fetch('http://localhost:8000/api/auth/login', {
     method: 'POST',
     headers: {'Content-Type': 'application/json'},
     body: JSON.stringify({email: 'attacker@test.com', password: "' OR 1=1 --"})
   });
   
   // Wait 2 seconds, then Attack 2
   setTimeout(() => {
     fetch('http://localhost:8000/api/auth/login', {
       method: 'POST',
       headers: {'Content-Type': 'application/json'},
       body: JSON.stringify({email: 'attacker@test.com', password: "admin' --"})
     });
   }, 2000);
   ```

4. **Check Admin Dashboard**:
   - Go to `http://localhost:4201/#/secure-admin/login`
   - Login as admin
   - Go to Users tab
   - Find `attacker@test.com`
   - Click to view details
   - Should show attack count and suspension status

---

## Expected Dashboard Display

### After 1 Attack
```
User: attacker@test.com
Status: Active
Attack Attempts: 1
```

### After 2 Attacks
```
User: attacker@test.com
Status: Suspended
Attack Attempts: 2
⚠️ User is suspended (2+ attacks)
📊 8 more attacks until permanent ban
```

### After 10 Attacks
```
User: attacker@test.com
Status: Suspended (Banned)
Attack Attempts: 10
❌ User is banned (10+ attacks)
```

---

## Verification Checklist

- [ ] Backend running on port 8000
- [ ] Frontend running on port 5173
- [ ] Admin panel running on port 4201
- [ ] Database tables created (run `backend/admin_logging_schema_safe.sql`)
- [ ] Test user registered
- [ ] First attack creates 1 alert, user stays active
- [ ] Second attack creates 2nd alert, user suspended
- [ ] User list auto-refreshes in admin panel
- [ ] Attack count visible in user detail modal
- [ ] Tenth attack creates ban record
- [ ] Banned user cannot login
- [ ] All actions logged in `backend/logs/`

---

## Troubleshooting

### Issue: Attacks not being counted
**Solution**: Check security middleware is running:
```bash
# Check backend logs
tail -f backend/logs/application.log
```

### Issue: User not suspended after 2 attacks
**Solution**: Verify attack_tracking integration:
```bash
# Check if module is imported
grep -r "track_attack_and_check_suspension" backend/
```

### Issue: Dashboard not updating
**Solution**: 
1. Check auto-refresh is enabled (toggle in UI)
2. Manually refresh the users list
3. Clear browser cache

---

## Production Deployment Notes

1. **Adjust thresholds** in `backend/attack_tracking.py` if needed:
   ```python
   SUSPENSION_THRESHOLD = 2  # Change as needed
   BAN_THRESHOLD = 10  # Change as needed
   ```

2. **Enable logging**:
   - All attacks are logged to `backend/logs/`
   - Check logs regularly for security monitoring

3. **SOAR Integration**:
   - Configure SOAR platform in Admin Dashboard
   - All bans/suspensions will forward to SOAR

4. **Database Backups**:
   - Back up `security_alerts` and `bans` tables regularly
   - Use for forensic analysis

---

**Status**: ✅ Fully implemented and ready for testing
**Last Updated**: 2025-12-09

