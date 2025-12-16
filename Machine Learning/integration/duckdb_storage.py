"""
DuckDB Storage for ML Results and Analytics
Stores ML inference outputs, feature snapshots, and model metrics.
NO writes to Supabase - DuckDB is the analytics/OLAP store.
"""

import duckdb
import json
from typing import Dict, Optional, List
from datetime import datetime, timedelta
from pathlib import Path


class DuckDBStorage:
    """
    DuckDB storage for ML outputs and analytics.
    
    Stores:
    - ML inference results
    - Feature snapshots
    - Model metrics
    - Decision metadata
    
    DuckDB is used as the analytics/OLAP layer (not Supabase).
    """
    
    def __init__(self, db_path: Optional[Path] = None):
        """
        Initialize DuckDB storage.
        
        Args:
            db_path: Path to DuckDB file (creates new if doesn't exist)
        """
        if db_path is None:
            db_path = Path(__file__).parent.parent / "artifacts" / "ml_analytics.duckdb"
        
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Initialize DuckDB connection
        self.conn = duckdb.connect(str(self.db_path))
        
        # Create tables if they don't exist
        self._initialize_schema()
    
    def _initialize_schema(self):
        """Initialize DuckDB schema for ML data."""
        # ML Inference Results table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS ml_inference_results (
                inference_id BIGINT PRIMARY KEY,
                timestamp TIMESTAMPTZ NOT NULL,
                request_id VARCHAR(255) NOT NULL,
                model_name VARCHAR(100) NOT NULL,
                model_version VARCHAR(50) NOT NULL,
                input_features JSON NOT NULL,
                output_scores JSON NOT NULL,
                decision VARCHAR(50),
                confidence FLOAT,
                transaction_id VARCHAR(255),
                wallet_address VARCHAR(255),
                event_id INTEGER,
                metadata JSON
            )
        """)
        
        # Feature Snapshots table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS ml_feature_snapshots (
                snapshot_id BIGINT PRIMARY KEY,
                timestamp TIMESTAMPTZ NOT NULL,
                request_id VARCHAR(255) NOT NULL,
                transaction_id VARCHAR(255),
                wallet_address VARCHAR(255),
                event_id INTEGER,
                features JSON NOT NULL,
                feature_hash VARCHAR(64)  -- Hash for deduplication
            )
        """)
        
        # Model Metrics table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS ml_model_metrics (
                metric_id BIGINT PRIMARY KEY,
                timestamp TIMESTAMPTZ NOT NULL,
                model_name VARCHAR(100) NOT NULL,
                model_version VARCHAR(50) NOT NULL,
                metric_name VARCHAR(100) NOT NULL,
                metric_value FLOAT NOT NULL,
                metadata JSON
            )
        """)
        
        # Create indexes for performance
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_inference_request_id ON ml_inference_results(request_id)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_inference_timestamp ON ml_inference_results(timestamp)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_inference_wallet ON ml_inference_results(wallet_address)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_inference_model ON ml_inference_results(model_name, model_version)")
        
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_snapshot_request_id ON ml_feature_snapshots(request_id)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_snapshot_timestamp ON ml_feature_snapshots(timestamp)")
        
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_metrics_model ON ml_model_metrics(model_name, model_version)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_metrics_timestamp ON ml_model_metrics(timestamp)")
        
        self.conn.commit()
    
    def store_inference_result(self, request_id: str, model_name: str, model_version: str,
                              input_features: Dict, output_scores: Dict,
                              decision: Optional[str] = None, confidence: Optional[float] = None,
                              transaction_id: Optional[str] = None, wallet_address: Optional[str] = None,
                              event_id: Optional[int] = None, metadata: Optional[Dict] = None) -> int:
        """
        Store ML inference result in DuckDB.
        
        Args:
            request_id: Unique request identifier
            model_name: Name of the model
            model_version: Model version
            input_features: Input feature dict
            output_scores: Model output scores dict
            decision: Final decision (e.g., "APPROVED", "BLOCKED")
            confidence: Confidence score
            transaction_id: Transaction ID
            wallet_address: Wallet address
            event_id: Event ID
            metadata: Additional metadata
            
        Returns:
            Inference ID (primary key)
        """
        timestamp = datetime.now().isoformat()
        
        # Get next inference_id
        result = self.conn.execute("SELECT COALESCE(MAX(inference_id), 0) + 1 FROM ml_inference_results").fetchone()
        inference_id = result[0] if result else 1
        
        # Insert inference result
        self.conn.execute("""
            INSERT INTO ml_inference_results (
                inference_id, timestamp, request_id, model_name, model_version,
                input_features, output_scores, decision, confidence,
                transaction_id, wallet_address, event_id, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            inference_id,
            timestamp,
            request_id,
            model_name,
            model_version,
            json.dumps(input_features),
            json.dumps(output_scores),
            decision,
            confidence,
            transaction_id,
            wallet_address,
            event_id,
            json.dumps(metadata) if metadata else None
        ))
        
        self.conn.commit()
        return inference_id
    
    def store_feature_snapshot(self, request_id: str, features: Dict,
                              transaction_id: Optional[str] = None,
                              wallet_address: Optional[str] = None,
                              event_id: Optional[int] = None,
                              feature_hash: Optional[str] = None) -> int:
        """
        Store feature snapshot in DuckDB.
        
        Args:
            request_id: Unique request identifier
            features: Feature dict
            transaction_id: Transaction ID
            wallet_address: Wallet address
            event_id: Event ID
            feature_hash: Optional hash for deduplication
            
        Returns:
            Snapshot ID (primary key)
        """
        timestamp = datetime.now().isoformat()
        
        # Get next snapshot_id
        result = self.conn.execute("SELECT COALESCE(MAX(snapshot_id), 0) + 1 FROM ml_feature_snapshots").fetchone()
        snapshot_id = result[0] if result else 1
        
        # Insert feature snapshot
        self.conn.execute("""
            INSERT INTO ml_feature_snapshots (
                snapshot_id, timestamp, request_id, transaction_id,
                wallet_address, event_id, features, feature_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            snapshot_id,
            timestamp,
            request_id,
            transaction_id,
            wallet_address,
            event_id,
            json.dumps(features),
            feature_hash
        ))
        
        self.conn.commit()
        return snapshot_id
    
    def store_model_metric(self, model_name: str, model_version: str,
                          metric_name: str, metric_value: float,
                          metadata: Optional[Dict] = None) -> int:
        """
        Store model metric in DuckDB.
        
        Args:
            model_name: Name of the model
            model_version: Model version
            metric_name: Name of the metric
            metric_value: Metric value
            metadata: Additional metadata
            
        Returns:
            Metric ID (primary key)
        """
        timestamp = datetime.now().isoformat()
        
        # Get next metric_id
        result = self.conn.execute("SELECT COALESCE(MAX(metric_id), 0) + 1 FROM ml_model_metrics").fetchone()
        metric_id = result[0] if result else 1
        
        # Insert model metric
        self.conn.execute("""
            INSERT INTO ml_model_metrics (
                metric_id, timestamp, model_name, model_version,
                metric_name, metric_value, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            metric_id,
            timestamp,
            model_name,
            model_version,
            metric_name,
            metric_value,
            json.dumps(metadata) if metadata else None
        ))
        
        self.conn.commit()
        return metric_id
    
    def get_inference_results(self, request_id: Optional[str] = None,
                             wallet_address: Optional[str] = None,
                             model_name: Optional[str] = None,
                             limit: int = 100) -> List[Dict]:
        """
        Query inference results from DuckDB.
        
        Args:
            request_id: Filter by request ID
            wallet_address: Filter by wallet address
            model_name: Filter by model name
            limit: Maximum number of results
            
        Returns:
            List of inference result dicts
        """
        query = "SELECT * FROM ml_inference_results WHERE 1=1"
        params = []
        
        if request_id:
            query += " AND request_id = ?"
            params.append(request_id)
        
        if wallet_address:
            query += " AND wallet_address = ?"
            params.append(wallet_address)
        
        if model_name:
            query += " AND model_name = ?"
            params.append(model_name)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)
        
        result = self.conn.execute(query, params).fetchall()
        
        # Convert to list of dicts
        columns = ['inference_id', 'timestamp', 'request_id', 'model_name', 'model_version',
                  'input_features', 'output_scores', 'decision', 'confidence',
                  'transaction_id', 'wallet_address', 'event_id', 'metadata']
        
        results = []
        for row in result:
            row_dict = dict(zip(columns, row))
            # Parse JSON fields
            row_dict['input_features'] = json.loads(row_dict['input_features']) if row_dict['input_features'] else {}
            row_dict['output_scores'] = json.loads(row_dict['output_scores']) if row_dict['output_scores'] else {}
            row_dict['metadata'] = json.loads(row_dict['metadata']) if row_dict['metadata'] else {}
            results.append(row_dict)
        
        return results
    
    def get_analytics_summary(self, days: int = 7) -> Dict:
        """
        Get analytics summary for the last N days.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dict with analytics summary
        """
        cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
        
        # Count total inferences
        total_inferences = self.conn.execute(
            "SELECT COUNT(*) FROM ml_inference_results WHERE timestamp >= ?",
            (cutoff_date,)
        ).fetchone()[0]
        
        # Count by decision
        decisions = self.conn.execute("""
            SELECT decision, COUNT(*) as count
            FROM ml_inference_results
            WHERE timestamp >= ?
            GROUP BY decision
        """, (cutoff_date,)).fetchall()
        
        # Average confidence
        avg_confidence = self.conn.execute("""
            SELECT AVG(confidence) FROM ml_inference_results
            WHERE timestamp >= ? AND confidence IS NOT NULL
        """, (cutoff_date,)).fetchone()[0]
        
        # Count by model
        by_model = self.conn.execute("""
            SELECT model_name, model_version, COUNT(*) as count
            FROM ml_inference_results
            WHERE timestamp >= ?
            GROUP BY model_name, model_version
        """, (cutoff_date,)).fetchall()
        
        return {
            'period_days': days,
            'total_inferences': total_inferences,
            'decisions': {d[0]: d[1] for d in decisions},
            'avg_confidence': float(avg_confidence) if avg_confidence else 0.0,
            'by_model': {f"{m[0]}_{m[1]}": m[2] for m in by_model}
        }
    
    def close(self):
        """Close DuckDB connection."""
        if self.conn:
            self.conn.close()


# Singleton instance
_duckdb_storage = None

def get_duckdb_storage(db_path: Optional[Path] = None) -> DuckDBStorage:
    """Get singleton DuckDB storage instance."""
    global _duckdb_storage
    if _duckdb_storage is None:
        _duckdb_storage = DuckDBStorage(db_path=db_path)
    return _duckdb_storage


if __name__ == "__main__":
    # Example usage
    storage = get_duckdb_storage()
    
    # Store inference result
    inference_id = storage.store_inference_result(
        request_id="test_123",
        model_name="fraud_detection",
        model_version="v1.2.3",
        input_features={"txn_velocity_1h": 2, "wallet_age_days": 30},
        output_scores={"fraud_probability": 0.23, "decision": "APPROVED"},
        decision="APPROVED",
        confidence=0.82,
        wallet_address="0x123..."
    )
    print(f"Stored inference: {inference_id}")
    
    # Query results
    results = storage.get_inference_results(limit=10)
    print(f"Retrieved {len(results)} inference results")
    
    # Get analytics
    summary = storage.get_analytics_summary(days=7)
    print(f"Analytics summary: {summary}")

