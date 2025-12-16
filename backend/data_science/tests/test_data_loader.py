"""Unit tests for DataLoader class."""
import pytest
from unittest.mock import Mock, MagicMock
from data_science.data_loader import DataLoader


class TestDataLoader:
    """Test suite for DataLoader."""
    
    @pytest.fixture
    def mock_supabase(self):
        """Create a mock Supabase client."""
        mock_client = Mock()
        mock_table = Mock()
        mock_client.table.return_value = mock_table
        return mock_client, mock_table
    
    @pytest.fixture
    def data_loader(self, mock_supabase):
        """Create DataLoader instance with mock client."""
        mock_client, _ = mock_supabase
        return DataLoader(mock_client)
    
    def test_initialization(self, data_loader, mock_supabase):
        """Test DataLoader initializes correctly."""
        mock_client, _ = mock_supabase
        assert data_loader.db == mock_client
    
    def test_fetch_transaction_history(self, data_loader, mock_supabase):
        """Test fetching transaction history."""
        _, mock_table = mock_supabase
        
        # Setup mock response
        mock_response = Mock()
        mock_response.data = [
            {"id": "tx1", "amount": 100, "user_id": "user1"},
            {"id": "tx2", "amount": 200, "user_id": "user2"}
        ]
        
        mock_table.select.return_value = mock_table
        mock_table.gte.return_value = mock_table
        mock_table.order.return_value = mock_table
        mock_table.limit.return_value = mock_table
        mock_table.execute.return_value = mock_response
        
        # Test
        result = data_loader.fetch_transaction_history(limit=10)
        
        assert len(result) == 2
        assert result[0]["id"] == "tx1"
        assert result[1]["amount"] == 200
    
    def test_fetch_user_behavior(self, data_loader, mock_supabase):
        """Test fetching user behavior."""
        _, mock_table = mock_supabase
        
        mock_response = Mock()
        mock_response.data = [{"id": "user1", "name": "Test User"}]
        
        mock_table.select.return_value = mock_table
        mock_table.limit.return_value = mock_table
        mock_table.execute.return_value = mock_response
        
        result = data_loader.fetch_user_behavior(limit=10)
        
        assert len(result) == 1
        assert result[0]["id"] == "user1"
    
    def test_save_prediction(self, data_loader, mock_supabase):
        """Test saving prediction."""
        _, mock_table = mock_supabase
        
        mock_table.insert.return_value = mock_table
        mock_table.execute.return_value = Mock()
        
        result = data_loader.save_prediction(
            model_name="test_model",
            input_data={"x": 1},
            output=0.5,
            confidence=0.9,
            latency_ms=10.5
        )
        
        assert result == True
        mock_table.insert.assert_called_once()
    
    def test_save_model_metrics(self, data_loader, mock_supabase):
        """Test saving model metrics."""
        _, mock_table = mock_supabase
        
        mock_table.insert.return_value = mock_table
        mock_table.execute.return_value = Mock()
        
        result = data_loader.save_model_metrics(
            model_name="test_model",
            metrics={"accuracy": 0.95, "precision": 0.92}
        )
        
        assert result == True
        mock_table.insert.assert_called_once()
    
    def test_get_user_transaction_stats(self, data_loader, mock_supabase):
        """Test getting user transaction statistics."""
        _, mock_table = mock_supabase
        
        mock_response = Mock()
        mock_response.data = [
            {"amount": 100},
            {"amount": 200},
            {"amount": 150}
        ]
        
        mock_table.select.return_value = mock_table
        mock_table.eq.return_value = mock_table
        mock_table.execute.return_value = mock_response
        
        stats = data_loader.get_user_transaction_stats("user1")
        
        assert stats["count"] == 3
        assert stats["avg_amount"] == 150.0
        assert stats["total_amount"] == 450
        assert stats["max_amount"] == 200
        assert stats["min_amount"] == 100
    
    def test_error_handling(self, data_loader, mock_supabase):
        """Test error handling in fetch methods."""
        _, mock_table = mock_supabase
        
        # Simulate error
        mock_table.select.side_effect = Exception("Database error")
        
        # Should return empty list on error
        result = data_loader.fetch_transaction_history()
        assert result == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
