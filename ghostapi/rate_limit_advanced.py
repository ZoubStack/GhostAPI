"""
Advanced Rate Limiting for GhostAPI.

Supports:
- Rate limit by IP (existing)
- Rate limit by User ID
- Rate limit by Token
- Rate limit by Role
- Sliding window algorithm
- Fixed window algorithm
"""

import time
from typing import Optional, Dict, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import threading

from fastapi import HTTPException, Request, Depends, status


class RateLimitScope(str, Enum):
    """Rate limit scope types."""
    IP = "ip"
    USER = "user"
    TOKEN = "token"
    ROLE = "role"


class RateLimitAlgorithm(str, Enum):
    """Rate limit algorithms."""
    SLIDING_WINDOW = "sliding_window"
    FIXED_WINDOW = "fixed_window"
    TOKEN_BUCKET = "token_bucket"


@dataclass
class RateLimitRule:
    """Rate limit rule configuration."""
    max_calls: int
    period: int  # seconds
    scope: RateLimitScope = RateLimitScope.IP
    algorithm: RateLimitAlgorithm = RateLimitAlgorithm.SLIDING_WINDOW
    block_duration: int = 60  # seconds to block after limit exceeded


class AdvancedRateLimiter:
    """
    Advanced rate limiter with multiple scopes and algorithms.
    
    Example:
        limiter = AdvancedRateLimiter()
        
        # Add rules
        limiter.add_rule(\"default\", RateLimitRule(max_calls=60, period=60))
        limiter.add_rule(\"premium\", RateLimitRule(max_calls=1000, period=60, scope=RateLimitScope.USER))
        limiter.add_rule(\"admin\", RateLimitRule(max_calls=10000, period=60, scope=RateLimitScope.ROLE))
        
        # Use with FastAPI
        @app.get(\"/api\")
        async def endpoint(request: Request, user_id: str = Depends(limiter.get_identifier)):
            return limiter.check_limit(request, \"default\")
    """
    
    def __init__(self):
        self._rules: Dict[str, RateLimitRule] = {}
        self._limits: Dict[str, Dict] = defaultdict(dict)
        self._lock = threading.Lock()
    
    def add_rule(
        self,
        name: str,
        max_calls: int,
        period: int,
        scope: RateLimitScope = RateLimitScope.IP,
        algorithm: RateLimitAlgorithm = RateLimitAlgorithm.SLIDING_WINDOW,
        block_duration: int = 60
    ) -> None:
        """Add a rate limit rule."""
        self._rules[name] = RateLimitRule(
            max_calls=max_calls,
            period=period,
            scope=scope,
            algorithm=algorithm,
            block_duration=block_duration
        )
    
    def get_identifier(
        self,
        request: Request,
        scope: RateLimitScope = RateLimitScope.IP
    ) -> str:
        """
        Extract identifier based on scope.
        
        Args:
            request: FastAPI request
            scope: Rate limit scope
        
        Returns:
            Identifier string
        """
        if scope == RateLimitScope.IP:
            # Get client IP
            forwarded = request.headers.get("X-Forwarded-For")
            if forwarded:
                return forwarded.split(",")[0].strip()
            return request.client.host if request.client else "unknown"
        
        elif scope == RateLimitScope.USER:
            # Try to get user from request state
            if hasattr(request.state, "user_id"):
                return f"user:{request.state.user_id}"
            # Try from token
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                token = auth_header[7:]
                return f"token:{token[:20]}"  # Use first 20 chars as identifier
            return f"user:anonymous"
        
        elif scope == RateLimitScope.TOKEN:
            # Use full token
            auth_header = request.headers.get("Authorization")
            if auth_header and auth_header.startswith("Bearer "):
                return auth_header[7:]
            return "token:anonymous"
        
        elif scope == RateLimitScope.ROLE:
            # Use role
            if hasattr(request.state, "role"):
                return f"role:{request.state.role}"
            return "role:guest"
        
        return "ip:unknown"
    
    def _get_limit_key(self, identifier: str, rule: RateLimitRule) -> str:
        """Get storage key for limit tracking."""
        return f"{rule.scope.value}:{identifier}"
    
    def _check_sliding_window(
        self,
        identifier: str,
        rule: RateLimitRule
    ) -> tuple[bool, int, int]:
        """Check limit using sliding window algorithm."""
        key = self._get_limit_key(identifier, rule)
        current_time = time.time()
        
        with self._lock:
            if key not in self._limits:
                self._limits[key] = {"calls": [], "blocked_until": 0}
            
            limit_data = self._limits[key]
            
            # Check if blocked
            if limit_data["blocked_until"] > current_time:
                remaining = 0
                reset_time = int(limit_data["blocked_until"])
                return False, remaining, reset_time
            
            # Remove old calls outside window
            window_start = current_time - rule.period
            limit_data["calls"] = [
                t for t in limit_data["calls"]
                if t > window_start
            ]
            
            # Check limit
            if len(limit_data["calls"]) >= rule.max_calls:
                # Block the identifier
                limit_data["blocked_until"] = current_time + rule.block_duration
                return False, 0, int(current_time + rule.block_duration)
            
            # Add current call
            limit_data["calls"].append(current_time)
            
            remaining = rule.max_calls - len(limit_data["calls"])
            reset_time = int(current_time + rule.period)
            
            return True, remaining, reset_time
    
    def _check_fixed_window(
        self,
        identifier: str,
        rule: RateLimitRule
    ) -> tuple[bool, int, int]:
        """Check limit using fixed window algorithm."""
        key = self._get_limit_key(identifier, rule)
        current_time = time.time()
        
        with self._lock:
            if key not in self._limits:
                self._limits[key] = {"count": 0, "window_start": current_time, "blocked_until": 0}
            
            limit_data = self._limits[key]
            
            # Check if blocked
            if limit_data["blocked_until"] > current_time:
                return False, 0, int(limit_data["blocked_until"])
            
            # Reset window if needed
            if current_time - limit_data["window_start"] >= rule.period:
                limit_data["count"] = 0
                limit_data["window_start"] = current_time
            
            # Check limit
            if limit_data["count"] >= rule.max_calls:
                limit_data["blocked_until"] = current_time + rule.block_duration
                return False, 0, int(current_time + rule.block_duration)
            
            limit_data["count"] += 1
            
            remaining = rule.max_calls - limit_data["count"]
            reset_time = int(limit_data["window_start"] + rule.period)
            
            return True, remaining, reset_time
    
    def check_limit(
        self,
        identifier: str,
        rule_name: str = "default"
    ) -> tuple[bool, int, int]:
        """
        Check if request is within rate limit.
        
        Returns:
            Tuple of (allowed, remaining_requests, reset_time)
        """
        if rule_name not in self._rules:
            return True, 999999, 0
        
        rule = self._rules[rule_name]
        
        if rule.algorithm == RateLimitAlgorithm.SLIDING_WINDOW:
            return self._check_sliding_window(identifier, rule)
        elif rule.algorithm == RateLimitAlgorithm.FIXED_WINDOW:
            return self._check_fixed_window(identifier, rule)
        else:
            return True, 999999, 0
    
    def check_request(
        self,
        request: Request,
        rule_name: str = "default",
        scope: RateLimitScope = RateLimitScope.IP
    ) -> Dict:
        """
        Check rate limit for a request.
        
        Args:
            request: FastAPI request
            rule_name: Name of rate limit rule
            scope: Rate limit scope
        
        Returns:
            Dict with limit info
        
        Raises:
            HTTPException: If rate limit exceeded
        """
        identifier = self.get_identifier(request, scope)
        allowed, remaining, reset_time = self.check_limit(identifier, rule_name)
        
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Try again later.",
                headers={
                    "X-RateLimit-Limit": str(self._rules[rule_name].max_calls),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_time),
                    "Retry-After": str(reset_time - int(time.time()))
                }
            )
        
        return {
            "allowed": allowed,
            "remaining": remaining,
            "reset_time": reset_time,
            "limit": self._rules[rule_name].max_calls
        }
    
    def reset_limit(self, identifier: str, rule_name: str = "default") -> bool:
        """Reset rate limit for an identifier."""
        if rule_name not in self._rules:
            return False
        
        rule = self._rules[rule_name]
        key = self._get_limit_key(identifier, rule)
        
        with self._lock:
            if key in self._limits:
                del self._limits[key]
        
        return True
    
    def get_stats(self) -> Dict:
        """Get rate limiter statistics."""
        return {
            "rules": {
                name: {
                    "max_calls": rule.max_calls,
                    "period": rule.period,
                    "scope": rule.scope.value,
                    "algorithm": rule.algorithm.value
                }
                for name, rule in self._rules.items()
            },
            "active_limits": len(self._limits)
        }


