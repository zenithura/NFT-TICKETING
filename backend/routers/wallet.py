"""Wallet connection router for Web3 wallet syncing."""
from fastapi import APIRouter, HTTPException, Depends
from supabase import Client
from database import get_supabase_admin
from models import WalletAuthRequest

router = APIRouter(prefix="/wallet", tags=["Wallet"])


@router.post("/connect")
async def connect_wallet(
    wallet_data: WalletAuthRequest,
    db: Client = Depends(get_supabase_admin)
):
    """
    Connect wallet and optionally create/update user record.
    This is optional - wallet connection works without this endpoint.
    """
    try:
        address = wallet_data.address.lower()
        
        # Check if user exists with this wallet address
        user_response = db.table("users").select("*").eq("wallet_address", address).execute()
        
        if user_response.data:
            # User exists, return success
            return {
                "success": True,
                "message": "Wallet connected",
                "user": user_response.data[0]
            }
        else:
            # User doesn't exist, but that's okay - wallet connection still works
            # Optionally create a minimal user record
            return {
                "success": True,
                "message": "Wallet connected (no user record found)",
                "address": address
            }
    
    except Exception as e:
        # Don't fail - wallet connection should work even if backend fails
        return {
            "success": True,
            "message": "Wallet connected (backend sync skipped)",
            "error": str(e)
        }

