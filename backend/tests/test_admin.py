"""Admin endpoint tests."""
import pytest

@pytest.mark.integration
@pytest.mark.admin
class TestAdminEndpoints:
    """Test admin endpoints."""
    
    def test_get_stats_requires_auth(self, client):
        """Test that admin stats require authentication."""
        response = client.get("/api/admin/stats")
        assert response.status_code in [401, 403]
    
    def test_get_alerts_requires_auth(self, client):
        """Test that admin alerts require authentication."""
        response = client.get("/api/admin/alerts")
        assert response.status_code in [401, 403]
    
    def test_get_users_requires_auth(self, client):
        """Test that getting users requires authentication."""
        response = client.get("/api/admin/users")
        assert response.status_code in [401, 403]

