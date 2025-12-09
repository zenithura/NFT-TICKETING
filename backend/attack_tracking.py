"""
Attack tracking and auto-suspension system.
Tracks attack attempts per user and automatically suspends/bans based on thresholds.
"""
import logging
from typing import Optional
from datetime import datetime, timezone, timedelta
from supabase import Client

from database import get_supabase_admin
from logging_system import get_logging_system, LogType, LogLevel

logger = logging.getLogger(__name__)

# Attack types that count toward suspension/ban
ATTACK_TYPES = [
    'XSS',
    'SQL_INJECTION',
    'COMMAND_INJECTION',
    'BRUTE_FORCE',
    'UNAUTHORIZED_ACCESS',
    'API_ABUSE',
    'RATE_LIMIT_EXCEEDED',
    'PENETRATION_TEST',
]

# Thresholds
SUSPENSION_THRESHOLD = 2  # 2+ attacks → suspend
BAN_THRESHOLD = 10  # 10+ attacks → ban permanently


async def track_attack_and_check_suspension(
    db: Client,
    user_id: Optional[int],
    ip_address: str,
    attack_type: str,
    alert_id: Optional[int] = None,
):
    """Track attack attempt and check if user should be suspended or banned.
    
    Args:
        db: Database client
        user_id: User ID if authenticated
        ip_address: IP address
        attack_type: Type of attack detected
        alert_id: Security alert ID
    
    Returns:
        dict with action taken: None, 'suspended', or 'banned'
    """
    if attack_type not in ATTACK_TYPES:
        return {"action": None}
    
    action_taken = None
    
    try:
        # Only track attacks for authenticated users
        if user_id:
            # Count total attack attempts for this user
            attack_count_result = db.table("security_alerts").select(
                "alert_id", count="exact"
            ).eq("user_id", user_id).in_("attack_type", ATTACK_TYPES).execute()
            
            attack_count = attack_count_result.count or 0
            
            # Get current user status
            user_result = db.table("users").select("is_active, role").eq("user_id", user_id).execute()
            if not user_result.data:
                return {"action": None}
            
            user = user_result.data[0]
            is_active = user.get("is_active", True)
            user_role = user.get("role", "")
            
            # Skip if user is already banned or is an admin
            if user_role == "ADMIN":
                return {"action": None}
            
            # Check if user should be banned (10+ attacks)
            if attack_count >= BAN_THRESHOLD and is_active:
                # Ban user permanently
                ban_data = {
                    "user_id": user_id,
                    "ban_type": "USER",
                    "ban_reason": f"Auto-banned: {attack_count} attack attempts detected",
                    "ban_duration": "PERMANENT",
                    "is_active": True,
                    "created_at": datetime.now(timezone.utc).isoformat(),
                }
                db.table("bans").insert(ban_data).execute()
                
                # Deactivate user account
                db.table("users").update({
                    "is_active": False,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }).eq("user_id", user_id).execute()
                
                action_taken = "banned"
                
                # Log admin action (system action)
                logging_system = get_logging_system()
                logging_system.log_event(
                    log_type=LogType.USER_SUSPENDED,
                    message=f"User {user_id} auto-banned due to {attack_count} attack attempts",
                    log_level=LogLevel.WARNING,
                    user_id=user_id,
                    ip_address=ip_address,
                    metadata={
                        "attack_count": attack_count,
                        "attack_type": attack_type,
                        "alert_id": alert_id,
                        "auto_action": "banned",
                    },
                )
                
                logger.warning(f"Auto-banned user {user_id} due to {attack_count} attack attempts")
            
            # Check if user should be suspended (2+ attacks but < 10)
            elif attack_count >= SUSPENSION_THRESHOLD and attack_count < BAN_THRESHOLD and is_active:
                # Suspend user (set is_active to False)
                db.table("users").update({
                    "is_active": False,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }).eq("user_id", user_id).execute()
                
                action_taken = "suspended"
                
                # Log admin action (system action)
                logging_system = get_logging_system()
                logging_system.log_event(
                    log_type=LogType.USER_SUSPENDED,
                    message=f"User {user_id} auto-suspended due to {attack_count} attack attempts",
                    log_level=LogLevel.WARNING,
                    user_id=user_id,
                    ip_address=ip_address,
                    metadata={
                        "attack_count": attack_count,
                        "attack_type": attack_type,
                        "alert_id": alert_id,
                        "auto_action": "suspended",
                    },
                )
                
                logger.warning(f"Auto-suspended user {user_id} due to {attack_count} attack attempts")
        
        # For unauthenticated attacks, try to find user by email from alert metadata
        # This allows blocking by email account even for login attempts
        if not user_id and attack_type in ['BRUTE_FORCE', 'SQL_INJECTION', 'XSS']:
            # Try to find user by email from recent alerts with same IP
            try:
                recent_alert = db.table("security_alerts").select(
                    "metadata, user_id"
                ).eq("ip_address", ip_address).in_("attack_type", ATTACK_TYPES).order(
                    "created_at", desc=True
                ).limit(1).execute()
                
                if recent_alert.data:
                    alert_data = recent_alert.data[0]
                    metadata = alert_data.get("metadata")
                    
                    # Try to extract email from metadata
                    if isinstance(metadata, str):
                        import json
                        try:
                            metadata = json.loads(metadata)
                        except:
                            pass
                    
                    if isinstance(metadata, dict):
                        email = metadata.get("email") or metadata.get("username")
                        if email:
                            # Look up user by email
                            user_lookup = db.table("users").select("user_id, role").eq("email", email.lower()).limit(1).execute()
                            if user_lookup.data:
                                found_user = user_lookup.data[0]
                                found_user_id = found_user.get("user_id")
                                found_role = found_user.get("role", "")
                                
                                # Skip if admin
                                if found_role != "ADMIN":
                                    # Recursively call with found user_id
                                    return await track_attack_and_check_suspension(
                                        db, found_user_id, ip_address, attack_type, alert_id
                                    )
            except Exception as lookup_error:
                logger.error(f"Error looking up user by email: {lookup_error}")
        
        # IP-based tracking (fallback for truly unauthenticated attacks)
        # Only ban IP if we can't find a user account
        if not user_id:
            twenty_four_hours_ago = datetime.now(timezone.utc) - timedelta(hours=24)
            ip_attack_count = db.table("security_alerts").select(
                "alert_id", count="exact"
            ).eq("ip_address", ip_address).in_("attack_type", ATTACK_TYPES).gte(
                "created_at", twenty_four_hours_ago.isoformat()
            ).execute()
            
            ip_count = ip_attack_count.count or 0
            
            # Auto-ban IP if 10+ attacks in 24 hours (only if no user found)
            if ip_count >= BAN_THRESHOLD:
                existing_ban = db.table("bans").select("ban_id").eq("ip_address", ip_address).eq("is_active", True).execute()
                
                if not existing_ban.data:
                    ban_data = {
                        "ip_address": ip_address,
                        "ban_type": "IP",
                        "ban_reason": f"Auto-banned: {ip_count} attack attempts from IP in 24 hours",
                        "ban_duration": "PERMANENT",
                        "is_active": True,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    }
                    db.table("bans").insert(ban_data).execute()
                    
                    logger.warning(f"Auto-banned IP {ip_address} due to {ip_count} attack attempts")
        
        return {
            "action": action_taken,
            "attack_count": attack_count if user_id else 0,
            "user_id": user_id,
            "ip_address": ip_address,
        }
        
    except Exception as e:
        logger.error(f"Error tracking attack and checking suspension: {e}", exc_info=True)
        return {"action": None, "error": str(e)}


def get_user_attack_count(db: Client, user_id: int) -> int:
    """Get total attack count for a user."""
    try:
        result = db.table("security_alerts").select(
            "alert_id", count="exact"
        ).eq("user_id", user_id).in_("attack_type", ATTACK_TYPES).execute()
        
        return result.count or 0
    except Exception as e:
        logger.error(f"Error getting user attack count: {e}")
        return 0


def get_ip_attack_count(db: Client, ip_address: str, hours: int = 24) -> int:
    """Get attack count for an IP address in the last N hours."""
    try:
        cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
        result = db.table("security_alerts").select(
            "alert_id", count="exact"
        ).eq("ip_address", ip_address).in_("attack_type", ATTACK_TYPES).gte(
            "created_at", cutoff.isoformat()
        ).execute()
        
        return result.count or 0
    except Exception as e:
        logger.error(f"Error getting IP attack count: {e}")
        return 0

