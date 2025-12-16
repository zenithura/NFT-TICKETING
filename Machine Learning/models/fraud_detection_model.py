"""
Fraud Detection Model - XGBoost Classifier
Classical ML model for detecting fraudulent ticket transactions.
"""

import pickle
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Optional, Tuple
import xgboost as xgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    roc_auc_score, precision_recall_curve, auc,
    f1_score, confusion_matrix, classification_report
)
import json
from datetime import datetime


class FraudDetectionModel:
    """
    XGBoost-based fraud detection model.
    
    Input: 10 feature vector
    Output: Fraud probability [0, 1] and decision (APPROVED/REQUIRE_2FA/MANUAL_REVIEW/BLOCKED)
    """
    
    # Feature columns in order (must match training data)
    FEATURE_COLS = [
        'txn_velocity_1h',
        'wallet_age_days',
        'avg_ticket_hold_time',
        'event_popularity_score',
        'price_deviation_ratio',
        'cross_event_attendance',
        'geo_velocity_flag',
        'payment_method_diversity',
        'social_graph_centrality',
        'time_to_first_resale'
    ]
    
    # Decision thresholds
    THRESHOLDS = {
        'APPROVED': 0.40,
        'REQUIRE_2FA': 0.65,
        'MANUAL_REVIEW': 0.85,
        'BLOCKED': 1.0
    }
    
    def __init__(self, model_path: Optional[Path] = None):
        """
        Initialize fraud detection model.
        
        Args:
            model_path: Path to trained model file. If None, uses default location.
        """
        self.model = None
        self.model_version = "v1.2.3"
        self.model_path = model_path or Path(__file__).parent.parent / "artifacts" / "fraud_detection_v1.2.3.joblib"
        self.is_fitted = False
        
        # Load model if exists
        if self.model_path.exists():
            self.load_model()
    
    def load_model(self) -> bool:
        """Load trained model from disk."""
        try:
            with open(self.model_path, 'rb') as f:
                self.model = pickle.load(f)
            self.is_fitted = True
            print(f"✅ Loaded fraud detection model from {self.model_path}")
            return True
        except Exception as e:
            print(f"⚠️  Could not load model: {e}")
            return False
    
    def save_model(self, output_path: Optional[Path] = None):
        """Save trained model to disk."""
        if not self.is_fitted:
            raise ValueError("Model not fitted. Train model before saving.")
        
        path = output_path or self.model_path
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'wb') as f:
            pickle.dump(self.model, f)
        print(f"✅ Saved model to {path}")
    
    def train(self, X: pd.DataFrame, y: pd.Series, test_size: float = 0.15, 
              validation_size: float = 0.15, random_state: int = 42) -> Dict:
        """
        Train fraud detection model.
        
        Args:
            X: Feature DataFrame (must contain all FEATURE_COLS)
            y: Binary labels (1 = fraud, 0 = legitimate)
            test_size: Proportion for test set
            validation_size: Proportion for validation set
            random_state: Random seed
            
        Returns:
            Dict with training metrics
        """
        # Validate features
        missing_cols = set(self.FEATURE_COLS) - set(X.columns)
        if missing_cols:
            raise ValueError(f"Missing features: {missing_cols}")
        
        # Prepare data
        X_features = X[self.FEATURE_COLS].fillna(0)
        y = y.fillna(0)
        
        # Split data
        X_temp, X_test, y_temp, y_test = train_test_split(
            X_features, y, test_size=test_size, random_state=random_state, stratify=y
        )
        
        val_size_adjusted = validation_size / (1 - test_size)
        X_train, X_val, y_train, y_val = train_test_split(
            X_temp, y_temp, test_size=val_size_adjusted, random_state=random_state, stratify=y_temp
        )
        
        # Train XGBoost model
        self.model = xgb.XGBClassifier(
            n_estimators=100,
            max_depth=6,
            learning_rate=0.1,
            random_state=random_state,
            eval_metric='logloss'
        )
        
        self.model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            verbose=False
        )
        
        self.is_fitted = True
        
        # Evaluate
        train_metrics = self._evaluate(X_train, y_train, "train")
        val_metrics = self._evaluate(X_val, y_val, "validation")
        test_metrics = self._evaluate(X_test, y_test, "test")
        
        # Save model
        self.save_model()
        
        return {
            'training': train_metrics,
            'validation': val_metrics,
            'test': test_metrics,
            'model_version': self.model_version
        }
    
    def _evaluate(self, X: pd.DataFrame, y: pd.Series, split_name: str) -> Dict:
        """Evaluate model on dataset."""
        y_pred_proba = self.model.predict_proba(X)[:, 1]
        y_pred = (y_pred_proba > 0.65).astype(int)  # Threshold = 0.65
        
        auc_roc = roc_auc_score(y, y_pred_proba)
        precision, recall, _ = precision_recall_curve(y, y_pred_proba)
        auc_pr = auc(recall, precision)
        f1 = f1_score(y, y_pred)
        
        cm = confusion_matrix(y, y_pred)
        fpr = cm[0, 1] / (cm[0, 0] + cm[0, 1]) if (cm[0, 0] + cm[0, 1]) > 0 else 0.0
        
        print(f"\n📊 {split_name.capitalize()} Metrics:")
        print(f"  AUC-ROC: {auc_roc:.3f}")
        print(f"  AUC-PR:  {auc_pr:.3f}")
        print(f"  F1 Score: {f1:.3f}")
        print(f"  FPR: {fpr:.3f}")
        
        return {
            'auc_roc': float(auc_roc),
            'auc_pr': float(auc_pr),
            'f1_score': float(f1),
            'false_positive_rate': float(fpr),
            'confusion_matrix': cm.tolist()
        }
    
    def predict(self, features: Dict) -> Dict:
        """
        Predict fraud probability for a transaction.
        
        Args:
            features: Dict with feature values (keys must match FEATURE_COLS)
            
        Returns:
            Dict with fraud_probability, decision, confidence, top_features
        """
        if not self.is_fitted:
            raise ValueError("Model not fitted. Train or load model first.")
        
        # Extract features in correct order
        feature_vector = np.array([[
            features.get(col, 0) for col in self.FEATURE_COLS
        ]])
        
        # Predict
        fraud_probability = float(self.model.predict_proba(feature_vector)[0][1])
        
        # Determine decision
        decision = self._get_decision(fraud_probability)
        
        # Calculate confidence (distance from decision boundary 0.5)
        confidence = float(1 - abs(fraud_probability - 0.5) * 2)
        
        # Get feature importance
        feature_importance = dict(zip(
            self.FEATURE_COLS,
            [float(x) for x in self.model.feature_importances_]
        ))
        top_features = dict(sorted(
            feature_importance.items(),
            key=lambda x: x[1],
            reverse=True
        )[:3])
        
        return {
            'fraud_probability': round(fraud_probability, 4),
            'decision': decision,
            'confidence': round(confidence, 4),
            'top_features': top_features,
            'model_version': self.model_version,
            'timestamp': datetime.now().isoformat()
        }
    
    def _get_decision(self, fraud_probability: float) -> str:
        """Map fraud probability to decision."""
        if fraud_probability < self.THRESHOLDS['APPROVED']:
            return 'APPROVED'
        elif fraud_probability < self.THRESHOLDS['REQUIRE_2FA']:
            return 'REQUIRE_2FA'
        elif fraud_probability < self.THRESHOLDS['MANUAL_REVIEW']:
            return 'MANUAL_REVIEW'
        else:
            return 'BLOCKED'
    
    def get_feature_importance(self) -> Dict:
        """Get feature importance scores."""
        if not self.is_fitted:
            return {}
        
        return dict(zip(
            self.FEATURE_COLS,
            [float(x) for x in self.model.feature_importances_]
        ))


# Singleton instance
_fraud_model = None

def get_fraud_model() -> FraudDetectionModel:
    """Get singleton fraud detection model instance."""
    global _fraud_model
    if _fraud_model is None:
        _fraud_model = FraudDetectionModel()
    return _fraud_model


if __name__ == "__main__":
    # Example usage
    import sys
    
    if "--train" in sys.argv:
        # Train model (would load real data in production)
        print("Training fraud detection model...")
        print("Note: Requires labeled transaction data")
        # model = FraudDetectionModel()
        # X, y = load_training_data()  # Would load from database
        # metrics = model.train(X, y)
        # print(f"Training complete: {metrics}")
    else:
        # Test prediction
        model = get_fraud_model()
        if model.is_fitted:
            test_features = {
                'txn_velocity_1h': 5,
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
            result = model.predict(test_features)
            print(f"Prediction: {result}")
        else:
            print("Model not loaded. Train model first or place trained model in artifacts/")

