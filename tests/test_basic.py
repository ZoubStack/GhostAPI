"""Tests for basic ghostapi functionality."""

import pytest
from fastapi.testclient import TestClient

from ghostapi import create_api, get_app
from ghostapi.core import add_routes


# Test functions
def hello():
    """Simple hello function."""
    return {"message": "Hello World"}


def get_greeting(name: str = "World"):
    """Get greeting with name."""
    return {"message": f"Hello {name}"}


def get_numbers():
    """Get list of numbers."""
    return [1, 2, 3, 4, 5]


def create_item(name: str, description: str = ""):
    """Create an item."""
    return {"name": name, "description": description}


def test_api_creation():
    """Test API can be created."""
    app = create_api()
    assert app is not None
    assert app.title == "GhostAPI"


def test_api_with_custom_title():
    """Test API with custom title."""
    app = create_api(title="My API", version="2.0.0")
    assert app.title == "My API"
    assert app.version == "2.0.0"


def test_hello_endpoint():
    """Test hello endpoint works."""
    app = create_api()
    add_routes(app, {"hello": hello})
    
    client = TestClient(app)
    response = client.get("/hello")
    
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


def test_get_greeting_endpoint():
    """Test get_greeting endpoint with default name."""
    app = create_api()
    add_routes(app, {"get_greeting": get_greeting})
    
    client = TestClient(app)
    response = client.get("/greeting")
    
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}


def test_get_greeting_with_name():
    """Test get_greeting endpoint with custom name."""
    app = create_api()
    add_routes(app, {"get_greeting": get_greeting})
    
    client = TestClient(app)
    response = client.get("/greeting?name=John")
    
    assert response.status_code == 200
    assert response.json() == {"message": "Hello John"}


def test_get_numbers_endpoint():
    """Test get_numbers endpoint."""
    app = create_api()
    add_routes(app, {"get_numbers": get_numbers})
    
    client = TestClient(app)
    response = client.get("/numbers")
    
    assert response.status_code == 200
    assert response.json() == [1, 2, 3, 4, 5]


def test_create_item_endpoint():
    """Test create_item endpoint."""
    app = create_api()
    add_routes(app, {"create_item": create_item})
    
    client = TestClient(app)
    response = client.post("/item", json={"name": "Test Item", "description": "A test"})
    
    assert response.status_code == 200
    assert response.json() == {"name": "Test Item", "description": "A test"}


def test_swagger_docs_available():
    """Test that Swagger docs are available."""
    app = create_api()
    add_routes(app, {"hello": hello})
    
    client = TestClient(app)
    response = client.get("/docs")
    
    assert response.status_code == 200


def test_openapi_json_available():
    """Test that OpenAPI JSON is available."""
    app = create_api()
    add_routes(app, {"hello": hello})
    
    client = TestClient(app)
    response = client.get("/openapi.json")
    
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "paths" in data
