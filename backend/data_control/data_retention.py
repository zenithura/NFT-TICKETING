"""Data Retention Policy - Configurable Retention and Archival."""
import os
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional
import logging
from data_control.db_connection import get_db_connection, return_db_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DataRetentionPolicy:
    """Enforce data retention policies and archival."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize retention policy.
        
        Args:
            config_path: Path to retention config file
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent / 'config' / 'config.yaml'
        
        # Load config
        self.config = {}
        if isinstance(config_path, str):
            config_path = Path(config_path)
        
        if config_path.exists():
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)
        
        # Get retention settings
        retention_config = self.config.get('retention', {})
        self.onchain_retention_days = retention_config.get('onchain_retention_days', 365)
        self.offchain_retention_days = retention_config.get('offchain_retention_days', 90)
        self.archival_enabled = retention_config.get('archival_enabled', True)
        self.auto_delete_enabled = retention_config.get('auto_delete_enabled', True)
        
        # Archive directory
        self.archive_dir = Path(__file__).parent.parent / 'archives'
        self.archive_dir.mkdir(exist_ok=True)
    
    def archive_old_data(self, table_name: str, retention_days: int,
                        where_clause: Optional[str] = None) -> int:
        """
        Archive old data from a table.
        
        Args:
            table_name: Table to archive from
            retention_days: Days to retain before archiving
            where_clause: Optional WHERE clause filter
            
        Returns:
            Number of rows archived
        """
        if not self.archival_enabled:
            logger.info(f"Archival disabled, skipping {table_name}")
            return 0
        
        conn = get_db_connection()
        if not conn:
            logger.error("Failed to get database connection")
            return 0
        
        try:
            with conn.cursor() as cur:
                cutoff_date = datetime.now() - timedelta(days=retention_days)
                
                # Build query
                where_condition = f"created_at < %s"
                if where_clause:
                    where_condition += f" AND {where_clause}"
                
                # Export to CSV
                archive_file = self.archive_dir / f"{table_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                
                export_query = f"""
                    COPY (
                        SELECT * FROM {table_name}
                        WHERE {where_condition}
                    ) TO STDOUT WITH CSV HEADER
                """
                
                # Note: COPY TO requires superuser or specific permissions
                # Alternative: Use Python to fetch and write
                select_query = f"""
                    SELECT * FROM {table_name}
                    WHERE {where_condition}
                """
                
                cur.execute(select_query, (cutoff_date,))
                columns = [desc[0] for desc in cur.description]
                rows = cur.fetchall()
                
                if rows:
                    import csv
                    with open(archive_file, 'w', newline='') as f:
                        writer = csv.writer(f)
                        writer.writerow(columns)
                        writer.writerows(rows)
                    
                    logger.info(f"Archived {len(rows)} rows from {table_name} to {archive_file}")
                    
                    if self.auto_delete_enabled:
                        # Delete archived data
                        delete_query = f"""
                            DELETE FROM {table_name}
                            WHERE {where_condition}
                        """
                        cur.execute(delete_query, (cutoff_date,))
                        conn.commit()
                        logger.info(f"Deleted {cur.rowcount} rows from {table_name}")
                    
                    return len(rows)
                else:
                    logger.info(f"No data to archive from {table_name}")
                    return 0
                    
        except Exception as e:
            logger.error(f"Error archiving {table_name}: {e}")
            if conn:
                conn.rollback()
            return 0
        finally:
            return_db_connection(conn)
    
    def enforce_retention_policy(self):
        """Enforce all retention policies."""
        logger.info("Enforcing data retention policies...")
        
        # Archive off-chain logs
        tables_to_archive = [
            ('model_inference_logs', self.offchain_retention_days),
            ('fraud_detections', self.offchain_retention_days),
            ('audit_logs', self.offchain_retention_days),
            ('security_alerts', self.offchain_retention_days)
        ]
        
        total_archived = 0
        for table_name, retention_days in tables_to_archive:
            try:
                archived_count = self.archive_old_data(table_name, retention_days)
                total_archived += archived_count
            except Exception as e:
                logger.warning(f"Failed to archive {table_name}: {e}")
        
        # On-chain data retention
        # Note: On-chain data is typically immutable, so we don't delete it
        # But we can archive off-chain references
        logger.info(f"Archived {total_archived} total rows")
        
        # Clean up old archive files (keep last 365 days)
        self._cleanup_old_archives(days=365)
    
    def _cleanup_old_archives(self, days: int = 365):
        """Delete archive files older than specified days."""
        cutoff_time = datetime.now() - timedelta(days=days)
        
        deleted_count = 0
        for archive_file in self.archive_dir.glob('*.csv'):
            if archive_file.stat().st_mtime < cutoff_time.timestamp():
                try:
                    archive_file.unlink()
                    deleted_count += 1
                except Exception as e:
                    logger.warning(f"Failed to delete {archive_file}: {e}")
        
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} old archive files")


# Singleton instance
_retention_policy = None

def get_retention_policy(config_path: Optional[str] = None) -> DataRetentionPolicy:
    """Get singleton retention policy instance."""
    global _retention_policy
    if _retention_policy is None:
        _retention_policy = DataRetentionPolicy(config_path=config_path)
    return _retention_policy

