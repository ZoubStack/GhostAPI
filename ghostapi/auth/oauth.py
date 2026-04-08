"""
OAuth2 / Social Login module for GhostAPI.

Supports:
- Google
- GitHub
- Discord
"""

import os
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2
from pydantic import BaseModel


class OAuthProvider(str, Enum):
    """Supported OAuth providers."""
    GOOGLE = "google"
    GITHUB = "github"
    DISCORD = "discord"


@dataclass
class OAuthConfig:
    """Configuration for OAuth providers."""
    # Google
    google_client_id: str = ""
    google_client_secret: str = ""
    
    # GitHub
    github_client_id: str = ""
    github_client_secret: str = ""
    
    # Discord
    discord_client_id: str = ""
    discord_client_secret: str = ""
    
    # Common
    callback_url: str = "/api/auth/oauth/callback"
    session_secret: str = "ghostapi-oauth-secret"
    
    def is_enabled(self, provider: OAuthProvider) -> bool:
        """Check if a provider is enabled."""
        if provider == OAuthProvider.GOOGLE:
            return bool(self.google_client_id and self.google_client_secret)
        elif provider == OAuthProvider.GITHUB:
            return bool(self.github_client_id and self.github_client_secret)
        elif provider == OAuthProvider.DISCORD:
            return bool(self.discord_client_id and self.discord_client_secret)
        return False
    
    def get_client_id(self, provider: OAuthProvider) -> str:
        """Get client ID for provider."""
        if provider == OAuthProvider.GOOGLE:
            return self.google_client_id
        elif provider == OAuthProvider.GITHUB:
            return self.github_client_id
        elif provider == OAuthProvider.DISCORD:
            return self.discord_client_id
        return ""
    
    def get_client_secret(self, provider: OAuthProvider) -> str:
        """Get client secret for provider."""
        if provider == OAuthProvider.GOOGLE:
            return self.google_client_secret
        elif provider == OAuthProvider.GITHUB:
            return self.github_client_secret
        elif provider == OAuthProvider.DISCORD:
            return self.discord_client_secret
        return ""
    
    @classmethod
    def from_env(cls) -> "OAuthConfig":
        """Create config from environment variables."""
        return cls(
            google_client_id=os.getenv("GOOGLE_CLIENT_ID", ""),
            google_client_secret=os.getenv("GOOGLE_CLIENT_SECRET", ""),
            github_client_id=os.getenv("GITHUB_CLIENT_ID", ""),
            github_client_secret=os.getenv("GITHUB_CLIENT_SECRET", ""),
            discord_client_id=os.getenv("DISCORD_CLIENT_ID", ""),
            discord_client_secret=os.getenv("DISCORD_CLIENT_SECRET", ""),
            callback_url=os.getenv("OAUTH_CALLBACK_URL", "/api/auth/oauth/callback"),
            session_secret=os.getenv("OAUTH_SESSION_SECRET", "ghostapi-oauth-secret")
        )


# OAuth URLs for each provider
OAUTH_URLS = {
    OAuthProvider.GOOGLE: {
        "auth": "https://accounts.google.com/o/oauth2/v2/auth",
        "token": "https://oauth2.googleapis.com/token",
        "userinfo": "https://www.googleapis.com/oauth2/v2/userinfo",
        "scope": "openid email profile"
    },
    OAuthProvider.GITHUB: {
        "auth": "https://github.com/login/oauth/authorize",
        "token": "https://github.com/login/oauth/access_token",
        "userinfo": "https://api.github.com/user",
        "scope": "read:user user:email"
    },
    OAuthProvider.DISCORD: {
        "auth": "https://discord.com/api/oauth2/authorize",
        "token": "https://discord.com/api/oauth2/token",
        "userinfo": "https://discord.com/api/users/@me",
        "scope": "identify email"
    }
}


class OAuthUser(BaseModel):
    """OAuth user information."""
    provider: OAuthProvider
    provider_id: str
    email: str
    name: str
    picture: Optional[str] = None


