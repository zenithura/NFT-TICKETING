"""Comprehensive tests for events router."""
import pytest
from unittest.mock import Mock, patch


class TestEventsCreate:
    """Test event creation."""
    
    def test_create_event_success(self, client, organizer_headers, mock_supabase_client, test_venue):
        """Test successful event creation by organizer."""
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
        mock_table.select.return_value.eq.return_value.eq.return_value.execute.side_effect = [
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
    
    def test_create_event_existing_venue(self, client, organizer_headers, mock_supabase_client, test_venue):
        """Test event creation with existing venue."""
        venue_check = Mock()
        venue_check.data = [test_venue]
        
        event_insert = Mock()
        event_insert.data = [{"event_id": 1, "name": "Test", "created_at": "2024-01-01T00:00:00Z"}]
        
        mock_table = mock_supabase_client.table.return_value
        mock_table.select.return_value.eq.return_value.eq.return_value.execute.return_value = venue_check
        mock_table.insert.return_value.execute.return_value = event_insert
        
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
        
        assert response.status_code == 401
    
    def test_create_event_not_organizer(self, client, auth_headers):
        """Test event creation by non-organizer."""
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


class TestEventsList:
    """Test event listing."""
    
    def test_list_events_success(self, client, mock_supabase_client):
        """Test successful event listing."""
        mock_response = Mock()
        mock_response.data = [
            {
                "event_id": 1,
                "name": "Event 1",
                "event_date": "2024-12-31T20:00:00Z",
                "total_supply": 100,
                "base_price": 50.00,
                "created_at": "2024-01-01T00:00:00Z"
            }
        ]
        
        mock_table = mock_supabase_client.table.return_value
        mock_table.select.return_value.execute.return_value = mock_response
        
        response = client.get("/api/events/")
        
        assert response.status_code == 200
        assert len(response.json()) >= 1
    
    def test_list_events_with_filters(self, client, mock_supabase_client):
        """Test event listing with filters."""
        mock_response = Mock()
        mock_response.data = []
        
        mock_table = mock_supabase_client.table.return_value
        mock_table.select.return_value.eq.return_value.execute.return_value = mock_response
        
        response = client.get("/api/events/?category=Music")
        
        assert response.status_code == 200


class TestEventsGet:
    """Test getting single event."""
    
    def test_get_event_success(self, client, mock_supabase_client, test_event):
        """Test successful event retrieval."""
        mock_response = Mock()
        mock_response.data = [test_event]
        
        mock_table = mock_supabase_client.table.return_value
        mock_table.select.return_value.eq.return_value.execute.return_value = mock_response
        
        response = client.get(f"/api/events/{test_event['event_id']}")
        
        assert response.status_code == 200
        assert response.json()["id"] == test_event["event_id"]
    
    def test_get_event_not_found(self, client, mock_supabase_client):
        """Test getting non-existent event."""
        mock_response = Mock()
        mock_response.data = []
        
        mock_table = mock_supabase_client.table.return_value
        mock_table.select.return_value.eq.return_value.execute.return_value = mock_response
        
        response = client.get("/api/events/999")
        
        assert response.status_code == 404


class TestEventsOrganizer:
    """Test organizer-specific endpoints."""
    
    def test_get_organizer_events(self, client, organizer_headers, mock_supabase_client):
        """Test getting events by organizer address."""
        mock_response = Mock()
        mock_response.data = [{"event_id": 1, "name": "Event 1"}]
        
        mock_table = mock_supabase_client.table.return_value
        mock_table.select.return_value.eq.return_value.execute.return_value = mock_response
        
        response = client.get(
            "/api/events/organizer/0x2345678901234567890123456789012345678901",
            headers=organizer_headers
        )
        
        assert response.status_code == 200
    
    def test_get_organizer_stats(self, client, organizer_headers, mock_supabase_client):
        """Test getting organizer statistics."""
        events_mock = Mock()
        events_mock.data = [
            {"total_supply": 100, "available_tickets": 50},
            {"total_supply": 200, "available_tickets": 100}
        ]
        
        mock_table = mock_supabase_client.table.return_value
        mock_table.select.return_value.eq.return_value.execute.return_value = events_mock
        
        response = client.get(
            "/api/events/organizer/0x2345678901234567890123456789012345678901/stats",
            headers=organizer_headers
        )
        
        assert response.status_code == 200

