"""Cache system for ghostapi."""

import asyncio
import hashlib
import json
import time
from collections import defaultdict
from typing import Any, Callable, Dict, Optional
from functools import wraps

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class CacheEntry:
    """Represents a cached value with TTL."""
    
    def __init__(self, value: Any, ttl: int) -> None:
        self.value = value
        self.expires_at = time.time() + ttl
    
    def is_expired(self) -> bool:
        return time.time() > self.expires_at


class InMemoryCache:
    """In-memory cache with TTL support."""
    
    def __init__(self, default_ttl: int = 300) -> None:
        self._cache: Dict[str, CacheEntry] = {}
        self.default_ttl = default_ttl
    
    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate a cache key from arguments."""
        key_data = f"{prefix}:{args}:{sorted(kwargs.items())}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, key: str) -> Optional[Any]:
        """Get a value from cache."""
        if key in self._cache:
            entry = self._cache[key]
            if not entry.is_expired():
                return entry.value
            # Remove expired entry
            del self._cache[key]
        return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set a value in cache."""
        ttl = ttl or self.default_ttl
        self._cache[key] = CacheEntry(value, ttl)
    
    def delete(self, key: str) -> bool:
        """Delete a key from cache."""
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    def clear(self) -> None:
        """Clear all cache."""
        self._cache.clear()
    
    def cleanup_expired(self) -> int:
        """Remove expired entries and return count."""
        expired_keys = [
            key for key, entry in self._cache.items()
            if entry.is_expired()
        ]
        for key in expired_keys:
            del self._cache[key]
        return len(expired_keys)


# Global cache instance
_cache: Optional[InMemoryCache] = None


def get_cache() -> InMemoryCache:
    """Get the global cache instance."""
    global _cache
    if _cache is None:
        _cache = InMemoryCache()
    return _cache


def set_cache(cache: InMemoryCache) -> None:
    """Set the global cache instance."""
    global _cache
    _cache = cache


def init_cache(default_ttl: int = 300) -> InMemoryCache:
    """Initialize the cache."""
    global _cache
    _cache = InMemoryCache(default_ttl)
    return _cache


def cache_key(prefix: str, *args, **kwargs) -> str:
    """Generate a cache key."""
    return get_cache()._generate_key(prefix, *args, **kwargs)


def cached(ttl: int = 300, key_prefix: Optional[str] = None):
    """
    Decorator to cache function results.
    
    Args:
        ttl: Time to live in seconds (default 5 minutes).
        key_prefix: Prefix for cache key (defaults to function name).
    
    Example:
        @cached(ttl=60)
        def get_expensive_data():
            return expensive_computation()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            cache = get_cache()
            prefix = key_prefix or func.__name__
            key = cache._generate_key(prefix, *args, **kwargs)
            
            # Try to get from cache
            cached_value = cache.get(key)
            if cached_value is not None:
                return cached_value
            
            # Call function
            result = func(*args, **kwargs)
            
            # Handle coroutines
            if asyncio.iscoroutine(result):
                result = await result
            
            # Store in cache
            cache.set(key, result, ttl)
            
            return result
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            cache = get_cache()
            prefix = key_prefix or func.__name__
            key = cache._generate_key(prefix, *args, **kwargs)
            
            # Try to get from cache
            cached_value = cache.get(key)
            if cached_value is not None:
                return cached_value
            
            # Call function
            result = func(*args, **kwargs)
            
            # Store in cache
            cache.set(key, result, ttl)
            
            return result
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


class CacheMiddleware(BaseHTTPMiddleware):
    """Middleware for HTTP-level caching."""
    
    def __init__(
        self,
        app,
        ttl: int = 300,
        excluded_paths: Optional[list] = None,
        methods: Optional[list] = None
    ) -> None:
        super().__init__(app)
        self.ttl = ttl
        self.excluded_paths = excluded_paths or ["/docs", "/openapi.json", "/redoc", "/health"]
        self.methods = methods or ["GET"]
        self.cache = get_cache()
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Skip for non-cached methods
        if request.method not in self.methods:
            return await call_next(request)
        
        # Skip for excluded paths
        if any(request.url.path.startswith(path) for path in self.excluded_paths):
            return await call_next(request)
        
        # Generate cache key from request
        cache_key = f"{request.method}:{request.url.path}:{request.query_params}"
        key_hash = hashlib.md5(cache_key.encode()).hexdigest()
        
        # Try to get cached response
        cached_response = self.cache.get(key_hash)
        if cached_response is not None:
            return cached_response
        
        # Call the endpoint
        response = await call_next(request)
        
        # Only cache successful responses
        if response.status_code == 200:
            # Store response in cache
            self.cache.set(key_hash, response, self.ttl)
        
        return response


def add_cache_middleware(
    app: FastAPI,
    ttl: int = 300,
    excluded_paths: Optional[list] = None,
    methods: Optional[list] = None
) -> None:
    """
    Add cache middleware to the application.
    
    Args:
        app: The FastAPI application.
        ttl: Cache TTL in seconds.
        excluded_paths: Paths to exclude from caching.
        methods: HTTP methods to cache.
    """
    app.add_middleware(
        CacheMiddleware,
        ttl=ttl,
        excluded_paths=excluded_paths,
        methods=methods
    )


# Cache management commands
def clear_cache() -> int:
    """Clear all cached values."""
    cache = get_cache()
    count = len(cache._cache)
    cache.clear()
    return count


def get_cache_stats() -> Dict[str, Any]:
    """Get cache statistics."""
    cache = get_cache()
    expired_count = cache.cleanup_expired()
    return {
        "total_entries": len(cache._cache),
        "default_ttl": cache.default_ttl,
        "expired_cleaned": expired_count
    }
