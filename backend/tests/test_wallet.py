"""Tests for wallet router."""
import pytest
from unittest.mock import Mock, patch


class TestWalletConnect:
    """Test wallet connection."""
    
    def test_connect_wallet_success(self, client, auth_headers, mock_supabase_client, mock_supabase_table, test_user):
        """Test successful wallet connection."""
        # Mock user lookup
        user_response = Mock()
        user_response.data = [test_user]
        
        mock_supabase_table.execute.side_effect = [
            user_response
        ]
        
        wallet_address = "0x1234567890123456789012345678901234567890"
        response = client.post(
            "/api/wallet/connect",
            json={"address": wallet_address}
        )
        
        if response.status_code != 200:
            print(f"Response success: {response.json()}")
            
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert response.json()["user"]["wallet_address"] == test_user["wallet_address"]

    def test_connect_wallet_new_user(self, client, mock_supabase_client, mock_supabase_table):
        """Test wallet connection for new user (no account)."""
        # Mock user lookup (empty)
        user_response = Mock()
        user_response.data = []
        
        # Mock for the update operation that creates the new user
        update_response = Mock()
        update_response.data = [{"address": "0xnewuseraddress"}] # Simulate a successful insert/update
        
        mock_supabase_table.execute.side_effect = [
            user_response,
            update_response
        ]
        
        wallet_address = "0xNewUserAddress"
        response = client.post(
            "/api/wallet/connect",
            json={"address": wallet_address}
        )
        
        if response.status_code != 200:
            print(f"Response new user: {response.json()}")
        
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert response.json()["address"] == wallet_address.lower()

