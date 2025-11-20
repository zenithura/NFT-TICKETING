-- NFT Ticketing Platform Supabase Schema

-- Wallets table
CREATE TABLE IF NOT EXISTS wallets (
    address TEXT PRIMARY KEY,
    balance DECIMAL(18, 2) DEFAULT 1000.0,
    allowlist_status BOOLEAN DEFAULT FALSE,
    owned_tickets TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Venues table
CREATE TABLE IF NOT EXISTS venues (
    venue_id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    location TEXT NOT NULL,
    capacity INTEGER NOT NULL,
    active_scanners TEXT[] DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Events table
CREATE TABLE IF NOT EXISTS events (
    event_id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    venue_id UUID REFERENCES venues(venue_id),
    date TEXT NOT NULL,
    total_supply INTEGER NOT NULL,
    price DECIMAL(18, 4) NOT NULL,
    status TEXT DEFAULT 'ACTIVE',
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tickets table
CREATE TABLE IF NOT EXISTS tickets (
    token_id UUID PRIMARY KEY,
    event_id UUID REFERENCES events(event_id),
    owner TEXT NOT NULL,
    minted_at TIMESTAMPTZ DEFAULT NOW(),
    status TEXT DEFAULT 'MINTED',
    metadata JSONB DEFAULT '{}'
);

-- Orders table
CREATE TABLE IF NOT EXISTS orders (
    order_id UUID PRIMARY KEY,
    buyer_wallet TEXT NOT NULL,
    ticket_id UUID REFERENCES tickets(token_id),
    price DECIMAL(18, 4) NOT NULL,
    status TEXT DEFAULT 'COMPLETED',
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Resales table
CREATE TABLE IF NOT EXISTS resales (
    resale_id UUID PRIMARY KEY,
    ticket_id UUID REFERENCES tickets(token_id),
    seller_wallet TEXT NOT NULL,
    buyer_wallet TEXT,
    price DECIMAL(18, 4) NOT NULL,
    status TEXT DEFAULT 'LISTED',
    listed_at TIMESTAMPTZ DEFAULT NOW()
);

-- Scanners table
CREATE TABLE IF NOT EXISTS scanners (
    scanner_id UUID PRIMARY KEY,
    venue_id UUID REFERENCES venues(venue_id),
    operator_name TEXT NOT NULL,
    registered_at TIMESTAMPTZ DEFAULT NOW()
);

-- Scans table
CREATE TABLE IF NOT EXISTS scans (
    scan_id UUID PRIMARY KEY,
    ticket_id UUID REFERENCES tickets(token_id),
    scanner_id UUID REFERENCES scanners(scanner_id),
    venue_id UUID REFERENCES venues(venue_id),
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    valid BOOLEAN DEFAULT TRUE
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_tickets_owner ON tickets(owner);
CREATE INDEX IF NOT EXISTS idx_tickets_event ON tickets(event_id);
CREATE INDEX IF NOT EXISTS idx_events_status ON events(status);
CREATE INDEX IF NOT EXISTS idx_resales_status ON resales(status);
CREATE INDEX IF NOT EXISTS idx_orders_buyer ON orders(buyer_wallet);

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
CREATE POLICY "Allow all operations on wallets" ON wallets FOR ALL USING (true);
CREATE POLICY "Allow all operations on venues" ON venues FOR ALL USING (true);
CREATE POLICY "Allow all operations on events" ON events FOR ALL USING (true);
CREATE POLICY "Allow all operations on tickets" ON tickets FOR ALL USING (true);
CREATE POLICY "Allow all operations on orders" ON orders FOR ALL USING (true);
CREATE POLICY "Allow all operations on resales" ON resales FOR ALL USING (true);
CREATE POLICY "Allow all operations on scanners" ON scanners FOR ALL USING (true);
CREATE POLICY "Allow all operations on scans" ON scans FOR ALL USING (true);