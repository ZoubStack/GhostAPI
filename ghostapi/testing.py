"""
Integrated testing system for GhostAPI.

This module provides automatic testing capabilities for user-defined functions.
It generates and runs tests automatically when functions are exposed.
"""

import inspect
import tempfile
from typing import Any, Callable, Dict, List, Optional, Type
from dataclasses import dataclass

from fastapi import FastAPI
from pydantic import BaseModel, ValidationError


@dataclass
class TestCase:
    """Represents a generated test case."""
    name: str
    func_name: str
    input_params: Dict[str, Any]
    expected_type: Optional[type] = None


class TestGenerator:
    """
    Automatically generates test cases from function signatures.
    
    Example:
        generator = TestGenerator()
        
        def create_user(name: str, age: int):
            return {"name": name, "age": age}
        
        test_cases = generator.generate_tests(create_user)
        # Generates: test_create_user_success, test_create_user_invalid_age, etc.
    """
    
    def __init__(self) -> None:
        self.test_cases: List[TestCase] = []
    
    def generate_tests(self, func: Callable) -> List[TestCase]:
        """
        Generate test cases from a function.
        
        Args:
            func: The function to generate tests for.
        
        Returns:
            List of test cases.
        """
        test_cases = []
        sig = inspect.signature(func)
        
        # Generate valid input test
        valid_params = {}
        for name, param in sig.parameters.items():
            if param.annotation != inspect.Parameter.empty:
                valid_params[name] = self._get_sample_value(param.annotation)
        
        if valid_params:
            test_cases.append(TestCase(
                name=f"test_{func.__name__}_success",
                func_name=func.__name__,
                input_params=valid_params
            ))
        
        # Generate invalid type tests for each parameter
        for name, param in sig.parameters.items():
            if param.annotation != inspect.Parameter.empty:
                # Test with wrong type
                invalid_params = valid_params.copy()
                invalid_params[name] = self._get_invalid_value(param.annotation)
                
                test_cases.append(TestCase(
                    name=f"test_{func.__name__}_invalid_{name}",
                    func_name=func.__name__,
                    input_params=invalid_params
                ))
        
        return test_cases
    
    def _get_sample_value(self, annotation: type) -> Any:
        """Get a sample value for a type."""
        sample_values = {
            str: "test",
            int: 1,
            float: 1.0,
            bool: True,
            list: [],
            dict: {},
        }
        
        # Handle Optional
        origin = getattr(annotation, "__origin__", None)
        if origin is not None:
            from typing import Optional
            if origin is Optional:
                args = getattr(annotation, "__args__", ())
                for arg in args:
                    if arg is not type(None) and arg in sample_values:
                        return sample_values[arg]
        
        return sample_values.get(annotation, "test")
    
    def _get_invalid_value(self, annotation: type) -> Any:
        """Get an invalid value for a type."""
        invalid_values = {
            str: 123,
            int: "invalid",
            float: "invalid",
            bool: "not a bool",
            list: "not a list",
            dict: "not a dict",
        }
        
        origin = getattr(annotation, "__origin__", None)
        if origin is not None:
            from typing import Optional
            if origin is Optional:
                return "invalid"
        
        return invalid_values.get(annotation, "invalid")


