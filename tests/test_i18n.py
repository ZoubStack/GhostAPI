"""Tests for Internationalization (i18n) features."""

import pytest

from ghostapi.i18n import (
    Language,
    I18nManager,
    I18nMiddleware,
    get_i18n_manager,
    set_language,
    get_error_message,
    get_docstring,
    field_required,
    invalid_type,
    invalid_email,
    invalid_credentials,
    access_denied,
    role_required,
    rate_limit_exceeded,
    translated_docstring,
)


class TestLanguage:
    """Tests for Language enum."""
    
    def test_language_values(self):
        """Test language enum values."""
        assert Language.FRENCH.value == "fr"
        assert Language.ENGLISH.value == "en"
        assert Language.SPANISH.value == "es"
        assert Language.DEFAULT == Language.ENGLISH


class TestI18nManager:
    """Tests for I18nManager."""
    
    def test_singleton(self):
        """Test manager is singleton."""
        manager1 = get_i18n_manager()
        manager2 = get_i18n_manager()
        assert manager1 is manager2
    
    def test_set_language(self):
        """Test setting language."""
        manager = get_i18n_manager()
        manager.set_language(Language.FRENCH)
        assert manager.current_language == Language.FRENCH
    
    def test_detect_language_french(self):
        """Test detecting French language."""
        manager = get_i18n_manager()
        
        assert manager.detect_language("fr") == Language.FRENCH
        assert manager.detect_language("fr-FR") == Language.FRENCH
        assert manager.detect_language("fr-CA") == Language.FRENCH
    
    def test_detect_language_english(self):
        """Test detecting English language."""
        manager = get_i18n_manager()
        
        assert manager.detect_language("en") == Language.ENGLISH
        assert manager.detect_language("en-US") == Language.ENGLISH
        assert manager.detect_language("en-GB") == Language.ENGLISH
    
    def test_detect_language_spanish(self):
        """Test detecting Spanish language."""
        manager = get_i18n_manager()
        
        assert manager.detect_language("es") == Language.SPANISH
        assert manager.detect_language("es-ES") == Language.SPANISH
        assert manager.detect_language("es-MX") == Language.SPANISH
    
    def test_detect_language_with_quality(self):
        """Test detecting language with quality values."""
        manager = get_i18n_manager()
        
        assert manager.detect_language("fr;q=0.9, en;q=0.8") == Language.FRENCH
        assert manager.detect_language("es-ES;q=0.5, fr;q=0.9") == Language.FRENCH
    
    def test_detect_language_unknown(self):
        """Test detecting unknown language falls back."""
        manager = get_i18n_manager()
        
        assert manager.detect_language("de") == Language.DEFAULT
        assert manager.detect_language("zh") == Language.DEFAULT
        assert manager.detect_language(None) == Language.DEFAULT
    
    def test_get_error_message_french(self):
        """Test getting error message in French."""
        manager = get_i18n_manager()
        manager.set_language(Language.FRENCH)
        
        msg = manager.get_error_message("field_required", field="email")
        assert "email" in msg
        assert "requis" in msg
    
    def test_get_error_message_english(self):
        """Test getting error message in English."""
        manager = get_i18n_manager()
        manager.set_language(Language.ENGLISH)
        
        msg = manager.get_error_message("field_required", field="email")
        assert "email" in msg
        assert "required" in msg
    
    def test_get_error_message_spanish(self):
        """Test getting error message in Spanish."""
        manager = get_i18n_manager()
        manager.set_language(Language.SPANISH)
        
        msg = manager.get_error_message("field_required", field="email")
        assert "email" in msg
        assert "requerido" in msg
    
    def test_get_docstring_french(self):
        """Test getting docstring in French."""
        manager = get_i18n_manager()
        manager.set_language(Language.FRENCH)
        
        doc = manager.get_docstring("Authentication")
        assert "Authentification" in doc
    
    def test_get_docstring_english(self):
        """Test getting docstring in English."""
        manager = get_i18n_manager()
        manager.set_language(Language.ENGLISH)
        
        doc = manager.get_docstring("Authentication")
        assert "Authentication" in doc
    
    def test_get_docstring_spanish(self):
        """Test getting docstring in Spanish."""
        manager = get_i18n_manager()
        manager.set_language(Language.SPANISH)
        
        doc = manager.get_docstring("Authentication")
        assert "Autenticación" in doc
    
    def test_custom_message(self):
        """Test adding custom message."""
        manager = get_i18n_manager()
        manager.set_language(Language.FRENCH)
        
        manager.add_custom_message(Language.FRENCH, "custom_key", "Message personnalisé")
        
        msg = manager.get_error_message("custom_key")
        assert msg == "Message personnalisé"
    
    def test_supported_languages(self):
        """Test getting supported languages."""
        manager = get_i18n_manager()
        
        languages = manager.get_supported_languages()
        
        assert "fr" in languages
        assert "en" in languages
        assert "es" in languages
        assert languages["fr"] == "Français"
        assert languages["en"] == "English"
        assert languages["es"] == "Español"


