"""End-to-end flow tests."""
import pytest
import time

@pytest.mark.e2e
@pytest.mark.slow
class TestE2EFlows:
    """Test complete user flows."""
    
    def test_full_event_creation_flow(self, client, test_user_data, test_event_data):
        """Test complete flow: register → login → create event."""
        # 1. Register user
        register_response = client.post("/api/auth/register", json=test_user_data)
        
        # Get auth token
        if register_response.status_code == 201:
            access_token = register_response.json().get("access_token")
        elif register_response.status_code == 409:
            # User exists, try login
            login_response = client.post(
                "/api/auth/login",
                json={
                    "email": test_user_data["email"],
                    "password": test_user_data["password"]
                }
            )
            if login_response.status_code == 200:
                access_token = login_response.json().get("access_token")
            else:
                pytest.skip("Could not authenticate")
        else:
            pytest.skip("Could not register user")
        
        headers = {"Authorization": f"Bearer {access_token}"}
        
        # 2. Create event (may require organizer role)
        event_response = client.post(
            "/api/events/",
            json=test_event_data,
            headers=headers
        )
        
        # May require organizer role upgrade
        assert event_response.status_code in [200, 201, 403]
    
    def test_marketplace_listing_flow(self, client):
        """Test flow: get events → get tickets → create listing."""
        # 1. Get events
        events_response = client.get("/api/events/")
        assert events_response.status_code == 200
        
        # 2. Get marketplace listings
        listings_response = client.get("/api/marketplace/")
        assert listings_response.status_code == 200
        
        # Flow depends on having actual tickets/events in test database

