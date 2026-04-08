"""GhostAPI - Transform Python functions into REST APIs instantly.

Quick Start:
    from ghostapi import expose
    
    def hello():
        return "Hello World"
    
    def get_user(user_id: int):
        return {"id": user_id, "name": "John"}
    
    def create_user(name: str, email: str):
        return {"name": name, "email": email}
    
    # Expose as API
    expose()

With Authentication:
    from ghostapi import expose
    
    def get_data():
        return {"data": "secret"}
    
    expose(auth=True)

This will create:
    - GET  /hello
    - GET  /user?user_id=1
    - POST /user (with name, email in body)
    - GET  /data (requires auth)

Visit http://127.0.0.1:8000/docs for interactive API documentation.
"""

from ghostapi.core import (
    expose,
    create_api,
    get_app,
    add_routes
)
from ghostapi.auth import (
    enable_auth,
    require_role,
    has_role,
    get_current_user
)
from ghostapi.storage import (
    get_storage,
    set_storage,
    init_storage,
    StorageBackend,
    InMemoryStorage,
    FileStorage,
    BufferedFileStorage,
    AsyncFileStorage
)
from ghostapi.security_headers import add_security_headers

# New features - Cache
from ghostapi.cache import (
    get_cache,
    set_cache,
    init_cache,
    cached,
    clear_cache,
    get_cache_stats,
    add_cache_middleware,
    InMemoryCache
)

# New features - Hooks
from ghostapi.hooks import (
    Hooks,
    add_hooks,
    create_request_logger,
    create_response_timer,
    MetricsCollector
)

# New features - Decorators
from ghostapi.decorators import (
    cache,
    rate_limit,
    require_auth,
    retry,
    timeout,
    validate_params
)

# New features - Health
from ghostapi.health import (
    add_health_check,
    get_health_check
)

# New features - Testing
from ghostapi.testing import (
    TestGenerator,
    AutoTester,
    ContinuousTester,
    auto_test,
    run_auto_tests
)

# New features - Hot Reload
from ghostapi.hotreload import (
    FunctionWatcher,
    FunctionReloader,
    hot_reload,
    setup_hot_reload
)

# New features - Tasks / Async Queue
from ghostapi.tasks import (
    task,
    AsyncRunner,
    BackgroundTasks,
    run_in_background,
    TaskBackend,
    TaskStatus,
    TaskResult,
    InMemoryTaskQueue,
    CeleryTaskQueue,
    RQTaskQueue
)

# New features - Distributed Cache
from ghostapi.distributed_cache import (
    RedisCache,
    MemcachedCache,
    CacheBackend,
    create_distributed_cache,
    distributed_cache
)

# New features - Advanced Rate Limiter
from ghostapi.rate_limit_advanced import (
    AdvancedRateLimiter,
    RoleRateLimiter,
    TokenRateLimiter,
    RateLimitScope,
    RateLimitAlgorithm,
    get_rate_limiter,
    set_rate_limiter
)

# New features - Monitoring / Metrics
from ghostapi.monitoring import (
    MetricsCollector,
    MonitoringMiddleware,
    PerformanceProfiler,
    profile_block,
    setup_monitoring,
    get_metrics_collector,
    get_profiler
)

# New features - Test Generator
from ghostapi.test_generator import (
    AutoTestGenerator,
    TypeTestGenerator,
    TestCase,
    MockDataGenerator,
    get_test_generator,
    get_mock_generator
)

__version__ = "0.1.0"
__author__ = "GhostAPI Team"

__all__ = [
    # Main functions
    "expose",
    "create_api",
    "get_app",
    "add_routes",
    
    # Auth
    "enable_auth",
    "require_role",
    "has_role",
    "get_current_user",
    
    # Storage
    "get_storage",
    "set_storage",
    "init_storage",
    "StorageBackend",
    "InMemoryStorage",
    "FileStorage",
    "BufferedFileStorage",
    "AsyncFileStorage",
    
    # Cache
    "get_cache",
    "set_cache",
    "init_cache",
    "cached",
    "clear_cache",
    "get_cache_stats",
    "add_cache_middleware",
    "InMemoryCache",
    
    # Hooks
    "Hooks",
    "add_hooks",
    "create_request_logger",
    "create_response_timer",
    "MetricsCollector",
    
    # Decorators
    "cache",
    "rate_limit",
    "require_auth",
    "retry",
    "timeout",
    "validate_params",
    
    # Health
    "add_health_check",
    "get_health_check",
    
    # Hot Reload
    "FunctionWatcher",
    "FunctionReloader",
    "hot_reload",
    "setup_hot_reload",
    
    # Tasks / Async Queue
    "task",
    "AsyncRunner",
    "BackgroundTasks",
    "run_in_background",
    "TaskBackend",
    "TaskStatus",
    "TaskResult",
    "InMemoryTaskQueue",
    "CeleryTaskQueue",
    "RQTaskQueue",
    
    # Distributed Cache
    "RedisCache",
    "MemcachedCache",
    "CacheBackend",
    "create_distributed_cache",
    "distributed_cache",
    
    # Advanced Rate Limiter
    "AdvancedRateLimiter",
    "RoleRateLimiter",
    "TokenRateLimiter",
    "RateLimitScope",
    "RateLimitAlgorithm",
    "get_rate_limiter",
    "set_rate_limiter",
    
    # Monitoring / Metrics
    "MetricsCollector",
    "MonitoringMiddleware",
    "PerformanceProfiler",
    "profile_block",
    "setup_monitoring",
    "get_metrics_collector",
    "get_profiler",
    
    # Test Generator
    "AutoTestGenerator",
    "TypeTestGenerator",
    "TestCase",
    "MockDataGenerator",
    "get_test_generator",
    "get_mock_generator",
    
    # Version
    "__version__",
]
