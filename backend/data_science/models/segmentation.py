import time
import logging
from typing import Dict, Any
from ..core import data_logger, ModelManager

logger = logging.getLogger(__name__)

# Try to import sklearn
try:
    from sklearn.cluster import KMeans
    import numpy as np
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

import joblib
import os

class SegmentationModel(ModelManager):
    def __init__(self):
        super().__init__("segmentation", "config/model_configs/segmentation.json")
        self.data_loader = None  # Will be set externally
        
        # If no model loaded, train a dummy one
        if self.model is None and SKLEARN_AVAILABLE:
            self.train(None)

    def train(self, data: Any = None):
        """
        Trains the segmentation model using user transaction statistics.
        """
        if not SKLEARN_AVAILABLE:
            logger.warning("scikit-learn not available, skipping training")
            return

        if data is None and self.data_loader:
            logger.info("Fetching user behavior for segmentation training...")
            try:
                users = self.data_loader.fetch_user_behavior(limit=500)
                X_list = []
                for user in users:
                    stats = self.data_loader.get_user_transaction_stats(user.get("id"))
                    X_list.append([stats.get("avg_amount", 0), stats.get("count", 0)])
                
                if len(X_list) > 10:
                    X = np.array(X_list)
                    logger.info(f"Training on {len(X)} users from database")
                    data = X
                else:
                    logger.warning("Insufficient user data, using dummy data")
            except Exception as e:
                logger.error(f"Error fetching user data for segmentation: {e}")

        if data is None:
            logger.info("Using dummy training data for segmentation")
            # Dummy training data: [AvgTxValue, Frequency]
            data = np.array([
                [10, 1], [15, 2], [12, 1], # Low value, low freq
                [100, 5], [120, 6], [110, 5], # High value, high freq
                [50, 10], [45, 12], [55, 11] # Medium value, very high freq
            ])

        n_clusters = self.config.get("n_clusters", 3)
        self.model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        self.model.fit(data)
        self.save()

    def predict(self, inputs: Dict[str, Any]) -> int:
        """
        Segments user into a cluster.
        Inputs expected: 'avg_tx_value', 'frequency'
        """
        start_time = time.time()
        avg_tx_value = inputs.get("avg_tx_value", 0)
        frequency = inputs.get("frequency", 0)
        
        segment = -1
        
        if SKLEARN_AVAILABLE and self.model:
            try:
                segment = int(self.model.predict([[avg_tx_value, frequency]])[0])
            except Exception as e:
                logger.error(f"Error during segmentation prediction: {e}")
                segment = 0
        else:
            # Fallback
            if avg_tx_value > 100:
                segment = 1 # High value
            elif frequency > 10:
                segment = 2 # High freq
            else:
                segment = 0 # Low value/freq

        latency = (time.time() - start_time) * 1000
        data_logger.log("segmentation_model", inputs, segment, latency)
        
        # Save prediction to database if data_loader available
        if self.data_loader:
            try:
                self.data_loader.save_prediction(
                    model_name="segmentation",
                    input_data=inputs,
                    output={"segment": segment},
                    latency_ms=latency,
                    metadata={"timestamp": time.strftime("%Y-%m-%d %H:%M:%S")}
                )
            except Exception as e:
                logger.error(f"Error saving prediction: {e}")
        
        return segment

segmentation_model = SegmentationModel()
