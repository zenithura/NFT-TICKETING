"""Model Logging Middleware - Log All Inference Calls."""
import json
import logging
from datetime import datetime
from typing import Dict, Optional, Any
from functools import wraps
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from data_control.db_connection import get_db_connection, return_db_connection, get_redis_client


class ModelLogger:
    """Log all model inference calls with full context."""
    
    def __init__(self):
        self.logger = logging.getLogger('model_inference')
        self.logger.setLevel(logging.INFO)
        handler = logging.FileHandler('sprint3/logs/model_inferences.log')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.redis_client = get_redis_client()
    
    def log_inference(self, model_name: str, model_version: str, 
                     input_features: Dict, output_score: float,
                     decision: str, request_id: str,
                     ab_path: Optional[str] = None,
                     metadata: Optional[Dict] = None):
        """
        Log a model inference call.
        
        Args:
            model_name: Name of the model (e.g., 'fraud_detection', 'recommender')
            model_version: Model version (e.g., 'v1.2.3')
            input_features: Input feature dictionary
            output_score: Model output score
            decision: Decision made (e.g., 'APPROVED', 'BLOCKED')
            request_id: Unique request identifier
            ab_path: A/B test path (e.g., 'control', 'treatment')
            metadata: Additional metadata
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'model_name': model_name,
            'model_version': model_version,
            'request_id': request_id,
            'input_features': input_features,
            'output_score': float(output_score),
            'decision': decision,
            'ab_path': ab_path,
            'metadata': metadata or {}
        }
        
        # Log to file
        self.logger.info(json.dumps(log_entry))
        
        # Store in database
        self._store_in_db(log_entry)
        
        # Cache recent logs in Redis (last 1000)
        if self.redis_client:
            try:
                redis_key = f"model_logs:{model_name}:{request_id}"
                self.redis_client.setex(redis_key, 3600, json.dumps(log_entry))  # 1 hour TTL
                
                # Add to recent logs list
                list_key = f"model_logs:recent:{model_name}"
                self.redis_client.lpush(list_key, json.dumps(log_entry))
                self.redis_client.ltrim(list_key, 0, 999)  # Keep last 1000
            except Exception as e:
                print(f"Error caching model log in Redis: {e}")
    
    def _store_in_db(self, log_entry: Dict):
        """Store log entry in database."""
        conn = get_db_connection()
        if not conn:
            return
        
        try:
            with conn.cursor() as cur:
                # Check if table exists, create if not
                create_table_query = """
                    CREATE TABLE IF NOT EXISTS model_inference_logs (
                        log_id BIGSERIAL PRIMARY KEY,
                        timestamp TIMESTAMPTZ NOT NULL,
                        model_name VARCHAR(100) NOT NULL,
                        model_version VARCHAR(50) NOT NULL,
                        request_id VARCHAR(255) NOT NULL,
                        input_features JSONB,
                        output_score FLOAT,
                        decision VARCHAR(50),
                        ab_path VARCHAR(50),
                        metadata JSONB,
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    );
                    
                    CREATE INDEX IF NOT EXISTS idx_model_logs_timestamp ON model_inference_logs(timestamp);
                    CREATE INDEX IF NOT EXISTS idx_model_logs_model_name ON model_inference_logs(model_name);
                    CREATE INDEX IF NOT EXISTS idx_model_logs_request_id ON model_inference_logs(request_id);
                """
                cur.execute(create_table_query)
                conn.commit()
                
                # Insert log entry
                insert_query = """
                    INSERT INTO model_inference_logs 
                    (timestamp, model_name, model_version, request_id, input_features, 
                     output_score, decision, ab_path, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                cur.execute(insert_query, (
                    log_entry['timestamp'],
                    log_entry['model_name'],
                    log_entry['model_version'],
                    log_entry['request_id'],
                    json.dumps(log_entry['input_features']),
                    log_entry['output_score'],
                    log_entry['decision'],
                    log_entry.get('ab_path'),
                    json.dumps(log_entry.get('metadata', {}))
                ))
                conn.commit()
        except Exception as e:
            print(f"Error storing model log in database: {e}")
            if conn:
                conn.rollback()
        finally:
            return_db_connection(conn)
    
    def get_recent_logs(self, model_name: Optional[str] = None, limit: int = 100) -> list:
        """Get recent inference logs."""
        conn = get_db_connection()
        if not conn:
            return []
        
        try:
            with conn.cursor() as cur:
                if model_name:
                    query = """
                        SELECT * FROM model_inference_logs
                        WHERE model_name = %s
                        ORDER BY timestamp DESC
                        LIMIT %s
                    """
                    cur.execute(query, (model_name, limit))
                else:
                    query = """
                        SELECT * FROM model_inference_logs
                        ORDER BY timestamp DESC
                        LIMIT %s
                    """
                    cur.execute(query, (limit,))
                
                results = cur.fetchall()
                return [dict(row) for row in results]
        except Exception as e:
            print(f"Error fetching model logs: {e}")
            return []
        finally:
            return_db_connection(conn)


# Singleton instance
_model_logger = None

def get_model_logger() -> ModelLogger:
    """Get singleton model logger instance."""
    global _model_logger
    if _model_logger is None:
        _model_logger = ModelLogger()
    return _model_logger


def log_inference_decorator(model_name: str, model_version: str):
    """
    Decorator to automatically log model inference calls.
    
    Usage:
        @log_inference_decorator('fraud_detection', 'v1.2.3')
        def predict_fraud(features):
            # ... model logic ...
            return score, decision
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            logger = get_model_logger()
            
            # Extract features and request_id from args/kwargs
            features = kwargs.get('features') or (args[0] if args else {})
            request_id = kwargs.get('request_id') or kwargs.get('transaction_id') or f"req_{datetime.now().timestamp()}"
            
            # Call original function
            result = func(*args, **kwargs)
            
            # Parse result (assumes tuple of (score, decision) or dict)
            if isinstance(result, tuple):
                output_score, decision = result
                ab_path = None
                metadata = {}
            elif isinstance(result, dict):
                output_score = result.get('score') or result.get('fraud_score') or 0.0
                decision = result.get('decision') or result.get('action') or 'UNKNOWN'
                ab_path = result.get('ab_path') or result.get('mab_arm')
                metadata = result.get('metadata', {})
            else:
                output_score = float(result) if result else 0.0
                decision = 'UNKNOWN'
                ab_path = None
                metadata = {}
            
            # Log inference
            logger.log_inference(
                model_name=model_name,
                model_version=model_version,
                input_features=features if isinstance(features, dict) else {},
                output_score=output_score,
                decision=decision,
                request_id=request_id,
                ab_path=ab_path,
                metadata=metadata
            )
            
            return result
        return wrapper
    return decorator

