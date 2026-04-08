"""Tests for Plugin System features."""

import pytest

from ghostapi.plugins import (
    Plugin,
    PluginMetadata,
    StoragePlugin,
    ValidationPlugin,
    DecoratorPlugin,
    MiddlewarePlugin,
    PluginRegistry,
    CustomMiddlewareRegistry,
    get_plugin_registry,
    get_middleware_registry,
    register_plugin,
    add_custom_middleware,
    SQLiteStoragePlugin,
    EmailValidationPlugin,
    RateLimitDecoratorPlugin,
)


class TestPluginMetadata:
    """Tests for PluginMetadata dataclass."""
    
    def test_creation(self):
        """Test creating metadata."""
        metadata = PluginMetadata(
            name="test_plugin",
            version="1.0.0",
            author="Test Author",
            description="Test description"
        )
        
        assert metadata.name == "test_plugin"
        assert metadata.version == "1.0.0"
        assert metadata.author == "Test Author"
        assert metadata.description == "Test description"


class TestPluginRegistry:
    """Tests for PluginRegistry."""
    
    def test_singleton(self):
        """Test registry is a singleton."""
        registry1 = get_plugin_registry()
        registry2 = get_plugin_registry()
        
        assert registry1 is registry2
    
    def test_register_plugin(self):
        """Test registering a plugin."""
        class TestPlugin(Plugin):
            def get_metadata(self):
                return PluginMetadata("test", "1.0.0", "author")
            
            def on_load(self, app):
                pass
            
            def on_unload(self):
                pass
        
        registry = get_plugin_registry()
        plugin = TestPlugin()
        registry.register(plugin)
        
        assert registry.get_plugin("test") is plugin
    
    def test_unregister_plugin(self):
        """Test unregistering a plugin."""
        class TestPlugin(Plugin):
            def get_metadata(self):
                return PluginMetadata("test_unreg", "1.0.0", "author")
            
            def on_load(self, app):
                pass
            
            def on_unload(self):
                pass
        
        registry = get_plugin_registry()
        plugin = TestPlugin()
        registry.register(plugin)
        registry.unregister("test_unreg")
        
        assert registry.get_plugin("test_unreg") is None
    
    def test_list_plugins(self):
        """Test listing all plugins."""
        class TestPlugin1(Plugin):
            def get_metadata(self):
                return PluginMetadata("plugin1", "1.0.0", "author")
            
            def on_load(self, app):
                pass
            
            def on_unload(self):
                pass
        
        class TestPlugin2(Plugin):
            def get_metadata(self):
                return PluginMetadata("plugin2", "1.0.0", "author")
            
            def on_load(self, app):
                pass
            
            def on_unload(self):
                pass
        
        registry = get_plugin_registry()
        registry.register(TestPlugin1())
        registry.register(TestPlugin2())
        
        plugins = registry.list_plugins()
        assert len(plugins) >= 2
    
    def test_enable_disable_plugin(self):
        """Test enabling and disabling plugins."""
        class TestPlugin(Plugin):
            def get_metadata(self):
                return PluginMetadata("enable_test", "1.0.0", "author")
            
            def on_load(self, app):
                pass
            
            def on_unload(self):
                pass
        
        registry = get_plugin_registry()
        plugin = TestPlugin()
        registry.register(plugin)
        
        assert plugin.enabled is True
        registry.disable_plugin("enable_test")
        assert plugin.enabled is False
        registry.enable_plugin("enable_test")
        assert plugin.enabled is True


class TestStoragePlugin:
    """Tests for StoragePlugin."""
    
    def test_sqlite_storage_plugin(self):
        """Test SQLite storage plugin."""
        plugin = SQLiteStoragePlugin({"db_path": "test.db"})
        
        metadata = plugin.get_metadata()
        assert metadata.name == "sqlite_storage"
        
        plugin.on_load(None)
        
        # Test operations
        plugin.set("key1", "value1")
        assert plugin.get("key1") == "value1"
        assert plugin.get("nonexistent") is None
        
        plugin.delete("key1")
        assert plugin.get("key1") is None
        
        plugin.set("key2", "value2")
        plugin.clear()
        assert plugin.get_all() == {}
        
        plugin.on_unload()


