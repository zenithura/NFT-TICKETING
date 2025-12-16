import time
import logging
from typing import Dict, Any, List
from ..core import data_logger, ModelManager
import json
import os

logger = logging.getLogger(__name__)

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False

class WashTradingModel(ModelManager):
    def __init__(self):
        super().__init__("wash_trading", "data_science/config/model_configs/wash_trading.json")
        self.data_loader = None  # Will be set externally
        # In a real scenario, we would load the graph from a database or build it incrementally
        self.graph = nx.DiGraph() if NETWORKX_AVAILABLE else None

    def train(self, data: Any = None):
        # Graph based models don't necessarily "train" in the traditional sense, 
        # but we might pre-compute communities or load historical edges here.
        self.model = self.graph
        self.save()

    def predict(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Detects wash trading cycles.
        Inputs: 'buyer_id', 'seller_id', 'nft_id', 'transaction_id'
        """
        start_time = time.time()
        buyer = inputs.get("buyer_id")
        seller = inputs.get("seller_id")
        nft_id = inputs.get("nft_id")
        
        is_wash_trade = False
        cycle_path = []
        
        if NETWORKX_AVAILABLE and self.graph is not None:
            # Add the potential edge
            self.graph.add_edge(buyer, seller, nft=nft_id)
            
            # Check for cycles involving these nodes
            try:
                # Simple cycle detection
                cycles = list(nx.simple_cycles(self.graph))
                for cycle in cycles:
                    if buyer in cycle and seller in cycle:
                        is_wash_trade = True
                        cycle_path = cycle
                        break
            except Exception:
                pass
            
            # Cleanup for demo purposes (don't let graph grow infinitely in memory)
            if self.graph.number_of_edges() > 1000:
                self.graph.clear()
        else:
            # Fallback: simple check if buyer == seller (self-trade)
            if buyer == seller:
                is_wash_trade = True
                cycle_path = [buyer, seller]

        result = {
            "is_wash_trade": is_wash_trade,
            "cycle_path": cycle_path,
            "model_version": self.config.get("version", "1.0")
        }

        latency = (time.time() - start_time) * 1000
        data_logger.log("wash_trading_model", inputs, result, latency)
        
        # Save prediction to database if data_loader available
        if self.data_loader:
            try:
                self.data_loader.save_prediction(
                    model_name="wash_trading",
                    input_data=inputs,
                    output=result,
                    latency_ms=latency,
                    metadata={"timestamp": time.strftime("%Y-%m-%d %H:%M:%S")}
                )
            except Exception as e:
                logger.error(f"Error saving prediction: {e}")
        
        return result

wash_trading_model = WashTradingModel()
