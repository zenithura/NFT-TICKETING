-- NFT Ticketing Platform - Complete Database Schema
-- Compatible with server.py models

-- Drop existing tables if they exist (careful in production!)
DROP TABLE IF EXISTS scans CASCADE;
DROP TABLE IF EXISTS resales CASCADE;
DROP TABLE IF EXISTS orders CASCADE;
DROP TABLE IF EXISTS tickets CASCADE;
DROP TABLE IF EXISTS events CASCADE;
DROP TABLE IF EXISTS scanners CASCADE;
DROP TABLE IF EXISTS venues CASCADE;
DROP TABLE IF EXISTS wallets CASCADE;

-- Wallets table
CREATE TABLE wallets (
    wallet_id SERIAL PRIMARY KEY,
    address TEXT NOT NULL UNIQUE,
    balance DECIMAL(18, 2) DEFAULT 1000.0,
    allowlist_status BOOLEAN DEFAULT FALSE,
    verification_level INTEGER DEFAULT 0,
    blacklisted BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    last_activity TIMESTAMPTZ DEFAULT NOW()
);

-- Venues table
CREATE TABLE venues (
    venue_id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    location TEXT,
    city TEXT,
    country TEXT,
    capacity INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Events table
CREATE TABLE events (
    event_id SERIAL PRIMARY KEY,
    venue_id INTEGER NOT NULL REFERENCES venues(venue_id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    description TEXT,
    event_date TEXT NOT NULL,
    start_time TEXT DEFAULT '19:00:00',
    end_time TEXT DEFAULT '23:00:00',
    total_supply INTEGER NOT NULL,
    available_tickets INTEGER NOT NULL,
    base_price DECIMAL(18, 4) NOT NULL,
    max_resale_percentage DECIMAL(5, 2) DEFAULT 150.0,
    status TEXT DEFAULT 'UPCOMING' CHECK (status IN ('UPCOMING', 'ACTIVE', 'COMPLETED', 'CANCELLED')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tickets table
CREATE TABLE tickets (
    ticket_id SERIAL PRIMARY KEY,
    event_id INTEGER NOT NULL REFERENCES events(event_id) ON DELETE CASCADE,
    owner_wallet_id INTEGER NOT NULL REFERENCES wallets(wallet_id) ON DELETE CASCADE,
    token_id TEXT NOT NULL UNIQUE,
    nft_metadata_uri TEXT,
    seat_number TEXT,
    tier TEXT DEFAULT 'GENERAL' CHECK (tier IN ('GENERAL', 'VIP', 'PREMIUM')),
    purchase_price DECIMAL(18, 4) NOT NULL,
    status TEXT DEFAULT 'ACTIVE' CHECK (status IN ('ACTIVE', 'USED', 'TRANSFERRED', 'CANCELLED')),
    minted_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    last_transfer_at TIMESTAMPTZ
);

-- Orders table
CREATE TABLE orders (
    order_id SERIAL PRIMARY KEY,
    buyer_wallet_id INTEGER NOT NULL REFERENCES wallets(wallet_id) ON DELETE CASCADE,
    ticket_id INTEGER NOT NULL REFERENCES tickets(ticket_id) ON DELETE CASCADE,
    event_id INTEGER NOT NULL REFERENCES events(event_id) ON DELETE CASCADE,
    order_type TEXT DEFAULT 'PRIMARY' CHECK (order_type IN ('PRIMARY', 'RESALE')),
    price DECIMAL(18, 4) NOT NULL,
    platform_fee DECIMAL(18, 4) DEFAULT 0.0,
    total_amount DECIMAL(18, 4) NOT NULL,
    transaction_hash TEXT,
    status TEXT DEFAULT 'COMPLETED' CHECK (status IN ('PENDING', 'COMPLETED', 'FAILED', 'REFUNDED')),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    completed_at TIMESTAMPTZ
);

-- Resales table
CREATE TABLE resales (
    resale_id SERIAL PRIMARY KEY,
    ticket_id INTEGER NOT NULL REFERENCES tickets(ticket_id) ON DELETE CASCADE,
    seller_wallet_id INTEGER NOT NULL REFERENCES wallets(wallet_id) ON DELETE CASCADE,
    buyer_wallet_id INTEGER REFERENCES wallets(wallet_id) ON DELETE CASCADE,
    original_order_id INTEGER NOT NULL REFERENCES orders(order_id) ON DELETE CASCADE,
    listing_price DECIMAL(18, 4) NOT NULL,
    original_price DECIMAL(18, 4) NOT NULL,
    markup_percentage DECIMAL(8, 2),
    status TEXT DEFAULT 'LISTED' CHECK (status IN ('LISTED', 'SOLD', 'CANCELLED', 'EXPIRED')),
    listed_at TIMESTAMPTZ DEFAULT NOW(),
    sold_at TIMESTAMPTZ
);

-- Scanners table
CREATE TABLE scanners (
    scanner_id SERIAL PRIMARY KEY,
    venue_id INTEGER NOT NULL REFERENCES venues(venue_id) ON DELETE CASCADE,
    operator_name TEXT NOT NULL,
    operator_wallet TEXT,
    device_id TEXT NOT NULL UNIQUE,
    active BOOLEAN DEFAULT TRUE,
    registered_at TIMESTAMPTZ DEFAULT NOW()
);

-- Scans table
CREATE TABLE scans (
    scan_id SERIAL PRIMARY KEY,
    ticket_id INTEGER NOT NULL REFERENCES tickets(ticket_id) ON DELETE CASCADE,
    scanner_id INTEGER NOT NULL REFERENCES scanners(scanner_id) ON DELETE CASCADE,
    venue_id INTEGER NOT NULL REFERENCES venues(venue_id) ON DELETE CASCADE,
    event_id INTEGER NOT NULL REFERENCES events(event_id) ON DELETE CASCADE,
    scan_type TEXT DEFAULT 'ENTRY' CHECK (scan_type IN ('ENTRY', 'EXIT', 'VERIFICATION')),
    valid BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    scanned_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_wallets_address ON wallets(address);
CREATE INDEX idx_tickets_owner ON tickets(owner_wallet_id);
CREATE INDEX idx_tickets_event ON tickets(event_id);
CREATE INDEX idx_tickets_token ON tickets(token_id);
CREATE INDEX idx_tickets_status ON tickets(status);
CREATE INDEX idx_events_status ON events(status);
CREATE INDEX idx_events_venue ON events(venue_id);
CREATE INDEX idx_events_date ON events(event_date);
CREATE INDEX idx_orders_buyer ON orders(buyer_wallet_id);
CREATE INDEX idx_orders_ticket ON orders(ticket_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_resales_status ON resales(status);
CREATE INDEX idx_resales_ticket ON resales(ticket_id);
CREATE INDEX idx_resales_seller ON resales(seller_wallet_id);
CREATE INDEX idx_scans_ticket ON scans(ticket_id);
CREATE INDEX idx_scans_scanner ON scans(scanner_id);
CREATE INDEX idx_scans_venue ON scans(venue_id);

-- Enable Row Level Security (RLS)
ALTER TABLE wallets ENABLE ROW LEVEL SECURITY;
ALTER TABLE venues ENABLE ROW LEVEL SECURITY;
ALTER TABLE events ENABLE ROW LEVEL SECURITY;
ALTER TABLE tickets ENABLE ROW LEVEL SECURITY;
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE resales ENABLE ROW LEVEL SECURITY;
ALTER TABLE scanners ENABLE ROW LEVEL SECURITY;
ALTER TABLE scans ENABLE ROW LEVEL SECURITY;

-- Create policies for public access (using service role key)
CREATE POLICY "Allow all operations on wallets" ON wallets FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all operations on venues" ON venues FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all operations on events" ON events FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all operations on tickets" ON tickets FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all operations on orders" ON orders FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all operations on resales" ON resales FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all operations on scanners" ON scanners FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Allow all operations on scans" ON scans FOR ALL USING (true) WITH CHECK (true);

-- Trigger to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_venues_updated_at BEFORE UPDATE ON venues
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_events_updated_at BEFORE UPDATE ON events
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_tickets_updated_at BEFORE UPDATE ON tickets
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Trigger to update wallet last_activity
CREATE OR REPLACE FUNCTION update_wallet_activity()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE wallets SET last_activity = NOW() WHERE wallet_id = NEW.buyer_wallet_id;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_wallet_activity_on_order AFTER INSERT ON orders
    FOR EACH ROW EXECUTE FUNCTION update_wallet_activity();

-- Insert sample data for testing
INSERT INTO venues (name, location, city, country, capacity) VALUES
('Baku Crystal Hall', 'Bayil Area', 'Baku', 'Azerbaijan', 25000),
('Heydar Aliyev Palace', 'Winter Park', 'Baku', 'Azerbaijan', 3500),
('Baku Congress Center', 'White City', 'Baku', 'Azerbaijan', 4000);

COMMENT ON TABLE wallets IS 'User wallet information and balances';
COMMENT ON TABLE venues IS 'Event venues with capacity information';
COMMENT ON TABLE events IS 'Events with ticket information';
COMMENT ON TABLE tickets IS 'NFT tickets for events';
COMMENT ON TABLE orders IS 'Purchase orders for tickets';
COMMENT ON TABLE resales IS 'Secondary market resale listings';
COMMENT ON TABLE scanners IS 'Ticket scanning devices at venues';
COMMENT ON TABLE scans IS 'Scan records for ticket verification';
