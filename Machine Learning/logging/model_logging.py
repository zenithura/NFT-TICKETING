"""
Model Logging - Inference Logging System
Logs all model predictions for audit trail and monitoring.
"""

import json
from typing import Dict, Optional
from datetime import datetime
from pathlib import Path


class ModelLogger:
    """
    Logs model inferences for audit trail, debugging, and monitoring.
    
    Log Format:
    {
        "timestamp": ISO 8601 timestamp,
        "model_name": str,
        "model_version": str,
        "request_id": str,
        "input_features": dict,
        "output_scores": dict,
        "decision": str,
        "ab_path": str,
        "metadata": dict
    }
    """
    
    def __init__(self, log_file: Optional[Path] = None):
        """
        Initialize model logger.
        
        Args:
            log_file: Path to log file (JSONL format - one JSON object per line)
        """
        self.log_file = log_file or Path(__file__).parent.parent / "logs" / "model_inferences.jsonl"
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
    
    def log_inference(self, model_name: str, model_version: str,
                     input_features: Dict, output_score: float,
                     decision: str, request_id: str,
                     ab_path: Optional[str] = None,
                     metadata: Optional[Dict] = None):
        """
        Log a model inference.
        
        Args:
            model_name: Name of the model (e.g., "fraud_detection")
            model_version: Model version (e.g., "v1.2.3")
            input_features: Input feature dictionary
            output_score: Model output score
            decision: Final decision (e.g., "APPROVED", "BLOCKED")
            request_id: Unique request identifier
            ab_path: A/B test path or MAB arm selected
            metadata: Additional metadata (event_id, price, etc.)
        """
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'model_name': model_name,
            'model_version': model_version,
            'request_id': request_id,
            'input_features': input_features,
            'output_scores': {
                'score': output_score,
                'decision': decision
            },
            'decision': decision,
            'ab_path': ab_path,
            'metadata': metadata or {}
        }
        
        # Append to log file (JSONL format)
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    
    def get_recent_logs(self, n: int = 100, model_name: Optional[str] = None) -> list:
        """
        Get recent log entries.
        
        Args:
            n: Number of entries to return
            model_name: Filter by model name (optional)
            
        Returns:
            List of log entries (most recent first)
        """
        if not self.log_file.exists():
            return []
        
        logs = []
        with open(self.log_file, 'r') as f:
            for line in f:
                try:
                    entry = json.loads(line.strip())
                    if model_name is None or entry.get('model_name') == model_name:
                        logs.append(entry)
                except json.JSONDecodeError:
                    continue
        
        # Return most recent N entries
        return logs[-n:][::-1]


# Singleton instance
_model_logger = None

def get_model_logger() -> ModelLogger:
    """Get singleton model logger instance."""
    global _model_logger
    if _model_logger is None:
        _model_logger = ModelLogger()
    return _model_logger

