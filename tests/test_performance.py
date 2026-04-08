"""Tests for Performance/Scalability features."""

import pytest
import time
from unittest.mock import Mock, patch

from ghostapi.distributed_cache import (
    RedisCache,
    MemcachedCache,
    CacheBackend,
    create_distributed_cache
)

from ghostapi.rate_limit_advanced import (
    AdvancedRateLimiter,
    RoleRateLimiter,
    TokenRateLimiter,
    RateLimitScope,
    RateLimitAlgorithm,
    get_rate_limiter,
    set_rate_limiter
)

from ghostapi.tasks import (
    task,
    AsyncRunner,
    TaskBackend,
    TaskStatus,
    TaskResult,
    InMemoryTaskQueue,
    BackgroundTasks
)


# ====== Distributed Cache Tests ======

class TestDistributedCache:
    """Tests for distributed caching."""
    
    def test_cache_backend_enum(self):
        """Test cache backend enum."""
        assert CacheBackend.REDIS.value == "redis"
        assert CacheBackend.MEMCACHED.value == "memcached"
        assert CacheBackend.IN_MEMORY.value == "memory"


class TestRedisCache:
    """Tests for Redis cache (mocked)."""
    
    @patch('ghostapi.distributed_cache.redis.Redis')
    def test_redis_cache_initialization(self, mock_redis):
        """Test Redis cache initialization."""
        cache = RedisCache(
            host="localhost",
            port=6379,
            prefix="test:"
        )
        
        assert cache.host == "localhost"
        assert cache.port == 6379
        assert cache.prefix == "test:"
    
    @patch('ghostapi.distributed_cache.redis.Redis')
    def test_redis_cache_get_missing_key(self, mock_redis):
        """Test getting missing key returns None."""
        mock_client = Mock()
        mock_client.get.return_value = None
        
        cache = RedisCache()
        cache._client = mock_client
        
        result = cache.get("missing_key")
        
        assert result is None


class TestMemcachedCache:
    """Tests for Memcached cache (mocked)."""
    
    def test_memcached_cache_initialization(self):
        """Test Memcached cache initialization."""
        cache = MemcachedCache(
            servers=["localhost:11211"],
            prefix="test:"
        )
        
        assert cache.servers == ["localhost:11211"]
        assert cache.prefix == "test:"


class TestCacheFactory:
    """Tests for cache factory function."""
    
    def test_create_redis_cache(self):
        """Test creating Redis cache."""
        with patch('ghostapi.distributed_cache.redis.Redis'):
            cache = create_distributed_cache(
                CacheBackend.REDIS,
                host="localhost"
            )
            
            assert isinstance(cache, RedisCache)
    
    def test_create_memcached_cache(self):
        """Test creating Memcached cache."""
        with patch('ghostapi.distributed_cache.pymemcache.client.base.Client'):
            cache = create_distributed_cache(
                CacheBackend.MEMCACHED,
                servers=["localhost:11211"]
            )
            
            assert isinstance(cache, MemcachedCache)


# ====== Advanced Rate Limiter Tests ======

class TestAdvancedRateLimiter:
    """Tests for advanced rate limiter."""
    
    def test_initialization(self):
        """Test rate limiter initialization."""
        limiter = AdvancedRateLimiter()
        
        assert limiter is not None
        assert len(limiter._rules) == 0
    
    def test_add_rule(self):
        """Test adding rate limit rule."""
        limiter = AdvancedRateLimiter()
        
        limiter.add_rule(
            "test",
            max_calls=10,
            period=60,
            scope=RateLimitScope.IP
        )
        
        assert "test" in limiter._rules
        assert limiter._rules["test"].max_calls == 10
        assert limiter._rules["test"].period == 60
    
    def test_check_sliding_window(self):
        """Test sliding window algorithm."""
        limiter = AdvancedRateLimiter()
        
        limiter.add_rule(
            "test",
            max_calls=3,
            period=60,
            algorithm=RateLimitAlgorithm.SLIDING_WINDOW
        )
        
        # First 3 requests should succeed
        allowed, remaining, reset_time = limiter.check_limit("ip:127.0.0.1", "test")
        assert allowed is True
        assert remaining == 2
        
        allowed, remaining, reset_time = limiter.check_limit("ip:127.0.0.1", "test")
        assert allowed is True
        assert remaining == 1
        
        allowed, remaining, reset_time = limiter.check_limit("ip:127.0.0.1", "test")
        assert allowed is True
        assert remaining == 0
    
    def test_get_stats(self):
        """Test getting rate limiter stats."""
        limiter = AdvancedRateLimiter()
        
        limiter.add_rule("default", 60, 60)
        
        stats = limiter.get_stats()
        
        assert "rules" in stats
        assert "default" in stats["rules"]


class TestRateLimitScope:
    """Tests for rate limit scope enum."""
    
    def test_scope_values(self):
        """Test rate limit scope values."""
        assert RateLimitScope.IP.value == "ip"
        assert RateLimitScope.USER.value == "user"
        assert RateLimitScope.TOKEN.value == "token"
        assert RateLimitScope.ROLE.value == "role"


