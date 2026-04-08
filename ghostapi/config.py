"""Global configuration for ghostapi."""

import os
from typing import Optional


class Config:
    """Global configuration for ghostapi."""
    
    # Auth settings
    AUTH_ENABLED: bool = False
    SECRET_KEY: str = os.environ.get("GHOSTAPI_SECRET") or "ghostapi-secret-key-change-in-production"
    TOKEN_EXPIRE_MINUTES: int = 30
    
    # Server settings
    HOST: str = "127.0.0.1"
    PORT: int = 8000
    DEBUG: bool = False
    
    # Rate limiting (future)
    RATE_LIMIT_ENABLED: bool = False
    RATE_LIMIT_PER_MINUTE: int = 60
    
    # Caching (future)
    CACHE_ENABLED: bool = False
    
    @classmethod
    def configure(
        cls,
        auth: bool = False,
        debug: bool = False,
        host: Optional[str] = None,
        port: Optional[int] = None,
        secret: Optional[str] = None,
        expire_minutes: Optional[int] = None
    ) -> None:
        """
        Configure ghostapi settings.
        
        Args:
            auth: Enable authentication.
            debug: Enable debug mode.
            host: Server host.
            port: Server port.
            secret: JWT secret key.
            expire_minutes: Token expiration in minutes.
        """
        cls.AUTH_ENABLED = auth
        cls.DEBUG = debug
        
        if host is not None:
            cls.HOST = host
        if port is not None:
            cls.PORT = port
        if secret is not None:
            cls.SECRET_KEY = secret
        if expire_minutes is not None:
            cls.TOKEN_EXPIRE_MINUTES = expire_minutes
    
    @classmethod
    def reset(cls) -> None:
        """Reset configuration to defaults."""
        cls.AUTH_ENABLED = False
        cls.SECRET_KEY = os.environ.get("GHOSTAPI_SECRET") or "ghostapi-secret-key-change-in-production"
        cls.TOKEN_EXPIRE_MINUTES = 30
        cls.HOST = "127.0.0.1"
        cls.PORT = 8000
        cls.DEBUG = False
        cls.RATE_LIMIT_ENABLED = False
        cls.CACHE_ENABLED = False


# Global config instance
config = Config()
