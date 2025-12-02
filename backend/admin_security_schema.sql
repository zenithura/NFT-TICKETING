-- ============================================================================
-- ADMIN DASHBOARD & SECURITY ALERTS SYSTEM - DATABASE SCHEMA
-- ============================================================================
-- This file contains ONLY the new tables and changes for the Admin Dashboard
-- and Security Alerts System. Run this AFTER the main schema is set up.
-- ============================================================================
-- Run this file in your Supabase SQL Editor
-- ============================================================================

-- ============================================================================
-- SECURITY & ADMIN TABLES
-- ============================================================================

-- Security Alerts table
-- Stores all detected security threats and attacks
CREATE TABLE IF NOT EXISTS security_alerts (
    alert_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(user_id) ON DELETE SET NULL,
    ip_address VARCHAR(45) NOT NULL,
    attack_type VARCHAR(50) NOT NULL CHECK (attack_type IN ('XSS', 'SQL_INJECTION', 'COMMAND_INJECTION', 'BRUTE_FORCE', 'UNAUTHORIZED_ACCESS', 'API_ABUSE', 'SUSPICIOUS_ACTIVITY', 'RATE_LIMIT_EXCEEDED', 'INVALID_TOKEN', 'PENETRATION_TEST')),
    payload TEXT,
    endpoint VARCHAR(500),
    severity VARCHAR(20) NOT NULL DEFAULT 'MEDIUM' CHECK (severity IN ('LOW', 'MEDIUM', 'HIGH', 'CRITICAL')),
    risk_score INTEGER DEFAULT 50 CHECK (risk_score >= 0 AND risk_score <= 100),
    status VARCHAR(20) NOT NULL DEFAULT 'NEW' CHECK (status IN ('NEW', 'REVIEWED', 'BANNED', 'IGNORED', 'FALSE_POSITIVE')),
    user_agent TEXT,
    country_code VARCHAR(2),
    city VARCHAR(100),
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    reviewed_at TIMESTAMPTZ,
    reviewed_by BIGINT REFERENCES users(user_id) ON DELETE SET NULL
);

-- Banned Users/IPs table
-- Stores banned users and IP addresses with ban details
CREATE TABLE IF NOT EXISTS bans (
    ban_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
    ip_address VARCHAR(45),
    ban_type VARCHAR(20) NOT NULL CHECK (ban_type IN ('USER', 'IP', 'BOTH')),
    ban_reason TEXT NOT NULL,
    ban_duration VARCHAR(20) NOT NULL DEFAULT 'PERMANENT' CHECK (ban_duration IN ('TEMPORARY', 'PERMANENT')),
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_by BIGINT REFERENCES users(user_id) ON DELETE SET NULL,
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT
);