class OAuthState:
    """Manages OAuth state for CSRF protection."""
    
    def __init__(self):
        self._states: Dict[str, Dict[str, Any]] = {}
    
    def create(self, provider: OAuthProvider, redirect_uri: str) -> str:
        """Create a new OAuth state."""
        import secrets
        state = secrets.token_urlsafe(32)
        
        self._states[state] = {
            "provider": provider.value,
            "redirect_uri": redirect_uri,
            "created_at": datetime.utcnow()
        }
        return state
    
    def validate(self, state: str) -> Optional[Dict[str, Any]]:
        """Validate and consume an OAuth state."""
        if state not in self._states:
            return None
        
        state_data = self._states.pop(state)
        
        # Check if expired (10 minutes)
        created_at = state_data.get("created_at")
        if created_at:
            if datetime.utcnow() - created_at > timedelta(minutes=10):
                return None
        
        return state_data


# Global instances
_oauth_config: Optional[OAuthConfig] = None
_oauth_state = OAuthState()


def get_oauth_config() -> OAuthConfig:
    """Get the OAuth configuration."""
    global _oauth_config
    if _oauth_config is None:
        _oauth_config = OAuthConfig.from_env()
    return _oauth_config


def set_oauth_config(config: OAuthConfig) -> None:
    """Set the OAuth configuration."""
    global _oauth_config
    _oauth_config = config


def setup_oauth(app, config: Optional[OAuthConfig] = None) -> APIRouter:
    """
    Setup OAuth routes for the FastAPI app.
    
    Args:
        app: FastAPI application
        config: OAuth configuration (will use env vars if not provided)
    
    Returns:
        APIRouter with OAuth routes
    """
    global _oauth_config
    
    if config is None:
        config = OAuthConfig.from_env()
    
    _oauth_config = config
    
    router = APIRouter(prefix="/oauth", tags=["OAuth"])
    
    # OAuth callback handler
    @router.get("/callback")
    async def oauth_callback(
        provider: OAuthProvider,
        code: str,
        state: str,
        request: Request
    ):
        """Handle OAuth callback."""
        state_data = _oauth_state.validate(state)
        
        if not state_data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired OAuth state"
            )
        
        # Exchange code for token
        token_data = await _exchange_code(provider, code, request)
        
        # Get user info
        user_info = await _get_user_info(provider, token_data["access_token"])
        
        # Create or update user in database
        user = await _get_or_create_oauth_user(provider, user_info)
        
        # Generate JWT token
        from ghostapi.auth.core import create_access_token
        from ghostapi import get_app
        
        app = get_app()
        access_token = create_access_token(
            data={"sub": user.email, "user_id": user.provider_id}
        )
        
        # Redirect with token
        redirect_uri = state_data.get("redirect_uri", "/")
        
        # Build redirect URL with token
        from urllib.parse import urlencode
        params = urlencode({"token": access_token})
        
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=f"{redirect_uri}?{params}")
    
    # Get authorization URL
    @router.get("/authorize/{provider}")
    async def get_authorization_url(
        provider: OAuthProvider,
        redirect_uri: str = "/"
    ):
        """Get OAuth authorization URL."""
        config = get_oauth_config()
        
        if not config.is_enabled(provider):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Provider {provider.value} is not configured"
            )
        
        # Create state
        state = _oauth_state.create(provider, redirect_uri)
        
        # Build authorization URL
        urls = OAUTH_URLS[provider]
        client_id = config.get_client_id(provider)
        
        from urllib.parse import urlencode
        
        params = {
            "client_id": client_id,
            "redirect_uri": f"{request.base_url}{config.callback_url.lstrip('/')}",
            "response_type": "code",
            "scope": urls["scope"],
            "state": state
        }
        
        auth_url = f"{urls['auth']}?{urlencode(params)}"
        
        return {"authorization_url": auth_url}
    
    # List available providers
    @router.get("/providers")
    async def list_providers():
        """List available OAuth providers."""
        config = get_oauth_config()
        
        return {
            "google": config.is_enabled(OAuthProvider.GOOGLE),
            "github": config.is_enabled(OAuthProvider.GITHUB),
            "discord": config.is_enabled(OAuthProvider.DISCORD)
        }
    
    return router


