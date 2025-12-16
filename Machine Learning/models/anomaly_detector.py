"""
Anomaly Detection Model - Isolation Forest
Detects unusual/outlier transactions.
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Optional
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
import pickle
from datetime import datetime


class AnomalyDetectionModel:
    """
    Isolation Forest for transaction anomaly detection.
    
    Input: Feature subset [txn_velocity_1h, price_deviation_ratio, wallet_age_days, avg_ticket_hold_time]
    Output: Anomaly score [0, 1] (lower = more anomalous), is_outlier flag
    """
    
    FEATURE_COLS = [
        'txn_velocity_1h',
        'price_deviation_ratio',
        'wallet_age_days',
        'avg_ticket_hold_time'
    ]
    
    def __init__(self, model_path: Optional[Path] = None):
        """
        Initialize anomaly detection model.
        
        Args:
            model_path: Path to trained model file
        """
        self.model = IsolationForest(
            contamination=0.02,  # Expect 2% outliers
            random_state=42,
            n_estimators=100
        )
        self.scaler = StandardScaler()
        self.is_fitted = False
        
        # Default path
        artifacts_dir = Path(__file__).parent.parent / "artifacts"
        self.model_path = model_path or artifacts_dir / "anomaly_detector.joblib"
        self.scaler_path = artifacts_dir / "anomaly_detector_scaler.joblib"
        
        # Load model if exists
        self.load_model()
    
    def load_model(self) -> bool:
        """Load trained model from disk."""
        try:
            if self.model_path.exists() and self.scaler_path.exists():
                with open(self.model_path, 'rb') as f:
                    self.model = pickle.load(f)
                with open(self.scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f)
                self.is_fitted = True
                print(f"✅ Loaded anomaly detection model from {self.model_path}")
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
        
        with open(output_dir / "anomaly_detector.joblib", 'wb') as f:
            pickle.dump(self.model, f)
        
        with open(output_dir / "anomaly_detector_scaler.joblib", 'wb') as f:
            pickle.dump(self.scaler, f)
        
        print(f"✅ Saved anomaly detection model to {output_dir}")
    
    def train(self, X: pd.DataFrame, contamination: float = 0.02, random_state: int = 42) -> Dict:
        """
        Train anomaly detection model.
        
        Args:
            X: Feature DataFrame (should contain normal transactions only)
            contamination: Expected proportion of outliers
            random_state: Random seed
            
        Returns:
            Dict with training metrics
        """
        # Prepare features
        missing_cols = set(self.FEATURE_COLS) - set(X.columns)
        if missing_cols:
            raise ValueError(f"Missing features: {missing_cols}")
        
        X_features = X[self.FEATURE_COLS].fillna(0)
        X_scaled = self.scaler.fit_transform(X_features)
        
        # Update contamination
        self.model.contamination = contamination
        self.model.random_state = random_state
        
        # Train
        self.model.fit(X_scaled)
        self.is_fitted = True
        
        # Evaluate on training data
        predictions = self.model.predict(X_scaled)
        scores = self.model.score_samples(X_scaled)
        n_outliers = list(predictions).count(-1)
        
        print(f"✅ Anomaly detector trained: {n_outliers} outliers detected ({n_outliers/len(X)*100:.2f}%)")
        
        # Save model
        self.save_model()
        
        return {
            'n_samples': len(X),
            'n_outliers_detected': int(n_outliers),
            'outlier_rate': float(n_outliers / len(X)),
            'contamination': contamination
        }
    
    def detect(self, features: Dict) -> Dict:
        """
        Detect if transaction is anomalous.
        
        Args:
            features: Dict with feature values
            
        Returns:
            Dict with is_outlier, anomaly_score, outlier_score
        """
        if not self.is_fitted:
            # Return default if not fitted
            return {
                'is_outlier': False,
                'outlier_score': 1,
                'anomaly_score': 0.5,
                'model_type': 'isolation_forest',
                'note': 'model_not_fitted'
            }
        
        # Extract features
        feature_vector = np.array([[
            features.get('txn_velocity_1h', 0),
            features.get('price_deviation_ratio', 0),
            features.get('wallet_age_days', 30),
            features.get('avg_ticket_hold_time', 48)
        ]])
        
        # Scale
        feature_vector_scaled = self.scaler.transform(feature_vector)
        
        # Predict
        prediction = self.model.predict(feature_vector_scaled)[0]  # -1 for outlier, 1 for normal
        score = self.model.score_samples(feature_vector_scaled)[0]  # Lower = more anomalous
        
        # Normalize score to [0, 1] using sigmoid
        # Lower scores (more negative) = more anomalous
        # Transform: sigmoid(-score) gives higher values for normal, lower for anomalous
        anomaly_score = 1 / (1 + np.exp(-score))  # Sigmoid transform
        
        # Invert so lower = more anomalous (original Isolation Forest behavior)
        anomaly_score = 1 - anomaly_score
        
        return {
            'is_outlier': bool(prediction == -1),
            'outlier_score': int(prediction),
            'anomaly_score': round(float(anomaly_score), 4),
            'raw_score': float(score),
            'model_type': 'isolation_forest',
            'timestamp': datetime.now().isoformat()
        }


# Singleton instance
_anomaly_detector = None

def get_anomaly_detector() -> AnomalyDetectionModel:
    """Get singleton anomaly detector instance."""
    global _anomaly_detector
    if _anomaly_detector is None:
        _anomaly_detector = AnomalyDetectionModel()
    return _anomaly_detector


if __name__ == "__main__":
    # Example usage
    import sys
    
    if "--train" in sys.argv:
        print("Training anomaly detection model...")
        print("Note: Requires normal transaction data (no fraud labels needed)")
        # model = AnomalyDetectionModel()
        # X = load_normal_transactions()  # Would load from database
        # results = model.train(X)
        # print(f"Training complete: {results}")
    else:
        model = get_anomaly_detector()
        if model.is_fitted:
            test_features = {
                'txn_velocity_1h': 50,  # Very high = suspicious
                'price_deviation_ratio': 2.0,  # 200% above floor = suspicious
                'wallet_age_days': 1,  # New wallet = suspicious
                'avg_ticket_hold_time': 5  # Very short hold = suspicious
            }
            result = model.detect(test_features)
            print(f"Anomaly detection: {result}")
        else:
            print("Model not loaded. Train model first or place trained model in artifacts/")

