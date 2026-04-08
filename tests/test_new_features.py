"""Tests for new GhostAPI features: cache, hooks, decorators, health, storage."""

import pytest
import time
from fastapi.testclient import TestClient

from ghostapi import create_api
from ghostapi.cache import (
    get_cache, set_cache, init_cache, clear_cache, 
    get_cache_stats, InMemoryCache
)
from ghostapi.storage import (
    init_storage, get_storage, InMemoryStorage, 
    FileStorage, BufferedFileStorage
)
from ghostapi.health import add_health_check, get_health_check
from ghostapi.hooks import Hooks, MetricsCollector
from ghostapi.core import add_routes


# Test functions
def get_data():
    """Simple data function."""
    return {"data": "test"}


def get_expensive_data():
    """Simulate expensive computation."""
    return {"computed": time.time()}


class TestCache:
    """Test cache functionality."""
    
    def setup_method(self):
        """Setup before each test."""
        init_cache(default_ttl=60)
        clear_cache()
    
    def test_cache_set_get(self):
        """Test basic cache set and get."""
        cache = get_cache()
        cache.set("key1", {"value": "test"})
        
        result = cache.get("key1")
        assert result == {"value": "test"}
    
    def test_cache_miss(self):
        """Test cache miss returns None."""
        cache = get_cache()
        result = cache.get("nonexistent")
        assert result is None
    
    def test_cache_expiration(self):
        """Test cache expiration."""
        cache = get_cache()
        cache.set("key1", "value", ttl=1)
        
        # Should exist immediately
        assert cache.get("key1") == "value"
        
        # Wait for expiration
        time.sleep(1.5)
        
        # Should be expired
        assert cache.get("key1") is None
    
    def test_cache_delete(self):
        """Test cache delete."""
        cache = get_cache()
        cache.set("key1", "value")
        assert cache.get("key1") == "value"
        
        cache.delete("key1")
        assert cache.get("key1") is None
    
    def test_cache_clear(self):
        """Test cache clear."""
        cache = get_cache()
        cache.set("key1", "value1")
        cache.set("key2", "value2")
        
        count = clear_cache()
        assert count == 2
        assert cache.get("key1") is None
    
    def test_cache_stats(self):
        """Test cache statistics."""
        cache = get_cache()
        cache.set("key1", "value1")
        
        stats = get_cache_stats()
        assert stats["total_entries"] >= 1
        assert stats["default_ttl"] == 60


class TestInMemoryCache:
    """Test InMemoryCache class."""
    
    def test_initialization(self):
        """Test cache initialization."""
        cache = InMemoryCache(default_ttl=120)
        assert cache.default_ttl == 120
    
    def test_key_generation(self):
        """Test cache key generation."""
        cache = InMemoryCache()
        key1 = cache._generate_key("test", 1, 2, 3)
        key2 = cache._generate_key("test", 1, 2, 3)
        assert key1 == key2


class TestStorage:
    """Test storage backends."""
    
    def setup_method(self):
        """Setup before each test."""
        init_storage(backend="memory", force=True)
    
    def test_inmemory_storage(self):
        """Test in-memory storage."""
        storage = get_storage()
        storage.set("user1", {"name": "John"})
        
        user = storage.get("user1")
        assert user["name"] == "John"
    
    def test_storage_get_all(self):
        """Test getting all items."""
        storage = get_storage()
        storage.set("user1", {"name": "John"})
        storage.set("user2", {"name": "Jane"})
        
        all_users = storage.get_all()
        assert len(all_users) >= 2
    
    def test_storage_delete(self):
        """Test deleting items."""
        storage = get_storage()
        storage.set("user1", {"name": "John"})
        
        result = storage.delete("user1")
        assert result is True
        assert storage.get("user1") is None
    
    def test_storage_clear(self):
        """Test clearing storage."""
        storage = get_storage()
        storage.set("user1", {"name": "John"})
        storage.set("user2", {"name": "Jane"})
        
        storage.clear()
        
        all_users = storage.get_all()
        assert len(all_users) == 0


class TestBufferedFileStorage:
    """Test BufferedFileStorage."""
    
    def test_initialization(self):
        """Test BufferedFileStorage initialization."""
        storage = BufferedFileStorage(
            file_path="test_buffered.json",
            buffer_size=5,
            flush_interval=10
        )
        assert storage._buffer_size == 5
        assert storage._flush_interval == 10
    
    def test_set_and_get(self):
        """Test set and get operations."""
        storage = BufferedFileStorage(file_path="test_buffered.json")
        storage.set("key1", {"value": "test"})
        
        result = storage.get("key1")
        assert result["value"] == "test"


