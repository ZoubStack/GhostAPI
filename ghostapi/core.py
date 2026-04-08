"""Core functionality for ghostapi - the expose function."""

import os
import sys
import uuid
import inspect
import logging as logging_module
from typing import Any, Callable, Dict, List, Optional

import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from ghostapi.auth import enable_auth
from ghostapi.config import config
from ghostapi.inspector import ModuleInspector
from ghostapi.router import RouteMapper
from ghostapi.logging_ import add_exception_handlers, setup_logging, get_logger
from ghostapi.rate_limit import add_rate_limiting
from ghostapi.storage import init_storage
from ghostapi.security_headers import add_security_headers
from ghostapi.cache import init_cache, add_cache_middleware
from ghostapi.health import add_health_check
from ghostapi.testing import run_auto_tests


# Global app instance
_app: Optional[FastAPI] = None


def create_app(
    auth: bool = False,
    title: str = "GhostAPI",
    description: str = "Auto-generated REST API",
    version: str = "1.0.0",
    debug: bool = False,
    cors_origins: Optional[List[str]] = None,
    rate_limit: int = 60,
    storage_backend: str = "memory",
    storage_file: str = "ghostapi_data.json",
    max_request_size: int = 1024 * 1024,  # 1MB default
    cache_enabled: bool = False,
    cache_ttl: int = 300,
    health_check: bool = True,
    hooks: Optional[Any] = None
) -> FastAPI:
    """
    Create a FastAPI application.
    
    Args:
        auth: Enable authentication.
        title: API title.
        description: API description.
        version: API version.
        debug: Enable debug mode.
        cors_origins: List of allowed origins for CORS.
        rate_limit: Requests per minute for rate limiting.
        storage_backend: Storage backend type ("memory", "file", "buffered", "async_file").
        storage_file: Path for file storage.
        max_request_size: Maximum request body size in bytes (default 1MB).
        cache_enabled: Enable caching.
        cache_ttl: Cache TTL in seconds.
        health_check: Enable health check endpoints.
        hooks: Custom hooks for request/response processing.
    
    Returns:
        Configured FastAPI application.
    """
    # Initialize storage
    init_storage(backend=storage_backend, file_path=storage_file, force=False)
    
    # Initialize cache if enabled
    if cache_enabled:
        init_cache(default_ttl=cache_ttl)
    
    app = FastAPI(
        title=title,
        description=description,
        version=version,
        debug=debug,
        default_response_class=JSONResponse,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )
    
    # Set request max size
    app.router.default_ws_probing_mode = True
    
    # Add security headers
    add_security_headers(app)
    
    # Add CORS middleware
    if cors_origins is not None:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    # Add rate limiting
    if rate_limit > 0:
        add_rate_limiting(
            app,
            requests_per_minute=rate_limit,
            excluded_paths=["/docs", "/openapi.json", "/redoc", "/api/auth", "/health"]
        )
    
    # Add cache middleware if enabled
    if cache_enabled:
        add_cache_middleware(
            app,
            ttl=cache_ttl,
            excluded_paths=["/docs", "/openapi.json", "/redoc", "/health"]
        )
    
    # Add health check endpoints if enabled
    if health_check:
        add_health_check(app)
    
    # Add hooks if provided
    if hooks is not None:
        from ghostapi.hooks import add_hooks
        add_hooks(app, hooks)
    
    # Add exception handlers
    add_exception_handlers(app)
    
    # Setup logging
    log_level = logging_module.DEBUG if debug else logging_module.INFO
    setup_logging(app, level=log_level)
    
    # Enable auth if requested
    if auth:
        enable_auth(app)
    
    return app
    # Initialize storage
    init_storage(backend=storage_backend, file_path=storage_file, force=False)
    
    app = FastAPI(
        title=title,
        description=description,
        version=version,
        debug=debug,
        default_response_class=JSONResponse,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )
    
    # Set request max size
    app.router.default_ws_probing_mode = True
    
    # Add security headers
    add_security_headers(app)
    
    # Add CORS middleware
    if cors_origins is not None:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
    
    # Add rate limiting
    if rate_limit > 0:
        add_rate_limiting(
            app,
            requests_per_minute=rate_limit,
            excluded_paths=["/docs", "/openapi.json", "/redoc", "/api/auth"]
        )
    
    # Add exception handlers
    add_exception_handlers(app)
    
    # Setup logging
    log_level = logging_module.DEBUG if debug else logging_module.INFO
    setup_logging(app, level=log_level)
    
    # Enable auth if requested
    if auth:
        enable_auth(app)
    
    return app


