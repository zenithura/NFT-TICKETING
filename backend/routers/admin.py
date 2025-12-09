"""Admin dashboard and security alerts management router."""
from fastapi import APIRouter, HTTPException, Depends, Query, status, Request
from fastapi.responses import StreamingResponse
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta, timezone
from supabase import Client
from pydantic import BaseModel, Field

from database import get_supabase_admin
from auth_middleware import require_role, get_current_user
from routers.admin_auth import require_admin_auth
from models import UserResponse
from logging_system import get_logging_system, LogType, LogLevel
from soar_integration import get_soar_integration, SOAREvent, SOAREventType
from attack_tracking import get_user_attack_count, get_ip_attack_count
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])


# Pydantic models
class AlertResponse(BaseModel):
    alert_id: int
    user_id: Optional[int] = None
    ip_address: str
    attack_type: str
    payload: Optional[str] = None
    endpoint: str
    severity: str
    risk_score: int
    status: str
    user_agent: Optional[str] = None
    country_code: Optional[str] = None
    city: Optional[str] = None
    created_at: str
    reviewed_at: Optional[str] = None
    reviewed_by: Optional[int] = None


class AlertUpdate(BaseModel):
    status: str = Field(..., description="New status: REVIEWED, IGNORED, BANNED, FALSE_POSITIVE")


class BanRequest(BaseModel):
    user_id: Optional[int] = None
    ip_address: Optional[str] = None
    ban_reason: str
    ban_duration: str = Field(default="PERMANENT", description="TEMPORARY or PERMANENT")
    expires_hours: Optional[int] = Field(None, description="Hours until expiration (for temporary bans)")
    notes: Optional[str] = None


class UnbanRequest(BaseModel):
    user_id: Optional[int] = None
    ip_address: Optional[str] = None


class AdminStatsResponse(BaseModel):
    total_users: int
    total_alerts_24h: int
    total_alerts_7d: int
    total_alerts_30d: int
    critical_alerts_24h: int
    banned_users: int
    banned_ips: int
    system_health: str


class GraphDataResponse(BaseModel):
    alerts_by_type: dict
    alerts_by_severity: dict
    alerts_timeline: List[dict]
    top_attacking_ips: List[dict]
    top_attacked_endpoints: List[dict]


@router.get("/stats", response_model=AdminStatsResponse)
async def get_admin_stats(
    admin: dict = Depends(require_admin_auth),
    db: Client = Depends(get_supabase_admin)
):
    """Get admin dashboard statistics."""
    try:
        now = datetime.now(timezone.utc)
        
        # Total users
        users_count = db.table("users").select("user_id", count="exact").execute()
        total_users = users_count.count or 0
        
        # Alerts in last 24h
        alerts_24h = db.table("security_alerts").select("alert_id", count="exact").gte(
            "created_at", (now - timedelta(hours=24)).isoformat()
        ).execute()
        total_alerts_24h = alerts_24h.count or 0
        
        # Critical alerts in last 24h
        critical_24h = db.table("security_alerts").select("alert_id", count="exact").gte(
            "created_at", (now - timedelta(hours=24)).isoformat()
        ).eq("severity", "CRITICAL").execute()
        critical_alerts_24h = critical_24h.count or 0
        
        # Alerts in last 7 days
        alerts_7d = db.table("security_alerts").select("alert_id", count="exact").gte(
            "created_at", (now - timedelta(days=7)).isoformat()
        ).execute()
        total_alerts_7d = alerts_7d.count or 0
        
        # Alerts in last 30 days
        alerts_30d = db.table("security_alerts").select("alert_id", count="exact").gte(
            "created_at", (now - timedelta(days=30)).isoformat()
        ).execute()
        total_alerts_30d = alerts_30d.count or 0
        
        # Banned users
        banned_users = db.table("bans").select("ban_id", count="exact").eq("ban_type", "USER").eq("is_active", True).execute()
        banned_users_count = banned_users.count or 0
        
        # Banned IPs
        banned_ips = db.table("bans").select("ban_id", count="exact").eq("ban_type", "IP").eq("is_active", True).execute()
        banned_ips_count = banned_ips.count or 0
        
        # System health
        if critical_alerts_24h > 10:
            system_health = "CRITICAL"
        elif critical_alerts_24h > 5:
            system_health = "WARNING"
        elif total_alerts_24h > 50:
            system_health = "CAUTION"
        else:
            system_health = "HEALTHY"
        
        return AdminStatsResponse(
            total_users=total_users,
            total_alerts_24h=total_alerts_24h,
            total_alerts_7d=total_alerts_7d,
            total_alerts_30d=total_alerts_30d,
            critical_alerts_24h=critical_alerts_24h,
            banned_users=banned_users_count,
            banned_ips=banned_ips_count,
            system_health=system_health
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get admin stats: {str(e)}"
        )


