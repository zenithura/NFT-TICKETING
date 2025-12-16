"""Tests for events router."""
import pytest
from unittest.mock import Mock, patch


class TestEventsCreate:
    """Test event creation."""
    
    def test_create_event_success(self, client, organizer_headers, mock_supabase_client, mock_supabase_table, test_organizer):
        """Test successful event creation by organizer."""
        # Mock venue lookup (venue doesn't exist)
        venue_check = Mock()
        venue_check.data = []
        mock_supabase_table.execute.side_effect = [
            venue_check,  # Venue lookup
            Mock(data=[{"venue_id": 1}]),  # Venue insert
            Mock(data=[{"event_id": 1}])   # Event insert
        ]
        
        response = client.post(
            "/api/events/",
            headers=organizer_headers,
            json={
                "title": "Test Concert",
                "description": "A test event",
                "date": "2024-12-31T20:00:00Z",
                "location": "Test Venue, Test City",
                "total_tickets": 100,
                "price": 50.00,
                "category": "Music"
            }
        )
        
        assert response.status_code == 200
        assert response.json()["title"] == "Test Concert"
    
    def test_create_event_unauthorized(self, client):
        """Test event creation without authentication."""
        response = client.post("/api/events/", json={
            "title": "Test Event",
            "description": "Test",
            "date": "2024-12-31T20:00:00Z",
            "location": "Test",
            "total_tickets": 100,
            "price": 50.00,
            "category": "Music"
        })
        
        assert response.status_code == 401
    
    def test_create_event_not_organizer(self, client, auth_headers):
        """Test event creation by non-organizer."""
        response = client.post(
            "/api/events/",
            headers=auth_headers,
            json={
                "title": "Test Event",
                "description": "Test",
                "date": "2024-12-31T20:00:00Z",
                "location": "Test",
                "total_tickets": 100,
                "price": 50.00,
                "category": "Music"
            }
        )
        
        assert response.status_code == 403


class TestEventsList:
    """Test event listing."""
    
    def test_list_events_success(self, client, mock_supabase_client, mock_supabase_table):
        """Test successful event listing."""
        mock_response = Mock()
        mock_response.data = [
            {
                "event_id": 1,
                "title": "Event 1",
                "date": "2024-12-31T20:00:00Z",
                "total_tickets": 100,
                "price": 50.00
            },
            {
                "event_id": 2,
                "title": "Event 2",
                "date": "2024-12-31T21:00:00Z",
                "total_tickets": 200,
                "price": 75.00
            }
        ]
        mock_supabase_table.execute.return_value = mock_response
        
        response = client.get("/api/events/")
        
        assert response.status_code == 200
        assert len(response.json()) == 2
    
    def test_list_events_with_category_filter(self, client, mock_supabase_client, mock_supabase_table):
        """Test event listing with category filter."""
        mock_response = Mock()
        mock_response.data = [{"event_id": 1, "title": "Music Event", "category": "Music"}]
        mock_supabase_table.execute.return_value = mock_response
        
        response = client.get("/api/events/?category=Music")
        
        assert response.status_code == 200
        assert len(response.json()) == 1
    
    def test_list_events_empty(self, client, mock_supabase_client, mock_supabase_table):
        """Test event listing when no events exist."""
        mock_response = Mock()
        mock_response.data = []
        mock_supabase_table.execute.return_value = mock_response
        
        response = client.get("/api/events/")
        
        assert response.status_code == 200
        assert response.json() == []


class TestEventsGet:
    """Test getting single event."""
    
    def test_get_event_success(self, client, mock_supabase_client, mock_supabase_table, test_event):
        """Test successful event retrieval."""
        mock_response = Mock()
        mock_response.data = [test_event]
        mock_supabase_table.execute.return_value = mock_response
        
        response = client.get(f"/api/events/{test_event['event_id']}")
        
        assert response.status_code == 200
        assert response.json()["event_id"] == test_event["event_id"]
        assert response.json()["title"] == test_event["title"]
    
    def test_get_event_not_found(self, client, mock_supabase_client, mock_supabase_table):
        """Test getting non-existent event."""
        mock_response = Mock()
        mock_response.data = []
        mock_supabase_table.execute.return_value = mock_response
        
        response = client.get("/api/events/999")
        
        assert response.status_code == 404


class TestEventsUpdate:
    """Test event updates."""
    
    def test_update_event_success(self, client, organizer_headers, mock_supabase_client, mock_supabase_table, test_event):
        """Test successful event update."""
        # Mock get event
        get_response = Mock()
        get_response.data = [test_event]
        
        # Mock update
        update_response = Mock()
        update_response.data = [{**test_event, "title": "Updated Title"}]
        
        mock_supabase_table.execute.side_effect = [
            get_response,
            update_response
        ]
        
        response = client.put(
            f"/api/events/{test_event['event_id']}",
            headers=organizer_headers,
            json={
                "title": "Updated Title",
                "description": test_event["description"],
                "date": test_event["date"],
                "location": test_event["location"],
                "total_tickets": test_event["total_tickets"],
                "price": test_event["price"],
                "category": test_event["category"]
            }
        )
        
        assert response.status_code == 200
        assert response.json()["title"] == "Updated Title"
    
    def test_update_event_unauthorized(self, client, test_event):
        """Test event update without authentication."""
        response = client.put(f"/api/events/{test_event['event_id']}", json={
            "title": "Updated"
        })
        
        assert response.status_code == 401


class TestEventsDelete:
    """Test event deletion."""
    
    def test_delete_event_success(self, client, organizer_headers, mock_supabase_client, mock_supabase_table, test_event):
        """Test successful event deletion."""
        mock_response = Mock()
        mock_response.data = [test_event]
        mock_supabase_table.execute.return_value = mock_response
        
        response = client.delete(
            f"/api/events/{test_event['event_id']}",
            headers=organizer_headers
        )
        
        assert response.status_code == 200
    
    def test_delete_event_not_owner(self, client, auth_headers, mock_supabase_client, mock_supabase_table, test_event):
        """Test deleting event not owned by user."""
        mock_response = Mock()
        mock_response.data = [test_event]  # Event owned by different user
        mock_supabase_table.execute.return_value = mock_response
        
        response = client.delete(
            f"/api/events/{test_event['event_id']}",
            headers=auth_headers
        )
        
        assert response.status_code == 403

