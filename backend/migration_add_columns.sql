-- Run this script to add the missing columns to the events table
-- This avoids errors about existing tables or policies

ALTER TABLE events ADD COLUMN IF NOT EXISTS image_url TEXT;
ALTER TABLE events ADD COLUMN IF NOT EXISTS category VARCHAR(100) DEFAULT 'All';
ALTER TABLE events ADD COLUMN IF NOT EXISTS currency VARCHAR(10) DEFAULT 'ETH';
