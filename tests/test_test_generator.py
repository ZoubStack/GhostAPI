"""Tests for Test Generator features."""

import pytest

from ghostapi.test_generator import (
    TypeTestGenerator,
    AutoTestGenerator,
    TestCase,
    MockDataGenerator,
    get_test_generator,
    get_mock_generator
)


class TestTypeTestGenerator:
    """Tests for type-based test data generation."""
    
    def test_initialization(self):
        """Test generator initialization."""
        gen = TypeTestGenerator()
        
        assert gen is not None
    
    def test_generate_int(self):
        """Test integer generation."""
        gen = TypeTestGenerator()
        
        values = gen.generate_for_type(int)
        
        assert 0 in values
        assert 1 in values
        assert -1 in values
    
    def test_generate_str(self):
        """Test string generation."""
        gen = TypeTestGenerator()
        
        values = gen.generate_for_type(str)
        
        assert "test" in values
        assert "hello" in values
    
    def test_generate_bool(self):
        """Test boolean generation."""
        gen = TypeTestGenerator()
        
        values = gen.generate_for_type(bool)
        
        assert True in values
        assert False in values
    
    def test_generate_float(self):
        """Test float generation."""
        gen = TypeTestGenerator()
        
        values = gen.generate_for_type(float)
        
        assert 0.0 in values
        assert isinstance(values[0], float)


class TestAutoTestGenerator:
    """Tests for automatic test generation."""
    
    def test_initialization(self):
        """Test generator initialization."""
        gen = AutoTestGenerator()
        
        assert gen is not None
    
    def test_generate_simple_function(self):
        """Test generating tests for simple function."""
        def add(x: int, y: int) -> int:
            return x + y
        
        gen = AutoTestGenerator()
        test_cases = gen.generate_tests(add, max_cases=3)
        
        assert len(test_cases) <= 3
        assert all(isinstance(tc, TestCase) for tc in test_cases)
    
    def test_run_tests(self):
        """Test running generated tests."""
        def add(x: int, y: int) -> int:
            return x + y
        
        gen = AutoTestGenerator()
        test_cases = gen.generate_tests(add, max_cases=3)
        
        results = gen.run_tests(add, test_cases)
        
        assert results["total"] == len(test_cases)
        assert results["passed"] >= 0
    
    def test_generate_test_code(self):
        """Test generating pytest code."""
        def multiply(x: int, y: int) -> int:
            return x * y
        
        gen = AutoTestGenerator()
        code = gen.generate_test_code(multiply)
        
        assert "import pytest" in code
        assert "def test_multiply" in code
        assert "assert isinstance(result, int)" in code
    
    def test_function_with_defaults(self):
        """Test generating tests for function with defaults."""
        def greet(name: str, greeting: str = "Hello") -> str:
            return f"{greeting}, {name}!"
        
        gen = AutoTestGenerator()
        test_cases = gen.generate_tests(greet, max_cases=2)
        
        assert len(test_cases) > 0


class TestMockDataGenerator:
    """Tests for mock data generation."""
    
    def test_initialization(self):
        """Test generator initialization."""
        gen = MockDataGenerator()
        
        assert gen is not None
    
    def test_generate_for_schema(self):
        """Test generating mock data for schema."""
        gen = MockDataGenerator()
        
        schema = {
            "id": "int",
            "name": "str",
            "email": "str",
            "age": "int"
        }
        
        data = gen.generate_for_schema(schema)
        
        assert "id" in data
        assert "name" in data
        assert "email" in data
        assert "age" in data
    
    def test_generate_list(self):
        """Test generating list of mock objects."""
        gen = MockDataGenerator()
        
        schema = {
            "id": "int",
            "name": "str"
        }
        
        data = gen.generate_list(schema, count=3)
        
        assert len(data) == 3
    
    def test_parse_type_string(self):
        """Test parsing type strings."""
        gen = MockDataGenerator()
        
        assert gen._parse_type_string("int") == int
        assert gen._parse_type_string("str") == str
        assert gen._parse_type_string("bool") == bool
        assert gen._parse_type_string("float") == float


class TestGlobalInstances:
    """Tests for global generator instances."""
    
    def test_get_test_generator(self):
        """Test getting global test generator."""
        gen1 = get_test_generator()
        gen2 = get_test_generator()
        
        assert gen1 is gen2
    
    def test_get_mock_generator(self):
        """Test getting global mock generator."""
        gen1 = get_mock_generator()
        gen2 = get_mock_generator()
        
        assert gen1 is gen2


class TestTestCase:
    """Tests for TestCase dataclass."""
    
    def test_creation(self):
        """Test creating a TestCase."""
        case = TestCase(
            name="test_example",
            input_args=(1, 2),
            input_kwargs={},
            expected_type=int
        )
        
        assert case.name == "test_example"
        assert case.input_args == (1, 2)
        assert case.expected_type == int
