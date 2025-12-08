"""Unit tests for Multi-Armed Bandit."""
import pytest
from ml_pipeline.mab_pricing import MultiArmedBandit


def test_mab_initialization():
    """Test MAB can be initialized."""
    mab = MultiArmedBandit(epsilon=0.15)
    assert mab.epsilon == 0.15
    assert len(mab.arms) == 4


def test_select_arm():
    """Test arm selection."""
    mab = MultiArmedBandit(epsilon=0.15)
    selected_arm = mab.select_arm()
    
    assert selected_arm in ['baseline', 'surge_pricing', 'early_bird', 'ml_pricing']


def test_update_reward():
    """Test reward update."""
    mab = MultiArmedBandit(epsilon=0.15)
    
    mab.update_reward('baseline', reward=0.8)
    mab.update_reward('baseline', reward=0.9)
    
    assert mab.arms['baseline']['count'] == 2
    assert mab.arms['baseline']['avg_reward'] > 0


def test_route_request():
    """Test request routing."""
    mab = MultiArmedBandit(epsilon=0.15)
    result = mab.route_request(request_id='test_001', event_id=1)
    
    assert 'selected_arm' in result
    assert 'pricing_strategy' in result
    assert 'decision_path' in result


def test_calculate_pricing():
    """Test pricing calculation."""
    mab = MultiArmedBandit(epsilon=0.15)
    
    base_price = 100.0
    price = mab.calculate_pricing(base_price, 'baseline')
    assert price == base_price
    
    price_surge = mab.calculate_pricing(base_price, 'surge_pricing', {'popularity_score': 0.8})
    assert price_surge >= base_price

