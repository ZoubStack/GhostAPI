"""Authentication exceptions for ghostapi."""

from typing import Any


class GhostAPIException(Exception):
    """Base exception for GhostAPI authentication."""

    def __init__(self, message: str, status_code: int = 401) -> None:
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AuthenticationError(GhostAPIException):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Authentication failed") -> None:
        super().__init__(message, status_code=401)


class InvalidTokenError(GhostAPIException):
    """Raised when token is invalid or expired."""

    def __init__(self, message: str = "Invalid or expired token") -> None:
        super().__init__(message, status_code=401)


class AuthorizationError(GhostAPIException):
    """Raised when user lacks required permissions."""

    def __init__(self, message: str = "Insufficient permissions") -> None:
        super().__init__(message, status_code=403)


class UserNotFoundError(GhostAPIException):
    """Raised when user is not found."""

    def __init__(self, message: str = "User not found") -> None:
        super().__init__(message, status_code=404)


class UserAlreadyExistsError(GhostAPIException):
    """Raised when trying to register an existing user."""

    def __init__(self, message: str = "User already exists") -> None:
        super().__init__(message, status_code=409)


class InvalidCredentialsError(GhostAPIException):
    """Raised when credentials are invalid."""

    def __init__(self, message: str = "Invalid credentials") -> None:
        super().__init__(message, status_code=401)
