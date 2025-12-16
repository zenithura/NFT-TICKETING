"""
Model Unit Tests
Tests for ML model implementations.
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from models.fraud_detection_model import FraudDetectionModel
from models.user_clustering import UserClusteringModel
from models.anomaly_detector import AnomalyDetectionModel
from models.recommendation_engine import RecommendationEngine
from models.pricing_bandit import PricingBandit


class TestFraudDetectionModel:
    """Tests for fraud detection model."""
    
    def test_model_initialization(self):
        """Test model can be initialized."""
        model = FraudDetectionModel()
        assert model is not None
        assert model.model_version == "v1.2.3"
    
    def test_predict_requires_fitted_model(self):
        """Test that predict requires fitted model."""
        model = FraudDetectionModel()
        features = {
            'txn_velocity_1h': 1,
            'wallet_age_days': 30,
            'avg_ticket_hold_time': 48,
            'event_popularity_score': 0.5,
            'price_deviation_ratio': 0.1,
            'cross_event_attendance': 2,
            'geo_velocity_flag': 0,
            'payment_method_diversity': 1,
            'social_graph_centrality': 0.5,
            'time_to_first_resale': 0
        }
        
        if not model.is_fitted:
            with pytest.raises(ValueError, match="not fitted"):
                model.predict(features)


class TestUserClustering:
    """Tests for user clustering model."""
    
    def test_model_initialization(self):
        """Test model can be initialized."""
        model = UserClusteringModel()
        assert model is not None
    
    def test_predict_cluster_requires_fitted_model(self):
        """Test that predict requires fitted model."""
        model = UserClusteringModel()
        features = {
            'cross_event_attendance': 5,
            'payment_method_diversity': 2,
            'avg_ticket_hold_time': 72,
            'social_graph_centrality': 0.7
        }
        
        if not model.kmeans_fitted and not model.dbscan_fitted:
            with pytest.raises(ValueError, match="not fitted"):
                model.predict_cluster(features)


class TestAnomalyDetector:
    """Tests for anomaly detection model."""
    
    def test_model_initialization(self):
        """Test model can be initialized."""
        model = AnomalyDetectionModel()
        assert model is not None
    
    def test_detect_returns_default_if_not_fitted(self):
        """Test that detect returns default if model not fitted."""
        model = AnomalyDetectionModel()
        if not model.is_fitted:
            features = {
                'txn_velocity_1h': 1,
                'price_deviation_ratio': 0.1,
                'wallet_age_days': 30,
                'avg_ticket_hold_time': 48
            }
            result = model.detect(features)
            assert 'note' in result
            assert result['note'] == 'model_not_fitted'


class TestPricingBandit:
    """Tests for pricing bandit."""
    
    def test_model_initialization(self):
        """Test bandit can be initialized."""
        bandit = PricingBandit(epsilon=0.15)
        assert bandit is not None
        assert bandit.epsilon == 0.15
    
    def test_select_arm_returns_valid_arm(self):
        """Test that select_arm returns valid arm name."""
        bandit = PricingBandit(epsilon=0.15)
        result = bandit.select_arm()
        assert 'selected_arm' in result
        assert result['selected_arm'] in bandit.ARM_NAMES
    
    def test_calculate_price(self):
        """Test price calculation for different arms."""
        bandit = PricingBandit(epsilon=0.15)
        base_price = 100.0
        
        # Standard price
        price = bandit.calculate_price(base_price, 'standard')
        assert price == base_price
        
        # Premium price
        price = bandit.calculate_price(base_price, 'premium_+10pct')
        assert price == base_price * 1.10
        
        # Discount price
        price = bandit.calculate_price(base_price, 'discount_-10pct')
        assert price == base_price * 0.90


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

