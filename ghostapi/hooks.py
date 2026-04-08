"""Hooks system for customizing GhostAPI behavior."""

import time
from typing import Any, Callable, Dict, List, Optional
from dataclasses import dataclass, field

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


@dataclass
class Hooks:
    """
    Container for custom hooks to customize GhostAPI behavior.
    
    Example:
        def log_request(request):
            print(f"Request: {request.method} {request.url}")
        
        def before_response(response):
            response.headers["X-API-Version"] = "1.0.0"
            return response
        
        hooks = Hooks(
            before_request=log_request,
            after_response=before_response
        )
        
        expose(hooks=hooks)
    """
    # Request hooks
    before_request: Optional[Callable[[Request], None]] = None
    after_request: Optional[Callable[[Request, Response], Response]] = None
    
    # Response hooks
    before_response: Optional[Callable[[Response], Response]] = None
    after_response: Optional[Callable[[Request, Response], Response]] = None
    
    # Error hooks
    on_error: Optional[Callable[[Request, Exception], Response]] = None
    on_validation_error: Optional[Callable[[Request, Exception], Response]] = None
    on_auth_error: Optional[Callable[[Request, Exception], Response]] = None
    
    # Auth hooks
    on_auth_success: Optional[Callable[[Request, Dict], None]] = None
    on_login: Optional[Callable[[Request, str], None]] = None
    on_logout: Optional[Callable[[Request, str], None]] = None
    on_register: Optional[Callable[[Request, str], None]] = None
    
    # Rate limit hooks
    on_rate_limit_exceeded: Optional[Callable[[Request], None]] = None
    
    # Cache hooks
    on_cache_hit: Optional[Callable[[str], None]] = None
    on_cache_miss: Optional[Callable[[str], None]] = None


class HooksMiddleware(BaseHTTPMiddleware):
    """Middleware to execute hooks."""
    
    def __init__(self, app: FastAPI, hooks: Hooks) -> None:
        super().__init__(app)
        self.hooks = hooks
    
    async def dispatch(self, request: Request, call_next) -> Response:
        # Before request hook
        if self.hooks.before_request:
            try:
                self.hooks.before_request(request)
            except Exception:
                pass  # Don't fail request if hook fails
        
        try:
            response = await call_next(request)
            
            # After request hook
            if self.hooks.after_request:
                response = self.hooks.after_request(request, response) or response
            
            # Before response hook
            if self.hooks.before_response:
                response = self.hooks.before_response(response)
            
            # After response hook
            if self.hooks.after_response:
                response = self.hooks.after_response(request, response)
            
            return response
            
        except Exception as e:
            # Error hook
            if self.hooks.on_error:
                try:
                    return self.hooks.on_error(request, e)
                except Exception:
                    pass
            
            # Re-raise if no custom handler
            raise


def add_hooks(app: FastAPI, hooks: Hooks) -> None:
    """
    Add hooks to the application.
    
    Args:
        app: The FastAPI application.
        hooks: Hooks configuration.
    """
    app.add_middleware(HooksMiddleware, hooks=hooks)


# Request logging hook helpers
def create_request_logger() -> Callable:
    """Create a request logging hook."""
    def log_request(request: Request):
        print(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {request.method} {request.url.path}")
    return log_request


def create_response_timer() -> Callable:
    """Create a hook that adds response timing."""
    def before_response(response: Response) -> Response:
        response.headers["X-Response-Time"] = str(time.time())
        return response
    return before_response


def create_request_id() -> Callable:
    """Create hooks for request ID tracking."""
    import uuid
    
    def before_request(request: Request):
        request.state.request_id = str(uuid.uuid4())
    
    def after_request(request: Request, response: Response) -> Response:
        request_id = getattr(request.state, "request_id", None)
        if request_id:
            response.headers["X-Request-ID"] = request_id
        return response
    
    return after_request


# Metrics hooks
class MetricsCollector:
    """Collect request metrics."""
    
    def __init__(self) -> None:
        self.requests: List[Dict] = []
        self.start_time = time.time()
    
    def record_request(self, request: Request, response: Response, duration: float):
        self.requests.append({
            "method": request.method,
            "path": request.url.path,
            "status": response.status_code,
            "duration": duration,
            "timestamp": time.time()
        })
    
    def get_stats(self) -> Dict[str, Any]:
        total = len(self.requests)
        if total == 0:
            return {
                "total_requests": 0,
                "uptime": time.time() - self.start_time
            }
        
        status_counts = {}
        for req in self.requests:
            status = req["status"]
            status_counts[status] = status_counts.get(status, 0) + 1
        
        return {
            "total_requests": total,
            "status_counts": status_counts,
            "uptime": time.time() - self.start_time
        }


def create_metrics_hook() -> tuple[Callable, MetricsCollector]:
    """
    Create hooks for collecting metrics.
    
    Returns:
        Tuple of (after_request hook, MetricsCollector)
    """
    collector = MetricsCollector()
    
    async def after_request(request: Request, response: Response) -> Response:
        duration = float(response.headers.get("X-Response-Time", 0))
        collector.record_request(request, response, duration)
        return response
    
    return after_request, collector