@router.get("/alerts", response_model=List[AlertResponse])
async def get_alerts(
    admin: dict = Depends(require_admin_auth),
    db: Client = Depends(get_supabase_admin),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    severity: Optional[str] = Query(None),
    attack_type: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None),
    ip_address: Optional[str] = Query(None),
    user_id: Optional[int] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """Get security alerts with filters."""
    try:
        query = db.table("security_alerts").select("*")
        
        # Apply filters
        if severity:
            query = query.eq("severity", severity.upper())
        if attack_type:
            query = query.eq("attack_type", attack_type.upper())
        if status_filter:
            query = query.eq("status", status_filter.upper())
        if ip_address:
            query = query.eq("ip_address", ip_address)
        if user_id:
            query = query.eq("user_id", user_id)
        if start_date:
            query = query.gte("created_at", start_date)
        if end_date:
            query = query.lte("created_at", end_date)
        
        # Order by created_at descending
        query = query.order("created_at", desc=True)
        
        # Pagination
        result = query.range(skip, skip + limit - 1).execute()
        
        # DEDUPLICATION: Remove duplicates based on alert_id
        # This is a safety measure in case duplicates somehow exist in the database
        seen_ids = set()
        unique_alerts = []
        for alert in result.data:
            alert_id = alert.get("alert_id")
            if alert_id and alert_id not in seen_ids:
                seen_ids.add(alert_id)
                unique_alerts.append(alert)
        
        return [AlertResponse(**alert) for alert in unique_alerts]
        
    except Exception as e:
        logger.error(f"Failed to get alerts: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get alerts: {str(e)}"
        )


@router.get("/alerts/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: int,
    admin: dict = Depends(require_admin_auth),
    db: Client = Depends(get_supabase_admin)
):
    """Get specific alert details."""
    try:
        result = db.table("security_alerts").select("*").eq("alert_id", alert_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found"
            )
        
        alert = result.data[0]
        
        # Get user's previous alerts
        if alert.get("user_id"):
            user_alerts = db.table("security_alerts").select("alert_id", count="exact").eq("user_id", alert["user_id"]).execute()
            alert["user_previous_alerts_count"] = user_alerts.count or 0
        
        return AlertResponse(**alert)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get alert: {str(e)}"
        )


@router.patch("/alerts/{alert_id}/status", response_model=AlertResponse)
async def update_alert_status(
    alert_id: int,
    update: AlertUpdate,
    admin: dict = Depends(require_admin_auth),
    db: Client = Depends(get_supabase_admin)
):
    """Update alert status."""
    try:
        valid_statuses = ["REVIEWED", "IGNORED", "BANNED", "FALSE_POSITIVE"]
        if update.status.upper() not in valid_statuses:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid status. Must be one of: {', '.join(valid_statuses)}"
            )
        
        # Get admin user_id from database (admin dict only has username and role)
        admin_username = admin.get("username")
        if not admin_username:
            logger.error(f"Admin dict missing username. Admin dict keys: {list(admin.keys())}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Admin authentication error: username not found"
            )
        
        # Look up user_id from username/email
        try:
            # Try email first
            user_lookup = db.table("users").select("user_id").eq("email", admin_username.lower()).limit(1).execute()
            
            # If not found, try username
            if not user_lookup.data:
                user_lookup = db.table("users").select("user_id").eq("username", admin_username).limit(1).execute()
            
            if not user_lookup.data:
                logger.error(f"Admin user not found in database: {admin_username}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Admin user not found in database"
                )
            
            admin_user_id = user_lookup.data[0].get("user_id")
            if not admin_user_id:
                logger.error(f"Admin user has no user_id: {user_lookup.data[0]}")
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Admin user_id not found"
                )
        except HTTPException:
            raise
        except Exception as lookup_error:
            logger.error(f"Error looking up admin user_id: {lookup_error}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get admin user_id: {str(lookup_error)}"
            )
        
        # Build update data - only include fields that exist
        update_data = {
            "status": update.status.upper()
        }
        
        # Try to add reviewed_at and reviewed_by if columns exist
        # If they don't exist, the update will still work without them
        try:
            update_data["reviewed_at"] = datetime.now(timezone.utc).isoformat()
            update_data["reviewed_by"] = admin_user_id
        except Exception:
            pass  # Columns might not exist, that's okay
        
        # First check if alert exists
        check_result = db.table("security_alerts").select("alert_id").eq("alert_id", alert_id).execute()
        if not check_result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found"
            )
        
        # Update the alert
        try:
            result = db.table("security_alerts").update(update_data).eq("alert_id", alert_id).execute()
        except Exception as update_error:
            error_str = str(update_error)
            logger.error(f"Database update error: {error_str}", exc_info=True)
            
            # If error mentions missing columns, try without them
            if "column" in error_str.lower() and ("does not exist" in error_str.lower() or "unknown" in error_str.lower()):
                logger.warning("reviewed_at/reviewed_by columns may not exist, trying update without them")
                update_data_minimal = {"status": update.status.upper()}
                result = db.table("security_alerts").update(update_data_minimal).eq("alert_id", alert_id).execute()
            else:
                raise
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found or update failed"
            )
        
        # Log admin action using logging system (more reliable than admin_actions table)
        try:
            logging_system = get_logging_system()
            logging_system.log_event(
                log_type=LogType.ADMIN_ACTION,
                message=f"Admin updated alert {alert_id} status to {update.status.upper()}",
                log_level=LogLevel.INFO,
                user_id=admin_user_id,
                username=admin.get("username") or admin.get("email"),
                metadata={
                    "action_type": "UPDATE_ALERT_STATUS",
                    "target_type": "ALERT",
                    "target_id": alert_id,
                    "status": update.status.upper()
                }
            )
        except Exception as log_error:
            # Don't fail the request if logging fails
            logger.warning(f"Failed to log admin action: {log_error}")
        
        return AlertResponse(**result.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update alert status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update alert: {str(e)}"
        )


