import json
import time
import random
import logging
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
import numpy as np
import joblib

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Try to import supabase
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False

class DataLogger:
    """
    Logs inputs and outputs for model tracing.
    """
    def __init__(self, log_file: str = "model_logs.jsonl"):
        self.log_file = log_file
        self.supabase: Optional[Client] = None
        
        if SUPABASE_AVAILABLE:
            url = os.environ.get("SUPABASE_URL")
            key = os.environ.get("SUPABASE_KEY")
            if url and key:
                try:
                    self.supabase = create_client(url, key)
                    logger.info("Connected to Supabase for logging.")
                except Exception as e:
                    logger.error(f"Failed to connect to Supabase: {e}")

    def log(self, model_name: str, inputs: Dict[str, Any], output: Any, latency_ms: float):
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "model_name": model_name,
            "inputs": inputs,
            "output": output,
            "latency_ms": latency_ms
        }
        
        # Log to console
        logger.info(f"Model: {model_name} | Latency: {latency_ms}ms | Output: {output}")
        
        # Log to file (append mode)
        try:
            with open(self.log_file, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            logger.error(f"Failed to write to log file: {e}")

        # Log to Supabase (Async ideally, but sync for now)
        if self.supabase:
            try:
                # Ensure table 'model_logs' exists in Supabase
                self.supabase.table("model_logs").insert(entry).execute()
            except Exception as e:
                # Don't crash app if logging fails
                logger.error(f"Failed to log to Supabase: {e}")

class KPICalculator:
    """
    Calculates core KPIs: Conversion Rate and Time-to-Finality.
    """
    def __init__(self):
        self.transactions = [] # List of {timestamp, status, finality_time}
        self.visits = 0

    def record_visit(self):
        self.visits += 1

    def record_transaction(self, status: str, time_to_finality_seconds: Optional[float] = None):
        self.transactions.append({
            "timestamp": datetime.utcnow(),
            "status": status,
            "time_to_finality": time_to_finality_seconds
        })

    def get_conversion_rate(self) -> float:
        if self.visits == 0:
            return 0.0
        completed_txs = sum(1 for tx in self.transactions if tx["status"] == "completed")
        return (completed_txs / self.visits) * 100

    def get_avg_time_to_finality(self) -> float:
        finality_times = [tx["time_to_finality"] for tx in self.transactions if tx["time_to_finality"] is not None]
        if not finality_times:
            return 0.0
        return np.mean(finality_times)

class ABTestManager:
    """
    Manages A/B testing and Multi-Armed Bandit routing.
    """
    def __init__(self, strategies: List[str] = ["baseline", "variant_a"]):
        self.strategies = strategies
        self.counts = {s: 0 for s in strategies}
        self.rewards = {s: 0.0 for s in strategies}
        self.epsilon = 0.1 # Exploration rate for Epsilon-Greedy

    def route_traffic(self, user_id: str) -> str:
        """
        Simple A/B routing based on user_id hash.
        """
        # Deterministic routing for A/B
        hash_val = hash(user_id)
        return self.strategies[hash_val % len(self.strategies)]

    def route_traffic_mab(self) -> str:
        """
        Multi-Armed Bandit routing (Epsilon-Greedy).
        """
        if random.random() < self.epsilon:
            # Explore
            return random.choice(self.strategies)
        else:
            # Exploit: choose strategy with highest average reward
            avg_rewards = {}
            for s in self.strategies:
                if self.counts[s] == 0:
                    avg_rewards[s] = 0
                else:
                    avg_rewards[s] = self.rewards[s] / self.counts[s]
            
            # Return strategy with max average reward
            return max(avg_rewards, key=avg_rewards.get)

    def update_reward(self, strategy: str, reward: float):
        if strategy in self.counts:
            self.counts[strategy] += 1
            self.rewards[strategy] += reward

class ModelManager:
    """
    Base class for models with persistence support.
    """
    def __init__(self, model_name: str, config_path: str):
        self.model_name = model_name
        self.config = self._load_config(config_path)
        self.model = None
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.artifact_path = os.path.join(base_dir, "artifacts", f"{model_name}.joblib")
        self.load() # Try to load on init

    def _load_config(self, path: str) -> Dict[str, Any]:
        try:
            # Path should be relative to backend/data_science/
            base_dir = os.path.dirname(os.path.abspath(__file__))
            full_path = os.path.join(base_dir, path)
            if os.path.exists(full_path):
                with open(full_path, "r") as f:
                    return json.load(f)
            else:
                 logger.warning(f"Config not found at {full_path}")
        except Exception as e:
            logger.warning(f"Could not load config from {path}: {e}")
        return {}

    def save(self):
        """Saves the model to disk."""
        if self.model:
            try:
                # Ensure directory exists
                os.makedirs(os.path.dirname(self.artifact_path), exist_ok=True)
                joblib.dump(self.model, self.artifact_path)
                logger.info(f"Saved model {self.model_name} to {self.artifact_path}")
            except Exception as e:
                logger.error(f"Failed to save model {self.model_name}: {e}")

    def load(self):
        """Loads the model from disk."""
        try:
            if os.path.exists(self.artifact_path):
                self.model = joblib.load(self.artifact_path)
                logger.info(f"Loaded model {self.model_name} from {self.artifact_path}")
            else:
                logger.warning(f"No artifact found for {self.model_name} at {self.artifact_path}. Model will need training.")
        except Exception as e:
            logger.error(f"Failed to load model {self.model_name}: {e}")

    def train(self, data: Any):
        """Abstract method to train the model."""
        raise NotImplementedError

# Global instances
data_logger = DataLogger()
kpi_calculator = KPICalculator()
ab_test_manager = ABTestManager()
