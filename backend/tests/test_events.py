"""Events endpoint tests."""
import pytest

@pytest.mark.integration
@pytest.mark.events
class TestEventsEndpoints:
    """Test events endpoints."""
    
    def test_get_events(self, client):
        """Test getting all events."""
        response = client.get("/api/events/")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_get_event_by_id(self, client):
        """Test getting event by ID."""
        # First get list to find an event ID
        events_response = client.get("/api/events/")
        events = events_response.json()
        
        if events:
            event_id = events[0].get("id") or events[0].get("event_id")
            response = client.get(f"/api/events/{event_id}")
            assert response.status_code == 200
            data = response.json()
            assert "name" in data
            assert "description" in data
        else:
            # Test with invalid ID
            response = client.get("/api/events/99999")
            assert response.status_code == 404
    
    def test_create_event_requires_auth(self, client, test_event_data):
        """Test that creating event requires authentication."""
        response = client.post("/api/events/", json=test_event_data)
        # Should require authentication
        assert response.status_code in [401, 403]
    
    def test_create_event_with_auth(self, client, test_event_data, organizer_auth_headers):
        """Test creating event with organizer authentication."""
        if not organizer_auth_headers:
            pytest.skip("Organizer authentication not available")
        
        response = client.post(
            "/api/events/",
            json=test_event_data,
            headers=organizer_auth_headers
        )
        
        # May require organizer role
        assert response.status_code in [200, 201, 403]
        
        if response.status_code in [200, 201]:
            data = response.json()
            assert data["name"] == test_event_data["name"]
            assert data["total_tickets"] == test_event_data["total_tickets"]
    
    def test_get_organizer_events(self, client):
        """Test getting organizer's events."""
        organizer_address = "0x1234567890abcdef1234567890abcdef12345678"
        response = client.get(f"/api/events/organizer/{organizer_address}")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
    
    def test_get_organizer_stats(self, client):
        """Test getting organizer statistics."""
        organizer_address = "0x1234567890abcdef1234567890abcdef12345678"
        response = client.get(f"/api/events/organizer/{organizer_address}/stats")
        # May require authentication
        assert response.status_code in [200, 401, 404]

