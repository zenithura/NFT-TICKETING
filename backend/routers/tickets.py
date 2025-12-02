"""Tickets management router."""
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from supabase import Client

from database import get_supabase_admin
from database import get_supabase_admin
from models import TicketCreate, TicketResponse, MintRequest, ValidatorRequest, ValidateRequest
from web3_client import contracts, send_transaction, w3, account
from web3 import Web3

router = APIRouter(prefix="/tickets", tags=["Tickets"])



@router.get("/server-address")
def get_server_address():
    """Get the server's wallet address."""
    if account:
        return {"address": account.address}
    return {"address": None}

@router.post("/", response_model=TicketResponse)
async def create_ticket(
    ticket: TicketCreate,
    db: Client = Depends(get_supabase_admin)
):
    """Create/mint a new ticket."""
    try:
        # Verify event exists - try event_id first, then id
        event_response = db.table("events").select("*").eq("event_id", ticket.event_id).execute()
        
        if not event_response.data:
            # Try with id field as fallback
            event_response = db.table("events").select("*").eq("id", ticket.event_id).execute()
        
        if not event_response.data:
            raise HTTPException(status_code=404, detail="Event not found")
        
        event = event_response.data[0]
        event_id_actual = event.get("event_id") or event.get("id")
        
        # Check if tickets are still available
        total_supply = event.get("total_supply", 0)
        available_tickets = event.get("available_tickets", total_supply)
        
        if available_tickets <= 0:
            raise HTTPException(status_code=400, detail="No tickets available for this event")
        
        # Get or create wallet entry
        wallet_response = db.table("wallets").select("wallet_id").eq("address", ticket.owner_address).execute()
        
        if wallet_response.data:
            wallet_id = wallet_response.data[0]["wallet_id"]
        else:
            # Create new wallet entry
            wallet_insert = db.table("wallets").insert({
                "address": ticket.owner_address,
                "balance": 0,
                "allowlist_status": False,
                "blacklisted": False
            }).execute()
            
            if not wallet_insert.data:
                raise HTTPException(status_code=500, detail="Failed to create wallet entry")
            wallet_id = wallet_insert.data[0]["wallet_id"]
        
        # Map frontend status to database enum
        # Frontend: "available", "bought", "used"
        # Database: "ACTIVE", "USED", "TRANSFERRED", "REVOKED"
        status_map = {
            "available": "ACTIVE",
            "bought": "ACTIVE",  # Bought tickets are still active
            "used": "USED"
        }
        db_status = status_map.get(ticket.status, "ACTIVE")
        
        # Create ticket - try complete schema first (owner_wallet_id)
        ticket_data = {
            "event_id": event_id_actual,
            "owner_wallet_id": wallet_id,
            "status": db_status,
        }
        
        # Store purchase_price if provided (for resale markup validation)
        if hasattr(ticket, 'purchase_price') and ticket.purchase_price is not None:
            ticket_data["purchase_price"] = float(ticket.purchase_price)
        elif hasattr(event, 'base_price') and event.get("base_price"):
            # If no purchase_price provided, use event base_price as fallback
            ticket_data["purchase_price"] = float(event.get("base_price", 0))
        
        # Generate token_id if not provided (required in complete schema)
        # Use a numeric token_id for better compatibility
        if ticket.nft_token_id:
            ticket_data["token_id"] = str(ticket.nft_token_id)
        else:
            # Generate a unique numeric token_id based on timestamp
            import time
            import random
            # Use timestamp in milliseconds + random to ensure uniqueness
            numeric_token_id = int(time.time() * 1000) * 10000 + random.randint(1000, 9999)
            ticket_data["token_id"] = str(numeric_token_id)
        
        try:
            response = db.table("tickets").insert(ticket_data).execute()
        except Exception as e:
            # Fallback to simple schema (owner_address) if complete schema fails
            error_str = str(e).lower()
            if "owner_wallet_id" in error_str or "column" in error_str or "not found" in error_str:
                # Fallback to simple schema - use string status
                ticket_data = {
                    "event_id": event_id_actual,
                    "owner_address": ticket.owner_address,
                    "status": ticket.status or "available",
                }
                if ticket.nft_token_id:
                    ticket_data["nft_token_id"] = ticket.nft_token_id
                # Store purchase_price if provided (for simple schema)
                if hasattr(ticket, 'purchase_price') and ticket.purchase_price is not None:
                    ticket_data["purchase_price"] = float(ticket.purchase_price)
                elif hasattr(event, 'base_price') and event.get("base_price"):
                    ticket_data["purchase_price"] = float(event.get("base_price", 0))
                response = db.table("tickets").insert(ticket_data).execute()
            else:
                raise
        
        if not response.data:
            raise HTTPException(status_code=500, detail="Failed to create ticket")
        
        created_ticket = response.data[0]
        
        # Decrement available tickets count
        new_available = max(0, available_tickets - 1)
        db.table("events").update({"available_tickets": new_available}).eq("event_id", event_id_actual).execute()
        
        # Map database response to TicketResponse model
        # Handle both ticket_id and id field names
        ticket_id = created_ticket.get("ticket_id") or created_ticket.get("id")
        
        # Get owner_address - either directly or from wallets table
        owner_address = created_ticket.get("owner_address")
        if not owner_address and "owner_wallet_id" in created_ticket:
            # Join with wallets table to get address
            wallet_lookup = db.table("wallets").select("address").eq("wallet_id", created_ticket["owner_wallet_id"]).execute()
            if wallet_lookup.data:
                owner_address = wallet_lookup.data[0]["address"]
        
        # Map database status back to frontend format
        # Database: "ACTIVE", "USED", "TRANSFERRED", "REVOKED"
        # Frontend: "available", "bought", "used"
        db_status = created_ticket.get("status", "ACTIVE")
        status_map_back = {
            "ACTIVE": "available",
            "USED": "used",
            "TRANSFERRED": "bought",
            "REVOKED": "used"
        }
        frontend_status = status_map_back.get(db_status, "available")
        
        # Handle nft_token_id - it should be an integer or None
        # token_id from database is a string, try to parse it or use None
        nft_token_id = None
        token_id_value = created_ticket.get("nft_token_id") or created_ticket.get("token_id")
        if token_id_value:
            # Try to parse as integer if it's numeric, otherwise use None
            try:
                # If it's already an integer, use it
                if isinstance(token_id_value, int):
                    nft_token_id = token_id_value
                # If it's a numeric string, parse it
                elif isinstance(token_id_value, str):
                    # Try to parse as integer
                    if token_id_value.isdigit():
                        nft_token_id = int(token_id_value)
                    # If it's a string like "ticket_123_456", extract numeric part
                    elif token_id_value.startswith("ticket_"):
                        # Extract the first number after "ticket_"
                        parts = token_id_value.split("_")
                        if len(parts) >= 2:
                            try:
                                nft_token_id = int(parts[1])
                            except (ValueError, IndexError):
                                nft_token_id = None
                    else:
                        nft_token_id = None
                else:
                    nft_token_id = None
            except (ValueError, TypeError):
                nft_token_id = None
        
        ticket_response_data = {
            "id": ticket_id,
            "event_id": created_ticket.get("event_id"),
            "owner_address": owner_address or ticket.owner_address,
            "status": frontend_status,
            "nft_token_id": nft_token_id,
            "created_at": created_ticket.get("created_at")
        }
        
        return TicketResponse(**ticket_response_data)
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/user/{owner_address}", response_model=List[TicketResponse])
async def get_user_tickets(
    owner_address: str,
    db: Client = Depends(get_supabase_admin)
):
    """Get all tickets owned by a specific user."""
    try:
        # Try to find wallet first (for complete schema)
        wallet_response = db.table("wallets").select("wallet_id").eq("address", owner_address).execute()
        
        if wallet_response.data:
            # Use owner_wallet_id (complete schema)
            wallet_id = wallet_response.data[0]["wallet_id"]
            response = db.table("tickets").select("*").eq("owner_wallet_id", wallet_id).execute()
        else:
            # Try owner_address directly (simple schema)
            response = db.table("tickets").select("*").eq("owner_address", owner_address).execute()
        
        # Map database response to TicketResponse model
        tickets = []
        for ticket in response.data:
            ticket_id = ticket.get("ticket_id") or ticket.get("id")
            
            # Get owner_address - either directly or from wallets table
            ticket_owner_address = ticket.get("owner_address")
            if not ticket_owner_address and "owner_wallet_id" in ticket:
                wallet_lookup = db.table("wallets").select("address").eq("wallet_id", ticket["owner_wallet_id"]).execute()
                if wallet_lookup.data:
                    ticket_owner_address = wallet_lookup.data[0]["address"]
            
            # Map database status to frontend format
            db_status = ticket.get("status", "ACTIVE")
            status_map_back = {
                "ACTIVE": "available",
                "USED": "used",
                "TRANSFERRED": "bought",
                "REVOKED": "used"
            }
            frontend_status = status_map_back.get(db_status, "available")
            
            # Handle nft_token_id - parse from token_id if needed
            nft_token_id = None
            token_id_value = ticket.get("nft_token_id") or ticket.get("token_id")
            if token_id_value:
                try:
                    if isinstance(token_id_value, int):
                        nft_token_id = token_id_value
                    elif isinstance(token_id_value, str) and token_id_value.isdigit():
                        nft_token_id = int(token_id_value)
                except (ValueError, TypeError):
                    nft_token_id = None
            
            tickets.append(TicketResponse(
                id=ticket_id,
                event_id=ticket.get("event_id"),
                owner_address=ticket_owner_address or owner_address,
                status=frontend_status,
                nft_token_id=nft_token_id,
                created_at=ticket.get("created_at")
            ))
        
        return tickets
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/event/{event_id}", response_model=List[TicketResponse])
async def get_event_tickets(
    event_id: int,
    db: Client = Depends(get_supabase_admin)
):
    """Get all tickets for a specific event."""
    try:
        response = db.table("tickets").select("*").eq("event_id", event_id).execute()
        
        # Map database response to TicketResponse model
        tickets = []
        for ticket in response.data:
            ticket_id = ticket.get("ticket_id") or ticket.get("id")
            # Map database status to frontend format
            db_status = ticket.get("status", "ACTIVE")
            status_map_back = {
                "ACTIVE": "available",
                "USED": "used",
                "TRANSFERRED": "bought",
                "REVOKED": "used"
            }
            frontend_status = status_map_back.get(db_status, "available")
            
            # Handle nft_token_id - parse from token_id if needed
            nft_token_id = None
            token_id_value = ticket.get("nft_token_id") or ticket.get("token_id")
            if token_id_value:
                try:
                    if isinstance(token_id_value, int):
                        nft_token_id = token_id_value
                    elif isinstance(token_id_value, str) and token_id_value.isdigit():
                        nft_token_id = int(token_id_value)
                except (ValueError, TypeError):
                    nft_token_id = None
            
            tickets.append(TicketResponse(
                id=ticket_id,
                event_id=ticket.get("event_id"),
                owner_address=ticket.get("owner_address"),
                status=frontend_status,
                nft_token_id=nft_token_id,
                created_at=ticket.get("created_at")
            ))
        
        return tickets
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{ticket_id}", response_model=TicketResponse)
async def get_ticket(
    ticket_id: int,
    db: Client = Depends(get_supabase_admin)
):
    """Get a specific ticket by ID."""
    try:
        # Try ticket_id first, then id
        response = db.table("tickets").select("*").eq("ticket_id", ticket_id).execute()
        
        if not response.data:
            response = db.table("tickets").select("*").eq("id", ticket_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        ticket = response.data[0]
        ticket_id_actual = ticket.get("ticket_id") or ticket.get("id")
        
        # Map database status to frontend format
        db_status = ticket.get("status", "ACTIVE")
        status_map_back = {
            "ACTIVE": "available",
            "USED": "used",
            "TRANSFERRED": "bought",
            "REVOKED": "used"
        }
        frontend_status = status_map_back.get(db_status, "available")
        
        # Handle nft_token_id - parse from token_id if needed
        nft_token_id = None
        token_id_value = ticket.get("nft_token_id") or ticket.get("token_id")
        if token_id_value:
            try:
                if isinstance(token_id_value, int):
                    nft_token_id = token_id_value
                elif isinstance(token_id_value, str) and token_id_value.isdigit():
                    nft_token_id = int(token_id_value)
            except (ValueError, TypeError):
                nft_token_id = None
        
        return TicketResponse(
            id=ticket_id_actual,
            event_id=ticket.get("event_id"),
            owner_address=ticket.get("owner_address"),
            status=frontend_status,
            nft_token_id=nft_token_id,
            created_at=ticket.get("created_at")
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{ticket_id}/transfer")
async def transfer_ticket(
    ticket_id: int,
    new_owner_address: str,
    db: Client = Depends(get_supabase_admin)
):
    """Transfer ticket to a new owner."""
    try:
        response = db.table("tickets").update({"owner_address": new_owner_address}).eq("id", ticket_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        return {"message": "Ticket transferred successfully", "ticket": response.data[0]}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.patch("/{ticket_id}/use")
async def use_ticket(
    ticket_id: int,
    db: Client = Depends(get_supabase_admin)
):
    """Mark ticket as used."""
    try:
        # Map frontend "used" to database "USED"
        response = db.table("tickets").update({"status": "USED"}).eq("id", ticket_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Ticket not found")
        
        return {"message": "Ticket marked as used", "ticket": response.data[0]}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.post("/approve-marketplace")
def approve_marketplace():
    """Approve the marketplace contract to transfer tickets."""
    nft_contract = contracts.get("NFT_TICKET")
    marketplace_contract = contracts.get("MarketPlace")
    
    if not nft_contract or not marketplace_contract:
        raise HTTPException(status_code=404, detail="Contracts not found")
        
    # Check for setApprovalForAll
    if hasattr(nft_contract.functions, 'setApprovalForAll'):
        func = nft_contract.functions.setApprovalForAll(marketplace_contract.address, True)
    else:
        raise HTTPException(status_code=500, detail="setApprovalForAll not found")
        
    return send_transaction(func)


# --- Blockchain Endpoints ---


@router.post("/mint")
def mint_ticket(
    req: MintRequest,
    db: Client = Depends(get_supabase_admin)
):
    contract = contracts.get("NFT_TICKET")
    if not contract:
        raise HTTPException(status_code=404, detail="NFT_TICKET contract not found")
        
    # Check for 'mint' or 'createTicket'
    if hasattr(contract.functions, 'mint'):
        func = contract.functions.mint(Web3.to_checksum_address(req.to_address), req.event_id, req.token_uri)
    elif hasattr(contract.functions, 'createTicket'):
        func = contract.functions.createTicket(req.token_uri, w3.to_wei(req.price, 'ether'))
    else:
        # Fallback or error if neither exists, but let's assume one does based on user intent
        raise HTTPException(status_code=500, detail="Mint function not found in ABI")

    tx_result = send_transaction(func)
    
    if tx_result["status"] == 1:
        # Transaction successful, save to DB
        try:
            # Fetch receipt to get Token ID
            try:
                receipt = w3.eth.get_transaction_receipt(tx_result["tx_hash"])
                # Assuming Transfer(from, to, tokenId) event
                # We need to find the log from the NFT contract
                logs = contract.events.Transfer().process_receipt(receipt)
                if logs:
                    token_id = logs[0]['args']['tokenId']
                    print(f"Minted Token ID: {token_id}")
                else:
                    print("No Transfer logs found in receipt")
                    token_id = None
            except Exception as e:
                print(f"Error parsing logs: {e}")
                token_id = None

            ticket_data = {
                "event_id": req.event_id,
                "owner_address": req.to_address,
                "status": "available",
                "nft_token_id": token_id
            }
            print(f"Inserting ticket data: {ticket_data}")
            response = db.table("tickets").insert(ticket_data).execute()
            print(f"DB Insert Response: {response}")
        except Exception as e:
            print(f"DB Error: {e}")
            # Don't fail the request if DB fails, but maybe log it?
            # Or should we fail? User wants it in DB.
            # Let's include a warning in response.
            tx_result["db_error"] = str(e)
            
    return tx_result

@router.post("/validators/add")
def add_validator(req: ValidatorRequest):
    contract = contracts.get("NFT_TICKET")
    val_contract = contracts.get("TicketValidator")
    
    if contract and hasattr(contract.functions, 'addValidator'):
        func = contract.functions.addValidator(req.validator_address)
    elif val_contract and hasattr(val_contract.functions, 'addValidator'):
        func = val_contract.functions.addValidator(req.validator_address)
    else:
         raise HTTPException(status_code=500, detail="addValidator function not found")
             
    return send_transaction(func)

@router.post("/validators/remove")
def remove_validator(req: ValidatorRequest):
    contract = contracts.get("NFT_TICKET")
    val_contract = contracts.get("TicketValidator")
    
    if contract and hasattr(contract.functions, 'removeValidator'):
        func = contract.functions.removeValidator(req.validator_address)
    elif val_contract and hasattr(val_contract.functions, 'removeValidator'):
        func = val_contract.functions.removeValidator(req.validator_address)
    else:
        raise HTTPException(status_code=500, detail="removeValidator function not found")
        
    return send_transaction(func)

@router.post("/validate")
def validate_ticket(req: ValidateRequest):
    contract = contracts.get("NFT_TICKET")
    val_contract = contracts.get("TicketValidator")
    
    target_contract = val_contract if val_contract else contract
    if not target_contract:
        raise HTTPException(status_code=404, detail="Contract not found")

    if hasattr(target_contract.functions, 'validateTicket'):
        func = target_contract.functions.validateTicket(req.ticket_id)
        return send_transaction(func)
    else:
         raise HTTPException(status_code=500, detail="validateTicket function not found")

