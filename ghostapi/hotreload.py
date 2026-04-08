"""
Hot reload module for individual functions.

This module allows reloading specific functions without restarting the entire server.
Useful for microservices development.
"""

import importlib
import inspect
import os
import time
from typing import Any, Callable, Dict, Optional
from threading import Thread
from pathlib import Path


class FunctionWatcher:
    """
    Watches a file for changes and reloads specific functions.
    
    Example:
        watcher = FunctionWatcher()
        
        # Watch a specific function
        watcher.watch_function("my_module", "my_function")
        
        # Or watch all functions in a module
        watcher.watch_module("my_module")
        
        # Start watching
        watcher.start()
    """
    
    def __init__(self, callback: Optional[Callable] = None) -> None:
        self._watched_functions: Dict[str, Callable] = {}
        self._watched_modules: Dict[str, Any] = {}
        self._last_modified: Dict[str, float] = {}
        self._running = False
        self._callback = callback
        self._poll_interval = 1.0  # seconds
    
    def watch_function(self, module_name: str, function_name: str) -> None:
        """
        Watch a specific function for changes.
        
        Args:
            module_name: Name of the module containing the function.
            function_name: Name of the function to watch.
        """
        key = f"{module_name}.{function_name}"
        self._watched_functions[key] = {
            "module": module_name,
            "function": function_name,
            "last_reload": time.time()
        }
    
    def watch_module(self, module_name: str) -> None:
        """
        Watch all functions in a module.
        
        Args:
            module_name: Name of the module to watch.
        """
        self._watched_modules[module_name] = {
            "last_reload": time.time()
        }
    
    def unwatch_function(self, module_name: str, function_name: str) -> bool:
        """Stop watching a function."""
        key = f"{module_name}.{function_name}"
        if key in self._watched_functions:
            del self._watched_functions[key]
            return True
        return False
    
    def unwatch_module(self, module_name: str) -> bool:
        """Stop watching a module."""
        if module_name in self._watched_modules:
            del self._watched_modules[module_name]
            return True
        return False
    
    def _get_module_path(self, module_name: str) -> Optional[str]:
        """Get the file path of a module."""
        try:
            import sys
            if module_name in sys.modules:
                module = sys.modules[module_name]
                return inspect.getfile(module)
        except Exception:
            pass
        return None
    
    def _check_for_changes(self) -> None:
        """Check if any watched file has changed."""
        current_time = time.time()
        
        # Check individual functions
        for key, info in list(self._watched_functions.items()):
            module_path = self._get_module_path(info["module"])
            if not module_path:
                continue
            
            try:
                mtime = os.path.getmtime(module_path)
                
                if module_path not in self._last_modified:
                    self._last_modified[module_path] = mtime
                    continue
                
                if mtime > self._last_modified[module_path]:
                    self._last_modified[module_path] = mtime
                    self._reload_function(info["module"], info["function"])
                    
            except OSError:
                pass
        
        # Check modules
        for module_name in list(self._watched_modules.keys()):
            module_path = self._get_module_path(module_name)
            if not module_path:
                continue
            
            try:
                mtime = os.path.getmtime(module_path)
                
                if module_path not in self._last_modified:
                    self._last_modified[module_path] = mtime
                    continue
                
                if mtime > self._last_modified[module_path]:
                    self._last_modified[module_path] = mtime
                    self._reload_module(module_name)
                    
            except OSError:
                pass
    
    def _reload_function(self, module_name: str, function_name: str) -> bool:
        """Reload a specific function."""
        try:
            # Reload the module
            if module_name in __import__(module_name.split('.')[0]).__dict__:
                import sys
                if module_name in sys.modules:
                    module = sys.modules[module_name]
                    importlib.reload(module)
            
            # Call callback if provided
            if self._callback:
                self._callback(module_name, function_name)
            
            return True
        except Exception as e:
            print(f"Error reloading function {function_name}: {e}")
            return False
    
    def _reload_module(self, module_name: str) -> None:
        """Reload an entire module."""
        try:
            import sys
            if module_name in sys.modules:
                importlib.reload(sys.modules[module_name])
            
            if self._callback:
                self._callback(module_name, None)
        except Exception as e:
            print(f"Error reloading module {module_name}: {e}")
    
    def start(self, poll_interval: float = 1.0) -> None:
        """
        Start watching for file changes.
        
        Args:
            poll_interval: How often to check for changes (seconds).
        """
        self._poll_interval = poll_interval
        self._running = True
        
        def run():
            while self._running:
                self._check_for_changes()
                time.sleep(self._poll_interval)
        
        thread = Thread(target=run, daemon=True)
        thread.start()
    
    def stop(self) -> None:
        """Stop watching for file changes."""
        self._running = False
    
    def get_watched(self) -> Dict[str, Any]:
        """Get list of watched functions/modules."""
        return {
            "functions": list(self._watched_functions.keys()),
            "modules": list(self._watched_modules.keys())
        }


class FunctionReloader:
    """
    Context manager for hot-reloading a function.
    
    Example:
        with FunctionReloader("my_module", "my_function") as reloader:
            # Function will auto-reload when file changes
            result = my_function()
    """
    
    def __init__(self, module_name: str, function_name: str) -> None:
        self.module_name = module_name
        self.function_name = function_name
        self.watcher = FunctionWatcher()
    
    def __enter__(self):
        self.watcher.watch_function(self.module_name, self.function_name)
        self.watcher.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.watcher.stop()


# Decorator for hot-reload
def hot_reload(module_name: Optional[str] = None):
    """
    Decorator to enable hot-reload for a function.
    
    Example:
        @hot_reload("my_module")
        def my_function():
            return "Hello"
    """
    def decorator(func: Callable) -> Callable:
        module = module_name or func.__module__
        
        # Create watcher for this function
        watcher = FunctionWatcher()
        watcher.watch_function(module, func.__name__)
        
        # Store watcher on function for access
        func._hot_reload_watcher = watcher
        
        return func
    return decorator


# Auto-refresh routes in FastAPI
def setup_hot_reload(app, module_name: str, poll_interval: float = 1.0):
    """
    Setup hot reload for a FastAPI app.
    
    Args:
        app: FastAPI application
        module_name: Module to watch for changes
        poll_interval: How often to check for changes
    
    Returns:
        FunctionWatcher instance
    """
    watcher = FunctionWatcher(
        callback=lambda mod, func: print(f"🔄 Reloaded: {mod}.{func}")
    )
    watcher.watch_module(module_name)
    watcher.start(poll_interval)
    return watcher
