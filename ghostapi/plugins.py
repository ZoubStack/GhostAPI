"""
Plugin System for GhostAPI

Allows users to create extensions that add new functionality:
- Custom storage strategies
- Custom validation types
- Custom decorators for endpoints
"""

from typing import Any, Callable, Dict, List, Optional, Type
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from functools import wraps
import importlib
import inspect


@dataclass
class PluginMetadata:
    """Metadata for a plugin."""
    name: str
    version: str
    author: str
    description: str = ""
    dependencies: List[str] = field(default_factory=list)


class Plugin(ABC):
    """Base class for all GhostAPI plugins."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self._enabled = True
    
    @abstractmethod
    def get_metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        pass
    
    @abstractmethod
    def on_load(self, app: Any) -> None:
        """Called when plugin is loaded."""
        pass
    
    @abstractmethod
    def on_unload(self) -> None:
        """Called when plugin is unloaded."""
        pass
    
    @property
    def enabled(self) -> bool:
        return self._enabled
    
    def enable(self) -> None:
        self._enabled = True
    
    def disable(self) -> None:
        self._enabled = False


class StoragePlugin(Plugin):
    """Base class for storage strategy plugins."""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get a value by key."""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """Set a value by key."""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete a value by key."""
        pass
    
    @abstractmethod
    def clear(self) -> None:
        """Clear all values."""
        pass
    
    @abstractmethod
    def get_all(self) -> Dict[str, Any]:
        """Get all key-value pairs."""
        pass


class ValidationPlugin(Plugin):
    """Base class for custom validation type plugins."""
    
    @abstractmethod
    def validate(self, value: Any) -> bool:
        """Validate a value."""
        pass
    
    @abstractmethod
    def get_error_message(self, field_name: str, value: Any) -> str:
        """Get error message for validation failure."""
        pass


class DecoratorPlugin(Plugin):
    """Base class for custom decorator plugins."""
    
    @abstractmethod
    def create_decorator(self, *args, **kwargs) -> Callable:
        """Create a decorator function."""
        pass


class PluginRegistry:
    """Registry for managing plugins."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._plugins = {}
            cls._instance._storage_plugins = {}
            cls._instance._validation_plugins = {}
            cls._instance._decorator_plugins = {}
        return cls._instance
    
    def register(self, plugin: Plugin) -> None:
        """Register a plugin."""
        metadata = plugin.get_metadata()
        self._plugins[metadata.name] = plugin
        
        # Register in appropriate category
        if isinstance(plugin, StoragePlugin):
            self._storage_plugins[metadata.name] = plugin
        elif isinstance(plugin, ValidationPlugin):
            self._validation_plugins[metadata.name] = plugin
        elif isinstance(plugin, DecoratorPlugin):
            self._decorator_plugins[metadata.name] = plugin
    
    def unregister(self, name: str) -> None:
        """Unregister a plugin."""
        if name in self._plugins:
            plugin = self._plugins[name]
            plugin.on_unload()
            del self._plugins[name]
            
            # Remove from categories
            if name in self._storage_plugins:
                del self._storage_plugins[name]
            if name in self._validation_plugins:
                del self._validation_plugins[name]
            if name in self._decorator_plugins:
                del self._decorator_plugins[name]
    
    def get_plugin(self, name: str) -> Optional[Plugin]:
        """Get a plugin by name."""
        return self._plugins.get(name)
    
    def get_storage_plugin(self, name: str) -> Optional[StoragePlugin]:
        """Get a storage plugin by name."""
        return self._storage_plugins.get(name)
    
    def get_validation_plugin(self, name: str) -> Optional[ValidationPlugin]:
        """Get a validation plugin by name."""
        return self._validation_plugins.get(name)
    
    def get_decorator_plugin(self, name: str) -> Optional[DecoratorPlugin]:
        """Get a decorator plugin by name."""
        return self._decorator_plugins.get(name)
    
    def list_plugins(self) -> List[PluginMetadata]:
        """List all registered plugins."""
        return [p.get_metadata() for p in self._plugins.values()]
    
    def enable_plugin(self, name: str) -> None:
        """Enable a plugin."""
        plugin = self._plugins.get(name)
        if plugin:
            plugin.enable()
    
    def disable_plugin(self, name: str) -> None:
        """Disable a plugin."""
        plugin = self._plugins.get(name)
        if plugin:
            plugin.disable()


def get_plugin_registry() -> PluginRegistry:
    """Get the global plugin registry."""
    return PluginRegistry()


def register_plugin(plugin: Plugin) -> None:
    """Register a plugin in the global registry."""
    registry = get_plugin_registry()
    registry.register(plugin)


