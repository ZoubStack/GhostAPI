"""Security headers middleware for ghostapi."""

from typing import Callable, List, Optional

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to responses.
    
    Adds headers like:
    - X-Content-Type-Options
    - X-Frame-Options
    - X-XSS-Protection
    - Strict-Transport-Security
    - Content-Security-Policy
    """
    
    def __init__(
        self,
        app: ASGIApp,
        hsts: bool = True,
        frame_deny: bool = True,
        xss_protection: bool = True,
        content_type_nosniff: bool = True,
        csp_policy: Optional[str] = None,
        allowed_hosts: Optional[List[str]] = None
    ) -> None:
        """
        Initialize security headers middleware.
        
        Args:
            app: The ASGI application.
            hsts: Enable Strict-Transport-Security header.
            frame_deny: Enable X-Frame-Options: DENY.
            xss_protection: Enable X-XSS-Protection.
            content_type_nosniff: Enable X-Content-Type-Options: nosniff.
            csp_policy: Content-Security-Policy header value.
            allowed_hosts: List of allowed hosts for HSTS.
        """
        super().__init__(app)
        self.hsts = hsts
        self.frame_deny = frame_deny
        self.xss_protection = xss_protection
        self.content_type_nosniff = content_type_nosniff
        self.csp_policy = csp_policy
        self.allowed_hosts = allowed_hosts
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process request and add security headers.
        
        Args:
            request: The incoming request.
            call_next: The next middleware/handler.
        
        Returns:
            Response with security headers.
        """
        response = await call_next(request)
        
        # Prevent content type sniffing
        if self.content_type_nosniff:
            response.headers["X-Content-Type-Options"] = "nosniff"
        
        # Prevent clickjacking
        if self.frame_deny:
            response.headers["X-Frame-Options"] = "DENY"
        
        # XSS Protection
        if self.xss_protection:
            response.headers["X-XSS-Protection"] = "1; mode=block"
        
        # HSTS (only for HTTPS)
        if self.hsts and request.url.scheme == "https":
            max_age = 31536000  # 1 year
            hsts_value = f"max-age={max_age}"
            if self.allowed_hosts:
                hsts_value += f"; includeSubDomains"
            response.headers["Strict-Transport-Security"] = hsts_value
        
        # Content Security Policy
        if self.csp_policy:
            response.headers["Content-Security-Policy"] = self.csp_policy
        
        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Permissions Policy
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        return response


def add_security_headers(
    app: FastAPI,
    hsts: bool = True,
    frame_deny: bool = True,
    xss_protection: bool = True,
    content_type_nosniff: bool = True,
    csp_policy: Optional[str] = None,
    allowed_hosts: Optional[List[str]] = None
) -> None:
    """
    Add security headers to the application.
    
    Args:
        app: The FastAPI application.
        hsts: Enable HSTS.
        frame_deny: Enable frame protection.
        xss_protection: Enable XSS protection.
        content_type_nosniff: Prevent content type sniffing.
        csp_policy: Custom CSP policy.
        allowed_hosts: Allowed hosts for HSTS.
    """
    app.add_middleware(
        SecurityHeadersMiddleware,
        hsts=hsts,
        frame_deny=frame_deny,
        xss_protection=xss_protection,
        content_type_nosniff=content_type_nosniff,
        csp_policy=csp_policy,
        allowed_hosts=allowed_hosts
    )
