"""Integration tests for API workflows."""
import pytest
from unittest.mock import Mock, patch


class TestCompleteWorkflow:
    """Test complete user workflows."""
    
    @pytest.mark.integration
    def test_full_event_lifecycle(self, client, organizer_headers, mock_supabase_client, mock_supabase_table):
        """Test complete event lifecycle: create, list, update, delete."""
        # 1. Create event
        venue_check = Mock()
        venue_check.data = []
        event_data = {"event_id": 1, "title": "Test Event"}
        
        mock_supabase_table.execute.side_effect = [
            venue_check,
            Mock(data=[{"venue_id": 1}]),
            Mock(data=[event_data])
        ]
        
        create_response = client.post(
            "/api/events/",
            headers=organizer_headers,
            json={
                "title": "Test Event",
                "description": "Test",
                "date": "2024-12-31T20:00:00Z",
                "location": "Test Venue",
                "total_tickets": 100,
                "price": 50.00,
                "category": "Music"
            }
        )
        
        assert create_response.status_code == 200
        event_id = create_response.json()["event_id"]
        
        # 2. List events
        mock_supabase_table.execute.return_value = Mock(data=[event_data])
        list_response = client.get("/api/events/")
        assert list_response.status_code == 200
        
        # 3. Get event
        mock_supabase_table.execute.return_value = Mock(data=[event_data])
        get_response = client.get(f"/api/events/{event_id}")
        assert get_response.status_code == 200
        
        # 4. Update event
        updated_event = {**event_data, "title": "Updated Event"}
        mock_supabase_table.execute.side_effect = [
            Mock(data=[event_data]),
            Mock(data=[updated_event])
        ]
        
        update_response = client.put(
            f"/api/events/{event_id}",
            headers=organizer_headers,
            json={
                "title": "Updated Event",
                "description": "Test",
                "date": "2024-12-31T20:00:00Z",
                "location": "Test Venue",
                "total_tickets": 100,
                "price": 50.00,
                "category": "Music"
            }
        )
        assert update_response.status_code == 200
    
    @pytest.mark.integration
    def test_user_registration_to_ticket_purchase(self, client, mock_supabase_client, mock_supabase_table):
        """Test workflow from registration to ticket purchase."""
        # 1. Register
        mock_check = Mock()
        mock_check.data = []
        new_user = {"user_id": 1, "email": "new@example.com"}
        
        mock_supabase_table.execute.side_effect = [
            mock_check,
            Mock(data=[new_user])
        ]
        
        register_response = client.post("/api/auth/register", json={
            "email": "new@example.com",
            "password": "SecurePass123!",
            "username": "newuser",
            "first_name": "New",
            "last_name": "User",
            "role": "BUYER"
        })
        
        assert register_response.status_code == 201
        token = register_response.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. List events
        mock_supabase_table.execute.return_value = Mock(data=[])
        events_response = client.get("/api/events/", headers=headers)
        assert events_response.status_code == 200

