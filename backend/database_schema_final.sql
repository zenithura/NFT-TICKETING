-- ============================================================================
-- NFT TICKETING PLATFORM - FINAL DATABASE SCHEMA
-- ============================================================================
-- This file matches the ACTUAL database structure in use
-- Run this entire file in your Supabase SQL Editor
-- ============================================================================
-- IMPORTANT: This schema uses owner_wallet_id (NOT owner_address) in tickets table
-- ============================================================================

-- ============================================================================
-- PART 1: CUSTOM TYPES/ENUMS
-- ============================================================================

-- Create custom types/enums for type safety
DO $$ BEGIN
    CREATE TYPE event_status AS ENUM ('UPCOMING', 'ACTIVE', 'COMPLETED', 'CANCELLED');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE ticket_status AS ENUM ('ACTIVE', 'USED', 'TRANSFERRED', 'REVOKED');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE ticket_tier AS ENUM ('GENERAL', 'VIP', 'PREMIUM');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE scan_type AS ENUM ('ENTRY', 'EXIT', 'VERIFICATION');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE activity_type AS ENUM ('PURCHASE', 'TRANSFER', 'RESALE', 'SCAN');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

DO $$ BEGIN
    CREATE TYPE action_taken AS ENUM ('ALLOWED', 'FLAGGED', 'BLOCKED');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- ============================================================================
-- PART 2: AUTHENTICATION TABLES
-- ============================================================================

-- Users table for authentication with role selection
CREATE TABLE IF NOT EXISTS users (
    user_id BIGSERIAL PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    username VARCHAR(100),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    role VARCHAR(20) NOT NULL DEFAULT 'BUYER' 
        CHECK (role IN ('BUYER', 'ORGANIZER', 'ADMIN', 'RESELLER', 'SCANNER')),
    is_email_verified BOOLEAN DEFAULT FALSE,
    verification_token VARCHAR(255),
    verification_token_expires TIMESTAMPTZ,
    reset_password_token VARCHAR(255),
    reset_password_expires TIMESTAMPTZ,
    is_active BOOLEAN DEFAULT TRUE,
    failed_login_attempts INTEGER DEFAULT 0,
    locked_until TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_login_at TIMESTAMPTZ,
    wallet_address VARCHAR(255)
);

-- Refresh tokens table for JWT token management
CREATE TABLE IF NOT EXISTS refresh_tokens (
    token_id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    token VARCHAR(500) NOT NULL UNIQUE,
    expires_at TIMESTAMPTZ NOT NULL,
    is_valid BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_used_at TIMESTAMPTZ,
    ip_address VARCHAR(45),
    user_agent TEXT
);

-- ============================================================================
-- PART 3: NFT TICKETING PLATFORM TABLES
-- ============================================================================

