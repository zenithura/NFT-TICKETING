# Backend Setup Instructions

## Prerequisites
- Python 3.8 or higher
- Supabase account with a project

## Setup Steps

### 1. Database Setup
1. Go to your Supabase project dashboard at https://kuupyybybbvviupflpgj.supabase.co
2. Navigate to the SQL Editor
3. Copy and run the SQL from `supabase_schema.sql`
4. Verify tables are created in the Table Editor

### 2. Backend Installation
```bash
cd backend

# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration
The `.env` file is already configured with your Supabase credentials:
- SUPABASE_URL
- SUPABASE_KEY (anon key)
- SUPABASE_SERVICE_KEY

### 4. Run the Backend
```bash
# Make sure you're in the backend directory with venv activated
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- Main API: http://localhost:8000
- Interactive docs: http://localhost:8000/docs
- Alternative docs: http://localhost:8000/redoc

## API Endpoints

### Authentication
- `POST /auth/connect` - Connect wallet and create/get user
- `GET /auth/user/{address}` - Get user by address
- `POST /auth/upgrade-to-organizer/{address}` - Upgrade user to organizer

### Events
- `POST /events/` - Create event (organizer only)
- `GET /events/` - List all events
- `GET /events/{event_id}` - Get specific event
- `GET /events/organizer/{organizer_address}` - Get organizer's events

### Tickets
- `POST /tickets/` - Create/mint ticket
- `GET /tickets/user/{owner_address}` - Get user's tickets
- `GET /tickets/event/{event_id}` - Get event tickets
- `GET /tickets/{ticket_id}` - Get specific ticket
- `PATCH /tickets/{ticket_id}/transfer` - Transfer ticket
- `PATCH /tickets/{ticket_id}/use` - Mark ticket as used

### Marketplace
- `POST /marketplace/` - Create listing
- `GET /marketplace/` - List all active listings
- `GET /marketplace/{listing_id}` - Get specific listing
- `PATCH /marketplace/{listing_id}` - Update listing
- `POST /marketplace/{listing_id}/buy` - Buy ticket
- `GET /marketplace/seller/{seller_address}` - Get seller's listings

## Testing
Use the interactive docs at http://localhost:8000/docs to test all endpoints.
