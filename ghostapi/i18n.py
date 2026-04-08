"""
Internationalization (i18n) for GhostAPI

Support multi-language for error messages and Swagger docstrings.
Languages: French, English, Spanish (automatically based on Accept-Language header).
"""

from typing import Dict, Optional, Any, Callable
from dataclasses import dataclass
from enum import Enum
import re


class Language(Enum):
    """Supported languages."""
    FRENCH = "fr"
    ENGLISH = "en"
    SPANISH = "es"
    DEFAULT = ENGLISH


# =============================================================================
# Translation Dictionaries
# =============================================================================

ERROR_MESSAGES = {
    Language.FRENCH: {
        # Validation errors
        "field_required": "Le champ '{field}' est requis.",
        "invalid_type": "Le champ '{field}' doit être de type {expected}, reçu : {received}",
        "invalid_value": "La valeur '{value}' n'est pas valide pour le champ '{field}'.",
        "value_too_short": "Le champ '{field}' doit contenir au moins {min} caractères.",
        "value_too_long": "Le champ '{field}' doit contenir au plus {max} caractères.",
        "invalid_email": "Le champ '{field}' doit être une adresse email valide.",
        "invalid_url": "Le champ '{field}' doit être une URL valide.",
        "invalid_number": "Le champ '{field}' doit être un nombre valide.",
        "number_too_small": "Le champ '{field}' doit être au moins {min}.",
        "number_too_large": "Le champ '{field}' doit être au plus {max}.",
        "invalid_choice": "Le champ '{field}' doit être l'une des valeurs suivantes: {choices}.",
        "invalid_format": "Le format du champ '{field}' est invalide.",
        
        # Auth errors
        "invalid_credentials": "Email ou mot de passe invalide.",
        "user_not_found": "Utilisateur non trouvé.",
        "user_already_exists": "Un utilisateur avec cet email existe déjà.",
        "token_expired": "Le token a expiré.",
        "token_invalid": "Token invalide.",
        "access_denied": "Accès refusé. Permissions insuffisantes.",
        "role_required": "Le rôle '{role}' est requis pour accéder à cette ressource.",
        
        # Rate limiting
        "rate_limit_exceeded": "Limite de requêtes dépassée. Veuillez réessayer plus tard.",
        
        # General errors
        "not_found": "Ressource non trouvée.",
        "method_not_allowed": "Méthode non autorisée.",
        "internal_error": "Erreur interne du serveur.",
        "bad_request": "Requête invalide.",
        "service_unavailable": "Service temporairement indisponible.",
    },
    
    Language.ENGLISH: {
        # Validation errors
        "field_required": "Field '{field}' is required.",
        "invalid_type": "Field '{field}' must be of type {expected}, received: {received}",
        "invalid_value": "Value '{value}' is not valid for field '{field}'.",
        "value_too_short": "Field '{field}' must contain at least {min} characters.",
        "value_too_long": "Field '{field}' must contain at most {max} characters.",
        "invalid_email": "Field '{field}' must be a valid email address.",
        "invalid_url": "Field '{field}' must be a valid URL.",
        "invalid_number": "Field '{field}' must be a valid number.",
        "number_too_small": "Field '{field}' must be at least {min}.",
        "number_too_large": "Field '{field}' must be at most {max}.",
        "invalid_choice": "Field '{field}' must be one of: {choices}.",
        "invalid_format": "Field '{field}' has an invalid format.",
        
        # Auth errors
        "invalid_credentials": "Invalid email or password.",
        "user_not_found": "User not found.",
        "user_already_exists": "A user with this email already exists.",
        "token_expired": "Token has expired.",
        "token_invalid": "Invalid token.",
        "access_denied": "Access denied. Insufficient permissions.",
        "role_required": "Role '{role}' is required to access this resource.",
        
        # Rate limiting
        "rate_limit_exceeded": "Rate limit exceeded. Please try again later.",
        
        # General errors
        "not_found": "Resource not found.",
        "method_not_allowed": "Method not allowed.",
        "internal_error": "Internal server error.",
        "bad_request": "Bad request.",
        "service_unavailable": "Service temporarily unavailable.",
    },
    
    Language.SPANISH: {
        # Validation errors
        "field_required": "El campo '{field}' es requerido.",
        "invalid_type": "El campo '{field}' debe ser de tipo {expected}, recibido: {received}",
        "invalid_value": "El valor '{value}' no es válido para el campo '{field}'.",
        "value_too_short": "El campo '{field}' debe contener al menos {min} caracteres.",
        "value_too_long": "El campo '{field}' debe contener como máximo {max} caracteres.",
        "invalid_email": "El campo '{field}' debe ser una dirección de correo válida.",
        "invalid_url": "El campo '{field}' debe ser una URL válida.",
        "invalid_number": "El campo '{field}' debe ser un número válido.",
        "number_too_small": "El campo '{field}' debe ser al menos {min}.",
        "number_too_large": "El campo '{field}' debe ser como máximo {max}.",
        "invalid_choice": "El campo '{field}' debe ser uno de: {choices}.",
        "invalid_format": "El campo '{field}' tiene un formato inválido.",
        
        # Auth errors
        "invalid_credentials": "Email o contraseña inválidos.",
        "user_not_found": "Usuario no encontrado.",
        "user_already_exists": "Ya existe un usuario con este email.",
        "token_expired": "El token ha expirado.",
        "token_invalid": "Token inválido.",
        "access_denied": "Acceso denegado. Permisos insuficientes.",
        "role_required": "El rol '{role}' es requerido para acceder a este recurso.",
        
        # Rate limiting
        "rate_limit_exceeded": "Límite de solicitudes excedido. Por favor intente más tarde.",
        
        # General errors
        "not_found": "Recurso no encontrado.",
        "method_not_allowed": "Método no permitido.",
        "internal_error": "Error interno del servidor.",
        "bad_request": "Solicitud incorrecta.",
        "service_unavailable": "Servicio temporalmente no disponible.",
    },
}