def get_caller_module() -> Optional[Any]:
    """
    Get the module that called expose().
    
    Returns:
        The caller's module or None.
    """
    frame = inspect.currentframe()
    if frame is None:
        return None
    
    try:
        # Go up the call stack
        frame = frame.f_back
        while frame is not None:
            module_name = frame.f_globals.get("__name__")
            if module_name and module_name != "ghostapi" and module_name != "__main__":
                # Try to get the module
                return frame.f_globals.get("__module__")
            frame = frame.f_back
    except Exception:
        pass
    
    return None


def discover_functions(module: Any) -> Dict[str, Callable]:
    """
    Discover public functions in a module.
    
    Args:
        module: The module to scan.
    
    Returns:
        Dictionary of function name to function.
    """
    inspector = ModuleInspector(module)
    return inspector.scan_module()


def expose(
    auth: bool = False,
    host: str = "127.0.0.1",
    port: int = 8000,
    debug: bool = False,
    title: str = "GhostAPI",
    description: str = "Auto-generated REST API from Python functions",
    version: str = "1.0.0",
    secret: Optional[str] = None,
    expire_minutes: int = 30,
    cors_origins: Optional[List[str]] = None,
    rate_limit: int = 60,
    storage_backend: str = "memory",
    storage_file: str = "ghostapi_data.json",
    cache_enabled: bool = False,
    cache_ttl: int = 300,
    health_check: bool = True,
    hooks: Optional[Any] = None,
    auto_test: bool = False
) -> FastAPI:
    """
    Transform Python functions into a REST API and start the server.
    
    This function:
    1. Scans the caller's module for public functions
    2. Maps functions to HTTP routes (GET, POST, PUT, DELETE)
    3. Optionally enables authentication (JWT + roles)
    4. Starts the FastAPI server
    
    Args:
        auth: Enable JWT authentication.
        host: Server host address.
        port: Server port.
        debug: Enable debug mode.
        title: API title.
        description: API description.
        version: API version.
        secret: JWT secret key (auto-generated if None).
        expire_minutes: Token expiration time in minutes.
        cors_origins: List of allowed origins for CORS.
        rate_limit: Requests per minute for rate limiting (0 to disable).
        storage_backend: Storage backend ("memory", "file", "buffered", "async_file").
        storage_file: Path for file storage.
        cache_enabled: Enable caching.
        cache_ttl: Cache TTL in seconds.
        health_check: Enable health check endpoints.
        hooks: Custom hooks for request/response processing.
        auto_test: Run automatic tests on exposed functions.
    
    Returns:
        The FastAPI application (before server starts).
    
    Example:
        from ghostapi import expose
        
        def get_users():
            return [{"name": "John"}]
        
        def create_user(name: str):
            return {"name": name}
        
        # Expose as API with auth
        expose(auth=True)
        
        # Results in:
        # GET  /users
        # POST /user
    """
    global _app
    
    # Configure
    config.configure(
        auth=auth,
        debug=debug,
        host=host,
        port=port,
        secret=secret,
        expire_minutes=expire_minutes
    )
    
    # Get caller module
    caller_module = get_caller_module()
    
    if caller_module is None:
        raise RuntimeError("Could not determine caller module")
    
    # Discover functions
    functions = discover_functions(caller_module)
    
    if not functions:
        print("Warning: No public functions found to expose")
    
    # Run auto-tests if enabled
    if auto_test or debug:
        print("\n🧪 Running auto-tests on exposed functions...")
        test_results = run_auto_tests(functions)
        print(f"   Tests: {test_results['passed']}/{test_results['total']} passed")
        if test_results['failed'] > 0:
            print(f"   ⚠️  {test_results['failed']} tests failed!")
            for error in test_results.get('errors', [])[:3]:
                print(f"      - {error}")
        print()
    
    # Create FastAPI app
    app = create_app(
        auth=auth,
        title=title,
        description=description,
        version=version,
        debug=debug,
        cors_origins=cors_origins,
        rate_limit=rate_limit,
        storage_backend=storage_backend,
        storage_file=storage_file,
        cache_enabled=cache_enabled,
        cache_ttl=cache_ttl,
        health_check=health_check,
        hooks=hooks
    )
    
    # Create router and map functions
    route_mapper = RouteMapper()
    route_mapper.add_functions(functions, auth_required=auth)
    
    # Include router in app
    app.include_router(route_mapper.get_router())
    
    # Store global reference
    _app = app
    
    # Get logger for startup messages
    logger = get_logger("ghostapi")
    logger.info(f"Starting GhostAPI server on {host}:{port}")
    logger.info(f"Auth: {'Enabled' if auth else 'Disabled'}")
    logger.info(f"Rate limit: {rate_limit} req/min")
    logger.info(f"Functions exposed: {len(functions)}")
    
    # Start server
    print(f"\n🚀 Starting GhostAPI server...")
    print(f"   Host: {host}")
    print(f"   Port: {port}")
    print(f"   Auth: {'Enabled' if auth else 'Disabled'}")
    print(f"   Rate limit: {rate_limit} req/min")
    print(f"   Storage: {storage_backend}")
    print(f"   Functions: {len(functions)}")
    print(f"\n📚 API Documentation: http://{host}:{port}/docs")
    print(f"🛑 Press Ctrl+C to stop\n")
    
    uvicorn.run(app, host=host, port=port, log_level="info" if debug else "warning")
    
    return app


