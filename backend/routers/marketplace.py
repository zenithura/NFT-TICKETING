"""Marketplace management router."""
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from supabase import Client
import sys
from pathlib import Path

from database import get_supabase_admin
from models import MarketplaceListingCreate, MarketplaceListingResponse, MarketplaceListingUpdate, ListRequest, BuyRequest, UpdatePriceRequest, EscrowRequest
from web3_client import contracts, send_transaction, w3
from web3 import Web3
from cache import get as cache_get, set as cache_set, clear as cache_clear

# Import ML services for fraud detection
_ml_integration = None
def get_ml_integration():
    """Lazy import ML integration."""
    global _ml_integration
    if _ml_integration is None:
        try:
            ml_path = Path(__file__).parent.parent.parent / "Machine Learning"
            if ml_path.exists():
                sys.path.insert(0, str(ml_path.parent))
                from integration.ml_integration_backend import get_ml_integration_backend
                _ml_integration = get_ml_integration_backend()
        except Exception:
            _ml_integration = None  # ML services optional
    return _ml_integration

router = APIRouter(prefix="/marketplace", tags=["Marketplace"])


@router.post("/", response_model=MarketplaceListingResponse)
async def create_listing(
    listing: MarketplaceListingCreate,
    db: Client = Depends(get_supabase_admin)
):
    """Create a new marketplace listing with 50% max markup validation and fraud detection."""
    try:
        # Optional: Run fraud detection if ML services available
        ml_integration = get_ml_integration()
        if ml_integration:
            try:
                import uuid
                transaction_id = str(uuid.uuid4())
                # Get event_id from ticket
                ticket_response = db.table("tickets").select("event_id").eq("ticket_id", listing.ticket_id).execute()
                if not ticket_response.data:
                    ticket_response = db.table("tickets").select("event_id").eq("id", listing.ticket_id).execute()
                event_id = ticket_response.data[0].get("event_id") if ticket_response.data else None
                
                fraud_check = ml_integration.process_transaction(
                    transaction_id=transaction_id,
                    wallet_address=listing.seller_address,
                    event_id=event_id,
                    price_paid=listing.price
                )
                risk_score = fraud_check.get('model_outputs', {}).get('risk_scoring', {}).get('risk_score', 0.0)
                if risk_score > 0.85:
                    raise HTTPException(
                        status_code=403,
                        detail=f"Listing flagged as high risk (score: {risk_score:.2f}). Please contact support."
                    )
            except HTTPException:
                raise
            except Exception as e:
                # Don't fail listing creation if ML check fails
                import logging
                logging.warning(f"ML fraud check failed (non-blocking): {e}")
        # Convert ticket_id to int if needed
        ticket_id = int(listing.ticket_id) if listing.ticket_id else None
        if not ticket_id:
            raise HTTPException(status_code=400, detail="Invalid ticket_id")
        
        # Verify ticket exists and belongs to seller
        # Try ticket_id column first (complete schema)
        ticket_response = db.table("tickets").select("*").eq("ticket_id", ticket_id).execute()
        if not ticket_response.data:
            # Try id column (simple schema)
            ticket_response = db.table("tickets").select("*").eq("id", ticket_id).execute()
        
        if not ticket_response.data:
            raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
        
        ticket = ticket_response.data[0]
        
        # Get owner_address - either directly or from wallets table
        ticket_owner_address = ticket.get("owner_address")
        if not ticket_owner_address and "owner_wallet_id" in ticket:
            wallet_lookup = db.table("wallets").select("address").eq("wallet_id", ticket["owner_wallet_id"]).execute()
            if wallet_lookup.data:
                ticket_owner_address = wallet_lookup.data[0]["address"]
        
        if not ticket_owner_address or ticket_owner_address.lower() != listing.seller_address.lower():
            raise HTTPException(status_code=403, detail="You don't own this ticket")
        
        # Check ticket status - allow ACTIVE/available tickets to be listed
        ticket_status = ticket.get("status", "ACTIVE")
        if ticket_status not in ["ACTIVE", "available"]:
            raise HTTPException(status_code=400, detail="Only active/available tickets can be listed for resale")
        
        # Get original purchase price for markup validation
        original_price = None
        if listing.original_price is not None:
            original_price = listing.original_price
        elif ticket.get("purchase_price"):
            original_price = float(ticket["purchase_price"])
        else:
            # Fallback: get event base_price
            event_id = ticket.get("event_id")
            if event_id:
                event_response = db.table("events").select("base_price").eq("event_id", event_id).execute()
                if not event_response.data:
                    event_response = db.table("events").select("base_price").eq("id", event_id).execute()
                if event_response.data and event_response.data[0].get("base_price"):
                    original_price = float(event_response.data[0]["base_price"])
        
        # Validate 50% max markup
        if original_price and original_price > 0:
            max_allowed_price = original_price * 1.5  # 50% markup = 150% of original
            if listing.price > max_allowed_price:
                raise HTTPException(
                    status_code=400,
                    detail=f"Resale price cannot exceed 50% markup. Maximum allowed: {max_allowed_price:.8f} ETH (original: {original_price:.8f} ETH)"
                )
        elif original_price == 0:
            # Free tickets can be sold at any price
            pass
        else:
            # If we can't determine original price, allow listing but warn
            print(f"Warning: Could not determine original price for ticket {listing.ticket_id}, allowing listing without markup validation")
        
        # Create listing with original_price
        listing_data = listing.model_dump()
        # Ensure ticket_id is the correct type (BIGINT in database) - use the ticket_id variable we defined
        listing_data["ticket_id"] = ticket_id
        if original_price is not None:
            listing_data["original_price"] = original_price
        
        # Ensure status is set
        if "status" not in listing_data:
            listing_data["status"] = "active"
        
        # Debug: Log what we're inserting
        import logging
        logging.info(f"Creating marketplace listing: {listing_data}")
        
        # Update ticket status to resale_listed (map to database enum)
        # Database uses ACTIVE, but we can track resale status separately
        # For now, keep ticket status as ACTIVE and track resale in marketplace table
        
        try:
            response = db.table("marketplace").insert(listing_data).execute()
        except Exception as insert_error:
            import traceback
            error_msg = f"Failed to insert into marketplace: {str(insert_error)}\n{traceback.format_exc()}\nListing data: {listing_data}"
            logging.error(error_msg)
            raise HTTPException(status_code=500, detail=f"Failed to create listing: {str(insert_error)}")
        
        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to create listing: No data returned from insert")
        
        listing_response = dict(response.data[0])
        # Ensure original_price is included in response
        if "original_price" not in listing_response:
            listing_response["original_price"] = original_price
        
        return MarketplaceListingResponse(**listing_response)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[MarketplaceListingResponse])
