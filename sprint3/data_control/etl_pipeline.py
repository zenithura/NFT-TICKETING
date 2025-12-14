"""ETL Pipeline - Extract, Transform, Load with Derived Features."""
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path
import logging
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from data_control.db_connection import get_db_connection, return_db_connection
from ml_pipeline.feature_engineering import get_feature_engineer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ETLPipeline:
    """Extract, Transform, Load pipeline for data processing."""
    
    def __init__(self):
        self.feature_engineer = get_feature_engineer()
    
    def extract_transactions(self, since: Optional[datetime] = None,
                           until: Optional[datetime] = None) -> pd.DataFrame:
        """
        Extract transaction data from database.
        
        Args:
            since: Start time for extraction
            until: End time for extraction
            
        Returns:
            DataFrame with transaction data
        """
        conn = get_db_connection()
        if not conn:
            logger.error("Failed to get database connection")
            return pd.DataFrame()
        
        try:
            with conn.cursor() as cur:
                time_filter = ""
                params = []
                
                if since:
                    time_filter += " AND t.created_at >= %s"
                    params.append(since)
                else:
                    since = datetime.now() - timedelta(days=1)
                    time_filter += " AND t.created_at >= %s"
                    params.append(since)
                
                if until:
                    time_filter += " AND t.created_at <= %s"
                    params.append(until)
                
                query = f"""
                    SELECT 
                        o.order_id as transaction_id,
                        w.address as wallet_address,
                        o.event_id,
                        o.price as price_paid,
                        o.status,
                        o.created_at,
                        o.transaction_hash,
                        e.name as event_name,
                        e.total_supply as capacity,
                        e.event_date,
                        e.created_at as event_created_at
                    FROM orders o
                    JOIN wallets w ON w.wallet_id = o.buyer_wallet_id
                    LEFT JOIN events e ON e.event_id = o.event_id
                    WHERE 1=1 {time_filter}
                    ORDER BY o.created_at DESC
                """
                
                cur.execute(query, params)
                columns = [desc[0] for desc in cur.description]
                rows = cur.fetchall()
                
                df = pd.DataFrame(rows, columns=columns)
                logger.info(f"Extracted {len(df)} transactions")
                return df
                
        except Exception as e:
            logger.error(f"Error extracting transactions: {e}")
            return pd.DataFrame()
        finally:
            return_db_connection(conn)
    
    def transform_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Transform raw data into engineered features.
        
        Args:
            df: Raw transaction DataFrame
            
        Returns:
            DataFrame with engineered features
        """
        if df.empty:
            return df
        
        logger.info("Transforming features...")
        
        # Compute derived features using feature engineering module
        df_transformed = self.feature_engineer.compute_derived_features(df.copy())
        
        # Additional transformations
        # 1. avg_tx_per_day
        if 'wallet_address' in df_transformed.columns:
            wallet_stats = df_transformed.groupby('wallet_address').agg({
                'transaction_id': 'count',
                'created_at': ['min', 'max']
            }).reset_index()
            
            wallet_stats.columns = ['wallet_address', 'tx_count', 'first_tx', 'last_tx']
            wallet_stats['days_active'] = (wallet_stats['last_tx'] - wallet_stats['first_tx']).dt.days + 1
            wallet_stats['avg_tx_per_day'] = wallet_stats['tx_count'] / wallet_stats['days_active']
            
            df_transformed = df_transformed.merge(
                wallet_stats[['wallet_address', 'avg_tx_per_day']],
                on='wallet_address',
                how='left'
            )
            df_transformed['avg_tx_per_day'] = df_transformed['avg_tx_per_day'].fillna(0)
        
        # 2. tag_frequency (simplified - would need event_tags table)
        df_transformed['tag_frequency'] = 1.0
        
        # 3. event_lag (time between event creation and first ticket sale)
        if 'event_created_at' in df_transformed.columns and 'created_at' in df_transformed.columns:
            # Group by event and find first ticket sale
            event_first_sale = df_transformed.groupby('event_id')['created_at'].min().reset_index()
            event_first_sale.columns = ['event_id', 'first_ticket_sale']
            
            df_transformed = df_transformed.merge(event_first_sale, on='event_id', how='left')
            df_transformed['event_lag'] = (
                df_transformed['first_ticket_sale'] - df_transformed['event_created_at']
            ).dt.total_seconds() / 3600.0
            df_transformed['event_lag'] = df_transformed['event_lag'].fillna(0)
        
        # 4. user_activity_delta (week-over-week change)
        if 'wallet_address' in df_transformed.columns and 'created_at' in df_transformed.columns:
            df_transformed['week'] = df_transformed['created_at'].dt.isocalendar().week
            df_transformed['year'] = df_transformed['created_at'].dt.year
            
            weekly_activity = df_transformed.groupby(['wallet_address', 'year', 'week']).size().reset_index(name='weekly_tx_count')
            weekly_activity['prev_week_count'] = weekly_activity.groupby('wallet_address')['weekly_tx_count'].shift(1)
            weekly_activity['user_activity_delta'] = weekly_activity['weekly_tx_count'] - weekly_activity['prev_week_count'].fillna(0)
            
            df_transformed = df_transformed.merge(
                weekly_activity[['wallet_address', 'year', 'week', 'user_activity_delta']],
                on=['wallet_address', 'year', 'week'],
                how='left'
            )
            df_transformed['user_activity_delta'] = df_transformed['user_activity_delta'].fillna(0)
        
        logger.info(f"Transformed {len(df_transformed)} records with {len(df_transformed.columns)} features")
        return df_transformed
    
    def load_to_feature_store(self, df: pd.DataFrame, table_name: str = 'feature_store'):
        """
        Load transformed features into feature store (materialized view or table).
        
        Args:
            df: Transformed DataFrame
            table_name: Target table/view name
        """
        if df.empty:
            logger.warning("Empty DataFrame, skipping load")
            return
        
        conn = get_db_connection()
        if not conn:
            logger.error("Failed to get database connection")
            return
        
        try:
            with conn.cursor() as cur:
                # Create feature store table if not exists
                create_table_query = f"""
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        feature_id BIGSERIAL PRIMARY KEY,
                        transaction_id VARCHAR(255),
                        wallet_address VARCHAR(255),
                        event_id INTEGER,
                        avg_tx_per_day FLOAT,
                        tag_frequency FLOAT,
                        event_lag FLOAT,
                        user_activity_delta FLOAT,
                        created_at TIMESTAMPTZ DEFAULT NOW(),
                        updated_at TIMESTAMPTZ DEFAULT NOW()
                    );
                    
                    CREATE INDEX IF NOT EXISTS idx_feature_store_transaction ON {table_name}(transaction_id);
                    CREATE INDEX IF NOT EXISTS idx_feature_store_wallet ON {table_name}(wallet_address);
                    CREATE INDEX IF NOT EXISTS idx_feature_store_event ON {table_name}(event_id);
                """
                cur.execute(create_table_query)
                conn.commit()
                
                # Insert or update features
                for _, row in df.iterrows():
                    upsert_query = f"""
                        INSERT INTO {table_name} 
                        (transaction_id, wallet_address, event_id, avg_tx_per_day, 
                         tag_frequency, event_lag, user_activity_delta, updated_at)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, NOW())
                        ON CONFLICT (transaction_id) 
                        DO UPDATE SET
                            avg_tx_per_day = EXCLUDED.avg_tx_per_day,
                            tag_frequency = EXCLUDED.tag_frequency,
                            event_lag = EXCLUDED.event_lag,
                            user_activity_delta = EXCLUDED.user_activity_delta,
                            updated_at = NOW()
                    """
                    cur.execute(upsert_query, (
                        row.get('transaction_id'),
                        row.get('wallet_address'),
                        row.get('event_id'),
                        row.get('avg_tx_per_day', 0),
                        row.get('tag_frequency', 0),
                        row.get('event_lag', 0),
                        row.get('user_activity_delta', 0)
                    ))
                
                conn.commit()
                logger.info(f"Loaded {len(df)} features to {table_name}")
                
        except Exception as e:
            logger.error(f"Error loading features to store: {e}")
            if conn:
                conn.rollback()
        finally:
            return_db_connection(conn)
    
    def refresh_materialized_views(self):
        """Refresh all materialized views used by models."""
        conn = get_db_connection()
        if not conn:
            logger.error("Failed to get database connection")
            return
        
        try:
            with conn.cursor() as cur:
                # Refresh KPI materialized view
                kpi_view_query = """
                    CREATE MATERIALIZED VIEW IF NOT EXISTS kpi_hourly AS
                    SELECT 
                        DATE_TRUNC('hour', created_at) as hour,
                        COUNT(*) as transaction_count,
                        SUM(price_paid) as total_revenue,
                        AVG(price_paid) as avg_price,
                        COUNT(DISTINCT wallet_address) as unique_users
                    FROM transactions
                    WHERE status = 'completed'
                    GROUP BY DATE_TRUNC('hour', created_at);
                    
                    REFRESH MATERIALIZED VIEW CONCURRENTLY kpi_hourly;
                """
                
                # Refresh event analytics view
                event_view_query = """
                    CREATE MATERIALIZED VIEW IF NOT EXISTS event_analytics AS
                    SELECT 
                        e.event_id,
                        e.event_name,
                        COUNT(t.ticket_id) as tickets_sold,
                        e.capacity,
                        COUNT(t.ticket_id)::FLOAT / NULLIF(e.capacity, 0) as sell_through_rate,
                        AVG(t.price_paid) as avg_price_paid
                    FROM events e
                    LEFT JOIN tickets t ON t.event_id = e.event_id
                    GROUP BY e.event_id, e.event_name, e.capacity;
                    
                    REFRESH MATERIALIZED VIEW CONCURRENTLY event_analytics;
                """
                
                cur.execute(kpi_view_query.split(';')[0])
                conn.commit()
                cur.execute(kpi_view_query.split(';')[1])
                conn.commit()
                
                cur.execute(event_view_query.split(';')[0])
                conn.commit()
                cur.execute(event_view_query.split(';')[1])
                conn.commit()
                
                logger.info("Refreshed materialized views")
                
        except Exception as e:
            logger.error(f"Error refreshing materialized views: {e}")
            if conn:
                conn.rollback()
        finally:
            return_db_connection(conn)
    
    def run_full_pipeline(self, since: Optional[datetime] = None,
                         until: Optional[datetime] = None):
        """
        Run full ETL pipeline: Extract → Transform → Load.
        
        Args:
            since: Start time for extraction
            until: End time for extraction
        """
        logger.info("Starting ETL pipeline...")
        
        # Extract
        df = self.extract_transactions(since=since, until=until)
        if df.empty:
            logger.warning("No data extracted, ending pipeline")
            return
        
        # Transform
        df_transformed = self.transform_features(df)
        
        # Load
        self.load_to_feature_store(df_transformed)
        
        # Refresh materialized views
        self.refresh_materialized_views()
        
        logger.info("ETL pipeline completed successfully")


# Singleton instance
_etl_pipeline = None

def get_etl_pipeline() -> ETLPipeline:
    """Get singleton ETL pipeline instance."""
    global _etl_pipeline
    if _etl_pipeline is None:
        _etl_pipeline = ETLPipeline()
    return _etl_pipeline

