"""
Monitoring and Metrics module for GhostAPI.

Features:
- Prometheus metrics export
- Request/response tracking
- Error tracking
- Performance profiling
"""

import time
import threading
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
from contextlib import contextmanager

from fastapi import FastAPI, Request, Response
from pydantic import BaseModel


# Prometheus-compatible metrics
class MetricsCollector:
    """
    Collects and exposes Prometheus metrics.
    
    Example:
        metrics = MetricsCollector()
        
        # Increment counter
        metrics.increment("requests_total", labels={"method": "GET", "status": "200"})
        
        # Observe histogram
        metrics.observe("request_duration_seconds", 0.125, labels={"endpoint": "/api/users"})
        
        # Get metrics in Prometheus format
        output = metrics.get_metrics()
    """
    
    def __init__(self):
        self._counters: Dict[str, Dict[tuple, float]] = defaultdict(lambda: defaultdict(float))
        self._histograms: Dict[str, Dict[tuple, List[float]]] = defaultdict(lambda: defaultdict(list))
        self._gauges: Dict[str, Dict[tuple, float]] = defaultdict(lambda: defaultdict(float))
        self._lock = threading.Lock()
    
    def _labels_to_tuple(self, labels: Dict[str, str]) -> tuple:
        """Convert labels dict to sorted tuple."""
        return tuple(sorted(labels.items())) if labels else ()
    
    def increment(self, name: str, value: float = 1, labels: Optional[Dict[str, str]] = None) -> None:
        """Increment a counter metric."""
        with self._lock:
            key = self._labels_to_tuple(labels)
            self._counters[name][key] += value
    
    def observe(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Observe a value for histogram metric."""
        with self._lock:
            key = self._labels_to_tuple(labels)
            self._histograms[name][key].append(value)
    
    def set_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """Set a gauge metric value."""
        with self._lock:
            key = self._labels_to_tuple(labels)
            self._gauges[name][key] = value
    
    def get_metrics(self) -> str:
        """Get all metrics in Prometheus format."""
        lines = []
        
        with self._lock:
            # Counters
            for name, values in self._counters.items():
                for labels, value in values.items():
                    labels_str = _format_labels(labels)
                    lines.append(f"{name}{{labels_str}} {value}")
            
            # Gauges
            for name, values in self._gauges.items():
                for labels, value in values.items():
                    labels_str = _format_labels(labels)
                    lines.append(f"{name}{{labels_str}} {value}")
            
            # Histograms
            for name, values in self._histograms.items():
                for labels, observations in values.items():
                    if observations:
                        labels_str = _format_labels(labels)
                        obs_sum = sum(observations)
                        obs_count = len(observations)
                        
                        # Prometheus histogram format
                        lines.append(f"{name}_sum{labels_str} {obs_sum}")
                        lines.append(f"{name}_count{labels_str} {obs_count}")
                        
                        # Buckets
                        buckets = [0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
                        for bucket in buckets:
                            count = sum(1 for v in observations if v <= bucket)
                            lines.append(f"{name}_bucket{{{labels_str},le=\"{bucket}\"}} {count}")
        
        return "\n".join(lines)
    
    def reset(self) -> None:
        """Reset all metrics."""
        with self._lock:
            self._counters.clear()
            self._histograms.clear()
            self._gauges.clear()


def _format_labels(labels: tuple) -> str:
    """Format labels for Prometheus."""
    if not labels:
        return ""
    return ','.join(f'{k}="{v}"' for k, v in labels)


# Global metrics instance
_metrics_collector: Optional[MetricsCollector] = None


def get_metrics_collector() -> MetricsCollector:
    """Get global metrics collector."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector


def set_metrics_collector(collector: MetricsCollector) -> None:
    """Set global metrics collector."""
    global _metrics_collector
    _metrics_collector = collector


# Middleware for automatic metrics collection
class MonitoringMiddleware:
    """
    FastAPI middleware for automatic request monitoring.
    
    Example:
        from fastapi import FastAPI
        from ghostapi.monitoring import MonitoringMiddleware
        
        app = FastAPI()
        app.add_middleware(MonitoringMiddleware)
    """
    
    def __init__(
        self,
        app: FastAPI,
        collector: Optional[MetricsCollector] = None,
        track_request_body: bool = False,
        track_response_body: bool = False
    ):
        self.app = app
        self.collector = collector or get_metrics_collector()
        self.track_request_body = track_request_body
        self.track_response_body = track_response_body
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Start timing
        start_time = time.time()
        
        # Get request info
        method = scope.get("method", "UNKNOWN")
        path = scope.get("path", "/")
        client = scope.get("client")
        ip = client[0] if client else "unknown"
        
        # Process request
        status_code = 500
        
        async def send_wrapper(message):
            nonlocal status_code
            if message["type"] == "http.response.start":
                status_code = message["status"]
            await send(message)
        
        try:
            await self.app(scope, receive, send_wrapper)
        except Exception:
            status_code = 500
            raise
        finally:
            # Calculate duration
            duration = time.time() - start_time
            
            # Record metrics
            self.collector.increment(
                "ghostapi_requests_total",
                labels={
                    "method": method,
                    "endpoint": path,
                    "status": str(status_code)
                }
            )
            
            self.collector.observe(
                "ghostapi_request_duration_seconds",
                duration,
                labels={
                    "method": method,
                    "endpoint": path
                }
            )


# Performance profiler
@dataclass
class ProfileResult:
    """Result of a profiling session."""
    function_name: str
    call_count: int
    total_time: float
    avg_time: float
    min_time: float
    max_time: float
    last_call: datetime


class PerformanceProfiler:
    """
    Profiles function execution time automatically.
    
    Example:
        profiler = PerformanceProfiler()
        profiler.start()
        
        # Or use as decorator
        @profiler.profile()
        def my_function():
            return expensive_operation()
        
        # Get report
        report = profiler.get_report()
    """
    
    def __init__(self):
        self._profiles: Dict[str, ProfileResult] = {}
        self._lock = threading.Lock()
        self._enabled = False
    
    def start(self) -> None:
        """Start profiling."""
        self._enabled = True
    
    def stop(self) -> None:
        """Stop profiling."""
        self._enabled = False
    
    def profile(self, func: Optional[Callable] = None, name: Optional[str] = None):
        """Decorator to profile a function."""
        def decorator(f: Callable) -> Callable:
            func_name = name if name else f.__name__
            
            def wrapper(*args, **kwargs):
                if not self._enabled:
                    return f(*args, **kwargs)
                
                start = time.perf_counter()
                try:
                    return f(*args, **kwargs)
                finally:
                    duration = time.perf_counter() - start
                    self._record_call(func_name, duration)
            
            return wrapper
        
        if func is not None:
            return decorator(func)
        
        # If name is provided, return decorator directly
        return decorator
    
    def _record_call(self, name: str, duration: float) -> None:
        """Record a function call."""
        with self._lock:
            if name not in self._profiles:
                self._profiles[name] = ProfileResult(
                    function_name=name,
                    call_count=0,
                    total_time=0,
                    avg_time=0,
                    min_time=float('inf'),
                    max_time=0,
                    last_call=datetime.utcnow()
                )
            
            profile = self._profiles[name]
            profile.call_count += 1
            profile.total_time += duration
            profile.avg_time = profile.total_time / profile.call_count
            profile.min_time = min(profile.min_time, duration)
            profile.max_time = max(profile.max_time, duration)
            profile.last_call = datetime.utcnow()
    
    def get_report(self, sort_by: str = "total_time") -> List[ProfileResult]:
        """Get profiling report."""
        with self._lock:
            profiles = list(self._profiles.values())
        
        if sort_by == "total_time":
            return sorted(profiles, key=lambda x: x.total_time, reverse=True)
        elif sort_by == "avg_time":
            return sorted(profiles, key=lambda x: x.avg_time, reverse=True)
        elif sort_by == "call_count":
            return sorted(profiles, key=lambda x: x.call_count, reverse=True)
        
        return profiles
    
    def get_function_stats(self, name: str) -> Optional[ProfileResult]:
        """Get stats for a specific function."""
        with self._lock:
            return self._profiles.get(name)
    
    def reset(self) -> None:
        """Reset all profiling data."""
        with self._lock:
            self._profiles.clear()
    
    def export_report(self, format: str = "text") -> str:
        """Export profiling report."""
        profiles = self.get_report()
        
        if format == "text":
            lines = ["=== Performance Profile ===", ""]
            lines.append(f"{'Function':<30} {'Calls':>10} {'Total':>12} {'Avg':>12} {'Min':>12} {'Max':>12}")
            lines.append("-" * 90)
            
            for p in profiles:
                lines.append(
                    f"{p.function_name:<30} {p.call_count:>10} "
                    f"{p.total_time:>12.4f} {p.avg_time:>12.4f} "
                    f"{p.min_time:>12.4f} {p.max_time:>12.4f}"
                )
            
            return "\n".join(lines)
        
        elif format == "json":
            import json
            return json.dumps([{
                "function_name": p.function_name,
                "call_count": p.call_count,
                "total_time": p.total_time,
                "avg_time": p.avg_time,
                "min_time": p.min_time,
                "max_time": p.max_time,
                "last_call": p.last_call.isoformat()
            } for p in profiles], indent=2)
        
        return str(profiles)


# Context manager for profiling blocks
@contextmanager
def profile_block(name: str, profiler: Optional[PerformanceProfiler] = None):
    """
    Profile a block of code.
    
    Example:
        with profile_block("database_query"):
            # Code to profile
            result = db.query()
    """
    if profiler is None:
        profiler = _profiler
    
    if not profiler._enabled:
        yield
        return
    
    start = time.perf_counter()
    try:
        yield
    finally:
        duration = time.perf_counter() - start
        profiler._record_call(name, duration)


# Global profiler instance
_profiler = PerformanceProfiler()


def get_profiler() -> PerformanceProfiler:
    """Get global profiler."""
    return _profiler


def set_profiler(profiler: PerformanceProfiler) -> None:
    """Set global profiler."""
    global _profiler
    _profiler = profiler


# Setup function for FastAPI
def setup_monitoring(
    app: FastAPI,
    enable_prometheus: bool = True,
    enable_profiling: bool = True,
    metrics_path: str = "/metrics"
) -> None:
    """
    Setup monitoring for FastAPI app.
    
    Example:
        from fastapi import FastAPI
        from ghostapi.monitoring import setup_monitoring
        
        app = FastAPI()
        setup_monitoring(app)
    
    Args:
        app: FastAPI application
        enable_prometheus: Enable /metrics endpoint
        enable_profiling: Enable automatic profiling
        metrics_path: Path for metrics endpoint
    """
    # Add monitoring middleware
    app.add_middleware(MonitoringMiddleware)
    
    # Enable profiling if requested
    if enable_profiling:
        _profiler.start()
    
    # Add metrics endpoint if enabled
    if enable_prometheus:
        @app.get(metrics_path)
        async def metrics():
            collector = get_metrics_collector()
            return Response(
                content=collector.get_metrics(),
                media_type="text/plain"
            )
        
        # Add profiling report endpoint
        @app.get("/profile")
        async def profile_report():
            return Response(
                content=_profiler.export_report(),
                media_type="text/plain"
            )


# Prometheus metrics
PROMETHEUS_METRICS = {
    "requests_total": "Total number of requests",
    "request_duration_seconds": "Request duration in seconds",
    "errors_total": "Total number of errors",
    "cache_hits_total": "Total number of cache hits",
    "cache_misses_total": "Total number of cache misses",
    "active_connections": "Number of active connections"
}
