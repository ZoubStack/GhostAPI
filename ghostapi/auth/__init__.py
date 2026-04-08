"""Authentication module for ghostapi.

This module provides:
- JWT-based authentication
- Role-based access control
- User management
- Token verification

Usage:
    from ghostapi import expose
    from ghostapi.auth import enable_auth
    
    def my_func():
        return "Hello"
    
    # With authentication
    expose(auth=True)
"""

from ghostapi.auth.core import enable_auth, create_test_user, clear_user_storage
from ghostapi.auth.exceptions import (
    GhostAPIException,
    AuthenticationError,
    InvalidTokenError,
    AuthorizationError,
    UserNotFoundError,
    UserAlreadyExistsError,
    InvalidCredentialsError
)
from ghostapi.auth.models import (
    User,
    UserCreate,
    UserResponse,
    Token,
    TokenData,
    LoginRequest
)
from ghostapi.auth.middleware import AuthMiddleware, get_current_user
from ghostapi.auth.roles import require_role, RequireRole, has_role
from ghostapi.auth.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    decode_access_token,
    create_user_token
)

# OAuth
from ghostapi.auth.oauth import (
    OAuthProvider,
    OAuthConfig,
    OAuthUser,
    setup_oauth,
    get_oauth_config,
    set_oauth_config
)

# Audit
from ghostapi.auth.audit import (
    AuditLogger,
    AuditEntry,
    AuditAction,
    AuditLevel,
    get_audit_logger,
    set_audit_logger,
    create_audit_middleware
)

# Token Blacklist
from ghostapi.auth.token_blacklist import (
    TokenBlacklist,
    get_token_blacklist,
    set_token_blacklist,
    check_token_not_revoked,
    revoke_current_token
)

__all__ = [
    # Core
    "enable_auth",
    "create_test_user",
    "clear_user_storage",
    
    # Exceptions
    "GhostAPIException",
    "AuthenticationError",
    "InvalidTokenError",
    "AuthorizationError",
    "UserNotFoundError",
    "UserAlreadyExistsError",
    "InvalidCredentialsError",
    
    # Models
    "User",
    "UserCreate",
    "UserResponse",
    "Token",
    "TokenData",
    "LoginRequest",
    
    # Middleware
    "AuthMiddleware",
    "get_current_user",
    
    # Roles
    "require_role",
    "RequireRole",
    "has_role",
    
    # Security
    "verify_password",
    "get_password_hash",
    "create_access_token",
    "decode_access_token",
    "create_user_token",
    
    # OAuth
    "OAuthProvider",
    "OAuthConfig",
    "OAuthUser",
    "setup_oauth",
    "get_oauth_config",
    "set_oauth_config",
    
    # Audit
    "AuditLogger",
    "AuditEntry",
    "AuditAction",
    "AuditLevel",
    "get_audit_logger",
    "set_audit_logger",
    "create_audit_middleware",
    
    # Token Blacklist
    "TokenBlacklist",
    "get_token_blacklist",
    "set_token_blacklist",
    "check_token_not_revoked",
    "revoke_current_token",
]
