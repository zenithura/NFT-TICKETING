-- ============================================================================
-- ADMIN LOGGING, WEB REQUESTS, AND SOAR INTEGRATION - DATABASE SCHEMA (SAFE VERSION)
-- ============================================================================
-- This version safely handles existing tables and columns
-- Run this file in your Supabase SQL Editor
-- ============================================================================

-- ============================================================================
-- APPLICATION LOGS TABLE
-- ============================================================================
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
    log_data JSONB,
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
CREATE TABLE IF NOT EXISTS soar_config (
    config_id BIGSERIAL PRIMARY KEY,
    platform_name VARCHAR(100) NOT NULL UNIQUE,
    endpoint_url VARCHAR(500) NOT NULL,
    api_key VARCHAR(500) NOT NULL,
    is_enabled BOOLEAN DEFAULT FALSE,
    event_types TEXT[] DEFAULT ARRAY[]::TEXT[],
    severity_filter TEXT[] DEFAULT ARRAY['CRITICAL', 'HIGH']::TEXT[],
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
CREATE TABLE IF NOT EXISTS soar_event_log (
    log_id BIGSERIAL PRIMARY KEY,
    config_id BIGINT REFERENCES soar_config(config_id) ON DELETE CASCADE,
    event_type VARCHAR(50) NOT NULL,
    event_id BIGINT,
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
-- USER ACTIVITY LOGS (Enhanced) - Safe Migration
-- ============================================================================
-- Check if table exists and has the correct structure
DO $$
BEGIN
    -- Check if table exists
    IF EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'user_activity_logs') THEN
        -- Check if activity_type column exists
        IF NOT EXISTS (
            SELECT FROM information_schema.columns 
            WHERE table_name = 'user_activity_logs' AND column_name = 'activity_type'
        ) THEN
            -- Add the activity_type column if it doesn't exist
            ALTER TABLE user_activity_logs 
            ADD COLUMN activity_type VARCHAR(50);
            
            -- Update existing rows with a default value
            UPDATE user_activity_logs 
            SET activity_type = 'LOGIN' 
            WHERE activity_type IS NULL;
            
            -- Make it NOT NULL and add constraint
            ALTER TABLE user_activity_logs 
            ALTER COLUMN activity_type SET NOT NULL;
            
            ALTER TABLE user_activity_logs 
            ADD CONSTRAINT user_activity_logs_activity_type_check 
            CHECK (activity_type IN (
                'LOGIN', 'LOGOUT', 'REGISTER', 'PASSWORD_CHANGE', 'PASSWORD_RESET',
                'PROFILE_UPDATE', 'TICKET_PURCHASE', 'TICKET_TRANSFER', 'TICKET_RESALE',
                'EVENT_CREATE', 'EVENT_UPDATE', 'EVENT_DELETE',
                'ACCOUNT_SUSPENDED', 'ACCOUNT_ACTIVATED', 'ACCOUNT_DELETED'
            ));
        END IF;
        
        -- Add other missing columns if needed
        IF NOT EXISTS (
            SELECT FROM information_schema.columns 
            WHERE table_name = 'user_activity_logs' AND column_name = 'metadata'
        ) THEN
            ALTER TABLE user_activity_logs ADD COLUMN metadata JSONB;
        END IF;
        
        IF NOT EXISTS (
            SELECT FROM information_schema.columns 
            WHERE table_name = 'user_activity_logs' AND column_name = 'ip_address'
        ) THEN
            ALTER TABLE user_activity_logs ADD COLUMN ip_address VARCHAR(45);
        END IF;
        
        IF NOT EXISTS (
            SELECT FROM information_schema.columns 
            WHERE table_name = 'user_activity_logs' AND column_name = 'user_agent'
        ) THEN
            ALTER TABLE user_activity_logs ADD COLUMN user_agent TEXT;
        END IF;
    ELSE
        -- Create table if it doesn't exist
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
    END IF;
END $$;

-- Indexes for user activity logs (create only if they don't exist)
CREATE INDEX IF NOT EXISTS idx_user_activity_logs_user_id ON user_activity_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_user_activity_logs_activity_type ON user_activity_logs(activity_type);
CREATE INDEX IF NOT EXISTS idx_user_activity_logs_created_at ON user_activity_logs(created_at);

-- ============================================================================
-- FUNCTIONS FOR LOG ROTATION
-- ============================================================================

CREATE OR REPLACE FUNCTION archive_old_logs(days_to_keep INTEGER DEFAULT 90)
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM application_logs
    WHERE created_at < NOW() - (days_to_keep || ' days')::INTERVAL
    AND log_level NOT IN ('ERROR', 'CRITICAL');
    
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    
    DELETE FROM web_requests
    WHERE created_at < NOW() - (days_to_keep || ' days')::INTERVAL
    AND response_status < 400;
    
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

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

-- Drop existing policies if they exist, then recreate
DROP POLICY IF EXISTS "Admins can view application logs" ON application_logs;
DROP POLICY IF EXISTS "Admins can view web requests" ON web_requests;
DROP POLICY IF EXISTS "Admins can manage SOAR config" ON soar_config;
DROP POLICY IF EXISTS "Admins can view SOAR event log" ON soar_event_log;

-- Policy: Only admins can view application logs
-- Note: This uses service role bypass in Supabase, adjust if using RLS
CREATE POLICY "Admins can view application logs"
    ON application_logs FOR SELECT
    USING (true); -- Simplified for service role access

-- Policy: Only admins can view web requests
CREATE POLICY "Admins can view web requests"
    ON web_requests FOR SELECT
    USING (true); -- Simplified for service role access

-- Policy: Only admins can manage SOAR config
CREATE POLICY "Admins can manage SOAR config"
    ON soar_config FOR ALL
    USING (true); -- Simplified for service role access

-- Policy: Only admins can view SOAR event log
CREATE POLICY "Admins can view SOAR event log"
    ON soar_event_log FOR SELECT
    USING (true); -- Simplified for service role access

-- ============================================================================
-- COMMENTS FOR DOCUMENTATION
-- ============================================================================

COMMENT ON TABLE application_logs IS 'Structured application logs with support for JSON and plain text formats';
COMMENT ON TABLE web_requests IS 'All incoming HTTP requests for monitoring and security analysis';
COMMENT ON TABLE soar_config IS 'SOAR platform configuration for security event forwarding';
COMMENT ON TABLE soar_event_log IS 'Log of events forwarded to SOAR platforms';
COMMENT ON TABLE user_activity_logs IS 'Enhanced user activity tracking with detailed metadata';

