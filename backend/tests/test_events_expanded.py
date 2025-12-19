"""Comprehensive tests for events router."""
import pytest
from unittest.mock import Mock, patch


class TestEventsCreate:
    """Test event creation."""
    
    def test_create_event_success(self, client, organizer_headers, mock_supabase_client, test_venue, test_organizer):
        """Test successful event creation by organizer."""
        from main import app
        from auth_middleware import get_current_user
        
        # Override get_current_user to avoid DB call consuming mock side effect
        app.dependency_overrides[get_current_user] = lambda: test_organizer
        
        try:
            # Mock venue lookup (venue doesn't exist, then created)
            venue_check = Mock()
            venue_check.data = []
            
            venue_insert = Mock()
            venue_insert.data = [test_venue]
            
            event_insert = Mock()
            event_data = {
                "event_id": 1,
                "name": "Test Concert",
                "description": "A test event",
                "event_date": "2024-12-31T20:00:00Z",
                "venue_id": 1,
                "organizer_address": "0x2345678901234567890123456789012345678901",
                "total_supply": 100,
                "available_tickets": 100,
                "base_price": 50.00,
                "status": "UPCOMING",
                "created_at": "2024-01-01T00:00:00Z"
            }
            event_insert.data = [event_data]
            
            mock_table = mock_supabase_client.table.return_value
            # Use side_effect because multiple execute calls happen on the same mock object
            mock_table.execute.side_effect = [
                venue_check,
                venue_insert,
                event_insert
            ]
            
            with patch("routers.events.cache_clear"):
                response = client.post(
                    "/api/events/",
                    headers=organizer_headers,
                    json={
                        "name": "Test Concert",
                        "description": "A test event",
                        "date": "2024-12-31T20:00:00Z",
                        "location": "Test Venue, Test City",
                        "total_tickets": 100,
                        "price": 50.00,
                        "category": "Music"
                    }
                )
            
            assert response.status_code == 200
            assert response.json()["name"] == "Test Concert"
        finally:
            app.dependency_overrides = {}
    
    def test_create_event_existing_venue(self, client, organizer_headers, mock_supabase_client, test_venue, test_organizer):
        """Test event creation with existing venue."""
        from main import app
        from auth_middleware import get_current_user
        
        app.dependency_overrides[get_current_user] = lambda: test_organizer
        
        try:
            venue_check = Mock()
            venue_check.data = [test_venue]
            
            event_insert = Mock()
            # Provide COMPLETE event data to satisfy EventResponse validation
            event_insert.data = [{
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
            }]
            
            mock_table = mock_supabase_client.table.return_value
            # Use side_effect for sequential calls: 1. check venue, 2. insert event
            mock_table.execute.side_effect = [venue_check, event_insert]
            
            with patch("routers.events.cache_clear"):
                response = client.post(
                    "/api/events/",
                    headers=organizer_headers,
                    json={
                        "name": "Test Event",
                        "description": "Test",
                        "date": "2024-12-31T20:00:00Z",
                        "location": "Test Venue, Test City",
                        "total_tickets": 100,
                        "price": 50.00
                    }
                )
            
            assert response.status_code == 200
        finally:
            app.dependency_overrides = {}
    
    def test_create_event_unauthorized(self, client):
        """Test event creation without authentication."""
        response = client.post("/api/events/", json={
            "name": "Test Event",
            "description": "Test",
            "date": "2024-12-31T20:00:00Z",
            "location": "Test",
            "total_tickets": 100,
            "price": 50.00
        })
        
        # HTTPBearer raises 401 if no credentials (updated from 403)
        assert response.status_code == 401
    
    def test_create_event_not_organizer(self, client, auth_headers, test_user):
        """Test event creation by non-organizer."""
        from main import app
        from auth_middleware import get_current_user
        
        app.dependency_overrides[get_current_user] = lambda: test_user
        
        try:
            response = client.post(
                "/api/events/",
                headers=auth_headers,
                json={
                    "name": "Test Event",
                    "description": "Test",
                    "date": "2024-12-31T20:00:00Z",
                    "location": "Test",
                    "total_tickets": 100,
                    "price": 50.00
                }
            )
            
            assert response.status_code == 403
        finally:
            app.dependency_overrides = {}


