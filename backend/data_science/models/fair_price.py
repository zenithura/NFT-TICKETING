import time
import logging
from typing import Dict, Any
from ..core import data_logger, ModelManager
import numpy as np

logger = logging.getLogger(__name__)

try:
    from sklearn.ensemble import GradientBoostingRegressor
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

class FairPriceModel(ModelManager):
    def __init__(self):
        super().__init__("fair_price", "config/model_configs/fair_price.json")
        self.data_loader = None  # Will be set externally
        
        if self.model is None and SKLEARN_AVAILABLE:
            self.train(None)

    def train(self, data: Any = None):
        if not SKLEARN_AVAILABLE:
            logger.warning("scikit-learn not available, skipping training")
            return
        
        # Use provided data or dummy data
        if data is None:
            logger.info("Using dummy training data")
            X = np.array([[100, 5, 10], [100, 8, 5], [100, 2, 20], [50, 5, 10], [200, 9, 2]])
            y = np.array([120, 150, 105, 60, 350])
        else:
            X, y = data
        
        self.model = GradientBoostingRegressor(random_state=42)
        self.model.fit(X, y)
        self.save()
        
        # Save metrics if data_loader available
        if self.data_loader:
            try:
                train_score = self.model.score(X, y)
                self.data_loader.save_model_metrics(
                    model_name="fair_price",
                    metrics={"train_r2_score": train_score, "n_samples": len(X)},
                    metadata={"training_date": time.strftime("%Y-%m-%d")}
                )
                logger.info(f"Saved training metrics")
            except Exception as e:
                logger.error(f"Error saving metrics: {e}")

    def predict(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        start_time = time.time()
        orig_price = inputs.get("original_price", 0)
        popularity = inputs.get("popularity", 5)
        days_left = inputs.get("days_left", 10)
        
        predicted_price = 0.0
        
        if SKLEARN_AVAILABLE and self.model:
            predicted_price = float(self.model.predict([[orig_price, popularity, days_left]])[0])
        else:
            markup = 1 + (popularity * 0.05) + (10 / (days_left + 1) * 0.02)
            predicted_price = orig_price * markup

        max_markup = self.config.get("max_markup_percent", 100) / 100.0
        max_allowed = orig_price * (1 + max_markup)
        final_price = min(predicted_price, max_allowed)

        result = {
            "fair_price": round(final_price, 2),
            "max_allowed": round(max_allowed, 2),
            "model_version": self.config.get("version", "1.0")
        }

        latency = (time.time() - start_time) * 1000
        data_logger.log("fair_price_model", inputs, result, latency)
        
        # Save prediction to database if data_loader available
        if self.data_loader:
            try:
                self.data_loader.save_prediction(
                    model_name="fair_price",
                    input_data=inputs,
                    output=result,
                    latency_ms=latency,
                    metadata={"timestamp": time.strftime("%Y-%m-%d %H:%M:%S")}
                )
            except Exception as e:
                logger.error(f"Error saving prediction: {e}")
        
        return result

fair_price_model = FairPriceModel()
