import time
from typing import Dict, Any, List
import json
import os

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False

class FeatureStore:
    """
    Manages feature engineering and retrieval.
    Supports Redis or in-memory storage.
    """
    def __init__(self):
        self.redis_client = None
        if REDIS_AVAILABLE:
            try:
                # Connect to local Redis (default port 6379)
                self.redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
                self.redis_client.ping() # Check connection
            except Exception:
                self.redis_client = None # Fallback to in-memory

        # In-memory store for sliding windows (fallback)
        self._store: Dict[str, List[tuple]] = {}

    def add_event(self, entity_id: str, feature_name: str, value: float):
        """Adds an event to the feature store."""
        key = f"{feature_name}:{entity_id}"
        timestamp = time.time()
        
        if self.redis_client:
            # Use Redis Sorted Set (ZSET) for time-series data
            # Score = timestamp, Member = value (or unique ID if values duplicate)
            # For simplicity, we store "timestamp:value" as member
            member = f"{timestamp}:{value}"
            self.redis_client.zadd(key, {member: timestamp})
            # Cleanup old events (older than 1 hour)
            cutoff = timestamp - 3600
            self.redis_client.zremrangebyscore(key, 0, cutoff)
        else:
            if key not in self._store:
                self._store[key] = []
            self._store[key].append((timestamp, value))
            cutoff = timestamp - 3600
            self._store[key] = [x for x in self._store[key] if x[0] > cutoff]

    def get_sliding_window_count(self, entity_id: str, feature_name: str, window_seconds: int) -> int:
        """Returns the count of events in the last N seconds."""
        key = f"{feature_name}:{entity_id}"
        cutoff = time.time() - window_seconds
        
        if self.redis_client:
            return self.redis_client.zcount(key, cutoff, "+inf")
        else:
            if key not in self._store:
                return 0
            return sum(1 for t, v in self._store[key] if t > cutoff)

    def get_sliding_window_avg(self, entity_id: str, feature_name: str, window_seconds: int) -> float:
        """Returns the average value of events in the last N seconds."""
        key = f"{feature_name}:{entity_id}"
        cutoff = time.time() - window_seconds
        
        if self.redis_client:
            # Get all elements in range
            elements = self.redis_client.zrangebyscore(key, cutoff, "+inf")
            if not elements:
                return 0.0
            values = [float(e.split(":")[1]) for e in elements]
            return sum(values) / len(values)
        else:
            if key not in self._store:
                return 0.0
            values = [v for t, v in self._store[key] if t > cutoff]
            if not values:
                return 0.0
            return sum(values) / len(values)
    
    # ==================== DATABASE FEATURE EXTRACTION ====================
    
    def extract_risk_features(self, transaction_data: Dict[str, Any], user_stats: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Extract features for risk scoring from transaction data.
        
        Args:
            transaction_data: Transaction record from database
            user_stats: Optional user statistics (tx count, avg amount, etc.)
            
        Returns:
            Feature dictionary for risk model
        """
        features = {
            "amount": float(transaction_data.get("amount", 0)),
            "user_tx_count": user_stats.get("count", 0) if user_stats else 0,
            "avg_user_amount": user_stats.get("avg_amount", 0) if user_stats else 0,
            "max_user_amount": user_stats.get("max_amount", 0) if user_stats else 0
        }
        return features
    
    def extract_recommender_features(self, user_data: Dict[str, Any], event_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract features for recommender system.
        
        Args:
            user_data: User profile from database
            event_data: List of event records
            
        Returns:
            Feature dictionary for recommender
        """
        # Get user preferences (could be from user profile or past behavior)
        preferred_category = user_data.get("preferred_category", "general")
        
        # Filter events by category
        matching_events = [
            e for e in event_data 
            if e.get("category", "").lower() == preferred_category.lower()
        ]
        
        return {
            "user_id": user_data.get("id"),
            "preferred_category": preferred_category,
            "matching_events": matching_events[:10]  # Top 10
        }
    
    def extract_segmentation_features(self, user_stats: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract features for user segmentation.
        
        Args:
            user_stats: User transaction statistics
            
        Returns:
            Feature dictionary for clustering
        """
        return {
            "avg_transaction_value": user_stats.get("avg_amount", 0),
            "transaction_frequency": user_stats.get("count", 0),
            "total_spent": user_stats.get("total_amount", 0)
        }
    
    def extract_bot_features(self, transaction_data: Dict[str, Any], user_stats: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Extract features for bot detection.
        
        Args:
            transaction_data: Transaction record
            user_stats: User statistics
            
        Returns:
            Feature dictionary for bot detection
        """
        return {
            "transaction_velocity": user_stats.get("count", 0) if user_stats else 0,
            "amount_variance": user_stats.get("max_amount", 0) - user_stats.get("min_amount", 0) if user_stats else 0,
            "avg_amount": user_stats.get("avg_amount", 0) if user_stats else 0
        }
    
    def extract_scalping_features(self, ticket_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Extract features for scalping detection.
        
        Args:
            ticket_data: List of ticket records
            
        Returns:
            Feature dictionary for scalping detection
        """
        if not ticket_data:
            return {"resale_count": 0, "price_markup": 0}
        
        # Count resales
        resale_count = sum(1 for t in ticket_data if t.get("is_resale", False))
        
        # Calculate average markup
        markups = []
        for ticket in ticket_data:
            if ticket.get("is_resale") and ticket.get("original_price"):
                markup = (ticket.get("price", 0) - ticket.get("original_price", 0)) / ticket.get("original_price", 1)
                markups.append(markup)
        
        avg_markup = sum(markups) / len(markups) if markups else 0
        
        return {
            "resale_count": resale_count,
            "price_markup": avg_markup,
            "total_tickets": len(ticket_data)
        }

    def extract_fair_price_features(self, ticket_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract features for fair price prediction.
        
        Args:
            ticket_data: Ticket record
            
        Returns:
            Feature dictionary for fair price model
        """
        # In a real app, popularity might come from a separate table or analytics
        popularity = ticket_data.get("popularity_score", 5)
        
        # Calculate days left until event
        days_left = 10 # Default
        event_date_str = ticket_data.get("event_date")
        if event_date_str:
            try:
                from datetime import datetime
                event_date = datetime.fromisoformat(event_date_str.replace('Z', '+00:00'))
                days_left = (event_date - datetime.now(event_date.tzinfo)).days
                days_left = max(0, days_left)
            except Exception:
                pass
                
        return {
            "original_price": float(ticket_data.get("original_price", 0)),
            "popularity": popularity,
            "days_left": days_left
        }

# Global instance
feature_store = FeatureStore()
