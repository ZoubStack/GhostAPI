"""Router for mapping Python functions to FastAPI routes."""

import inspect
from typing import Any, Callable, Dict, List, Optional, Union

from fastapi import APIRouter, Request, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, create_model, ValidationError

from ghostapi.wrapper import wrap_function


# Supported types for automatic model creation
SUPPORTED_TYPES = {
    str, int, float, bool, list, dict,
}


class RouteMapper:
    """
    Maps Python functions to FastAPI routes.
    
    Determines:
    - HTTP method (GET, POST, PUT, DELETE, PATCH)
    - Route path
    - Request model (for POST/PUT/PATCH)
    - Response model
    """
    
    # HTTP method mapping based on function prefix
    METHOD_MAP = {
        "get": "GET",
        "create": "POST",
        "update": "PUT",
        "delete": "DELETE",
        "patch": "PATCH",
    }
    
    # Type to Pydantic mapping for better error messages
    TYPE_ERROR_MESSAGES = {
        str: "une chaîne de caractères",
        int: "un entier",
        float: "un nombre décimal",
        bool: "un booléen (true/false)",
        list: "une liste",
        dict: "un objet JSON",
    }
    
    def __init__(self, router: Optional[APIRouter] = None) -> None:
        """
        Initialize the route mapper.
        
        Args:
            router: FastAPI router to use. Creates new one if None.
        """
        self.router = router or APIRouter()
        self._routes: List[Dict[str, Any]] = []
    
    def _get_http_method(self, func_name: str) -> str:
        """
        Determine HTTP method from function name.
        
        Args:
            func_name: The function name.
        
        Returns:
            HTTP method.
        """
        name_lower = func_name.lower()
        
        for prefix, method in self.METHOD_MAP.items():
            if name_lower.startswith(prefix + "_"):
                return method
        
        # Default to GET
        return "GET"
    
    def _get_route_path(self, func_name: str) -> str:
        """
        Convert function name to route path.
        
        Args:
            func_name: The function name.
        
        Returns:
            Route path.
        """
        name_lower = func_name.lower()
        
        # Remove known prefixes
        for prefix in self.METHOD_MAP.keys():
            if name_lower.startswith(prefix + "_"):
                func_name = func_name[len(prefix) + 1:]
                break
        
        # Convert to kebab-case
        path = func_name.replace("_", "-")
        
        return f"/{path}"
    
    def _create_request_model(
        self,
        func: Callable,
        func_name: str
    ) -> Optional[type[BaseModel]]:
        """
        Create a Pydantic model from function parameters.
        
        Args:
            func: The function.
            func_name: The function name.
        
        Returns:
            Pydantic model or None if no parameters.
        """
        sig = inspect.signature(func)
        params = sig.parameters
        
        if not params:
            return None
        
        # Build field definitions
        fields = {}
        unsupported_types = []
        
        for name, param in params.items():
            if name in ("request", "self"):
                continue
            
            # Get type
            param_type = Any
            if param.annotation != inspect.Parameter.empty:
                # Check if type is supported
                origin = getattr(param.annotation, "__origin__", None)
                if origin is not None:
                    # Handle generic types like Optional, List, Union
                    param_type = param.annotation
                elif param.annotation in SUPPORTED_TYPES:
                    param_type = param.annotation
                elif param.annotation not in SUPPORTED_TYPES:
                    # Collect unsupported types for error message
                    unsupported_types.append((name, param.annotation))
                    continue
            
            # Get default
            default = ...
            if param.default != inspect.Parameter.empty:
                default = param.default
            
            fields[name] = (param_type, default)
        
        if unsupported_types:
            # Create error message for unsupported types
            type_msgs = []
            for param_name, param_type in unsupported_types:
                type_name = getattr(param_type, "__name__", str(param_type))
                type_msgs.append(f"  - {param_name}: {type_name}")
            
            error_detail = (
                f"Type(s) Python non supporté(s) pour la génération automatique du modèle "
                f"de la fonction '{func_name}':\n" + "\n".join(type_msgs) +
                f"\n\nTypes supportés: str, int, float, bool, list, dict, Optional[T], List[T], Union[T, ...]\n"
                f"\nPour utiliser ce type, utilisez un Pydantic model explicite:\n"
                f"\nclass {func_name.title().replace('_', '')}Request(BaseModel):\n"
                f"    {param_name}: {type_name}\n"
                f"\ndef {func_name}(data: {func_name.title().replace('_', '')}Request):\n"
                f"    return data.dict()"
            )
            
            # Store error in function for later raising
            func._unsupported_types_error = error_detail
        
        if not fields:
            return None
        
        # Create model
        model_name = f"{func_name.title().replace('_', '')}Request"
        return create_model(model_name, **fields)
    
    def _create_response_model(
        self,
        func: Callable
    ) -> Optional[type[BaseModel]]:
        """
        Create a Pydantic model from function return type.
        
        Args:
            func: The function.
        
        Returns:
            Pydantic model or None.
        """
        # Try to get return type
        try:
            hints = inspect.getannotations(func)
            return_type = hints.get("return")
        except Exception:
            return_type = None
        
        if return_type is None:
            sig = inspect.signature(func)
            if sig.return_annotation != inspect.Signature.empty:
                return_type = sig.return_annotation
        
        if return_type is None or return_type == inspect.Signature.empty:
            return None
        
        # For simple types, return as-is
        if return_type in (str, int, float, bool, list, dict):
            return None
        
        # For list types, create a generic response
        if hasattr(return_type, "__origin__"):
            if return_type.__origin__ is list:
                # Get inner type
                args = getattr(return_type, "__args__", ())
                if args:
                    inner = args[0]
                    # Create a list model
                    return create_model(
                        f"ListResponse",
                        __annotations__={"items": return_type}
                    )
        
        # For other types, use directly
        return return_type
    
    def add_function(
        self,
        func: Callable,
        auth_required: bool = False,
        required_role: Optional[str] = None
    ) -> None:
        """
        Add a function as a route.
        
        Args:
            func: The function to expose.
            auth_required: Whether authentication is required.
            required_role: Required role for access (if auth enabled).
        """
        func_name = func.__name__
        http_method = self._get_http_method(func_name)
        route_path = self._get_route_path(func_name)
        
        # Create request model
        request_model = self._create_request_model(func, func_name)
        
        # Create response model
        response_model = self._create_response_model(func)
        
        # Create wrapped endpoint
        endpoint = wrap_function(
            func,
            request_model=request_model,
            auth_required=auth_required,
            required_role=required_role
        )
        
        # Determine endpoint kwargs
        endpoint_kwargs = {}
        if response_model:
            endpoint_kwargs["response_model"] = response_model
        
        # Add route to router
        if http_method == "GET":
            self.router.get(route_path, **endpoint_kwargs)(endpoint)
        elif http_method == "POST":
            self.router.post(route_path, **endpoint_kwargs)(endpoint)
        elif http_method == "PUT":
            self.router.put(route_path, **endpoint_kwargs)(endpoint)
        elif http_method == "DELETE":
            self.router.delete(route_path, **endpoint_kwargs)(endpoint)
        elif http_method == "PATCH":
            self.router.patch(route_path, **endpoint_kwargs)(endpoint)
        
        # Store route info
        self._routes.append({
            "function": func_name,
            "method": http_method,
            "path": route_path,
            "auth_required": auth_required,
            "role": required_role
        })
    
    def add_functions(
        self,
        functions: Dict[str, Callable],
        auth_required: bool = False
    ) -> None:
        """
        Add multiple functions as routes.
        
        Args:
            functions: Dictionary of function name to function.
            auth_required: Whether authentication is required.
        """
        for func_name, func in functions.items():
            self.add_function(func, auth_required=auth_required)
    
    def get_routes(self) -> List[Dict[str, Any]]:
        """
        Get list of registered routes.
        
        Returns:
            List of route info dictionaries.
        """
        return self._routes
    
    def get_router(self) -> APIRouter:
        """
        Get the FastAPI router.
        
        Returns:
            The router.
        """
        return self.router