@router.post("/ban", response_model=dict)
async def ban_user_or_ip(
    ban_request: BanRequest,
    admin: dict = Depends(require_admin_auth),
    db: Client = Depends(get_supabase_admin)
):
    """Ban a user or IP address."""
    try:
        if not ban_request.user_id and not ban_request.ip_address:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either user_id or ip_address must be provided"
            )
        
        ban_data = {
            "user_id": ban_request.user_id,
            "ip_address": ban_request.ip_address,
            "ban_type": "BOTH" if ban_request.user_id and ban_request.ip_address else ("USER" if ban_request.user_id else "IP"),
            "ban_reason": ban_request.ban_reason,
            "ban_duration": ban_request.ban_duration.upper(),
            "is_active": True,
            "created_by": admin["user_id"],
            "notes": ban_request.notes
        }
        
        if ban_request.ban_duration.upper() == "TEMPORARY" and ban_request.expires_hours:
            expires_at = datetime.now(timezone.utc) + timedelta(hours=ban_request.expires_hours)
            ban_data["expires_at"] = expires_at.isoformat()
        
        result = db.table("bans").insert(ban_data).execute()
        
        # If banning user, deactivate their account
        if ban_request.user_id:
            db.table("users").update({"is_active": False}).eq("user_id", ban_request.user_id).execute()
        
        # Log admin action
        db.table("admin_actions").insert({
            "admin_id": admin["user_id"],
            "action_type": "BAN",
            "target_type": "USER" if ban_request.user_id else "IP",
            "target_id": ban_request.user_id,
            "details": ban_data,
            "ip_address": "admin_action"
        }).execute()
        
        return {
            "success": True,
            "message": "Ban created successfully",
            "ban": result.data[0] if result.data else None
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create ban: {str(e)}"
        )


@router.post("/unban", response_model=dict)
async def unban_user_or_ip(
    unban_request: UnbanRequest,
    admin: dict = Depends(require_admin_auth),
    db: Client = Depends(get_supabase_admin)
):
    """Unban a user or IP address."""
    try:
        if not unban_request.user_id and not unban_request.ip_address:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Either user_id or ip_address must be provided"
            )
        
        query = db.table("bans").update({"is_active": False})
        
        if unban_request.user_id:
            query = query.eq("user_id", unban_request.user_id)
        if unban_request.ip_address:
            query = query.eq("ip_address", unban_request.ip_address)
        
        result = query.execute()
        
        # If unbanning user, reactivate their account
        if unban_request.user_id:
            db.table("users").update({"is_active": True}).eq("user_id", unban_request.user_id).execute()
        
        # Log admin action
        db.table("admin_actions").insert({
            "admin_id": admin["user_id"],
            "action_type": "UNBAN",
            "target_type": "USER" if unban_request.user_id else "IP",
            "target_id": unban_request.user_id,
            "details": {"user_id": unban_request.user_id, "ip_address": unban_request.ip_address},
            "ip_address": "admin_action"
        }).execute()
        
        return {
            "success": True,
            "message": "Unbanned successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to unban: {str(e)}"
        )


@router.get("/graph-data", response_model=GraphDataResponse)
async def get_graph_data(
    admin: dict = Depends(require_admin_auth),
    db: Client = Depends(get_supabase_admin),
    days: int = Query(7, ge=1, le=30)
):
    """Get graph data for dashboard charts."""
    try:
        start_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        
        # Get all alerts in time range
        alerts = db.table("security_alerts").select("*").gte("created_at", start_date).execute()
        
        # Alerts by type
        alerts_by_type = {}
        alerts_by_severity = {}
        alerts_timeline = []
        ip_counts = {}
        endpoint_counts = {}
        
        for alert in alerts.data:
            # By type
            attack_type = alert.get("attack_type", "UNKNOWN")
            alerts_by_type[attack_type] = alerts_by_type.get(attack_type, 0) + 1
            
            # By severity
            severity = alert.get("severity", "MEDIUM")
            alerts_by_severity[severity] = alerts_by_severity.get(severity, 0) + 1
            
            # Timeline (group by day)
            created_at = alert.get("created_at", "")
            if created_at:
                date = created_at[:10]  # YYYY-MM-DD
                alerts_timeline.append({"date": date, "count": 1})
            
            # IP counts
            ip = alert.get("ip_address", "unknown")
            ip_counts[ip] = ip_counts.get(ip, 0) + 1
            
            # Endpoint counts
            endpoint = alert.get("endpoint", "unknown")
            endpoint_counts[endpoint] = endpoint_counts.get(endpoint, 0) + 1
        
        # Aggregate timeline
        timeline_dict = {}
        for item in alerts_timeline:
            date = item["date"]
            timeline_dict[date] = timeline_dict.get(date, 0) + 1
        
        timeline = [{"date": date, "count": count} for date, count in sorted(timeline_dict.items())]
        
        # Top attacking IPs
        top_ips = sorted(ip_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        top_attacking_ips = [{"ip": ip, "count": count} for ip, count in top_ips]
        
        # Top attacked endpoints
        top_endpoints = sorted(endpoint_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        top_attacked_endpoints = [{"endpoint": endpoint, "count": count} for endpoint, count in top_endpoints]
        
        return GraphDataResponse(
            alerts_by_type=alerts_by_type,
            alerts_by_severity=alerts_by_severity,
            alerts_timeline=timeline,
            top_attacking_ips=top_attacking_ips,
            top_attacked_endpoints=top_attacked_endpoints
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get graph data: {str(e)}"
        )


@router.get("/users", response_model=List[UserResponse])
async def get_all_users(
    admin: dict = Depends(require_admin_auth),
    db: Client = Depends(get_supabase_admin),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None)
):
    """Get all users (admin only)."""
    try:
        query = db.table("users").select("*")
        
        if search:
            query = query.or_(f"email.ilike.%{search}%,username.ilike.%{search}%")
        
        result = query.order("created_at", desc=True).range(skip, skip + limit - 1).execute()
        
        # Ensure is_active is included in response
        users = []
        for user in result.data:
            user_dict = dict(user)
            # Default to True if not present
            if "is_active" not in user_dict:
                user_dict["is_active"] = True
            users.append(UserResponse(**user_dict))
        
        return users
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get users: {str(e)}"
        )


