# File header: Custom middleware for security, logging, and request processing.
# Provides rate limiting, security headers, error handling, and request logging.

"""
Custom middleware for FastAPI application.
Includes security headers, error handling, and request logging.
"""

import time
import logging
from typing import Callable
from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)

# Purpose: Security headers middleware to add security-related HTTP headers.
# Prevents common attacks like XSS, clickjacking, and MIME type sniffing.
class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Purpose: Add security headers to prevent common web vulnerabilities.
        # Side effects: Modifies response headers.
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Purpose: Add HSTS header for HTTPS connections (production only).
        # Side effects: Sets Strict-Transport-Security header.
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        # Purpose: Add Content-Security-Policy header (can be customized per route).
        # Side effects: Sets CSP header to restrict resource loading.
        if "Content-Security-Policy" not in response.headers:
            response.headers["Content-Security-Policy"] = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self' https:;"
            )
        
        return response

# Purpose: Request logging middleware to log all API requests and responses.
# Provides audit trail and debugging capabilities.
class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests and responses."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Purpose: Record request start time for performance measurement.
        # Side effects: Stores timestamp.
        start_time = time.time()
        
        # Purpose: Log incoming request details.
        # Side effects: Writes to log file.
        logger.info(
            f"Request: {request.method} {request.url.path} "
            f"from {request.client.host if request.client else 'unknown'}"
        )
        
        try:
            response = await call_next(request)
            
            # Purpose: Calculate request processing time.
            # Side effects: Computes duration.
            process_time = time.time() - start_time
            
            # Purpose: Log successful response with timing information.
            # Side effects: Writes to log file.
            logger.info(
                f"Response: {request.method} {request.url.path} "
                f"Status: {response.status_code} "
                f"Time: {process_time:.3f}s"
            )
            
            # Purpose: Add processing time to response header.
            # Side effects: Modifies response headers.
            response.headers["X-Process-Time"] = str(process_time)
            
            return response
            
        except Exception as e:
            # Purpose: Log errors and calculate processing time.
            # Side effects: Writes error to log file.
            process_time = time.time() - start_time
            logger.error(
                f"Error: {request.method} {request.url.path} "
                f"Time: {process_time:.3f}s "
                f"Error: {str(e)}"
            )
            raise

# Purpose: Error handling middleware to sanitize error messages.
# Prevents information disclosure while maintaining useful error responses.
class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Sanitize error messages to prevent information disclosure."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
        except HTTPException:
            # Purpose: Re-raise HTTP exceptions as-is (they're already sanitized).
            # Side effects: None - pass through.
            raise
        except Exception as e:
            # Purpose: Log full error details internally but return sanitized message.
            # Side effects: Logs error, returns generic error response.
            logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
            
            # Purpose: Return generic error message to prevent information disclosure.
            # Side effects: Returns JSON error response.
            return JSONResponse(
                status_code=500,
                content={
                    "error": "Internal server error",
                    "message": "An unexpected error occurred. Please try again later.",
                    "request_id": getattr(request.state, "request_id", "unknown")
                }
            )

# Purpose: Rate limiting middleware (simple in-memory implementation).
# Prevents abuse by limiting requests per IP address.
class SimpleRateLimitMiddleware(BaseHTTPMiddleware):
    """Simple in-memory rate limiting (use Redis for production)."""
    
    def __init__(self, app: ASGIApp, requests_per_minute: int = 100):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.request_counts: dict[str, list[float]] = {}
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Purpose: Get client IP address for rate limiting.
        # Side effects: Extracts IP from request headers or client.
        client_ip = request.client.host if request.client else "unknown"
        
        # Purpose: Clean old request timestamps (older than 1 minute).
        # Side effects: Modifies request_counts dictionary.
        current_time = time.time()
        if client_ip in self.request_counts:
            self.request_counts[client_ip] = [
                timestamp for timestamp in self.request_counts[client_ip]
                if current_time - timestamp < 60
            ]
        else:
            self.request_counts[client_ip] = []
        
        # Purpose: Check if client has exceeded rate limit.
        # Side effects: Returns 429 error if limit exceeded.
        if len(self.request_counts[client_ip]) >= self.requests_per_minute:
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "message": f"Too many requests. Limit: {self.requests_per_minute} per minute."
                }
            )
        
        # Purpose: Record this request timestamp.
        # Side effects: Adds timestamp to request_counts.
        self.request_counts[client_ip].append(current_time)
        
        return await call_next(request)

