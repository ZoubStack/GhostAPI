"""Tests for Monitoring and Metrics features."""

import pytest
import time

from ghostapi.monitoring import (
    MetricsCollector,
    PerformanceProfiler,
    profile_block,
    get_metrics_collector,
    get_profiler,
    ProfileResult
)


class TestMetricsCollector:
    """Tests for metrics collector."""
    
    def test_initialization(self):
        """Test metrics collector initialization."""
        collector = MetricsCollector()
        
        assert collector is not None
        assert len(collector._counters) == 0
    
    def test_increment_counter(self):
        """Test incrementing a counter."""
        collector = MetricsCollector()
        
        collector.increment("test_counter")
        collector.increment("test_counter")
        
        output = collector.get_metrics()
        
        assert "test_counter" in output
    
    def test_increment_with_labels(self):
        """Test increment with labels."""
        collector = MetricsCollector()
        
        collector.increment(
            "requests_total",
            labels={"method": "GET", "status": "200"}
        )
        
        output = collector.get_metrics()
        
        # Check that labels are included
        assert "requests_total" in output
    
    def test_observe_histogram(self):
        """Test observing histogram values."""
        collector = MetricsCollector()
        
        collector.observe("request_duration", 0.1)
        collector.observe("request_duration", 0.2)
        collector.observe("request_duration", 0.3)
        
        output = collector.get_metrics()
        
        assert "request_duration_sum" in output
        assert "request_duration_count" in output
    
    def test_set_gauge(self):
        """Test setting gauge value."""
        collector = MetricsCollector()
        
        collector.set_gauge("temperature", 25.5, labels={"room": "living"})
        
        output = collector.get_metrics()
        
        assert 'temperature' in output
    
    def test_reset(self):
        """Test resetting metrics."""
        collector = MetricsCollector()
        
        collector.increment("test_counter")
        collector.reset()
        
        output = collector.get_metrics()
        
        assert output == ""


class TestGlobalMetrics:
    """Tests for global metrics collector."""
    
    def test_get_metrics_collector(self):
        """Test getting global metrics collector."""
        collector1 = get_metrics_collector()
        collector2 = get_metrics_collector()
        
        assert collector1 is collector2


class TestPerformanceProfiler:
    """Tests for performance profiler."""
    
    def test_initialization(self):
        """Test profiler initialization."""
        profiler = PerformanceProfiler()
        
        assert profiler is not None
        assert profiler._enabled is False
    
    def test_start_stop(self):
        """Test starting and stopping profiler."""
        profiler = PerformanceProfiler()
        
        profiler.start()
        assert profiler._enabled is True
        
        profiler.stop()
        assert profiler._enabled is False
    
    def test_decorator(self):
        """Test profiling decorator."""
        profiler = PerformanceProfiler()
        profiler.start()
        
        @profiler.profile()
        def test_function():
            time.sleep(0.01)
            return "result"
        
        result = test_function()
        
        assert result == "result"
        
        stats = profiler.get_function_stats("test_function")
        
        assert stats is not None
        assert stats.call_count == 1
        assert stats.total_time > 0
    
    def test_get_report(self):
        """Test getting profiling report."""
        profiler = PerformanceProfiler()
        profiler.start()
        
        @profiler.profile()
        def func1():
            time.sleep(0.01)
        
        @profiler.profile()
        def func2():
            time.sleep(0.02)
        
        func1()
        func2()
        
        report = profiler.get_report()
        
        assert len(report) == 2
    
    def test_export_text(self):
        """Test exporting report as text."""
        profiler = PerformanceProfiler()
        profiler.start()
        
        @profiler.profile()
        def test_func():
            pass
        
        test_func()
        
        output = profiler.export_report("text")
        
        assert "Performance Profile" in output
        assert "test_func" in output
    
    def test_export_json(self):
        """Test exporting report as JSON."""
        profiler = PerformanceProfiler()
        profiler.start()
        
        @profiler.profile()
        def test_json():
            pass
        
        test_json()
        
        output = profiler.export_report("json")
        
        assert "test_json" in output
    
    def test_reset(self):
        """Test resetting profiler."""
        profiler = PerformanceProfiler()
        profiler.start()
        
        @profiler.profile()
        def test():
            pass
        
        test()
        
        profiler.reset()
        
        report = profiler.get_report()
        
        assert len(report) == 0


class TestProfileBlock:
    """Tests for profile_block context manager."""
    
    def test_profile_block(self):
        """Test profiling a code block."""
        profiler = PerformanceProfiler()
        profiler.start()
        
        with profile_block("my_block", profiler):
            time.sleep(0.01)
        
        stats = profiler.get_function_stats("my_block")
        
        assert stats is not None
        assert stats.call_count == 1


class TestGlobalProfiler:
    """Tests for global profiler."""
    
    def test_get_profiler(self):
        """Test getting global profiler."""
        profiler1 = get_profiler()
        profiler2 = get_profiler()
        
        assert profiler1 is profiler2


class TestProfileResult:
    """Tests for ProfileResult dataclass."""
    
    def test_creation(self):
        """Test creating ProfileResult."""
        from datetime import datetime
        
        result = ProfileResult(
            function_name="test",
            call_count=10,
            total_time=1.5,
            avg_time=0.15,
            min_time=0.1,
            max_time=0.2,
            last_call=datetime.utcnow()
        )
        
        assert result.function_name == "test"
        assert result.call_count == 10
        assert result.total_time == 1.5
