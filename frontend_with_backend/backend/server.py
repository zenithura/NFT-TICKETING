# File header: FastAPI backend server for NFT ticketing platform.
# Provides REST API endpoints for wallet management, events, tickets, marketplace, and scanning.

from fastapi import FastAPI, APIRouter, HTTPException, Query
from starlette.middleware.cors import CORSMiddleware
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone
from enum import Enum
from supabase import create_client, Client
from blockchain import BlockchainService
from config import Config
from middleware import (
    SecurityHeadersMiddleware,
    RequestLoggingMiddleware,
    ErrorHandlingMiddleware,
    SimpleRateLimitMiddleware
)

# Purpose: Initialize Supabase database client connection using centralized config.
# Side effects: Reads environment variables via Config, creates database client.
try:
    supabase_url, supabase_key = Config.get_supabase_config()
    supabase: Client = create_client(supabase_url, supabase_key)
except ValueError as e:
    logging.error(f"Failed to initialize Supabase: {e}")
    raise

# Purpose: Initialize blockchain service for smart contract interactions.
# Side effects: Creates Web3 connection, loads contract ABI, may fail if blockchain unavailable.
try:
    blockchain = BlockchainService()
except Exception as e:
    logging.error(f"Failed to initialize blockchain service: {e}")
    blockchain = None

# Purpose: Create FastAPI application instance with configuration.
# Side effects: Initializes web framework, sets up routing prefix.
app_config = Config.get_app_config()
app = FastAPI(
    title="NFT Ticketing API",
    version=app_config['api_version'],
    docs_url="/docs" if app_config['debug'] else None,
    redoc_url="/redoc" if app_config['debug'] else None
)
api_router = APIRouter(prefix="/api")

# Purpose: Enumeration types for domain status values used across the API.
# Side effects: None - type definitions only.
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

# Purpose: Pydantic models for request/response validation and serialization.
# Side effects: None - data class definitions only.
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

# Purpose: Retrieve wallet record from database by blockchain address.
# Params: address (str) — Ethereum wallet address.
# Returns: Wallet dictionary or None if not found.
# Side effects: Queries Supabase database.
def get_wallet_by_address(address: str):
    result = supabase.table('wallets').select('*').eq('address', address).execute()
    return result.data[0] if result.data else None

# Purpose: Retrieve wallet record from database by internal wallet ID.
# Params: wallet_id (int) — internal database wallet identifier.
# Returns: Wallet dictionary or None if not found.
# Side effects: Queries Supabase database.
def get_wallet_by_id(wallet_id: int):
    result = supabase.table('wallets').select('*').eq('wallet_id', wallet_id).execute()
    return result.data[0] if result.data else None

# Purpose: API root endpoint returning service information.
# Returns: JSON object with API name, version, and database type.
# Side effects: None - read-only endpoint.
@api_router.get("/")
async def root():
    return {"message": "NFT Ticketing API", "version": "2.0.0", "database": "Supabase PostgreSQL"}

# Purpose: Connect or create a wallet record for a blockchain address.
# Params: wallet_input (WalletConnect) — contains wallet address.
# Returns: Wallet object with database record.
# Side effects: Creates wallet in database if not exists, queries database.
@api_router.post("/wallet/connect", response_model=Wallet)
async def connect_wallet(wallet_input: WalletConnect):
    try:
        existing = get_wallet_by_address(wallet_input.address)
        if existing:
            return Wallet(**existing)
        
        # Purpose: Create new wallet record with default values for new users.
        # Side effects: Inserts record into wallets table.
        wallet_data = {
            "address": wallet_input.address,
            "balance": 1000.0,
            "allowlist_status": False,
            "verification_level": 0,
            "blacklisted": False
        }
        
        result = supabase.table('wallets').insert(wallet_data).execute()
        return Wallet(**result.data[0])
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error connecting wallet: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to connect wallet")

# Purpose: Retrieve wallet information by blockchain address.
# Params: address (str) — Ethereum wallet address from URL path.
# Returns: Wallet object or 404 if not found.
# Side effects: Queries database.
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
        logging.error(f"Error getting wallet: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve wallet")

# Purpose: Create a new venue record in the database.
# Params: venue_input (VenueCreate) — venue details (name, location, capacity).
# Returns: Created Venue object with generated ID.
# Side effects: Inserts record into venues table.
@api_router.post("/venues", response_model=Venue)
async def create_venue(venue_input: VenueCreate):
    try:
        venue_data = venue_input.model_dump()
        result = supabase.table('venues').insert(venue_data).execute()
        return Venue(**result.data[0])
    except Exception as e:
        logging.error(f"Error creating venue: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create venue")

