"""
Auto Test Generator module for GhostAPI.

Generates unit tests automatically based on:
- Type annotations
- Function signatures
- Return types
"""

import inspect
import ast
from typing import Any, Callable, Dict, List, Optional, get_type_hints, get_origin, get_args
from dataclasses import dataclass

from pydantic import BaseModel


# Test data generators based on types
class TypeTestGenerator:
    """
    Generates test data based on Python type annotations.
    
    Example:
        generator = TypeTestGenerator()
        
        # Generate test values for a type
        values = generator.generate_for_type(int)  # [0, 1, -1, 100, etc.]
        values = generator.generate_for_type(str)  # ["test", "hello", etc.]
    """
    
    def __init__(self):
        self._generators = {
            int: self._generate_int,
            float: self._generate_float,
            str: self._generate_str,
            bool: self._generate_bool,
            list: self._generate_list,
            dict: self._generate_dict,
        }
    
    def generate_for_type(self, type_hint: Any, depth: int = 0) -> List[Any]:
        """Generate test values for a type hint."""
        # Handle Optional
        origin = get_origin(type_hint)
        
        if origin is list:
            return self._generate_list(get_args(type_hint)[0] if get_args(type_hint) else str)
        elif origin is dict:
            args = get_args(type_hint)
            key_type = args[0] if args else str
            value_type = args[1] if len(args) > 1 else str
            return self._generate_dict(key_type, value_type)
        elif origin is Optional:
            # Include None as one of the values
            args = get_args(type_hint)
            if args:
                values = self.generate_for_type(args[0], depth)
                values.append(None)
                return values
        
        # Handle standard types
        for type_obj, generator in self._generators.items():
            if type_hint == type_obj or (origin and origin == type_obj):
                return generator()
        
        # For complex types, return generic values
        return [None]
    
    def _generate_int(self) -> List[int]:
        """Generate integer test values."""
        return [0, 1, -1, 100, -100, 42, 999999]
    
    def _generate_float(self) -> List[float]:
        """Generate float test values."""
        return [0.0, 1.5, -0.5, 3.14159, 100.5, -50.25]
    
    def _generate_str(self) -> List[str]:
        """Generate string test values."""
        return ["test", "hello", "world", "", "a" * 100, "123", "test@example.com"]
    
    def _generate_bool(self) -> List[bool]:
        """Generate boolean test values."""
        return [True, False]
    
    def _generate_list(self, item_type: Any = str) -> List[List]:
        """Generate list test values."""
        return [[], [1, 2, 3], ["a", "b"], [True, False], []]
    
    def _generate_dict(self, key_type: Any = str, value_type: Any = str) -> List[Dict]:
        """Generate dict test values."""
        return [
            {},
            {"key": "value"},
            {"a": 1, "b": 2},
            {"nested": {"key": "value"}},
        ]


# Test case representation
@dataclass
class TestCase:
    """Represents a generated test case."""
    name: str
    input_args: tuple
    input_kwargs: dict
    expected_type: Optional[type]
    description: str = ""


class AutoTestGenerator:
    """
    Automatically generates unit tests for functions.
    
    Example:
        generator = AutoTestGenerator()
        
        def add(x: int, y: int) -> int:
            return x + y
        
        # Generate test cases
        test_cases = generator.generate_tests(add)
        
        # Run tests
        for case in test_cases:
            result = add(*case.input_args, **case.input_kwargs)
            assert isinstance(result, int)
    """
    
    def __init__(self):
        self.type_generator = TypeTestGenerator()
    
    def generate_tests(
        self,
        func: Callable,
        max_cases: int = 10
    ) -> List[TestCase]:
        """
        Generate test cases for a function.
        
        Args:
            func: Function to generate tests for
            max_cases: Maximum number of test cases
        
        Returns:
            List of TestCase objects
        """
        # Get function signature
        sig = inspect.signature(func)
        type_hints = get_type_hints(func) if hasattr(func, '__annotations__') else {}
        
        test_cases = []
        
        # Generate combinations of test values
        param_values = {}
        
        for param_name, param in sig.parameters.items():
            param_type = type_hints.get(param_name, param.annotation if param.annotation != inspect.Parameter.empty else str)
            values = self.type_generator.generate_for_type(param_type)[:3]  # Limit values per param
            
            if param.default != inspect.Parameter.empty:
                # Include default value
                values = [param.default] + values
            
            param_values[param_name] = values
        
        # Generate combinations
        import itertools
        param_names = list(param_values.keys())
        
        for i, values in enumerate(itertools.product(*param_values.values())):
            if i >= max_cases:
                break
            
            args = ()
            kwargs = {}
            
            for j, name in enumerate(param_names):
                value = values[j]
                
                # Determine if positional or keyword
                param = sig.parameters[name]
                if param.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD):
                    args = args + (value,)
                else:
                    kwargs[name] = value
            
            # Get return type
            return_type = type_hints.get('return')
            
            test_case = TestCase(
                name=f"test_{func.__name__}_{i+1}",
                input_args=args,
                input_kwargs=kwargs,
                expected_type=return_type,
                description=f"Test case {i+1} for {func.__name__}"
            )
            
            test_cases.append(test_case)
        
        return test_cases
    
    def run_tests(self, func: Callable, test_cases: List[TestCase]) -> Dict[str, Any]:
        """
        Run generated test cases.
        
        Returns:
            Dict with test results
        """
        results = {
            "total": len(test_cases),
            "passed": 0,
            "failed": 0,
            "errors": []
        }
        
        for case in test_cases:
            try:
                result = func(*case.input_args, **case.input_kwargs)
                
                # Check return type if specified
                if case.expected_type and result is not None:
                    if not isinstance(result, case.expected_type):
                        results["failed"] += 1
                        results["errors"].append({
                            "case": case.name,
                            "error": f"Return type mismatch: expected {case.expected_type}, got {type(result)}"
                        })
                        continue
                
                results["passed"] += 1
                
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "case": case.name,
                    "error": str(e)
                })
        
        return results
    
    def generate_test_code(self, func: Callable) -> str:
        """
        Generate pytest-compatible test code.
        
        Args:
            func: Function to generate tests for
        
        Returns:
            String containing generated test code
        """
        sig = inspect.signature(func)
        type_hints = get_type_hints(func) if hasattr(func, '__annotations__') else {}
        
        lines = [
            f"import pytest",
            f"from {func.__module__} import {func.__name__}",
            "",
            f"class Test{func.__name__.capitalize()}:",
            f"    \"\"\"Auto-generated tests for {func.__name__}.\"\"\"",
            ""
        ]
        
        # Generate test cases
        test_cases = self.generate_tests(func, max_cases=5)
        
        for case in test_cases:
            # Format arguments
            args_str = ", ".join(repr(a) for a in case.input_args)
            kwargs_str = ", ".join(f"{k}={repr(v)}" for k, v in case.input_kwargs.items())
            all_args = ", ".join(filter(None, [args_str, kwargs_str]))
            
            lines.append(f"    def {case.name}(self):")
            lines.append(f"        \"\"\"Test case: {case.description}\"\"\"" )
            lines.append(f"        result = {func.__name__}({all_args})")
            
            # Add type check if return type is specified
            return_type = type_hints.get('return')
            if return_type and return_type != inspect.Parameter.empty:
                lines.append(f"        assert isinstance(result, {return_type.__name__})")
            
            lines.append("")
        
        return "\n".join(lines)


