import time
import logging
from typing import Dict, Any
from ..core import data_logger, ModelManager

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

class MarketTrendModel(ModelManager):
    def __init__(self):
        super().__init__("market_trend", "config/model_configs/market_trend.json")
        self.data_loader = None  # Will be set externally
        
        # If no model loaded, train a dummy one
        if self.model is None and SKLEARN_AVAILABLE:
            self.train(None)

    def train(self, data: Any = None):
        """
        Trains the market trend model using historical transaction data.
        """
        if not SKLEARN_AVAILABLE:
            logger.warning("scikit-learn not available, skipping training")
            return

        if data is None and self.data_loader:
            logger.info("Fetching transaction history for market trend training...")
            try:
                transactions = self.data_loader.fetch_transaction_history(limit=1000)
                if transactions:
                    # Aggregate sales by day
                    from datetime import datetime
                    sales_by_day = {}
                    for tx in transactions:
                        date_str = tx.get("created_at", "").split("T")[0]
                        if date_str:
                            sales_by_day[date_str] = sales_by_day.get(date_str, 0) + float(tx.get("amount", 0))
                    
                    # Convert to X, y
                    sorted_days = sorted(sales_by_day.keys())
                    X_list = [[i] for i in range(len(sorted_days))]
                    y_list = [sales_by_day[d] for d in sorted_days]
                    
                    if len(X_list) > 5:
                        X = np.array(X_list)
                        y = np.array(y_list)
                        logger.info(f"Training on {len(X)} days of sales data")
                        data = (X, y)
                else:
                    logger.warning("No transaction history found, using dummy data")
            except Exception as e:
                logger.error(f"Error fetching data for market trend: {e}")

        if data is None:
            logger.info("Using dummy training data for market trend")
            # Dummy training data: [DayIndex] -> [Sales]
            X = np.array([[1], [2], [3], [4], [5]])
            y = np.array([100, 110, 120, 135, 150])
            data = (X, y)

        X, y = data
        self.model = LinearRegression()
        self.model.fit(X, y)
        self.save()

    def predict(self, inputs: Dict[str, Any]) -> float:
        """
        Predicts future trend value.
        Inputs expected: 'day_index'
        """
        start_time = time.time()
        day_index = inputs.get("day_index", 0)
        
        prediction = 0.0
        
        if SKLEARN_AVAILABLE and self.model:
            try:
                prediction = float(self.model.predict([[day_index]])[0])
            except Exception as e:
                logger.error(f"Error during market trend prediction: {e}")
                prediction = 0.0
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