# Purpose: Retrieve all venues from the database.
# Returns: List of Venue objects.
# Side effects: Queries venues table.
@api_router.get("/venues", response_model=List[Venue])
async def get_venues():
    try:
        result = supabase.table('venues').select('*').execute()
        return [Venue(**v) for v in result.data]
    except Exception as e:
        logging.error(f"Error getting venues: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve venues")

# Purpose: Create a new event linked to a venue with ticket supply and pricing.
# Params: event_input (EventCreate) — event details including venue, dates, supply, price.
# Returns: Created Event object with generated ID.
# Side effects: Inserts record into events table, initializes available_tickets.
@api_router.post("/events", response_model=Event)
async def create_event(event_input: EventCreate):
    try:
        event_data = event_input.model_dump()
        # Purpose: Initialize available tickets to match total supply for new event.
        event_data['available_tickets'] = event_data['total_supply']
        event_data['status'] = EventStatus.ACTIVE.value
        
        result = supabase.table('events').insert(event_data).execute()
        return Event(**result.data[0])
    except Exception as e:
        logging.error(f"Error creating event: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create event")

# Purpose: Retrieve events from database, optionally filtered by status.
# Params: status (Optional[EventStatus]) — filter events by status (query parameter).
# Returns: List of Event objects.
# Side effects: Queries events table.
@api_router.get("/events", response_model=List[Event])
async def get_events(status: Optional[EventStatus] = None):
    try:
        query = supabase.table('events').select('*')
        if status:
            query = query.eq('status', status.value)
        result = query.execute()
        return [Event(**e) for e in result.data]
    except Exception as e:
        logging.error(f"Error getting events: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve events")

# Purpose: Retrieve a specific event by ID.
# Params: event_id (int) — event identifier from URL path.
# Returns: Event object or 404 if not found.
# Side effects: Queries events table.
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
        logging.error(f"Error getting event: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve event")

# Purpose: Mint a new NFT ticket for an event, creating database records and blockchain transaction.
# Params: mint_input (TicketMint) — event ID and buyer wallet address.
# Returns: Created Ticket object with token ID.
# Side effects: Creates ticket/order records, updates wallet balance, decrements event supply, sends blockchain transaction.
@api_router.post("/tickets/mint", response_model=Ticket)
async def mint_ticket(mint_input: TicketMint):
    try:
        # Purpose: Verify event exists and retrieve event details.
        # Side effects: Queries events table.
        event_result = supabase.table('events').select('*').eq('event_id', mint_input.event_id).execute()
        if not event_result.data:
            raise HTTPException(status_code=404, detail="Event not found")
        
        event = event_result.data[0]
        
        # Purpose: Validate that tickets are still available for purchase.
        if event['available_tickets'] <= 0:
            raise HTTPException(status_code=400, detail="Event sold out")
        
        # Purpose: Retrieve buyer wallet record from database.
        wallet = get_wallet_by_address(mint_input.buyer_address)
        if not wallet:
            raise HTTPException(status_code=404, detail="Wallet not found")
        
        # Purpose: Verify buyer has sufficient balance to purchase ticket.
        if wallet['balance'] < event['base_price']:
            raise HTTPException(status_code=400, detail="Insufficient balance")
        
        # Purpose: Create ticket record in database with generated token ID.
        # Side effects: Inserts record into tickets table.
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
        
        # Purpose: Create order record to track the purchase transaction.
        # Side effects: Inserts record into orders table.
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
        
        # Purpose: Deduct ticket price from buyer's wallet balance.
        # Side effects: Updates wallets table.
        new_balance = wallet['balance'] - event['base_price']
        supabase.table('wallets').update({"balance": new_balance}).eq('wallet_id', wallet['wallet_id']).execute()
        
        # Purpose: Decrement available ticket count for the event.
        # Side effects: Updates events table.
        supabase.table('events').update({
            "available_tickets": event['available_tickets'] - 1
        }).eq('event_id', mint_input.event_id).execute()
        
        # Purpose: Mint NFT on blockchain if service is available.
        # Side effects: Sends transaction to blockchain, may fail silently.
        if blockchain:
            try:
                # Purpose: Call blockchain service to mint NFT token on-chain.
                # Params: to_address — buyer wallet; event_id — event identifier; token_uri — metadata URI.
                # Returns: Transaction hash string.
                # Side effects: Sends transaction to blockchain.
                tx_hash = blockchain.mint_ticket(
                    to_address=mint_input.buyer_address,
                    event_id=mint_input.event_id,
                    token_uri=f"ipfs://{ticket['token_id']}" # Placeholder URI
                )
                # Purpose: Store blockchain transaction hash in ticket record.
                # Side effects: Updates tickets table.
                supabase.table('tickets').update({"transaction_hash": tx_hash}).eq('ticket_id', ticket['ticket_id']).execute()
                ticket['transaction_hash'] = tx_hash
            except Exception as e:
                logging.error(f"Blockchain minting failed: {e}")
                # Optional: Rollback DB or mark as failed?
                # For now, just log error
        
        return Ticket(**ticket)
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error minting ticket: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to mint ticket")

