"""Core authentication functionality for ghostapi."""

import uuid
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from ghostapi.auth.exceptions import (
    AuthenticationError,
    InvalidCredentialsError,
    UserAlreadyExistsError,
    UserNotFoundError
)
from ghostapi.auth.middleware import AuthMiddleware
from ghostapi.auth.models import LoginRequest, Token, UserCreate, UserResponse
from ghostapi.auth.security import (
    create_user_token,
    get_password_hash,
    verify_password,
    DEFAULT_SECRET,
    DEFAULT_EXPIRE_MINUTES
)
from ghostapi.storage import get_storage


def enable_auth(
    app: FastAPI,
    secret: str = DEFAULT_SECRET,
    expire_minutes: int = DEFAULT_EXPIRE_MINUTES,
    excluded_paths: Optional[List[str]] = None
) -> None:
    """
    Enable authentication for the FastAPI application.
    
    This function:
    1. Adds auth middleware
    2. Adds auth routes (register, login)
    3. Configures JWT settings
    
    Args:
        app: The FastAPI application.
        secret: JWT secret key.
        expire_minutes: Token expiration time in minutes.
        excluded_paths: Paths to exclude from auth middleware.
    """
    storage = get_storage()
    
    # Add auth middleware
    app.add_middleware(
        AuthMiddleware,
        secret=secret,
        excluded_paths=excluded_paths or []
    )
    
    # Add auth routes
    @app.post("/api/auth/register", response_model=UserResponse, tags=["auth"])
    async def register(user_data: UserCreate):
        """Register a new user."""
        storage = get_storage()
        
        # Check if user already exists by email
        all_users = storage.get_all()
        for user in all_users:
            if user.get("email") == user_data.email:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"User with email {user_data.email} already exists"
                )
        
        # Create new user (using UUID)
        user_id = str(uuid.uuid4())
        
        user = {
            "id": user_id,
            "email": user_data.email,
            "password": get_password_hash(user_data.password),
            "role": user_data.role
        }
        
        storage.set(user_id, user)
        
        return UserResponse(id=user_id, email=user_data.email, role=user_data.role)
    
    @app.post("/api/auth/login", response_model=Token, tags=["auth"])
    async def login(form_data: OAuth2PasswordRequestForm = Depends()):
        """
        Login and get access token.
        
        Use OAuth2 form data with:
        - username: email
        - password: password
        """
        storage = get_storage()
        
        # Find user by email (username in OAuth2 form is used as email)
        all_users = storage.get_all()
        user = None
        for u in all_users:
            if u.get("email") == form_data.username:
                user = u
                break
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        if not verify_password(form_data.password, user["password"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        # Create token
        access_token = create_user_token(
            user_id=user["id"],
            email=user["email"],
            role=user["role"],
            secret=secret,
            expires_minutes=expire_minutes
        )
        
        return Token(access_token=access_token, token_type="bearer")
    
    @app.get("/api/auth/me", response_model=UserResponse, tags=["auth"])
    async def get_current_user_info(request: Request):
        """Get current authenticated user info."""
        user_id = getattr(request.state, "user_id", None)
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
                headers={"WWW-Authenticate": "Bearer"}
            )
        
        storage = get_storage()
        user = storage.get(user_id)
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        return UserResponse(id=user["id"], email=user["email"], role=user["role"])


def get_user_storage():
    """Get the user storage (for testing)."""
    return get_storage()


def clear_user_storage() -> None:
    """Clear user storage (for testing)."""
    storage = get_storage()
    storage.clear()


def create_test_user(
    email: str,
    password: str,
    role: str = "user"
) -> dict:
    """
    Create a test user (for testing purposes).
    
    Args:
        email: User email.
        password: User password.
        role: User role.
    
    Returns:
        Created user dict.
    """
    storage = get_storage()
    
    # Check if user exists
    all_users = storage.get_all()
    for user in all_users:
        if user.get("email") == email:
            return user
    
    user_id = str(uuid.uuid4())
    
    user = {
        "id": user_id,
        "email": email,
        "password": get_password_hash(password),
        "role": role
    }
    
    storage.set(user_id, user)
    
    return user
