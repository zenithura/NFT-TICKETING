import time
import logging
from typing import Dict, Any
from ..core import data_logger

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

class SegmentationModel:
    def __init__(self):
        self.data_loader = None  # Will be set externally
        self.model = None
        if SKLEARN_AVAILABLE:
            # Dummy training data: [AvgTxValue, Frequency]
            X = np.array([
                [10, 1], [15, 2], [12, 1], # Low value, low freq
                [100, 5], [120, 6], [110, 5], # High value, high freq
                [50, 10], [45, 12], [55, 11] # Medium value, very high freq
            ])
            self.model = KMeans(n_clusters=3, random_state=42, n_init=10)
            self.model.fit(X)

    def train(self, data: Any = None):
        """Dummy train method for pipeline compatibility."""
        if self.model:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            artifact_dir = os.path.join(base_dir, "artifacts")
            os.makedirs(artifact_dir, exist_ok=True)
            joblib.dump(self.model, os.path.join(artifact_dir, "segmentation.joblib"))

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
            segment = int(self.model.predict([[avg_tx_value, frequency]])[0])
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
