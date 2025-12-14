"""Feature Engineering Pipeline - Derived Features for ML Models."""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from data_control.db_connection import get_db_connection, return_db_connection, get_redis_client
import json


class FeatureEngineer:
    """Engineer features from raw transaction and event data."""
    
    def __init__(self):
        self.db_conn = None
        self.redis_client = None
    
    def _get_db(self):
        """Get database connection."""
        if self.db_conn is None:
            self.db_conn = get_db_connection()
        return self.db_conn
    
    def _get_redis(self):
        """Get Redis client."""
        if self.redis_client is None:
            self.redis_client = get_redis_client()
        return self.redis_client
    
    def compute_features(self, transaction_id: str, wallet_address: str, 
                        event_id: Optional[int] = None) -> Dict:
        """
        Compute all 10 core features for a transaction.
        
        Args:
            transaction_id: Unique transaction identifier
            wallet_address: Wallet address making the transaction
            event_id: Optional event ID
            
        Returns:
            Dict with all engineered features
        """
        features = {
            'txn_velocity_1h': self._txn_velocity(wallet_address, hours=1),
            'wallet_age_days': self._wallet_age(wallet_address),
            'avg_ticket_hold_time': self._avg_ticket_hold_time(wallet_address),
            'event_popularity_score': self._event_popularity_score(event_id) if event_id else 0.5,
            'price_deviation_ratio': self._price_deviation_ratio(transaction_id),
            'cross_event_attendance': self._cross_event_attendance(wallet_address),
            'geo_velocity_flag': self._geo_velocity_flag(wallet_address),
            'payment_method_diversity': self._payment_method_diversity(wallet_address),
            'social_graph_centrality': self._social_graph_centrality(wallet_address),
            'time_to_first_resale': self._time_to_first_resale(transaction_id)
        }
        
        # Cache features in Redis (5-minute TTL)
        redis_client = self._get_redis()
        if redis_client:
            cache_key = f"features:{transaction_id}"
            redis_client.setex(cache_key, 300, json.dumps(features))
        
        return features
    
    def _txn_velocity(self, wallet_address: str, hours: int = 1) -> int:
        """Count transactions from wallet in last N hours."""
        conn = self._get_db()
        if not conn:
            return 0
        
        try:
            with conn.cursor() as cur:
                query = """
                    SELECT COUNT(*) 
                    FROM orders o
                    JOIN wallets w ON w.wallet_id = o.buyer_wallet_id
                    WHERE w.address = %s
                    AND o.created_at > NOW() - INTERVAL '%s hours'
                """
                cur.execute(query, (wallet_address, hours))
                result = cur.fetchone()
                return result[0] if result else 0
        except Exception as e:
            print(f"Error computing txn_velocity: {e}")
            return 0
    
    def _wallet_age_days(self, wallet_address: str) -> float:
        """Calculate wallet age in days."""
        conn = self._get_db()
        if not conn:
            return 30.0  # Default
        
        try:
            with conn.cursor() as cur:
                query = """
                    SELECT MIN(o.created_at) as first_transaction
                    FROM orders o
                    JOIN wallets w ON w.wallet_id = o.buyer_wallet_id
                    WHERE w.address = %s
                """
                cur.execute(query, (wallet_address,))
                result = cur.fetchone()
                if result and result[0]:
                    first_txn = result[0]
                    age_delta = datetime.now() - first_txn
                    return age_delta.total_seconds() / 86400.0
                return 30.0  # Default for new wallets
        except Exception as e:
            print(f"Error computing wallet_age: {e}")
            return 30.0
    
    def _avg_ticket_hold_time(self, wallet_address: str) -> float:
        """Calculate average ticket hold time in hours."""
        conn = self._get_db()
        if not conn:
            return 48.0  # Default
        
        try:
            with conn.cursor() as cur:
                query = """
                    SELECT AVG(EXTRACT(EPOCH FROM (t.last_transfer_at - t.minted_at)) / 3600.0)
                    FROM tickets t
                    JOIN wallets w ON w.wallet_id = t.owner_wallet_id
                    WHERE w.address = %s
                    AND t.last_transfer_at IS NOT NULL
                    AND t.minted_at IS NOT NULL
                """
                cur.execute(query, (wallet_address,))
                result = cur.fetchone()
                avg_hours = float(result[0]) if result and result[0] else 48.0
                return avg_hours
        except Exception as e:
            print(f"Error computing avg_ticket_hold_time: {e}")
            return 48.0
    
    def _event_popularity_score(self, event_id: int) -> float:
        """Calculate event popularity: (tickets_sold / capacity) × (days_until_event)^-0.5."""
        conn = self._get_db()
        if not conn:
            return 0.5  # Default
        
        try:
            with conn.cursor() as cur:
                query = """
                    SELECT 
                        COALESCE(COUNT(t.ticket_id), 0) as tickets_sold,
                        e.capacity,
                        EXTRACT(EPOCH FROM (e.event_date - NOW())) / 86400.0 as days_until_event
                    FROM events e
                    LEFT JOIN tickets t ON t.event_id = e.event_id
                    WHERE e.event_id = %s
                    GROUP BY e.event_id, e.capacity, e.event_date
                """
                cur.execute(query, (event_id,))
                result = cur.fetchone()
                
                if result:
                    tickets_sold = result[0] or 0
                    capacity = result[1] or 1
                    days_until = max(result[2] or 1.0, 0.1)  # Avoid division by zero
                    
                    sell_through = tickets_sold / capacity if capacity > 0 else 0
                    time_factor = days_until ** -0.5
                    popularity = sell_through * time_factor
                    return min(popularity, 1.0)  # Cap at 1.0
                return 0.5
        except Exception as e:
            print(f"Error computing event_popularity_score: {e}")
            return 0.5
    
    def _price_deviation_ratio(self, transaction_id: str) -> float:
        """Calculate price deviation from floor price."""
        conn = self._get_db()
        if not conn:
            return 0.0
        
        try:
            with conn.cursor() as cur:
                # Get transaction price and event floor price
                query = """
                    SELECT 
                        t.price_paid,
                        e.base_price as floor_price
                    FROM transactions t
                    JOIN events e ON e.event_id = t.event_id
                    WHERE t.transaction_id = %s
                """
                cur.execute(query, (transaction_id,))
                result = cur.fetchone()
                
                if result and result[0] and result[1]:
                    price_paid = float(result[0])
                    floor_price = float(result[1])
                    if floor_price > 0:
                        return (price_paid - floor_price) / floor_price
                return 0.0
        except Exception as e:
            print(f"Error computing price_deviation_ratio: {e}")
            return 0.0
    
    def _cross_event_attendance(self, wallet_address: str) -> int:
        """Count distinct events attended by wallet."""
        conn = self._get_db()
        if not conn:
            return 0
        
        try:
            with conn.cursor() as cur:
                query = """
                    SELECT COUNT(DISTINCT t.event_id)
                    FROM tickets t
                    JOIN wallets w ON w.wallet_id = t.owner_wallet_id
                    WHERE w.address = %s
                """
                cur.execute(query, (wallet_address,))
                result = cur.fetchone()
                return result[0] if result else 0
        except Exception as e:
            print(f"Error computing cross_event_attendance: {e}")
            return 0
    
    def _geo_velocity_flag(self, wallet_address: str) -> int:
        """Flag if IP location changed >500km in <1h (binary)."""
        # Simplified: check if wallet has transactions from different IPs in short time
        conn = self._get_db()
        if not conn:
            return 0
        
        try:
            with conn.cursor() as cur:
                # This is a simplified version - in production, would use IP geolocation
                # Note: IP address tracking would need to be added to orders table
                query = """
                    SELECT COUNT(DISTINCT o.order_id) as distinct_orders
                    FROM orders o
                    JOIN wallets w ON w.wallet_id = o.buyer_wallet_id
                    WHERE w.address = %s
                    AND o.created_at > NOW() - INTERVAL '1 hour'
                """
                cur.execute(query, (wallet_address,))
                # For now, return 0 (geo velocity requires IP tracking)
                # In production, would use IP geolocation data
                return 0
        except Exception as e:
            print(f"Error computing geo_velocity_flag: {e}")
            return 0
    
    def _payment_method_diversity(self, wallet_address: str) -> int:
        """Count unique payment methods used by wallet."""
        conn = self._get_db()
        if not conn:
            return 1
        
        try:
            with conn.cursor() as cur:
                # Note: payment_method would need to be added to orders table
                # For now, return 1 (default)
                return 1
                result = cur.fetchone()
                return result[0] if result else 1
        except Exception as e:
            print(f"Error computing payment_method_diversity: {e}")
            return 1
    
    def _social_graph_centrality(self, wallet_address: str) -> float:
        """Calculate PageRank/centrality score in referral network."""
        # Simplified: return default for now
        # In production, would compute actual graph centrality
        return 0.5
    
    def _time_to_first_resale(self, transaction_id: str) -> float:
        """Time from mint to first resale in minutes."""
        conn = self._get_db()
        if not conn:
            return 0.0
        
        try:
            with conn.cursor() as cur:
                query = """
                    SELECT 
                        t.minted_at as mint_time,
                        MIN(r.listed_at) as first_resale_time
                    FROM tickets t
                    LEFT JOIN resales r ON r.ticket_id = t.ticket_id
                    WHERE t.ticket_id = (
                        SELECT o.ticket_id FROM orders o WHERE o.order_id::text = %s
                    )
                    GROUP BY t.ticket_id, t.minted_at
                """
                cur.execute(query, (transaction_id,))
                result = cur.fetchone()
                
                if result and result[0] and result[1]:
                    mint_time = result[0]
                    resale_time = result[1]
                    delta = resale_time - mint_time
                    return delta.total_seconds() / 60.0
                return 0.0
        except Exception as e:
            print(f"Error computing time_to_first_resale: {e}")
            return 0.0
    
    def compute_derived_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute derived features for batch processing.
        
        Derived features:
        - avg_tx_per_day: Average transactions per day for wallet
        - tag_frequency: Frequency of event tags in user's history
        - event_lag: Time between event creation and first ticket sale
        - user_activity_delta: Change in user activity (transactions) week-over-week
        """
        # avg_tx_per_day
        df['avg_tx_per_day'] = df.groupby('wallet_address')['transaction_id'].transform(
            lambda x: x.count() / max((x.index.max() - x.index.min()).days, 1) if len(x) > 1 else 1
        )
        
        # tag_frequency (simplified - would need event_tags table)
        df['tag_frequency'] = 1.0  # Placeholder
        
        # event_lag
        if 'event_created_at' in df.columns and 'first_ticket_sale' in df.columns:
            df['event_lag'] = (df['first_ticket_sale'] - df['event_created_at']).dt.total_seconds() / 3600.0
        else:
            df['event_lag'] = 0.0
        
        # user_activity_delta (week-over-week change)
        df['user_activity_delta'] = df.groupby('wallet_address')['transaction_id'].transform(
            lambda x: (x.count() - x.iloc[:-7].count()) if len(x) > 7 else 0
        )
        
        return df


# Singleton instance
_feature_engineer = None

def get_feature_engineer():
    """Get singleton feature engineer instance."""
    global _feature_engineer
    if _feature_engineer is None:
        _feature_engineer = FeatureEngineer()
    return _feature_engineer

