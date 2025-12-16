"""
ML Integration Layer - Main Integration Point
Connects ML models to the application backend.
"""

from typing import Dict, Optional
from datetime import datetime
import sys
from pathlib import Path

# Import models
sys.path.insert(0, str(Path(__file__).parent.parent))
from models.fraud_detection_model import get_fraud_model
from models.user_clustering import get_clustering_model
from models.anomaly_detector import get_anomaly_detector
from models.recommendation_engine import get_recommendation_engine
from models.pricing_bandit import get_pricing_bandit

# Import supporting components
from features.feature_engineering import get_feature_engineer
from logging.model_logging import get_model_logger


class MLIntegrationLayer:
    """
    Main integration layer connecting ML models to application backend.
    
    This class demonstrates how ML model outputs change application behavior.
    """
    
    def __init__(self):
        """Initialize ML integration layer with all models."""
        self.fraud_model = get_fraud_model()
        self.clustering_model = get_clustering_model()
        self.anomaly_detector = get_anomaly_detector()
        self.recommendation_engine = get_recommendation_engine()
        self.pricing_bandit = get_pricing_bandit(epsilon=0.15)
        self.feature_engineer = get_feature_engineer()
        self.model_logger = get_model_logger()
    
    def process_transaction(self, transaction_id: str, wallet_address: str,
                          event_id: Optional[int] = None, price_paid: float = 0.0) -> Dict:
        """
        End-to-end transaction processing with ML models.
        
        This is the main integration point showing how ML affects application behavior.
        
        Args:
            transaction_id: Unique transaction ID
            wallet_address: Wallet address
            event_id: Event ID (optional)
            price_paid: Price paid (optional)
            
        Returns:
            Dict with model outputs and decisions
        """
        result = {
            'transaction_id': transaction_id,
            'timestamp': datetime.now().isoformat(),
            'status': 'processing'
        }
        
        try:
            # Step 1: Feature Engineering
            features = self.feature_engineer.compute_features(
                transaction_id=transaction_id,
                wallet_address=wallet_address,
                event_id=event_id
            )
            result['features'] = features
            
            # Step 2: Fraud Detection
            fraud_result = self.fraud_model.predict(features)
            result['fraud_detection'] = fraud_result
            
            # Decision: BLOCK transaction if fraud detected
            if fraud_result['decision'] == 'BLOCKED':
                result['status'] = 'blocked'
                result['reason'] = 'fraud_detected'
                
                # Log inference
                self.model_logger.log_inference(
                    model_name='fraud_detection',
                    model_version=fraud_result['model_version'],
                    input_features=features,
                    output_score=fraud_result['fraud_probability'],
                    decision='BLOCKED',
                    request_id=transaction_id,
                    metadata={'event_id': event_id, 'price_paid': price_paid}
                )
                
                return result
            
            # Step 3: Anomaly Detection
            anomaly_result = self.anomaly_detector.detect(features)
            result['anomaly_detection'] = anomaly_result
            
            # Decision: Flag for review if anomalous
            if anomaly_result['anomaly_score'] < 0.3:
                result['anomaly_flag'] = True
                result['status'] = 'flagged_for_review'
            
            # Step 4: User Clustering
            cluster_result = self.clustering_model.predict_cluster(features)
            result['user_cluster'] = cluster_result
            
            # Decision: Adjust fraud threshold for scalpers
            if cluster_result['cluster_label'] == 'scalper':
                # Stricter fraud threshold for scalpers
                if fraud_result['fraud_probability'] > 0.5:  # Lower threshold
                    result['status'] = 'blocked'
                    result['reason'] = 'scalper_high_risk'
                    return result
            
            # Step 5: Pricing Bandit (if transaction approved)
            if result['status'] == 'processing':
                pricing_result = self.pricing_bandit.select_arm({
                    'event_id': event_id,
                    'user_cluster': cluster_result['cluster_label']
                })
                result['pricing_decision'] = pricing_result
            
            # Log all inferences
            self.model_logger.log_inference(
                model_name='fraud_detection',
                model_version=fraud_result['model_version'],
                input_features=features,
                output_score=fraud_result['fraud_probability'],
                decision=fraud_result['decision'],
                request_id=transaction_id,
                ab_path=pricing_result.get('selected_arm') if result.get('pricing_decision') else None,
                metadata={
                    'event_id': event_id,
                    'price_paid': price_paid,
                    'user_cluster': cluster_result['cluster_label'],
                    'anomaly_score': anomaly_result['anomaly_score']
                }
            )
            
            result['status'] = 'approved'
            
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
        
        return result
    
    def recommend_events(self, user_id: str, user_features: Dict, events: list) -> list:
        """
        Recommend events for a user.
        
        This shows how recommendation engine changes application behavior.
        
        Args:
            user_id: User identifier
            user_features: User feature dict
            events: List of event dicts
            
        Returns:
            List of events sorted by recommendation score
        """
        # Get user cluster
        cluster_result = self.clustering_model.predict_cluster(user_features)
        user_features['cluster_id'] = cluster_result['cluster_id']
        user_features['wallet_address'] = user_id
        
        # Get recommendations
        recommended_events = self.recommendation_engine.recommend_events(
            user_features=user_features,
            events=events,
            top_k=10
        )
        
        return recommended_events
    
    def get_pricing(self, base_price: float, event_id: int, user_features: Dict,
                   event_features: Dict) -> Dict:
        """
        Get dynamic pricing for an event.
        
        This shows how pricing bandit changes application behavior.
        
        Args:
            base_price: Base ticket price
            event_id: Event ID
            user_features: User features
            event_features: Event features
            
        Returns:
            Dict with final_price, pricing_strategy, selected_arm
        """
        # Get user cluster
        cluster_result = self.clustering_model.predict_cluster(user_features)
        
        # Select pricing arm
        pricing_decision = self.pricing_bandit.select_arm({
            'event_id': event_id,
            'user_cluster': cluster_result['cluster_label'],
            'event_features': event_features
        })
        
        # Calculate final price
        final_price = self.pricing_bandit.calculate_price(
            base_price=base_price,
            arm_name=pricing_decision['selected_arm'],
            event_features=event_features
        )
        
        return {
            'final_price': round(final_price, 2),
            'base_price': base_price,
            'price_change_pct': round((final_price - base_price) / base_price * 100, 2),
            'selected_arm': pricing_decision['selected_arm'],
            'pricing_strategy': pricing_decision,
            'user_cluster': cluster_result['cluster_label']
        }


# Singleton instance
_ml_integration = None

def get_ml_integration_layer() -> MLIntegrationLayer:
    """Get singleton ML integration layer instance."""
    global _ml_integration
    if _ml_integration is None:
        _ml_integration = MLIntegrationLayer()
    return _ml_integration


if __name__ == "__main__":
    # Example usage
    integration = get_ml_integration_layer()
    
    # Process a transaction
    result = integration.process_transaction(
        transaction_id="test_123",
        wallet_address="0x123...",
        event_id=42,
        price_paid=50.0
    )
    print(f"Transaction result: {result['status']}")
    print(f"Fraud decision: {result.get('fraud_detection', {}).get('decision')}")
    print(f"User cluster: {result.get('user_cluster', {}).get('cluster_label')}")

