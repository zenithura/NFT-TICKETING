"""Wallet endpoint tests."""
import pytest

@pytest.mark.integration
class TestWalletEndpoints:
    """Test wallet endpoints."""
    
    def test_connect_wallet(self, client):
        """Test wallet connection endpoint."""
        wallet_data = {
            "address": "0x1234567890abcdef1234567890abcdef12345678",
            "provider": "metamask"
        }
        response = client.post("/api/wallet/connect", json=wallet_data)
        # Should always succeed (graceful degradation)
        assert response.status_code in [200, 201]
        data = response.json()
        assert "success" in data or "message" in data

