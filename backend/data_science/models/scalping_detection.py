import time
import logging
from typing import Dict, Any
from ..core import data_logger, ModelManager
from ..feature_store import feature_store
import numpy as np

logger = logging.getLogger(__name__)

try:
    from sklearn.linear_model import LogisticRegression
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

class ScalpingDetectionModel(ModelManager):
    def __init__(self):
        super().__init__("scalping_detection", "data_science/config/model_configs/scalping_detection.json")
        self.data_loader = None  # Will be set externally
        
        if self.model is None and SKLEARN_AVAILABLE:
            self.train(None)

    def train(self, data: Any = None):
        if not SKLEARN_AVAILABLE:
            logger.warning("scikit-learn not available, skipping training")
            return
        
        # Try to fetch real data from database
        if data is None and self.data_loader:
            logger.info("Fetching real ticket data from database...")
            try:
                tickets = self.data_loader.fetch_ticket_data(limit=500)
                if tickets and len(tickets) > 10:
                    features = feature_store.extract_scalping_features(tickets)
                    # Use extracted features for training
                    logger.info(f"Extracted scalping features from {len(tickets)} tickets")
            except Exception as e:
                logger.error(f"Error fetching training data: {e}")
        
        # Use provided data or dummy data
        if data is None:
            logger.info("Using dummy training data")
            X = np.array([[1, 100, 100], [2, 50, 48], [20, 1, 0.5], [50, 0.5, 0.1]])
            y = np.array([0, 0, 1, 1])
        else:
            X, y = data
        
        self.model = LogisticRegression(random_state=42)
        self.model.fit(X, y)
        self.save()
        
        # Save metrics if data_loader available
        if self.data_loader:
            try:
                train_score = self.model.score(X, y)
                self.data_loader.save_model_metrics(
                    model_name="scalping_detection",
                    metrics={"train_accuracy": train_score, "n_samples": len(X)},
                    metadata={"training_date": time.strftime("%Y-%m-%d")}
                )
                logger.info(f"Saved training metrics")
            except Exception as e:
                logger.error(f"Error saving metrics: {e}")

    def predict(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        start_time = time.time()
        purch_count = inputs.get("purchase_count", 0)
        resale_vel = inputs.get("resale_velocity", 0)
        hold_time = inputs.get("holding_time", 100)
        
        prob_scalper = 0.0
        
        if SKLEARN_AVAILABLE and self.model:
            prob_scalper = float(self.model.predict_proba([[purch_count, resale_vel, hold_time]])[0][1])
        else:
            if purch_count > 10 and hold_time < 1:
                prob_scalper = 0.9
            else:
                prob_scalper = 0.1

        threshold = self.config.get("threshold", 0.7)
        is_scalper = prob_scalper > threshold

        result = {
            "is_scalper": is_scalper,
            "scalper_probability": round(prob_scalper, 2),
            "model_version": self.config.get("version", "1.0")
        }

        latency = (time.time() - start_time) * 1000
        data_logger.log("scalping_detection_model", inputs, result, latency)
        
        # Save prediction to database if data_loader available
        if self.data_loader:
            try:
                self.data_loader.save_prediction(
                    model_name="scalping_detection",
                    input_data=inputs,
                    output=result,
                    latency_ms=latency,
                    metadata={"timestamp": time.strftime("%Y-%m-%d %H:%M:%S")}
                )
            except Exception as e:
                logger.error(f"Error saving prediction: {e}")
        
        return result

scalping_model = ScalpingDetectionModel()
