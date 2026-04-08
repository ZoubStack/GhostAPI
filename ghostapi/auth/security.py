"""Security utilities for authentication (JWT, password hashing)."""

import os
import warnings
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

import bcrypt
from jose import JWTError, jwt

from ghostapi.auth.exceptions import InvalidTokenError

# Default JWT settings
ALGORITHM = "HS256"
DEFAULT_SECRET = os.environ.get("GHOSTAPI_SECRET") or "ghostapi-secret-key-change-in-production"
DEFAULT_EXPIRE_MINUTES = 30

# Bcrypt rounds (work factor) - higher is more secure but slower
# Default 12 is recommended by OWASP
BCRYPT_ROUNDS = 12


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a hashed password.
    
    Args:
        plain_password: The plain text password to verify.
        hashed_password: The hashed password to compare against.
    
    Returns:
        True if the password matches, False otherwise.
    """
    return bcrypt.checkpw(
        plain_password.encode('utf-8'),
        hashed_password.encode('utf-8')
    )


def get_password_hash(password: str, rounds: Optional[int] = None) -> str:
    """
    Hash a password using bcrypt.
    
    Args:
        password: The plain text password to hash.
        rounds: Optional bcrypt rounds (work factor). Higher = more secure but slower.
                Default is 12 (OWASP recommended).
    
    Returns:
        The hashed password.
    """
    work_rounds = rounds if rounds is not None else BCRYPT_ROUNDS
    return bcrypt.hashpw(
        password.encode('utf-8'),
        bcrypt.gensalt(rounds=work_rounds)
    ).decode('utf-8')


def verify_secret(secret: str, require_env: bool = True) -> bool:
    """
    Verify that the secret is properly configured for production.
    
    Args:
        secret: The secret to verify.
        require_env: If True, secret must come from environment variable in production.
    
    Returns:
        True if secret is secure.
    
    Raises:
        Warning: If using default secret in production.
    """
    default_secret = "ghostapi-secret-key-change-in-production"
    
    if secret == default_secret:
        warnings.warn(
            "⚠️ SECURITY WARNING: You are using the default secret key! "
            "This is insecure for production. Set GHOSTAPI_SECRET environment variable "
            "or provide a custom secret to expose().",
            UserWarning,
            stacklevel=2
        )
        return False
    
    if require_env and not os.environ.get("GHOSTAPI_SECRET"):
        warnings.warn(
            "⚠️ SECURITY WARNING: Secret should be set via GHOSTAPI_SECRET environment variable "
            "for production use.",
            UserWarning,
            stacklevel=2
        )
    
    return True


def create_access_token(
    data: Dict[str, Any],
    secret: str = DEFAULT_SECRET,
    expires_delta: Optional[timedelta] = None,
    algorithm: str = ALGORITHM
) -> str:
    """
    Create a JWT access token.
    
    Args:
        data: The data to encode in the token.
        secret: The secret key for signing the token.
        expires_delta: Optional expiration time delta.
        algorithm: The algorithm to use for signing.
    
    Returns:
        The encoded JWT token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=DEFAULT_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, secret, algorithm=algorithm)
    return encoded_jwt


def decode_access_token(
    token: str,
    secret: str = DEFAULT_SECRET,
    algorithm: str = ALGORITHM
) -> Dict[str, Any]:
    """
    Decode and verify a JWT access token.
    
    Args:
        token: The JWT token to decode.
        secret: The secret key for verifying the token.
        algorithm: The algorithm used for signing.
    
    Returns:
        The decoded token payload.
    
    Raises:
        InvalidTokenError: If the token is invalid or expired.
    """
    try:
        payload = jwt.decode(token, secret, algorithms=[algorithm])
        return payload
    except JWTError as e:
        raise InvalidTokenError(f"Invalid token: {str(e)}")


def create_user_token(
    user_id: str,
    email: str,
    role: str,
    secret: str = DEFAULT_SECRET,
    expires_minutes: int = DEFAULT_EXPIRE_MINUTES
) -> str:
    """
    Create a JWT token for a user.
    
    Args:
        user_id: The user's ID (UUID string).
        email: The user's email.
        role: The user's role.
        secret: The secret key for signing.
        expires_minutes: Token expiration in minutes.
    
    Returns:
        The encoded JWT token.
    """
    expire = timedelta(minutes=expires_minutes)
    return create_access_token(
        data={"sub": str(user_id), "email": email, "role": role},
        secret=secret,
        expires_delta=expire
    )
