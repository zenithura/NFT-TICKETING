-- NFT Ticketing Platform - Supabase Migration
-- This migration creates all necessary tables with proper constraints and relationships

-- Create custom types/enums
CREATE TYPE event_status AS ENUM ('UPCOMING', 'ACTIVE', 'COMPLETED', 'CANCELLED');
CREATE TYPE ticket_status AS ENUM ('ACTIVE', 'USED', 'TRANSFERRED', 'REVOKED');
CREATE TYPE ticket_tier AS ENUM ('GENERAL', 'VIP', 'PREMIUM');
CREATE TYPE scan_type AS ENUM ('ENTRY', 'EXIT', 'VERIFICATION');
CREATE TYPE activity_type AS ENUM ('PURCHASE', 'TRANSFER', 'RESALE', 'SCAN');
CREATE TYPE action_taken AS ENUM ('ALLOWED', 'FLAGGED', 'BLOCKED');

-- Wallets table
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
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Tickets table
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

-- Create indexes for performance
CREATE INDEX idx_wallets_address ON wallets(address);
CREATE INDEX idx_wallets_blacklisted ON wallets(blacklisted);
CREATE INDEX idx_events_venue_id ON events(venue_id);
CREATE INDEX idx_events_status ON events(status);
CREATE INDEX idx_events_date ON events(event_date);
CREATE INDEX idx_tickets_event_id ON tickets(event_id);
CREATE INDEX idx_tickets_owner_wallet_id ON tickets(owner_wallet_id);
CREATE INDEX idx_tickets_token_id ON tickets(token_id);
CREATE INDEX idx_tickets_status ON tickets(status);
CREATE INDEX idx_orders_buyer_wallet_id ON orders(buyer_wallet_id);
CREATE INDEX idx_orders_event_id ON orders(event_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_resales_ticket_id ON resales(ticket_id);
CREATE INDEX idx_resales_seller_wallet_id ON resales(seller_wallet_id);
CREATE INDEX idx_resales_status ON resales(status);
CREATE INDEX idx_scans_ticket_id ON scans(ticket_id);
CREATE INDEX idx_scans_scanner_id ON scans(scanner_id);
CREATE INDEX idx_scans_event_id ON scans(event_id);
CREATE INDEX idx_scans_scanned_at ON scans(scanned_at);
CREATE INDEX idx_scanners_venue_id ON scanners(venue_id);
CREATE INDEX idx_scanners_device_id ON scanners(device_id);
CREATE INDEX idx_allowlist_wallet_id ON allowlist(wallet_id);
CREATE INDEX idx_allowlist_event_id ON allowlist(event_id);
CREATE INDEX idx_bot_detection_wallet_id ON bot_detection(wallet_id);
CREATE INDEX idx_bot_detection_detected_at ON bot_detection(detected_at);
CREATE INDEX idx_metrics_event_id ON metrics(event_id);
CREATE INDEX idx_metrics_date ON metrics(metric_date);
CREATE INDEX idx_payouts_order_id ON payouts(order_id);
CREATE INDEX idx_payouts_status ON payouts(status);

-- Enable Row Level Security
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

-- Create basic RLS policies (allow all for now - adjust based on your auth requirements)
CREATE POLICY "Allow all operations on wallets" ON wallets FOR ALL USING (true);
CREATE POLICY "Allow all operations on venues" ON venues FOR ALL USING (true);
CREATE POLICY "Allow all operations on events" ON events FOR ALL USING (true);
CREATE POLICY "Allow all operations on tickets" ON tickets FOR ALL USING (true);
CREATE POLICY "Allow all operations on orders" ON orders FOR ALL USING (true);
CREATE POLICY "Allow all operations on resales" ON resales FOR ALL USING (true);
CREATE POLICY "Allow all operations on scanners" ON scanners FOR ALL USING (true);
CREATE POLICY "Allow all operations on scans" ON scans FOR ALL USING (true);
CREATE POLICY "Allow all operations on allowlist" ON allowlist FOR ALL USING (true);
CREATE POLICY "Allow all operations on metrics" ON metrics FOR ALL USING (true);
CREATE POLICY "Allow all operations on bot_detection" ON bot_detection FOR ALL USING (true);
CREATE POLICY "Allow all operations on payouts" ON payouts FOR ALL USING (true);
