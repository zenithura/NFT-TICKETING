"""
Feature Engineering - Core Feature Computation
Version-controlled feature engineering pipeline.

Note: This file uses the simplified feature engineering implementation.
For production Supabase-based feature engineering, use integration/supabase_feature_engineer.py
"""

# Use simplified version as default
# For production, use integration/supabase_feature_engineer.py
from .feature_engineering_simple import FeatureEngineer, get_feature_engineer

__all__ = ['FeatureEngineer', 'get_feature_engineer']