class TestEventsList:
    """Test event listing."""
    
    def test_list_events_success(self, client, mock_supabase_client):
        """Test successful event listing."""
        mock_response = Mock()
        # Provide COMPLETE event data
        mock_response.data = [
            {
                "event_id": 1,
                "name": "Event 1",
                "description": "Description 1",
                "event_date": "2024-12-31T20:00:00Z",
                "venue_id": 1,
                "organizer_address": "0x123...",
                "total_supply": 100,
                "available_tickets": 100,
                "base_price": 50.00,
                "created_at": "2024-01-01T00:00:00Z"
            }
        ]
        
        venue_response = Mock()
        venue_response.data = [{"venue_id": 1, "name": "Venue 1", "location": "Loc 1", "city": "City 1"}]
        
        mock_table = mock_supabase_client.table.return_value
        # 1. List events, 2. Get venues (batch)
        mock_table.execute.side_effect = [mock_response, venue_response]
        
        # We need to mock the chain properly because list_events uses order().range().execute()
        # And get venues uses select().eq().limit().execute()
        # Since we added 'range' to chain_methods in conftest.py, this should work with side_effect
        
        response = client.get("/api/events/")
        
        assert response.status_code == 200
        assert len(response.json()) == 1
        assert response.json()[0]["name"] == "Event 1"
    
    def test_list_events_with_filters(self, client, mock_supabase_client):
        """Test event listing with filters."""
        mock_response = Mock()
        mock_response.data = []
        
        mock_table = mock_supabase_client.table.return_value
        mock_table.execute.return_value = mock_response
        
        response = client.get("/api/events/?category=Music")
        
        assert response.status_code == 200
        assert len(response.json()) == 0


class TestEventsGet:
    """Test getting single event."""
    
    def test_get_event_success(self, client, mock_supabase_client, test_event):
        """Test getting a single event."""
        mock_response = Mock()
        # Ensure test_event has all fields
        test_event["description"] = "Test Desc"
        test_event["organizer_address"] = "0x123..."
        mock_response.data = [test_event]
        
        venue_response = Mock()
        venue_response.data = [{"venue_id": 1, "name": "Venue 1", "location": "Loc 1", "city": "City 1"}]
        
        mock_table = mock_supabase_client.table.return_value
        # 1. Get event, 2. Get venue
        mock_table.execute.side_effect = [mock_response, venue_response]
        
        response = client.get("/api/events/1")
        
        assert response.status_code == 200
        assert response.json()["name"] == test_event["name"]
    
    def test_get_event_not_found(self, client, mock_supabase_client):
        """Test getting non-existent event."""
        mock_response = Mock()
        mock_response.data = []
        
        mock_table = mock_supabase_client.table.return_value
        mock_table.execute.return_value = mock_response
        
        response = client.get("/api/events/999")
        
        assert response.status_code == 404


class TestEventsOrganizer:
    """Test organizer event operations."""
    
    def test_get_organizer_events(self, client, organizer_headers, mock_supabase_client, test_event):
        """Test getting events by organizer address."""
        mock_response = Mock()
        test_event["description"] = "Test Desc"
        test_event["organizer_address"] = "0x2345678901234567890123456789012345678901"
        mock_response.data = [test_event]
        
        mock_table = mock_supabase_client.table.return_value
        mock_table.execute.return_value = mock_response
        
        response = client.get(
            "/api/events/organizer/0x2345678901234567890123456789012345678901",
            headers=organizer_headers
        )
        
        assert response.status_code == 200
        assert len(response.json()) == 1
    
    def test_get_organizer_stats(self, client, organizer_headers, mock_supabase_client, test_event):
        """Test getting organizer statistics."""
        mock_response = Mock()
        mock_response.data = [test_event]
        
        mock_table = mock_supabase_client.table.return_value
        mock_table.execute.return_value = mock_response
        
        response = client.get(
            "/api/events/organizer/0x2345678901234567890123456789012345678901/stats",
            headers=organizer_headers
        )
        
        assert response.status_code == 200
        stats = response.json()
        assert "total_revenue" in stats
        assert "tickets_sold" in stats