async def _exchange_code(
    provider: OAuthProvider,
    code: str,
    request: Request
) -> Dict[str, Any]:
    """Exchange authorization code for access token."""
    import httpx
    
    config = get_oauth_config()
    urls = OAUTH_URLS[provider]
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            urls["token"],
            data={
                "client_id": config.get_client_id(provider),
                "client_secret": config.get_client_secret(provider),
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": str(request.base_url).rstrip("/") + config.callback_url
            }
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to exchange code for token"
            )
        
        return response.json()


async def _get_user_info(
    provider: OAuthProvider,
    access_token: str
) -> Dict[str, Any]:
    """Get user information from provider."""
    import httpx
    
    urls = OAUTH_URLS[provider]
    
    async with httpx.AsyncClient() as client:
        response = await client.get(
            urls["userinfo"],
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        if response.status_code != 200:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to get user info"
            )
        
        data = response.json()
        
        # Normalize user info
        if provider == OAuthProvider.GOOGLE:
            return {
                "id": data.get("id"),
                "email": data.get("email"),
                "name": data.get("name"),
                "picture": data.get("picture")
            }
        elif provider == OAuthProvider.GITHUB:
            return {
                "id": str(data.get("id")),
                "email": data.get("email") or f"{data.get('login')}@github.com",
                "name": data.get("name") or data.get("login"),
                "picture": data.get("avatar_url")
            }
        elif provider == OAuthProvider.DISCORD:
            return {
                "id": data.get("id"),
                "email": data.get("email"),
                "username": f"{data.get('username')}#{data.get('discriminator')}",
                "picture": f"https://cdn.discordapp.com/avatars/{data.get('id')}/{data.get('avatar')}.png" if data.get("avatar") else None
            }
        
        return data


async def _get_or_create_oauth_user(
    provider: OAuthProvider,
    user_info: Dict[str, Any]
) -> OAuthUser:
    """Get or create OAuth user in the database."""
    from ghostapi.auth.core import get_user_db
    
    db = await get_user_db()
    
    # Search for existing user
    user = await db.find_one({
        "oauth_provider": provider.value,
        "oauth_id": user_info["id"]
    })
    
    if user:
        # Update user info
        user.update({
            "email": user_info["email"],
            "name": user_info.get("name") or user_info.get("username", ""),
            "picture": user_info.get("picture"),
            "updated_at": datetime.utcnow()
        })
        await db.update_one({"_id": user["_id"]}, user)
    else:
        # Create new user
        user = {
            "email": user_info["email"],
            "oauth_provider": provider.value,
            "oauth_id": user_info["id"],
            "name": user_info.get("name") or user_info.get("username", ""),
            "picture": user_info.get("picture"),
            "role": "user",
            "created_at": datetime.utcnow()
        }
        await db.insert_one(user)
    
    return OAuthUser(
        provider=provider,
        provider_id=user_info["id"],
        email=user_info["email"],
        name=user_info.get("name") or user_info.get("username", ""),
        picture=user_info.get("picture")
    )


# Decorator for OAuth-only routes
def require_oauth(provider: Optional[OAuthProvider] = None):
    """
    Decorator to require OAuth authentication.
    
    Example:
        @require_oauth(OAuthProvider.GOOGLE)
        def protected_endpoint():
            return {"message": "OAuth protected"}
    """
    def decorator(func):
        # This would be used with FastAPI's dependency system
        async def dependency(request: Request):
            from ghostapi.auth.core import get_current_user
            
            # Try to get user via JWT first
            try:
                user = await get_current_user(request)
                return user
            except:
                # Check for OAuth token in query
                token = request.query_params.get("token")
                if token:
                    from ghostapi.auth.core import verify_token
                    payload = verify_token(token)
                    if payload:
                        return payload
                
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="OAuth authentication required"
                )
        
        return func
    return decorator