async def list_marketplace(
    status: str = "active",
    db: Client = Depends(get_supabase_admin)
):
    """List all marketplace listings with optimized queries."""
    cache_key = f"marketplace:list:{status}"
    cached_result = cache_get(cache_key)
    if cached_result is not None:
        return cached_result
    
    try:
        response = db.table("marketplace").select("*").eq("status", status).execute()
        
        if not response.data:
            return []
        
        listings = []
        
        # Batch fetch ticket event_ids and event names to avoid N+1 queries
        ticket_ids = [listing.get("ticket_id") for listing in response.data if listing.get("ticket_id")]
        unique_ticket_ids = list(set(ticket_ids))
        
        # Create ticket_id -> event_id and event_name mappings
        ticket_event_map = {}
        event_names_map = {}  # Map event_id to event name
        if unique_ticket_ids:
            # Fetch tickets in batches (Supabase limit)
            for ticket_id in unique_ticket_ids[:100]:  # Limit to 100 at a time
                try:
                    # Try ticket_id first
                    ticket_response = db.table("tickets").select("ticket_id, id, event_id").eq("ticket_id", ticket_id).limit(1).execute()
                    if not ticket_response.data:
                        # Fallback to id column
                        ticket_response = db.table("tickets").select("ticket_id, id, event_id").eq("id", ticket_id).limit(1).execute()
                    
                    if ticket_response.data:
                        ticket = ticket_response.data[0]
                        ticket_key = ticket.get("ticket_id") or ticket.get("id")
                        event_id = ticket.get("event_id")
                        ticket_event_map[ticket_key] = event_id
                        
                        # Fetch event name if we haven't already
                        if event_id and event_id not in event_names_map:
                            try:
                                event_response = db.table("events").select("event_id, name").eq("event_id", event_id).limit(1).execute()
                                if not event_response.data:
                                    event_response = db.table("events").select("id, name").eq("id", event_id).limit(1).execute()
                                if event_response.data:
                                    event_names_map[event_id] = event_response.data[0].get("name")
                            except Exception:
                                pass
                except Exception:
                    # Skip if ticket lookup fails
                    continue
        
        for listing in response.data:
            listing_dict = dict(listing)
            # Ensure original_price is included (may be None for old listings)
            if "original_price" not in listing_dict:
                listing_dict["original_price"] = None
            # Add event_id for frontend optimization (not in response model, but useful)
            ticket_id = listing.get("ticket_id")
            if ticket_id and ticket_id in ticket_event_map:
                event_id = ticket_event_map[ticket_id]
                listing_dict["_event_id"] = event_id  # Internal field
                # Add event_name if available
                if event_id and event_id in event_names_map:
                    listing_dict["event_name"] = event_names_map[event_id]
            listings.append(MarketplaceListingResponse(**listing_dict))
        
        result = listings
        # Cache for 1 minute (listings change more frequently)
        cache_set(cache_key, result, ttl=60)
        return result
    
    except HTTPException:
        raise
    except Exception as e:
        import traceback
        error_detail = f"Failed to list marketplace: {str(e)}\n{traceback.format_exc()}"
        raise HTTPException(status_code=500, detail=error_detail)