class TestHealthCheck:
    """Test health check functionality."""
    
    def test_health_endpoint(self):
        """Test /health endpoint."""
        app = create_api(health_check=True)
        
        client = TestClient(app)
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "uptime_seconds" in data
        assert "components" in data
    
    def test_readiness_endpoint(self):
        """Test /health/ready endpoint."""
        app = create_api(health_check=True)
        
        client = TestClient(app)
        response = client.get("/health/ready")
        
        assert response.status_code == 200
        data = response.json()
        assert "ready" in data
    
    def test_liveness_endpoint(self):
        """Test /health/live endpoint."""
        app = create_api(health_check=True)
        
        client = TestClient(app)
        response = client.get("/health/live")
        
        assert response.status_code == 200
        data = response.json()
        assert data["alive"] is True
    
    def test_health_check_manager(self):
        """Test HealthCheck manager."""
        health = get_health_check()
        
        # Register a custom check
        health.register_check("custom", lambda: True)
        
        status = health.get_status()
        assert status["components"]["custom"] == "ok"


class TestHooks:
    """Test hooks functionality."""
    
    def test_hooks_creation(self):
        """Test creating hooks."""
        hooks = Hooks(
            before_request=lambda r: None,
            after_response=lambda r, r2: r2
        )
        
        assert hooks.before_request is not None
        assert hooks.after_response is not None
    
    def test_metrics_collector(self):
        """Test MetricsCollector."""
        collector = MetricsCollector()
        
        # Record some requests
        stats = collector.get_stats()
        assert stats["total_requests"] == 0
        assert "uptime" in stats


class TestDecorators:
    """Test custom decorators."""
    
    def test_rate_limit_decorator(self):
        """Test rate limit decorator is importable."""
        from ghostapi.decorators import rate_limit
        
        @rate_limit(max_calls=5, period=60)
        def test_func():
            return {"result": "ok"}
        
        # Function should be callable
        assert callable(test_func)


class TestCacheMiddleware:
    """Test cache middleware."""
    
    def test_cache_middleware_creation(self):
        """Test cache middleware can be created."""
        from ghostapi.cache import CacheMiddleware
        
        app = create_api(cache_enabled=True, cache_ttl=60)
        
        client = TestClient(app)
        
        # First request - should not be cached yet
        response = client.get("/docs")
        assert response.status_code == 200


class TestStorageBackends:
    """Test different storage backends."""
    
    def test_memory_backend(self):
        """Test memory storage backend."""
        init_storage(backend="memory", force=True)
        storage = get_storage()
        
        storage.set("key1", {"value": "test"})
        assert storage.get("key1")["value"] == "test"
    
    def test_file_backend(self):
        """Test file storage backend."""
        init_storage(backend="file", file_path="test_data.json", force=True)
        storage = get_storage()
        
        storage.set("key1", {"value": "test"})
        assert storage.get("key1")["value"] == "test"
        
        # Cleanup
        storage.clear()
    
    def test_buffered_backend(self):
        """Test buffered storage backend."""
        init_storage(backend="buffered", file_path="test_buffered.json", force=True)
        storage = get_storage()
        
        storage.set("key1", {"value": "test"})
        assert storage.get("key1")["value"] == "test"
        
        # Cleanup
        storage.clear()


class TestErrorMessages:
    """Test improved error messages."""
    
    def test_validation_error_message(self):
        """Test validation error returns clear message."""
        def get_user(age: int):
            return {"age": age}
        
        app = create_api()
        add_routes(app, {"get_user": get_user})
        
        client = TestClient(app)
        
        # Send invalid parameter (string instead of int)
        response = client.get("/user?age=abc")
        
        # Should return 400 with clear error message
        assert response.status_code == 400
        assert "doit être" in response.json()["detail"]


class TestNewExposeOptions:
    """Test new options in expose/create_api."""
    
    def test_cache_option(self):
        """Test cache_enabled option."""
        app = create_api(cache_enabled=True, cache_ttl=120)
        assert app is not None
    
    def test_health_option(self):
        """Test health_check option."""
        app = create_api(health_check=True)
        
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 200
    
    def test_health_disabled(self):
        """Test health_check disabled."""
        app = create_api(health_check=False)
        
        client = TestClient(app)
        response = client.get("/health")
        assert response.status_code == 404
