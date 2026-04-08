"""
Example demonstrating the integrated testing system.

This example shows how to use:
- Auto-testing when exposing functions
- ContinuousTester for ongoing validation
- TestGenerator for generating test cases
"""

from ghostapi import expose, create_api, add_routes
from ghostapi.testing import (
    ContinuousTester,
    TestGenerator,
    run_auto_tests
)
from ghostapi.hooks import Hooks


# Define some functions to expose
def get_users():
    """Get list of users."""
    return [{"id": 1, "name": "John"}, {"id": 2, "name": "Jane"}]


def create_user(name: str, email: str):
    """Create a new user."""
    return {"id": 3, "name": name, "email": email}


def get_user_by_id(user_id: int):
    """Get user by ID."""
    return {"id": user_id, "name": "User"}


# Example 1: Using auto_test parameter in expose
# This runs automatic tests when the API starts
# expose(auto_test=True)


# Example 2: Using debug mode (includes auto-tests)
# This is useful during development
# expose(debug=True)


# Example 3: Programmatic testing
def example_continuous_testing():
    """Example of using ContinuousTester."""
    
    tester = ContinuousTester()
    
    def my_function(name: str, age: int):
        return {"name": name, "age": age}
    
    # Test a function
    result = tester.test_function(my_function)
    print(f"Test result: {result}")
    
    # Get validation issues
    print(f"Valid: {result['valid']}")
    print(f"Tests passed: {result['tests_passed']}")


def example_test_generator():
    """Example of using TestGenerator."""
    
    generator = TestGenerator()
    
    def calculate(a: int, b: int) -> int:
        return a + b
    
    # Generate test cases
    test_cases = generator.generate_tests(calculate)
    
    print("Generated test cases:")
    for test_case in test_cases:
        print(f"  - {test_case.name}")
        print(f"    Input: {test_case.input_params}")


def example_manual_tests():
    """Example of running tests manually."""
    
    def get_data():
        return {"data": "test"}
    
    def process_data(name: str, value: int):
        return {"name": name, "value": value}
    
    # Run tests on specific functions
    results = run_auto_tests({
        "get_data": get_data,
        "process_data": process_data
    })
    
    print(f"Total: {results['total']}")
    print(f"Passed: {results['passed']}")
    print(f"Failed: {results['failed']}")


def example_with_hooks():
    """Example of using hooks for custom behavior."""
    
    def log_request(request):
        print(f"Request: {request.method} {request.url}")
    
    def before_response(response):
        response.headers["X-Custom-Header"] = "value"
        return response
    
    hooks = Hooks(
        before_request=log_request,
        before_response=before_response
    )
    
    # Create API with hooks
    app = create_api(hooks=hooks)
    
    print("API created with custom hooks")


if __name__ == "__main__":
    # Run examples
    print("=== Example: Continuous Testing ===")
    example_continuous_testing()
    
    print("\n=== Example: Test Generator ===")
    example_test_generator()
    
    print("\n=== Example: Manual Tests ===")
    example_manual_tests()
    
    print("\n=== Example: Hooks ===")
    example_with_hooks()
