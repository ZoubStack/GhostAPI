"""Authentication middleware for verifying tokens and injecting user info."""

from typing import Callable, Optional

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from ghostapi.auth.exceptions import InvalidTokenError
from ghostapi.auth.security import decode_access_token, DEFAULT_SECRET


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Middleware to verify JWT tokens and inject user info into request state.
    
    This middleware:
    1. Checks for Authorization header
    2. Validates JWT token
    3. Injects user info (id, email, role) into request.state
    """
    
    def __init__(
        self,
        app: ASGIApp,
        secret: str = DEFAULT_SECRET,
        excluded_paths: Optional[list] = None
    ) -> None:
        """
        Initialize the auth middleware.
        
        Args:
            app: The ASGI application.
            secret: The JWT secret key.
            excluded_paths: List of paths to skip auth (e.g., ["/docs", "/openapi.json"]).
        """
        super().__init__(app)
        self.secret = secret
        self.excluded_paths = excluded_paths or [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/api/auth/register",
            "/api/auth/login"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and verify authentication.
        
        Args:
            request: The incoming request.
            call_next: The next middleware/handler in the chain.
        
        Returns:
            The response.
        """
        # Skip auth for excluded paths
        if any(request.url.path.startswith(path) for path in self.excluded_paths):
            return await call_next(request)
        
        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization")
        
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header[7:]  # Remove "Bearer " prefix
            
            try:
                payload = decode_access_token(token, self.secret)
                
                # Inject user info into request state
                request.state.user_id = payload.get("sub", "")
                request.state.user_email = payload.get("email")
                request.state.user_role = payload.get("role", "guest")
                
            except InvalidTokenError:
                # Token invalid or expired - continue without auth
                request.state.user_id = None
                request.state.user_email = None
                request.state.user_role = None
        else:
            # No token provided
            request.state.user_id = None
            request.state.user_email = None
            request.state.user_role = None
        
        return await call_next(request)


def get_current_user(request: Request) -> Optional[dict]:
    """
    Get the current authenticated user from request state.
    
    Args:
        request: The FastAPI request object.
    
    Returns:
        User info dict or None if not authenticated.
    """
    user_id = getattr(request.state, "user_id", None)
    if user_id is None:
        return None
    
    return {
        "id": user_id,
        "email": getattr(request.state, "user_email", None),
        "role": getattr(request.state, "user_role", "guest")
    }


async def verify_token(request: Request, secret: str = DEFAULT_SECRET) -> dict:
    """
    Verify JWT token from request.
    
    Args:
        request: The FastAPI request object.
        secret: The JWT secret key.
    
    Returns:
        Token payload if valid.
    
    Raises:
        InvalidTokenError: If token is invalid.
    """
    auth_header = request.headers.get("Authorization")
    
    if not auth_header or not auth_header.startswith("Bearer "):
        raise InvalidTokenError("Missing or invalid Authorization header")
    
    token = auth_header[7:]
    return decode_access_token(token, secret)
