"""Prometheus metrics and monitoring setup."""
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response
from contextlib import asynccontextmanager
import time
from functools import wraps

# Metrics
http_requests_total = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

http_request_duration_seconds = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint']
)

http_request_errors_total = Counter(
    'http_request_errors_total',
    'Total HTTP request errors',
    ['method', 'endpoint', 'error_type']
)

database_queries_total = Counter(
    'database_queries_total',
    'Total database queries',
    ['operation', 'table']
)

database_query_duration_seconds = Histogram(
    'database_query_duration_seconds',
    'Database query duration in seconds',
    ['operation', 'table']
)

active_users = Gauge(
    'active_users_total',
    'Number of active users'
)

events_created_total = Counter(
    'events_created_total',
    'Total events created'
)

tickets_sold_total = Counter(
    'tickets_sold_total',
    'Total tickets sold'
)

api_response_time = Histogram(
    'api_response_time_seconds',
    'API response time',
    ['endpoint']
)

error_rate = Gauge(
    'error_rate',
    'Current error rate percentage'
)

event_processing_lag = Gauge(
    'event_processing_lag_seconds',
    'Event processing lag in seconds'
)

suspicious_transactions_total = Counter(
    'suspicious_transactions_total',
    'Total suspicious transactions detected'
)

def track_request_metrics(func):
    """Decorator to track request metrics."""
    @wraps(func)
    async def wrapper(request, *args, **kwargs):
        start_time = time.time()
        method = request.method
        endpoint = request.url.path
        
        try:
            response = await func(request, *args, **kwargs)
            status_code = response.status_code if hasattr(response, 'status_code') else 200
            
            # Record metrics
            http_requests_total.labels(method=method, endpoint=endpoint, status=status_code).inc()
            duration = time.time() - start_time
            http_request_duration_seconds.labels(method=method, endpoint=endpoint).observe(duration)
            
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
    
    return wrapper

def get_metrics():
    """Get Prometheus metrics as string."""
    return generate_latest().decode('utf-8')

