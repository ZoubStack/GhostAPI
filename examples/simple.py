"""Simple example of using ghostapi.

This example demonstrates:
- Basic API creation
- Multiple route types (GET, POST)
- Function parameter handling

Run with: python examples/simple.py
"""

from ghostapi import expose


def hello():
    """Simple hello endpoint."""
    return {"message": "Hello World"}


def get_users():
    """Get list of users."""
    return [
        {"id": 1, "name": "John Doe", "email": "john@example.com"},
        {"id": 2, "name": "Jane Smith", "email": "jane@example.com"},
    ]


def get_user(user_id: int):
    """Get a specific user by ID."""
    return {"id": user_id, "name": f"User {user_id}", "email": f"user{user_id}@example.com"}


def create_user(name: str, email: str):
    """Create a new user."""
    return {
        "id": 999,
        "name": name,
        "email": email,
        "created": True
    }


def delete_user(user_id: int):
    """Delete a user."""
    return {"deleted": True, "user_id": user_id}


# Expose all functions as API endpoints
# This will automatically:
# - Create routes: GET /hello, GET /users, GET /user, POST /user, DELETE /user
# - Start server on http://127.0.0.1:8000
# - Generate Swagger docs at http://127.0.0.1:8000/docs
expose()
