"""
Audit Logs module for GhostAPI.

Automatically logs all access to secured routes with:
- User information
- Route accessed
- Timestamp
- IP address
- Request details
"""

import os
import json
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
from pathlib import Path

from fastapi import Request, HTTPException
from pydantic import BaseModel


class AuditAction(str, Enum):
    """Audit action types."""
    LOGIN = "login"
    LOGOUT = "logout"
    LOGIN_FAILED = "login_failed"
    TOKEN_REFRESH = "token_refresh"
    TOKEN_REVOKED = "token_revoked"
    ACCESS_DENIED = "access_denied"
    ACCESS_GRANTED = "access_granted"
    DATA_READ = "data_read"
    DATA_WRITE = "data_write"
    DATA_DELETE = "data_delete"
    OAUTH_LOGIN = "oauth_login"
    PASSWORD_CHANGE = "password_change"
    ROLE_CHANGE = "role_change"


class AuditLevel(str, Enum):
    """Audit log levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEntry:
    """Single audit log entry."""
    id: str
    timestamp: datetime
    action: AuditAction
    level: AuditLevel
    user_id: Optional[str] = None
    user_email: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    route: Optional[str] = None
    method: Optional[str] = None
    status_code: Optional[int] = None
    response_time_ms: Optional[float] = None
    request_body: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        data["action"] = self.action.value
        data["level"] = self.level.value
        return data


class AuditLogger:
    """
    Audit logger for tracking all secure route access.
    
    Example:
        audit = AuditLogger()
        
        @app.middleware("http")
        async def audit_middleware(request, call_next):
            return await audit.log_request(request, call_next)
    """
    
    def __init__(
        self,
        storage_path: Optional[str] = None,
        max_entries: int = 10000,
        retention_days: int = 90,
        include_request_body: bool = False
    ):
        """
        Initialize audit logger.
        
        Args:
            storage_path: Path to store audit logs (file or directory)
            max_entries: Maximum entries to keep in memory
            retention_days: Days to retain logs
            include_request_body: Whether to log request body
        """
        self.storage_path = storage_path or os.getenv(
            "AUDIT_LOG_PATH",
            "data/audit_logs.json"
        )
        self.max_entries = max_entries
        self.retention_days = retention_days
        self.include_request_body = include_request_body
        
        self._entries: List[AuditEntry] = []
        self._id_counter = 0
        
        # Ensure storage directory exists
        Path(self.storage_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing logs
        self._load_logs()
    
    def _generate_id(self) -> str:
        """Generate unique entry ID."""
        import uuid
        return str(uuid.uuid4())
    
    def _load_logs(self) -> None:
        """Load existing logs from storage."""
        try:
            path = Path(self.storage_path)
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    for entry in data:
                        entry["timestamp"] = datetime.fromisoformat(entry["timestamp"])
                        self._entries.append(AuditEntry(**entry))
        except Exception:
            pass
    
    def _save_logs(self) -> None:
        """Save logs to storage."""
        try:
            # Clean old entries first
            self._cleanup_old_entries()
            
            # Save to file
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(
                    [e.to_dict() for e in self._entries],
                    f,
                    indent=2,
                    ensure_ascii=False
                )
        except Exception:
            pass
    
    def _cleanup_old_entries(self) -> None:
        """Remove entries older than retention period."""
        cutoff = datetime.utcnow() - timedelta(days=self.retention_days)
        self._entries = [
            e for e in self._entries
            if e.timestamp > cutoff
        ]
    
    async def log_request(
        self,
        request: Request,
        call_next,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        action: Optional[AuditAction] = None
    ) -> Any:
        """
        Log a request (middleware compatible).
        
        Example:
            @app.middleware("http")
            async def audit_middleware(request, call_next):
                return await audit_logger.log_request(request, call_next)
        """
        import time
        
        start_time = time.time()
        client_ip = request.client.host if request.client else None
        
        # Extract user info from request state if available
        if not user_id and hasattr(request.state, "user_id"):
            user_id = request.state.user_id
        if not user_email and hasattr(request.state, "user_email"):
            user_email = request.state.user_email
        
        try:
            response = await call_next(request)
            status_code = response.status_code
            
            # Determine action
            if action is None:
                if request.url.path.startswith("/api/auth/login"):
                    action = AuditAction.LOGIN
                elif request.url.path.startswith("/api/auth/logout"):
                    action = AuditAction.LOGOUT
                elif status_code == 401:
                    action = AuditAction.ACCESS_DENIED
                elif request.method in ["GET"]:
                    action = AuditAction.DATA_READ
                elif request.method in ["POST", "PUT", "PATCH"]:
                    action = AuditAction.DATA_WRITE
                elif request.method == "DELETE":
                    action = AuditAction.DATA_DELETE
                else:
                    action = AuditAction.ACCESS_GRANTED
            
            # Determine level
            if status_code >= 500:
                level = AuditLevel.ERROR
            elif status_code >= 400:
                level = AuditLevel.WARNING
            else:
                level = AuditLevel.INFO
            
            # Calculate response time
            response_time = (time.time() - start_time) * 1000
            
            # Create entry
            entry = AuditEntry(
                id=self._generate_id(),
                timestamp=datetime.utcnow(),
                action=action,
                level=level,
                user_id=user_id,
                user_email=user_email,
                ip_address=client_ip,
                user_agent=request.headers.get("user-agent"),
                route=str(request.url.path),
                method=request.method,
                status_code=status_code,
                response_time_ms=response_time,
                metadata={
                    "query_params": dict(request.query_params),
                    "headers": dict(request.headers)
                }
            )
            
            # Add to entries
            self._add_entry(entry)
            
            return response
            
        except HTTPException as e:
            # Log error
            entry = AuditEntry(
                id=self._generate_id(),
                timestamp=datetime.utcnow(),
                action=action or AuditAction.ACCESS_DENIED,
                level=AuditLevel.ERROR,
                user_id=user_id,
                user_email=user_email,
                ip_address=client_ip,
                route=str(request.url.path),
                method=request.method,
                status_code=e.status_code,
                metadata={"error": str(e.detail)}
            )
            
            self._add_entry(entry)
            raise
    
    def _add_entry(self, entry: AuditEntry) -> None:
        """Add entry to memory and optionally save."""
        self._entries.append(entry)
        
        # Trim if needed
        if len(self._entries) > self.max_entries:
            self._entries = self._entries[-self.max_entries:]
        
        # Save synchronously to avoid async issues
        try:
            self._save_logs()
        except RuntimeError:
            # No event loop running, will save later
            pass
    
    async def _async_save(self) -> None:
        """Save logs asynchronously."""
        self._save_logs()
    
    def log_event(
        self,
        action: AuditAction,
        level: AuditLevel = AuditLevel.INFO,
        user_id: Optional[str] = None,
        user_email: Optional[str] = None,
        ip_address: Optional[str] = None,
        route: Optional[str] = None,
        method: Optional[str] = None,
        status_code: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditEntry:
        """
        Log a specific event.
        
        Example:
            audit.log_event(
                action=AuditAction.LOGIN,
                user_id="123",
                user_email="user@example.com",
                ip_address="192.168.1.1"
            )
        """
        entry = AuditEntry(
            id=self._generate_id(),
            timestamp=datetime.utcnow(),
            action=action,
            level=level,
            user_id=user_id,
            user_email=user_email,
            ip_address=ip_address,
            route=route,
            method=method,
            status_code=status_code,
            metadata=metadata or {}
        )
        
        self._add_entry(entry)
        return entry
    
    def get_entries(
        self,
        user_id: Optional[str] = None,
        action: Optional[AuditAction] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 100
    ) -> List[AuditEntry]:
        """
        Query audit entries.
        
        Example:
            entries = audit.get_entries(
                user_id="123",
                start_date=datetime.utcnow() - timedelta(days=7)
            )
        """
        results = self._entries.copy()
        
        if user_id:
            results = [e for e in results if e.user_id == user_id]
        
        if action:
            results = [e for e in results if e.action == action]
        
        if start_date:
            results = [e for e in results if e.timestamp >= start_date]
        
        if end_date:
            results = [e for e in results if e.timestamp <= end_date]
        
        # Sort by timestamp descending
        results.sort(key=lambda x: x.timestamp, reverse=True)
        
        return results[:limit]
    
    def get_user_activity(self, user_id: str) -> Dict[str, Any]:
        """Get activity summary for a user."""
        user_entries = [e for e in self._entries if e.user_id == user_id]
        
        return {
            "user_id": user_id,
            "total_actions": len(user_entries),
            "first_activity": user_entries[-1].timestamp.isoformat() if user_entries else None,
            "last_activity": user_entries[0].timestamp.isoformat() if user_entries else None,
            "actions_by_type": self._count_by_action(user_entries),
            "actions_by_level": self._count_by_level(user_entries)
        }
    
    def _count_by_action(self, entries: List[AuditEntry]) -> Dict[str, int]:
        """Count entries by action type."""
        counts = {}
        for entry in entries:
            action = entry.action.value
            counts[action] = counts.get(action, 0) + 1
        return counts
    
    def _count_by_level(self, entries: List[AuditEntry]) -> Dict[str, int]:
        """Count entries by level."""
        counts = {}
        for entry in entries:
            level = entry.level.value
            counts[level] = counts.get(level, 0) + 1
        return counts
    
    def export_logs(
        self,
        format: str = "json",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> str:
        """
        Export audit logs.
        
        Args:
            format: Output format ("json", "csv")
            start_date: Filter start date
            end_date: Filter end date
        
        Returns:
            Formatted log string
        """
        entries = self._entries.copy()
        
        if start_date:
            entries = [e for e in entries if e.timestamp >= start_date]
        if end_date:
            entries = [e for e in entries if e.timestamp <= end_date]
        
        if format == "json":
            return json.dumps(
                [e.to_dict() for e in entries],
                indent=2,
                ensure_ascii=False
            )
        elif format == "csv":
            import csv
            import io
            
            output = io.StringIO()
            if entries:
                fieldnames = list(entries[0].to_dict().keys())
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                for entry in entries:
                    row = entry.to_dict()
                    row["timestamp"] = entry.timestamp.isoformat()
                    writer.writerow(row)
            
            return output.getvalue()
        
        return str(entries)
    
    def clear_old_logs(self, days: int) -> int:
        """
        Clear logs older than specified days.
        
        Returns:
            Number of entries deleted
        """
        cutoff = datetime.utcnow() - timedelta(days=days)
        before = len(self._entries)
        
        self._entries = [
            e for e in self._entries
            if e.timestamp > cutoff
        ]
        
        deleted = before - len(self._entries)
        
        if deleted > 0:
            self._save_logs()
        
        return deleted


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get the global audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger()
    return _audit_logger


def set_audit_logger(logger: AuditLogger) -> None:
    """Set the global audit logger instance."""
    global _audit_logger
    _audit_logger = logger


def create_audit_middleware(audit_logger: Optional[AuditLogger] = None):
    """
    Create audit middleware for FastAPI.
    
    Example:
        audit_logger = AuditLogger()
        app.add_middleware(AuditMiddleware, audit_logger=audit_logger)
    """
    from starlette.middleware.base import BaseHTTPMiddleware
    
    class AuditMiddleware(BaseHTTPMiddleware):
        def __init__(self, app, audit_logger=None):
            super().__init__(app)
            self.audit_logger = audit_logger or get_audit_logger()
        
        async def dispatch(self, request: Request, call_next):
            # Skip audit for certain paths
            skip_paths = ["/docs", "/openapi.json", "/redoc", "/health"]
            
            if any(request.url.path.startswith(p) for p in skip_paths):
                return await call_next(request)
            
            return await self.audit_logger.log_request(request, call_next)
    
    return AuditMiddleware