-- Wallets table (REQUIRED - tickets reference this table)
CREATE TABLE IF NOT EXISTS wallets (
    wallet_id BIGSERIAL PRIMARY KEY,
    address VARCHAR(255) NOT NULL UNIQUE,
    balance NUMERIC(18, 8) DEFAULT 0 CHECK (balance >= 0),
    allowlist_status BOOLEAN NOT NULL DEFAULT FALSE,
    verification_level INTEGER DEFAULT 0 CHECK (verification_level >= 0),
    verification_date TIMESTAMPTZ,
    blacklisted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_activity TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Venues table
CREATE TABLE IF NOT EXISTS venues (
    venue_id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    location VARCHAR(255),
    city VARCHAR(100),
    country VARCHAR(100),
    capacity INTEGER CHECK (capacity >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Events table
CREATE TABLE IF NOT EXISTS events (
    event_id BIGSERIAL PRIMARY KEY,
    venue_id BIGINT NOT NULL REFERENCES venues(venue_id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    event_date TIMESTAMPTZ NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    total_supply INTEGER CHECK (total_supply >= 0),
    available_tickets INTEGER CHECK (available_tickets >= 0),
    base_price NUMERIC(18, 8) CHECK (base_price >= 0),
    max_resale_percentage NUMERIC(5, 2) DEFAULT 150.00 CHECK (max_resale_percentage >= 0),
    status event_status NOT NULL DEFAULT 'UPCOMING',
    organizer_address VARCHAR(255),  -- Added for organizer tracking
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Tickets table (USES owner_wallet_id, NOT owner_address)
CREATE TABLE IF NOT EXISTS tickets (
    ticket_id BIGSERIAL PRIMARY KEY,
    event_id BIGINT NOT NULL REFERENCES events(event_id) ON DELETE CASCADE,
    owner_wallet_id BIGINT NOT NULL REFERENCES wallets(wallet_id) ON DELETE CASCADE,
    token_id VARCHAR(255) NOT NULL UNIQUE,
    nft_metadata_uri VARCHAR(500),
    seat_number VARCHAR(50),
    tier ticket_tier NOT NULL DEFAULT 'GENERAL',
    purchase_price NUMERIC(18, 8) CHECK (purchase_price >= 0),
    status ticket_status NOT NULL DEFAULT 'ACTIVE',
    minted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_transfer_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Orders table
CREATE TABLE IF NOT EXISTS orders (
    order_id BIGSERIAL PRIMARY KEY,
    buyer_wallet_id BIGINT NOT NULL REFERENCES wallets(wallet_id) ON DELETE CASCADE,
    ticket_id BIGINT NOT NULL REFERENCES tickets(ticket_id) ON DELETE CASCADE,
    event_id BIGINT NOT NULL REFERENCES events(event_id) ON DELETE CASCADE,
    order_type VARCHAR(50) CHECK (order_type IN ('PRIMARY', 'RESALE')),
    price NUMERIC(18, 8) NOT NULL,
    platform_fee NUMERIC(18, 8) DEFAULT 0.00,
    total_amount NUMERIC(18, 8) DEFAULT 0.00,
    transaction_hash VARCHAR(255),
    status VARCHAR(50) CHECK (status IN ('PENDING', 'COMPLETED', 'FAILED', 'REFUNDED')),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- Resales table
CREATE TABLE IF NOT EXISTS resales (
    resale_id BIGSERIAL PRIMARY KEY,
    ticket_id BIGINT NOT NULL REFERENCES tickets(ticket_id) ON DELETE CASCADE,
    seller_wallet_id BIGINT NOT NULL REFERENCES wallets(wallet_id) ON DELETE CASCADE,
    buyer_wallet_id BIGINT REFERENCES wallets(wallet_id) ON DELETE SET NULL,
    original_order_id BIGINT NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    listing_price NUMERIC(18, 8) NOT NULL,
    original_price NUMERIC(18, 8) NOT NULL,
    markup_percentage NUMERIC(5, 2) DEFAULT 0.00,
    status VARCHAR(50) CHECK (status IN ('LISTED', 'SOLD', 'CANCELLED', 'EXPIRED')),
    listed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    sold_at TIMESTAMPTZ,
    cancelled_at TIMESTAMPTZ
);

-- Payouts table
CREATE TABLE IF NOT EXISTS payouts (
    payout_id BIGSERIAL PRIMARY KEY,
    order_id BIGINT NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    recipient_wallet_id BIGINT NOT NULL REFERENCES wallets(wallet_id) ON DELETE CASCADE,
    recipient_type VARCHAR(50) CHECK (recipient_type IN ('ORGANIZER', 'PLATFORM', 'VENUE', 'SELLER')),
    amount NUMERIC(18, 8) NOT NULL CHECK (amount >= 0),
    currency VARCHAR(10) DEFAULT 'USD',
    status VARCHAR(50) CHECK (status IN ('PENDING', 'PROCESSED', 'FAILED')),
    transaction_hash VARCHAR(255),
    processed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Allowlist table
CREATE TABLE IF NOT EXISTS allowlist (
    allowlist_id BIGSERIAL PRIMARY KEY,
    wallet_id BIGINT NOT NULL REFERENCES wallets(wallet_id) ON DELETE CASCADE,
    event_id BIGINT NOT NULL REFERENCES events(event_id) ON DELETE CASCADE,
    verification_method VARCHAR(50) CHECK (verification_method IN ('KYC', 'WHITELIST', 'PRESALE', 'INVITATION')),
    verification_data JSONB,
    approved_by VARCHAR(255),
    approved_at TIMESTAMPTZ,
    expires_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Scanners table
CREATE TABLE IF NOT EXISTS scanners (
    scanner_id BIGSERIAL PRIMARY KEY,
    venue_id BIGINT NOT NULL REFERENCES venues(venue_id) ON DELETE CASCADE,
    operator_name VARCHAR(255) NOT NULL,
    operator_wallet VARCHAR(255),
    device_id VARCHAR(255) NOT NULL UNIQUE,
    active BOOLEAN NOT NULL DEFAULT TRUE,
    authorized_events JSONB,
    registered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_scan_at TIMESTAMPTZ
);

-- Scans table
CREATE TABLE IF NOT EXISTS scans (
    scan_id BIGSERIAL PRIMARY KEY,
    ticket_id BIGINT NOT NULL REFERENCES tickets(ticket_id) ON DELETE CASCADE,
    scanner_id BIGINT NOT NULL REFERENCES scanners(scanner_id) ON DELETE CASCADE,
    venue_id BIGINT NOT NULL REFERENCES venues(venue_id) ON DELETE CASCADE,
    event_id BIGINT NOT NULL REFERENCES events(event_id) ON DELETE CASCADE,
    scan_type scan_type NOT NULL,
    valid BOOLEAN NOT NULL DEFAULT TRUE,
    error_message VARCHAR(500),
    latitude NUMERIC(10, 8),
    longitude NUMERIC(11, 8),
    scanned_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Metrics table
CREATE TABLE IF NOT EXISTS metrics (
    metric_id BIGSERIAL PRIMARY KEY,
    event_id BIGINT NOT NULL REFERENCES events(event_id) ON DELETE CASCADE,
    metric_date DATE NOT NULL,
    total_sales INTEGER DEFAULT 0 CHECK (total_sales >= 0),
    total_revenue NUMERIC(18, 8) DEFAULT 0 CHECK (total_revenue >= 0),
    resale_count INTEGER DEFAULT 0 CHECK (resale_count >= 0),
    resale_revenue NUMERIC(18, 8) DEFAULT 0 CHECK (resale_revenue >= 0),
    average_resale_markup NUMERIC(5, 2) DEFAULT 0 CHECK (average_resale_markup >= 0),
    bot_attempts INTEGER DEFAULT 0 CHECK (bot_attempts >= 0),
    successful_scans INTEGER DEFAULT 0 CHECK (successful_scans >= 0),
    failed_scans INTEGER DEFAULT 0 CHECK (failed_scans >= 0),
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Bot Detection table
CREATE TABLE IF NOT EXISTS bot_detection (
    detection_id BIGSERIAL PRIMARY KEY,
    wallet_id BIGINT NOT NULL REFERENCES wallets(wallet_id) ON DELETE CASCADE,
    activity_type activity_type NOT NULL,
    risk_score NUMERIC(5, 2) CHECK (risk_score >= 0 AND risk_score <= 100),
    pattern_matched VARCHAR(255),
    action_taken action_taken NOT NULL DEFAULT 'ALLOWED',
    details JSONB,
    detected_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================================
-- PART 4: SECURITY & ADMIN TABLES
-- ============================================================================

-- Security Alerts table
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
-- PART 5: INDEXES FOR PERFORMANCE
-- ============================================================================

-- Authentication indexes
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_role ON users(role);
CREATE INDEX IF NOT EXISTS idx_users_verification_token ON users(verification_token);
CREATE INDEX IF NOT EXISTS idx_users_reset_token ON users(reset_password_token);
CREATE INDEX IF NOT EXISTS idx_users_wallet_address ON users(wallet_address);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user_id ON refresh_tokens(user_id);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_token ON refresh_tokens(token);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_expires ON refresh_tokens(expires_at);
CREATE INDEX IF NOT EXISTS idx_refresh_tokens_is_valid ON refresh_tokens(is_valid);

-- Platform indexes
CREATE INDEX IF NOT EXISTS idx_wallets_address ON wallets(address);
CREATE INDEX IF NOT EXISTS idx_wallets_blacklisted ON wallets(blacklisted);
CREATE INDEX IF NOT EXISTS idx_events_venue_id ON events(venue_id);
CREATE INDEX IF NOT EXISTS idx_events_status ON events(status);
CREATE INDEX IF NOT EXISTS idx_events_date ON events(event_date);
CREATE INDEX IF NOT EXISTS idx_events_organizer_address ON events(organizer_address);
CREATE INDEX IF NOT EXISTS idx_tickets_event_id ON tickets(event_id);
CREATE INDEX IF NOT EXISTS idx_tickets_owner_wallet_id ON tickets(owner_wallet_id);
CREATE INDEX IF NOT EXISTS idx_tickets_token_id ON tickets(token_id);
CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);
CREATE INDEX IF NOT EXISTS idx_orders_buyer_wallet_id ON orders(buyer_wallet_id);
CREATE INDEX IF NOT EXISTS idx_orders_event_id ON orders(event_id);
CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
CREATE INDEX IF NOT EXISTS idx_resales_ticket_id ON resales(ticket_id);
CREATE INDEX IF NOT EXISTS idx_resales_seller_wallet_id ON resales(seller_wallet_id);
CREATE INDEX IF NOT EXISTS idx_resales_status ON resales(status);
CREATE INDEX IF NOT EXISTS idx_scans_ticket_id ON scans(ticket_id);
CREATE INDEX IF NOT EXISTS idx_scans_scanner_id ON scans(scanner_id);
CREATE INDEX IF NOT EXISTS idx_scans_event_id ON scans(event_id);
CREATE INDEX IF NOT EXISTS idx_scans_scanned_at ON scans(scanned_at);
CREATE INDEX IF NOT EXISTS idx_scanners_venue_id ON scanners(venue_id);
CREATE INDEX IF NOT EXISTS idx_scanners_device_id ON scanners(device_id);
CREATE INDEX IF NOT EXISTS idx_allowlist_wallet_id ON allowlist(wallet_id);
CREATE INDEX IF NOT EXISTS idx_allowlist_event_id ON allowlist(event_id);
CREATE INDEX IF NOT EXISTS idx_bot_detection_wallet_id ON bot_detection(wallet_id);
CREATE INDEX IF NOT EXISTS idx_bot_detection_detected_at ON bot_detection(detected_at);
CREATE INDEX IF NOT EXISTS idx_metrics_event_id ON metrics(event_id);
CREATE INDEX IF NOT EXISTS idx_metrics_date ON metrics(metric_date);
CREATE INDEX IF NOT EXISTS idx_payouts_order_id ON payouts(order_id);
CREATE INDEX IF NOT EXISTS idx_payouts_status ON payouts(status);

-- Security table indexes
CREATE INDEX IF NOT EXISTS idx_security_alerts_user_id ON security_alerts(user_id);
CREATE INDEX IF NOT EXISTS idx_security_alerts_ip_address ON security_alerts(ip_address);
CREATE INDEX IF NOT EXISTS idx_security_alerts_attack_type ON security_alerts(attack_type);
CREATE INDEX IF NOT EXISTS idx_security_alerts_severity ON security_alerts(severity);
CREATE INDEX IF NOT EXISTS idx_security_alerts_status ON security_alerts(status);
CREATE INDEX IF NOT EXISTS idx_security_alerts_created_at ON security_alerts(created_at);
CREATE INDEX IF NOT EXISTS idx_bans_user_id ON bans(user_id);
CREATE INDEX IF NOT EXISTS idx_bans_ip_address ON bans(ip_address);
CREATE INDEX IF NOT EXISTS idx_bans_is_active ON bans(is_active);
CREATE INDEX IF NOT EXISTS idx_user_activity_logs_user_id ON user_activity_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_user_activity_logs_created_at ON user_activity_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_admin_actions_admin_id ON admin_actions(admin_id);
CREATE INDEX IF NOT EXISTS idx_admin_actions_created_at ON admin_actions(created_at);

-- ============================================================================
-- PART 6: FUNCTIONS AND TRIGGERS
-- ============================================================================

-- Function to auto-update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to auto-update updated_at on users table
DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger to auto-update updated_at on venues table
DROP TRIGGER IF EXISTS update_venues_updated_at ON venues;
CREATE TRIGGER update_venues_updated_at 
    BEFORE UPDATE ON venues
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger to auto-update updated_at on events table
DROP TRIGGER IF EXISTS update_events_updated_at ON events;
CREATE TRIGGER update_events_updated_at 
    BEFORE UPDATE ON events
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger to auto-update updated_at on tickets table
DROP TRIGGER IF EXISTS update_tickets_updated_at ON tickets;
CREATE TRIGGER update_tickets_updated_at 
    BEFORE UPDATE ON tickets
    FOR EACH ROW 
    EXECUTE FUNCTION update_updated_at_column();

-- Function to update wallet last_activity
CREATE OR REPLACE FUNCTION update_wallet_activity()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE wallets SET last_activity = NOW() WHERE wallet_id = NEW.buyer_wallet_id;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to update wallet activity on order creation
DROP TRIGGER IF EXISTS update_wallet_activity_on_order ON orders;
CREATE TRIGGER update_wallet_activity_on_order 
    AFTER INSERT ON orders
    FOR EACH ROW 
    EXECUTE FUNCTION update_wallet_activity();

-- ============================================================================
-- PART 7: ROW LEVEL SECURITY (RLS)
-- ============================================================================

-- Enable RLS on all tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE refresh_tokens ENABLE ROW LEVEL SECURITY;
ALTER TABLE wallets ENABLE ROW LEVEL SECURITY;
ALTER TABLE venues ENABLE ROW LEVEL SECURITY;
ALTER TABLE events ENABLE ROW LEVEL SECURITY;
ALTER TABLE tickets ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE resales ENABLE ROW LEVEL SECURITY;
ALTER TABLE scanners ENABLE ROW LEVEL SECURITY;
ALTER TABLE scans ENABLE ROW LEVEL SECURITY;
ALTER TABLE allowlist ENABLE ROW LEVEL SECURITY;
ALTER TABLE metrics ENABLE ROW LEVEL SECURITY;
ALTER TABLE bot_detection ENABLE ROW LEVEL SECURITY;
ALTER TABLE payouts ENABLE ROW LEVEL SECURITY;
ALTER TABLE security_alerts ENABLE ROW LEVEL SECURITY;
ALTER TABLE bans ENABLE ROW LEVEL SECURITY;
ALTER TABLE user_activity_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE admin_actions ENABLE ROW LEVEL SECURITY;

-- RLS Policies for all tables (Service role can manage everything)
-- Note: In production, use more restrictive policies

DROP POLICY IF EXISTS "Service role can manage users" ON users;
CREATE POLICY "Service role can manage users" ON users 
    FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Service role can manage refresh_tokens" ON refresh_tokens;
CREATE POLICY "Service role can manage refresh_tokens" ON refresh_tokens 
    FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Allow all operations on wallets" ON wallets;
CREATE POLICY "Allow all operations on wallets" ON wallets 
    FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Allow all operations on venues" ON venues;
CREATE POLICY "Allow all operations on venues" ON venues 
    FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Allow all operations on events" ON events;
CREATE POLICY "Allow all operations on events" ON events 
    FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Allow all operations on tickets" ON tickets;
CREATE POLICY "Allow all operations on tickets" ON tickets 
    FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Allow all operations on orders" ON orders;
CREATE POLICY "Allow all operations on orders" ON orders 
    FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Allow all operations on resales" ON resales;
CREATE POLICY "Allow all operations on resales" ON resales 
    FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Allow all operations on scanners" ON scanners;
CREATE POLICY "Allow all operations on scanners" ON scanners 
    FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Allow all operations on scans" ON scans;
CREATE POLICY "Allow all operations on scans" ON scans 
    FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Allow all operations on allowlist" ON allowlist;
CREATE POLICY "Allow all operations on allowlist" ON allowlist 
    FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Allow all operations on metrics" ON metrics;
CREATE POLICY "Allow all operations on metrics" ON metrics 
    FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Allow all operations on bot_detection" ON bot_detection;
CREATE POLICY "Allow all operations on bot_detection" ON bot_detection 
    FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Allow all operations on payouts" ON payouts;
CREATE POLICY "Allow all operations on payouts" ON payouts 
    FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Service role can manage security_alerts" ON security_alerts;
CREATE POLICY "Service role can manage security_alerts" ON security_alerts 
    FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Service role can manage bans" ON bans;
CREATE POLICY "Service role can manage bans" ON bans 
    FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Service role can manage user_activity_logs" ON user_activity_logs;
CREATE POLICY "Service role can manage user_activity_logs" ON user_activity_logs 
    FOR ALL USING (true) WITH CHECK (true);

DROP POLICY IF EXISTS "Service role can manage admin_actions" ON admin_actions;
CREATE POLICY "Service role can manage admin_actions" ON admin_actions 
    FOR ALL USING (true) WITH CHECK (true);

-- ============================================================================
-- VERIFICATION QUERIES (Run these after schema creation to verify)
-- ============================================================================

-- Check if all tables exist
-- SELECT table_name 
-- FROM information_schema.tables 
-- WHERE table_schema = 'public' 
--   AND table_type = 'BASE TABLE'
-- ORDER BY table_name;

-- Check tickets table structure (should show owner_wallet_id, NOT owner_address)
-- SELECT column_name, data_type, is_nullable, column_default 
-- FROM information_schema.columns 
-- WHERE table_name = 'tickets' 
-- ORDER BY ordinal_position;

-- ============================================================================
-- END OF SCHEMA
-- ============================================================================
-- 
-- IMPORTANT NOTES:
-- 1. Tickets table uses owner_wallet_id (BIGINT) referencing wallets(wallet_id)
-- 2. Tickets table does NOT have owner_address column
-- 3. To get owner address for a ticket, join with wallets table:
--    SELECT t.*, w.address as owner_address 
--    FROM tickets t 
--    JOIN wallets w ON t.owner_wallet_id = w.wallet_id;
-- 4. Events table includes organizer_address field for organizer tracking
-- 5. All foreign keys use CASCADE delete for data integrity
-- ============================================================================

