"""Enhanced Rate Limiting with Monitoring."""
import time
import json
from typing import Optional, Dict
from functools import wraps
from flask import request, jsonify
from data_control.db_connection import get_redis_client, get_db_connection, return_db_connection
import logging

logger = logging.getLogger(__name__)


class EnhancedRateLimiter:
    """Enhanced rate limiter with monitoring and logging."""
    
    def __init__(self):
        self.redis_client = get_redis_client()
    
    def check_rate_limit(self, identifier: str, limit: int, window_seconds: int,
                        key_prefix: str = 'rate_limit') -> tuple[bool, Optional[Dict]]:
        """
        Check if rate limit is exceeded.
        
        Args:
            identifier: Identifier (IP, user_id, etc.)
            limit: Maximum requests allowed
            window_seconds: Time window in seconds
            key_prefix: Redis key prefix
            
        Returns:
            Tuple of (allowed: bool, rate_limit_info: Dict or None)
        """
        if not self.redis_client:
            # No Redis, allow all requests (fallback)
            return True, None
        
        try:
            redis_key = f"{key_prefix}:{identifier}"
            
            # Sliding window algorithm
            now = time.time()
            window_start = now - window_seconds
            
            # Remove old entries
            self.redis_client.zremrangebyscore(redis_key, 0, window_start)
            
            # Count requests in current window
            current_requests = self.redis_client.zcard(redis_key)
            
            if current_requests >= limit:
                # Rate limit exceeded
                retry_after = int(window_seconds - (now - (window_start + 1)))
                rate_limit_info = {
                    'limit': limit,
                    'window_seconds': window_seconds,
                    'current_requests': current_requests,
                    'retry_after': max(retry_after, 1)
                }
                
                # Log rate limit event
                self._log_rate_limit_exceeded(identifier, rate_limit_info)
                
                return False, rate_limit_info
            
            # Add current request
            self.redis_client.zadd(redis_key, {str(now): now})
            self.redis_client.expire(redis_key, window_seconds)
            
            return True, {
                'limit': limit,
                'window_seconds': window_seconds,
                'current_requests': current_requests + 1,
                'remaining': limit - (current_requests + 1)
            }
        
        except Exception as e:
            logger.error(f"Error checking rate limit: {e}")
            # On error, allow request (fail open)
            return True, None
    
    def _log_rate_limit_exceeded(self, identifier: str, rate_limit_info: Dict):
        """Log rate limit exceed event."""
        conn = get_db_connection()
        if not conn:
            return
        
        try:
            with conn.cursor() as cur:
                create_table_query = """
                    CREATE TABLE IF NOT EXISTS rate_limit_logs (
                        log_id BIGSERIAL PRIMARY KEY,
                        identifier VARCHAR(255),
                        limit_value INTEGER,
                        current_requests INTEGER,
                        endpoint VARCHAR(255),
                        ip_address VARCHAR(255),
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    );
                    
                    CREATE INDEX IF NOT EXISTS idx_rate_limit_logs_timestamp ON rate_limit_logs(created_at);
                    CREATE INDEX IF NOT EXISTS idx_rate_limit_logs_identifier ON rate_limit_logs(identifier);
                """
                cur.execute(create_table_query)
                conn.commit()
                
                insert_query = """
                    INSERT INTO rate_limit_logs 
                    (identifier, limit_value, current_requests, endpoint, ip_address)
                    VALUES (%s, %s, %s, %s, %s)
                """
                cur.execute(insert_query, (
                    identifier,
                    rate_limit_info['limit'],
                    rate_limit_info['current_requests'],
                    request.path if request else 'unknown',
                    request.remote_addr if request else identifier
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Error logging rate limit: {e}")
            if conn:
                conn.rollback()
        finally:
            return_db_connection(conn)


# Singleton instance
_rate_limiter = None

def get_rate_limiter() -> EnhancedRateLimiter:
    """Get singleton rate limiter instance."""
    global _rate_limiter
    if _rate_limiter is None:
        _rate_limiter = EnhancedRateLimiter()
    return _rate_limiter


def rate_limit_decorator(limit: int, window_seconds: int = 60, 
                        key_func=lambda: request.remote_addr):
    """
    Decorator for rate limiting endpoints.
    
    Usage:
        @app.route('/api/endpoint')
        @rate_limit_decorator(limit=100, window_seconds=60)
        def endpoint():
            return jsonify({'status': 'ok'})
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            limiter = get_rate_limiter()
            identifier = key_func()
            
            allowed, rate_limit_info = limiter.check_rate_limit(
                identifier=identifier,
                limit=limit,
                window_seconds=window_seconds,
                key_prefix='rate_limit:endpoint'
            )
            
            if not allowed:
                return jsonify({
                    'error': 'Rate limit exceeded',
                    'retry_after': rate_limit_info['retry_after'],
                    'limit': rate_limit_info['limit'],
                    'window_seconds': rate_limit_info['window_seconds']
                }), 429
            
            response = func(*args, **kwargs)
            
            # Add rate limit headers
            if isinstance(response, tuple):
                response_obj, status_code = response
                if hasattr(response_obj, 'headers'):
                    response_obj.headers['X-RateLimit-Limit'] = str(limit)
                    response_obj.headers['X-RateLimit-Remaining'] = str(rate_limit_info['remaining'])
                    response_obj.headers['X-RateLimit-Reset'] = str(int(time.time() + window_seconds))
                return response_obj, status_code
            
            return response
        return wrapper
    return decorator

