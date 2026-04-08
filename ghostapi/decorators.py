"""Custom decorators for ghostapi functions."""

import asyncio
import functools
import time
from typing import Any, Callable, Optional

from fastapi import HTTPException, Request, status


def cache(ttl: int = 300, key_prefix: Optional[str] = None):
    """
    Decorator to cache function results.
    
    Args:
        ttl: Time to live in seconds (default 5 minutes).
        key_prefix: Prefix for cache key (defaults to function name).
    
    Example:
        @cache(ttl=60)
        def get_expensive_data():
            return expensive_computation()
    """
    def decorator(func: Callable) -> Callable:
        # Import here to avoid circular imports
        from ghostapi.cache import get_cache, cache_key as generate_cache_key
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            cache = get_cache()
            prefix = key_prefix or func.__name__
            
            # Try to get from cache
            cached_value = cache.get(prefix)
            if cached_value is not None:
                return cached_value
            
            # Call function
            result = func(*args, **kwargs)
            
            # Handle coroutines
            if asyncio.iscoroutine(result):
                result = await result
            
            # Store in cache
            cache.set(prefix, result, ttl)
            
            return result
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            cache = get_cache()
            prefix = key_prefix or func.__name__
            
            # Try to get from cache
            cached_value = cache.get(prefix)
            if cached_value is not None:
                return cached_value
            
            # Call function
            result = func(*args, **kwargs)
            
            # Store in cache
            cache.set(prefix, result, ttl)
            
            return result
        
        # Return appropriate wrapper based on function type
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def rate_limit(max_calls: int = 10, period: int = 60):
    """
    Decorator to rate limit function calls.
    
    Args:
        max_calls: Maximum number of calls allowed in the period.
        period: Time period in seconds.
    
    Example:
        @rate_limit(max_calls=5, period=60)
        def api_call():
            return {"data": "result"}
    """
    # Simple in-memory rate limiter
    _calls = {}
    
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            current_time = time.time()
            func_name = func.__name__
            
            # Initialize if not exists
            if func_name not in _calls:
                _calls[func_name] = []
            
            # Clean old calls outside the window
            _calls[func_name] = [
                t for t in _calls[func_name]
                if current_time - t < period
            ]
            
            # Check limit
            if len(_calls[func_name]) >= max_calls:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Max {max_calls} calls per {period} seconds."
                )
            
            # Record this call
            _calls[func_name].append(current_time)
            
            # Call function
            result = func(*args, **kwargs)
            
            # Handle coroutines
            if asyncio.iscoroutine(result):
                result = await result
            
            return result
        
        return wrapper
    return decorator


def require_auth(role: Optional[str] = None):
    """
    Decorator to require authentication for a function.
    
    Args:
        role: Optional role requirement.
    
    Example:
        @require_auth()
        def protected_function():
            return {"data": "secret"}
        
        @require_auth(role="admin")
        def admin_function():
            return {"data": "admin only"}
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(request: Request, *args, **kwargs):
            # Check if user is authenticated
            user_id = getattr(request.state, "user_id", None)
            
            if user_id is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required",
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            # Check role if specified
            if role:
                user_role = getattr(request.state, "user_role", None)
                if user_role != role:
                    # Check hierarchy
                    from ghostapi.auth.roles import has_role
                    if not has_role(user_role, role):
                        raise HTTPException(
                            status_code=status.HTTP_403_FORBIDDEN,
                            detail=f"Role '{role}' required"
                        )
            
            # Call function
            result = func(request=request, *args, **kwargs)
            
            # Handle coroutines
            if asyncio.iscoroutine(result):
                result = await result
            
            return result
        
        return wrapper
    return decorator


def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    Decorator to retry function on failure.
    
    Args:
        max_attempts: Maximum number of attempts.
        delay: Initial delay between retries in seconds.
        backoff: Multiplier for delay after each retry.
    
    Example:
        @retry(max_attempts=3, delay=1.0)
        def unreliable_api_call():
            return fetch_data()
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            current_delay = delay
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    result = func(*args, **kwargs)
                    if asyncio.iscoroutine(result):
                        result = await result
                    return result
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
            
            raise last_exception
        
        return wrapper
    return decorator


def timeout(seconds: float = 30.0):
    """
    Decorator to add timeout to function.
    
    Args:
        seconds: Timeout in seconds.
    
    Example:
        @timeout(seconds=10.0)
        def slow_operation():
            return long_computation()
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=seconds
                )
            except asyncio.TimeoutError:
                raise HTTPException(
                    status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                    detail=f"Operation timed out after {seconds} seconds"
                )
        
        return wrapper
    return decorator


def validate_params(**validators):
    """
    Decorator to validate function parameters.
    
    Args:
        **validators: Parameter name to validator function mappings.
    
    Example:
        @validate_params(
            age=lambda x: x >= 0,
            email=lambda x: '@' in x
        )
        def create_user(name: str, age: int, email: str):
            return {"name": name, "age": age, "email": email}
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            for param_name, validator in validators.items():
                if param_name in kwargs:
                    value = kwargs[param_name]
                    try:
                        if not validator(value):
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"Invalid value for parameter '{param_name}'"
                            )
                    except HTTPException:
                        raise
                    except Exception as e:
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"Validation failed for '{param_name}': {str(e)}"
                        )
            
            result = func(*args, **kwargs)
            if asyncio.iscoroutine(result):
                result = await result
            return result
        
        return wrapper
    return decorator
