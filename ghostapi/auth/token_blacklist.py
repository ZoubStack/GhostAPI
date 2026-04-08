"""
Token Blacklist / Revocation module for GhostAPI.

Allows revoking JWT tokens before their expiration.
Useful for:
- Logout functionality
- Security incidents
- Password changes
- Role changes
"""

import os
import json
from typing import Optional, Dict, Any, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from pathlib import Path

from pydantic import BaseModel


@dataclass
class RevokedToken:
    """Represents a revoked token."""
    jti: str  # JWT ID
    user_id: str
    revoked_at: datetime
    expires_at: datetime
    reason: Optional[str] = None


class TokenBlacklist:
    """
    Manages revoked JWT tokens.
    
    Example:
        blacklist = TokenBlacklist()
        
        # Revoke a token
        blacklist.revoke_token(jti="token-id", user_id="123", reason="logout")
        
        # Check if token is revoked
        if blacklist.is_revoked(jti="token-id"):
            raise HTTPException(status_code=401, detail="Token revoked")
    """
    
    def __init__(
        self,
        storage_path: Optional[str] = None,
        cleanup_interval: int = 3600  # 1 hour
    ):
        """
        Initialize token blacklist.
        
        Args:
            storage_path: Path to store blacklist (JSON file)
            cleanup_interval: Seconds between cleanup of expired entries
        """
        self.storage_path = storage_path or os.getenv(
            "TOKEN_BLACKLIST_PATH",
            "data/token_blacklist.json"
        )
        self.cleanup_interval = cleanup_interval
        
        # In-memory storage
        self._revoked: Dict[str, RevokedToken] = {}
        
        # Ensure storage directory exists
        Path(self.storage_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing blacklist
        self._load_blacklist()
        
        # Schedule cleanup
        self._schedule_cleanup()
    
    def _load_blacklist(self) -> None:
        """Load blacklist from storage."""
        try:
            path = Path(self.storage_path)
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for item in data:
                        self._revoked[item["jti"]] = RevokedToken(
                            jti=item["jti"],
                            user_id=item["user_id"],
                            revoked_at=datetime.fromisoformat(item["revoked_at"]),
                            expires_at=datetime.fromisoformat(item["expires_at"]),
                            reason=item.get("reason")
                        )
        except Exception:
            pass
    
    def _save_blacklist(self) -> None:
        """Save blacklist to storage."""
        try:
            data = []
            for jti, token in self._revoked.items():
                data.append({
                    "jti": token.jti,
                    "user_id": token.user_id,
                    "revoked_at": token.revoked_at.isoformat(),
                    "expires_at": token.expires_at.isoformat(),
                    "reason": token.reason
                })
            
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
        except Exception:
            pass
    
    def _schedule_cleanup(self) -> None:
        """Schedule periodic cleanup of expired tokens."""
        import threading
        
        def cleanup():
            while True:
                import time
                time.sleep(self.cleanup_interval)
                self._cleanup_expired()
        
        thread = threading.Thread(target=cleanup, daemon=True)
        thread.start()
    
    def _cleanup_expired(self) -> int:
        """Remove expired tokens from blacklist."""
        now = datetime.utcnow()
        expired = [
            jti for jti, token in self._revoked.items()
            if token.expires_at < now
        ]
        
        for jti in expired:
            del self._revoked[jti]
        
        if expired:
            self._save_blacklist()
        
        return len(expired)
    
    def revoke_token(
        self,
        jti: str,
        user_id: str,
        expires_at: datetime,
        reason: Optional[str] = None
    ) -> None:
        """
        Revoke a token.
        
        Args:
            jti: JWT ID (from token payload)
            user_id: User ID who owns the token
            expires_at: When the token expires
            reason: Reason for revocation (optional)
        
        Example:
            blacklist.revoke_token(
                jti="token-id-123",
                user_id="user-456",
                expires_at=datetime.utcnow() + timedelta(hours=1),
                reason="logout"
            )
        """
        self._revoked[jti] = RevokedToken(
            jti=jti,
            user_id=user_id,
            revoked_at=datetime.utcnow(),
            expires_at=expires_at,
            reason=reason
        )
        
        # Save to storage
        self._save_blacklist()
    
    def is_revoked(self, jti: str) -> bool:
        """
        Check if a token is revoked.
        
        Args:
            jti: JWT ID to check
        
        Returns:
            True if token is revoked
        """
        if jti not in self._revoked:
            return False
        
        token = self._revoked[jti]
        
        # Check if expired
        if token.expires_at < datetime.utcnow():
            # Auto-remove expired entry
            del self._revoked[jti]
            return False
        
        return True
    
    def get_revocation_info(self, jti: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a revoked token.
        
        Args:
            jti: JWT ID to check
        
        Returns:
            Dict with revocation info or None
        """
        if jti not in self._revoked:
            return None
        
        token = self._revoked[jti]
        
        return {
            "jti": token.jti,
            "user_id": token.user_id,
            "revoked_at": token.revoked_at.isoformat(),
            "expires_at": token.expires_at.isoformat(),
            "reason": token.revoked_at
        }
    
    def revoke_all_user_tokens(
        self,
        user_id: str,
        reason: Optional[str] = None
    ) -> int:
        """
        Revoke all tokens for a specific user.
        
        Useful for password changes or security incidents.
        
        Args:
            user_id: User ID
            reason: Reason for revocation
        
        Returns:
            Number of tokens revoked
        """
        now = datetime.utcnow()
        count = 0
        
        for jti, token in list(self._revoked.items()):
            if token.user_id == user_id:
                # Update reason
                token.reason = reason
                count += 1
        
        self._save_blacklist()
        return count
    
    def get_user_revoked_tokens(self, user_id: str) -> list[Dict[str, Any]]:
        """
        Get all revoked tokens for a user.
        
        Args:
            user_id: User ID
        
        Returns:
            List of revoked token info
        """
        return [
            {
                "jti": token.jti,
                "revoked_at": token.revoked_at.isoformat(),
                "expires_at": token.expires_at.isoformat(),
                "reason": token.reason
            }
            for jti, token in self._revoked.items()
            if token.user_id == user_id
        ]
    
    def clear(self) -> None:
        """Clear entire blacklist (use with caution)."""
        self._revoked.clear()
        self._save_blacklist()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get blacklist statistics."""
        now = datetime.utcnow()
        
        active = sum(
            1 for token in self._revoked.values()
            if token.expires_at > now
        )
        
        expired = len(self._revoked) - active
        
        return {
            "total_revoked": len(self._revoked),
            "active": active,
            "expired": expired,
            "storage_path": self.storage_path
        }


# Global blacklist instance
_token_blacklist: Optional[TokenBlacklist] = None


def get_token_blacklist() -> TokenBlacklist:
    """Get the global token blacklist instance."""
    global _token_blacklist
    if _token_blacklist is None:
        _token_blacklist = TokenBlacklist()
    return _token_blacklist


def set_token_blacklist(blacklist: TokenBlacklist) -> None:
    """Set the global token blacklist instance."""
    global _token_blacklist
    _token_blacklist = blacklist


# Token revocation dependency for FastAPI
async def check_token_not_revoked(jti: str) -> str:
    """
    FastAPI dependency to check if token is revoked.
    
    Example:
        @app.get("/protected")
        async def protected_route(token_jti: str = Depends(check_token_not_revoked)):
            return {"message": "Valid token"}
    """
    from fastapi import HTTPException, status
    
    blacklist = get_token_blacklist()
    
    if blacklist.is_revoked(jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked"
        )
    
    return jti


# Helper functions for JWT handling
def extract_jti(token_payload: Dict[str, Any]) -> Optional[str]:
    """Extract JWT ID from token payload."""
    return token_payload.get("jti")


def create_revokable_token(
    user_id: str,
    email: str,
    expires_delta: timedelta = timedelta(minutes=30)
) -> tuple[str, datetime]:
    """
    Create a revokable JWT token.
    
    Args:
        user_id: User ID
        email: User email
        expires_delta: Token expiration time
    
    Returns:
        Tuple of (token, expires_at)
    """
    import uuid
    from ghostapi.auth.core import create_access_token, get_settings
    
    jti = str(uuid.uuid4())
    expires_at = datetime.utcnow() + expires_delta
    
    token = create_access_token(
        data={
            "sub": email,
            "user_id": user_id,
            "jti": jti
        },
        expires_delta=expires_delta
    )
    
    return token, expires_at


def revoke_current_token(
    token_payload: Dict[str, Any],
    reason: Optional[str] = None
) -> bool:
    """
    Revoke a token from its payload.
    
    Args:
        token_payload: Decoded JWT payload
        reason: Reason for revocation
    
    Returns:
        True if successful
    """
    jti = extract_jti(token_payload)
    if not jti:
        return False
    
    user_id = token_payload.get("user_id")
    exp = token_payload.get("exp")
    
    if not user_id or not exp:
        return False
    
    expires_at = datetime.fromtimestamp(exp)
    
    blacklist = get_token_blacklist()
    blacklist.revoke_token(
        jti=jti,
        user_id=user_id,
        expires_at=expires_at,
        reason=reason
    )
    
    return True
