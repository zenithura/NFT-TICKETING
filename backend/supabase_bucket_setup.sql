-- =====================================================
-- Supabase Configuration for NFT Ticketing Platform
-- =====================================================
-- This script creates the storage bucket and policies
-- for event image uploads
-- =====================================================

-- Create storage bucket for event images
INSERT INTO storage.buckets (id, name, public)
VALUES ('event-images', 'event-images', true)
ON CONFLICT (id) DO NOTHING;

-- =====================================================
-- Storage Policies
-- =====================================================

-- Allow public read access to event images
CREATE POLICY "Event images are publicly accessible"
ON storage.objects FOR SELECT
USING (bucket_id = 'event-images');

-- Allow authenticated organizers to upload event images
CREATE POLICY "Organizers can upload event images"
ON storage.objects FOR INSERT
WITH CHECK (
  bucket_id = 'event-images' AND
  auth.role() = 'authenticated'
);

-- Allow authenticated organizers to update their event images
CREATE POLICY "Organizers can update their event images"
ON storage.objects FOR UPDATE
USING (bucket_id = 'event-images' AND auth.role() = 'authenticated');

-- Allow authenticated organizers to delete their event images
CREATE POLICY "Organizers can delete their event images"
ON storage.objects FOR DELETE
USING (bucket_id = 'event-images' AND auth.role() = 'authenticated');

-- =====================================================
-- Table Updates
-- =====================================================

-- Ensure events table has image_url column
ALTER TABLE events 
ADD COLUMN IF NOT EXISTS image_url TEXT;

-- =====================================================
-- Performance Indexes
-- =====================================================

-- Create index for faster organizer event queries
CREATE INDEX IF NOT EXISTS idx_events_organizer 
ON events(organizer_address);

-- Create index for faster ticket event queries
CREATE INDEX IF NOT EXISTS idx_tickets_event 
ON tickets(event_id);

-- Create index for faster ticket status queries
CREATE INDEX IF NOT EXISTS idx_tickets_status 
ON tickets(status);

-- =====================================================
-- Usage Instructions
-- =====================================================
-- 
-- 1. Copy this entire script
-- 2. Go to Supabase Dashboard > SQL Editor
-- 3. Paste the script and click "Run"
-- 4. Verify the bucket was created in Storage section
-- 
-- After running this script:
-- - Event images can be uploaded to the 'event-images' bucket
-- - Images will be publicly accessible for viewing
-- - Only authenticated users can upload/modify images
-- - The events table will have an image_url field
-- =====================================================
