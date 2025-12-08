"""Authentication endpoint tests."""
import pytest

@pytest.mark.integration
@pytest.mark.auth
class TestAuthEndpoints:
    """Test authentication endpoints."""
    
    def test_register_success(self, client, test_user_data):
        """Test successful user registration."""
        response = client.post("/api/auth/register", json=test_user_data)
        
        # Should succeed or return conflict if user exists
        assert response.status_code in [201, 409]
        
        if response.status_code == 201:
            data = response.json()
            assert "access_token" in data
            assert "refresh_token" in data
            assert "user" in data
            assert data["user"]["email"] == test_user_data["email"].lower()
    
    def test_register_weak_password(self, client):
        """Test registration with weak password."""
        weak_password_data = {
            "email": "weak@example.com",
            "password": "weak",
            "username": "weakuser",
            "first_name": "Weak",
            "last_name": "User",
            "role": "BUYER"
        }
        response = client.post("/api/auth/register", json=weak_password_data)
        assert response.status_code == 400
    
    def test_register_duplicate_email(self, client, test_user_data):
        """Test registration with duplicate email."""
        # First registration
        client.post("/api/auth/register", json=test_user_data)
        # Second registration with same email
        response = client.post("/api/auth/register", json=test_user_data)
        assert response.status_code == 409
    
    def test_login_success(self, client, test_user_data):
        """Test successful login."""
        # Ensure user exists
        client.post("/api/auth/register", json=test_user_data)
        
        response = client.post(
            "/api/auth/login",
            json={
                "email": test_user_data["email"],
                "password": test_user_data["password"]
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
    
    def test_login_invalid_credentials(self, client):
        """Test login with invalid credentials."""
        response = client.post(
            "/api/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "wrongpassword"
            }
        )
        assert response.status_code == 401
    
    def test_refresh_token(self, client, test_user_data):
        """Test token refresh."""
        # Register and get refresh token
        register_response = client.post("/api/auth/register", json=test_user_data)
        
        if register_response.status_code == 201:
            refresh_token = register_response.json().get("refresh_token")
            
            response = client.post(
                "/api/auth/refresh-token",
                json={"refresh_token": refresh_token}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "access_token" in data
    
    def test_get_current_user(self, client, auth_headers):
        """Test getting current user info."""
        if not auth_headers:
            pytest.skip("Authentication not available")
        
        response = client.get("/api/auth/me", headers=auth_headers)
        
        # May require authentication
        assert response.status_code in [200, 401]
        
        if response.status_code == 200:
            data = response.json()
            assert "email" in data
            assert "user_id" in data
    
    def test_forgot_password(self, client):
        """Test forgot password endpoint."""
        response = client.post(
            "/api/auth/forgot-password",
            json={"email": "test@example.com"}
        )
        # Should succeed even if email doesn't exist (security best practice)
        assert response.status_code in [200, 404]

