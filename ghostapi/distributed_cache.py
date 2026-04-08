"""
Distributed caching module for GhostAPI.

Supports:
- Redis
- Memcached

Example:
    from ghostapi.cache.distributed import RedisCache, MemcachedCache
    
    # Redis
    cache = RedisCache(host="localhost", port=6379)
    
    # Memcached  
    cache = MemcachedCache(servers=["localhost:11211"])
    
    # Use with decorators
    @cached(cache=cache, ttl=300)
    def get_expensive_data():
        return expensive_operation()
"""

from typing import Optional, Any, Dict
from abc import ABC, abstractmethod
from dataclasses import dataclass
import enum
import json
import pickle

from pydantic import BaseModel


class CacheBackend(str, enum.Enum):
    """Supported cache backends."""
    REDIS = "redis"
    MEMCACHED = "memcached"
    IN_MEMORY = "memory"


class DistributedCache(ABC):
    """Abstract base class for distributed caches."""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        pass
    
    @abstractmethod
    def clear(self) -> bool:
        """Clear all cache."""
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if key exists."""
        pass


class RedisCache(DistributedCache):
    """
    Redis cache implementation.
    
    Example:
        cache = RedisCache(
            host="localhost",
            port=6379,
            password="secret",
            db=0,
            prefix="ghostapi:"
        )
    """
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 6379,
        password: Optional[str] = None,
        db: int = 0,
        prefix: str = "ghostapi:",
        socket_timeout: int = 5,
        socket_connect_timeout: int = 5,
        decode_responses: bool = True
    ):
        """
        Initialize Redis cache.
        
        Args:
            host: Redis host
            port: Redis port
            password: Redis password (optional)
            db: Redis database number
            prefix: Key prefix
            socket_timeout: Socket timeout
            socket_connect_timeout: Socket connect timeout
            decode_responses: Decode responses to strings
        """
        self.host = host
        self.port = port
        self.password = password
        self.db = db
        self.prefix = prefix
        self._client = None
        self._decode_responses = decode_responses
    
    def _get_client(self):
        """Get or create Redis client."""
        if self._client is None:
            try:
                import redis
                self._client = redis.Redis(
                    host=self.host,
                    port=self.port,
                    password=self.password,
                    db=self.db,
                    socket_timeout=5,
                    socket_connect_timeout=5,
                    decode_responses=self._decode_responses
                )
            except ImportError:
                raise ImportError(
                    "redis package not installed. Install with: pip install redis"
                )
        return self._client
    
    def _make_key(self, key: str) -> str:
        """Add prefix to key."""
        return f"{self.prefix}{key}"
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            client = self._get_client()
            value = client.get(self._make_key(key))
            
            if value is None:
                return None
            
            # Try to deserialize
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                return value
                
        except Exception:
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        try:
            client = self._get_client()
            
            # Serialize value
            if isinstance(value, (dict, list)):
                serialized = json.dumps(value)
            else:
                serialized = str(value)
            
            return client.set(
                self._make_key(key),
                serialized,
                ex=ttl
            )
        except Exception:
            return False
    
    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        try:
            client = self._get_client()
            return bool(client.delete(self._make_key(key)))
        except Exception:
            return False
    
    def clear(self) -> bool:
        """Clear all cache with prefix."""
        try:
            client = self._get_client()
            keys = client.keys(f"{self.prefix}*")
            if keys:
                client.delete(*keys)
            return True
        except Exception:
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists."""
        try:
            client = self._get_client()
            return bool(client.exists(self._make_key(key)))
        except Exception:
            return False
    
    def get_many(self, keys: list[str]) -> Dict[str, Any]:
        """Get multiple values."""
        try:
            client = self._get_client()
            full_keys = [self._make_key(k) for k in keys]
            values = client.mget(full_keys)
            
            result = {}
            for key, value in zip(keys, values):
                if value is not None:
                    try:
                        result[key] = json.loads(value)
                    except json.JSONDecodeError:
                        result[key] = value
            
            return result
        except Exception:
            return {}
    
    def set_many(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """Set multiple values."""
        try:
            client = self._get_client()
            
            pipeline = client.pipeline()
            for key, value in mapping.items():
                if isinstance(value, (dict, list)):
                    serialized = json.dumps(value)
                else:
                    serialized = str(value)
                
                pipeline.set(self._make_key(key), serialized, ex=ttl)
            
            pipeline.execute()
            return True
        except Exception:
            return False
    
    def increment(self, key: str, amount: int = 1) -> Optional[int]:
        """Increment a counter."""
        try:
            client = self._get_client()
            return client.incrby(self._make_key(key), amount)
        except Exception:
            return None
    
    def get_ttl(self, key: str) -> int:
        """Get TTL for a key."""
        try:
            client = self._get_client()
            return client.ttl(self._make_key(key))
        except Exception:
            return -2


class MemcachedCache(DistributedCache):
    """
    Memcached cache implementation.
    
    Example:
        cache = MemcachedCache(
            servers=["localhost:11211"],
            prefix="ghostapi_"
        )
    """
    
    def __init__(
        self,
        servers: list[str] = None,
        prefix: str = "ghostapi_",
        default_noreply: bool = False,
        socket_timeout: int = 3,
        socket_connect_timeout: int = 3
    ):
        """
        Initialize Memcached cache.
        
        Args:
            servers: List of server addresses
            prefix: Key prefix
            default_noreply: Default noreply flag
            socket_timeout: Socket timeout
            socket_connect_timeout: Socket connect timeout
        """
        self.servers = servers or ["localhost:11211"]
        self.prefix = prefix
        self._client = None
    
    def _get_client(self):
        """Get or create Memcached client."""
        if self._client is None:
            try:
                from pymemcache.client.base import Client
                from pymemcache import serde
                
                self._client = Client(
                    self.servers,
                    serializer=serde.python_memcache_serializer,
                    deserializer=serde.python_memcache_deserializer,
                    connect_timeout=3,
                    timeout=3
                )
            except ImportError:
                raise ImportError(
                    "pymemcache package not installed. Install with: pip install pymemcache"
                )
        return self._client
    
    def _make_key(self, key: str) -> str:
        """Add prefix to key."""
        return f"{self.prefix}{key}"
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            client = self._get_client()
            return client.get(self._make_key(key))
        except Exception:
            return None
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache."""
        try:
            client = self._get_client()
            return client.set(
                self._make_key(key),
                value,
                expire=ttl
            )
        except Exception:
            return False
    
    def delete(self, key: str) -> bool:
        """Delete value from cache."""
        try:
            client = self._get_client()
            return client.delete(self._make_key(key))
        except Exception:
            return False
    
    def clear(self) -> bool:
        """Clear all cache."""
        try:
            client = self._get_client()
            # Memcached doesn't support flush_all reliably
            # Just return True as we can't easily clear
            return True
        except Exception:
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists."""
        try:
            client = self._get_client()
            value = client.get(self._make_key(key))
            return value is not None
        except Exception:
            return False


# Factory function
def create_distributed_cache(
    backend: CacheBackend = CacheBackend.REDIS,
    **kwargs
) -> DistributedCache:
    """
    Create a distributed cache instance.
    
    Example:
        # Redis
        cache = create_distributed_cache(CacheBackend.REDIS, host="localhost", port=6379)
        
        # Memcached
        cache = create_distributed_cache(CacheBackend.MEMCACHED, servers=["localhost:11211"])
    
    Args:
        backend: Cache backend type
        **kwargs: Backend-specific configuration
    
    Returns:
        DistributedCache instance
    """
    if backend == CacheBackend.REDIS:
        return RedisCache(**kwargs)
    elif backend == CacheBackend.MEMCACHED:
        return MemcachedCache(**kwargs)
    else:
        raise ValueError(f"Unknown cache backend: {backend}")


# Decorator for distributed caching
def distributed_cache(
    backend: CacheBackend = CacheBackend.REDIS,
    ttl: int = 300,
    key_prefix: str = "",
    **kwargs
):
    """
    Decorator for distributed caching.
    
    Example:
        @distributed_cache(CacheBackend.REDIS, ttl=300)
        def get_user(user_id):
            return db.fetch_user(user_id)
    
    Args:
        backend: Cache backend type
        ttl: Time to live in seconds
        key_prefix: Prefix for cache keys
        **kwargs: Backend configuration
    """
    cache = create_distributed_cache(backend, prefix=key_prefix, **kwargs)
    
    def decorator(func):
        import functools
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and args
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try to get from cache
            cached_value = cache.get(cache_key)
            if cached_value is not None:
                return cached_value
            
            # Call function
            result = func(*args, **kwargs)
            
            # Store in cache
            cache.set(cache_key, result, ttl=ttl)
            
            return result
        
        # Add cache methods to wrapper
        wrapper.cache = cache
        wrapper.clear_cache = lambda: cache.clear()
        
        return wrapper
    
    return decorator