def create_storage_plugin(name: str, version: str, author: str):
    """Decorator to create a storage plugin class."""
    def decorator(cls: Type[StoragePlugin]):
        original_init = cls.__init__
        
        def new_init(self, config=None):
            original_init(self, config)
        
        @wraps(cls, ("__init__", "get_metadata", "on_load", "on_unload", "get", "set", "delete", "clear", "get_all"))
        class WrappedPlugin(cls):
            def get_metadata(self):
                return PluginMetadata(
                    name=name,
                    version=version,
                    author=author
                )
        
        return WrappedPlugin
    return decorator


# ============================================================================
# Custom Middleware System
# ============================================================================

class MiddlewarePlugin(Plugin):
    """Base class for custom middleware plugins."""
    
    @abstractmethod
    def get_middleware(self) -> Callable:
        """Return the middleware function."""
        pass


class CustomMiddlewareRegistry:
    """Registry for custom middleware."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._middleware = []
        return cls._instance
    
    def add_middleware(self, middleware: Callable, position: str = "last") -> None:
        """
        Add custom middleware.
        
        Args:
            middleware: The middleware function (ASGI compatible)
            position: "first" or "last" - position in middleware stack
        """
        if position == "first":
            self._middleware.insert(0, middleware)
        else:
            self._middleware.append(middleware)
    
    def remove_middleware(self, middleware: Callable) -> None:
        """Remove a middleware."""
        if middleware in self._middleware:
            self._middleware.remove(middleware)
    
    def get_middleware(self) -> List[Callable]:
        """Get all registered middleware."""
        return self._middleware.copy()
    
    def clear(self) -> None:
        """Clear all middleware."""
        self._middleware.clear()


def get_middleware_registry() -> CustomMiddlewareRegistry:
    """Get the global middleware registry."""
    return CustomMiddlewareRegistry()


def add_custom_middleware(middleware: Callable, position: str = "last") -> None:
    """Add custom middleware to the global registry."""
    registry = get_middleware_registry()
    registry.add_middleware(middleware, position)


# ============================================================================
# Example: Custom Storage Plugin
# ============================================================================

class SQLiteStoragePlugin(StoragePlugin):
    """Example: SQLite storage plugin."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.db_path = self.config.get("db_path", "data.db")
        self._data = {}
    
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="sqlite_storage",
            version="1.0.0",
            author="GhostAPI",
            description="SQLite-based storage plugin"
        )
    
    def on_load(self, app: Any) -> None:
        print(f"SQLite storage plugin loaded with db: {self.db_path}")
    
    def on_unload(self) -> None:
        print("SQLite storage plugin unloaded")
    
    def get(self, key: str) -> Optional[Any]:
        return self._data.get(key)
    
    def set(self, key: str, value: Any) -> None:
        self._data[key] = value
    
    def delete(self, key: str) -> bool:
        if key in self._data:
            del self._data[key]
            return True
        return False
    
    def clear(self) -> None:
        self._data.clear()
    
    def get_all(self) -> Dict[str, Any]:
        return self._data.copy()


# ============================================================================
# Example: Custom Validation Plugin
# ============================================================================

class EmailValidationPlugin(ValidationPlugin):
    """Example: Email validation plugin."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
    
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="email_validation",
            version="1.0.0",
            author="GhostAPI",
            description="Email format validation plugin"
        )
    
    def on_load(self, app: Any) -> None:
        print("Email validation plugin loaded")
    
    def on_unload(self) -> None:
        print("Email validation plugin unloaded")
    
    def validate(self, value: Any) -> bool:
        if not isinstance(value, str):
            return False
        return "@" in value and "." in value.split("@")[-1]
    
    def get_error_message(self, field_name: str, value: Any) -> str:
        return f"Le champ '{field_name}' doit être une adresse email valide."


# ============================================================================
# Example: Custom Decorator Plugin
# ============================================================================

class RateLimitDecoratorPlugin(DecoratorPlugin):
    """Example: Rate limit decorator plugin."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.default_limit = self.config.get("default_limit", 100)
    
    def get_metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="rate_limit_decorator",
            version="1.0.0",
            author="GhostAPI",
            description="Rate limit decorator plugin"
        )
    
    def on_load(self, app: Any) -> None:
        print("Rate limit decorator plugin loaded")
    
    def on_unload(self) -> None:
        print("Rate limit decorator plugin unloaded")
    
    def create_decorator(self, max_calls: int = None, period: int = 60):
        """Create a rate limiting decorator."""
        limit = max_calls or self.default_limit
        
        def decorator(func: Callable) -> Callable:
            calls = []
            
            @wraps(func)
            def wrapper(*args, **kwargs):
                import time
                now = time.time()
                
                # Clean old calls
                calls[:] = [t for t in calls if now - t < period]
                
                if len(calls) >= limit:
                    raise Exception(f"Rate limit exceeded. Max {limit} calls per {period} seconds.")
                
                calls.append(now)
                return func(*args, **kwargs)
            
            return wrapper
        return decorator
