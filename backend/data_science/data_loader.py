"""
Data Loader - Database Access Layer for ML Models
Provides abstraction for fetching training/inference data from Supabase.
"""
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from supabase import Client

logger = logging.getLogger(__name__)


class DataLoader:
    """
    Handles all database operations for ML models.
    Separates data access logic from model logic.
    """
    
    def __init__(self, supabase_client: Client):
        """
        Initialize data loader with Supabase client.
        
        Args:
            supabase_client: Supabase client instance (admin preferred)
        """
        self.db = supabase_client
    
    # ==================== TRAINING DATA ====================
    
    def fetch_transaction_history(
        self, 
        limit: int = 1000,
        days_back: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Fetch historical transactions for training fraud/risk models.
        
        Args:
            limit: Maximum number of records to fetch
            days_back: How many days of history to fetch
            
        Returns:
            List of transaction dictionaries
        """
        try:
            cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()
            
            response = self.db.table("transactions") \
                .select("*") \
                .gte("created_at", cutoff_date) \
                .order("created_at", desc=True) \
                .limit(limit) \
                .execute()
            
            logger.info(f"Fetched {len(response.data)} transactions for training")
            return response.data
        except Exception as e:
            logger.error(f"Error fetching transaction history: {e}")
            return []
    
    def fetch_user_behavior(
        self, 
        user_id: Optional[str] = None,
        limit: int = 500
    ) -> List[Dict[str, Any]]:
        """
        Fetch user activity patterns for segmentation/recommender.
        
        Args:
            user_id: Specific user ID (None for all users)
            limit: Maximum number of records
            
        Returns:
            List of user activity dictionaries
        """
        try:
            query = self.db.table("users").select("*")
            
            if user_id:
                query = query.eq("id", user_id)
            
            response = query.limit(limit).execute()
            
            logger.info(f"Fetched {len(response.data)} user records")
            return response.data
        except Exception as e:
            logger.error(f"Error fetching user behavior: {e}")
            return []
    
    def fetch_event_data(
        self, 
        limit: int = 500,
        include_past: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Fetch event metadata for recommender/trend models.
        
        Args:
            limit: Maximum number of events
            include_past: Whether to include past events
            
        Returns:
            List of event dictionaries
        """
        try:
            query = self.db.table("events").select("*")
            
            if not include_past:
                query = query.gte("event_date", datetime.now().isoformat())
            
            response = query.order("created_at", desc=True).limit(limit).execute()
            
            logger.info(f"Fetched {len(response.data)} events")
            return response.data
        except Exception as e:
            logger.error(f"Error fetching event data: {e}")
            return []
    
    def fetch_ticket_data(
        self,
        limit: int = 1000,
        days_back: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Fetch ticket data for scalping detection.
        
        Args:
            limit: Maximum number of tickets
            days_back: How many days of history
            
        Returns:
            List of ticket dictionaries
        """
        try:
            cutoff_date = (datetime.now() - timedelta(days=days_back)).isoformat()
            
            response = self.db.table("tickets") \
                .select("*") \
                .gte("created_at", cutoff_date) \
                .order("created_at", desc=True) \
                .limit(limit) \
                .execute()
            
            logger.info(f"Fetched {len(response.data)} tickets")
            return response.data
        except Exception as e:
            logger.error(f"Error fetching ticket data: {e}")
            return []
    
    # ==================== INFERENCE DATA ====================
    
    def fetch_transaction_by_id(self, transaction_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch single transaction for real-time prediction.
        
        Args:
            transaction_id: Transaction ID
            
        Returns:
            Transaction dictionary or None
        """
        try:
            response = self.db.table("transactions") \
                .select("*") \
                .eq("id", transaction_id) \
                .single() \
                .execute()
            
            return response.data
        except Exception as e:
            logger.error(f"Error fetching transaction {transaction_id}: {e}")
            return None
    
    def fetch_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch user profile for segmentation/personalization.
        
        Args:
            user_id: User ID
            
        Returns:
            User dictionary or None
        """
        try:
            response = self.db.table("users") \
                .select("*") \
                .eq("id", user_id) \
                .single() \
                .execute()
            
            return response.data
        except Exception as e:
            logger.error(f"Error fetching user {user_id}: {e}")
            return None
    
    def fetch_user_transaction_count(self, user_id: str) -> int:
        """
        Get transaction count for a user (for risk scoring).
        
        Args:
            user_id: User ID
            
        Returns:
            Number of transactions
        """
        try:
            response = self.db.table("transactions") \
                .select("id", count="exact") \
                .eq("user_id", user_id) \
                .execute()
            
            return response.count or 0
        except Exception as e:
            logger.error(f"Error counting transactions for user {user_id}: {e}")
            return 0
    
    # ==================== PREDICTIONS STORAGE ====================
    
    def save_prediction(
        self,
        model_name: str,
        input_data: Dict[str, Any],
        output: Any,
        confidence: Optional[float] = None,
        latency_ms: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Save model prediction to database.
        
        Args:
            model_name: Name of the model
            input_data: Input features/data
            output: Model output
            confidence: Prediction confidence (0-1)
            latency_ms: Inference latency
            metadata: Additional metadata
            
        Returns:
            True if successful, False otherwise
        """
        try:
            record = {
                "model_name": model_name,
                "input_data": input_data,
                "output": output if isinstance(output, dict) else {"value": output},
                "confidence": confidence,
                "latency_ms": latency_ms,
                "metadata": metadata or {},
                "created_at": datetime.now().isoformat()
            }
            
            self.db.table("model_predictions").insert(record).execute()
            logger.info(f"Saved prediction for {model_name}")
            return True
        except Exception as e:
            logger.error(f"Error saving prediction: {e}")
            return False
    
    def save_model_metrics(
        self,
        model_name: str,
        metrics: Dict[str, float],
        model_version: str = "1.0",
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Save model performance metrics.
        
        Args:
            model_name: Name of the model
            metrics: Dictionary of metric_name -> metric_value
            model_version: Model version
            metadata: Additional metadata
            
        Returns:
            True if successful, False otherwise
        """
        try:
            records = []
            for metric_name, metric_value in metrics.items():
                records.append({
                    "model_name": model_name,
                    "model_version": model_version,
                    "metric_name": metric_name,
                    "metric_value": float(metric_value),
                    "metric_metadata": metadata or {},
                    "evaluation_date": datetime.now().isoformat()
                })
            
            self.db.table("model_metrics").insert(records).execute()
            logger.info(f"Saved {len(metrics)} metrics for {model_name}")
            return True
        except Exception as e:
            logger.error(f"Error saving metrics: {e}")
            return False
    
    def save_training_data(
        self,
        model_name: str,
        features: Dict[str, Any],
        labels: Optional[Dict[str, Any]] = None,
        source_table: Optional[str] = None,
        source_id: Optional[int] = None
    ) -> bool:
        """
        Save preprocessed training data.
        
        Args:
            model_name: Name of the model
            features: Feature dictionary
            labels: Label dictionary
            source_table: Source table name
            source_id: Source record ID
            
        Returns:
            True if successful, False otherwise
        """
        try:
            record = {
                "model_name": model_name,
                "features": features,
                "labels": labels,
                "source_table": source_table,
                "source_id": source_id,
                "created_at": datetime.now().isoformat()
            }
            
            self.db.table("model_training_data").insert(record).execute()
            return True
        except Exception as e:
            logger.error(f"Error saving training data: {e}")
            return False
    
    # ==================== AGGREGATIONS ====================
    
    def get_user_transaction_stats(self, user_id: str) -> Dict[str, Any]:
        """
        Get aggregated transaction statistics for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            Dictionary with stats (count, avg_amount, total_amount, etc.)
        """
        try:
            transactions = self.db.table("transactions") \
                .select("*") \
                .eq("user_id", user_id) \
                .execute()
            
            if not transactions.data:
                return {
                    "count": 0,
                    "avg_amount": 0,
                    "total_amount": 0,
                    "max_amount": 0
                }
            
            amounts = [t.get("amount", 0) for t in transactions.data]
            
            return {
                "count": len(transactions.data),
                "avg_amount": sum(amounts) / len(amounts) if amounts else 0,
                "total_amount": sum(amounts),
                "max_amount": max(amounts) if amounts else 0,
                "min_amount": min(amounts) if amounts else 0
            }
        except Exception as e:
            logger.error(f"Error getting user stats: {e}")
            return {"count": 0, "avg_amount": 0, "total_amount": 0, "max_amount": 0}


# Singleton instance (optional, can be instantiated per request)
_data_loader_instance: Optional[DataLoader] = None


def get_data_loader(supabase_client: Client) -> DataLoader:
    """
    Get or create DataLoader instance.
    
    Args:
        supabase_client: Supabase client
        
    Returns:
        DataLoader instance
    """
    global _data_loader_instance
    if _data_loader_instance is None:
        _data_loader_instance = DataLoader(supabase_client)
    return _data_loader_instance
