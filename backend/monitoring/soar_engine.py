"""SOAR Engine - Security Orchestration, Automation, and Response."""
import logging
from datetime import datetime
from typing import Dict, List, Any
from data_control.db_connection import get_db_connection, return_db_connection

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SOAREngine:
    """Automated response engine for security alerts."""
    
    def __init__(self):
        self.actions_taken = []

    def process_alert(self, alert: Dict[str, Any]):
        """
        Process an alert and trigger automated playbooks.
        """
        alert_name = alert.get('name')
        severity = alert.get('severity')
        
        logger.info(f"SOAR processing alert: {alert_name} ({severity})")
        
        # Playbook: High Error Rate
        if alert_name == 'api_error_rate_high' and severity == 'HIGH':
            self._execute_playbook_throttle_api(alert)
            
        # Playbook: Suspicious Transaction Spike
        elif alert_name == 'suspicious_transaction_spike':
            self._execute_playbook_block_suspicious_ips(alert)
            
        # Playbook: Event Processing Lag
        elif alert_name == 'event_processing_lag_high' and severity == 'HIGH':
            self._execute_playbook_notify_devops(alert)

    def _execute_playbook_throttle_api(self, alert: Dict):
        """Playbook to increase rate limiting during high error rates."""
        logger.warning("SOAR: Executing Playbook - Throttle API")
        # In a real system, this would update Redis rate limit configs
        self._log_action("THROTTLE_API", "Increased rate limit strictness due to high error rate", alert)

    def _execute_playbook_block_suspicious_ips(self, alert: Dict):
        """Playbook to block IPs associated with suspicious transactions."""
        logger.warning("SOAR: Executing Playbook - Block Suspicious IPs")
        metadata = alert.get('metadata', {})
        suspicious_ips = metadata.get('suspicious_ips', [])
        
        for ip in suspicious_ips:
            self._block_ip(ip)
            self._log_action("BLOCK_IP", f"Blocked suspicious IP: {ip}", alert)

    def _execute_playbook_notify_devops(self, alert: Dict):
        """Playbook to escalate critical lag to DevOps."""
        logger.warning("SOAR: Executing Playbook - Notify DevOps")
        # In a real system, this would trigger PagerDuty or Slack
        self._log_action("NOTIFY_DEVOPS", "Escalated critical event lag to on-call engineer", alert)

    def _block_ip(self, ip: str):
        """Add IP to blacklist in database."""
        conn = get_db_connection()
        if not conn: return
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS ip_blacklist (
                        ip_address VARCHAR(50) PRIMARY KEY,
                        reason TEXT,
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    )
                """)
                cur.execute("INSERT INTO ip_blacklist (ip_address, reason) VALUES (%s, %s) ON CONFLICT DO NOTHING", 
                           (ip, "Automated SOAR block due to suspicious activity"))
                conn.commit()
        except Exception as e:
            logger.error(f"Error blocking IP: {e}")
        finally:
            return_db_connection(conn)

    def _log_action(self, action_type: str, description: str, alert: Dict):
        """Log SOAR action to database."""
        logger.info(f"SOAR Action: {action_type} - {description}")
        conn = get_db_connection()
        if not conn: return
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS soar_actions (
                        id SERIAL PRIMARY KEY,
                        action_type VARCHAR(100),
                        description TEXT,
                        alert_id VARCHAR(255),
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    )
                """)
                cur.execute("""
                    INSERT INTO soar_actions (action_type, description, alert_id)
                    VALUES (%s, %s, %s)
                """, (action_type, description, alert.get('alert_id')))
                conn.commit()
        except Exception as e:
            logger.error(f"Error logging SOAR action: {e}")
        finally:
            return_db_connection(conn)

# Singleton instance
_soar_engine = None

def get_soar_engine() -> SOAREngine:
    """Get singleton SOAR engine instance."""
    global _soar_engine
    if _soar_engine is None:
        _soar_engine = SOAREngine()
    return _soar_engine
