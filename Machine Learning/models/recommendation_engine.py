"""
Recommendation Engine - Collaborative Filtering
Recommends events to users based on similarity patterns.
"""

import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Optional, List
from sklearn.preprocessing import StandardScaler
from sklearn.metrics.pairwise import cosine_similarity
import pickle
import json
from datetime import datetime


class RecommendationEngine:
    """
    Collaborative filtering-based event recommendation engine.
    
    Uses user clustering (K-Means) and event popularity for recommendations.
    
    Input: User features, event features
    Output: Recommendation score [0, 1] for user-event pairs
    """
    
    def __init__(self, model_path: Optional[Path] = None):
        """
        Initialize recommendation engine.
        
        Args:
            model_path: Path to trained model/config
        """
        self.user_clusters = {}  # Map user_id -> cluster_id
        self.cluster_event_preferences = {}  # Map cluster_id -> event_id -> preference_score
        self.event_popularity = {}  # Map event_id -> popularity_score
        self.is_fitted = False
        
        # Default path
        artifacts_dir = Path(__file__).parent.parent / "artifacts"
        self.model_path = model_path or artifacts_dir / "recommendation_engine.joblib"
        
        # Load model if exists
        self.load_model()
    
    def load_model(self) -> bool:
        """Load trained model from disk."""
        try:
            if self.model_path.exists():
                with open(self.model_path, 'rb') as f:
                    data = pickle.load(f)
                    self.user_clusters = data.get('user_clusters', {})
                    self.cluster_event_preferences = data.get('cluster_event_preferences', {})
                    self.event_popularity = data.get('event_popularity', {})
                    self.is_fitted = True
                print(f"✅ Loaded recommendation engine from {self.model_path}")
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
        
        data = {
            'user_clusters': self.user_clusters,
            'cluster_event_preferences': self.cluster_event_preferences,
            'event_popularity': self.event_popularity
        }
        
        with open(path, 'wb') as f:
            pickle.dump(data, f)
        
        print(f"✅ Saved recommendation engine to {path}")
    
    def train(self, user_event_interactions: pd.DataFrame, 
              user_clusters: Dict[str, int],
              event_popularity: Dict[int, float]) -> Dict:
        """
        Train recommendation engine.
        
        Args:
            user_event_interactions: DataFrame with columns [user_id, event_id, interaction_score]
                                    (interaction_score = 1 for purchase, 0.5 for view, etc.)
            user_clusters: Dict mapping user_id -> cluster_id (from clustering model)
            event_popularity: Dict mapping event_id -> popularity_score
            
        Returns:
            Dict with training metrics
        """
        self.user_clusters = user_clusters
        self.event_popularity = event_popularity
        
        # Compute cluster-event preferences
        # For each cluster, average interaction scores for events
        self.cluster_event_preferences = {}
        
        for cluster_id in set(user_clusters.values()):
            cluster_users = [uid for uid, cid in user_clusters.items() if cid == cluster_id]
            cluster_interactions = user_event_interactions[
                user_event_interactions['user_id'].isin(cluster_users)
            ]
            
            # Average preference per event for this cluster
            event_prefs = cluster_interactions.groupby('event_id')['interaction_score'].mean().to_dict()
            self.cluster_event_preferences[cluster_id] = event_prefs
        
        self.is_fitted = True
        
        # Evaluate (simple cross-validation)
        # Would do proper evaluation in production
        print("✅ Recommendation engine trained")
        
        # Save model
        self.save_model()
        
        return {
            'n_clusters': len(set(user_clusters.values())),
            'n_users': len(user_clusters),
            'n_events': len(event_popularity)
        }
    
    def recommend_score(self, user_features: Dict, event_features: Dict) -> Dict:
        """
        Calculate recommendation score for user-event pair.
        
        Args:
            user_features: Dict with user info (wallet_address, cluster_id, etc.)
            event_features: Dict with event info (event_id, popularity_score, etc.)
            
        Returns:
            Dict with recommendation_score, confidence, recommendation_reason
        """
        if not self.is_fitted:
            # Return default recommendation based on popularity
            event_id = event_features.get('event_id')
            popularity = event_features.get('event_popularity_score', self.event_popularity.get(event_id, 0.5))
            return {
                'recommendation_score': round(popularity, 3),
                'confidence': 0.3,
                'recommendation_reason': 'popularity_only',
                'model_type': 'collaborative_filtering',
                'note': 'model_not_fitted'
            }
        
        wallet_address = user_features.get('wallet_address')
        cluster_id = user_features.get('cluster_id')
        event_id = event_features.get('event_id')
        
        # Get cluster preference for this event
        cluster_preference = 0.5  # Default
        if cluster_id is not None and cluster_id in self.cluster_event_preferences:
            cluster_preference = self.cluster_event_preferences[cluster_id].get(event_id, 0.5)
        
        # Get event popularity
        popularity = event_features.get('event_popularity_score', 
                                       self.event_popularity.get(event_id, 0.5))
        
        # Get user engagement (attendance history)
        attendance = user_features.get('cross_event_attendance', 0)
        engagement_factor = min(attendance / 10.0, 1.0)  # Normalize to [0, 1]
        
        # Combine: 40% cluster preference, 40% popularity, 20% user engagement
        recommendation_score = (
            0.4 * cluster_preference +
            0.4 * popularity +
            0.2 * engagement_factor
        )
        recommendation_score = min(recommendation_score, 1.0)
        
        # Determine recommendation reason
        if cluster_preference > 0.7:
            reason = "similar_users_liked"
        elif popularity > 0.7:
            reason = "popular_event"
        elif engagement_factor > 0.7:
            reason = "high_user_engagement"
        else:
            reason = "balanced_score"
        
        # Confidence = distance from neutral (0.5)
        confidence = abs(recommendation_score - 0.5) * 2
        
        return {
            'recommendation_score': round(recommendation_score, 4),
            'confidence': round(confidence, 4),
            'recommendation_reason': reason,
            'cluster_preference': round(cluster_preference, 3),
            'popularity': round(popularity, 3),
            'engagement_factor': round(engagement_factor, 3),
            'model_type': 'collaborative_filtering',
            'timestamp': datetime.now().isoformat()
        }
    
    def recommend_events(self, user_features: Dict, events: List[Dict], top_k: int = 10) -> List[Dict]:
        """
        Recommend top K events for a user.
        
        Args:
            user_features: User feature dict
            events: List of event dicts with event_id and other features
            top_k: Number of recommendations to return
            
        Returns:
            List of events sorted by recommendation score (highest first)
        """
        scored_events = []
        
        for event in events:
            score_result = self.recommend_score(user_features, event)
            scored_events.append({
                **event,
                'recommendation_score': score_result['recommendation_score'],
                'confidence': score_result['confidence'],
                'recommendation_reason': score_result['recommendation_reason']
            })
        
        # Sort by recommendation score (descending)
        scored_events.sort(key=lambda x: x['recommendation_score'], reverse=True)
        
        return scored_events[:top_k]


# Singleton instance
_recommendation_engine = None

def get_recommendation_engine() -> RecommendationEngine:
    """Get singleton recommendation engine instance."""
    global _recommendation_engine
    if _recommendation_engine is None:
        _recommendation_engine = RecommendationEngine()
    return _recommendation_engine


if __name__ == "__main__":
    # Example usage
    import sys
    
    if "--train" in sys.argv:
        print("Training recommendation engine...")
        print("Note: Requires user-event interaction data")
        # engine = RecommendationEngine()
        # interactions = load_user_event_interactions()
        # clusters = load_user_clusters()
        # popularity = load_event_popularity()
        # results = engine.train(interactions, clusters, popularity)
        # print(f"Training complete: {results}")
    else:
        engine = get_recommendation_engine()
        user_features = {
            'wallet_address': '0x123...',
            'cluster_id': 1,  # regular_user
            'cross_event_attendance': 5
        }
        event_features = {
            'event_id': 42,
            'event_popularity_score': 0.8
        }
        result = engine.recommend_score(user_features, event_features)
        print(f"Recommendation: {result}")

