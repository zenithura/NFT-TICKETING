"""Tests for marketplace router."""
import pytest
from unittest.mock import Mock, patch


class TestMarketplaceList:
    """Test marketplace listing."""
    
    @patch("routers.marketplace.cache_get")
    def test_list_tickets_for_sale(self, mock_cache_get, client, mock_supabase_client, mock_supabase_table):
        """Test listing tickets available for resale."""
        mock_cache_get.return_value = None
        mock_response = Mock()
        mock_response.data = [
            {
                "id": 1,
                "ticket_id": 1,
                "seller_address": "0xSeller1",
                "price": 100.00,
                "status": "active",
                "original_price": 50.00,
                "created_at": "2024-01-01T00:00:00Z"
            },
            {
                "id": 2,
                "ticket_id": 2,
                "seller_address": "0xSeller2",
                "price": 150.00,
                "status": "active",
                "original_price": 75.00,
                "created_at": "2024-01-01T00:00:00Z"
            }
        ]
        mock_supabase_table.execute.return_value = mock_response
        
        response = client.get("/api/marketplace/")
        
        assert response.status_code == 200
        assert len(response.json()) == 2
    
    @patch("routers.marketplace.cache_get")
    def test_list_tickets_with_filters(self, mock_cache_get, client, mock_supabase_client, mock_supabase_table):
        """Test listing with status filter."""
        mock_cache_get.return_value = None
        mock_response = Mock()
        mock_response.data = [{
            "id": 1,
            "ticket_id": 1,
            "seller_address": "0xSeller1",
            "price": 100.00,
            "status": "active",
            "original_price": 50.00,
            "created_at": "2024-01-01T00:00:00Z"
        }]
        mock_supabase_table.execute.return_value = mock_response
        
        response = client.get("/api/marketplace/?status=active")
        
        assert response.status_code == 200
        assert len(response.json()) == 1


class TestMarketplaceCreateListing:
    """Test creating a listing."""
    
    def test_create_listing_success(self, client, auth_headers, mock_supabase_client, mock_supabase_table, test_ticket):
        """Test creating a new listing."""
        # Mock ticket lookup
        ticket_response = Mock()
        ticket_response.data = [{**test_ticket, "owner_address": "0xSeller", "status": "ACTIVE"}]
        
        # Mock listing insert
        listing_response = Mock()
        listing_response.data = [{
            "id": 1,
            "ticket_id": test_ticket["ticket_id"],
            "seller_address": "0xSeller",
            "price": 120.00,
            "status": "active",
            "original_price": 100.00,
            "created_at": "2024-01-01T00:00:00Z"
        }]
        
        mock_supabase_table.execute.side_effect = [
            ticket_response, # Check ticket ownership
            listing_response # Insert listing
        ]
        
        response = client.post(
            "/api/marketplace/",
            headers=auth_headers,
            json={
                "ticket_id": test_ticket["ticket_id"],
                "seller_address": "0xSeller",
                "price": 120.00,
                "original_price": 100.00
            }
        )
        
        assert response.status_code == 200
        assert response.json()["id"] == 1


class TestMarketplaceBlockchainList:
    """Test blockchain listing endpoint."""
    
    @patch("routers.marketplace.send_transaction")
    @patch("routers.marketplace.contracts")
    @patch("routers.marketplace.w3")
    def test_list_ticket_blockchain(self, mock_w3, mock_contracts, mock_send_tx, client, auth_headers, mock_supabase_client, mock_supabase_table):
        """Test listing a ticket via blockchain."""
        # Mock contract
        mock_contract = Mock()
        mock_contracts.get.return_value = mock_contract
        mock_contract.functions.listTicket.return_value = Mock()
        
        # Mock transaction result
        mock_send_tx.return_value = {"status": 1, "tx_hash": "0x123"}
        
        # Mock ticket lookup for owner
        ticket_response = Mock()
        ticket_response.data = [{"owner_address": "0xSeller"}]
        
        # Mock DB insert
        insert_response = Mock()
        insert_response.data = [{"id": 1}]
        
        mock_supabase_table.execute.side_effect = [
            ticket_response,
            insert_response
        ]
        
        response = client.post(
            "/api/marketplace/list",
            headers=auth_headers,
            json={
                "ticket_id": 1,
                "price": 0.5
            }
        )
        
        assert response.status_code == 200
        assert response.json()["status"] == 1


class TestMarketplaceBlockchainBuy:
    """Test blockchain buy endpoint."""
    
    @patch("routers.marketplace.send_transaction")
    @patch("routers.marketplace.contracts")
    def test_buy_ticket_blockchain(self, mock_contracts, mock_send_tx, client, auth_headers, mock_supabase_client, mock_supabase_table):
        """Test buying a ticket via blockchain."""
        # Mock contract
        mock_contract = Mock()
        mock_contracts.get.return_value = mock_contract
        mock_contract.functions.buyTicket.return_value = Mock()
        
        # Mock transaction result
        mock_send_tx.return_value = {"status": 1, "tx_hash": "0x123"}
        
        # Mock listing lookup
        listing_response = Mock()
        listing_response.data = [{"id": 1, "ticket_id": 1}]
        
        # Mock updates
        update_response = Mock()
        update_response.data = []
        
        mock_supabase_table.execute.side_effect = [
            listing_response,
            update_response, # Update listing
            update_response  # Update ticket
        ]
        
        response = client.post(
            "/api/marketplace/buy",
            headers=auth_headers,
            json={
                "ticket_id": 1,
                "value": 0.5
            }
        )
        
        assert response.status_code == 200
        assert response.json()["status"] == 1


class TestMarketplaceDelist:
    """Test delisting."""
    
    @patch("routers.marketplace.send_transaction")
    @patch("routers.marketplace.contracts")
    def test_delist_ticket(self, mock_contracts, mock_send_tx, client, auth_headers, mock_supabase_client, mock_supabase_table):
        """Test delisting a ticket."""
        # Mock contract
        mock_contract = Mock()
        mock_contracts.get.return_value = mock_contract
        # Try cancelListing first (as per implementation logic)
        mock_contract.functions.cancelListing.return_value = Mock()
        
        # Mock transaction result
        mock_send_tx.return_value = {"status": 1, "tx_hash": "0x123"}
        
        # Mock DB update
        update_response = Mock()
        update_response.data = []
        mock_supabase_table.execute.return_value = update_response
        
        response = client.post(
            "/api/marketplace/delist",
            headers=auth_headers,
            json={"ticket_id": 1}
        )
        
        assert response.status_code == 200
        assert response.json()["status"] == 1

