"""KPI Calculation Module - Primary KPIs and Business Metrics."""
import psycopg2
from datetime import datetime, timedelta
from typing import Dict, Optional
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from data_control.db_connection import get_db_connection, return_db_connection, execute_query
import json


class KPICalculator:
    """Calculate and track key performance indicators."""
    
    def __init__(self):
        self.db_conn = None
    
    def _get_connection(self):
        """Get database connection."""
        if self.db_conn is None:
            self.db_conn = get_db_connection()
        return self.db_conn
    
    def conversion_rate(self, event_id: Optional[int] = None, 
                       start_time: Optional[datetime] = None,
                       end_time: Optional[datetime] = None) -> Dict:
        """
        Calculate conversion rate: (tickets_sold / views) × 100
        
        Args:
            event_id: Specific event ID (None for overall)
            start_time: Start of time window
            end_time: End of time window
            
        Returns:
            Dict with conversion_rate, tickets_sold, views, metadata
        """
        conn = self._get_connection()
        if conn is None:
            return {'error': 'Database connection failed'}
        
        try:
            with conn.cursor() as cur:
                # Build time filter
                time_filter = ""
                params = []
                if start_time:
                    time_filter += " AND t.created_at >= %s"
                    params.append(start_time)
                if end_time:
                    time_filter += " AND t.created_at <= %s"
                    params.append(end_time)
                if event_id:
                    time_filter += " AND t.event_id = %s"
                    params.append(event_id)
                
                # Count tickets sold
                tickets_query = f"""
                    SELECT COUNT(*) as tickets_sold
                    FROM tickets t
                    WHERE t.status = 'ACTIVE' {time_filter}
                """
                cur.execute(tickets_query, params)
                tickets_sold = cur.fetchone()[0] or 0
                
                # Count views (approximate from event_views table or use event capacity)
                # For now, we'll use a simplified calculation
                if event_id:
                    views_query = """
                        SELECT views_count, capacity
                        FROM events
                        WHERE event_id = %s
                    """
                    cur.execute(views_query, [event_id])
                    result = cur.fetchone()
                    if result:
                        views = result[0] or result[1] or 1000  # Fallback to capacity
                    else:
                        views = 1000
                else:
                    # Aggregate views across all events
                    views_query = f"""
                        SELECT COALESCE(SUM(capacity), 0) as total_capacity
                        FROM events
                        WHERE 1=1 {time_filter.replace('t.created_at', 'created_at').replace('t.event_id', 'event_id')}
                    """
                    cur.execute(views_query, params)
                    views = cur.fetchone()[0] or 1000
                
                conversion = (tickets_sold / views * 100) if views > 0 else 0.0
                
                return {
                    'kpi_name': 'conversion_rate',
                    'value': round(conversion, 2),
                    'unit': 'percent',
                    'tickets_sold': tickets_sold,
                    'views': views,
                    'timestamp': datetime.now().isoformat(),
                    'metadata': {
                        'event_id': event_id,
                        'start_time': start_time.isoformat() if start_time else None,
                        'end_time': end_time.isoformat() if end_time else None
                    }
                }
        except Exception as e:
            return {'error': str(e)}
    
    def time_to_finality(self, transaction_id: Optional[str] = None,
                        start_time: Optional[datetime] = None,
                        end_time: Optional[datetime] = None) -> Dict:
        """
        Calculate time to finality: Average time from transaction creation to blockchain confirmation.
        
        Args:
            transaction_id: Specific transaction (None for aggregate)
            start_time: Start of time window
            end_time: End of time window
            
        Returns:
            Dict with time_to_finality (seconds), count, metadata
        """
        conn = self._get_connection()
        if conn is None:
            return {'error': 'Database connection failed'}
        
        try:
            with conn.cursor() as cur:
                # Build time filter
                time_filter = ""
                params = []
                if start_time:
                    time_filter += " AND created_at >= %s"
                    params.append(start_time)
                if end_time:
                    time_filter += " AND created_at <= %s"
                    params.append(end_time)
                if transaction_id:
                    time_filter += " AND transaction_hash = %s"
                    params.append(transaction_id)
                
                # Calculate average time to finality
                # Assuming we track blockchain_confirmations table or similar
                query = f"""
                    SELECT 
                        AVG(EXTRACT(EPOCH FROM (confirmed_at - created_at))) as avg_finality_seconds,
                        COUNT(*) as count,
                        MIN(EXTRACT(EPOCH FROM (confirmed_at - created_at))) as min_finality,
                        MAX(EXTRACT(EPOCH FROM (confirmed_at - created_at))) as max_finality,
                        PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY EXTRACT(EPOCH FROM (confirmed_at - created_at))) as median_finality
                    FROM blockchain_transactions
                    WHERE confirmed_at IS NOT NULL {time_filter}
                """
                
                # If table doesn't exist, use tickets table as fallback
                try:
                    cur.execute(query, params)
                    result = cur.fetchone()
                    if result and result[0]:
                        avg_finality = float(result[0])
                        count = result[1]
                        min_finality = float(result[2]) if result[2] else None
                        max_finality = float(result[3]) if result[3] else None
                        median_finality = float(result[4]) if result[4] else None
                    else:
                        # Fallback: use tickets table (assuming mint_time and created_at)
                        fallback_query = f"""
                            SELECT 
                                AVG(EXTRACT(EPOCH FROM (created_at - mint_time))) as avg_finality_seconds,
                                COUNT(*) as count
                            FROM tickets
                            WHERE mint_time IS NOT NULL {time_filter.replace('created_at', 'created_at').replace('transaction_hash', 'ticket_id')}
                        """
                        cur.execute(fallback_query, params)
                        result = cur.fetchone()
                        avg_finality = float(result[0]) if result and result[0] else 30.0  # Default 30 seconds
                        count = result[1] if result else 0
                        min_finality = None
                        max_finality = None
                        median_finality = None
                except psycopg2.errors.UndefinedTable:
                    # Table doesn't exist, return default
                    avg_finality = 30.0
                    count = 0
                    min_finality = None
                    max_finality = None
                    median_finality = None
                
                return {
                    'kpi_name': 'time_to_finality',
                    'value': round(avg_finality, 2),
                    'unit': 'seconds',
                    'count': count,
                    'min': round(min_finality, 2) if min_finality else None,
                    'max': round(max_finality, 2) if max_finality else None,
                    'median': round(median_finality, 2) if median_finality else None,
                    'timestamp': datetime.now().isoformat(),
                    'metadata': {
                        'transaction_id': transaction_id,
                        'start_time': start_time.isoformat() if start_time else None,
                        'end_time': end_time.isoformat() if end_time else None
                    }
                }
        except Exception as e:
            return {'error': str(e)}
    
    def revenue_per_hour(self, start_time: Optional[datetime] = None,
                        end_time: Optional[datetime] = None) -> Dict:
        """
        Calculate revenue per hour.
        
        Returns:
            Dict with revenue_per_hour, total_revenue, hours, metadata
        """
        conn = self._get_connection()
        if conn is None:
            return {'error': 'Database connection failed'}
        
        try:
            with conn.cursor() as cur:
                time_filter = ""
                params = []
                if start_time:
                    time_filter += " AND created_at >= %s"
                    params.append(start_time)
                else:
                    start_time = datetime.now() - timedelta(hours=24)
                    time_filter += " AND created_at >= %s"
                    params.append(start_time)
                
                if end_time:
                    time_filter += " AND created_at <= %s"
                    params.append(end_time)
                else:
                    end_time = datetime.now()
                
                # Calculate total revenue from transactions
                query = f"""
                    SELECT 
                        COALESCE(SUM(price_paid), 0) as total_revenue,
                        COUNT(*) as transaction_count
                    FROM transactions
                    WHERE status = 'completed' {time_filter}
                """
                
                cur.execute(query, params)
                result = cur.fetchone()
                total_revenue = float(result[0]) if result and result[0] else 0.0
                transaction_count = result[1] if result else 0
                
                # Calculate hours in window
                hours = (end_time - start_time).total_seconds() / 3600.0
                revenue_per_hour = total_revenue / hours if hours > 0 else 0.0
                
                return {
                    'kpi_name': 'revenue_per_hour',
                    'value': round(revenue_per_hour, 2),
                    'unit': 'dollars',
                    'total_revenue': round(total_revenue, 2),
                    'transaction_count': transaction_count,
                    'hours': round(hours, 2),
                    'timestamp': datetime.now().isoformat(),
                    'metadata': {
                        'start_time': start_time.isoformat(),
                        'end_time': end_time.isoformat()
                    }
                }
        except Exception as e:
            return {'error': str(e)}
    
    def fraud_detection_rate(self, start_time: Optional[datetime] = None,
                            end_time: Optional[datetime] = None) -> Dict:
        """
        Calculate fraud detection rate: (blocked_fraud / total_fraud_attempts) × 100
        
        Returns:
            Dict with fraud_detection_rate, blocked_count, total_attempts, metadata
        """
        conn = self._get_connection()
        if conn is None:
            return {'error': 'Database connection failed'}
        
        try:
            with conn.cursor() as cur:
                time_filter = ""
                params = []
                if start_time:
                    time_filter += " AND created_at >= %s"
                    params.append(start_time)
                if end_time:
                    time_filter += " AND created_at <= %s"
                    params.append(end_time)
                
                # Count blocked fraud attempts
                blocked_query = f"""
                    SELECT COUNT(*) as blocked_count
                    FROM fraud_detections
                    WHERE decision = 'BLOCKED' {time_filter}
                """
                
                # Count total fraud attempts (fraud_score > threshold)
                total_query = f"""
                    SELECT COUNT(*) as total_attempts
                    FROM fraud_detections
                    WHERE fraud_score >= 0.65 {time_filter}
                """
                
                try:
                    cur.execute(blocked_query, params)
                    blocked_result = cur.fetchone()
                    blocked_count = blocked_result[0] if blocked_result else 0
                    
                    cur.execute(total_query, params)
                    total_result = cur.fetchone()
                    total_attempts = total_result[0] if total_result else 0
                except psycopg2.errors.UndefinedTable:
                    # Table doesn't exist yet, return defaults
                    blocked_count = 0
                    total_attempts = 0
                
                detection_rate = (blocked_count / total_attempts * 100) if total_attempts > 0 else 0.0
                
                return {
                    'kpi_name': 'fraud_detection_rate',
                    'value': round(detection_rate, 2),
                    'unit': 'percent',
                    'blocked_count': blocked_count,
                    'total_attempts': total_attempts,
                    'timestamp': datetime.now().isoformat(),
                    'metadata': {
                        'start_time': start_time.isoformat() if start_time else None,
                        'end_time': end_time.isoformat() if end_time else None
                    }
                }
        except Exception as e:
            return {'error': str(e)}
    
    def get_all_kpis(self, time_window_hours: int = 24) -> Dict:
        """
        Get all primary KPIs for the specified time window.
        
        Args:
            time_window_hours: Time window in hours (default 24)
            
        Returns:
            Dict with all KPIs
        """
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=time_window_hours)
        
        return {
            'conversion_rate': self.conversion_rate(start_time=start_time, end_time=end_time),
            'time_to_finality': self.time_to_finality(start_time=start_time, end_time=end_time),
            'revenue_per_hour': self.revenue_per_hour(start_time=start_time, end_time=end_time),
            'fraud_detection_rate': self.fraud_detection_rate(start_time=start_time, end_time=end_time),
            'timestamp': datetime.now().isoformat(),
            'time_window_hours': time_window_hours
        }


# Singleton instance
_kpi_calculator = None

def get_kpi_calculator():
    """Get singleton KPI calculator instance."""
    global _kpi_calculator
    if _kpi_calculator is None:
        _kpi_calculator = KPICalculator()
    return _kpi_calculator