@router.get("/alerts-stream")
async def stream_alerts(
    admin: dict = Depends(require_admin_auth),
    db: Client = Depends(get_supabase_admin)
):
    """Stream real-time security alerts via Server-Sent Events (SSE)."""
    import asyncio
    import json
    
    async def event_generator():
        last_alert_id = 0
        
        while True:
            try:
                # Get new alerts since last check
                query = db.table("security_alerts").select("*").eq("status", "NEW").gt("alert_id", last_alert_id).order("alert_id", desc=False).limit(10).execute()
                
                if query.data:
                    for alert in query.data:
                        last_alert_id = max(last_alert_id, alert["alert_id"])
                        yield f"data: {json.dumps(alert)}\n\n"
                
                # Send heartbeat every 5 seconds
                yield f"data: {json.dumps({'type': 'heartbeat', 'timestamp': datetime.now(timezone.utc).isoformat()})}\n\n"
                
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Error in alert stream: {e}")
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
                await asyncio.sleep(5)
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )


@router.get("/export-alerts")
async def export_alerts(
    admin: dict = Depends(require_admin_auth),
    db: Client = Depends(get_supabase_admin),
    format: str = Query("json", regex="^(json|csv)$"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None)
):
    """Export alerts as JSON or CSV."""
    try:
        query = db.table("security_alerts").select("*")
        
        if start_date:
            query = query.gte("created_at", start_date)
        if end_date:
            query = query.lte("created_at", end_date)
        
        result = query.order("created_at", desc=True).limit(10000).execute()
        
        # Log admin action
        logging_system = get_logging_system()
        logging_system.log_event(
            log_type=LogType.ALERT_EXPORTED,
            message=f"Admin exported alerts as {format.upper()}",
            log_level=LogLevel.INFO,
            user_id=admin["user_id"],
            username=admin.get("username"),
            metadata={"format": format, "start_date": start_date, "end_date": end_date},
        )
        
        if format == "json":
            from fastapi.responses import JSONResponse
            return JSONResponse(
                content=result.data,
                headers={"Content-Disposition": f"attachment; filename=alerts_{datetime.now().strftime('%Y%m%d')}.json"}
            )
        else:  # CSV
            import csv
            from fastapi.responses import Response
            import io
            
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=[
                "alert_id", "user_id", "ip_address", "attack_type", "endpoint",
                "severity", "risk_score", "status", "user_agent", "created_at"
            ])
            writer.writeheader()
            for alert in result.data:
                writer.writerow({
                    "alert_id": alert.get("alert_id"),
                    "user_id": alert.get("user_id") or "",
                    "ip_address": alert.get("ip_address"),
                    "attack_type": alert.get("attack_type"),
                    "endpoint": alert.get("endpoint") or "",
                    "severity": alert.get("severity"),
                    "risk_score": alert.get("risk_score"),
                    "status": alert.get("status"),
                    "user_agent": alert.get("user_agent") or "",
                    "created_at": alert.get("created_at")
                })
            
            return Response(
                content=output.getvalue(),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=alerts_{datetime.now().strftime('%Y%m%d')}.csv"}
            )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export alerts: {str(e)}"
        )


# ============================================================================
# NEW ENDPOINTS: Web Requests, Enhanced Users, Alerts Management, SOAR
# ============================================================================

class WebRequestResponse(BaseModel):
    request_id: int
    user_id: Optional[int] = None
    username: Optional[str] = None
    ip_address: str
    http_method: str
    path: str
    endpoint: Optional[str] = None
    response_status: Optional[int] = None
    response_time_ms: Optional[int] = None
    user_agent: Optional[str] = None
    is_authenticated: bool = False
    created_at: str
    
    class Config:
        # Allow None values for optional fields
        from_attributes = True
        # Allow population by field name or alias
        populate_by_name = True


class WebRequestFilters(BaseModel):
    user_id: Optional[int] = None
    username: Optional[str] = None
    ip_address: Optional[str] = None
    http_method: Optional[str] = None
    path: Optional[str] = None
    endpoint: Optional[str] = None
    status_code: Optional[int] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    skip: int = 0
    limit: int = 50


class WebRequestsResponse(BaseModel):
    skip: int
    limit: int
    total: int
    results: List[WebRequestResponse]


