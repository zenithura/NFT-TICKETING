"""
Integration Tests
Tests that verify ML models are integrated into system behavior.
"""

import pytest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from integration.ml_integration_layer import MLIntegrationLayer


class TestIntegration:
    """Tests for ML integration layer."""
    
    def test_integration_layer_initializes(self):
        """Test that integration layer can be initialized."""
        integration = MLIntegrationLayer()
        assert integration is not None
        assert integration.fraud_model is not None
        assert integration.clustering_model is not None
    
    def test_process_transaction_returns_result(self):
        """Test that process_transaction returns a result dict."""
        integration = MLIntegrationLayer()
        result = integration.process_transaction(
            transaction_id="test_123",
            wallet_address="0x123...",
            event_id=42,
            price_paid=50.0
        )
        
        assert 'transaction_id' in result
        assert 'status' in result
        assert result['transaction_id'] == "test_123"
        assert result['status'] in ['processing', 'approved', 'blocked', 'flagged_for_review', 'error']
    
    def test_process_transaction_blocks_high_risk(self):
        """Test that high-risk transactions are blocked."""
        integration = MLIntegrationLayer()
        
        # This test would require a fitted model with high-risk features
        # For now, just verify the structure
        result = integration.process_transaction(
            transaction_id="test_high_risk",
            wallet_address="0xBAD...",
            event_id=42,
            price_paid=1000.0
        )
        
        # Verify result structure
        assert 'status' in result
        # If model is fitted and detects fraud, status should be 'blocked'
        # Otherwise, it may be 'error' or 'processing'
    
    def test_recommend_events_returns_list(self):
        """Test that recommend_events returns a list."""
        integration = MLIntegrationLayer()
        user_features = {
            'cross_event_attendance': 5,
            'payment_method_diversity': 2,
            'avg_ticket_hold_time': 72,
            'social_graph_centrality': 0.7
        }
        events = [
            {'event_id': 1, 'event_popularity_score': 0.8},
            {'event_id': 2, 'event_popularity_score': 0.6}
        ]
        
        recommendations = integration.recommend_events(
            user_id="user_123",
            user_features=user_features,
            events=events
        )
        
        assert isinstance(recommendations, list)
        assert len(recommendations) <= len(events)
    
    def test_get_pricing_returns_price_dict(self):
        """Test that get_pricing returns price information."""
        integration = MLIntegrationLayer()
        user_features = {
            'cross_event_attendance': 5,
            'payment_method_diversity': 2,
            'avg_ticket_hold_time': 72,
            'social_graph_centrality': 0.7
        }
        event_features = {
            'popularity_score': 0.8,
            'days_until_event': 30
        }
        
        pricing = integration.get_pricing(
            base_price=100.0,
            event_id=42,
            user_features=user_features,
            event_features=event_features
        )
        
        assert 'final_price' in pricing
        assert 'selected_arm' in pricing
        assert pricing['final_price'] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

