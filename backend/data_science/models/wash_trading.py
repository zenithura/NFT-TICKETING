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
        super().__init__("wash_trading", "config/model_configs/wash_trading.json")
        self.data_loader = None  # Will be set externally
        # In a real scenario, we would load the graph from a database or build it incrementally
        self.graph = nx.DiGraph() if NETWORKX_AVAILABLE else None

    def train(self, data: Any = None):
        """
        Builds the initial graph from historical transactions.
        """
        if not NETWORKX_AVAILABLE:
            logger.warning("networkx not available, skipping graph building")
            return

        if self.data_loader:
            logger.info("Building wash trading graph from historical transactions...")
            try:
                transactions = self.data_loader.fetch_transaction_history(limit=1000)
                for tx in transactions:
                    buyer = tx.get("user_id") # Simplified, assuming buyer is user_id
                    seller = tx.get("seller_id")
                    nft_id = tx.get("nft_id")
                    if buyer and seller:
                        self.graph.add_edge(buyer, seller, nft=nft_id)
                logger.info(f"Built graph with {self.graph.number_of_nodes()} nodes and {self.graph.number_of_edges()} edges")
            except Exception as e:
                logger.error(f"Error building wash trading graph: {e}")
        
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
