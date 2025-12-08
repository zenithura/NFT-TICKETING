"""Marketplace endpoint tests."""
import pytest

@pytest.mark.integration
@pytest.mark.marketplace
class TestMarketplaceEndpoints:
    """Test marketplace endpoints."""
    
    def test_get_listings(self, client):
        """Test getting all marketplace listings."""
        response = client.get("/api/marketplace/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_get_listing_by_id(self, client):
        """Test getting listing by ID."""
        # Try with a test ID
        response = client.get("/api/marketplace/1")
        # May succeed or return 404
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert "listing_id" in data or "id" in data
    
    def test_get_seller_listings(self, client):
        """Test getting seller's listings."""
        seller_address = "0x1234567890abcdef1234567890abcdef12345678"
        response = client.get(f"/api/marketplace/seller/{seller_address}")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_create_listing_requires_data(self, client):
        """Test that creating listing requires valid data."""
        response = client.post("/api/marketplace/", json={})
        assert response.status_code in [400, 422]

