"""Tickets endpoint tests."""
import pytest

@pytest.mark.integration
@pytest.mark.tickets
class TestTicketsEndpoints:
    """Test tickets endpoints."""
    
    def test_get_server_address(self, client):
        """Test getting server wallet address."""
        response = client.get("/api/tickets/server-address")
        assert response.status_code == 200
        data = response.json()
        assert "address" in data
    
    def test_get_user_tickets(self, client):
        """Test getting user's tickets."""
        owner_address = "0x1234567890abcdef1234567890abcdef12345678"
        response = client.get(f"/api/tickets/user/{owner_address}")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_get_event_tickets(self, client):
        """Test getting tickets for an event."""
        # First get an event ID
        events_response = client.get("/api/events/")
        events = events_response.json()
        
        if events:
            event_id = events[0].get("id") or events[0].get("event_id")
            response = client.get(f"/api/tickets/event/{event_id}")
            assert response.status_code == 200
            assert isinstance(response.json(), list)
        else:
            response = client.get("/api/tickets/event/99999")
            assert response.status_code in [200, 404]
    
    def test_get_ticket_by_id(self, client):
        """Test getting ticket by ID."""
        # Try with a test ID
        response = client.get("/api/tickets/1")
        # May succeed or return 404
        assert response.status_code in [200, 404]
        
        if response.status_code == 200:
            data = response.json()
            assert "ticket_id" in data or "id" in data
    
    def test_create_ticket_requires_data(self, client):
        """Test that creating ticket requires valid data."""
        response = client.post("/api/tickets/", json={})
        assert response.status_code in [400, 422]

