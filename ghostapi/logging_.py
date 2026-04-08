"""Logging and exception handling for ghostapi."""

import logging
import sys
from typing import Any, Callable, Optional

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from ghostapi.auth.exceptions import GhostAPIException

# Configure logging
logging.basicConfig = logging.basicConfig


def setup_logging(
    app: FastAPI,
    level: int = logging.INFO,
    log_format: Optional[str] = None
) -> None:
    """
    Setup logging for the application.
    
    Args:
        app: The FastAPI application.
        level: Logging level (default: INFO).
        log_format: Custom log format.
    """
    if log_format is None:
        log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    logging.basicConfig(
        level=level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set FastAPI/uvicorn loggers
    logging.getLogger("fastapi").setLevel(logging.WARNING)
    logging.getLogger("uvicorn").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance.
    
    Args:
        name: Logger name.
    
    Returns:
        Logger instance.
    """
    return logging.getLogger(name)


class ExceptionHandlers:
    """Global exception handlers for FastAPI."""
    
    @staticmethod
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        """Handle HTTP exceptions."""
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )
    
    @staticmethod
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        """Handle validation errors."""
        errors = []
        for error in exc.errors():
            errors.append({
                "loc": list(error.get("loc", [])),
                "msg": str(error.get("msg", "")),
                "type": error.get("type", "")
            })
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": "Validation error", "errors": errors}
        )
    
    @staticmethod
    async def ghost_api_exception_handler(request: Request, exc: GhostAPIException) -> JSONResponse:
        """Handle custom GhostAPI exceptions."""
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message}
        )
    
    @staticmethod
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handle generic exceptions."""
        import os
        logger = get_logger("ghostapi")
        debug = os.environ.get("GHOSTAPI_DEBUG", "false").lower() == "true"
        
        if debug:
            logger.error(f"Unhandled exception: {exc}", exc_info=True)
            detail = str(exc)
        else:
            logger.error(f"Unhandled exception: {exc.__class__.__name__}")
            detail = "Internal server error"
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": detail}
        )


def add_exception_handlers(app: FastAPI) -> None:
    """
    Add global exception handlers to the application.
    
    Args:
        app: The FastAPI application.
    """
    app.add_exception_handler(StarletteHTTPException, ExceptionHandlers.http_exception_handler)
    app.add_exception_handler(RequestValidationError, ExceptionHandlers.validation_exception_handler)
    app.add_exception_handler(GhostAPIException, ExceptionHandlers.ghost_api_exception_handler)
    app.add_exception_handler(Exception, ExceptionHandlers.generic_exception_handler)
