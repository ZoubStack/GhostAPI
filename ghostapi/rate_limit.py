"""Rate limiting middleware for ghostapi."""

import time
from collections import defaultdict
from typing import Callable, Dict, List, Optional

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from starlette.types import ASGIApp
from starlette.types import ASGIApp


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware to prevent abuse.
    
    Limits requests per IP address within a time window.
    """
    
    def __init__(
        self,
        app: ASGIApp,
        requests_per_minute: int = 60,
        excluded_paths: Optional[list] = None
    ) -> None:
        """
        Initialize the rate limiting middleware.
        
        Args:
            app: The ASGI application.
            requests_per_minute: Maximum requests per minute per IP.
            excluded_paths: List of paths to exclude from rate limiting.
        """
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.window_size = 60  # seconds
        self.excluded_paths = excluded_paths or ["/docs", "/openapi.json", "/redoc"]
        self.requests: Dict[str, list] = defaultdict(list)
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request with rate limiting.
        
        Args:
            request: The incoming request.
            call_next: The next middleware/handler in the chain.
        
        Returns:
            The response.
        """
        # Skip rate limiting for excluded paths
        if any(request.url.path.startswith(path) for path in self.excluded_paths):
            return await call_next(request)
        
        # Get client IP
        client_ip = self._get_client_ip(request)
        
        # Check rate limit
        if not self._check_rate_limit(client_ip):
            from fastapi import HTTPException, status
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later."
            )
        
        # Record request
        self._record_request(client_ip)
        
        return await call_next(request)
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP from request."""
        # Try to get from forwarded header (for proxied requests)
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        
        # Fall back to direct client IP
        if request.client:
            return request.client.host
        
        return "unknown"
    
    def _check_rate_limit(self, client_ip: str) -> bool:
        """Check if client has exceeded rate limit."""
        current_time = time.time()
        window_start = current_time - self.window_size
        
        # Filter to only requests within the window
        self.requests[client_ip] = [
            req_time for req_time in self.requests[client_ip]
            if req_time > window_start
        ]
        
        # Check if under limit
        return len(self.requests[client_ip]) < self.requests_per_minute
    
    def _record_request(self, client_ip: str) -> None:
        """Record a request for rate limiting."""
        self.requests[client_ip].append(time.time())


def add_rate_limiting(
    app: FastAPI,
    requests_per_minute: int = 60,
    excluded_paths: Optional[list] = None
) -> None:
    """
    Add rate limiting to the application.
    
    Args:
        app: The FastAPI application.
        requests_per_minute: Maximum requests per minute.
        excluded_paths: Paths to exclude from rate limiting.
    """
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=requests_per_minute,
        excluded_paths=excluded_paths
    )
