"""Unit tests for feature engineering."""
import pytest
from ml_pipeline.feature_engineering import FeatureEngineer


def test_feature_engineer_initialization():
    """Test feature engineer can be initialized."""
    engineer = FeatureEngineer()
    assert engineer is not None


def test_compute_features():
    """Test feature computation."""
    engineer = FeatureEngineer()
    
    features = engineer.compute_features(
        transaction_id='test_001',
        wallet_address='0x1234567890abcdef',
        event_id=1
    )
    
    assert isinstance(features, dict)
    assert 'txn_velocity_1h' in features
    assert 'wallet_age_days' in features
    assert 'event_popularity_score' in features
    assert len(features) == 10  # 10 core features


def test_compute_derived_features():
    """Test derived feature computation."""
    import pandas as pd
    from datetime import datetime
    
    engineer = FeatureEngineer()
    
    df = pd.DataFrame({
        'transaction_id': ['tx1', 'tx2'],
        'wallet_address': ['0x1', '0x1'],
        'created_at': [datetime.now(), datetime.now()],
        'event_created_at': [datetime.now(), datetime.now()],
        'first_ticket_sale': [datetime.now(), datetime.now()]
    })
    
    df_transformed = engineer.compute_derived_features(df)
    
    assert 'avg_tx_per_day' in df_transformed.columns or 'user_activity_delta' in df_transformed.columns