# Role-based rate limiting
class RoleRateLimiter:
    """
    Rate limiter based on user roles.
    
    Example:
        role_limiter = RoleRateLimiter()
        role_limiter.set_limit(\"admin\", 1000, 60)  # 1000 req/min for admins
        role_limiter.set_limit(\"user\", 100, 60)   # 100 req/min for users
        role_limiter.set_limit(\"guest\", 10, 60)    # 10 req/min for guests
    """
    
    def __init__(self):
        self._limits: Dict[str, Dict] = {}
        self._limiter = AdvancedRateLimiter()
    
    def set_limit(
        self,
        role: str,
        max_calls: int,
        period: int,
        algorithm: RateLimitAlgorithm = RateLimitAlgorithm.SLIDING_WINDOW
    ) -> None:
        """Set rate limit for a role."""
        self._limits[role] = {
            "max_calls": max_calls,
            "period": period,
            "algorithm": algorithm
        }
        
        # Add to underlying limiter
        self._limiter.add_rule(
            f"role_{role}",
            max_calls=max_calls,
            period=period,
            scope=RateLimitScope.ROLE,
            algorithm=algorithm
        )
    
    def check(
        self,
        request: Request,
        user_role: str = "guest"
    ) -> Dict:
        """Check rate limit for user role."""
        # Determine effective role limit
        effective_role = user_role
        if user_role not in self._limits:
            # Find closest lower role
            role_hierarchy = ["admin", "moderator", "user", "guest"]
            for role in role_hierarchy:
                if role in self._limits:
                    effective_role = role
                    break
        
        rule_name = f"role_{effective_role}"
        return self._limiter.check_request(request, rule_name, RateLimitScope.ROLE)


