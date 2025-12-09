-- ============================================================================
-- ADMIN LOGGING, WEB REQUESTS, AND SOAR INTEGRATION - DATABASE SCHEMA
-- ============================================================================
-- This file contains tables for:
-- 1. Application logs (structured logging)
-- 2. Web requests (HTTP request logging)
-- 3. SOAR configuration and event forwarding
-- ============================================================================
-- Run this file in your Supabase SQL Editor
-- ============================================================================

-- ============================================================================
-- APPLICATION LOGS TABLE
-- ============================================================================
-- Stores structured application logs with support for JSON and plain text
CREATE TABLE IF NOT EXISTS application_logs (
    log_id BIGSERIAL PRIMARY KEY,
    log_level VARCHAR(20) NOT NULL CHECK (log_level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL')),
    log_type VARCHAR(50) NOT NULL CHECK (log_type IN (
        'AUTH_LOGIN', 'AUTH_LOGOUT', 'AUTH_FAILED_LOGIN', 'AUTH_PASSWORD_CHANGE',
        'HTTP_REQUEST', 'ADMIN_ACTION', 'SYSTEM_WARNING', 'SYSTEM_ERROR',
        'USER_CREATED', 'USER_DELETED', 'USER_SUSPENDED', 'USER_ACTIVATED',
        'ALERT_CLEARED', 'ALERT_EXPORTED', 'DATA_EXPORTED'
    )),
    message TEXT NOT NULL,
    user_id BIGINT REFERENCES users(user_id) ON DELETE SET NULL,
    username VARCHAR(100),
    ip_address VARCHAR(45),
    user_agent TEXT,
    endpoint VARCHAR(500),
    http_method VARCHAR(10),
    status_code INTEGER,
    request_payload JSONB,
    response_payload JSONB,
    metadata JSONB,
    log_data JSONB, -- For structured JSON logs
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for fast querying
CREATE INDEX IF NOT EXISTS idx_application_logs_log_type ON application_logs(log_type);
CREATE INDEX IF NOT EXISTS idx_application_logs_log_level ON application_logs(log_level);
CREATE INDEX IF NOT EXISTS idx_application_logs_user_id ON application_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_application_logs_created_at ON application_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_application_logs_ip_address ON application_logs(ip_address);

-- ============================================================================
-- WEB REQUESTS TABLE
-- ============================================================================
-- Stores all incoming HTTP requests for monitoring and analysis
CREATE TABLE IF NOT EXISTS web_requests (
    request_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT REFERENCES users(user_id) ON DELETE SET NULL,
    username VARCHAR(100),
    ip_address VARCHAR(45) NOT NULL,
    http_method VARCHAR(10) NOT NULL,
    path VARCHAR(500) NOT NULL,
    endpoint VARCHAR(500),
    query_params JSONB,
    request_headers JSONB,
    request_body JSONB,
    response_status INTEGER,
    response_headers JSONB,
    response_body JSONB,
    response_time_ms INTEGER,
    user_agent TEXT,
    referer VARCHAR(500),
    country_code VARCHAR(2),
    city VARCHAR(100),
    is_authenticated BOOLEAN DEFAULT FALSE,
    session_id VARCHAR(255),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for fast querying and filtering
CREATE INDEX IF NOT EXISTS idx_web_requests_user_id ON web_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_web_requests_ip_address ON web_requests(ip_address);
CREATE INDEX IF NOT EXISTS idx_web_requests_http_method ON web_requests(http_method);
CREATE INDEX IF NOT EXISTS idx_web_requests_path ON web_requests(path);
CREATE INDEX IF NOT EXISTS idx_web_requests_endpoint ON web_requests(endpoint);
CREATE INDEX IF NOT EXISTS idx_web_requests_created_at ON web_requests(created_at);
CREATE INDEX IF NOT EXISTS idx_web_requests_status_code ON web_requests(response_status);
CREATE INDEX IF NOT EXISTS idx_web_requests_username ON web_requests(username);

-- Composite index for common queries
CREATE INDEX IF NOT EXISTS idx_web_requests_user_date ON web_requests(user_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_web_requests_ip_date ON web_requests(ip_address, created_at DESC);

-- ============================================================================
-- SOAR CONFIGURATION TABLE
-- ============================================================================
-- Stores SOAR platform configuration and integration settings
CREATE TABLE IF NOT EXISTS soar_config (
    config_id BIGSERIAL PRIMARY KEY,
    platform_name VARCHAR(100) NOT NULL UNIQUE, -- e.g., 'Splunk SOAR', 'Cortex XSOAR', 'IBM Resilient'
    endpoint_url VARCHAR(500) NOT NULL,
    api_key VARCHAR(500) NOT NULL,
    is_enabled BOOLEAN DEFAULT FALSE,
    event_types TEXT[] DEFAULT ARRAY[]::TEXT[], -- Array of event types to forward
    severity_filter TEXT[] DEFAULT ARRAY['CRITICAL', 'HIGH']::TEXT[], -- Only forward these severities
    retry_count INTEGER DEFAULT 3,
    timeout_seconds INTEGER DEFAULT 30,
    verify_ssl BOOLEAN DEFAULT TRUE,
    custom_headers JSONB DEFAULT '{}'::JSONB,
    webhook_secret VARCHAR(255),
    last_successful_sync TIMESTAMPTZ,
    last_failed_sync TIMESTAMPTZ,
    failure_count INTEGER DEFAULT 0,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- SOAR EVENT FORWARDING LOG
-- ============================================================================
-- Tracks events forwarded to SOAR platforms
CREATE TABLE IF NOT EXISTS soar_event_log (
    log_id BIGSERIAL PRIMARY KEY,
    config_id BIGINT REFERENCES soar_config(config_id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    event_id BIGINT, -- Reference to security_alerts.alert_id or application_logs.log_id
    event_data JSONB NOT NULL,
    severity VARCHAR(20),
    status VARCHAR(20) NOT NULL CHECK (status IN ('PENDING', 'SENT', 'FAILED', 'RETRYING')),
    response_status INTEGER,
    response_body JSONB,
    error_message TEXT,
    retry_count INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    sent_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ
);

-- Indexes for SOAR event log
CREATE INDEX IF NOT EXISTS idx_soar_event_log_config_id ON soar_event_log(config_id);
CREATE INDEX IF NOT EXISTS idx_soar_event_log_status ON soar_event_log(status);
CREATE INDEX IF NOT EXISTS idx_soar_event_log_event_type ON soar_event_log(event_type);
CREATE INDEX IF NOT EXISTS idx_soar_event_log_created_at ON soar_event_log(created_at);

-- ============================================================================
-- USER ACTIVITY LOGS (Enhanced)
-- ============================================================================
-- Enhanced user activity logs with more detail
-- Drop existing table if it has wrong structure, then recreate
DROP TABLE IF EXISTS user_activity_logs CASCADE;

CREATE TABLE user_activity_logs (
    activity_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    activity_type VARCHAR(50) NOT NULL CHECK (activity_type IN (
        'LOGIN', 'LOGOUT', 'REGISTER', 'PASSWORD_CHANGE', 'PASSWORD_RESET',
        'PROFILE_UPDATE', 'TICKET_PURCHASE', 'TICKET_TRANSFER', 'TICKET_RESALE',
        'EVENT_CREATE', 'EVENT_UPDATE', 'EVENT_DELETE',
        'ACCOUNT_SUSPENDED', 'ACCOUNT_ACTIVATED', 'ACCOUNT_DELETED'
    )),
    description TEXT,
    ip_address VARCHAR(45),
    user_agent TEXT,
    metadata JSONB,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Indexes for user activity logs
CREATE INDEX IF NOT EXISTS idx_user_activity_logs_user_id ON user_activity_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_user_activity_logs_activity_type ON user_activity_logs(activity_type);
CREATE INDEX IF NOT EXISTS idx_user_activity_logs_created_at ON user_activity_logs(created_at);

-- ============================================================================
-- FUNCTIONS FOR LOG ROTATION
-- ============================================================================

-- Function to archive old logs (older than specified days)
CREATE OR REPLACE FUNCTION archive_old_logs(days_to_keep INTEGER DEFAULT 90)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    -- Archive application logs older than specified days
    DELETE FROM application_logs
    WHERE created_at < NOW() - (days_to_keep || ' days')::INTERVAL
    AND log_level NOT IN ('ERROR', 'CRITICAL'); -- Keep errors and critical logs longer
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    -- Archive web requests older than specified days
    DELETE FROM web_requests
    WHERE created_at < NOW() - (days_to_keep || ' days')::INTERVAL
    AND response_status < 400; -- Keep error requests longer
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- Function to get log statistics
CREATE OR REPLACE FUNCTION get_log_statistics(
    start_date TIMESTAMPTZ DEFAULT NOW() - INTERVAL '24 hours',
    end_date TIMESTAMPTZ DEFAULT NOW()
)
RETURNS TABLE (
    log_type VARCHAR,
    log_level VARCHAR,
    count BIGINT
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        al.log_type,
        al.log_level,
        COUNT(*)::BIGINT as count
    FROM application_logs al
    WHERE al.created_at BETWEEN start_date AND end_date
    GROUP BY al.log_type, al.log_level
    ORDER BY count DESC;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- ROW LEVEL SECURITY (RLS) POLICIES
-- ============================================================================

-- Enable RLS on sensitive tables
ALTER TABLE application_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE web_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE soar_config ENABLE ROW LEVEL SECURITY;
ALTER TABLE soar_event_log ENABLE ROW LEVEL SECURITY;

-- Policy: Only admins can view application logs
CREATE POLICY "Admins can view application logs"
    ON application_logs FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM users
            WHERE users.user_id = auth.uid()
            AND users.role = 'ADMIN'
        )
    );

-- Policy: Only admins can view web requests
CREATE POLICY "Admins can view web requests"
    ON web_requests FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM users
            WHERE users.user_id = auth.uid()
            AND users.role = 'ADMIN'
        )
    );

-- Policy: Only admins can manage SOAR config
CREATE POLICY "Admins can manage SOAR config"
    ON soar_config FOR ALL
    USING (
        EXISTS (
            SELECT 1 FROM users
            WHERE users.user_id = auth.uid()
            AND users.role = 'ADMIN'
        )
    );

-- Policy: Only admins can view SOAR event log
CREATE POLICY "Admins can view SOAR event log"
    ON soar_event_log FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM users
            WHERE users.user_id = auth.uid()
            AND users.role = 'ADMIN'
        )
    );

-- ============================================================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE application_logs IS 'Structured application logs with support for JSON and plain text formats';
COMMENT ON TABLE web_requests IS 'All incoming HTTP requests for monitoring and security analysis';
COMMENT ON TABLE soar_config IS 'SOAR platform configuration for security event forwarding';
COMMENT ON TABLE soar_event_log IS 'Log of events forwarded to SOAR platforms';
COMMENT ON TABLE user_activity_logs IS 'Enhanced user activity tracking with detailed metadata';

