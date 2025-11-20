from fastapi import FastAPI, APIRouter, HTTPException, Query
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone
from enum import Enum
from supabase import create_client, Client

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Supabase connection
supabase_url = os.environ['SUPABASE_URL']
supabase_key = os.environ['SUPABASE_KEY']
supabase: Client = create_client(supabase_url, supabase_key)

# Create the main app
app = FastAPI(title="NFT Ticketing API")
api_router = APIRouter(prefix="/api")

# Enums
class EventStatus(str, Enum):
    UPCOMING = "UPCOMING"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"

class TicketStatus(str, Enum):
    ACTIVE = "ACTIVE"
    USED = "USED"
    TRANSFERRED = "TRANSFERRED"
    CANCELLED = "CANCELLED"

class TicketTier(str, Enum):
    GENERAL = "GENERAL"
    VIP = "VIP"
    PREMIUM = "PREMIUM"

class OrderStatus(str, Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"

class ResaleStatus(str, Enum):
    LISTED = "LISTED"
    SOLD = "SOLD"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"

# Models
class Wallet(BaseModel):
    model_config = ConfigDict(extra="ignore")
    wallet_id: Optional[int] = None
    address: str
    balance: float = 1000.0
    allowlist_status: bool = False
    verification_level: int = 0
    blacklisted: bool = False
    created_at: Optional[str] = None
    last_activity: Optional[str] = None

class WalletConnect(BaseModel):
    address: str

class Venue(BaseModel):
    model_config = ConfigDict(extra="ignore")
    venue_id: Optional[int] = None
    name: str
    location: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    capacity: int
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class VenueCreate(BaseModel):
    name: str
    location: Optional[str] = None
    city: Optional[str] = None
    country: Optional[str] = None
    capacity: int

class Event(BaseModel):
    model_config = ConfigDict(extra="ignore")
    event_id: Optional[int] = None
    venue_id: int
    name: str
    description: Optional[str] = None
    event_date: str
    start_time: Optional[str] = None
    end_time: Optional[str] = None
    total_supply: int
    available_tickets: Optional[int] = None
    base_price: float
    max_resale_percentage: float = 150.0
    status: EventStatus = EventStatus.UPCOMING
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class EventCreate(BaseModel):
    venue_id: int
    name: str
    description: Optional[str] = None
    event_date: str
    start_time: Optional[str] = "19:00:00"
    end_time: Optional[str] = "23:00:00"
    total_supply: int
    base_price: float

class Ticket(BaseModel):
    model_config = ConfigDict(extra="ignore")
    ticket_id: Optional[int] = None
    event_id: int
    owner_wallet_id: int
    token_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    nft_metadata_uri: Optional[str] = None
    seat_number: Optional[str] = None
    tier: TicketTier = TicketTier.GENERAL
    purchase_price: float
    status: TicketStatus = TicketStatus.ACTIVE
    minted_at: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class TicketMint(BaseModel):
    event_id: int
    buyer_address: str

class Order(BaseModel):
    model_config = ConfigDict(extra="ignore")
    order_id: Optional[int] = None
    buyer_wallet_id: int
    ticket_id: int
    event_id: int
    order_type: str = "PRIMARY"
    price: float
    platform_fee: float = 0.0
    total_amount: float
    transaction_hash: Optional[str] = None
    status: OrderStatus = OrderStatus.COMPLETED
    created_at: Optional[str] = None
    completed_at: Optional[str] = None

class Resale(BaseModel):
    model_config = ConfigDict(extra="ignore")
    resale_id: Optional[int] = None
    ticket_id: int
    seller_wallet_id: int
    buyer_wallet_id: Optional[int] = None
    original_order_id: int
    listing_price: float
    original_price: float
    markup_percentage: Optional[float] = None
    status: ResaleStatus = ResaleStatus.LISTED
    listed_at: Optional[str] = None
    sold_at: Optional[str] = None

class ResaleCreate(BaseModel):
    ticket_id: int
    seller_address: str
    listing_price: float

class ResaleBuy(BaseModel):
    resale_id: int
    buyer_address: str

class Scanner(BaseModel):
    model_config = ConfigDict(extra="ignore")
    scanner_id: Optional[int] = None
    venue_id: int
    operator_name: str
    operator_wallet: Optional[str] = None
    device_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    active: bool = True
    registered_at: Optional[str] = None

class ScannerRegister(BaseModel):
    venue_id: int
    operator_name: str
    operator_wallet: Optional[str] = None

class Scan(BaseModel):
    model_config = ConfigDict(extra="ignore")
    scan_id: Optional[int] = None
    ticket_id: int
    scanner_id: int
    venue_id: int
    event_id: int
    scan_type: str = "ENTRY"
    valid: bool = True
    error_message: Optional[str] = None
    scanned_at: Optional[str] = None

class ScanVerify(BaseModel):
    ticket_id: int
    scanner_id: int

# Helper functions
def get_wallet_by_address(address: str):
    result = supabase.table('wallets').select('*').eq('address', address).execute()
    return result.data[0] if result.data else None

def get_wallet_by_id(wallet_id: int):
    result = supabase.table('wallets').select('*').eq('wallet_id', wallet_id).execute()
    return result.data[0] if result.data else None

# API Routes
@api_router.get("/")
async def root():
    return {"message": "NFT Ticketing API", "version": "2.0.0", "database": "Supabase PostgreSQL"}

# Wallet Routes
@api_router.post("/wallet/connect", response_model=Wallet)
async def connect_wallet(wallet_input: WalletConnect):
    try:
        existing = get_wallet_by_address(wallet_input.address)
        if existing:
            return Wallet(**existing)
        
        # Create new wallet
        wallet_data = {
            "address": wallet_input.address,
            "balance": 1000.0,
            "allowlist_status": False,
            "verification_level": 0,
            "blacklisted": False
        }
        
        result = supabase.table('wallets').insert(wallet_data).execute()
        return Wallet(**result.data[0])
    except Exception as e:
        logging.error(f"Error connecting wallet: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/wallet/{address}", response_model=Wallet)
async def get_wallet(address: str):
    try:
        wallet = get_wallet_by_address(address)
        if not wallet:
            raise HTTPException(status_code=404, detail="Wallet not found")
        return Wallet(**wallet)
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error getting wallet: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Venue Routes
@api_router.post("/venues", response_model=Venue)
async def create_venue(venue_input: VenueCreate):
    try:
        venue_data = venue_input.model_dump()
        result = supabase.table('venues').insert(venue_data).execute()
        return Venue(**result.data[0])
    except Exception as e:
        logging.error(f"Error creating venue: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/venues", response_model=List[Venue])
async def get_venues():
    try:
        result = supabase.table('venues').select('*').execute()
        return [Venue(**v) for v in result.data]
    except Exception as e:
        logging.error(f"Error getting venues: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Event Routes
@api_router.post("/events", response_model=Event)
async def create_event(event_input: EventCreate):
    try:
        event_data = event_input.model_dump()
        event_data['available_tickets'] = event_data['total_supply']
        event_data['status'] = EventStatus.ACTIVE.value
        
        result = supabase.table('events').insert(event_data).execute()
        return Event(**result.data[0])
    except Exception as e:
        logging.error(f"Error creating event: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/events", response_model=List[Event])
async def get_events(status: Optional[EventStatus] = None):
    try:
        query = supabase.table('events').select('*')
        if status:
            query = query.eq('status', status.value)
        result = query.execute()
        return [Event(**e) for e in result.data]
    except Exception as e:
        logging.error(f"Error getting events: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/events/{event_id}", response_model=Event)
async def get_event(event_id: int):
    try:
        result = supabase.table('events').select('*').eq('event_id', event_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Event not found")
        return Event(**result.data[0])
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error getting event: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Ticket Routes
@api_router.post("/tickets/mint", response_model=Ticket)
async def mint_ticket(mint_input: TicketMint):
    try:
        # Get event
        event_result = supabase.table('events').select('*').eq('event_id', mint_input.event_id).execute()
        if not event_result.data:
            raise HTTPException(status_code=404, detail="Event not found")
        
        event = event_result.data[0]
        
        # Check available tickets
        if event['available_tickets'] <= 0:
            raise HTTPException(status_code=400, detail="Event sold out")
        
        # Get wallet
        wallet = get_wallet_by_address(mint_input.buyer_address)
        if not wallet:
            raise HTTPException(status_code=404, detail="Wallet not found")
        
        # Check balance
        if wallet['balance'] < event['base_price']:
            raise HTTPException(status_code=400, detail="Insufficient balance")
        
        # Create ticket
        ticket_data = {
            "event_id": mint_input.event_id,
            "owner_wallet_id": wallet['wallet_id'],
            "token_id": str(uuid.uuid4()),
            "purchase_price": event['base_price'],
            "tier": TicketTier.GENERAL.value,
            "status": TicketStatus.ACTIVE.value
        }
        
        ticket_result = supabase.table('tickets').insert(ticket_data).execute()
        ticket = ticket_result.data[0]
        
        # Create order
        order_data = {
            "buyer_wallet_id": wallet['wallet_id'],
            "ticket_id": ticket['ticket_id'],
            "event_id": mint_input.event_id,
            "order_type": "PRIMARY",
            "price": event['base_price'],
            "platform_fee": 0.0,
            "total_amount": event['base_price'],
            "status": OrderStatus.COMPLETED.value,
            "completed_at": datetime.now(timezone.utc).isoformat()
        }
        supabase.table('orders').insert(order_data).execute()
        
        # Update wallet balance
        new_balance = wallet['balance'] - event['base_price']
        supabase.table('wallets').update({"balance": new_balance}).eq('wallet_id', wallet['wallet_id']).execute()
        
        # Update event available tickets
        supabase.table('events').update({
            "available_tickets": event['available_tickets'] - 1
        }).eq('event_id', mint_input.event_id).execute()
        
        return Ticket(**ticket)
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error minting ticket: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/tickets/wallet/{wallet_address}", response_model=List[Ticket])
async def get_wallet_tickets(wallet_address: str):
    try:
        wallet = get_wallet_by_address(wallet_address)
        if not wallet:
            return []
        
        result = supabase.table('tickets').select('*').eq('owner_wallet_id', wallet['wallet_id']).execute()
        return [Ticket(**t) for t in result.data]
    except Exception as e:
        logging.error(f"Error getting wallet tickets: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/tickets/{ticket_id}", response_model=Ticket)
async def get_ticket(ticket_id: int):
    try:
        result = supabase.table('tickets').select('*').eq('ticket_id', ticket_id).execute()
        if not result.data:
            raise HTTPException(status_code=404, detail="Ticket not found")
        return Ticket(**result.data[0])
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error getting ticket: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Marketplace/Resale Routes
@api_router.post("/marketplace/list", response_model=Resale)
async def list_resale(resale_input: ResaleCreate):
    try:
        # Get ticket
        ticket_result = supabase.table('tickets').select('*').eq('ticket_id', resale_input.ticket_id).execute()
        if not ticket_result.data:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        ticket = ticket_result.data[0]
        
        # Get seller wallet
        seller_wallet = get_wallet_by_address(resale_input.seller_address)
        if not seller_wallet:
            raise HTTPException(status_code=404, detail="Seller wallet not found")
        
        # Verify ownership
        if ticket['owner_wallet_id'] != seller_wallet['wallet_id']:
            raise HTTPException(status_code=403, detail="Not ticket owner")
        
        if ticket['status'] == TicketStatus.USED.value:
            raise HTTPException(status_code=400, detail="Ticket already used")
        
        # Check if already listed
        existing = supabase.table('resales').select('*').eq('ticket_id', resale_input.ticket_id).eq('status', ResaleStatus.LISTED.value).execute()
        if existing.data:
            raise HTTPException(status_code=400, detail="Ticket already listed")
        
        # Get original order
        order_result = supabase.table('orders').select('*').eq('ticket_id', resale_input.ticket_id).eq('order_type', 'PRIMARY').execute()
        if not order_result.data:
            raise HTTPException(status_code=404, detail="Original order not found")
        
        original_order = order_result.data[0]
        
        # Create resale
        resale_data = {
            "ticket_id": resale_input.ticket_id,
            "seller_wallet_id": seller_wallet['wallet_id'],
            "original_order_id": original_order['order_id'],
            "listing_price": resale_input.listing_price,
            "original_price": original_order['price'],
            "markup_percentage": ((resale_input.listing_price - original_order['price']) / original_order['price']) * 100,
            "status": ResaleStatus.LISTED.value
        }
        
        result = supabase.table('resales').insert(resale_data).execute()
        
        # Update ticket status
        supabase.table('tickets').update({'status': TicketStatus.TRANSFERRED.value}).eq('ticket_id', resale_input.ticket_id).execute()
        
        return Resale(**result.data[0])
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error listing resale: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/marketplace/listings", response_model=List[Resale])
async def get_marketplace_listings():
    try:
        result = supabase.table('resales').select('*').eq('status', ResaleStatus.LISTED.value).execute()
        return [Resale(**r) for r in result.data]
    except Exception as e:
        logging.error(f"Error getting marketplace listings: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/marketplace/buy")
async def buy_resale(buy_input: ResaleBuy):
    try:
        # Get resale
        resale_result = supabase.table('resales').select('*').eq('resale_id', buy_input.resale_id).execute()
        if not resale_result.data:
            raise HTTPException(status_code=404, detail="Resale not found")
        
        resale = resale_result.data[0]
        if resale['status'] != ResaleStatus.LISTED.value:
            raise HTTPException(status_code=400, detail="Resale not available")
        
        # Get buyer wallet
        buyer_wallet = get_wallet_by_address(buy_input.buyer_address)
        if not buyer_wallet:
            raise HTTPException(status_code=404, detail="Buyer wallet not found")
        
        if buyer_wallet['balance'] < resale['listing_price']:
            raise HTTPException(status_code=400, detail="Insufficient balance")
        
        # Get ticket
        ticket_result = supabase.table('tickets').select('*').eq('ticket_id', resale['ticket_id']).execute()
        ticket = ticket_result.data[0]
        
        # Get seller wallet
        seller_wallet = get_wallet_by_id(resale['seller_wallet_id'])
        
        # Transfer ticket
        supabase.table('tickets').update({
            'owner_wallet_id': buyer_wallet['wallet_id'],
            'status': TicketStatus.ACTIVE.value,
            'last_transfer_at': datetime.now(timezone.utc).isoformat()
        }).eq('ticket_id', resale['ticket_id']).execute()
        
        # Create resale order
        order_data = {
            "buyer_wallet_id": buyer_wallet['wallet_id'],
            "ticket_id": resale['ticket_id'],
            "event_id": ticket['event_id'],
            "order_type": "RESALE",
            "price": resale['listing_price'],
            "platform_fee": 0.0,
            "total_amount": resale['listing_price'],
            "status": OrderStatus.COMPLETED.value,
            "completed_at": datetime.now(timezone.utc).isoformat()
        }
        supabase.table('orders').insert(order_data).execute()
        
        # Update buyer balance
        supabase.table('wallets').update({
            'balance': buyer_wallet['balance'] - resale['listing_price']
        }).eq('wallet_id', buyer_wallet['wallet_id']).execute()
        
        # Update seller balance
        supabase.table('wallets').update({
            'balance': seller_wallet['balance'] + resale['listing_price']
        }).eq('wallet_id', seller_wallet['wallet_id']).execute()
        
        # Update resale
        supabase.table('resales').update({
            'status': ResaleStatus.SOLD.value,
            'buyer_wallet_id': buyer_wallet['wallet_id'],
            'sold_at': datetime.now(timezone.utc).isoformat()
        }).eq('resale_id', buy_input.resale_id).execute()
        
        return {"success": True, "message": "Ticket purchased successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error buying resale: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Scanner Routes
@api_router.post("/scanner/register", response_model=Scanner)
async def register_scanner(scanner_input: ScannerRegister):
    try:
        scanner_data = scanner_input.model_dump()
        scanner_data['device_id'] = str(uuid.uuid4())
        
        result = supabase.table('scanners').insert(scanner_data).execute()
        return Scanner(**result.data[0])
    except Exception as e:
        logging.error(f"Error registering scanner: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/scanner/verify", response_model=Scan)
async def verify_ticket(scan_input: ScanVerify):
    try:
        # Get ticket
        ticket_result = supabase.table('tickets').select('*').eq('ticket_id', scan_input.ticket_id).execute()
        if not ticket_result.data:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        ticket = ticket_result.data[0]
        
        # Get scanner
        scanner_result = supabase.table('scanners').select('*').eq('scanner_id', scan_input.scanner_id).execute()
        if not scanner_result.data:
            raise HTTPException(status_code=404, detail="Scanner not found")
        
        scanner = scanner_result.data[0]
        
        # Check if already used
        valid = True
        error_msg = None
        
        if ticket['status'] == TicketStatus.USED.value:
            valid = False
            error_msg = "Ticket already used"
        
        # Create scan record
        scan_data = {
            "ticket_id": scan_input.ticket_id,
            "scanner_id": scan_input.scanner_id,
            "venue_id": scanner['venue_id'],
            "event_id": ticket['event_id'],
            "scan_type": "ENTRY",
            "valid": valid,
            "error_message": error_msg
        }
        
        result = supabase.table('scans').insert(scan_data).execute()
        
        # Mark ticket as used if valid
        if valid:
            supabase.table('tickets').update({'status': TicketStatus.USED.value}).eq('ticket_id', scan_input.ticket_id).execute()
        else:
            raise HTTPException(status_code=400, detail=error_msg)
        
        return Scan(**result.data[0])
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error verifying ticket: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/scans/venue/{venue_id}", response_model=List[Scan])
async def get_venue_scans(venue_id: int):
    try:
        result = supabase.table('scans').select('*').eq('venue_id', venue_id).execute()
        return [Scan(**s) for s in result.data]
    except Exception as e:
        logging.error(f"Error getting venue scans: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000", "http://localhost:5000"],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:[0-9]+)?",  # Allow any localhost/127.0.0.1 port for development
    allow_methods=["*"],
    allow_headers=["*"],
)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)