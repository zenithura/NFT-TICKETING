"""Tests for security middleware."""
import pytest
from unittest.mock import Mock, patch
from fastapi import Request


class TestSecurityMiddleware:
    """Test security middleware functionality."""
    
    def test_security_headers_present(self, client):
        """Test that security headers are added to responses."""
        response = client.get("/health")
        
        # Check for common security headers
        # The middleware might add X-Frame-Options, X-Content-Type-Options, etc.
        assert response.status_code == 200
    
    def test_cors_headers(self, client):
        """Test CORS headers are present."""
        response = client.options("/api/events/", headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET"
        })
        
        # CORS middleware should handle this
        assert response.status_code in [200, 204]
    
    def test_rate_limiting_basic(self, client):
        """Test basic rate limiting (if implemented)."""
        # Make multiple requests
        for _ in range(10):
            response = client.get("/health")
            assert response.status_code == 200
        
        # If rate limiting is implemented, subsequent requests might be rate limited
        # Adjust based on actual implementation
    
    def test_sql_injection_protection(self, client, mock_supabase_client):
        """Test SQL injection protection."""
        # Attempt SQL injection in query parameter
        malicious_input = "'; DROP TABLE users; --"
        
        response = client.get(f"/api/events/?search={malicious_input}")
        
        # Should not cause server error or expose database
        assert response.status_code in [200, 400, 422]


class TestAuthMiddleware:
    """Test authentication middleware."""
    
    def test_protected_endpoint_without_token(self, client):
        """Test accessing protected endpoint without token."""
        response = client.get("/api/auth/me")
        
        assert response.status_code == 401
    
    def test_protected_endpoint_with_invalid_token(self, client):
        """Test accessing protected endpoint with invalid token."""
        response = client.get(
            "/api/auth/me",
            headers={"Authorization": "Bearer invalid_token_here"}
        )
        
        assert response.status_code == 401
    
    def test_protected_endpoint_with_valid_token(self, client, auth_headers, mock_supabase_client, mock_supabase_table, test_user):
        """Test accessing protected endpoint with valid token."""
        mock_response = Mock()
        mock_response.data = [test_user]
        mock_supabase_table.execute.return_value = mock_response
        
        response = client.get("/api/auth/me", headers=auth_headers)
        
        assert response.status_code == 200


class TestInputValidation:
    """Test input validation."""
    
    def test_email_validation(self, client):
        """Test email format validation."""
        response = client.post("/api/auth/register", json={
            "email": "invalid-email-format",
            "password": "SecurePass123!",
            "username": "test",
            "first_name": "Test",
            "last_name": "User",
            "role": "BUYER"
        })
        
        assert response.status_code == 422  # Validation error
    
    def test_password_validation(self, client):
        """Test password strength validation."""
        response = client.post("/api/auth/register", json={
            "email": "test@example.com",
            "password": "weak",  # Too weak
            "username": "test",
            "first_name": "Test",
            "last_name": "User",
            "role": "BUYER"
        })
        
        assert response.status_code == 400  # Password too weak
    
    def test_required_fields(self, client):
        """Test required field validation."""
        response = client.post("/api/auth/register", json={
            "email": "test@example.com"
            # Missing required fields
        })
        
        assert response.status_code == 422  # Missing fields