# Mock data generator for API endpoints
class MockDataGenerator:
    """
    Generates mock data for API testing and documentation.
    
    Example:
        generator = MockDataGenerator()
        
        # Generate mock data for a model\n        user_data = generator.generate_for_schema({\n            \"id\": \"int\",\n            \"name\": \"str\",\n            \"email\": \"str\",\n            \"age\": \"int\"\n        })
    """
    
    def __init__(self):
        self.type_gen = TypeTestGenerator()
    
    def generate_for_schema(self, schema: Dict[str, str]) -> Dict[str, Any]:
        """
        Generate mock data based on a schema dict.
        
        Args:
            schema: Dict mapping field names to type names
        
        Returns:
            Dict with generated mock data
        """
        result = {}
        
        for field, type_str in schema.items():
            # Parse type string
            type_hint = self._parse_type_string(type_str)
            values = self.type_gen.generate_for_type(type_hint)
            result[field] = values[0] if values else None
        
        return result
    
    def generate_list(self, schema: Dict[str, str], count: int = 5) -> List[Dict]:
        """Generate a list of mock objects."""
        return [self.generate_for_schema(schema) for _ in range(count)]
    
    def _parse_type_string(self, type_str: str) -> type:
        """Parse type string to Python type."""
        type_map = {
            "int": int,
            "float": float,
            "str": str,
            "bool": bool,
            "list": list,
            "dict": dict,
        }
        return type_map.get(type_str.lower(), str)
    
    def generate_for_pydantic(self, model: type) -> Dict[str, Any]:
        """Generate mock data for a Pydantic model."""
        if not issubclass(model, BaseModel):
            raise ValueError("Model must be a Pydantic BaseModel")
        
        result = {}
        
        for name, field in model.model_fields.items():
            values = self.type_gen.generate_for_type(field.annotation)
            result[name] = values[0] if values else None
        
        return result
    
    def generate_faker_data(self, schema: Dict[str, str]) -> Dict[str, Any]:
        """
        Generate realistic fake data using faker.
        
        Requires faker package.
        """
        try:
            from faker import Faker
            fake = Faker()
            
            result = {}
            
            for field, type_str in schema.items():
                # Generate based on field name patterns
                if 'email' in field.lower():
                    result[field] = fake.email()
                elif 'name' in field.lower():
                    result[field] = fake.name()
                elif 'first_name' in field.lower():
                    result[field] = fake.first_name()
                elif 'last_name' in field.lower():
                    result[field] = fake.last_name()
                elif 'address' in field.lower():
                    result[field] = fake.address()
                elif 'phone' in field.lower():
                    result[field] = fake.phone_number()
                elif 'city' in field.lower():
                    result[field] = fake.city()
                elif 'country' in field.lower():
                    result[field] = fake.country()
                elif 'company' in field.lower():
                    result[field] = fake.company()
                elif 'date' in field.lower():
                    result[field] = str(fake.date())
                elif 'url' in field.lower():
                    result[field] = fake.url()
                elif 'ip' in field.lower():
                    result[field] = fake.ipv4()
                else:
                    # Default generation
                    type_hint = self._parse_type_string(type_str)
                    values = self.type_gen.generate_for_type(type_hint)
                    result[field] = values[0] if values else None
            
            return result
            
        except ImportError:
            # Fallback to basic generation
            return self.generate_for_schema(schema)


# Global instances
_test_generator = AutoTestGenerator()
_mock_generator = MockDataGenerator()


def get_test_generator() -> AutoTestGenerator:
    """Get global test generator."""
    return _test_generator


def get_mock_generator() -> MockDataGenerator:
    """Get global mock data generator."""
    return _mock_generator
