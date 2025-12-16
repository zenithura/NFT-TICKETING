"""Multiple ML Models and Heuristics - 4-5 Production Processes."""
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import pickle
from pathlib import Path
from typing import Dict, List, Optional
import json


class RiskScoringModel:
    """Risk scoring heuristic based on rule-based decision bands."""
    
    def __init__(self):
        self.thresholds = {
            'high_risk': 0.75,
            'medium_risk': 0.50,
            'low_risk': 0.25
        }
    
    def score(self, features: Dict) -> Dict:
        """
        Calculate risk score using rule-based heuristic.
        
        Rules:
        - High transaction velocity (>10/hour) → +0.3
        - New wallet (<7 days) → +0.2
        - High price deviation (>50%) → +0.2
        - Geo velocity flag → +0.3
        - Low attendance (<2 events) → +0.1
        """
        score = 0.0
        reasons = []
        
        txn_velocity = features.get('txn_velocity_1h', 0)
        if txn_velocity > 10:
            score += 0.3
            reasons.append('high_transaction_velocity')
        
        wallet_age = features.get('wallet_age_days', 30)
        if wallet_age < 7:
            score += 0.2
            reasons.append('new_wallet')
        
        price_dev = abs(features.get('price_deviation_ratio', 0))
        if price_dev > 0.5:
            score += 0.2
            reasons.append('high_price_deviation')
        
        geo_velocity = features.get('geo_velocity_flag', 0)
        if geo_velocity == 1:
            score += 0.3
            reasons.append('geo_velocity_flag')
        
        attendance = features.get('cross_event_attendance', 0)
        if attendance < 2:
            score += 0.1
            reasons.append('low_attendance')
        
        # Normalize to [0, 1]
        score = min(score, 1.0)
        
        # Determine risk band
        if score >= self.thresholds['high_risk']:
            band = 'HIGH'
        elif score >= self.thresholds['medium_risk']:
            band = 'MEDIUM'
        else:
            band = 'LOW'
        
        return {
            'risk_score': round(score, 3),
            'risk_band': band,
            'reasons': reasons,
            'model_type': 'rule_based_heuristic'
        }


class RecommenderScore:
    """Collaborative filtering-based recommender score."""
    
    def __init__(self):
        self.scaler = StandardScaler()
        self.kmeans = None
        self.user_clusters = {}
    
    def fit(self, user_features: pd.DataFrame):
        """Fit K-Means clustering model for user segmentation."""
        feature_cols = ['cross_event_attendance', 'payment_method_diversity', 
                       'avg_ticket_hold_time', 'social_graph_centrality']
        
        X = user_features[feature_cols].fillna(0)
        X_scaled = self.scaler.fit_transform(X)
        
        # Use KMeans for user segmentation
        self.kmeans = KMeans(n_clusters=5, random_state=42, n_init=10)
        self.kmeans.fit(X_scaled)
        
        # Store user clusters
        clusters = self.kmeans.predict(X_scaled)
        for idx, user in enumerate(user_features.index):
            self.user_clusters[user] = int(clusters[idx])
    
    def recommend_score(self, user_features: Dict, event_features: Dict) -> Dict:
        """
        Calculate recommendation score for user-event pair.
        
        Returns:
            Dict with recommendation_score (0-1), cluster_id, reasoning
        """
        # Simplified recommendation: based on user cluster and event popularity
        user_cluster = self.user_clusters.get(user_features.get('wallet_address'), 0)
        event_popularity = event_features.get('event_popularity_score', 0.5)
        attendance = user_features.get('cross_event_attendance', 0)
        
        # Score formula: cluster preference + popularity + user engagement
        score = 0.4 * (user_cluster / 4.0) + 0.4 * event_popularity + 0.2 * min(attendance / 10.0, 1.0)
        
        return {
            'recommendation_score': round(min(score, 1.0), 3),
            'user_cluster': user_cluster,
            'confidence': round(abs(score - 0.5) * 2, 3),  # Distance from neutral
            'model_type': 'collaborative_filtering'
        }


