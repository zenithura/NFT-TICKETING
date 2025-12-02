ALTER TABLE tickets ADD COLUMN blockchain_id INTEGER;
CREATE INDEX idx_tickets_blockchain_id ON tickets(blockchain_id);