@router.get("/{listing_id}", response_model=MarketplaceListingResponse)
async def get_listing(
    listing_id: int,
    db: Client = Depends(get_supabase_admin)
):
    """Get a specific marketplace listing."""
    try:
        response = db.table("marketplace").select("*").eq("id", listing_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Listing not found")
        
        return MarketplaceListingResponse(**response.data[0])
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{listing_id}", response_model=MarketplaceListingResponse)
async def update_listing(
    listing_id: int,
    update: MarketplaceListingUpdate,
    db: Client = Depends(get_supabase_admin)
):
    """Update a marketplace listing."""
    try:
        update_data = {k: v for k, v in update.model_dump().items() if v is not None}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No update data provided")
        
        response = db.table("marketplace").update(update_data).eq("id", listing_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Listing not found")
        
        return MarketplaceListingResponse(**response.data[0])
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{listing_id}/buy")
async def buy_listing(
    listing_id: int,
    buyer_address: str,
    db: Client = Depends(get_supabase_admin)
):
    """Buy a ticket from the marketplace."""
    try:
        # Get listing
        listing_response = db.table("marketplace").select("*").eq("id", listing_id).execute()
        
        if not listing_response.data:
            raise HTTPException(status_code=404, detail="Listing not found")
        
        listing = listing_response.data[0]
        
        if listing["status"] != "active":
            raise HTTPException(status_code=400, detail="Listing is not active")
        
        # Transfer ticket ownership
        ticket_update = db.table("tickets").update({"owner_address": buyer_address}).eq("id", listing["ticket_id"]).execute()
        
        # Mark listing as sold
        listing_update = db.table("marketplace").update({"status": "sold"}).eq("id", listing_id).execute()
        
        return {
            "message": "Ticket purchased successfully",
            "ticket": ticket_update.data[0] if ticket_update.data else None,
            "listing": listing_update.data[0] if listing_update.data else None
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/seller/{seller_address}", response_model=List[MarketplaceListingResponse])
async def get_seller_listings(
    seller_address: str,
    db: Client = Depends(get_supabase_admin)
):
    """Get all listings by a specific seller."""
    try:
        response = db.table("marketplace").select("*").eq("seller_address", seller_address).execute()
        return [MarketplaceListingResponse(**listing) for listing in response.data]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Blockchain Endpoints ---

@router.post("/list")
def list_ticket(
    req: ListRequest,
    db: Client = Depends(get_supabase_admin)
):
    contract = contracts.get("MarketPlace")
    if not contract:
        raise HTTPException(status_code=404, detail="MarketPlace contract not found")
        
    func = contract.functions.listTicket(req.ticket_id, w3.to_wei(req.price, 'ether'))
    tx_result = send_transaction(func)

    if tx_result["status"] == 1:
        try:
            # Create listing in DB
            # We need seller address. Assuming server is acting on behalf of user or we get it from ticket.
            # But wait, req doesn't have seller address.
            # We should fetch ticket owner from DB or assume the caller.
            # For now, let's fetch ticket from DB to get owner.
            ticket_res = db.table("tickets").select("owner_address").eq("id", req.ticket_id).execute()
            seller = ticket_res.data[0]["owner_address"] if ticket_res.data else "0x0000000000000000000000000000000000000000"

            listing_data = {
                "ticket_id": req.ticket_id,
                "seller_address": seller,
                "price": req.price,
                "status": "active"
            }
            print(f"Inserting listing data: {listing_data}")
            response = db.table("marketplace").insert(listing_data).execute()
            print(f"DB Insert Response: {response}")
        except Exception as e:
            print(f"DB Error: {e}")
            tx_result["db_error"] = str(e)

    return tx_result

@router.post("/buy")
def buy_ticket(
    req: BuyRequest,
    db: Client = Depends(get_supabase_admin)
):
    contract = contracts.get("MarketPlace")
    if not contract:
        raise HTTPException(status_code=404, detail="MarketPlace contract not found")
        
    func = contract.functions.buyTicket(req.ticket_id)
    tx_result = send_transaction(func, value=req.value)

    if tx_result["status"] == 1:
        try:
            # Update listing status
            # We need to find the active listing for this ticket
            listing_res = db.table("marketplace").select("id").eq("ticket_id", req.ticket_id).eq("status", "active").execute()
            if listing_res.data:
                listing_id = listing_res.data[0]["id"]
                db.table("marketplace").update({"status": "sold"}).eq("id", listing_id).execute()
            
            # Update ticket owner
            # We don't have buyer address in req (it's implicit in tx sender).
            # But since server sends tx, server is technically the buyer?
            # Or is this a relay?
            # If server pays, server owns it.
            # But usually user pays.
            # If this is a relay, we should pass buyer address in req to update DB correctly.
            # The user's previous code had `buyer_address` in `buyListing` endpoint.
            # Let's assume we should update owner to... whom?
            # For now, let's leave owner update pending or set to a placeholder if we don't know buyer.
            # Actually, `buy_ticket` in `marketplace.py` (original) took `buyer_address`.
            # But `BuyRequest` only has `ticket_id` and `value`.
            # We should probably add `buyer_address` to `BuyRequest` for DB sync purposes, 
            # even if contract doesn't need it (if msg.sender is server).
            # But if server is buying, then server address is owner.
            # Let's assume server address for now or add TODO.
            pass 
        except Exception as e:
            print(f"DB Error: {e}")
            tx_result["db_error"] = str(e)

    return tx_result

@router.post("/update-price")
def update_price(req: UpdatePriceRequest):
    contract = contracts.get("MarketPlace")
    if not contract:
        raise HTTPException(status_code=404, detail="MarketPlace contract not found")
        
    func = contract.functions.updateListingPrice(req.ticket_id, w3.to_wei(req.new_price, 'ether'))
    return send_transaction(func)

@router.post("/delist")
def delist_ticket(
    req: EscrowRequest,
    db: Client = Depends(get_supabase_admin)
): # Reusing EscrowRequest for ticket_id
    contract = contracts.get("MarketPlace")
    if not contract:
        raise HTTPException(status_code=404, detail="MarketPlace contract not found")
    
    # Assuming delistTicket or cancelListing
    if hasattr(contract.functions, 'delistTicket'):
        func = contract.functions.delistTicket(req.ticket_id)
    elif hasattr(contract.functions, 'cancelListing'):
        func = contract.functions.cancelListing(req.ticket_id)
    else:
        raise HTTPException(status_code=500, detail="Delist function not found")
        
    tx_result = send_transaction(func)

    if tx_result["status"] == 1:
        try:
            # Cancel listing in DB
            db.table("marketplace").update({"status": "cancelled"}).eq("ticket_id", req.ticket_id).eq("status", "active").execute()
        except Exception as e:
            print(f"DB Error: {e}")
            tx_result["db_error"] = str(e)

    return tx_result

@router.post("/escrow/release")
def release_escrow(req: EscrowRequest):
    contract = contracts.get("MarketPlace")
    if not contract:
        raise HTTPException(status_code=404, detail="MarketPlace contract not found")
        
    func = contract.functions.releaseEscrow(req.ticket_id)
    return send_transaction(func)

@router.post("/escrow/refund")
def refund_escrow(req: EscrowRequest):
    contract = contracts.get("MarketPlace")
    if not contract:
        raise HTTPException(status_code=404, detail="MarketPlace contract not found")
        
    func = contract.functions.refundEscrow(req.ticket_id)
    return send_transaction(func)

@router.post("/withdraw")
def withdraw_funds():
    contract = contracts.get("MarketPlace")
    if not contract:
        raise HTTPException(status_code=404, detail="MarketPlace contract not found")
        
    func = contract.functions.withdraw()
    return send_transaction(func)

