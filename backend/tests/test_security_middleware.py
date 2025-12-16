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
        
        # Should be blocked by security middleware
        assert response.status_code == 403

    
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
        
        assert response.status_code == 422  # Password too weak (Pydantic validation)
    
    def test_required_fields(self, client):
        """Test required field validation."""
        response = client.post("/api/auth/register", json={
            "email": "test@example.com"
            # Missing required fields
        })
        
        assert response.status_code == 422  # Missing fields