@router.get("/web-requests", response_model=WebRequestsResponse)
async def get_web_requests(
    admin: dict = Depends(require_admin_auth),
    db: Client = Depends(get_supabase_admin),
    user_id: Optional[int] = Query(None),
    username: Optional[str] = Query(None),
    ip_address: Optional[str] = Query(None),
    http_method: Optional[str] = Query(None),
    path: Optional[str] = Query(None),
    endpoint: Optional[str] = Query(None),
    status_code: Optional[int] = Query(None),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """Get web requests with filtering."""
    try:
        # Check if table exists by trying a simple query
        try:
            test_query = db.table("web_requests").select("request_id").limit(1).execute()
            # If we get here, table exists
        except Exception as table_error:
            error_str = str(table_error)
            logger.error(f"Web requests table error: {error_str}")
            
            # Check if it's a table doesn't exist error
            if "does not exist" in error_str.lower() or "relation" in error_str.lower():
                logger.warning("web_requests table does not exist. Run admin_logging_schema_safe.sql in Supabase.")
            
            # Return empty result if table doesn't exist
            return WebRequestsResponse(
                skip=skip,
                limit=limit,
                total=0,
                results=[]
            )
        
        # Build query step by step to avoid issues
        query = db.table("web_requests")
        
        # Apply filters one by one
        if user_id is not None:
            query = query.eq("user_id", user_id)
        if username:
            query = query.ilike("username", f"%{username}%")
        if ip_address:
            query = query.eq("ip_address", ip_address)
        if http_method:
            query = query.eq("http_method", http_method.upper())
        if path:
            query = query.ilike("path", f"%{path}%")
        if endpoint:
            query = query.ilike("endpoint", f"%{endpoint}%")
        if status_code is not None:
            query = query.eq("response_status", status_code)
        if start_date:
            query = query.gte("created_at", start_date)
        if end_date:
            query = query.lte("created_at", end_date)
        
        # Get total count (separate query)
        total = 0
        try:
            count_query = db.table("web_requests")
            # Apply same filters for count
            if user_id is not None:
                count_query = count_query.eq("user_id", user_id)
            if username:
                count_query = count_query.ilike("username", f"%{username}%")
            if ip_address:
                count_query = count_query.eq("ip_address", ip_address)
            if http_method:
                count_query = count_query.eq("http_method", http_method.upper())
            if path:
                count_query = count_query.ilike("path", f"%{path}%")
            if endpoint:
                count_query = count_query.ilike("endpoint", f"%{endpoint}%")
            if status_code is not None:
                count_query = count_query.eq("response_status", status_code)
            if start_date:
                count_query = count_query.gte("created_at", start_date)
            if end_date:
                count_query = count_query.lte("created_at", end_date)
            
            count_result = count_query.select("request_id", count="exact").execute()
            total = count_result.count if count_result.count is not None else 0
        except Exception as count_error:
            logger.error(f"Error getting count: {count_error}", exc_info=True)
            total = 0
        
        # Get results - try simple query first if complex query fails
        result = None
        try:
            result = query.select("*").order("created_at", desc=True).range(skip, skip + limit - 1).execute()
        except Exception as query_error:
            error_str = str(query_error)
            logger.error(f"Error querying web requests: {error_str}", exc_info=True)
            
            # Try simplest possible query as fallback
            try:
                logger.info("Attempting fallback simple query...")
                result = db.table("web_requests").select("*").order("created_at", desc=True).limit(limit).execute()
                logger.info("Fallback query succeeded")
            except Exception as fallback_error:
                logger.error(f"Fallback query also failed: {fallback_error}")
                # Return empty result on error instead of crashing
                return WebRequestsResponse(
                    skip=skip,
                    limit=limit,
                    total=0,
                    results=[]
                )
        
        # Convert to response models
        requests = []
        if result.data:
            for req in result.data:
                try:
                    # Safely extract all fields with defaults
                    # Handle both dict and object access
                    if isinstance(req, dict):
                        req_data = req
                    else:
                        req_data = dict(req) if hasattr(req, '__dict__') else {}
                    
                    # Build request dict with safe access
                    req_dict = {
                        "request_id": req_data.get("request_id") or req_data.get("request_id"),
                        "user_id": req_data.get("user_id"),  # Can be None
                        "username": req_data.get("username"),  # Can be None
                        "ip_address": req_data.get("ip_address") or "unknown",
                        "http_method": req_data.get("http_method") or "GET",
                        "path": req_data.get("path") or "/",
                        "endpoint": req_data.get("endpoint") or req_data.get("path") or "/",
                        "response_status": req_data.get("response_status"),
                        "response_time_ms": req_data.get("response_time_ms"),
                        "user_agent": req_data.get("user_agent"),
                        "is_authenticated": req_data.get("is_authenticated", False),
                        "created_at": req_data.get("created_at") or "",
                    }
                    
                    # Validate required fields
                    if not req_dict["request_id"]:
                        logger.warning(f"Skipping request without request_id: {req_data}")
                        continue
                    
                    # Ensure created_at exists
                    if not req_dict["created_at"]:
                        from datetime import datetime, timezone
                        req_dict["created_at"] = datetime.now(timezone.utc).isoformat()
                    
                    # Create response model
                    web_request = WebRequestResponse(**req_dict)
                    requests.append(web_request)
                    
                except KeyError as key_error:
                    logger.error(f"Missing key in web request data: {key_error}")
                    logger.error(f"Available keys: {list(req_data.keys()) if 'req_data' in locals() else 'unknown'}")
                    continue
                except Exception as e:
                    logger.error(f"Error parsing web request: {e}", exc_info=True)
                    logger.error(f"Request data type: {type(req)}")
                    logger.error(f"Request data: {req}")
                    continue
        
        # Log admin action (safely)
        try:
            logging_system = get_logging_system()
            logging_system.log_event(
                log_type=LogType.ADMIN_ACTION,
                message=f"Admin viewed web requests",
                log_level=LogLevel.INFO,
                user_id=admin.get("user_id") or admin.get("id"),
                username=admin.get("username") or admin.get("email"),
                metadata={"filters": {"user_id": user_id, "ip_address": ip_address, "method": http_method}, "total": total},
            )
        except Exception as log_error:
            logger.warning(f"Failed to log admin action: {log_error}")
        
        return WebRequestsResponse(
            skip=skip,
            limit=limit,
            total=total,
            results=requests
        )
        
    except HTTPException:
        raise
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Failed to get web requests: {error_msg}", exc_info=True)
        
        # Provide more helpful error message
        if "'user_id'" in error_msg or "user_id" in error_msg.lower():
            logger.error("Possible issue: user_id column missing or query structure issue")
            # Return empty result instead of error
            return WebRequestsResponse(
                skip=skip,
                limit=limit,
                total=0,
                results=[]
            )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get web requests: {error_msg}"
        )


