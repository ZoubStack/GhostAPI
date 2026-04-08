"""Module inspector for discovering functions to expose as API endpoints."""

import inspect
import sys
from typing import Any, Callable, Dict, List, Optional


class ModuleInspector:
    """
    Inspector for discovering functions in a module.
    
    This class:
    1. Scans a module for public functions
    2. Filters out private functions (starting with _)
    3. Collects function metadata
    """
    
    def __init__(self, module: Optional[Any] = None) -> None:
        """
        Initialize the inspector.
        
        Args:
            module: The module to inspect. If None, will try to detect caller.
        """
        self.module = module
        self._functions: Dict[str, Callable] = {}
    
    def scan_module(self, module: Optional[Any] = None) -> Dict[str, Callable]:
        """
        Scan a module for public functions.
        
        Args:
            module: The module to scan. If None, uses stored module.
        
        Returns:
            Dictionary of function name to function.
        """
        if module is not None:
            self.module = module
        
        if self.module is None:
            return {}
        
        self._functions = {}
        
        for name, obj in inspect.getmembers(self.module, inspect.isfunction):
            # Skip private functions
            if name.startswith("_"):
                continue
            
            # Skip if not defined in this module
            if not self._is_defined_in_module(obj, self.module):
                continue
            
            self._functions[name] = obj
        
        return self._functions
    
    def _is_defined_in_module(self, func: Callable, module: Any) -> bool:
        """
        Check if a function is defined in a specific module.
        
        Args:
            func: The function to check.
            module: The module to check against.
        
        Returns:
            True if function is defined in module.
        """
        try:
            func_module = inspect.getmodule(func)
            if func_module is None:
                # Try to get from globals
                return func.__module__ == module.__name__
            return func_module.__name__ == module.__name__
        except Exception:
            return False
    
    def get_functions(self) -> Dict[str, Callable]:
        """
        Get discovered functions.
        
        Returns:
            Dictionary of function name to function.
        """
        if not self._functions and self.module:
            self.scan_module()
        return self._functions
    
    def get_function_info(self, func: Callable) -> Dict[str, Any]:
        """
        Get detailed information about a function.
        
        Args:
            func: The function to analyze.
        
        Returns:
            Dictionary with function metadata.
        """
        sig = inspect.signature(func)
        
        # Get parameter info
        params = []
        for name, param in sig.parameters.items():
            param_info = {
                "name": name,
                "has_default": param.default != inspect.Parameter.empty,
                "default": param.default if param.default != inspect.Parameter.empty else None,
                "annotation": param.annotation if param.annotation != inspect.Parameter.empty else None,
            }
            params.append(param_info)
        
        # Get return type
        return_annotation = None
        try:
            hints = inspect.getannotations(func)
            return_annotation = hints.get("return")
        except Exception:
            pass
        
        if return_annotation is None:
            if sig.return_annotation != inspect.Signature.empty:
                return_annotation = sig.return_annotation
        
        return {
            "name": func.__name__,
            "params": params,
            "return_type": return_annotation,
            "doc": func.__doc__,
        }
    
    def filter_functions(
        self,
        prefix: Optional[str] = None,
        exclude_prefix: Optional[str] = None
    ) -> Dict[str, Callable]:
        """
        Filter functions by name prefix.
        
        Args:
            prefix: Only include functions starting with this prefix.
            exclude_prefix: Exclude functions starting with this prefix.
        
        Returns:
            Filtered dictionary of functions.
        """
        functions = self.get_functions()
        
        if prefix:
            functions = {k: v for k, v in functions.items() if k.startswith(prefix)}
        
        if exclude_prefix:
            functions = {k: v for k, v in functions.items() if not k.startswith(exclude_prefix)}
        
        return functions


def inspect_caller_module() -> Optional[Any]:
    """
    Inspect the module that called the current function.
    
    Returns:
        The caller's module or None.
    """
    frame = inspect.currentframe()
    if frame is None:
        return None
    
    try:
        # Go up the call stack to find the caller module
        frame = frame.f_back
        while frame is not None:
            module_name = frame.f_globals.get("__name__")
            if module_name and module_name != "ghostapi" and module_name != "__main__":
                return frame.f_globals.get("__module__")
            frame = frame.f_back
    except Exception:
        pass
    
    return None


def get_caller_functions() -> Dict[str, Callable]:
    """
    Get all public functions from the caller's module.
    
    Returns:
        Dictionary of function name to function.
    """
    module = inspect_caller_module()
    if module is None:
        return {}
    
    inspector = ModuleInspector(module)
    return inspector.scan_module()
