"""
Web requests logging middleware.
Logs all incoming HTTP requests to database for monitoring and analysis.
"""
import time
import json
import logging
from typing import Optional, Dict, Any
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from supabase import Client

from database import get_supabase_admin
from logging_system import get_logging_system, LogType, LogLevel

logger = logging.getLogger(__name__)


class WebRequestsMiddleware(BaseHTTPMiddleware):
    """Middleware to log all HTTP requests."""
    
    def __init__(self, app: ASGIApp, exclude_paths: Optional[list] = None):
        """Initialize middleware.
        
        Args:
            app: ASGI application
            exclude_paths: List of paths to exclude from logging (e.g., ['/health', '/metrics'])
        """
        super().__init__(app)
        self.exclude_paths = exclude_paths or ['/health', '/metrics', '/docs', '/redoc', '/openapi.json']
        self._db: Optional[Client] = None
        self.logging_system = get_logging_system()
    
    async def dispatch(self, request: Request, call_next):
        """Process request and log it."""
        # Skip excluded paths
        if any(request.url.path.startswith(path) for path in self.exclude_paths):
            return await call_next(request)
        
        # Get request start time
        start_time = time.time()
        
        # Get client IP
        ip_address = self._get_client_ip(request)
        
        # Get user info if authenticated
        user_id = None
        username = None
        is_authenticated = False
        
        try:
            # Try to get user from request state (set by auth middleware)
            if hasattr(request.state, "user"):
                user = request.state.user
                user_id = user.get("user_id") if isinstance(user, dict) else getattr(user, "user_id", None)
                username = user.get("username") if isinstance(user, dict) else getattr(user, "username", None)
                is_authenticated = True
        except Exception:
            pass
        
        # Read request body (if any)
        request_body = None
        try:
            body = await request.body()
            if body:
                try:
                    request_body = json.loads(body.decode('utf-8'))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    request_body = {"raw": body.decode('utf-8', errors='ignore')[:1000]}  # Limit size
        except Exception:
            pass
        
        # Get query parameters
        query_params = dict(request.query_params) if request.query_params else None
        
        # Get headers (sanitize sensitive headers)
        request_headers = self._sanitize_headers(dict(request.headers))
        
        # Process request
        response = await call_next(request)
        
        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Get response status
        response_status = response.status_code
        
        # Get response body (if small enough)
        response_body = None
        try:
            # Only capture response body for errors or small responses
            if response_status >= 400 or response.headers.get("content-length", "0") < "10000":
                body_bytes = b""
                async for chunk in response.body_iterator:
                    body_bytes += chunk
                
                # Recreate response with body
                response = Response(
                    content=body_bytes,
                    status_code=response_status,
                    headers=dict(response.headers),
                    media_type=response.media_type
                )
                
                # Try to parse as JSON
                if body_bytes:
                    try:
                        response_body = json.loads(body_bytes.decode('utf-8'))
                    except (json.JSONDecodeError, UnicodeDecodeError):
                        response_body = {"raw": body_bytes.decode('utf-8', errors='ignore')[:1000]}
        except Exception:
            pass
        
        # Get response headers (sanitize)
        response_headers = self._sanitize_headers(dict(response.headers))
        
        # Log to database (async, don't block response)
        try:
            await self._log_request(
                user_id=user_id,
                username=username,
                ip_address=ip_address,
                http_method=request.method,
                path=request.url.path,
                endpoint=request.url.path,
                query_params=query_params,
                request_headers=request_headers,
                request_body=request_body,
                response_status=response_status,
                response_headers=response_headers,
                response_body=response_body,
                response_time_ms=response_time_ms,
                user_agent=request.headers.get("user-agent"),
                referer=request.headers.get("referer"),
                is_authenticated=is_authenticated,
            )
        except Exception as e:
            logger.error(f"Failed to log web request: {e}")
        
        # Also log to application logs
        self.logging_system.log_event(
            log_type=LogType.HTTP_REQUEST,
            message=f"{request.method} {request.url.path} - {response_status}",
            log_level=LogLevel.INFO if response_status < 400 else LogLevel.WARNING,
            user_id=user_id,
            username=username,
            ip_address=ip_address,
            user_agent=request.headers.get("user-agent"),
            endpoint=request.url.path,
            http_method=request.method,
            status_code=response_status,
            request_payload=request_body,
            response_payload=response_body,
            metadata={"response_time_ms": response_time_ms},
        )
        
        return response
    
    async def _log_request(
        self,
        user_id: Optional[int],
        username: Optional[str],
        ip_address: str,
        http_method: str,
        path: str,
        endpoint: str,
        query_params: Optional[Dict[str, Any]],
        request_headers: Dict[str, Any],
        request_body: Optional[Dict[str, Any]],
        response_status: int,
        response_headers: Dict[str, Any],
        response_body: Optional[Dict[str, Any]],
        response_time_ms: int,
        user_agent: Optional[str],
        referer: Optional[str],
        is_authenticated: bool,
    ):
        """Log request to database."""
        if not self._db:
            self._db = get_supabase_admin()
        
        try:
            record = {
                "user_id": user_id,
                "username": username,
                "ip_address": ip_address,
                "http_method": http_method,
                "path": path,
                "endpoint": endpoint,
                "query_params": query_params,
                "request_headers": request_headers,
                "request_body": request_body,
                "response_status": response_status,
                "response_headers": response_headers,
                "response_body": response_body,
                "response_time_ms": response_time_ms,
                "user_agent": user_agent,
                "referer": referer,
                "is_authenticated": is_authenticated,
            }
            
            self._db.table("web_requests").insert(record).execute()
        except Exception as e:
            logger.error(f"Failed to insert web request log: {e}")
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        # Check for forwarded IP
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        # Check for real IP
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback to client host
        return request.client.host if request.client else "unknown"
    
    def _sanitize_headers(self, headers: Dict[str, Any]) -> Dict[str, Any]:
        """Remove sensitive headers."""
        sensitive_headers = [
            "authorization",
            "cookie",
            "x-api-key",
            "x-auth-token",
            "x-access-token",
        ]
        
        sanitized = {}
        for key, value in headers.items():
            if key.lower() not in sensitive_headers:
                sanitized[key] = value
            else:
                sanitized[key] = "[REDACTED]"
        
        return sanitized