@router.get("/web-requests/export")
async def export_web_requests(
    admin: dict = Depends(require_admin_auth),
    db: Client = Depends(get_supabase_admin),
    format: str = Query("json", regex="^(json|csv)$"),
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
):
    """Export web requests as JSON or CSV."""
    try:
        query = db.table("web_requests").select("*")
        
        if start_date:
            query = query.gte("created_at", start_date)
        if end_date:
            query = query.lte("created_at", end_date)
        
        result = query.order("created_at", desc=True).limit(10000).execute()
        
        if format == "json":
            from fastapi.responses import JSONResponse
            return JSONResponse(content=result.data)
        else:  # CSV
            import csv
            from fastapi.responses import Response
            import io
            
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=[
                "request_id", "user_id", "username", "ip_address", "http_method",
                "path", "endpoint", "response_status", "response_time_ms", "created_at"
            ])
            writer.writeheader()
            for req in result.data:
                writer.writerow({
                    "request_id": req.get("request_id"),
                    "user_id": req.get("user_id") or "",
                    "username": req.get("username") or "",
                    "ip_address": req.get("ip_address"),
                    "http_method": req.get("http_method"),
                    "path": req.get("path"),
                    "endpoint": req.get("endpoint") or "",
                    "response_status": req.get("response_status") or "",
                    "response_time_ms": req.get("response_time_ms") or "",
                    "created_at": req.get("created_at")
                })
            
            return Response(
                content=output.getvalue(),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=web_requests_{datetime.now().strftime('%Y%m%d')}.csv"}
            )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export web requests: {str(e)}"
        )


@router.delete("/web-requests/clear")
async def clear_web_requests(
    request: Request,
    admin: dict = Depends(require_admin_auth),
    db: Client = Depends(get_supabase_admin),
    days: int = Query(90, ge=1, le=365, description="Delete requests older than N days"),
):
    """Clear old web requests (admin only)."""
    try:
        cutoff_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        
        # Delete old requests
        result = db.table("web_requests").delete().lt("created_at", cutoff_date).execute()
        
        deleted_count = len(result.data) if result.data else 0
        
        # Log admin action
        logging_system = get_logging_system()
        logging_system.log_event(
            log_type=LogType.ADMIN_ACTION,
            message=f"Admin cleared web requests older than {days} days",
            log_level=LogLevel.INFO,
            user_id=admin["user_id"],
            username=admin.get("username"),
            ip_address=request.client.host if request.client else None,
            metadata={"days": days, "cutoff_date": cutoff_date, "deleted_count": deleted_count},
        )
        
        # Forward to SOAR if configured
        soar = get_soar_integration()
        event = SOAREvent(
            event_type=SOAREventType.ADMIN_ACTION,
            user_id=admin["user_id"],
            severity="low",
            description=f"Admin cleared web requests older than {days} days",
            metadata={"admin_username": admin.get("username"), "days": days},
        )
        await soar.forward_event(event)
        
        return {
            "success": True,
            "message": f"Cleared web requests older than {days} days",
            "deleted_count": len(result.data) if result.data else 0
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear web requests: {str(e)}"
        )


@router.delete("/alerts/clear")
async def clear_all_alerts(
    request: Request,
    admin: dict = Depends(require_admin_auth),
    db: Client = Depends(get_supabase_admin),
):
    """Clear all alerts (admin only)."""
    try:
        # Get count before deletion
        count_before = db.table("security_alerts").select("alert_id", count="exact").execute()
        total_before = count_before.count or 0
        
        # Delete all alerts
        delete_result = db.table("security_alerts").delete().neq("alert_id", 0).execute()
        
        deleted_count = total_before  # Use count before deletion
        
        # Log admin action
        logging_system = get_logging_system()
        logging_system.log_event(
            log_type=LogType.ALERT_CLEARED,
            message="Admin cleared all alerts",
            log_level=LogLevel.INFO,
            user_id=admin["user_id"],
            username=admin.get("username"),
            ip_address=request.client.host if request.client else None,
            metadata={"deleted_count": deleted_count},
        )
        
        # Forward to SOAR if configured
        soar = get_soar_integration()
        event = SOAREvent(
            event_type=SOAREventType.ADMIN_ACTION,
            user_id=admin["user_id"],
            severity="medium",
            description="All alerts cleared by admin",
            metadata={"admin_username": admin.get("username"), "deleted_count": deleted_count},
        )
        await soar.forward_event(event)
        
        return {
            "success": True,
            "message": "All alerts cleared successfully",
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        logger.error(f"Failed to clear alerts: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to clear alerts: {str(e)}"
        )


# Enhanced Users Management
class UserCreateRequest(BaseModel):
    email: str
    password: str
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: str = Field(default="BUYER", description="BUYER, ORGANIZER, ADMIN, SCANNER, RESELLER")


class UserUpdateRequest(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    is_email_verified: Optional[bool] = None


class PasswordResetRequest(BaseModel):
    user_id: int
    new_password: str


@router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreateRequest,
    admin: dict = Depends(require_admin_auth),
    db: Client = Depends(get_supabase_admin),
):
    """Create a new user (admin only)."""
    try:
        from routers.auth import hash_password
        
        # Check if email exists
        existing = db.table("users").select("user_id").eq("email", user_data.email).execute()
        if existing.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already exists"
            )
        
        # Create user
        user_record = {
            "email": user_data.email,
            "password_hash": hash_password(user_data.password),
            "username": user_data.username,
            "first_name": user_data.first_name,
            "last_name": user_data.last_name,
            "role": user_data.role.upper(),
            "is_active": True,
            "is_email_verified": False,
        }
        
        result = db.table("users").insert(user_record).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to create user"
            )
        
        new_user = result.data[0]
        
        # Ensure is_active is True for new users
        user_dict = dict(new_user)
        if "is_active" not in user_dict:
            user_dict["is_active"] = True
        
        # Log admin action
        logging_system = get_logging_system()
        logging_system.log_event(
            log_type=LogType.USER_CREATED,
            message=f"Admin created user: {user_data.email}",
            log_level=LogLevel.INFO,
            user_id=admin["user_id"],
            username=admin.get("username"),
            metadata={"created_user_id": user_dict["user_id"], "created_email": user_data.email},
        )
        
        return UserResponse(**user_dict)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )


