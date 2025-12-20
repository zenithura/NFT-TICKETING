import time
import logging
import numpy as np
from typing import Dict, Any
from ..core import data_logger, ModelManager

logger = logging.getLogger(__name__)

import joblib
import os

class DecisionRuleModel(ModelManager):
    def __init__(self, window_size: int = 20, num_std_dev: float = 2.0):
        super().__init__("decision_rule", "config/model_configs/decision_rule.json")
        self.data_loader = None  # Will be set externally
        self.window_size = window_size
        self.num_std_dev = num_std_dev
        self.history = []
        
        # Try to load history from model attribute (which is set by ModelManager.load)
        if self.model and isinstance(self.model, list):
            self.history = self.model

    def train(self, data: Any = None):
        """
        Loads historical values for the sliding window.
        """
        if self.data_loader:
            logger.info("Fetching historical transaction amounts for decision rule...")
            try:
                transactions = self.data_loader.fetch_transaction_history(limit=self.window_size)
                if transactions:
                    self.history = [float(tx.get("amount", 0)) for tx in transactions]
                    logger.info(f"Loaded {len(self.history)} historical values")
            except Exception as e:
                logger.error(f"Error fetching data for decision rule: {e}")
        
        self.model = self.history
        self.save()

    def predict(self, inputs: Dict[str, Any]) -> str:
        """
        Detects anomalies using Bollinger Bands logic.
        Inputs expected: 'value' (e.g., transaction amount or latency)
        """
        start_time = time.time()
        value = inputs.get("value", 0)
        
        decision = "NORMAL"
        
        if len(self.history) >= self.window_size:
            # Calculate bands
            recent_data = np.array(self.history[-self.window_size:])
            mean = np.mean(recent_data)
            std = np.std(recent_data)
            
            upper_band = mean + (self.num_std_dev * std)
            lower_band = mean - (self.num_std_dev * std)
            
            if value > upper_band or value < lower_band:
                decision = "ANOMALY"
        
        # Update history
        self.history.append(value)
        # Keep history manageable
        if len(self.history) > self.window_size * 2:
            self.history = self.history[-self.window_size:]

        latency = (time.time() - start_time) * 1000
        data_logger.log("decision_rule_model", inputs, decision, latency)
        
        # Save prediction to database if data_loader available
        if self.data_loader:
            try:
                self.data_loader.save_prediction(
                    model_name="decision_rule",
                    input_data=inputs,
                    output={"decision": decision},
                    latency_ms=latency,
                    metadata={"timestamp": time.strftime("%Y-%m-%d %H:%M:%S")}
                )
            except Exception as e:
                logger.error(f"Error saving prediction: {e}")
        
        return decision

decision_rule_model = DecisionRuleModel()