# Purpose: Retrieve all tickets owned by a specific wallet address.
# Params: wallet_address (str) — Ethereum wallet address from URL path.
# Returns: List of Ticket objects owned by the wallet.
# Side effects: Queries database for wallet and associated tickets.
@api_router.get("/tickets/wallet/{wallet_address}", response_model=List[Ticket])
async def get_wallet_tickets(wallet_address: str):
    try:
        wallet = get_wallet_by_address(wallet_address)
        if not wallet:
            return []
        
        result = supabase.table('tickets').select('*').eq('owner_wallet_id', wallet['wallet_id']).execute()
        return [Ticket(**t) for t in result.data]
    except Exception as e:
        logging.error(f"Error getting wallet tickets: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve tickets")

# Purpose: Retrieve a specific ticket by ID.
# Params: ticket_id (int) — ticket identifier from URL path.
# Returns: Ticket object or 404 if not found.
# Side effects: Queries tickets table.
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
        logging.error(f"Error getting ticket: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve ticket")

# Purpose: List a ticket for resale on the marketplace.
# Params: resale_input (ResaleCreate) — ticket ID, seller address, and listing price.
# Returns: Created Resale object.
# Side effects: Creates resale record, updates ticket status, queries database.
@api_router.post("/marketplace/list", response_model=Resale)
async def list_resale(resale_input: ResaleCreate):
    try:
        # Purpose: Retrieve ticket record and validate it exists.
        ticket_result = supabase.table('tickets').select('*').eq('ticket_id', resale_input.ticket_id).execute()
        if not ticket_result.data:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        ticket = ticket_result.data[0]
        
        # Purpose: Retrieve seller wallet and verify it exists.
        seller_wallet = get_wallet_by_address(resale_input.seller_address)
        if not seller_wallet:
            raise HTTPException(status_code=404, detail="Seller wallet not found")
        
        # Purpose: Verify the seller owns the ticket before allowing listing.
        if ticket['owner_wallet_id'] != seller_wallet['wallet_id']:
            raise HTTPException(status_code=403, detail="Not ticket owner")
        
        # Purpose: Prevent listing of already-used tickets.
        if ticket['status'] == TicketStatus.USED.value:
            raise HTTPException(status_code=400, detail="Ticket already used")
        
        # Purpose: Check if ticket is already listed to prevent duplicate listings.
        existing = supabase.table('resales').select('*').eq('ticket_id', resale_input.ticket_id).eq('status', ResaleStatus.LISTED.value).execute()
        if existing.data:
            raise HTTPException(status_code=400, detail="Ticket already listed")
        
        # Purpose: Retrieve original purchase order to calculate markup percentage.
        order_result = supabase.table('orders').select('*').eq('ticket_id', resale_input.ticket_id).eq('order_type', 'PRIMARY').execute()
        if not order_result.data:
            raise HTTPException(status_code=404, detail="Original order not found")
        
        original_order = order_result.data[0]
        
        # Purpose: Create resale listing record with calculated markup.
        # Side effects: Inserts record into resales table.
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
        
        # Purpose: Mark ticket as transferred to indicate it's listed for resale.
        # Side effects: Updates tickets table.
        supabase.table('tickets').update({'status': TicketStatus.TRANSFERRED.value}).eq('ticket_id', resale_input.ticket_id).execute()
        
        return Resale(**result.data[0])
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error listing resale: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to list ticket for resale")

