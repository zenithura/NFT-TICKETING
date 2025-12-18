import time
import logging
from typing import Dict, Any, List
from ..core import data_logger, ModelManager

logger = logging.getLogger(__name__)

import joblib
import os

class RecommenderModel(ModelManager):
    def __init__(self):
        super().__init__("recommender", "config/model_configs/recommender.json")
        self.data_loader = None  # Will be set externally
        # Default items if DB fails
        self.items = [
            {"id": "ticket_1", "category": "concert", "price": 50},
            {"id": "ticket_2", "category": "sports", "price": 100},
            {"id": "ticket_3", "category": "concert", "price": 150},
            {"id": "ticket_4", "category": "theater", "price": 80},
            {"id": "ticket_5", "category": "sports", "price": 200},
        ]

    def train(self, data: Any = None):
        """
        Fetches items from database to build the recommendation index.
        """
        if self.data_loader:
            logger.info("Fetching events from database for recommender...")
            try:
                events = self.data_loader.fetch_event_data(limit=100)
                if events:
                    self.items = [
                        {"id": str(e.get("id")), "category": e.get("category", "general"), "price": float(e.get("price", 0))}
                        for e in events
                    ]
                    logger.info(f"Loaded {len(self.items)} items for recommendation")
            except Exception as e:
                logger.error(f"Error fetching events for recommender: {e}")
        
        self.model = self.items
        self.save()

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
            if str(item["category"]).lower() == str(preferred_category).lower()
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
