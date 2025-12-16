"""
ML Integration Layer for Backend - Production Implementation
Connects ML models to backend services with Supabase → DuckDB flow.

Data Flow:
  Supabase PostgreSQL → Feature Engineering → ML Models → DuckDB Analytics
"""

from typing import Dict, Optional
from datetime import datetime
import sys
from pathlib import Path

# Import backend database utilities
backend_path = Path(__file__).parent.parent.parent / "backend"
if backend_path.exists():
    sys.path.insert(0, str(backend_path))
    try:
        from database import get_supabase_admin
        _has_backend_db = True
    except ImportError:
        _has_backend_db = False
        print("Warning: Backend database utilities not available")
else:
    _has_backend_db = False

# Import ML components
sys.path.insert(0, str(Path(__file__).parent.parent))
from integration.supabase_feature_engineer import get_supabase_feature_engineer
from models.fraud_detection_model import get_fraud_model
from models.user_clustering import get_clustering_model
from models.anomaly_detector import get_anomaly_detector
from models.recommendation_engine import get_recommendation_engine
from models.pricing_bandit import get_pricing_bandit
from models.risk_scoring_heuristic import get_risk_scoring_heuristic
from integration.duckdb_storage import get_duckdb_storage


class MLIntegrationBackend:
    """
    ML Integration Layer for Backend Services.
    
    Features:
    - Queries Supabase PostgreSQL for all input data
    - Runs ML models on real features
    - Stores results in DuckDB (not Supabase)
    - Returns outputs to backend for business logic
    """
    
    def __init__(self, db_client=None):
        """
        Initialize ML integration layer.
        
        Args:
            db_client: Supabase client instance (if None, uses get_supabase_admin())
        """
        # Initialize feature engineer with Supabase client
        self.feature_engineer = get_supabase_feature_engineer(db_client=db_client)
        
        # Initialize ML models
        self.fraud_model = get_fraud_model()
        self.clustering_model = get_clustering_model()
        self.anomaly_detector = get_anomaly_detector()
        self.recommendation_engine = get_recommendation_engine()
        self.pricing_bandit = get_pricing_bandit(epsilon=0.15)
        self.risk_scoring_heuristic = get_risk_scoring_heuristic()  # Rule-based risk scoring
        
        # Initialize DuckDB storage
        self.duckdb_storage = get_duckdb_storage()
    
    def process_transaction(self, transaction_id: str, wallet_address: str,
                          event_id: Optional[int] = None, price_paid: float = 0.0) -> Dict:
        """
        End-to-end transaction processing with ML models.
        
        Data Flow:
        1. Query Supabase for features
        2. Run ML models
        3. Store results in DuckDB
        4. Return outputs to backend
        
        Args:
            transaction_id: Unique transaction identifier
            wallet_address: Wallet address
            event_id: Event ID (optional)
            price_paid: Price paid (optional)
            
        Returns:
            Dict with model outputs and decisions
        """
        result = {
            'transaction_id': transaction_id,
            'timestamp': datetime.now().isoformat(),
            'status': 'processing',
            'data_source': 'supabase'
        }
        
        try:
            # Step 1: Feature Engineering from Supabase
            features = self.feature_engineer.compute_features(
                transaction_id=transaction_id,
                wallet_address=wallet_address,
                event_id=event_id
            )
            result['features'] = features
            
            # Store feature snapshot in DuckDB
            self.duckdb_storage.store_feature_snapshot(
                request_id=transaction_id,
                features=features,
                transaction_id=transaction_id,
                wallet_address=wallet_address,
                event_id=event_id
            )
            
            # Step 2: Fraud Detection
            fraud_result = self.fraud_model.predict(features)
            result['fraud_detection'] = fraud_result
            
            # Decision: BLOCK transaction if fraud detected
            if fraud_result['decision'] == 'BLOCKED':
                result['status'] = 'blocked'
                result['reason'] = 'fraud_detected'
                
                # Store inference in DuckDB
                self.duckdb_storage.store_inference_result(
                    request_id=transaction_id,
                    model_name='fraud_detection',
                    model_version=fraud_result['model_version'],
                    input_features=features,
                    output_scores={'fraud_probability': fraud_result['fraud_probability']},
                    decision='BLOCKED',
                    confidence=fraud_result['confidence'],
                    transaction_id=transaction_id,
                    wallet_address=wallet_address,
                    event_id=event_id,
                    metadata={'price_paid': price_paid}
                )
                
                return result
            
            # Step 3: Anomaly Detection
            anomaly_result = self.anomaly_detector.detect(features)
            result['anomaly_detection'] = anomaly_result
            
            # Step 4: User Clustering
            cluster_result = self.clustering_model.predict_cluster(features)
            result['user_cluster'] = cluster_result
            
            # Step 5: Risk Scoring Heuristic (rule-based, complementary to fraud detection)
            risk_heuristic_result = self.risk_scoring_heuristic.score(features)
            result['risk_scoring_heuristic'] = risk_heuristic_result
            
            # Step 6: Pricing Bandit (if transaction approved)
            pricing_result = self.pricing_bandit.select_arm({
                'event_id': event_id,
                'user_cluster': cluster_result['cluster_label']
            })
            result['pricing_decision'] = pricing_result
            
            # Store all inference results in DuckDB
            self.duckdb_storage.store_inference_result(
                request_id=transaction_id,
                model_name='fraud_detection',
                model_version=fraud_result['model_version'],
                input_features=features,
                output_scores={
                    'fraud_probability': fraud_result['fraud_probability'],
                    'anomaly_score': anomaly_result['anomaly_score'],
                    'cluster_id': cluster_result['cluster_id'],
                    'risk_heuristic_score': risk_heuristic_result['risk_score'],
                    'risk_heuristic_band': risk_heuristic_result['risk_band']
                },
                decision=fraud_result['decision'],
                confidence=fraud_result['confidence'],
                transaction_id=transaction_id,
                wallet_address=wallet_address,
                event_id=event_id,
                metadata={
                    'price_paid': price_paid,
                    'user_cluster': cluster_result['cluster_label'],
                    'anomaly_score': anomaly_result['anomaly_score'],
                    'pricing_arm': pricing_result['selected_arm'],
                    'risk_heuristic_reasons': risk_heuristic_result['reasons'],
                    'risk_heuristic_band': risk_heuristic_result['risk_band']
                }
            )
            
            result['status'] = 'approved'
            
        except Exception as e:
            result['status'] = 'error'
            result['error'] = str(e)
            # Log error in DuckDB
            try:
                self.duckdb_storage.store_inference_result(
                    request_id=transaction_id,
                    model_name='error',
                    model_version='n/a',
                    input_features={},
                    output_scores={'error': str(e)},
                    decision='ERROR',
                    transaction_id=transaction_id,
                    wallet_address=wallet_address,
                    event_id=event_id,
                    metadata={'error_type': type(e).__name__}
                )
            except:
                pass  # Don't fail if DuckDB write fails
        
        return result
    
    def recommend_events(self, user_id: str, user_features: Dict, events: list) -> list:
        """
        Recommend events for a user using ML models.
        
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
        Get dynamic pricing for an event using ML bandit.
        
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
    
    def get_analytics(self, days: int = 7) -> Dict:
        """
        Get ML analytics from DuckDB.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Dict with analytics summary
        """
        return self.duckdb_storage.get_analytics_summary(days=days)


# Singleton instance
_ml_integration_backend = None

def get_ml_integration_backend(db_client=None) -> MLIntegrationBackend:
    """
    Get singleton ML integration backend instance.
    
    This is the main entry point for backend services to use ML.
    """
    global _ml_integration_backend
    if _ml_integration_backend is None:
        _ml_integration_backend = MLIntegrationBackend(db_client=db_client)
    return _ml_integration_backend


if __name__ == "__main__":
    # Example usage - would be called from backend
    from supabase import Client
    
    # Get Supabase client (would come from backend dependency injection)
    # db_client = get_supabase_admin()  # Would be injected
    
    # Initialize ML integration
    integration = get_ml_integration_backend()  # db_client would be passed
    
    # Process transaction
    result = integration.process_transaction(
        transaction_id="test_123",
        wallet_address="0x123...",
        event_id=42,
        price_paid=50.0
    )
    print(f"Transaction result: {result['status']}")
    print(f"Fraud decision: {result.get('fraud_detection', {}).get('decision')}")

