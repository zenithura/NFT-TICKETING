"""
Dimensionality Reduction - PCA
Principal Component Analysis for feature reduction and visualization.
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Optional, Tuple
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import pickle


class DimensionalityReducer:
    """
    PCA-based dimensionality reduction for feature analysis.
    
    Used as supporting model for visualization and feature analysis.
    """
    
    def __init__(self, model_path: Optional[Path] = None, n_components: int = 3):
        """
        Initialize dimensionality reducer.
        
        Args:
            model_path: Path to trained model
            n_components: Number of principal components to keep
        """
        self.n_components = n_components
        self.pca = PCA(n_components=n_components, random_state=42)
        self.scaler = StandardScaler()
        self.is_fitted = False
        
        # Default path
        artifacts_dir = Path(__file__).parent.parent / "artifacts"
        self.model_path = model_path or artifacts_dir / "dimensionality_reduction.joblib"
        self.scaler_path = artifacts_dir / "dimensionality_reduction_scaler.joblib"
        
        # Load model if exists
        self.load_model()
    
    def load_model(self) -> bool:
        """Load trained model from disk."""
        try:
            if self.model_path.exists() and self.scaler_path.exists():
                with open(self.model_path, 'rb') as f:
                    self.pca = pickle.load(f)
                with open(self.scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f)
                self.is_fitted = True
                self.n_components = self.pca.n_components
                print(f"✅ Loaded dimensionality reducer from {self.model_path}")
                return True
        except Exception as e:
            print(f"⚠️  Could not load model: {e}")
        
        return False
    
    def save_model(self, output_dir: Optional[Path] = None):
        """Save trained model to disk."""
        if not self.is_fitted:
            raise ValueError("Model not fitted. Train model before saving.")
        
        output_dir = output_dir or self.model_path.parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        with open(output_dir / "dimensionality_reduction.joblib", 'wb') as f:
            pickle.dump(self.pca, f)
        
        with open(output_dir / "dimensionality_reduction_scaler.joblib", 'wb') as f:
            pickle.dump(self.scaler, f)
        
        print(f"✅ Saved dimensionality reducer to {output_dir}")
    
    def fit_transform(self, X: pd.DataFrame, feature_cols: Optional[list] = None) -> Tuple[np.ndarray, Dict]:
        """
        Fit PCA and transform features.
        
        Args:
            X: Feature DataFrame
            feature_cols: Columns to use (if None, uses all numeric columns)
            
        Returns:
            Tuple of (transformed_features, explained_variance_info)
        """
        if feature_cols is None:
            feature_cols = X.select_dtypes(include=[np.number]).columns.tolist()
        
        X_features = X[feature_cols].fillna(0)
        X_scaled = self.scaler.fit_transform(X_features)
        
        # Fit PCA
        X_transformed = self.pca.fit_transform(X_scaled)
        self.is_fitted = True
        
        # Calculate explained variance
        explained_variance = self.pca.explained_variance_ratio_
        cumulative_variance = np.cumsum(explained_variance)
        
        variance_info = {
            'explained_variance_ratio': [float(v) for v in explained_variance],
            'cumulative_variance': [float(v) for v in cumulative_variance],
            'total_variance_explained': float(cumulative_variance[-1]),
            'n_components': self.n_components,
            'original_n_features': len(feature_cols)
        }
        
        # Save model
        self.save_model()
        
        return X_transformed, variance_info
    
    def transform(self, X: pd.DataFrame, feature_cols: Optional[list] = None) -> np.ndarray:
        """
        Transform features using fitted PCA.
        
        Args:
            X: Feature DataFrame
            feature_cols: Columns to use (must match training columns)
            
        Returns:
            Transformed features
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Call fit_transform first.")
        
        if feature_cols is None:
            # Use all numeric columns (assuming same as training)
            feature_cols = X.select_dtypes(include=[np.number]).columns.tolist()
        
        X_features = X[feature_cols].fillna(0)
        X_scaled = self.scaler.transform(X_features)
        X_transformed = self.pca.transform(X_scaled)
        
        return X_transformed
    
    def get_feature_importance(self, feature_names: list) -> Dict:
        """
        Get feature importance from PCA components.
        
        Args:
            feature_names: List of original feature names
            
        Returns:
            Dict with feature importance scores
        """
        if not self.is_fitted:
            return {}
        
        # Calculate feature importance as sum of absolute component loadings
        importance = np.abs(self.pca.components_).sum(axis=0)
        
        # Normalize
        importance = importance / importance.sum()
        
        return dict(zip(feature_names, [float(v) for v in importance]))


# Singleton instance
_dimensionality_reducer = None

def get_dimensionality_reducer(n_components: int = 3) -> DimensionalityReducer:
    """Get singleton dimensionality reducer instance."""
    global _dimensionality_reducer
    if _dimensionality_reducer is None:
        _dimensionality_reducer = DimensionalityReducer(n_components=n_components)
    return _dimensionality_reducer