class TestRateLimitAlgorithm:
    """Tests for rate limit algorithm enum."""
    
    def test_algorithm_values(self):
        """Test algorithm values."""
        assert RateLimitAlgorithm.SLIDING_WINDOW.value == "sliding_window"
        assert RateLimitAlgorithm.FIXED_WINDOW.value == "fixed_window"
        assert RateLimitAlgorithm.TOKEN_BUCKET.value == "token_bucket"


class TestRoleRateLimiter:
    """Tests for role-based rate limiter."""
    
    def test_initialization(self):
        """Test role rate limiter initialization."""
        limiter = RoleRateLimiter()
        
        assert limiter is not None
    
    def test_set_limit(self):
        """Test setting role limits."""
        limiter = RoleRateLimiter()
        
        limiter.set_limit("admin", 1000, 60)
        
        assert "admin" in limiter._limits


class TestTokenRateLimiter:
    """Tests for token-based rate limiter."""
    
    def test_initialization(self):
        """Test token rate limiter initialization."""
        limiter = TokenRateLimiter()
        
        assert limiter is not None
    
    def test_set_token_limit(self):
        """Test setting token limits."""
        limiter = TokenRateLimiter()
        
        limiter.set_token_limit("tok_test", 100, 60)
        
        assert "tok_test" in limiter._token_limits


class TestGlobalRateLimiter:
    """Tests for global rate limiter instance."""
    
    def test_get_rate_limiter(self):
        """Test getting global rate limiter."""
        limiter1 = get_rate_limiter()
        limiter2 = get_rate_limiter()
        
        assert limiter1 is limiter2
    
    def test_set_rate_limiter(self):
        """Test setting global rate limiter."""
        new_limiter = AdvancedRateLimiter()
        set_rate_limiter(new_limiter)
        
        retrieved = get_rate_limiter()
        
        assert retrieved is new_limiter


# ====== Async Task Queue Tests ======

class TestTaskBackend:
    """Tests for task backend enum."""
    
    def test_backend_values(self):
        """Test backend values."""
        assert TaskBackend.CELERY.value == "celery"
        assert TaskBackend.RQ.value == "rq"
        assert TaskBackend.IN_MEMORY.value == "memory"


class TestTaskStatus:
    """Tests for task status enum."""
    
    def test_status_values(self):
        """Test status values."""
        assert TaskStatus.PENDING.value == "pending"
        assert TaskStatus.RUNNING.value == "running"
        assert TaskStatus.COMPLETED.value == "completed"
        assert TaskStatus.FAILED.value == "failed"


class TestTaskResult:
    """Tests for task result dataclass."""
    
    def test_creation(self):
        """Test creating task result."""
        result = TaskResult(
            id="test-123",
            status=TaskStatus.PENDING
        )
        
        assert result.id == "test-123"
        assert result.status == TaskStatus.PENDING
    
    def test_with_result(self):
        """Test task result with data."""
        result = TaskResult(
            id="test-123",
            status=TaskStatus.COMPLETED,
            result={"data": "test"}
        )
        
        assert result.status == TaskStatus.COMPLETED
        assert result.result == {"data": "test"}


class TestInMemoryTaskQueue:
    """Tests for in-memory task queue."""
    
    def test_initialization(self):
        """Test queue initialization."""
        queue = InMemoryTaskQueue(max_workers=2)
        
        assert queue._max_workers == 2
    
    def test_enqueue(self):
        """Test enqueuing a task."""
        queue = InMemoryTaskQueue()
        
        def simple_task():
            return "result"
        
        result = queue.enqueue(simple_task)
        
        assert result is not None
        assert result.id is not None
        assert result.status == TaskStatus.PENDING
        
        # Wait for completion
        time.sleep(0.5)
        
        # Check result
        task_result = queue.get_result(result.id)
        assert task_result.status == TaskStatus.COMPLETED
        assert task_result.result == "result"
    
    def test_stop(self):
        """Test stopping the queue."""
        queue = InMemoryTaskQueue()
        queue.stop()


class TestAsyncRunner:
    """Tests for async runner."""
    
    def test_initialization(self):
        """Test runner initialization."""
        runner = AsyncRunner()
        
        assert runner is not None
    
    def test_enqueue_task(self):
        """Test enqueuing a task."""
        runner = AsyncRunner()
        
        def add_numbers(a, b):
            return a + b
        
        result = runner.enqueue(add_numbers, 2, 3)
        
        assert result is not None
        
        # Wait for completion
        final = runner.wait_for_result(result.id, timeout=5)
        
        assert final is not None
        assert final.status == TaskStatus.COMPLETED
        assert final.result == 5


class TestTaskDecorator:
    """Tests for task decorator."""
    
    def test_task_decorator(self):
        """Test task decorator."""
        
        @task(backend=TaskBackend.IN_MEMORY)
        def multiply(a, b):
            return a * b
        
        assert hasattr(multiply, 'delay')
        assert hasattr(multiply, 'task_queue')


class TestBackgroundTasks:
    """Tests for background tasks."""
    
    def test_initialization(self):
        """Test background tasks initialization."""
        bg_tasks = BackgroundTasks()
        
        assert bg_tasks is not None
    
    def test_add_task(self):
        """Test adding a task."""
        bg_tasks = BackgroundTasks()
        
        def dummy_task():
            return "done"
        
        bg_tasks.add_task(dummy_task)
        
        assert len(bg_tasks._tasks) == 1
