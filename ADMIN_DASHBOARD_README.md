# Admin Dashboard & Security Alerts System

## Overview

A comprehensive admin dashboard with real-time security monitoring, threat detection, and alert management system. The system automatically detects and logs various types of attacks including XSS, SQL injection, command injection, brute force attempts, and suspicious activities.

## Features

### 1. Security Detection Middleware

The backend middleware (`security_middleware.py`) automatically detects:

- **XSS Attacks**: Detects script tags, event handlers, and encoded XSS payloads
- **SQL Injection**: Detects SQL injection patterns like `' OR 1=1 --`, `UNION SELECT`, etc.
- **Command Injection**: Detects shell command injection attempts
- **Brute Force**: Tracks excessive login attempts and rate limiting violations
- **Unauthorized Access**: Monitors invalid tokens and access to protected routes
- **API Abuse**: Detects excessive requests and suspicious user agents
- **Penetration Testing Tools**: Identifies common security scanning tools

### 2. Admin Dashboard

#### Overview Page
- **Statistics Cards**: Total users, alerts (24h/7d/30d), banned users/IPs, system health
- **Charts**:
  - Alerts timeline (line chart)
  - Alerts by type (pie chart)
  - Alerts by severity (bar chart)
  - Top attacking IPs
  - Top attacked endpoints

#### Alerts Management
- **Filtering**: By severity, attack type, status, IP address, user ID, date range
- **Alert Details**: Full payload, IP address, user agent, risk score, metadata
- **Actions**:
  - Mark as Reviewed
  - Ignore
  - Ban User/IP
  - Export as JSON/CSV
- **Real-time Updates**: Auto-refresh every 10 seconds (configurable)

#### User Management
- View all users
- Search users
- Ban/unban users
- View user activity logs

### 3. Auto-Ban System

The system automatically bans users/IPs when:
- **3+ critical alerts** from the same user → Permanent ban
- **10+ alerts in 5 minutes** from the same IP → Temporary ban (1 hour)

### 4. Database Schema

#### `security_alerts` Table
- Stores all detected security threats
- Tracks attack type, severity, risk score, payload, IP, user, endpoint
- Status: NEW, REVIEWED, BANNED, IGNORED, FALSE_POSITIVE

#### `bans` Table
- Stores banned users and IP addresses
- Supports temporary and permanent bans
- Tracks ban reason, duration, expiration

#### `user_activity_logs` Table
- Logs all user activities for audit trail
- Tracks page visits, API calls, actions

#### `admin_actions` Table
- Logs all admin actions for accountability
- Tracks who did what and when

## API Endpoints

### Admin Endpoints (Requires ADMIN role)

- `GET /api/admin/stats` - Get dashboard statistics
- `GET /api/admin/alerts` - Get security alerts with filters
- `GET /api/admin/alerts/{id}` - Get specific alert details
- `PATCH /api/admin/alerts/{id}/status` - Update alert status
- `POST /api/admin/ban` - Ban a user or IP
- `POST /api/admin/unban` - Unban a user or IP
- `GET /api/admin/graph-data` - Get chart data
- `GET /api/admin/alerts-stream` - Real-time alerts via SSE
- `GET /api/admin/export-alerts` - Export alerts as JSON/CSV
- `GET /api/admin/users` - Get all users

## Setup

### 1. Database Setup

Run the updated `complete_database_schema.sql` in your Supabase SQL Editor to create:
- `security_alerts` table
- `bans` table
- `user_activity_logs` table
- `admin_actions` table
- All necessary indexes and RLS policies

### 2. Backend Setup

The security middleware is automatically enabled in `main.py`. It intercepts all requests and:
- Scans request bodies and query parameters for attack patterns
- Logs detected threats to the database
- Blocks critical attacks immediately
- Checks for banned users/IPs before processing requests

### 3. Frontend Setup

The admin dashboard is available at `/admin` route (protected by ADMIN role check).

To access:
1. User must have `role = 'ADMIN'` in the database
2. User must be authenticated
3. Navigate to `/admin` in the frontend

## Usage

### Accessing the Dashboard

