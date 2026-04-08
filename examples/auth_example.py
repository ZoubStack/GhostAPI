"""Authentication example for ghostapi.

This example demonstrates:
- Enabling JWT authentication
- Registering users
- Logging in
- Accessing protected endpoints
- Role-based access control

Run with: python examples/auth_example.py

Then test with:
1. Register: POST /api/auth/register {"email": "test@test.com", "password": "pass123"}
2. Login: POST /api/auth/login (form data: username=test@test.com, password=pass123)
3. Use token to access protected endpoints
"""

from ghostapi import expose, create_api, add_routes
from ghostapi.auth import enable_auth, create_test_user


# Public endpoint - no authentication required
def get_public_info():
    """Public information that anyone can access."""
    return {
        "message": "This is public information",
        "version": "1.0.0"
    }


# Protected endpoint - requires authentication
def get_user_profile():
    """Get the current user's profile."""
    return {
        "id": 1,
        "name": "John Doe",
        "email": "john@example.com",
        "role": "user"
    }


# Admin only endpoint
def get_all_users():
    """Get all users (admin only)."""
    return [
        {"id": 1, "name": "Admin", "role": "admin"},
        {"id": 2, "name": "User", "role": "user"},
    ]


# Another protected endpoint
def get_secret_data():
    """Secret data that requires authentication."""
    return {
        "secret": "This is sensitive data",
        "access_level": "authenticated"
    }


# Create API with authentication enabled
# This adds:
# - POST /api/auth/register
# - POST /api/auth/login
# - GET /api/auth/me
# - Auth middleware that validates JWT tokens

app = create_api(auth=True)

# Add routes
# With auth=True, all routes will require authentication
add_routes(app, {
    "get_public_info": get_public_info,
    "get_user_profile": get_user_profile,
    "get_all_users": get_all_users,
    "get_secret_data": get_secret_data,
})

# Create a test user for demonstration
create_test_user("admin@example.com", "admin123", role="admin")
create_test_user("user@example.com", "user123", role="user")

print("\n" + "="*50)
print("🔐 GhostAPI Authentication Example")
print("="*50)
print("\nTest users created:")
print("  - admin@example.com / admin123 (role: admin)")
print("  - user@example.com / user123 (role: user)")
print("\nAPI available at: http://127.0.0.1:8000")
print("Swagger docs at: http://127.0.0.1:8000/docs")
print("\nTo test authentication:")
print("  1. POST /api/auth/login with form data:")
print("       username=user@example.com")
print("       password=user123")
print("  2. Copy the access_token")
print("  3. Add header: Authorization: Bearer <token>")
print("="*50 + "\n")

# Start the server
import uvicorn
uvicorn.run(app, host="127.0.0.1", port=8000)