# =============================================================================
# Docstrings Translations (for Swagger)
# =============================================================================

DOCSTRINGS = {
    Language.FRENCH: {
        "Authentication": "Authentification",
        "Login": "Connexion",
        "Register": "Inscription",
        "Logout": "Déconnexion",
        "Get Current User": "Obtenir l'utilisateur actuel",
        "Protected Endpoint": "Endpoint protégé",
        "Admin Only": "Administrateur uniquement",
        "Create": "Créer",
        "Read": "Lire",
        "Update": "Mettre à jour",
        "Delete": "Supprimer",
        "List": "Lister",
        "Search": "Rechercher",
        "Filter": "Filtrer",
        "Sort": "Trier",
        "Pagination": "Pagination",
        "Success": "Succès",
        "Error": "Erreur",
        "Warning": "Avertissement",
        "Info": "Information",
        "Required": "Requis",
        "Optional": "Optionnel",
        "Default": "Par défaut",
        "Example": "Exemple",
        "Parameters": "Paramètres",
        "Returns": "Retourne",
        "Raises": "Lève",
        "Description": "Description",
        "Summary": "Résumé",
    },
    
    Language.ENGLISH: {
        "Authentication": "Authentication",
        "Login": "Login",
        "Register": "Register",
        "Logout": "Logout",
        "Get Current User": "Get Current User",
        "Protected Endpoint": "Protected Endpoint",
        "Admin Only": "Admin Only",
        "Create": "Create",
        "Read": "Read",
        "Update": "Update",
        "Delete": "Delete",
        "List": "List",
        "Search": "Search",
        "Filter": "Filter",
        "Sort": "Sort",
        "Pagination": "Pagination",
        "Success": "Success",
        "Error": "Error",
        "Warning": "Warning",
        "Info": "Information",
        "Required": "Required",
        "Optional": "Optional",
        "Default": "Default",
        "Example": "Example",
        "Parameters": "Parameters",
        "Returns": "Returns",
        "Raises": "Raises",
        "Description": "Description",
        "Summary": "Summary",
    },
    
    Language.SPANISH: {
        "Authentication": "Autenticación",
        "Login": "Iniciar sesión",
        "Register": "Registrarse",
        "Logout": "Cerrar sesión",
        "Get Current User": "Obtener usuario actual",
        "Protected Endpoint": "Endpoint protegido",
        "Admin Only": "Solo administrador",
        "Create": "Crear",
        "Read": "Leer",
        "Update": "Actualizar",
        "Delete": "Eliminar",
        "List": "Listar",
        "Search": "Buscar",
        "Filter": "Filtrar",
        "Sort": "Ordenar",
        "Pagination": "Paginación",
        "Success": "Éxito",
        "Error": "Error",
        "Warning": "Advertencia",
        "Info": "Información",
        "Required": "Requerido",
        "Optional": "Opcional",
        "Default": "Por defecto",
        "Example": "Ejemplo",
        "Parameters": "Parámetros",
        "Returns": "Retorna",
        "Raises": "Lanza",
        "Description": "Descripción",
        "Summary": "Resumen",
    },
}