1. **Login as Admin**: Ensure your user account has `role = 'ADMIN'` in the database
2. **Navigate**: Go to `/admin` route in the frontend
3. **View Alerts**: Click on "Alerts" tab to see all security alerts
4. **Filter**: Use filters to find specific alerts
5. **Take Action**: Review, ignore, or ban based on alert severity

### Monitoring Security

The dashboard automatically:
- Detects attacks in real-time
- Logs all security events
- Calculates risk scores (0-100)
- Assigns severity levels (LOW, MEDIUM, HIGH, CRITICAL)
- Triggers auto-ban when thresholds are met

### Manual Actions

**Ban a User/IP:**
1. Go to Alerts tab
2. Click on an alert to view details
3. Click "Ban User/IP" button
4. Confirm the ban

**Update Alert Status:**
1. Select an alert
2. Choose action: Review, Ignore, or Mark as False Positive
3. Status updates immediately

**Export Alerts:**
1. Go to Alerts tab
2. Apply filters if needed
3. Click "Export JSON" or "Export CSV"
4. File downloads automatically

## Security Features

### Threat Detection Patterns

**XSS Detection:**
- `<script>` tags
- `javascript:` protocol
- Event handlers (`onerror`, `onload`, `onclick`)
- HTML entities and encoding
- `eval()`, `document.cookie`, `innerHTML`

**SQL Injection Detection:**
- `' OR 1=1 --`
- `UNION SELECT`
- `DROP TABLE`, `TRUNCATE`
- `information_schema`, `pg_catalog`
- Time-based SQLi patterns

**Command Injection Detection:**
- Shell commands (`rm`, `cat`, `ls`, etc.)
- Command chaining (`;`, `&&`, `|`)
- Code execution (`bash -c`, `python -c`)

### Rate Limiting

- **100 requests per minute** per IP/endpoint combination
- Exceeding limit triggers `RATE_LIMIT_EXCEEDED` alert
- Repeated violations may trigger auto-ban

### Ban System

**Temporary Bans:**
- Duration: Configurable (default: 1 hour for auto-bans)
- Expires automatically
- Can be manually extended or made permanent

**Permanent Bans:**
- No expiration
- Must be manually removed
- User account is deactivated

## Risk Scoring

Risk scores (0-100) are calculated based on:
- Attack type (base score)
- Severity level (multiplier)
- Payload complexity (bonus for complex payloads)

**Base Scores:**
- XSS: 60
- SQL Injection: 80
- Command Injection: 90
- Brute Force: 50
- Unauthorized Access: 70
- API Abuse: 40

**Severity Multipliers:**
- LOW: 0.5x
- MEDIUM: 0.75x
- HIGH: 1.0x
- CRITICAL: 1.25x

## Real-Time Updates

The dashboard supports real-time alert streaming via Server-Sent Events (SSE):
- Endpoint: `GET /api/admin/alerts-stream`
- Auto-refresh: Every 10 seconds (configurable)
- Manual refresh: Click refresh button
- New alerts: Highlighted with badge count

## Best Practices

1. **Regular Review**: Review new alerts daily
2. **Investigate Critical**: Always investigate CRITICAL severity alerts
3. **False Positives**: Mark legitimate traffic as FALSE_POSITIVE
4. **Ban Carefully**: Only ban after confirming malicious intent
5. **Monitor Trends**: Use charts to identify attack patterns
6. **Export Logs**: Regularly export alerts for compliance/audit

## Troubleshooting

### Alerts Not Showing
- Check database connection
- Verify user has ADMIN role
- Check browser console for errors
- Verify backend is running

### Auto-Ban Not Working
- Check database triggers
- Verify `security_alerts` table has data
- Check backend logs for errors

### Real-Time Updates Not Working
- Check SSE endpoint is accessible
- Verify browser supports EventSource
- Check network tab for connection issues

## Future Enhancements

- [ ] WebSocket support for bidirectional communication
- [ ] Email notifications for critical alerts
- [ ] GeoIP integration for IP location
- [ ] Machine learning for anomaly detection
- [ ] Integration with external security services
- [ ] Custom alert rules and thresholds
- [ ] Alert correlation and grouping
- [ ] Automated response actions

## Support

For issues or questions:
1. Check backend logs: `backend/logs/`
2. Check browser console for frontend errors
3. Verify database schema is up to date
4. Ensure all environment variables are set