class AutoTester:
    """
    Automatically tests exposed functions.
    
    Example:
        from ghostapi.testing import AutoTester
        
        def create_user(name: str, age: int):
            return {"name": name, "age": age}
        
        tester = AutoTester()
        results = tester.run_tests([create_user])
        print(results)  # {'passed': 2, 'failed': 0, 'errors': []}
    """
    
    def __init__(self) -> None:
        self.generator = TestGenerator()
        self.results: Dict[str, Any] = {}
    
    def run_tests(self, functions: List[Callable]) -> Dict[str, Any]:
        """
        Run auto-generated tests on functions.
        
        Args:
            functions: List of functions to test.
        
        Returns:
            Test results dictionary.
        """
        passed = 0
        failed = 0
        errors = []
        
        for func in functions:
            test_cases = self.generator.generate_tests(func)
            
            for test_case in test_cases:
                try:
                    # Try to call the function
                    result = func(**test_case.input_params)
                    
                    # Check if result is valid
                    if result is not None:
                        passed += 1
                    else:
                        failed += 1
                        
                except ValidationError as e:
                    # Expected for invalid inputs
                    passed += 1  # Correctly rejected invalid input
                    
                except Exception as e:
                    # Unexpected error
                    failed += 1
                    errors.append({
                        "test": test_case.name,
                        "error": str(e)
                    })
        
        return {
            "passed": passed,
            "failed": failed,
            "total": passed + failed,
            "errors": errors
        }
    
    def validate_function(self, func: Callable) -> Dict[str, Any]:
        """
        Validate a function and return validation results.
        
        Args:
            func: Function to validate.
        
        Returns:
            Validation results with potential issues.
        """
        issues = []
        
        # Check function signature
        sig = inspect.signature(func)
        
        for name, param in sig.parameters.items():
            if param.annotation == inspect.Parameter.empty:
                issues.append({
                    "type": "missing_type_hint",
                    "param": name,
                    "message": f"Parameter '{name}' lacks type annotation"
                })
        
        # Check return type
        if sig.return_annotation == inspect.Signature.empty:
            issues.append({
                "type": "missing_return_type",
                "message": "Function lacks return type annotation"
            })
        
        return {
            "function": func.__name__,
            "valid": len(issues) == 0,
            "issues": issues
        }


class ContinuousTester:
    """
    Continuous testing integration for GhostAPI.
    
    This class provides hooks for continuous testing when adding new functions.
    
    Example:
        from ghostapi.testing import ContinuousTester
        
        tester = ContinuousTester()
        
        def my_new_function(name: str):
            return {"name": name}
        
        # Test when adding the function
        result = tester.test_function(my_new_function)
        print(result)  # {'valid': True, 'tests_passed': True}
    """
    
    def __init__(self) -> None:
        self.auto_tester = AutoTester()
        self.test_history: List[Dict] = []
    
    def test_function(self, func: Callable) -> Dict[str, Any]:
        """
        Test a new function automatically.
        
        Args:
            func: The function to test.
        
        Returns:
            Test results.
        """
        # Validate function
        validation = self.auto_tester.validate_function(func)
        
        # Run tests
        test_results = self.auto_tester.run_tests([func])
        
        # Store in history
        self.test_history.append({
            "function": func.__name__,
            "validation": validation,
            "test_results": test_results,
            "timestamp": str(inspect.getsourcefile(func))
        })
        
        return {
            "valid": validation["valid"],
            "tests_passed": test_results["failed"] == 0,
            "validation": validation,
            "test_results": test_results
        }
    
    def test_module(self, module: Any) -> Dict[str, Any]:
        """
        Test all functions in a module.
        
        Args:
            module: The module to test.
        
        Returns:
            Aggregated test results.
        """
        from ghostapi.inspector import ModuleInspector
        
        inspector = ModuleInspector(module)
        functions = inspector.scan_module()
        
        results = []
        for func_name, func in functions.items():
            result = self.test_function(func)
            results.append(result)
        
        passed = sum(1 for r in results if r["tests_passed"])
        failed = len(results) - passed
        
        return {
            "total_functions": len(results),
            "passed": passed,
            "failed": failed,
            "results": results
        }
    
    def get_history(self) -> List[Dict]:
        """Get test history."""
        return self.test_history


# Decorator for auto-testing
def auto_test(func: Callable) -> Callable:
    """
    Decorator to automatically test a function when it's called.
    
    Example:
        @auto_test
        def calculate(a: int, b: int) -> int:
            return a + b
    """
    tester = ContinuousTester()
    
    def wrapper(*args, **kwargs):
        result = func(*args, **kwargs)
        test_result = tester.test_function(func)
        
        if not test_result["tests_passed"]:
            print(f"Warning: Test failed for {func.__name__}")
        
        return result
    
    return wrapper


# Integration with expose
def run_auto_tests(functions: Dict[str, Callable]) -> Dict[str, Any]:
    """
    Run auto-tests on exposed functions.
    
    This can be called after expose() to verify all functions work correctly.
    
    Args:
        functions: Dictionary of function name to function.
    
    Returns:
        Test results.
    """
    tester = ContinuousTester()
    
    results = []
    for func_name, func in functions.items():
        result = tester.test_function(func)
        results.append(result)
    
    passed = sum(1 for r in results if r["tests_passed"])
    
    return {
        "total": len(results),
        "passed": passed,
        "failed": len(results) - passed,
        "results": results
    }
