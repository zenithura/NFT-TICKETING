"""Integration Layer - Connect All Components End-to-End."""
import logging
from typing import Dict, Optional
from datetime import datetime

# Import all modules
from ml_pipeline.kpi_calculator import get_kpi_calculator
from ml_pipeline.feature_engineering import get_feature_engineer
from ml_pipeline.models_ensemble import ModelEnsemble
from ml_pipeline.mab_pricing import get_mab
from ml_pipeline.model_logging import get_model_logger
from data_control.etl_pipeline import get_etl_pipeline
from data_control.data_retention import get_retention_policy
from monitoring.monitoring_api import get_monitoring
from monitoring.alert_rules import get_alert_system
from security.siem_integration import get_siem, get_soar
from security.rate_limiter import get_rate_limiter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IntegrationLayer:
    """Integration layer connecting all Sprint 3 components."""
    
    def __init__(self):
        # Initialize all components
        self.kpi_calculator = get_kpi_calculator()
        self.feature_engineer = get_feature_engineer()
        self.model_ensemble = ModelEnsemble()
        self.mab = get_mab(epsilon=0.15)
        self.model_logger = get_model_logger()
        self.etl_pipeline = get_etl_pipeline()
        self.retention_policy = get_retention_policy()
        self.monitoring = get_monitoring()
        self.alert_system = get_alert_system()
        self.siem = get_siem()
        self.soar = get_soar()
        self.rate_limiter = get_rate_limiter()
    
    def process_transaction(self, transaction_id: str, wallet_address: str,
                          event_id: Optional[int] = None, price_paid: float = 0.0) -> Dict:
        """
        End-to-end transaction processing pipeline.
        
        Flow:
        1. Extract features
        2. Run ML models
        3. MAB routing
        4. Log inference
        5. Update KPIs
        6. Check alerts
        
        Returns:
            Dict with processing result
        """
        logger.info(f"Processing transaction: {transaction_id}")
        
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
            
            # Step 2: Run ML Models
            event_features = {'event_id': event_id} if event_id else {}
            model_outputs = self.model_ensemble.predict_all(
                features=features,
                event_features=event_features
            )
            result['model_outputs'] = model_outputs
            
            # Step 3: MAB Routing (for pricing)
            mab_result = self.mab.route_request(
                request_id=transaction_id,
                event_id=event_id,
                user_features=features
            )
            result['mab_decision'] = mab_result
            
            # Step 4: Model Logging
            fraud_score = model_outputs.get('risk_scoring', {}).get('risk_score', 0.5)
            decision = 'APPROVED' if fraud_score < 0.65 else 'REVIEW'
            
            self.model_logger.log_inference(
                model_name='fraud_detection',
                model_version='v1.2.3',
                input_features=features,
                output_score=fraud_score,
                decision=decision,
                request_id=transaction_id,
                ab_path=mab_result.get('selected_arm'),
                metadata={'event_id': event_id, 'price_paid': price_paid}
            )
            
            # Step 5: Check Alerts
            alerts = self.alert_system.check_alerts()
            if alerts:
                result['alerts_triggered'] = [a['name'] for a in alerts]
            
            result['status'] = 'completed'
            result['decision'] = decision
            
        except Exception as e:
            logger.error(f"Error processing transaction: {e}")
            result['status'] = 'error'
            result['error'] = str(e)
        
        return result
    
    def run_daily_etl(self):
        """Run daily ETL pipeline."""
        logger.info("Running daily ETL pipeline...")
        self.etl_pipeline.run_full_pipeline()
        logger.info("ETL pipeline completed")
    
    def enforce_retention(self):
        """Enforce data retention policies."""
        logger.info("Enforcing data retention policies...")
        self.retention_policy.enforce_retention_policy()
        logger.info("Retention policies enforced")
    
    def run_siem_correlation(self):
        """Run SIEM correlation and SOAR automation."""
        logger.info("Running SIEM correlation...")
        findings = self.siem.correlate_events()
        
        if findings:
            logger.info(f"Found {len(findings)} correlation findings")
            responses = self.soar.process_findings()
            logger.info(f"Executed {len(responses)} SOAR responses")
        
        return findings
    
    def get_all_metrics(self) -> Dict:
        """Get all KPIs and system metrics."""
        return {
            'primary_kpis': self.kpi_calculator.get_all_kpis(),
            'system_metrics': self.monitoring.get_all_system_kpis(),
            'alerts': self.alert_system.get_recent_alerts(hours=24),
            'timestamp': datetime.now().isoformat()
        }
    
    def health_check(self) -> Dict:
        """Health check for all components."""
        health = {
            'status': 'healthy',
            'components': {},
            'timestamp': datetime.now().isoformat()
        }
        
        # Check each component
        try:
            self.kpi_calculator._get_connection()
            health['components']['kpi_calculator'] = 'healthy'
        except:
            health['components']['kpi_calculator'] = 'unhealthy'
            health['status'] = 'degraded'
        
        try:
            self.feature_engineer._get_db()
            health['components']['feature_engineer'] = 'healthy'
        except:
            health['components']['feature_engineer'] = 'unhealthy'
            health['status'] = 'degraded'
        
        try:
            self.monitoring.event_processing_lag()
            health['components']['monitoring'] = 'healthy'
        except:
            health['components']['monitoring'] = 'unhealthy'
            health['status'] = 'degraded'
        
        return health


# Singleton instance
_integration_layer = None

def get_integration_layer() -> IntegrationLayer:
    """Get singleton integration layer instance."""
    global _integration_layer
    if _integration_layer is None:
        _integration_layer = IntegrationLayer()
    return _integration_layer