def get_app() -> Optional[FastAPI]:
    """
    Get the current FastAPI application.
    
    Returns:
        The app or None if not created.
    """
    return _app


def create_api(
    auth: bool = False,
    title: str = "GhostAPI",
    description: str = "Auto-generated REST API",
    version: str = "1.0.0",
    debug: bool = False,
    cors_origins: Optional[List[str]] = None,
    rate_limit: int = 60,
    storage_backend: str = "memory",
    storage_file: str = "ghostapi_data.json",
    cache_enabled: bool = False,
    cache_ttl: int = 300,
    health_check: bool = True,
    hooks: Optional[Any] = None
) -> FastAPI:
    """
    Create a FastAPI app without starting the server.
    
    Use this when you want to integrate with custom servers
    or test the API.
    
    Args:
        auth: Enable authentication.
        title: API title.
        description: API description.
        version: API version.
        debug: Enable debug mode.
        cors_origins: List of allowed origins for CORS.
        rate_limit: Requests per minute for rate limiting.
        storage_backend: Storage backend type ("memory", "file", "buffered", "async_file").
        storage_file: Path for file storage.
        cache_enabled: Enable caching.
        cache_ttl: Cache TTL in seconds.
        health_check: Enable health check endpoints.
        hooks: Custom hooks for request/response processing.
    
    Returns:
        The FastAPI application.
    """
    global _app
    
    _app = create_app(
        auth=auth,
        title=title,
        description=description,
        version=version,
        debug=debug,
        cors_origins=cors_origins,
        rate_limit=rate_limit,
        storage_backend=storage_backend,
        storage_file=storage_file,
        cache_enabled=cache_enabled,
        cache_ttl=cache_ttl,
        health_check=health_check,
        hooks=hooks
    )
    
    return _app


def add_routes(
    app: FastAPI,
    functions: Optional[Dict[str, Callable]] = None,
    module: Optional[Any] = None,
    auth_required: bool = False
) -> None:
    """
    Add routes to an existing FastAPI app.
    
    Args:
        app: The FastAPI app.
        functions: Dictionary of functions to add.
        module: Module to scan for functions.
        auth_required: Whether auth is required for routes.
    """
    if functions is None:
        if module is None:
            module = get_caller_module()
        if module is not None:
            functions = discover_functions(module)
        else:
            functions = {}
    
    route_mapper = RouteMapper()
    route_mapper.add_functions(functions, auth_required=auth_required)
    app.include_router(route_mapper.get_router())
