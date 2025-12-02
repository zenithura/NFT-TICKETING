-- NFT Ticketing Platform - Supabase Database Schema
-- Run this in Supabase SQL Editor

-- Enable UUID extension (if not already enabled)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table
CREATE TABLE IF NOT EXISTS users (
    address VARCHAR(42) PRIMARY KEY,  -- Ethereum address (0x...)
    role VARCHAR(20) NOT NULL DEFAULT 'user' CHECK (role IN ('user', 'organizer')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Events table
CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    organizer_address VARCHAR(42) NOT NULL REFERENCES users(address) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    description TEXT NOT NULL,
    date VARCHAR(100) NOT NULL,  -- ISO format date string
    location VARCHAR(200) NOT NULL,
    total_tickets INTEGER NOT NULL CHECK (total_tickets > 0),
    price NUMERIC(18, 6) NOT NULL CHECK (price >= 0),  -- Support decimals for crypto
    image_url TEXT,
    category VARCHAR(100) DEFAULT 'All',
    currency VARCHAR(10) DEFAULT 'ETH',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tickets table
CREATE TABLE IF NOT EXISTS tickets (
    id SERIAL PRIMARY KEY,
    event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    owner_address VARCHAR(42) NOT NULL REFERENCES users(address) ON DELETE CASCADE,
    nft_token_id INTEGER,  -- Blockchain NFT token ID (nullable for initial creation)
    status VARCHAR(20) NOT NULL DEFAULT 'available' CHECK (status IN ('available', 'bought', 'used')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Marketplace table
CREATE TABLE IF NOT EXISTS marketplace (
    id SERIAL PRIMARY KEY,
    ticket_id INTEGER NOT NULL REFERENCES tickets(id) ON DELETE CASCADE,
    seller_address VARCHAR(42) NOT NULL REFERENCES users(address) ON DELETE CASCADE,
    price NUMERIC(18, 6) NOT NULL CHECK (price >= 0),
    status VARCHAR(20) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'sold', 'cancelled')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_events_organizer ON events(organizer_address);
CREATE INDEX IF NOT EXISTS idx_tickets_event ON tickets(event_id);
CREATE INDEX IF NOT EXISTS idx_tickets_owner ON tickets(owner_address);
CREATE INDEX IF NOT EXISTS idx_marketplace_ticket ON marketplace(ticket_id);
CREATE INDEX IF NOT EXISTS idx_marketplace_seller ON marketplace(seller_address);
CREATE INDEX IF NOT EXISTS idx_marketplace_status ON marketplace(status);

-- Enable Row Level Security (RLS) - Optional but recommended for production
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE events ENABLE ROW LEVEL SECURITY;
ALTER TABLE tickets ENABLE ROW LEVEL SECURITY;
ALTER TABLE marketplace ENABLE ROW LEVEL SECURITY;

-- Create policies for public read access (adjust based on your requirements)
-- Allow all users to read all data (service key bypasses these anyway)
CREATE POLICY "Allow public read access on users" ON users FOR SELECT USING (true);
CREATE POLICY "Allow public read access on events" ON events FOR SELECT USING (true);
CREATE POLICY "Allow public read access on tickets" ON tickets FOR SELECT USING (true);
CREATE POLICY "Allow public read access on marketplace" ON marketplace FOR SELECT USING (true);

-- For write operations, use service key from backend (which bypasses RLS)
-- Or create more specific policies based on user authentication

-- Insert some demo data (optional)
INSERT INTO users (address, role) VALUES 
    ('0x1234567890123456789012345678901234567890', 'organizer'),
    ('0x0987654321098765432109876543210987654321', 'user')
ON CONFLICT (address) DO NOTHING;
