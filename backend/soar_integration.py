"""
SOAR (Security Orchestration, Automation, and Response) Integration Module.
Provides abstraction layer for forwarding security events to external SOAR platforms.
"""
import json
import logging
import httpx
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from enum import Enum
from supabase import Client

from database import get_supabase_admin

logger = logging.getLogger(__name__)


class SOARPlatform(str, Enum):
    """Supported SOAR platforms."""
    SPLUNK_SOAR = "Splunk SOAR"
    CORTEX_XSOAR = "Cortex XSOAR"
    IBM_RESILIENT = "IBM Resilient"
    CUSTOM = "Custom"


class SOAREventType(str, Enum):
    """Event types that can be forwarded to SOAR."""
    LOGIN_ATTEMPT = "login_attempt"
    FAILED_LOGIN = "failed_login"
    SECURITY_ALERT = "security_alert"
    USER_BANNED = "user_banned"
    IP_BANNED = "ip_banned"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    SYSTEM_ERROR = "system_error"
    ADMIN_ACTION = "admin_action"


class SOAREvent:
    """Standardized security event object for SOAR platforms."""
    
    def __init__(
        self,
        event_type: SOAREventType,
        timestamp: Optional[datetime] = None,
        user_id: Optional[int] = None,
        ip: Optional[str] = None,
        severity: str = "medium",
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Initialize SOAR event.
        
        Args:
            event_type: Type of security event
            timestamp: Event timestamp (defaults to now)
            user_id: User ID if applicable
            ip: IP address
            severity: Event severity (low, medium, high, critical)
            description: Event description
            metadata: Additional event metadata
        """
        self.event_type = event_type.value
        self.timestamp = timestamp or datetime.now(timezone.utc)
        self.user_id = user_id
        self.ip = ip
        self.severity = severity.lower()
        self.description = description
        self.metadata = metadata or {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "user_id": str(self.user_id) if self.user_id else None,
            "ip": self.ip,
            "severity": self.severity,
            "description": self.description,
            "metadata": self.metadata,
        }
    
    def to_json(self) -> str:
        """Convert event to JSON string."""
        return json.dumps(self.to_dict())


class SOARIntegration:
    """SOAR integration manager."""
    
    def __init__(self):
        """Initialize SOAR integration."""
        self._db: Optional[Client] = None
    
    def _get_db(self) -> Client:
        """Get database client."""
        if not self._db:
            self._db = get_supabase_admin()
        return self._db
    
    async def forward_event(
        self,
        event: SOAREvent,
        config_id: Optional[int] = None,
    ) -> bool:
        """Forward event to configured SOAR platforms.
        
        Args:
            event: SOAR event to forward
            config_id: Specific config ID to use (if None, uses all enabled configs)
        
        Returns:
            True if at least one forward succeeded, False otherwise
        """
        db = self._get_db()
        
        # Get SOAR configurations
        query = db.table("soar_config").select("*").eq("is_enabled", True)
        
        if config_id:
            query = query.eq("config_id", config_id)
        
        configs = query.execute()
        
        if not configs.data:
            logger.debug("No enabled SOAR configurations found")
            return False
        
        success = False
        
        for config in configs.data:
            # Check if event type should be forwarded
            event_types = config.get("event_types", [])
            if event_types and event.event_type not in event_types:
                continue
            
            # Check severity filter
            severity_filter = config.get("severity_filter", [])
            if severity_filter and event.severity.upper() not in [s.upper() for s in severity_filter]:
                continue
            
            # Forward event
            try:
                await self._send_to_soar(event, config)
                success = True
                
                # Log successful forward
                self._log_forward(config["config_id"], event, "SENT")
            except Exception as e:
                logger.error(f"Failed to forward event to SOAR {config['platform_name']}: {e}")
                self._log_forward(config["config_id"], event, "FAILED", error_message=str(e))
        
        return success
    
    async def _send_to_soar(
        self,
        event: SOAREvent,
        config: Dict[str, Any],
    ):
        """Send event to SOAR platform.
        
        Args:
            event: Event to send
            config: SOAR configuration
        """
        endpoint_url = config["endpoint_url"]
        api_key = config["api_key"]
        timeout = config.get("timeout_seconds", 30)
        verify_ssl = config.get("verify_ssl", True)
        custom_headers = config.get("custom_headers", {})
        retry_count = config.get("retry_count", 3)
        
        # Prepare headers
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            **custom_headers,
        }
        
        # Prepare payload
        payload = event.to_dict()
        
        # Add platform-specific formatting if needed
        payload = self._format_for_platform(payload, config["platform_name"])
        
        # Send with retries
        last_error = None
        for attempt in range(retry_count):
            try:
                async with httpx.AsyncClient(timeout=timeout, verify=verify_ssl) as client:
                    response = await client.post(
                        endpoint_url,
                        json=payload,
                        headers=headers,
                    )
                    response.raise_for_status()
                    
                    # Update last successful sync
                    self._update_config_sync_status(config["config_id"], success=True)
                    return
            except Exception as e:
                last_error = e
                if attempt < retry_count - 1:
                    logger.warning(f"SOAR forward attempt {attempt + 1} failed, retrying...")
                else:
                    raise
        
        # Update last failed sync
        self._update_config_sync_status(config["config_id"], success=False)
        raise Exception(f"Failed after {retry_count} attempts: {last_error}")
    
    def _format_for_platform(
        self,
        payload: Dict[str, Any],
        platform_name: str,
    ) -> Dict[str, Any]:
        """Format payload for specific SOAR platform.
        
        Args:
            payload: Event payload
            platform_name: SOAR platform name
        
        Returns:
            Formatted payload
        """
        # Platform-specific formatting
        if platform_name == SOARPlatform.SPLUNK_SOAR.value:
            # Splunk SOAR format
            return {
                "source": "NFTix Platform",
                "event": payload,
            }
        elif platform_name == SOARPlatform.CORTEX_XSOAR.value:
            # Cortex XSOAR format
            return {
                "type": "NFTix Security Event",
                "contents": payload,
            }
        elif platform_name == SOARPlatform.IBM_RESILIENT.value:
            # IBM Resilient format
            return {
                "name": payload["description"],
                "properties": payload,
            }
        else:
            # Default format
            return payload
    
    def _log_forward(
        self,
        config_id: int,
        event: SOAREvent,
        status: str,
        error_message: Optional[str] = None,
    ):
        """Log event forward attempt.
        
        Args:
            config_id: SOAR config ID
            event: Event that was forwarded
            status: Forward status (SENT, FAILED, etc.)
            error_message: Error message if failed
        """
        db = self._get_db()
        
        try:
            log_record = {
                "config_id": config_id,
                "event_type": event.event_type,
                "event_data": event.to_dict(),
                "severity": event.severity.upper(),
                "status": status,
                "error_message": error_message,
                "retry_count": 0,
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
            
            if status == "SENT":
                log_record["sent_at"] = datetime.now(timezone.utc).isoformat()
                log_record["completed_at"] = datetime.now(timezone.utc).isoformat()
            
            db.table("soar_event_log").insert(log_record).execute()
        except Exception as e:
            logger.error(f"Failed to log SOAR forward: {e}")
    
    def _update_config_sync_status(
        self,
        config_id: int,
        success: bool,
    ):
        """Update SOAR config sync status.
        
        Args:
            config_id: Config ID
            success: Whether sync was successful
        """
        db = self._get_db()
        
        try:
            update_data = {
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            
            if success:
                update_data["last_successful_sync"] = datetime.now(timezone.utc).isoformat()
                update_data["failure_count"] = 0
            else:
                update_data["last_failed_sync"] = datetime.now(timezone.utc).isoformat()
                # Increment failure count
                config = db.table("soar_config").select("failure_count").eq("config_id", config_id).execute()
                if config.data:
                    current_failures = config.data[0].get("failure_count", 0)
                    update_data["failure_count"] = current_failures + 1
            
            db.table("soar_config").update(update_data).eq("config_id", config_id).execute()
        except Exception as e:
            logger.error(f"Failed to update SOAR config sync status: {e}")


# Global SOAR integration instance
_soar_integration: Optional[SOARIntegration] = None


def get_soar_integration() -> SOARIntegration:
    """Get global SOAR integration instance."""
    global _soar_integration
    if _soar_integration is None:
        _soar_integration = SOARIntegration()
    return _soar_integration

