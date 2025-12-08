"""Middleware for tracking Prometheus metrics."""
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response as StarletteResponse
import time
from monitoring import (
    http_requests_total,
    http_request_duration_seconds,
    http_request_errors_total
)

class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to track HTTP request metrics for Prometheus."""
    
    async def dispatch(self, request: Request, call_next):
        """Track request metrics."""
        start_time = time.time()
        method = request.method
        endpoint = request.url.path
        
        try:
            response = await call_next(request)
            status_code = response.status_code if hasattr(response, 'status_code') else 200
            
            # Record metrics
            http_requests_total.labels(
                method=method,
                endpoint=endpoint,
                status=status_code
            ).inc()
            
            duration = time.time() - start_time
            http_request_duration_seconds.labels(
                method=method,
                endpoint=endpoint
            ).observe(duration)
            
            if status_code >= 400:
                http_request_errors_total.labels(
                    method=method,
                    endpoint=endpoint,
                    error_type=f"status_{status_code}"
                ).inc()
            
            return response
            
        except Exception as e:
            http_request_errors_total.labels(
                method=method,
                endpoint=endpoint,
                error_type=type(e).__name__
            ).inc()
            raise

