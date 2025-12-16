import time
import logging
from typing import Dict, Any, List
from ..core import data_logger

logger = logging.getLogger(__name__)

import joblib
import os

class RecommenderModel:
    def __init__(self):
        self.data_loader = None  # Will be set externally
        # Mock database of items
        self.items = [
            {"id": "ticket_1", "category": "concert", "price": 50},
            {"id": "ticket_2", "category": "sports", "price": 100},
            {"id": "ticket_3", "category": "concert", "price": 150},
            {"id": "ticket_4", "category": "theater", "price": 80},
            {"id": "ticket_5", "category": "sports", "price": 200},
        ]

    def train(self, data: Any = None):
        """Dummy train method for pipeline compatibility."""
        os.makedirs("data_science/artifacts", exist_ok=True)
        joblib.dump(self.items, "data_science/artifacts/recommender.joblib")

    def predict(self, inputs: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Recommends items based on user preference.
        Inputs expected: 'preferred_category'
        """
        start_time = time.time()
        preferred_category = inputs.get("preferred_category", "concert")
        
        # Simple content-based filtering
        recommendations = [
            item for item in self.items 
            if item["category"] == preferred_category
        ]
        
        # If no matches, return generic popular items (e.g., all items sorted by price)
        if not recommendations:
            recommendations = sorted(self.items, key=lambda x: x["price"])[:3]

        latency = (time.time() - start_time) * 1000
        data_logger.log("recommender_model", inputs, [r["id"] for r in recommendations], latency)
        
        # Save prediction to database if data_loader available
        if self.data_loader:
            try:
                self.data_loader.save_prediction(
                    model_name="recommender",
                    input_data=inputs,
                    output={"recommendations": [r["id"] for r in recommendations]},
                    latency_ms=latency,
                    metadata={"timestamp": time.strftime("%Y-%m-%d %H:%M:%S")}
                )
            except Exception as e:
                logger.error(f"Error saving prediction: {e}")
        
        return recommendations

recommender_model = RecommenderModel()
