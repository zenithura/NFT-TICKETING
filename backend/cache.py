"""In-memory caching layer for API responses and database queries."""
import hashlib
import json
import time
from typing import Any, Optional, Callable
from functools import wraps
from datetime import datetime, timedelta

# In-memory cache store
_cache: dict[str, dict[str, Any]] = {}

# Cache configuration
DEFAULT_TTL = 300  # 5 minutes
MAX_CACHE_SIZE = 1000  # Maximum number of cached items


def _generate_cache_key(prefix: str, *args, **kwargs) -> str:
    """Generate a unique cache key from arguments."""
    key_data = {
        'prefix': prefix,
        'args': args,
        'kwargs': sorted(kwargs.items()) if kwargs else {}
    }
    key_str = json.dumps(key_data, sort_keys=True, default=str)
    return f"{prefix}:{hashlib.md5(key_str.encode()).hexdigest()}"


def _cleanup_expired():
    """Remove expired cache entries."""
    global _cache
    now = time.time()
    expired_keys = [
        key for key, value in _cache.items()
        if value.get('expires_at', 0) < now
    ]
    for key in expired_keys:
        _cache.pop(key, None)


def _evict_lru():
    """Evict least recently used entries if cache is full."""
    global _cache
    if len(_cache) >= MAX_CACHE_SIZE:
        # Sort by last accessed time and remove oldest 10%
        sorted_items = sorted(
            _cache.items(),
            key=lambda x: x[1].get('last_accessed', 0)
        )
        to_remove = int(MAX_CACHE_SIZE * 0.1)  # Remove 10%
        for key, _ in sorted_items[:to_remove]:
            _cache.pop(key, None)


def get(key: str) -> Optional[Any]:
    """Get value from cache."""
    _cleanup_expired()
    
    if key in _cache:
        entry = _cache[key]
        if entry.get('expires_at', 0) >= time.time():
            entry['last_accessed'] = time.time()
            return entry['value']
        else:
            # Expired, remove it
            _cache.pop(key, None)
    return None


def set(key: str, value: Any, ttl: int = DEFAULT_TTL) -> None:
    """Set value in cache with TTL."""
    _cleanup_expired()
    _evict_lru()
    
    _cache[key] = {
        'value': value,
        'expires_at': time.time() + ttl,
        'last_accessed': time.time(),
        'created_at': time.time()
    }


def delete(key: str) -> None:
    """Delete a cache entry."""
    _cache.pop(key, None)


def clear(prefix: Optional[str] = None) -> None:
    """Clear cache entries, optionally filtered by prefix."""
    global _cache
    if prefix:
        keys_to_remove = [key for key in _cache.keys() if key.startswith(prefix)]
        for key in keys_to_remove:
            _cache.pop(key, None)
    else:
        _cache.clear()


def cached(ttl: int = DEFAULT_TTL, prefix: str = "cache"):
    """Decorator to cache function results."""
    def decorator(func: Callable):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            cache_key = _generate_cache_key(f"{prefix}:{func.__name__}", *args, **kwargs)
            cached_value = get(cache_key)
            
            if cached_value is not None:
                return cached_value
            
            result = await func(*args, **kwargs)
            set(cache_key, result, ttl)
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            cache_key = _generate_cache_key(f"{prefix}:{func.__name__}", *args, **kwargs)
            cached_value = get(cache_key)
            
            if cached_value is not None:
                return cached_value
            
            result = func(*args, **kwargs)
            set(cache_key, result, ttl)
            return result
        
        # Return appropriate wrapper based on function type
        import inspect
        if inspect.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def get_cache_stats() -> dict:
    """Get cache statistics."""
    _cleanup_expired()
    return {
        'size': len(_cache),
        'max_size': MAX_CACHE_SIZE,
        'usage_percent': (len(_cache) / MAX_CACHE_SIZE) * 100,
        'entries': list(_cache.keys())[:10]  # First 10 keys for debugging
    }