class TestValidationPlugin:
    """Tests for ValidationPlugin."""
    
    def test_email_validation_plugin(self):
        """Test email validation plugin."""
        plugin = EmailValidationPlugin()
        
        metadata = plugin.get_metadata()
        assert metadata.name == "email_validation"
        
        plugin.on_load(None)
        
        # Test validation
        assert plugin.validate("test@example.com") is True
        assert plugin.validate("invalid") is False
        assert plugin.validate("no@domain") is False
        assert plugin.validate(123) is False
        
        # Test error message
        msg = plugin.get_error_message("email", "invalid")
        assert "email" in msg.lower()
        
        plugin.on_unload()


class TestDecoratorPlugin:
    """Tests for DecoratorPlugin."""
    
    def test_rate_limit_decorator(self):
        """Test rate limit decorator plugin."""
        plugin = RateLimitDecoratorPlugin({"default_limit": 3})
        
        metadata = plugin.get_metadata()
        assert metadata.name == "rate_limit_decorator"
        
        plugin.on_load(None)
        
        # Create decorator
        decorator = plugin.create_decorator(max_calls=2, period=60)
        
        call_count = 0
        
        @decorator
        def test_func():
            nonlocal call_count
            call_count += 1
            return "ok"
        
        # Should work
        assert test_func() == "ok"
        assert test_func() == "ok"
        
        # Third call should raise
        with pytest.raises(Exception) as exc_info:
            test_func()
        
        assert "Rate limit exceeded" in str(exc_info.value)
        
        plugin.on_unload()


class TestCustomMiddlewareRegistry:
    """Tests for CustomMiddlewareRegistry."""
    
    def test_singleton(self):
        """Test middleware registry is singleton."""
        registry1 = get_middleware_registry()
        registry2 = get_middleware_registry()
        
        assert registry1 is registry2
    
    def test_add_middleware(self):
        """Test adding middleware."""
        registry = get_middleware_registry()
        
        def middleware1(scope, receive, send):
            pass
        
        def middleware2(scope, receive, send):
            pass
        
        registry.add_middleware(middleware1, position="last")
        registry.add_middleware(middleware2, position="first")
        
        middleware = registry.get_middleware()
        assert middleware2 in middleware
        assert middleware1 in middleware
    
    def test_remove_middleware(self):
        """Test removing middleware."""
        registry = get_middleware_registry()
        
        def test_middleware(scope, receive, send):
            pass
        
        registry.add_middleware(test_middleware)
        assert test_middleware in registry.get_middleware()
        
        registry.remove_middleware(test_middleware)
        assert test_middleware not in registry.get_middleware()
    
    def test_clear_middleware(self):
        """Test clearing all middleware."""
        registry = get_middleware_registry()
        
        def m1(scope, receive, send):
            pass
        
        def m2(scope, receive, send):
            pass
        
        registry.add_middleware(m1)
        registry.add_middleware(m2)
        registry.clear()
        
        assert len(registry.get_middleware()) == 0


class TestHelperFunctions:
    """Tests for helper functions."""
    
    def test_register_plugin_helper(self):
        """Test register_plugin helper."""
        class HelperTestPlugin(Plugin):
            def get_metadata(self):
                return PluginMetadata("helper_test", "1.0.0", "author")
            
            def on_load(self, app):
                pass
            
            def on_unload(self):
                pass
        
        plugin = HelperTestPlugin()
        register_plugin(plugin)
        
        registry = get_plugin_registry()
        assert registry.get_plugin("helper_test") is plugin
    
    def test_add_custom_middleware_helper(self):
        """Test add_custom_middleware helper."""
        def test_middleware(scope, receive, send):
            pass
        
        add_custom_middleware(test_middleware)
        
        registry = get_middleware_registry()
        assert test_middleware in registry.get_middleware()


class TestPluginCategories:
    """Tests for plugin category registration."""
    
    def test_storage_plugin_registration(self):
        """Test storage plugin is registered in correct category."""
        registry = get_plugin_registry()
        plugin = SQLiteStoragePlugin()
        registry.register(plugin)
        
        assert registry.get_storage_plugin("sqlite_storage") is plugin
    
    def test_validation_plugin_registration(self):
        """Test validation plugin is registered in correct category."""
        registry = get_plugin_registry()
        plugin = EmailValidationPlugin()
        registry.register(plugin)
        
        assert registry.get_validation_plugin("email_validation") is plugin
    
    def test_decorator_plugin_registration(self):
        """Test decorator plugin is registered in correct category."""
        registry = get_plugin_registry()
        plugin = RateLimitDecoratorPlugin()
        registry.register(plugin)
        
        assert registry.get_decorator_plugin("rate_limit_decorator") is plugin
