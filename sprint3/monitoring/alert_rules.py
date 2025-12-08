"""Alert Rules and Trigger Logic."""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from data_control.db_connection import get_db_connection, return_db_connection
import json
from monitoring.monitoring_api import get_monitoring

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AlertRule:
    """Single alert rule definition."""
    
    def __init__(self, name: str, condition: str, threshold: float, severity: str):
        """
        Initialize alert rule.
        
        Args:
            name: Alert name
            condition: Condition to check (e.g., 'event_lag > threshold')
            threshold: Threshold value
            severity: 'LOW', 'MEDIUM', 'HIGH', 'CRITICAL'
        """
        self.name = name
        self.condition = condition
        self.threshold = threshold
        self.severity = severity
        self.last_triggered = None
    
    def evaluate(self, current_value: float) -> bool:
        """Evaluate if alert should trigger."""
        if self.condition == '>':
            return current_value > self.threshold
        elif self.condition == '<':
            return current_value < self.threshold
        elif self.condition == '>=':
            return current_value >= self.threshold
        elif self.condition == '<=':
            return current_value <= self.threshold
        elif self.condition == '==':
            return current_value == self.threshold
        else:
            return False


class AlertSystem:
    """Alert system for monitoring KPIs."""
    
    def __init__(self):
        self.rules = []
        self.monitoring = get_monitoring()
        self._initialize_rules()
    
    def _initialize_rules(self):
        """Initialize default alert rules."""
        # Event lag alert
        self.rules.append(AlertRule(
            name='event_processing_lag_high',
            condition='>',
            threshold=60.0,  # 60 seconds
            severity='HIGH'
        ))
        
        # Error rate alert
        self.rules.append(AlertRule(
            name='api_error_rate_high',
            condition='>',
            threshold=0.02,  # 2%
            severity='HIGH'
        ))
        
        # Suspicious transaction count alert
        self.rules.append(AlertRule(
            name='suspicious_transaction_spike',
            condition='>',
            threshold=10.0,  # 10 suspicious transactions
            severity='MEDIUM'
        ))
    
    def check_alerts(self) -> List[Dict]:
        """
        Check all alert rules and return triggered alerts.
        
        Returns:
            List of alert dictionaries
        """
        triggered_alerts = []
        
        # Get current system metrics
        system_kpis = self.monitoring.get_all_system_kpis()
        
        # Check event lag
        event_lag = system_kpis.get('event_processing_lag', {})
        if 'avg_lag_seconds' in event_lag:
            lag_rule = next((r for r in self.rules if r.name == 'event_processing_lag_high'), None)
            if lag_rule and lag_rule.evaluate(event_lag['avg_lag_seconds']):
                alert = self._create_alert(
                    rule=lag_rule,
                    current_value=event_lag['avg_lag_seconds'],
                    metric='event_processing_lag',
                    metadata=event_lag
                )
                triggered_alerts.append(alert)
                lag_rule.last_triggered = datetime.now()
        
        # Check error rate
        error_rate = system_kpis.get('api_error_rate', {})
        if 'error_rate' in error_rate:
            error_rule = next((r for r in self.rules if r.name == 'api_error_rate_high'), None)
            if error_rule and error_rule.evaluate(error_rate['error_rate']):
                alert = self._create_alert(
                    rule=error_rule,
                    current_value=error_rate['error_rate'],
                    metric='api_error_rate',
                    metadata=error_rate
                )
                triggered_alerts.append(alert)
                error_rule.last_triggered = datetime.now()
        
        # Check suspicious transactions
        suspicious = system_kpis.get('suspicious_transaction_count', {})
        if 'suspicious_count' in suspicious:
            suspicious_rule = next((r for r in self.rules if r.name == 'suspicious_transaction_spike'), None)
            if suspicious_rule and suspicious_rule.evaluate(float(suspicious['suspicious_count'])):
                alert = self._create_alert(
                    rule=suspicious_rule,
                    current_value=float(suspicious['suspicious_count']),
                    metric='suspicious_transaction_count',
                    metadata=suspicious
                )
                triggered_alerts.append(alert)
                suspicious_rule.last_triggered = datetime.now()
        
        # Log and store triggered alerts
        for alert in triggered_alerts:
            self._log_alert(alert)
            self._store_alert(alert)
        
        return triggered_alerts
    
    def _create_alert(self, rule: AlertRule, current_value: float,
                     metric: str, metadata: Dict) -> Dict:
        """Create alert dictionary."""
        return {
            'alert_id': f"{rule.name}_{datetime.now().timestamp()}",
            'name': rule.name,
            'severity': rule.severity,
            'metric': metric,
            'current_value': current_value,
            'threshold': rule.threshold,
            'condition': rule.condition,
            'message': f"{metric} is {current_value}, which {rule.condition} {rule.threshold}",
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata
        }
    
    def _log_alert(self, alert: Dict):
        """Log alert to file."""
        logger.warning(f"ALERT TRIGGERED: {alert['name']} - {alert['message']}")
    
    def _store_alert(self, alert: Dict):
        """Store alert in database."""
        conn = get_db_connection()
        if not conn:
            return
        
        try:
            with conn.cursor() as cur:
                # Create alerts table if not exists
                create_table_query = """
                    CREATE TABLE IF NOT EXISTS alerts (
                        alert_id VARCHAR(255) PRIMARY KEY,
                        name VARCHAR(255) NOT NULL,
                        severity VARCHAR(50) NOT NULL,
                        metric VARCHAR(100),
                        current_value FLOAT,
                        threshold FLOAT,
                        condition VARCHAR(10),
                        message TEXT,
                        metadata JSONB,
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    );
                    
                    CREATE INDEX IF NOT EXISTS idx_alerts_timestamp ON alerts(created_at);
                    CREATE INDEX IF NOT EXISTS idx_alerts_severity ON alerts(severity);
                """
                cur.execute(create_table_query)
                conn.commit()
                
                # Insert alert
                insert_query = """
                    INSERT INTO alerts 
                    (alert_id, name, severity, metric, current_value, threshold, condition, message, metadata)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (alert_id) DO NOTHING
                """
                cur.execute(insert_query, (
                    alert['alert_id'],
                    alert['name'],
                    alert['severity'],
                    alert['metric'],
                    alert['current_value'],
                    alert['threshold'],
                    alert['condition'],
                    alert['message'],
                    json.dumps(alert.get('metadata', {}))
                ))
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error storing alert: {e}")
            if conn:
                conn.rollback()
        finally:
            return_db_connection(conn)
    
    def get_recent_alerts(self, hours: int = 24, severity: Optional[str] = None) -> List[Dict]:
        """Get recent alerts from database."""
        conn = get_db_connection()
        if not conn:
            return []
        
        try:
            with conn.cursor() as cur:
                cutoff_time = datetime.now() - timedelta(hours=hours)
                
                if severity:
                    query = """
                        SELECT * FROM alerts
                        WHERE created_at >= %s AND severity = %s
                        ORDER BY created_at DESC
                    """
                    cur.execute(query, (cutoff_time, severity))
                else:
                    query = """
                        SELECT * FROM alerts
                        WHERE created_at >= %s
                        ORDER BY created_at DESC
                    """
                    cur.execute(query, (cutoff_time,))
                
                results = cur.fetchall()
                columns = [desc[0] for desc in cur.description]
                return [dict(zip(columns, row)) for row in results]
        except Exception as e:
            logger.error(f"Error fetching alerts: {e}")
            return []
        finally:
            return_db_connection(conn)


# Singleton instance
_alert_system = None

def get_alert_system() -> AlertSystem:
    """Get singleton alert system instance."""
    global _alert_system
    if _alert_system is None:
        _alert_system = AlertSystem()
    return _alert_system