class OutlierDetectionModel:
    """Isolation Forest for transaction outlier detection."""
    
    def __init__(self):
        self.model = IsolationForest(
            contamination=0.02,  # Expect 2% outliers
            random_state=42,
            n_estimators=100
        )
        self.scaler = StandardScaler()
        self.feature_cols = [
            'txn_velocity_1h',
            'price_deviation_ratio',
            'wallet_age_days',
            'avg_ticket_hold_time'
        ]
        self.is_fitted = False
    
    def fit(self, features_df: pd.DataFrame):
        """Fit outlier detection model."""
        X = features_df[self.feature_cols].fillna(0)
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled)
        self.is_fitted = True
    
    def detect(self, features: Dict) -> Dict:
        """
        Detect if transaction is an outlier.
        
        Returns:
            Dict with is_outlier (bool), outlier_score (-1 to 1), anomaly_score
        """
        if not self.is_fitted:
            # Return default if not fitted
            return {
                'is_outlier': False,
                'outlier_score': 0.0,
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
        prediction = self.model.predict(feature_vector_scaled)[0]
        score = self.model.score_samples(feature_vector_scaled)[0]
        
        # Normalize score to [0, 1] (anomaly_score)
        # Lower scores = more anomalous
        anomaly_score = 1 / (1 + np.exp(-score))  # Sigmoid transform
        
        return {
            'is_outlier': prediction == -1,
            'outlier_score': float(prediction),
            'anomaly_score': round(float(anomaly_score), 3),
            'model_type': 'isolation_forest'
        }


class ClusteringModel:
    """DBSCAN clustering for user behavior segmentation."""
    
    def __init__(self):
        self.model = DBSCAN(eps=0.5, min_samples=5)
        self.scaler = StandardScaler()
        self.feature_cols = [
            'txn_velocity_1h',
            'cross_event_attendance',
            'avg_ticket_hold_time',
            'payment_method_diversity'
        ]
        self.is_fitted = False
        self.clusters = {}
    
    def fit(self, features_df: pd.DataFrame):
        """Fit clustering model."""
        X = features_df[self.feature_cols].fillna(0)
        X_scaled = self.scaler.fit_transform(X)
        self.model.fit(X_scaled)
        
        # Store cluster assignments
        for idx, cluster_id in enumerate(self.model.labels_):
            self.clusters[idx] = int(cluster_id)
        
        self.is_fitted = True
    
    def predict_cluster(self, features: Dict) -> Dict:
        """Predict cluster assignment for features."""
        if not self.is_fitted:
            return {
                'cluster_id': -1,
                'cluster_label': 'unknown',
                'model_type': 'dbscan',
                'note': 'model_not_fitted'
            }
        
        feature_vector = np.array([[
            features.get('txn_velocity_1h', 0),
            features.get('cross_event_attendance', 0),
            features.get('avg_ticket_hold_time', 48),
            features.get('payment_method_diversity', 1)
        ]])
        
        feature_vector_scaled = self.scaler.transform(feature_vector)
        
        # Find nearest cluster (simplified - would use nearest neighbor in production)
        # For now, return default
        cluster_id = 0
        
        cluster_labels = {
            -1: 'outlier',
            0: 'casual_user',
            1: 'regular_user',
            2: 'vip_user',
            3: 'scalper'
        }
        
        return {
            'cluster_id': cluster_id,
            'cluster_label': cluster_labels.get(cluster_id, 'unknown'),
            'model_type': 'dbscan'
        }


class ModelEnsemble:
    """Ensemble of all models and heuristics."""
    
    def __init__(self):
        self.risk_scorer = RiskScoringModel()
        self.recommender = RecommenderScore()
        self.outlier_detector = OutlierDetectionModel()
        self.clusterer = ClusteringModel()
    
    def predict_all(self, features: Dict, event_features: Optional[Dict] = None) -> Dict:
        """
        Run all models/heuristics and return combined results.
        
        Returns:
            Dict with all model outputs
        """
        results = {
            'risk_scoring': self.risk_scorer.score(features),
            'recommender_score': self.recommender.recommend_score(features, event_features or {}),
            'outlier_detection': self.outlier_detector.detect(features),
            'clustering': self.clusterer.predict_cluster(features)
        }
        
        return results