class TestHelperFunctions:
    """Tests for helper functions."""
    
    def test_set_language(self):
        """Test set_language helper."""
        set_language(Language.SPANISH)
        assert get_i18n_manager().current_language == Language.SPANISH
    
    def test_get_error_message_helper(self):
        """Test get_error_message helper."""
        get_i18n_manager().set_language(Language.ENGLISH)
        
        msg = get_error_message("invalid_credentials")
        assert "email" in msg.lower() or "password" in msg.lower()
    
    def test_get_docstring_helper(self):
        """Test get_docstring helper."""
        get_i18n_manager().set_language(Language.FRENCH)
        
        doc = get_docstring("Login")
        assert "Connexion" in doc
    
    def test_field_required(self):
        """Test field_required helper."""
        get_i18n_manager().set_language(Language.FRENCH)
        
        msg = field_required("name")
        assert "name" in msg
        assert "requis" in msg
    
    def test_invalid_type(self):
        """Test invalid_type helper."""
        get_i18n_manager().set_language(Language.ENGLISH)
        
        msg = invalid_type("age", "int", "str")
        assert "age" in msg
        assert "int" in msg
        assert "str" in msg
    
    def test_invalid_email(self):
        """Test invalid_email helper."""
        get_i18n_manager().set_language(Language.FRENCH)
        
        msg = invalid_email("email")
        assert "email" in msg
        assert "valide" in msg
    
    def test_invalid_credentials(self):
        """Test invalid_credentials helper."""
        get_i18n_manager().set_language(Language.ENGLISH)
        
        msg = invalid_credentials()
        assert "invalid" in msg.lower() or "password" in msg.lower()
    
    def test_access_denied(self):
        """Test access_denied helper."""
        get_i18n_manager().set_language(Language.ENGLISH)
        
        msg = access_denied()
        assert "access" in msg.lower() or "denied" in msg.lower()
    
    def test_role_required(self):
        """Test role_required helper."""
        get_i18n_manager().set_language(Language.FRENCH)
        
        msg = role_required("admin")
        assert "admin" in msg
        assert "rôle" in msg.lower() or "role" in msg.lower()
    
    def test_rate_limit_exceeded(self):
        """Test rate_limit_exceeded helper."""
        get_i18n_manager().set_language(Language.ENGLISH)
        
        msg = rate_limit_exceeded()
        assert "rate" in msg.lower() or "limit" in msg.lower()


class TestTranslatedDocstring:
    """Tests for translated_docstring decorator."""
    
    def test_decorator(self):
        """Test decorator translates docstring."""
        get_i18n_manager().set_language(Language.FRENCH)
        
        @translated_docstring("Login")
        def my_function():
            '''Original docstring'''
            pass
        
        # Should be translated
        assert my_function.__doc__ == "Connexion"
    
    def test_decorator_english(self):
        """Test decorator with English."""
        get_i18n_manager().set_language(Language.ENGLISH)
        
        @translated_docstring("Login")
        def my_function():
            '''Original'''
            pass
        
        assert my_function.__doc__ == "Login"


class TestI18nMiddleware:
    """Tests for I18nMiddleware."""
    
    def test_initialization(self):
        """Test middleware initialization."""
        app = None  # Mock app
        middleware = I18nMiddleware(app)
        
        assert middleware.app is app
        assert middleware.fallback_language == Language.DEFAULT
    
    def test_initialization_custom_fallback(self):
        """Test middleware with custom fallback."""
        app = None
        middleware = I18nMiddleware(app, fallback_language=Language.SPANISH)
        
        assert middleware.fallback_language == Language.SPANISH
    
    def test_non_http_scope(self):
        """Test middleware with non-HTTP scope."""
        async def mock_app(scope, receive, send):
            pass
        
        middleware = I18nMiddleware(mock_app)
        
        # WebSocket scope (not http) - just test initialization doesn't raise
        assert middleware.app is mock_app


class TestErrorMessageKeys:
    """Test that all error message keys work."""
    
    def test_all_validation_keys(self):
        """Test all validation error keys."""
        manager = get_i18n_manager()
        
        keys = [
            "field_required", "invalid_type", "invalid_value",
            "value_too_short", "value_too_long", "invalid_email",
            "invalid_url", "invalid_number", "number_too_small",
            "number_too_large", "invalid_choice", "invalid_format"
        ]
        
        for lang in [Language.FRENCH, Language.ENGLISH, Language.SPANISH]:
            manager.set_language(lang)
            for key in keys:
                msg = manager.get_error_message(key, field="test", value="1", 
                                               expected="str", received="int",
                                               min=1, max=10, choices="a,b,c")
                assert msg
                assert isinstance(msg, str)
    
    def test_all_auth_keys(self):
        """Test all auth error keys."""
        manager = get_i18n_manager()
        
        keys = [
            "invalid_credentials", "user_not_found", "user_already_exists",
            "token_expired", "token_invalid", "access_denied", "role_required"
        ]
        
        for lang in [Language.FRENCH, Language.ENGLISH, Language.SPANISH]:
            manager.set_language(lang)
            for key in keys:
                msg = manager.get_error_message(key, role="admin")
                assert msg
                assert isinstance(msg, str)
    
    def test_all_general_keys(self):
        """Test all general error keys."""
        manager = get_i18n_manager()
        
        keys = ["not_found", "method_not_allowed", "internal_error", 
                "bad_request", "service_unavailable", "rate_limit_exceeded"]
        
        for lang in [Language.FRENCH, Language.ENGLISH, Language.SPANISH]:
            manager.set_language(lang)
            for key in keys:
                msg = manager.get_error_message(key)
                assert msg
                assert isinstance(msg, str)
