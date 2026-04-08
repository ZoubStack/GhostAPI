"""Role-based access control for ghostapi."""

from functools import wraps
from typing import Callable, List, Optional

from fastapi import Depends, HTTPException, Request, status

from ghostapi.auth.exceptions import AuthorizationError


# Default roles hierarchy
ROLES_HIERARCHY = {
    "admin": ["admin", "moderator", "user", "guest"],
    "moderator": ["moderator", "user", "guest"],
    "user": ["user", "guest"],
    "guest": ["guest"]
}


def get_user_role(request: Request) -> Optional[str]:
    """
    Extract user role from request state.
    
    Args:
        request: The FastAPI request object.
    
    Returns:
        The user's role or None if not authenticated.
    """
    return getattr(request.state, "user_role", None)


def get_user_id(request: Request) -> Optional[str]:
    """
    Extract user ID from request state.
    
    Args:
        request: The FastAPI request object.
    
    Returns:
        The user's ID (UUID string) or None if not authenticated.
    """
    return getattr(request.state, "user_id", None)


def has_role(user_role: Optional[str], required_role: str) -> bool:
    """
    Check if user has the required role.
    
    Args:
        user_role: The user's current role.
        required_role: The role required for access.
    
    Returns:
        True if user has the required role, False otherwise.
    """
    if user_role is None:
        return False
    
    # If exact match
    if user_role == required_role:
        return True
    
    # Check hierarchy
    allowed_roles = ROLES_HIERARCHY.get(user_role, [])
    return required_role in allowed_roles


class RequireRole:
    """
    Dependency class for role-based access control.
    
    Usage:
        @app.get("/admin")
        async def admin_endpoint(user = Depends(RequireRole("admin"))):
            return {"message": "Admin only"}
    """
    
    def __init__(self, required_role: str) -> None:
        """
        Initialize the role requirement.
        
        Args:
            required_role: The role required to access the endpoint.
        """
        self.required_role = required_role
    
    def __call__(self, request: Request) -> dict:
        """
        Check if the user has the required role.
        
        Args:
            request: The FastAPI request object.
        
        Returns:
            User info if authorized.
        
        Raises:
            HTTPException: If user is not authorized.
        """
        user_role = get_user_role(request)
        
        if user_role is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        if not has_role(user_role, self.required_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{self.required_role}' required"
            )
        
        return {
            "user_id": get_user_id(request),
            "email": getattr(request, "user_email", None),
            "role": user_role
        }


def require_role(role: str) -> RequireRole:
    """
    Create a role requirement dependency.
    
    This is a shortcut for creating RequireRole instances.
    
    Args:
        role: The required role.
    
    Returns:
        A RequireRole dependency instance.
    
    Example:
        @app.get("/admin")
        async def admin_endpoint(user = Depends(require_role("admin"))):
            return {"message": "Admin only"}
    """
    return RequireRole(role)


def require_roles(*roles: str) -> Callable:
    """
    Decorator for requiring multiple roles (any of them).
    
    Args:
        *roles: List of acceptable roles.
    
    Returns:
        A decorator function.
    
    Example:
        @require_roles("admin", "moderator")
        async def protected_endpoint():
            return {"message": "Protected"}
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            request = kwargs.get("request")
            if request is None:
                # Try to get request from args
                for arg in args:
                    if isinstance(arg, Request):
                        request = arg
                        break
            
            if request is None:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Request object not found"
                )
            
            user_role = get_user_role(request)
            
            if user_role is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if not any(has_role(user_role, role) for role in roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"One of roles {roles} required"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator
