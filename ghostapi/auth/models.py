"""User models for ghostapi authentication."""

from typing import Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class User(BaseModel):
    """User model for authentication."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    email: EmailStr
    password: str = Field(..., exclude=True)
    role: str = "user"


class UserCreate(BaseModel):
    """Schema for creating a new user."""
    
    email: EmailStr
    password: str = Field(
        ..., 
        min_length=8,
        description="Password must be at least 8 characters with uppercase, lowercase and digit"
    )
    role: str = Field(default="user", description="User role (user, moderator, admin)")
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password complexity."""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not any(c.islower() for c in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain at least one digit')
        return v
    
    @field_validator('role')
    @classmethod
    def validate_role(cls, v: str) -> str:
        """Validate role is allowed."""
        allowed_roles = ["user", "moderator", "admin"]
        if v not in allowed_roles:
            raise ValueError(f'Role must be one of: {allowed_roles}')
        return v


class UserResponse(BaseModel):
    """Schema for user response (without password)."""
    
    model_config = ConfigDict(from_attributes=True)
    
    id: str
    email: EmailStr
    role: str


class Token(BaseModel):
    """Schema for JWT token response."""
    
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for token payload data."""
    
    user_id: Optional[int] = None
    email: Optional[str] = None
    role: Optional[str] = None


class LoginRequest(BaseModel):
    """Schema for login request."""
    
    email: EmailStr
    password: str
