"""Wrapper for converting Python functions to HTTP endpoints."""

import inspect
from typing import Any, Callable, Dict, Optional, Union

from fastapi import Request, Depends, HTTPException, status
from pydantic import BaseModel, ValidationError

from ghostapi.auth.roles import RequireRole


def wrap_function(
    func: Callable,
    request_model: Optional[type[BaseModel]] = None,
    auth_required: bool = False,
    required_role: Optional[str] = None
) -> Callable:
    """
    Wrap a Python function to work as an HTTP endpoint.
    
    Handles:
    - Parameter extraction from request
    - JSON response serialization
    - Error handling
    - Authentication
    
    Args:
        func: The Python function to wrap.
        request_model: Optional Pydantic model for request body.
        auth_required: Whether authentication is required.
        required_role: Required role if auth is enabled.
    
    Returns:
        Wrapped async function suitable for FastAPI.
    """
    # Get function signature
    sig = inspect.signature(func)
    param_names = list(sig.parameters.keys())
    
    async def endpoint(request: Request, body: Optional[request_model] = None) -> Any:
        """
        Async endpoint wrapper.
        """
        try:
            # Build kwargs from query params and path params
            kwargs: Dict[str, Any] = {}
            
            # Get function parameters
            for param_name in param_names:
                if param_name == "request":
                    kwargs[param_name] = request
                    continue
                
                if param_name == "self":
                    continue
                
                param = sig.parameters[param_name]
                
                # Check if parameter is in request body
                if request_model is not None and body is not None:
                    if hasattr(body, param_name):
                        kwargs[param_name] = getattr(body, param_name)
                        continue
                
                # Try to get from query params
                if param.annotation != inspect.Parameter.empty:
                    # For simple types, try to get from query
                    query_value = request.query_params.get(param_name)
                    if query_value is not None:
                        # Try to convert type with detailed error
                        try:
                            if param.annotation != str:
                                kwargs[param_name] = param.annotation(query_value)
                            else:
                                kwargs[param_name] = query_value
                        except (ValueError, TypeError) as e:
                            # Build detailed error message
                            expected_type = _get_type_name(param.annotation)
                            raise HTTPException(
                                status_code=status.HTTP_400_BAD_REQUEST,
                                detail=f"Le paramètre '{param_name}' doit être {expected_type}, reçu : '{query_value}'"
                            )
                        continue
                
                # Check for default value
                if param.default != inspect.Parameter.empty:
                    kwargs[param_name] = param.default
            
            # Call the function
            result = func(**kwargs)
            
            # If result is a coroutine, await it
            if inspect.iscoroutine(result):
                result = await result
            
            return result
            
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except ValidationError as e:
            # Handle Pydantic validation errors with clear messages
            errors = e.errors()
            detailed_errors = []
            for error in errors:
                loc = ".".join(str(l) for l in error["loc"])
                msg = error["msg"]
                error_type = error["type"]
                
                # Build user-friendly message
                if error_type == "missing":
                    detailed_errors.append(f"Le paramètre '{loc}' est requis")
                elif error_type == "type_error":
                    expected = error.get("input", "inconnu")
                    detailed_errors.append(f"Le paramètre '{loc}' a un type invalide: {msg}")
                else:
                    detailed_errors.append(f"Erreur sur '{loc}': {msg}")
            
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=detailed_errors
            )
        except Exception as e:
            # Handle other exceptions - hide internal errors in production
            import os
            debug = os.environ.get("GHOSTAPI_DEBUG", "false").lower() == "true"
            
            if debug:
                import traceback
                detail = f"Error executing function: {str(e)}\n{traceback.format_exc()}"
            else:
                detail = "Internal server error"
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=detail
            )
    
    # Add auth dependency if required
    if auth_required:
        if required_role:
            auth_dep = RequireRole(required_role)
            endpoint = Depends(auth_dep)(endpoint)
        # For auth required without specific role, we rely on middleware
    
    # Preserve function metadata
    endpoint.__name__ = func.__name__
    endpoint.__doc__ = func.__doc__
    
    return endpoint


def _get_type_name(annotation: Any) -> str:
    """
    Get a human-readable type name from annotation.
    
    Args:
        annotation: Type annotation.
    
    Returns:
        Human-readable type name.
    """
    type_names = {
        str: "une chaîne de caractères",
        int: "un entier",
        float: "un nombre décimal",
        bool: "un booléen",
        list: "une liste",
        dict: "un objet",
    }
    
    if annotation in type_names:
        return type_names[annotation]
    
    # Handle Optional[T]
    origin = getattr(annotation, "__origin__", None)
    if origin is Union:
        args = getattr(annotation, "__args__", ())
        if len(args) == 2 and type(None) in args:
            # Optional[T] -> T or None
            non_none = args[0] if args[1] is type(None) else args[1]
            return f"{_get_type_name(non_none)} ou None"
    
    # Handle List[T]
    if origin is list:
        args = getattr(annotation, "__args__", ())
        if args:
            return f"une liste de {_get_type_name(args[0])}"
        return "une liste"
    
    # Default to the type name
    return str(annotation)


def create_endpoint(
    func: Callable,
    method: str = "GET",
    path: str = "/",
    auth_required: bool = False,
    required_role: Optional[str] = None,
    request_model: Optional[type[BaseModel]] = None,
    response_model: Optional[type] = None
) -> Callable:
    """
    Create a configured endpoint from a function.
    
    Args:
        func: The Python function.
        method: HTTP method.
        path: Route path.
        auth_required: Whether auth is required.
        required_role: Required role.
        request_model: Request body model.
        response_model: Response model.
    
    Returns:
        Configured endpoint.
    """
    endpoint = wrap_function(
        func,
        request_model=request_model,
        auth_required=auth_required,
        required_role=required_role
    )
    
    return endpoint
