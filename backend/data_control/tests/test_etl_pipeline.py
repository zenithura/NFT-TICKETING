"""Unit tests for ETL Pipeline."""
import pytest
import pandas as pd
from datetime import datetime, timedelta
from data_control.etl_pipeline import ETLPipeline

@pytest.fixture
def etl_pipeline():
    return ETLPipeline()

@pytest.fixture
def sample_df():
    return pd.DataFrame({
        'transaction_id': ['tx1', 'tx2'],
        'wallet_address': ['addr1', 'addr1'],
        'event_id': [1, 1],
        'price_paid': [100.0, 150.0],
        'created_at': [datetime.now() - timedelta(days=2), datetime.now() - timedelta(days=1)],
        'event_created_at': [datetime.now() - timedelta(days=5), datetime.now() - timedelta(days=5)]
    })

def test_transform_features(etl_pipeline, sample_df):
    """Test feature transformation logic."""
    transformed_df = etl_pipeline.transform_features(sample_df)
    
    assert not transformed_df.empty
    assert 'avg_tx_per_day' in transformed_df.columns
    assert 'event_lag' in transformed_df.columns
    assert 'user_activity_delta' in transformed_df.columns
    
    # Check avg_tx_per_day for addr1
    # 2 transactions over 2 days active = 1.0 tx/day
    addr1_stats = transformed_df[transformed_df['wallet_address'] == 'addr1']
    assert addr1_stats['avg_tx_per_day'].iloc[0] == 1.0

def test_extract_transactions_empty(etl_pipeline):
    """Test extraction with no data."""
    # This might fail if DB is not connected, but we can mock it if needed
    # For now, just check it returns a DataFrame
    df = etl_pipeline.extract_transactions(since=datetime.now() + timedelta(days=1))
    assert isinstance(df, pd.DataFrame)