@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdateRequest,
    admin: dict = Depends(require_admin_auth),
    db: Client = Depends(get_supabase_admin),
):
    """Update user (admin only)."""
    try:
        update_data = {}
        
        if user_data.email is not None:
            update_data["email"] = user_data.email
        if user_data.username is not None:
            update_data["username"] = user_data.username
        if user_data.first_name is not None:
            update_data["first_name"] = user_data.first_name
        if user_data.last_name is not None:
            update_data["last_name"] = user_data.last_name
        if user_data.role is not None:
            update_data["role"] = user_data.role.upper()
        if user_data.is_active is not None:
            update_data["is_active"] = user_data.is_active
        if user_data.is_email_verified is not None:
            update_data["is_email_verified"] = user_data.is_email_verified
        
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        result = db.table("users").update(update_data).eq("user_id", user_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        updated_user = result.data[0]
        user_dict = dict(updated_user)
        # Ensure is_active is included
        if "is_active" not in user_dict:
            user_dict["is_active"] = True
        
        # Log admin action
        logging_system = get_logging_system()
        log_type = LogType.USER_SUSPENDED if user_data.is_active is False else LogType.USER_ACTIVATED if user_data.is_active is True else LogType.ADMIN_ACTION
        logging_system.log_event(
            log_type=log_type,
            message=f"Admin updated user {user_id}",
            log_level=LogLevel.INFO,
            user_id=admin["user_id"],
            username=admin.get("username"),
            metadata={"target_user_id": user_id, "updates": update_data},
        )
        
        return UserResponse(**user_dict)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update user: {str(e)}"
        )


@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    admin: dict = Depends(require_admin_auth),
    db: Client = Depends(get_supabase_admin),
):
    """Delete user (admin only)."""
    try:
        # Get user info before deletion
        user = db.table("users").select("*").eq("user_id", user_id).execute()
        if not user.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user_email = user.data[0].get("email", "unknown")
        
        # Delete user (cascade will handle related records)
        db.table("users").delete().eq("user_id", user_id).execute()
        
        # Log admin action
        logging_system = get_logging_system()
        logging_system.log_event(
            log_type=LogType.USER_DELETED,
            message=f"Admin deleted user: {user_email}",
            log_level=LogLevel.WARNING,
            user_id=admin["user_id"],
            username=admin.get("username"),
            metadata={"deleted_user_id": user_id, "deleted_email": user_email},
        )
        
        # Forward to SOAR if configured
        soar = get_soar_integration()
        event = SOAREvent(
            event_type=SOAREventType.ADMIN_ACTION,
            user_id=admin["user_id"],
            severity="high",
            description=f"Admin deleted user: {user_email}",
            metadata={"admin_username": admin.get("username"), "deleted_user_id": user_id},
        )
        await soar.forward_event(event)
        
        return {
            "success": True,
            "message": f"User {user_email} deleted successfully"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete user: {str(e)}"
        )


@router.post("/users/{user_id}/reset-password")
async def reset_user_password(
    user_id: int,
    reset_data: PasswordResetRequest,
    admin: dict = Depends(require_admin_auth),
    db: Client = Depends(get_supabase_admin),
):
    """Reset user password (admin only)."""
    try:
        from routers.auth import hash_password
        
        # Update password
        db.table("users").update({
            "password_hash": hash_password(reset_data.new_password),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }).eq("user_id", user_id).execute()
        
        # Log admin action
        logging_system = get_logging_system()
        logging_system.log_event(
            log_type=LogType.AUTH_PASSWORD_CHANGE,
            message=f"Admin reset password for user {user_id}",
            log_level=LogLevel.INFO,
            user_id=admin["user_id"],
            username=admin.get("username"),
            metadata={"target_user_id": user_id},
        )
        
        return {
            "success": True,
            "message": "Password reset successfully"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset password: {str(e)}"
        )


