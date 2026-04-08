"""Utility functions for ghostapi."""

import inspect
from typing import Any, Callable, Dict, List, Optional, get_type_hints


def get_function_name(func: Callable) -> str:
    """
    Get the name of a function.
    
    Args:
        func: The function to get name from.
    
    Returns:
        The function name.
    """
    return func.__name__


def is_private_function(func: Callable) -> bool:
    """
    Check if a function is private (starts with underscore).
    
    Args:
        func: The function to check.
    
    Returns:
        True if the function is private.
    """
    return get_function_name(func).startswith("_")


def get_function_signature(func: Callable) -> inspect.Signature:
    """
    Get the signature of a function.
    
    Args:
        func: The function to get signature from.
    
    Returns:
        The function signature.
    """
    return inspect.signature(func)


def get_function_params(func: Callable) -> Dict[str, inspect.Parameter]:
    """
    Get the parameters of a function.
    
    Args:
        func: The function to get parameters from.
    
    Returns:
        Dictionary of parameter name to parameter.
    """
    sig = get_function_signature(func)
    return sig.parameters


def get_return_type(func: Callable) -> Optional[type]:
    """
    Get the return type annotation of a function.
    
    Args:
        func: The function to get return type from.
    
    Returns:
        The return type or None.
    """
    try:
        hints = get_type_hints(func)
        return hints.get("return")
    except Exception:
        # If type hints can't be resolved
        sig = get_function_signature(func)
        if sig.return_annotation != sig.empty:
            return sig.return_annotation
        return None


def get_http_method(func_name: str) -> str:
    """
    Determine HTTP method from function name.
    
    Args:
        func_name: The function name.
    
    Returns:
        The HTTP method (GET, POST, PUT, DELETE).
    """
    name_lower = func_name.lower()
    
    if name_lower.startswith("get_"):
        return "GET"
    elif name_lower.startswith("create_"):
        return "POST"
    elif name_lower.startswith("update_"):
        return "PUT"
    elif name_lower.startswith("delete_"):
        return "DELETE"
    elif name_lower.startswith("patch_"):
        return "PATCH"
    
    # Default to GET for other function names
    return "GET"


def get_route_path(func_name: str) -> str:
    """
    Convert function name to route path.
    
    Args:
        func_name: The function name.
    
    Returns:
        The route path.
    """
    # Convert function_name to /function-name
    # get_users -> /get-users
    # create_user -> /create-user
    
    # Remove prefix
    for prefix in ["get_", "create_", "update_", "delete_", "patch_"]:
        if func_name.lower().startswith(prefix):
            func_name = func_name[len(prefix):]
            break
    
    # Convert camelCase or snake_case to kebab-case
    path = func_name.replace("_", "-").lower()
    
    return f"/{path}"


def validate_params(func: Callable, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and sanitize function parameters.
    
    Args:
        func: The function to validate params for.
        params: The parameters to validate.
    
    Returns:
        Validated parameters.
    """
    func_params = get_function_params(func)
    validated = {}
    
    for name, param in func_params.items():
        if name in params:
            # Convert to expected type if needed
            if param.annotation != inspect.Parameter.empty:
                try:
                    validated[name] = param.annotation(params[name])
                except (ValueError, TypeError):
                    validated[name] = params[name]
            else:
                validated[name] = params[name]
        elif param.default == inspect.Parameter.empty:
            # Required param not provided
            pass
    
    return validated


def get_module_functions(module: Any) -> List[Callable]:
    """
    Get all public functions from a module.
    
    Args:
        module: The module to inspect.
    
    Returns:
        List of functions.
    """
    functions = []
    
    for name, obj in inspect.getmembers(module, inspect.isfunction):
        if not name.startswith("_"):
            functions.append(obj)
    
    return functions


def get_caller_module() -> Optional[Any]:
    """
    Get the module that called the expose function.
    
    Returns:
        The caller's module or None.
    """
    frame = inspect.currentframe()
    if frame is None:
        return None
    
    try:
        # Go up to find the caller
        frame = frame.f_back
        while frame is not None:
            module = frame.f_globals.get("__name__")
            if module and module != "__main__":
                # Try to import the module
                import sys
                return sys.modules.get(module)
            frame = frame.f_back
    except Exception:
        pass
    
    return None