# =============================================================================
# i18n Manager
# =============================================================================

class I18nManager:
    """Manager for internationalization."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._current_language = Language.DEFAULT
            cls._instance._fallback_language = Language.DEFAULT
            cls._instance._custom_messages = {}
        return cls._instance
    
    @property
    def current_language(self) -> Language:
        return self._current_language
    
    @current_language.setter
    def current_language(self, lang: Language) -> None:
        self._current_language = lang
    
    @property
    def fallback_language(self) -> Language:
        return self._fallback_language
    
    @fallback_language.setter
    def fallback_language(self, lang: Language) -> None:
        self._fallback_language = lang
    
    def set_language(self, lang: Language) -> None:
        """Set the current language."""
        self._current_language = lang
    
    def detect_language(self, accept_language: Optional[str]) -> Language:
        """
        Detect language from Accept-Language header.
        
        Args:
            accept_language: Value of Accept-Language header
            
        Returns:
            Detected Language enum value
        """
        if not accept_language:
            return self._fallback_language
        
        # Parse Accept-Language header
        languages = []
        for part in accept_language.split(","):
            part = part.strip().lower()
            # Handle quality value (e.g., "en-US;q=0.9")
            if ";q=" in part:
                lang_code, quality = part.split(";q=")
                try:
                    quality = float(quality)
                except ValueError:
                    quality = 1.0
                languages.append((lang_code.strip(), quality))
            else:
                languages.append((part, 1.0))
        
        # Sort by quality (highest first)
        languages.sort(key=lambda x: x[1], reverse=True)
        
        # Map language codes to Language enum
        code_mapping = {
            "fr": Language.FRENCH,
            "fr-fr": Language.FRENCH,
            "fr-ca": Language.FRENCH,
            "en": Language.ENGLISH,
            "en-us": Language.ENGLISH,
            "en-gb": Language.ENGLISH,
            "es": Language.SPANISH,
            "es-es": Language.SPANISH,
            "es-mx": Language.SPANISH,
        }
        
        for code, _ in languages:
            if code in code_mapping:
                return code_mapping[code]
        
        return self._fallback_language
    
    def get_error_message(self, key: str, **kwargs) -> str:
        """
        Get translated error message.
        
        Args:
            key: Message key
            **kwargs: Format parameters
            
        Returns:
            Translated error message
        """
        # Check custom messages first
        if key in self._custom_messages.get(self._current_language, {}):
            message = self._custom_messages[self._current_language][key]
        elif key in ERROR_MESSAGES.get(self._current_language, {}):
            message = ERROR_MESSAGES[self._current_language][key]
        elif key in ERROR_MESSAGES.get(self._fallback_language, {}):
            message = ERROR_MESSAGES[self._fallback_language][key]
        else:
            # Fallback to English
            message = ERROR_MESSAGES[Language.ENGLISH].get(key, key)
        
        # Format message with kwargs
        try:
            return message.format(**kwargs)
        except KeyError:
            return message
    
    def get_docstring(self, key: str) -> str:
        """
        Get translated docstring for Swagger.
        
        Args:
            key: Docstring key
            
        Returns:
            Translated docstring
        """
        # Check current language
        if key in DOCSTRINGS.get(self._current_language, {}):
            return DOCSTRINGS[self._current_language][key]
        
        # Check fallback
        if key in DOCSTRINGS.get(self._fallback_language, {}):
            return DOCSTRINGS[self._fallback_language][key]
        
        # Fallback to English
        return DOCSTRINGS[Language.ENGLISH].get(key, key)
    
    def add_custom_message(self, lang: Language, key: str, message: str) -> None:
        """
        Add custom translation message.
        
        Args:
            lang: Language
            key: Message key
            message: Translated message
        """
        if lang not in self._custom_messages:
            self._custom_messages[lang] = {}
        self._custom_messages[lang][key] = message
    
    def get_supported_languages(self) -> Dict[str, str]:
        """Get list of supported languages."""
        return {
            "fr": "Français",
            "en": "English",
            "es": "Español",
        }


def get_i18n_manager() -> I18nManager:
    """Get the global i18n manager."""
    return I18nManager()


def set_language(lang: Language) -> None:
    """Set the current language globally."""
    manager = get_i18n_manager()
    manager.set_language(lang)


def get_error_message(key: str, **kwargs) -> str:
    """Get translated error message."""
    return get_i18n_manager().get_error_message(key, **kwargs)


def get_docstring(key: str) -> str:
    """Get translated docstring."""
    return get_i18n_manager().get_docstring(key)


# =============================================================================
# Middleware for Language Detection
# =============================================================================

class I18nMiddleware:
    """Middleware to detect and set language from request."""
    
    def __init__(self, app, fallback_language: Language = Language.DEFAULT):
        self.app = app
        self.fallback_language = fallback_language
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        # Get Accept-Language header
        headers = dict(scope.get("headers", []))
        accept_language = None
        
        for key, value in headers:
            if key == b"accept-language":
                accept_language = value.decode("utf-8")
                break
        
        # Detect and set language
        manager = get_i18n_manager()
        detected_lang = manager.detect_language(accept_language)
        manager.set_language(detected_lang)
        
        # Continue to app
        await self.app(scope, receive, send)


# =============================================================================
# Decorator for Translated Docstrings
# =============================================================================

def translated_docstring(key: str):
    """
    Decorator to translate function docstrings for Swagger.
    
    Usage:
        @translated_docstring("Description")
        def my_function():
            '''This will be translated'''
            pass
    """
    def decorator(func: Callable) -> Callable:
        translated = get_docstring(key)
        func.__doc__ = translated
        return func
    return decorator


# =============================================================================
# Helper Functions for Common Error Messages
# =============================================================================

def field_required(field: str) -> str:
    """Get 'field required' error message."""
    return get_error_message("field_required", field=field)


def invalid_type(field: str, expected: str, received: str) -> str:
    """Get 'invalid type' error message."""
    return get_error_message("invalid_type", field=field, expected=expected, received=received)


def invalid_email(field: str) -> str:
    """Get 'invalid email' error message."""
    return get_error_message("invalid_email", field=field)


def invalid_credentials() -> str:
    """Get 'invalid credentials' error message."""
    return get_error_message("invalid_credentials")


def access_denied() -> str:
    """Get 'access denied' error message."""
    return get_error_message("access_denied")


def role_required(role: str) -> str:
    """Get 'role required' error message."""
    return get_error_message("role_required", role=role)


def rate_limit_exceeded() -> str:
    """Get 'rate limit exceeded' error message."""
    return get_error_message("rate_limit_exceeded")
