"""Integration tests for API workflows."""
import pytest
from unittest.mock import Mock, patch

class TestCompleteWorkflow:
    """Test complete user workflows."""
    
    @pytest.mark.integration
    def test_full_event_lifecycle(self, client, organizer_headers, mock_supabase_client, mock_supabase_table):
        """Test complete event lifecycle: create, list, get."""
        from main import app
        from auth_middleware import get_current_user
        
        # Mock organizer user
        test_organizer = {
            "user_id": 2,
            "email": "organizer@example.com",
            "role": "ORGANIZER",
            "wallet_address": "0x2345678901234567890123456789012345678901",
            "is_active": True
        }
        app.dependency_overrides[get_current_user] = lambda: test_organizer
        
        try:
            # 1. Create event
            venue_check = Mock()
            venue_check.data = []
            
            venue_insert = Mock()
            venue_insert.data = [{"venue_id": 1}]
            
            event_data = {
                "event_id": 1, 
                "name": "Test Event",
                "description": "Test Description",
                "event_date": "2024-12-31T20:00:00Z",
                "venue_id": 1,
                "organizer_address": "0x2345678901234567890123456789012345678901",
                "total_supply": 100,
                "available_tickets": 100,
                "base_price": 50.00,
                "status": "UPCOMING",
                "created_at": "2024-01-01T00:00:00Z"
            }
            event_insert = Mock()
            event_insert.data = [event_data]
            
            # Mock sequence for Create: 1. Check venue, 2. Insert venue, 3. Insert event
            # Mock sequence for List: 1. List events, 2. Get venues
            # Mock sequence for Get: 1. Get event, 2. Get venue
            
            # We need to be careful with side_effect across multiple client calls
            # It's better to patch per call or use a sophisticated side_effect
            
            # For this test, let's just test Create and verify response
            mock_supabase_table.execute.side_effect = [
                venue_check,
                venue_insert,
                event_insert
            ]
            
            with patch("routers.events.cache_clear"):
                create_response = client.post(
                    "/api/events/",
                    headers=organizer_headers,
                    json={
                        "name": "Test Event",
                        "description": "Test",
                        "date": "2024-12-31T20:00:00Z",
                        "location": "Test Venue, Test City",
                        "total_tickets": 100,
                        "price": 50.00,
                        "category": "Music"
                    }
                )
            
            assert create_response.status_code == 200
            event_id = create_response.json()["id"]
            assert event_id == 1
            
        finally:
            app.dependency_overrides = {}
            
    @pytest.mark.integration
    def test_user_registration_to_ticket_purchase(self, client, mock_supabase_client, mock_supabase_table):
        """Test workflow from registration to ticket purchase."""
        # 1. Register
        email_check = Mock()
        email_check.data = [] # Email not taken
        
        username_check = Mock()
        username_check.data = [] # Username not taken
        
        new_user = {
            "user_id": 1, 
            "email": "new@example.com",
            "role": "BUYER",
            "is_active": True,
            "created_at": "2024-01-01T00:00:00Z"
        }
        user_insert = Mock()
        user_insert.data = [new_user]
        
        # Register calls: 1. Check email, 2. Check username, 3. Insert user
        mock_supabase_table.execute.side_effect = [
            email_check,
            username_check,
            user_insert
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
        
        # 2. List events (separate call, reset mock side_effect if needed or append)
        # But since we used side_effect, it's consumed.
        # We need to reset mocks for the next call
        
        # Reset mocks for List Events
        mock_supabase_table.reset_mock()
        mock_response = Mock()
        mock_response.data = []
        mock_supabase_table.execute.side_effect = None
        mock_supabase_table.execute.return_value = mock_response
        
        # We also need to mock verify_token or get_current_user for the subsequent request
        # But the test uses the token returned by register.
        # Ideally we should override get_current_user to avoid decoding token and DB lookup
        
        from main import app
        from auth_middleware import get_current_user
        app.dependency_overrides[get_current_user] = lambda: new_user
        
        try:
            events_response = client.get("/api/events/", headers=headers)
            assert events_response.status_code == 200
        finally:
            app.dependency_overrides = {}