# Token-based rate limiting
class TokenRateLimiter:
    """
    Rate limiter based on API tokens.
    
    Example:
        token_limiter = TokenRateLimiter()
        token_limiter.set_token_limit(\"tok_123\", 100, 60)
    """
    
    def __init__(self):
        self._token_limits: Dict[str, Dict] = {}
        self._limiter = AdvancedRateLimiter()
    
    def set_token_limit(
        self,
        token_prefix: str,
        max_calls: int,
        period: int
    ) -> None:
        """Set rate limit for a token."""
        self._token_limits[token_prefix] = {
            "max_calls": max_calls,
            "period": period
        }
        
        self._limiter.add_rule(
            f"token_{token_prefix[:10]}",
            max_calls=max_calls,
            period=period,
            scope=RateLimitScope.TOKEN
        )
    
    def check(self, request: Request) -> Dict:
        """Check rate limit for token."""
        return self._limiter.check_request(request, "default", RateLimitScope.TOKEN)


# Global instances
_rate_limiter = AdvancedRateLimiter()


def get_rate_limiter() -> AdvancedRateLimiter:
    """Get global rate limiter."""
    return _rate_limiter


def set_rate_limiter(limiter: AdvancedRateLimiter) -> None:
    """Set global rate limiter."""
    global _rate_limiter
    _rate_limiter = limiter
