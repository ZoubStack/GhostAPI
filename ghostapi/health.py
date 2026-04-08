"""Health check endpoint for ghostapi."""

import time
from typing import Any, Dict, Optional

from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse


class HealthCheck:
    """
    Health check manager for GhostAPI.
    
    Provides /health endpoint that reports status of all components.
    """
    
    def __init__(self) -> None:
        self._start_time = time.time()
        self._checks = {}
    
    def register_check(self, name: str, check_func: callable) -> None:
        """
        Register a health check function.
        
        Args:
            name: Name of the component to check.
            check_func: Function that returns True if healthy, False otherwise.
        """
        self._checks[name] = check_func
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get overall health status.
        
        Returns:
            Dictionary with health information.
        """
        uptime = time.time() - self._start_time
        
        # Run all checks
        components = {}
        all_healthy = True
        
        for name, check_func in self._checks.items():
            try:
                is_healthy = check_func()
                components[name] = "ok" if is_healthy else "error"
                if not is_healthy:
                    all_healthy = False
            except Exception as e:
                components[name] = f"error: {str(e)}"
                all_healthy = False
        
        return {
            "status": "healthy" if all_healthy else "degraded",
            "uptime_seconds": uptime,
            "components": components
        }


# Global health check instance
_health_check: Optional[HealthCheck] = None


def get_health_check() -> HealthCheck:
    """Get the global health check instance."""
    global _health_check
    if _health_check is None:
        _health_check = HealthCheck()
    return _health_check


def add_health_check(app: FastAPI) -> None:
    """
    Add health check endpoint to the application.
    
    Args:
        app: The FastAPI application.
    """
    health = get_health_check()
    
    # Register default checks
    try:
        from ghostapi.storage import get_storage
        health.register_check("storage", lambda: get_storage() is not None)
    except Exception:
        pass
    
    try:
        from ghostapi.cache import get_cache
        health.register_check("cache", lambda: get_cache() is not None)
    except Exception:
        pass
    
    @app.get("/health", tags=["health"])
    async def health_check(response: Response) -> JSONResponse:
        """
        Health check endpoint.
        
        Returns status of all components.
        """
        status = health.get_status()
        
        # Set appropriate status code
        if status["status"] == "healthy":
            response.status_code = 200
        else:
            response.status_code = 503
        
        return JSONResponse(status_code=response.status_code, content=status)
    
    @app.get("/health/ready", tags=["health"])
    async def readiness_check(response: Response) -> JSONResponse:
        """
        Readiness check endpoint (for Kubernetes).
        
        Returns 200 if ready to serve traffic.
        """
        status = health.get_status()
        
        if status["status"] == "healthy":
            return JSONResponse(status_code=200, content={"ready": True})
        else:
            return JSONResponse(status_code=503, content={"ready": False})
    
    @app.get("/health/live", tags=["health"])
    async def liveness_check(response: Response) -> JSONResponse:
        """
        Liveness check endpoint (for Kubernetes).
        
        Returns 200 if the application is running.
        """
        return JSONResponse(status_code=200, content={"alive": True})
