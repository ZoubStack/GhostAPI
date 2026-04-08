"""Tests for route mapping."""

import pytest
from fastapi.testclient import TestClient

from ghostapi import create_api
from ghostapi.core import add_routes


# Test functions for different HTTP methods
def get_users():
    """Get all users."""
    return [{"id": 1, "name": "John"}, {"id": 2, "name": "Jane"}]


def get_user_by_id(user_id: int):
    """Get user by ID."""
    return {"id": user_id, "name": f"User {user_id}"}


def create_user(name: str, email: str):
    """Create a new user."""
    return {"name": name, "email": email, "id": 100}


def update_user(user_id: int, name: str):
    """Update a user."""
    return {"id": user_id, "name": name}


def delete_user(user_id: int):
    """Delete a user."""
    return {"deleted": True, "user_id": user_id}


def patch_user(user_id: int, name: str):
    """Patch a user."""
    return {"id": user_id, "name": name}


class TestRouteMapping:
    """Test route mapping functionality."""
    
    def test_get_method_mapping(self):
        """Test GET method mapping from function name."""
        app = create_api()
        add_routes(app, {"get_users": get_users})
        
        client = TestClient(app)
        response = client.get("/users")
        
        assert response.status_code == 200
        assert len(response.json()) == 2
    
    def test_get_with_params(self):
        """Test GET with query parameters."""
        app = create_api()
        add_routes(app, {"get_user_by_id": get_user_by_id})
        
        client = TestClient(app)
        response = client.get("/user-by-id?user_id=42")
        
        assert response.status_code == 200
        assert response.json() == {"id": 42, "name": "User 42"}
    
    def test_post_method_mapping(self):
        """Test POST method mapping."""
        app = create_api()
        add_routes(app, {"create_user": create_user})
        
        client = TestClient(app)
        response = client.post("/user", json={"name": "John", "email": "john@example.com"})
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "John"
        assert data["email"] == "john@example.com"
    
    def test_put_method_mapping(self):
        """Test PUT method mapping."""
        app = create_api()
        add_routes(app, {"update_user": update_user})
        
        client = TestClient(app)
        response = client.put("/user", json={"user_id": 1, "name": "Updated"})
        
        assert response.status_code == 200
        assert response.json() == {"id": 1, "name": "Updated"}
    
    def test_delete_method_mapping(self):
        """Test DELETE method mapping."""
        app = create_api()
        add_routes(app, {"delete_user": delete_user})
        
        client = TestClient(app)
        response = client.delete("/user?user_id=5")
        
        assert response.status_code == 200
        assert response.json() == {"deleted": True, "user_id": 5}
    
    def test_patch_method_mapping(self):
        """Test PATCH method mapping."""
        app = create_api()
        add_routes(app, {"patch_user": patch_user})
        
        client = TestClient(app)
        response = client.patch("/user", json={"user_id": 1, "name": "Patched"})
        
        assert response.status_code == 200
        assert response.json() == {"id": 1, "name": "Patched"}
    
    def test_multiple_routes(self):
        """Test multiple routes in one app."""
        app = create_api()
        add_routes(app, {
            "get_users": get_users,
            "create_user": create_user,
            "get_user_by_id": get_user_by_id
        })
        
        client = TestClient(app)
        
        # Test GET /users
        response = client.get("/users")
        assert response.status_code == 200
        
        # Test POST /user
        response = client.post("/user", json={"name": "Test", "email": "test@test.com"})
        assert response.status_code == 200
        
        # Test GET /user-by-id
        response = client.get("/user-by-id?user_id=1")
        assert response.status_code == 200


class TestRoutePathConversion:
    """Test route path conversion."""
    
    def test_underscore_to_dash(self):
        """Test underscore in function name converts to dash in path."""
        app = create_api()
        add_routes(app, {"get_user_by_id": get_user_by_id})
        
        client = TestClient(app)
        response = client.get("/user-by-id?user_id=1")
        
        assert response.status_code == 200
    
    def test_create_prefix_removed(self):
        """Test create_ prefix is removed from path."""
        app = create_api()
        add_routes(app, {"create_user": create_user})
        
        client = TestClient(app)
        response = client.post("/user", json={"name": "Test", "email": "test@test.com"})
        
        assert response.status_code == 200
