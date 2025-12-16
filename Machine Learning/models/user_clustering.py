"""
User Clustering Model - K-Means + DBSCAN
Clustering model for user behavior segmentation.
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Optional, List
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler
import pickle
import json


class UserClusteringModel:
    """
    Dual clustering approach: K-Means for user segments, DBSCAN for outlier detection.
    
    Input: User feature vector [cross_event_attendance, payment_method_diversity, 
                                avg_ticket_hold_time, social_graph_centrality]
    Output: Cluster ID, cluster label (casual_user, regular_user, vip_user, scalper, outlier)
    """
    
    FEATURE_COLS = [
        'cross_event_attendance',
        'payment_method_diversity',
        'avg_ticket_hold_time',
        'social_graph_centrality'
    ]
    
    CLUSTER_LABELS = {
        -1: 'outlier',  # DBSCAN outlier
        0: 'casual_user',
        1: 'regular_user',
        2: 'vip_user',
        3: 'scalper',
        4: 'premium_user'
    }
    
    def __init__(self, kmeans_path: Optional[Path] = None, dbscan_path: Optional[Path] = None):
        """
        Initialize clustering models.
        
        Args:
            kmeans_path: Path to trained K-Means model
            dbscan_path: Path to trained DBSCAN model
        """
        self.kmeans = None
        self.dbscan = None
        self.scaler = StandardScaler()
        self.kmeans_fitted = False
        self.dbscan_fitted = False
        
        # Default paths
        artifacts_dir = Path(__file__).parent.parent / "artifacts"
        self.kmeans_path = kmeans_path or artifacts_dir / "user_clustering_kmeans.joblib"
        self.dbscan_path = dbscan_path or artifacts_dir / "user_clustering_dbscan.joblib"
        self.scaler_path = artifacts_dir / "user_clustering_scaler.joblib"
        
        # Load models if exist
        self.load_models()
    
    def load_models(self) -> bool:
        """Load trained models from disk."""
        try:
            if self.kmeans_path.exists():
                with open(self.kmeans_path, 'rb') as f:
                    self.kmeans = pickle.load(f)
                self.kmeans_fitted = True
            
            if self.dbscan_path.exists():
                with open(self.dbscan_path, 'rb') as f:
                    self.dbscan = pickle.load(f)
                self.dbscan_fitted = True
            
            if self.scaler_path.exists():
                with open(self.scaler_path, 'rb') as f:
                    self.scaler = pickle.load(f)
            
            if self.kmeans_fitted or self.dbscan_fitted:
                print("✅ Loaded clustering models")
                return True
        except Exception as e:
            print(f"⚠️  Could not load models: {e}")
        
        return False
    
    def save_models(self, output_dir: Optional[Path] = None):
        """Save trained models to disk."""
        if not (self.kmeans_fitted or self.dbscan_fitted):
            raise ValueError("Models not fitted. Train models before saving.")
        
        output_dir = output_dir or self.kmeans_path.parent
        output_dir.mkdir(parents=True, exist_ok=True)
        
        if self.kmeans_fitted:
            with open(output_dir / "user_clustering_kmeans.joblib", 'wb') as f:
                pickle.dump(self.kmeans, f)
        
        if self.dbscan_fitted:
            with open(output_dir / "user_clustering_dbscan.joblib", 'wb') as f:
                pickle.dump(self.dbscan, f)
        
        with open(output_dir / "user_clustering_scaler.joblib", 'wb') as f:
            pickle.dump(self.scaler, f)
        
        print(f"✅ Saved clustering models to {output_dir}")
    
    def train(self, X: pd.DataFrame, use_kmeans: bool = True, use_dbscan: bool = True,
              n_clusters: int = 5, random_state: int = 42) -> Dict:
        """
        Train clustering models.
        
        Args:
            X: Feature DataFrame with user features
            use_kmeans: Whether to train K-Means
            use_dbscan: Whether to train DBSCAN
            n_clusters: Number of K-Means clusters
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
        
        results = {}
        
        # Train K-Means
        if use_kmeans:
            self.kmeans = KMeans(
                n_clusters=n_clusters,
                random_state=random_state,
                n_init=10
            )
            self.kmeans.fit(X_scaled)
            self.kmeans_fitted = True
            
            # Evaluate K-Means
            from sklearn.metrics import silhouette_score, davies_bouldin_score
            labels = self.kmeans.labels_
            silhouette = silhouette_score(X_scaled, labels)
            db_index = davies_bouldin_score(X_scaled, labels)
            
            results['kmeans'] = {
                'silhouette_score': float(silhouette),
                'davies_bouldin_index': float(db_index),
                'n_clusters': n_clusters,
                'inertia': float(self.kmeans.inertia_)
            }
            
            print(f"✅ K-Means trained: Silhouette={silhouette:.3f}, DB Index={db_index:.3f}")
        
        # Train DBSCAN
        if use_dbscan:
            self.dbscan = DBSCAN(eps=0.5, min_samples=5)
            self.dbscan.fit(X_scaled)
            self.dbscan_fitted = True
            
            n_clusters_dbscan = len(set(self.dbscan.labels_)) - (1 if -1 in self.dbscan.labels_ else 0)
            n_outliers = list(self.dbscan.labels_).count(-1)
            
            results['dbscan'] = {
                'n_clusters': n_clusters_dbscan,
                'n_outliers': n_outliers,
                'outlier_rate': float(n_outliers / len(X_scaled))
            }
            
            print(f"✅ DBSCAN trained: {n_clusters_dbscan} clusters, {n_outliers} outliers")
        
        # Save models
        self.save_models()
        
        return results
    
    def predict_cluster(self, features: Dict) -> Dict:
        """
        Predict cluster for a user.
        
        Args:
            features: Dict with user feature values
            
        Returns:
            Dict with cluster_id, cluster_label, confidence
        """
        if not (self.kmeans_fitted or self.dbscan_fitted):
            raise ValueError("Models not fitted. Train or load models first.")
        
        # Extract features
        feature_vector = np.array([[
            features.get(col, 0) for col in self.FEATURE_COLS
        ]])
        
        # Scale
        feature_vector_scaled = self.scaler.transform(feature_vector)
        
        # Predict with K-Means
        cluster_id = -1
        cluster_label = 'unknown'
        confidence = 0.0
        
        if self.kmeans_fitted:
            cluster_id = int(self.kmeans.predict(feature_vector_scaled)[0])
            cluster_label = self.CLUSTER_LABELS.get(cluster_id, 'unknown')
            
            # Calculate confidence as distance to cluster centroid
            centroid = self.kmeans.cluster_centers_[cluster_id]
            distance = np.linalg.norm(feature_vector_scaled[0] - centroid)
            # Normalize confidence (closer = more confident, inverse of distance)
            confidence = float(1 / (1 + distance))
        
        # Check if outlier with DBSCAN
        is_outlier = False
        if self.dbscan_fitted:
            dbscan_label = self.dbscan.fit_predict(feature_vector_scaled)[0]
            if dbscan_label == -1:
                is_outlier = True
                cluster_id = -1
                cluster_label = 'outlier'
                confidence = 0.3  # Lower confidence for outliers
        
        return {
            'cluster_id': cluster_id,
            'cluster_label': cluster_label,
            'confidence': round(confidence, 4),
            'is_outlier': is_outlier,
            'model_type': 'kmeans_dbscan_ensemble'
        }


# Singleton instance
_clustering_model = None

def get_clustering_model() -> UserClusteringModel:
    """Get singleton clustering model instance."""
    global _clustering_model
    if _clustering_model is None:
        _clustering_model = UserClusteringModel()
    return _clustering_model


if __name__ == "__main__":
    # Example usage
    import sys
    
    if "--train" in sys.argv:
        print("Training clustering models...")
        print("Note: Requires user feature data")
        # model = UserClusteringModel()
        # X = load_user_features()  # Would load from database
        # results = model.train(X)
        # print(f"Training complete: {results}")
    else:
        model = get_clustering_model()
        if model.kmeans_fitted or model.dbscan_fitted:
            test_features = {
                'cross_event_attendance': 5,
                'payment_method_diversity': 2,
                'avg_ticket_hold_time': 72,
                'social_graph_centrality': 0.7
            }
            result = model.predict_cluster(test_features)
            print(f"Cluster prediction: {result}")
        else:
            print("Models not loaded. Train models first or place trained models in artifacts/")

