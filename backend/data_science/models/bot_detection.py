import time
import logging
from typing import Dict, Any
from ..core import data_logger, ModelManager
from ..feature_store import feature_store
import numpy as np

try:
    from sklearn.ensemble import IsolationForest
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

logger = logging.getLogger(__name__)


class BotDetectionModel(ModelManager):
    def __init__(self):
        super().__init__("bot_detection", "data_science/config/model_configs/bot_detection.json")
        self.data_loader = None  # Will be set externally
        
        if self.model is None and SKLEARN_AVAILABLE:
            self.train(None)

    def train(self, data: Any = None):
        """Train bot detection model with real or dummy data."""
        if not SKLEARN_AVAILABLE:
            logger.warning("scikit-learn not available, skipping training")
            return
        
        # Try to fetch real data from database
        if data is None and self.data_loader:
            logger.info("Fetching real user behavior data from database...")
            try:
                transactions = self.data_loader.fetch_transaction_history(limit=500)
                
                if transactions and len(transactions) > 10:
                    X_list = []
                    
                    for tx in transactions:
                        user_id = tx.get("user_id")
                        if not user_id:
                            continue
                        
                        user_stats = self.data_loader.get_user_transaction_stats(user_id)
                        features = feature_store.extract_bot_features(tx, user_stats)
                        
                        # Create feature vector: [velocity, variance, avg_amount]
                        X_list.append([
                            features["transaction_velocity"],
                            features["amount_variance"],
                            features["avg_amount"]
                        ])
                    
                    if len(X_list) > 10:
                        X = np.array(X_list)
                        logger.info(f"Training on {len(X)} real user behavior patterns")
                        data = X
                else:
                    logger.warning("Insufficient data from database, using dummy data")
            except Exception as e:
                logger.error(f"Error fetching training data: {e}")
                logger.warning("Falling back to dummy data")
        
        # Use provided data or dummy data
        if data is None:
            logger.info("Using dummy training data")
            X_normal = np.array([[1, 0.9, 0.9], [2, 0.95, 0.95], [1, 0.8, 0.9]])
            X_anomalies = np.array([[50, 0.1, 0.1], [100, 0.0, 0.0]])
            X = np.vstack([X_normal, X_anomalies])
        else:
            X = data
        
        contamination = self.config.get("contamination", 0.1)
        self.model = IsolationForest(contamination=contamination, random_state=42)
        self.model.fit(X)
        self.save()
        
        # Save metrics if data_loader available
        if self.data_loader:
            try:
                metrics = {
                    "n_samples": len(X),
                    "contamination": contamination
                }
                self.data_loader.save_model_metrics(
                    model_name="bot_detection",
                    metrics=metrics,
                    metadata={"training_date": time.strftime("%Y-%m-%d")}
                )
                logger.info(f"Saved training metrics: {metrics}")
            except Exception as e:
                logger.error(f"Error saving metrics: {e}")

    def predict(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        start_time = time.time()
        req_freq = inputs.get("request_freq", 0)
        ua_score = inputs.get("ua_score", 1.0)
        ip_rep = inputs.get("ip_reputation", 1.0)
        
        is_bot = False
        anomaly_score = 0.0
        
        if SKLEARN_AVAILABLE and self.model:
            pred = self.model.predict([[req_freq, ua_score, ip_rep]])[0]
            anomaly_score = float(self.model.decision_function([[req_freq, ua_score, ip_rep]])[0])
            is_bot = True if pred == -1 else False
        else:
            if req_freq > 20 or ua_score < 0.5:
                is_bot = True
                anomaly_score = -1.0
            else:
                anomaly_score = 1.0

        result = {
            "is_bot": is_bot,
            "anomaly_score": anomaly_score,
            "model_version": self.config.get("version", "1.0")
        }

        latency = (time.time() - start_time) * 1000
        data_logger.log("bot_detection_model", inputs, result, latency)
        
        # Save prediction to database if data_loader available
        if self.data_loader:
            try:
                self.data_loader.save_prediction(
                    model_name="bot_detection",
                    input_data=inputs,
                    output=result,
                    latency_ms=latency,
                    metadata={"timestamp": time.strftime("%Y-%m-%d %H:%M:%S")}
                )
            except Exception as e:
                logger.error(f"Error saving prediction: {e}")
        
        return result

bot_model = BotDetectionModel()