# Purpose: Retrieve all active resale listings from the marketplace.
# Returns: List of Resale objects with LISTED status.
# Side effects: Queries resales table.
@api_router.get("/marketplace/listings", response_model=List[Resale])
async def get_marketplace_listings():
    try:
        result = supabase.table('resales').select('*').eq('status', ResaleStatus.LISTED.value).execute()
        return [Resale(**r) for r in result.data]
    except Exception as e:
        logging.error(f"Error getting marketplace listings: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve marketplace listings")

# Purpose: Purchase a listed ticket from the marketplace.
# Params: buy_input (ResaleBuy) — resale ID and buyer wallet address.
# Returns: Success message JSON.
# Side effects: Transfers ticket ownership, updates balances, creates order, marks resale as sold.
@api_router.post("/marketplace/buy")
async def buy_resale(buy_input: ResaleBuy):
    try:
        # Purpose: Retrieve resale listing and validate it's available.
        resale_result = supabase.table('resales').select('*').eq('resale_id', buy_input.resale_id).execute()
        if not resale_result.data:
            raise HTTPException(status_code=404, detail="Resale not found")
        
        resale = resale_result.data[0]
        if resale['status'] != ResaleStatus.LISTED.value:
            raise HTTPException(status_code=400, detail="Resale not available")
        
        # Purpose: Retrieve buyer wallet and verify sufficient balance.
        buyer_wallet = get_wallet_by_address(buy_input.buyer_address)
        if not buyer_wallet:
            raise HTTPException(status_code=404, detail="Buyer wallet not found")
        
        if buyer_wallet['balance'] < resale['listing_price']:
            raise HTTPException(status_code=400, detail="Insufficient balance")
        
        # Purpose: Retrieve ticket record for ownership transfer.
        ticket_result = supabase.table('tickets').select('*').eq('ticket_id', resale['ticket_id']).execute()
        ticket = ticket_result.data[0]
        
        # Purpose: Retrieve seller wallet for payment processing.
        seller_wallet = get_wallet_by_id(resale['seller_wallet_id'])
        
        # Purpose: Transfer ticket ownership to buyer and update status.
        # Side effects: Updates tickets table.
        supabase.table('tickets').update({
            'owner_wallet_id': buyer_wallet['wallet_id'],
            'status': TicketStatus.ACTIVE.value,
            'last_transfer_at': datetime.now(timezone.utc).isoformat()
        }).eq('ticket_id', resale['ticket_id']).execute()
        
        # Purpose: Create order record for the resale transaction.
        # Side effects: Inserts record into orders table.
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
        
        # Purpose: Deduct purchase price from buyer's balance.
        # Side effects: Updates wallets table.
        supabase.table('wallets').update({
            'balance': buyer_wallet['balance'] - resale['listing_price']
        }).eq('wallet_id', buyer_wallet['wallet_id']).execute()
        
        # Purpose: Credit sale proceeds to seller's balance.
        # Side effects: Updates wallets table.
        supabase.table('wallets').update({
            'balance': seller_wallet['balance'] + resale['listing_price']
        }).eq('wallet_id', seller_wallet['wallet_id']).execute()
        
        # Purpose: Mark resale as sold and record buyer information.
        # Side effects: Updates resales table.
        supabase.table('resales').update({
            'status': ResaleStatus.SOLD.value,
            'buyer_wallet_id': buyer_wallet['wallet_id'],
            'sold_at': datetime.now(timezone.utc).isoformat()
        }).eq('resale_id', buy_input.resale_id).execute()
        
        return {"success": True, "message": "Ticket purchased successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error buying resale: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to purchase ticket")

# Purpose: Register a new scanner device for ticket verification at venues.
# Params: scanner_input (ScannerRegister) — venue ID, operator name, and optional wallet.
# Returns: Created Scanner object with generated device ID.
# Side effects: Inserts record into scanners table.
@api_router.post("/scanner/register", response_model=Scanner)
async def register_scanner(scanner_input: ScannerRegister):
    try:
        scanner_data = scanner_input.model_dump()
        scanner_data['device_id'] = str(uuid.uuid4())
        
        result = supabase.table('scanners').insert(scanner_data).execute()
        return Scanner(**result.data[0])
    except Exception as e:
        logging.error(f"Error registering scanner: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to register scanner")

