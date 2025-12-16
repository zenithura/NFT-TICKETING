import time
import logging
from typing import Dict, Any
from ..core import data_logger

logger = logging.getLogger(__name__)

# Try to import sklearn
try:
    from sklearn.linear_model import LinearRegression
    import numpy as np
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

import joblib
import os

class MarketTrendModel:
    def __init__(self):
        self.data_loader = None  # Will be set externally
        self.model = None
        if SKLEARN_AVAILABLE:
            # Dummy training data: [DayIndex] -> [Sales]
            X = np.array([[1], [2], [3], [4], [5]])
            y = np.array([100, 110, 120, 135, 150])
            self.model = LinearRegression()
            self.model.fit(X, y)

    def train(self, data: Any = None):
        """Dummy train method for pipeline compatibility."""
        if self.model:
            os.makedirs("data_science/artifacts", exist_ok=True)
            joblib.dump(self.model, "data_science/artifacts/market_trend.joblib")

    def predict(self, inputs: Dict[str, Any]) -> float:
        """
        Predicts future trend value.
        Inputs expected: 'day_index'
        """
        start_time = time.time()
        day_index = inputs.get("day_index", 0)
        
        prediction = 0.0
        
        if SKLEARN_AVAILABLE and self.model:
            prediction = float(self.model.predict([[day_index]])[0])
        else:
            # Fallback: simple linear growth assumption
            prediction = 100 + (day_index * 10)

        latency = (time.time() - start_time) * 1000
        data_logger.log("market_trend_model", inputs, prediction, latency)
        
        # Save prediction to database if data_loader available
        if self.data_loader:
            try:
                self.data_loader.save_prediction(
                    model_name="market_trend",
                    input_data=inputs,
                    output={"prediction": prediction},
                    latency_ms=latency,
                    metadata={"timestamp": time.strftime("%Y-%m-%d %H:%M:%S")}
                )
            except Exception as e:
                logger.error(f"Error saving prediction: {e}")
        
        return prediction

market_trend_model = MarketTrendModel()
