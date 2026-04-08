"""Tests for hot reload functionality."""

import time
import pytest
from ghostapi.hotreload import (
    FunctionWatcher,
    FunctionReloader,
    hot_reload,
    setup_hot_reload
)


class TestFunctionWatcher:
    """Tests for FunctionWatcher class."""
    
    def test_initialization(self):
        """Test FunctionWatcher initialization."""
        watcher = FunctionWatcher()
        assert watcher is not None
        assert not watcher._running
    
    def test_initialization_with_callback(self):
        """Test FunctionWatcher with callback."""
        callback_called = []
        
        def callback(module, func):
            callback_called.append((module, func))
        
        watcher = FunctionWatcher(callback=callback)
        assert watcher._callback is not None
    
    def test_watch_function(self):
        """Test watching a specific function."""
        watcher = FunctionWatcher()
        watcher.watch_function("test_module", "test_function")
        
        watched = watcher.get_watched()
        assert "test_module.test_function" in watched["functions"]
    
    def test_watch_module(self):
        """Test watching an entire module."""
        watcher = FunctionWatcher()
        watcher.watch_module("test_module")
        
        watched = watcher.get_watched()
        assert "test_module" in watched["modules"]
    
    def test_unwatch_function(self):
        """Test unwatching a function."""
        watcher = FunctionWatcher()
        watcher.watch_function("test_module", "test_function")
        
        result = watcher.unwatch_function("test_module", "test_function")
        assert result is True
        
        watched = watcher.get_watched()
        assert "test_module.test_function" not in watched["functions"]
    
    def test_unwatch_function_not_found(self):
        """Test unwatching a non-watched function."""
        watcher = FunctionWatcher()
        
        result = watcher.unwatch_function("test_module", "test_function")
        assert result is False
    
    def test_unwatch_module(self):
        """Test unwatching a module."""
        watcher = FunctionWatcher()
        watcher.watch_module("test_module")
        
        result = watcher.unwatch_module("test_module")
        assert result is True
        
        watched = watcher.get_watched()
        assert "test_module" not in watched["modules"]
    
    def test_start_stop(self):
        """Test starting and stopping the watcher."""
        watcher = FunctionWatcher()
        watcher.start(poll_interval=0.1)
        assert watcher._running is True
        
        watcher.stop()
        assert watcher._running is False


class TestFunctionReloader:
    """Tests for FunctionReloader context manager."""
    
    def test_context_manager(self):
        """Test FunctionReloader as context manager."""
        with FunctionReloader("test_module", "test_function") as reloader:
            assert reloader.watcher is not None
            assert reloader.watcher._running is True
        
        # After exiting context, watcher should be stopped
        assert reloader.watcher._running is False


class TestHotReloadDecorator:
    """Tests for @hot_reload decorator."""
    
    def test_decorator_basic(self):
        """Test basic decorator usage."""
        
        @hot_reload("test_module")
        def test_func():
            return "test"
        
        assert hasattr(test_func, "_hot_reload_watcher")
        assert test_func._hot_reload_watcher is not None
    
    def test_decorator_no_module(self):
        """Test decorator without explicit module."""
        
        @hot_reload()
        def test_func():
            return "test"
        
        assert hasattr(test_func, "_hot_reload_watcher")


class TestSetupHotReload:
    """Tests for setup_hot_reload function."""
    
    def test_setup_basic(self):
        """Test setup_hot_reload basic usage."""
        # This just tests it doesn't crash - actual FastAPI integration
        # would require a more complex test setup
        watcher = setup_hot_reload(None, "test_module", poll_interval=1.0)
        
        assert watcher is not None
        assert isinstance(watcher, FunctionWatcher)
        
        watcher.stop()
    
    def test_setup_custom_interval(self):
        """Test setup_hot_reload with custom poll interval."""
        watcher = setup_hot_reload(None, "test_module", poll_interval=0.5)
        
        assert watcher._poll_interval == 0.5
        
        watcher.stop()