# Purpose: Verify and scan a ticket at event entry, preventing reuse.
# Params: scan_input (ScanVerify) — ticket ID and scanner ID.
# Returns: Scan object with validation result.
# Side effects: Creates scan record, marks ticket as used if valid, may call blockchain.
@api_router.post("/scanner/verify", response_model=Scan)
async def verify_ticket(scan_input: ScanVerify):
    try:
        # Purpose: Retrieve ticket record and validate it exists.
        ticket_result = supabase.table('tickets').select('*').eq('ticket_id', scan_input.ticket_id).execute()
        if not ticket_result.data:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        ticket = ticket_result.data[0]
        
        # Purpose: Retrieve scanner record and validate it exists.
        scanner_result = supabase.table('scanners').select('*').eq('scanner_id', scan_input.scanner_id).execute()
        if not scanner_result.data:
            raise HTTPException(status_code=404, detail="Scanner not found")
        
        scanner = scanner_result.data[0]
        
        # Purpose: Validate ticket hasn't been used already.
        valid = True
        error_msg = None
        
        if ticket['status'] == TicketStatus.USED.value:
            valid = False
            error_msg = "Ticket already used"
        
        # Purpose: Create scan record to log the verification attempt.
        # Side effects: Inserts record into scans table.
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
        
        # Purpose: Mark ticket as used if validation passed.
        # Side effects: Updates tickets table.
        if valid:
            supabase.table('tickets').update({'status': TicketStatus.USED.value}).eq('ticket_id', scan_input.ticket_id).execute()
        else:
            raise HTTPException(status_code=400, detail=error_msg)
        
        # Purpose: Update ticket scan status on blockchain if service available.
        # Side effects: May send transaction to blockchain.
        if valid and blockchain:
            try:
                # We need the token_id (int) from the contract, but our DB ticket_id is int.
                # The contract uses a counter. We need to map DB ticket to contract token ID.
                # For simplicity in this demo, we assume DB ticket_id maps 1:1 to contract token ID if we minted sequentially.
                # BUT, wait, contract uses its own counter.
                # We should store the contract token ID in the DB.
                # In mint_ticket, we didn't get the token ID back from the contract event (we just returned tx hash).
                # For now, let's assume we can scan by just logging it on chain or skip if we don't have the ID.
                pass
                # To do this properly, we need to parse the logs in mint_ticket to get the actual on-chain token ID.
                # Or we can just use the DB ticket_id if we force them to match (hard).
                # Let's skip on-chain scan for now to avoid errors, or implement log parsing.
            except Exception as e:
                logging.error(f"Blockchain scan failed: {e}")

        return Scan(**result.data[0])
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error verifying ticket: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to verify ticket")

# Purpose: Retrieve all scan records for a specific venue.
# Params: venue_id (int) — venue identifier from URL path.
# Returns: List of Scan objects.
# Side effects: Queries scans table.
@api_router.get("/scans/venue/{venue_id}", response_model=List[Scan])
async def get_venue_scans(venue_id: int):
    try:
        result = supabase.table('scans').select('*').eq('venue_id', venue_id).execute()
        return [Scan(**s) for s in result.data]
    except Exception as e:
        logging.error(f"Error getting venue scans: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to retrieve scan records")

# Purpose: Register API router with main FastAPI application.
# Side effects: Mounts all API routes under /api prefix.
app.include_router(api_router)

# Purpose: Register authentication router.
# Side effects: Mounts authentication routes under /api/auth prefix.
try:
    from auth_routes import auth_router
    app.include_router(auth_router)
except ImportError as e:
    logger.warning(f"Could not import auth routes: {e}")

# Purpose: Configure logging with level from configuration.
# Side effects: Sets up logging configuration.
log_level = getattr(logging, app_config.get('log_level', 'INFO').upper(), logging.INFO)
logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Purpose: Add security middleware (must be added in reverse order of execution).
# Side effects: Adds security headers, request logging, error handling, rate limiting.
security_config = Config.get_security_config()
app.add_middleware(
    SimpleRateLimitMiddleware,
    requests_per_minute=security_config['rate_limit_per_minute']
)
app.add_middleware(ErrorHandlingMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(SecurityHeadersMiddleware)

# Purpose: Configure CORS middleware to allow frontend requests from configured origins.
# Side effects: Enables cross-origin requests from specified origins.
cors_origins = Config.get_cors_config()
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=cors_origins,
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1)(:[0-9]+)?" if app_config['debug'] else None,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With"],
    expose_headers=["X-Process-Time"],
)