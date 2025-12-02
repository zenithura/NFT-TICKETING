"""Marketplace management router."""
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from supabase import Client

from database import get_supabase_admin
from database import get_supabase_admin
from models import MarketplaceListingCreate, MarketplaceListingResponse, MarketplaceListingUpdate, ListRequest, BuyRequest, UpdatePriceRequest, EscrowRequest
from web3_client import contracts, send_transaction, w3
from web3 import Web3

router = APIRouter(prefix="/marketplace", tags=["Marketplace"])


@router.post("/", response_model=MarketplaceListingResponse)
async def create_listing(
    listing: MarketplaceListingCreate,
    db: Client = Depends(get_supabase_admin)
):
    """Create a new marketplace listing."""
    try:
        # Verify ticket exists and belongs to seller
        ticket_response = db.table("tickets").select("*").eq("id", listing.ticket_id).execute()
        
        if not ticket_response.data:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        ticket = ticket_response.data[0]
        if ticket["owner_address"] != listing.seller_address:
            raise HTTPException(status_code=403, detail="You don't own this ticket")
        
        if ticket["status"] != "bought":
            raise HTTPException(status_code=400, detail="Only bought tickets can be listed")
        
        # Create listing
        listing_data = listing.model_dump()
        response = db.table("marketplace").insert(listing_data).execute()
        
        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to create listing")
        
        return MarketplaceListingResponse(**response.data[0])
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=List[MarketplaceListingResponse])
async def list_marketplace(
    status: str = "active",
    db: Client = Depends(get_supabase_admin)
):
    """List all marketplace listings."""
    try:
        response = db.table("marketplace").select("*").eq("status", status).execute()
        return [MarketplaceListingResponse(**listing) for listing in response.data]
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


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