@router.get("/users/{user_id}/activity")
async def get_user_activity(
    user_id: int,
    admin: dict = Depends(require_admin_auth),
    db: Client = Depends(get_supabase_admin),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    """Get user activity log."""
    try:
        result = db.table("user_activity_logs").select("*").eq("user_id", user_id).order("created_at", desc=True).range(skip, skip + limit - 1).execute()
        
        # Get attack count for this user
        attack_count = get_user_attack_count(db, user_id)
        
        return {
            "activity": result.data,
            "attack_count": attack_count,
            "is_suspended": attack_count >= 2,
            "is_banned": attack_count >= 10,
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get user activity: {str(e)}"
        )


# SOAR Configuration Endpoints
class SOARConfigCreate(BaseModel):
    platform_name: str
    endpoint_url: str
    api_key: str
    is_enabled: bool = False
    event_types: List[str] = []
    severity_filter: List[str] = ["CRITICAL", "HIGH"]
    retry_count: int = 3
    timeout_seconds: int = 30
    verify_ssl: bool = True
    custom_headers: Dict[str, Any] = {}


class SOARConfigUpdate(BaseModel):
    endpoint_url: Optional[str] = None
    api_key: Optional[str] = None
    is_enabled: Optional[bool] = None
    event_types: Optional[List[str]] = None
    severity_filter: Optional[List[str]] = None
    retry_count: Optional[int] = None
    timeout_seconds: Optional[int] = None
    verify_ssl: Optional[bool] = None
    custom_headers: Optional[Dict[str, Any]] = None


@router.post("/soar/config")
async def create_soar_config(
    config: SOARConfigCreate,
    admin: dict = Depends(require_admin_auth),
    db: Client = Depends(get_supabase_admin),
):
    """Create SOAR configuration."""
    try:
        config_data = config.dict()
        config_data["created_at"] = datetime.now(timezone.utc).isoformat()
        config_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        result = db.table("soar_config").insert(config_data).execute()
        
        # Log admin action
        logging_system = get_logging_system()
        logging_system.log_event(
            log_type=LogType.ADMIN_ACTION,
            message=f"Admin created SOAR config: {config.platform_name}",
            log_level=LogLevel.INFO,
            user_id=admin["user_id"],
            username=admin.get("username"),
        )
        
        return result.data[0] if result.data else {}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create SOAR config: {str(e)}"
        )


@router.get("/soar/config")
async def get_soar_configs(
    admin: dict = Depends(require_admin_auth),
    db: Client = Depends(get_supabase_admin),
):
    """Get all SOAR configurations."""
    try:
        result = db.table("soar_config").select("*").order("created_at", desc=True).execute()
        return result.data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get SOAR configs: {str(e)}"
        )


@router.patch("/soar/config/{config_id}")
async def update_soar_config(
    config_id: int,
    config: SOARConfigUpdate,
    admin: dict = Depends(require_admin_auth),
    db: Client = Depends(get_supabase_admin),
):
    """Update SOAR configuration."""
    try:
        update_data = config.dict(exclude_unset=True)
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        result = db.table("soar_config").update(update_data).eq("config_id", config_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="SOAR config not found"
            )
        
        # Log admin action
        logging_system = get_logging_system()
        logging_system.log_event(
            log_type=LogType.ADMIN_ACTION,
            message=f"Admin updated SOAR config {config_id}",
            log_level=LogLevel.INFO,
            user_id=admin["user_id"],
            username=admin.get("username"),
        )
        
        return result.data[0]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update SOAR config: {str(e)}"
        )


@router.delete("/soar/config/{config_id}")
async def delete_soar_config(
    config_id: int,
    admin: dict = Depends(require_admin_auth),
    db: Client = Depends(get_supabase_admin),
):
    """Delete SOAR configuration."""
    try:
        db.table("soar_config").delete().eq("config_id", config_id).execute()
        
        # Log admin action
        logging_system = get_logging_system()
        logging_system.log_event(
            log_type=LogType.ADMIN_ACTION,
            message=f"Admin deleted SOAR config {config_id}",
            log_level=LogLevel.INFO,
            user_id=admin["user_id"],
            username=admin.get("username"),
        )
        
        return {"success": True, "message": "SOAR config deleted successfully"}
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete SOAR config: {str(e)}"
        )


@router.post("/soar/config/{config_id}/test")
async def test_soar_connection(
    config_id: int,
    admin: dict = Depends(require_admin_auth),
    db: Client = Depends(get_supabase_admin),
):
    """Test SOAR configuration connection."""
    try:
        # Get config
        result = db.table("soar_config").select("*").eq("config_id", config_id).execute()
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="SOAR config not found"
            )
        
        config = result.data[0]
        
        # Create test event
        test_event = SOAREvent(
            event_type=SOAREventType.SYSTEM_ERROR,
            severity="low",
            description="Test connection from admin panel",
            metadata={"test": True, "admin_user_id": admin["user_id"]},
        )
        
        # Try to forward event
        soar = get_soar_integration()
        success = await soar.forward_event(test_event, config_id=config_id)
        
        # Log admin action
        logging_system = get_logging_system()
        logging_system.log_event(
            log_type=LogType.ADMIN_ACTION,
            message=f"Admin tested SOAR config {config_id}",
            log_level=LogLevel.INFO,
            user_id=admin["user_id"],
            username=admin.get("username"),
            metadata={"config_id": config_id, "success": success},
        )
        
        return {
            "success": success,
            "message": "Connection test successful" if success else "Connection test failed",
            "config_id": config_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        # Log admin action
        logging_system = get_logging_system()
        logging_system.log_event(
            log_type=LogType.ADMIN_ACTION,
            message=f"Admin tested SOAR config {config_id} - Failed",
            log_level=LogLevel.ERROR,
            user_id=admin["user_id"],
            username=admin.get("username"),
            metadata={"config_id": config_id, "error": str(e)},
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Connection test failed: {str(e)}"
        )

