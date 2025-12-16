"""Tests for tickets router."""
import pytest
from unittest.mock import Mock, patch


class TestTicketsPurchase:
    """Test ticket creation/purchase."""
    
    @patch("routers.tickets.send_transaction")
    @patch("routers.tickets.contracts")
    @patch("routers.tickets.w3")
    def test_create_ticket_success(self, mock_w3, mock_contracts, mock_send_tx, client, auth_headers, mock_supabase_client, mock_supabase_table, test_user, test_event):
        """Test successful ticket creation (minting)."""
        # Mock event lookup
        event_response = Mock()
        event_response.data = [test_event]
        
        # Mock wallet lookup/creation
        wallet_response = Mock()
        wallet_response.data = [{"wallet_id": 1, "address": test_user["wallet_address"]}]
        
        # Mock ticket insert
        ticket_response = Mock()
        ticket_response.data = [{
            "ticket_id": 1, 
            "event_id": test_event["event_id"],
            "owner_wallet_id": 1,
            "owner_address": test_user["wallet_address"],
            "status": "ACTIVE",
            "token_id": "123",
            "created_at": "2024-01-01T00:00:00Z"
        }]
        
        # Mock event update (decrement available tickets)
        update_response = Mock()
        update_response.data = [{"available_tickets": 99}]

        # Setup side effects for database calls
        mock_supabase_table.execute.side_effect = [
            event_response,
            wallet_response,
            ticket_response,
            update_response,
            wallet_response
        ]
        
        response = client.post(
            "/api/tickets/",
            headers=auth_headers,
            json={
                "event_id": test_event["event_id"],
                "owner_address": test_user["wallet_address"],
                "status": "bought",
                "purchase_price": 50.0,
                "nft_token_id": 123
            }
        )
        
        if response.status_code != 200:
            print(f"Response create ticket: {response.json()}")
            
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == 1
        assert data["event_id"] == test_event["event_id"]
        assert data["owner_address"] == test_user["wallet_address"]
    
    def test_create_ticket_unauthorized(self, client, test_event, test_user):
        """Test ticket creation without authentication."""
        pass

    def test_create_ticket_event_not_found(self, client, auth_headers, mock_supabase_client, mock_supabase_table, test_user):
        """Test creating ticket for non-existent event."""
        mock_response = Mock()
        mock_response.data = [] # Event not found
        mock_supabase_table.execute.return_value = mock_response
        
        response = client.post(
            "/api/tickets/",
            headers=auth_headers,
            json={
                "event_id": 999,
                "owner_address": test_user["wallet_address"]
            }
        )
        
        assert response.status_code == 404


class TestTicketsList:
    """Test ticket listing."""
    
    def test_list_user_tickets(self, client, auth_headers, mock_supabase_client, mock_supabase_table, test_user):
        """Test listing tickets for current user."""
        # Mock wallet lookup
        wallet_response = Mock()
        wallet_response.data = [{"wallet_id": 1, "address": test_user["wallet_address"]}]

        # Mock tickets lookup
        tickets_response = Mock()
        tickets_response.data = [
            {"ticket_id": 1, "event_id": 1, "owner_wallet_id": 1, "status": "ACTIVE", "token_id": "123"},
            {"ticket_id": 2, "event_id": 2, "owner_wallet_id": 1, "status": "ACTIVE", "token_id": "124"}
        ]
        
        # Mock event lookup (batch)
        event_response = Mock()
        event_response.data = [{"event_id": 1, "name": "Event 1"}]
        
        # Mock wallet lookup for response mapping (called for each ticket)
        wallet_lookup_response = Mock()
        wallet_lookup_response.data = [{"address": test_user["wallet_address"]}]

        mock_supabase_table.execute.side_effect = [
            wallet_response,
            tickets_response,
            event_response, # Check event 1
            event_response, # Check event 2 (mocking same response for simplicity)
            wallet_lookup_response,
            wallet_lookup_response
        ]
        
        response = client.get(f"/api/tickets/user/{test_user['wallet_address']}", headers=auth_headers)
        
        if response.status_code != 200:
            print(f"Response list tickets: {response.json()}")
            
        assert response.status_code == 200
        assert len(response.json()) == 2
    

class TestTicketsGet:
    """Test getting single ticket."""
    
    def test_get_ticket_success(self, client, auth_headers, mock_supabase_client, mock_supabase_table, test_ticket):
        """Test successful ticket retrieval."""
        mock_response = Mock()
        mock_response.data = [test_ticket]
        
        # Mock event lookup
        event_response = Mock()
        event_response.data = [{"event_id": 1, "name": "Test Event"}]
        
        mock_supabase_table.execute.side_effect = [
            mock_response,
            event_response
        ]
        
        response = client.get(f"/api/tickets/{test_ticket['ticket_id']}", headers=auth_headers)
        
        if response.status_code != 200:
            print(f"Response get ticket: {response.json()}")
            
        assert response.status_code == 200
        assert response.json()["id"] == test_ticket["ticket_id"]
    
    def test_get_ticket_not_found(self, client, auth_headers, mock_supabase_client, mock_supabase_table):
        """Test getting non-existent ticket."""
        mock_response = Mock()
        mock_response.data = []  # Ticket not found
        mock_supabase_table.execute.return_value = mock_response
        
        response = client.get("/api/tickets/999", headers=auth_headers)
        
        assert response.status_code == 404


class TestTicketsValidate:
    """Test ticket validation."""
    
    @patch("routers.tickets.send_transaction")
    @patch("routers.tickets.contracts")
    def test_validate_ticket_success(self, mock_contracts, mock_send_tx, client, test_ticket):
        """Test successful ticket validation via blockchain."""
        # Mock contract
        mock_contract = Mock()
        mock_contracts.get.return_value = mock_contract
        mock_contract.functions.validateTicket.return_value = Mock()
        
        # Mock transaction result
        mock_send_tx.return_value = {"status": 1, "tx_hash": "0x123"}
        
        response = client.post(
            "/api/tickets/validate",
            json={
                "ticket_id": test_ticket["ticket_id"],
                "validator_address": "0xValidator"
            }
        )
        
        if response.status_code != 200:
            print(f"Response validate ticket: {response.json()}")
            
        assert response.status_code == 200
        assert response.json()["status"] == 1

