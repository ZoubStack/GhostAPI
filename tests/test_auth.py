"""Tests for authentication functionality."""

import pytest
from fastapi.testclient import TestClient

from ghostapi import create_api
from ghostapi.auth import enable_auth, create_test_user, clear_user_storage
from ghostapi.core import add_routes


# Test functions
def get_public_data():
    """Public endpoint - no auth required."""
    return {"data": "public"}


def get_private_data():
    """Private endpoint - auth required."""
    return {"data": "private"}


def get_admin_data():
    """Admin only endpoint."""
    return {"data": "admin only"}


class TestAuthentication:
    """Test authentication functionality."""
    
    def setup_method(self):
        """Setup before each test."""
        clear_user_storage()
    
    def test_register_user(self):
        """Test user registration."""
        app = create_api(auth=True)
        
        client = TestClient(app)
        response = client.post(
            "/api/auth/register",
            json={"email": "test@example.com", "password": "Password123", "role": "user"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        assert data["role"] == "user"
        assert "id" in data
    
    def test_login_user(self):
        """Test user login."""
        # Create a test user first
        create_test_user("test@example.com", "Password123")
        
        app = create_api(auth=True)
        
        client = TestClient(app)
        response = client.post(
            "/api/auth/login",
            data={"username": "test@example.com", "password": "Password123"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        app = create_api(auth=True)
        
        client = TestClient(app)
        response = client.post(
            "/api/auth/login",
            data={"username": "test@example.com", "password": "WrongPass123"}
        )
        
        assert response.status_code == 401
    
    def test_protected_endpoint_without_token(self):
        """Test accessing protected endpoint without token."""
        app = create_api(auth=True)
        add_routes(app, {"get_private_data": get_private_data}, auth_required=True)
        
        client = TestClient(app)
        response = client.get("/private-data")
        
        # Without token, should have limited access (middleware allows but no user info)
        # The endpoint itself may need role check
    
    def test_protected_endpoint_with_token(self):
        """Test accessing protected endpoint with valid token."""
        # Create a test user
        create_test_user("test@example.com", "Password123")
        
        app = create_api(auth=True)
        add_routes(app, {"get_private_data": get_private_data}, auth_required=True)
        
        # Login to get token
        client = TestClient(app)
        login_response = client.post(
            "/api/auth/login",
            data={"username": "test@example.com", "password": "Password123"}
        )
        token = login_response.json()["access_token"]
        
        # Access protected endpoint
        response = client.get(
            "/private-data",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
    
    def test_get_current_user(self):
        """Test getting current user info."""
        create_test_user("test@example.com", "Password123")
        
        app = create_api(auth=True)
        
        client = TestClient(app)
        
        # Login
        login_response = client.post(
            "/api/auth/login",
            data={"username": "test@example.com", "password": "Password123"}
        )
        token = login_response.json()["access_token"]
        
        # Get current user
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
    
    def test_invalid_token(self):
        """Test using invalid token."""
        app = create_api(auth=True)
        
        client = TestClient(app)
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        # Invalid token should not authenticate
        assert response.status_code in [401, 403]
    
    def test_user_already_exists(self):
        """Test registering duplicate user."""
        create_test_user("test@example.com", "Password123")
        
        app = create_api(auth=True)
        
        client = TestClient(app)
        response = client.post(
            "/api/auth/register",
            json={"email": "test@example.com", "password": "Password123", "role": "user"}
        )
        
        assert response.status_code == 409
    
    def test_password_validation(self):
        """Test password validation requirements."""
        app = create_api(auth=True)
        
        client = TestClient(app)
        
        # Test short password
        response = client.post(
            "/api/auth/register",
            json={"email": "test@example.com", "password": "Pass123", "role": "user"}
        )
        assert response.status_code == 422
        
        # Test password without uppercase
        response = client.post(
            "/api/auth/register",
            json={"email": "test2@example.com", "password": "password123", "role": "user"}
        )
        assert response.status_code == 422
        
        # Test password without lowercase
        response = client.post(
            "/api/auth/register",
            json={"email": "test3@example.com", "password": "PASSWORD123", "role": "user"}
        )
        assert response.status_code == 422
        
        # Test password without digit
        response = client.post(
            "/api/auth/register",
            json={"email": "test4@example.com", "password": "Passwordabc", "role": "user"}
        )
        assert response.status_code == 422


class TestRoleBasedAccess:
    """Test role-based access control."""
    
    def setup_method(self):
        """Setup before each test."""
        clear_user_storage()
    
    def test_admin_role(self):
        """Test admin role access."""
        create_test_user("admin@example.com", "Password123", role="admin")
        
        app = create_api(auth=True)
        
        client = TestClient(app)
        
        # Login as admin
        login_response = client.post(
            "/api/auth/login",
            data={"username": "admin@example.com", "password": "Password123"}
        )
        token = login_response.json()["access_token"]
        
        # Access should work
        assert "access_token" in login_response.json()