-- User Activity Log table
-- Logs all user activities for audit trail and security analysis
CREATE TABLE IF NOT EXISTS user_activity_logs (
    log_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(user_id) ON DELETE CASCADE,
    action_type VARCHAR(50) NOT NULL,
    page_visited VARCHAR(500),
    endpoint VARCHAR(500),
    ip_address VARCHAR(45),
    user_agent TEXT,
    request_method VARCHAR(10),
    request_body JSONB,
    response_status INTEGER,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Admin Actions Log table
-- Logs all admin actions for accountability and audit trail
CREATE TABLE IF NOT EXISTS admin_actions (
    action_id BIGSERIAL PRIMARY KEY,
    admin_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    action_type VARCHAR(50) NOT NULL,
    target_type VARCHAR(50) NOT NULL CHECK (target_type IN ('USER', 'IP', 'ALERT', 'SYSTEM')),
    target_id BIGINT,
    details JSONB,
    ip_address VARCHAR(45),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- INDEXES FOR PERFORMANCE
-- ============================================================================

-- Indexes for security_alerts table
CREATE INDEX IF NOT EXISTS idx_security_alerts_user_id ON security_alerts(user_id);
CREATE INDEX IF NOT EXISTS idx_security_alerts_ip_address ON security_alerts(ip_address);
CREATE INDEX IF NOT EXISTS idx_security_alerts_attack_type ON security_alerts(attack_type);
CREATE INDEX IF NOT EXISTS idx_security_alerts_severity ON security_alerts(severity);
CREATE INDEX IF NOT EXISTS idx_security_alerts_status ON security_alerts(status);
CREATE INDEX IF NOT EXISTS idx_security_alerts_created_at ON security_alerts(created_at);

-- Indexes for bans table
CREATE INDEX IF NOT EXISTS idx_bans_user_id ON bans(user_id);
CREATE INDEX IF NOT EXISTS idx_bans_ip_address ON bans(ip_address);
CREATE INDEX IF NOT EXISTS idx_bans_is_active ON bans(is_active);

-- Indexes for user_activity_logs table
CREATE INDEX IF NOT EXISTS idx_user_activity_logs_user_id ON user_activity_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_user_activity_logs_created_at ON user_activity_logs(created_at);

-- Indexes for admin_actions table
CREATE INDEX IF NOT EXISTS idx_admin_actions_admin_id ON admin_actions(admin_id);
CREATE INDEX IF NOT EXISTS idx_admin_actions_created_at ON admin_actions(created_at);

-- ============================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ============================================================================

-- Enable RLS on security tables
ALTER TABLE security_alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE bans ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_activity_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE admin_actions ENABLE ROW LEVEL SECURITY;

-- RLS Policies for security_alerts table
-- Service role can manage all security alerts
DROP POLICY IF EXISTS "Service role can manage security_alerts" ON security_alerts;
CREATE POLICY "Service role can manage security_alerts" ON security_alerts 
    FOR ALL 
    USING (true) 
    WITH CHECK (true);

-- RLS Policies for bans table
-- Service role can manage all bans
DROP POLICY IF EXISTS "Service role can manage bans" ON bans;
CREATE POLICY "Service role can manage bans" ON bans 
    FOR ALL 
    USING (true) 
    WITH CHECK (true);

-- RLS Policies for user_activity_logs table
-- Service role can manage all activity logs
DROP POLICY IF EXISTS "Service role can manage user_activity_logs" ON user_activity_logs;
CREATE POLICY "Service role can manage user_activity_logs" ON user_activity_logs 
    FOR ALL 
    USING (true) 
    WITH CHECK (true);

-- RLS Policies for admin_actions table
-- Service role can manage all admin actions
DROP POLICY IF EXISTS "Service role can manage admin_actions" ON admin_actions;
CREATE POLICY "Service role can manage admin_actions" ON admin_actions 
    FOR ALL 
    USING (true) 
    WITH CHECK (true);

-- ============================================================================
-- TABLE COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE security_alerts IS 'Security alerts for detected attacks and suspicious activities';
COMMENT ON COLUMN security_alerts.alert_id IS 'Unique identifier for the security alert';
COMMENT ON COLUMN security_alerts.user_id IS 'User ID if attack was from authenticated user (NULL for guest)';
COMMENT ON COLUMN security_alerts.ip_address IS 'IP address of the attacker';
COMMENT ON COLUMN security_alerts.attack_type IS 'Type of attack: XSS, SQL_INJECTION, BRUTE_FORCE, etc.';
COMMENT ON COLUMN security_alerts.payload IS 'Sanitized attack payload (HTML escaped for safety)';
COMMENT ON COLUMN security_alerts.endpoint IS 'API endpoint that was attacked';
COMMENT ON COLUMN security_alerts.severity IS 'Severity level: LOW, MEDIUM, HIGH, CRITICAL';
COMMENT ON COLUMN security_alerts.risk_score IS 'Risk score from 0-100 calculated based on attack type and severity';
COMMENT ON COLUMN security_alerts.status IS 'Alert status: NEW, REVIEWED, BANNED, IGNORED, FALSE_POSITIVE';
COMMENT ON COLUMN security_alerts.user_agent IS 'User agent string from the request';
COMMENT ON COLUMN security_alerts.country_code IS 'Country code from GeoIP (if available)';
COMMENT ON COLUMN security_alerts.city IS 'City from GeoIP (if available)';
COMMENT ON COLUMN security_alerts.metadata IS 'Additional metadata about the attack (JSON)';
COMMENT ON COLUMN security_alerts.created_at IS 'Timestamp when alert was created';
COMMENT ON COLUMN security_alerts.reviewed_at IS 'Timestamp when alert was reviewed by admin';
COMMENT ON COLUMN security_alerts.reviewed_by IS 'User ID of admin who reviewed the alert';

COMMENT ON TABLE bans IS 'Banned users and IP addresses';
COMMENT ON COLUMN bans.ban_id IS 'Unique identifier for the ban record';
COMMENT ON COLUMN bans.user_id IS 'User ID if ban is for a specific user (NULL for IP-only bans)';
COMMENT ON COLUMN bans.ip_address IS 'IP address if ban is for a specific IP (NULL for user-only bans)';
COMMENT ON COLUMN bans.ban_type IS 'Type of ban: USER, IP, or BOTH';
COMMENT ON COLUMN bans.ban_reason IS 'Reason for the ban';
COMMENT ON COLUMN bans.ban_duration IS 'TEMPORARY or PERMANENT ban';
COMMENT ON COLUMN bans.expires_at IS 'Expiration timestamp for temporary bans (NULL for permanent)';
COMMENT ON COLUMN bans.created_at IS 'Timestamp when ban was created';
COMMENT ON COLUMN bans.created_by IS 'User ID of admin who created the ban';
COMMENT ON COLUMN bans.is_active IS 'Whether the ban is currently active';
COMMENT ON COLUMN bans.notes IS 'Additional notes about the ban';

COMMENT ON TABLE user_activity_logs IS 'Log of all user activities for audit trail and security analysis';
COMMENT ON COLUMN user_activity_logs.log_id IS 'Unique identifier for the activity log';
COMMENT ON COLUMN user_activity_logs.user_id IS 'User ID who performed the action';
COMMENT ON COLUMN user_activity_logs.action_type IS 'Type of action performed';
COMMENT ON COLUMN user_activity_logs.page_visited IS 'Page or route that was visited';
COMMENT ON COLUMN user_activity_logs.endpoint IS 'API endpoint that was called';
COMMENT ON COLUMN user_activity_logs.ip_address IS 'IP address of the user';
COMMENT ON COLUMN user_activity_logs.user_agent IS 'User agent string';
COMMENT ON COLUMN user_activity_logs.request_method IS 'HTTP method (GET, POST, etc.)';
COMMENT ON COLUMN user_activity_logs.request_body IS 'Request body data (JSON)';
COMMENT ON COLUMN user_activity_logs.response_status IS 'HTTP response status code';
COMMENT ON COLUMN user_activity_logs.metadata IS 'Additional metadata (JSON)';
COMMENT ON COLUMN user_activity_logs.created_at IS 'Timestamp when activity occurred';

COMMENT ON TABLE admin_actions IS 'Log of all admin actions for accountability and audit trail';
COMMENT ON COLUMN admin_actions.action_id IS 'Unique identifier for the admin action';
COMMENT ON COLUMN admin_actions.admin_id IS 'User ID of the admin who performed the action';
COMMENT ON COLUMN admin_actions.action_type IS 'Type of action (BAN, UNBAN, UPDATE_ALERT_STATUS, etc.)';
COMMENT ON COLUMN admin_actions.target_type IS 'Type of target: USER, IP, ALERT, SYSTEM';
COMMENT ON COLUMN admin_actions.target_id IS 'ID of the target (user_id, alert_id, etc.)';
COMMENT ON COLUMN admin_actions.details IS 'Additional details about the action (JSON)';
COMMENT ON COLUMN admin_actions.ip_address IS 'IP address from which action was performed';
COMMENT ON COLUMN admin_actions.created_at IS 'Timestamp when action was performed';

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================
-- Uncomment these to verify the schema was created correctly

-- Check if all security tables exist
-- SELECT table_name 
-- FROM information_schema.tables 
-- WHERE table_schema = 'public' 
--   AND table_name IN ('security_alerts', 'bans', 'user_activity_logs', 'admin_actions')
-- ORDER BY table_name;

-- Check security_alerts table structure
-- SELECT column_name, data_type, is_nullable, column_default 
-- FROM information_schema.columns 
-- WHERE table_name = 'security_alerts' 
-- ORDER BY ordinal_position;

-- Check all indexes on security tables
-- SELECT tablename, indexname, indexdef 
-- FROM pg_indexes 
-- WHERE schemaname = 'public' 
--   AND tablename IN ('security_alerts', 'bans', 'user_activity_logs', 'admin_actions')
-- ORDER BY tablename, indexname;

-- Check constraints on security_alerts
-- SELECT conname, contype, pg_get_constraintdef(oid) 
-- FROM pg_constraint 
-- WHERE conrelid = 'security_alerts'::regclass;

-- ============================================================================
-- END OF ADMIN SECURITY SCHEMA
-- ============================================================================

