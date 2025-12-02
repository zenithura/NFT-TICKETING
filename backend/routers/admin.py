"""Admin dashboard and security alerts management router."""
from fastapi import APIRouter, HTTPException, Depends, Query, status, Request
from fastapi.responses import StreamingResponse
from typing import List, Optional
from datetime import datetime, timedelta, timezone
from supabase import Client
from pydantic import BaseModel, Field

from database import get_supabase_admin
from auth_middleware import require_role, get_current_user
from routers.admin_auth import require_admin_auth
from models import UserResponse
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
        
        return [AlertResponse(**alert) for alert in result.data]
        
    except Exception as e:
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
        
        update_data = {
            "status": update.status.upper(),
            "reviewed_at": datetime.now(timezone.utc).isoformat(),
            "reviewed_by": admin["user_id"]
        }
        
        result = db.table("security_alerts").update(update_data).eq("alert_id", alert_id).execute()
        
        if not result.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Alert not found"
            )
        
        # Log admin action
        db.table("admin_actions").insert({
            "admin_id": admin["user_id"],
            "action_type": "UPDATE_ALERT_STATUS",
            "target_type": "ALERT",
            "target_id": alert_id,
            "details": {"status": update.status.upper()},
            "ip_address": "admin_action"
        }).execute()
        
        return AlertResponse(**result.data[0])
        
    except HTTPException:
        raise
    except Exception as e:
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
        
        return [UserResponse(**user) for user in result.data]
        
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
        
        result = query.order("created_at", desc=True).execute()
        
        if format == "json":
            from fastapi.responses import JSONResponse
            return JSONResponse(content=result.data)
        else:  # CSV
            import csv
            from fastapi.responses import Response
            import io
            
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=[
                "alert_id", "user_id", "ip_address", "attack_type", "endpoint",
                "severity", "risk_score", "status", "created_at"
            ])
            writer.writeheader()
            for alert in result.data:
                writer.writerow({
                    "alert_id": alert.get("alert_id"),
                    "user_id": alert.get("user_id") or "",
                    "ip_address": alert.get("ip_address"),
                    "attack_type": alert.get("attack_type"),
                    "endpoint": alert.get("endpoint"),
                    "severity": alert.get("severity"),
                    "risk_score": alert.get("risk_score"),
                    "status": alert.get("status"),
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

