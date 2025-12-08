"""SIEM/SOAR Pipeline - Central Log Pipeline with Correlation and Automatic Response."""
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from data_control.db_connection import get_db_connection, return_db_connection
import subprocess
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SIEMCorrelation:
    """SIEM event correlation engine."""
    
    def __init__(self):
        self.correlation_rules = self._load_correlation_rules()
    
    def _load_correlation_rules(self) -> List[Dict]:
        """Load correlation rules."""
        return [
            {
                'name': 'rapid_failed_logins',
                'pattern': 'failed_login',
                'threshold': 5,
                'window_minutes': 10,
                'action': 'block_ip'
            },
            {
                'name': 'suspicious_activity_pattern',
                'pattern': 'fraud_score > 0.8',
                'threshold': 3,
                'window_minutes': 60,
                'action': 'flag_user'
            },
            {
                'name': 'api_attack_pattern',
                'pattern': 'rate_limit_exceeded',
                'threshold': 10,
                'window_minutes': 5,
                'action': 'rate_limit_aggressive'
            }
        ]
    
    def correlate_events(self, time_window_minutes: int = 60) -> List[Dict]:
        """
        Correlate events and identify suspicious patterns.
        
        Returns:
            List of correlation findings
        """
        conn = get_db_connection()
        if not conn:
            return []
        
        findings = []
        
        try:
            with conn.cursor() as cur:
                cutoff_time = datetime.now() - timedelta(minutes=time_window_minutes)
                
                # Rule 1: Rapid failed logins
                try:
                    query = """
                        SELECT ip_address, COUNT(*) as count
                        FROM audit_logs
                        WHERE created_at >= %s
                        AND message LIKE '%failed login%'
                        GROUP BY ip_address
                        HAVING COUNT(*) >= 5
                    """
                    cur.execute(query, (cutoff_time,))
                    results = cur.fetchall()
                    
                    for row in results:
                        findings.append({
                            'correlation_id': f"rapid_failed_logins_{row[0]}_{datetime.now().timestamp()}",
                            'rule_name': 'rapid_failed_logins',
                            'severity': 'HIGH',
                            'pattern': 'Multiple failed login attempts',
                            'entities': {'ip_address': row[0]},
                            'count': row[1],
                            'recommended_action': 'block_ip',
                            'timestamp': datetime.now().isoformat()
                        })
                except Exception as e:
                    logger.warning(f"Error checking rapid failed logins: {e}")
                
                # Rule 2: Suspicious activity pattern
                try:
                    query = """
                        SELECT wallet_address, COUNT(*) as count
                        FROM fraud_detections
                        WHERE created_at >= %s
                        AND fraud_score > 0.8
                        GROUP BY wallet_address
                        HAVING COUNT(*) >= 3
                    """
                    cur.execute(query, (cutoff_time,))
                    results = cur.fetchall()
                    
                    for row in results:
                        findings.append({
                            'correlation_id': f"suspicious_pattern_{row[0]}_{datetime.now().timestamp()}",
                            'rule_name': 'suspicious_activity_pattern',
                            'severity': 'MEDIUM',
                            'pattern': 'High fraud score transactions',
                            'entities': {'wallet_address': row[0]},
                            'count': row[1],
                            'recommended_action': 'flag_user',
                            'timestamp': datetime.now().isoformat()
                        })
                except Exception as e:
                    logger.warning(f"Error checking suspicious patterns: {e}")
                
                # Rule 3: API attack pattern
                try:
                    query = """
                        SELECT ip_address, COUNT(*) as count
                        FROM audit_logs
                        WHERE created_at >= %s
                        AND message LIKE '%rate limit%'
                        GROUP BY ip_address
                        HAVING COUNT(*) >= 10
                    """
                    cur.execute(query, (cutoff_time,))
                    results = cur.fetchall()
                    
                    for row in results:
                        findings.append({
                            'correlation_id': f"api_attack_{row[0]}_{datetime.now().timestamp()}",
                            'rule_name': 'api_attack_pattern',
                            'severity': 'HIGH',
                            'pattern': 'Rate limit violations',
                            'entities': {'ip_address': row[0]},
                            'count': row[1],
                            'recommended_action': 'rate_limit_aggressive',
                            'timestamp': datetime.now().isoformat()
                        })
                except Exception as e:
                    logger.warning(f"Error checking API attacks: {e}")
        
        except Exception as e:
            logger.error(f"Error in correlation: {e}")
        finally:
            return_db_connection(conn)
        
        # Store findings
        for finding in findings:
            self._store_finding(finding)
        
        return findings
    
    def _store_finding(self, finding: Dict):
        """Store correlation finding in database."""
        conn = get_db_connection()
        if not conn:
            return
        
        try:
            with conn.cursor() as cur:
                create_table_query = """
                    CREATE TABLE IF NOT EXISTS siem_findings (
                        finding_id VARCHAR(255) PRIMARY KEY,
                        correlation_id VARCHAR(255),
                        rule_name VARCHAR(255),
                        severity VARCHAR(50),
                        pattern TEXT,
                        entities JSONB,
                        count INTEGER,
                        recommended_action VARCHAR(100),
                        status VARCHAR(50) DEFAULT 'OPEN',
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    );
                    
                    CREATE INDEX IF NOT EXISTS idx_siem_findings_timestamp ON siem_findings(created_at);
                    CREATE INDEX IF NOT EXISTS idx_siem_findings_severity ON siem_findings(severity);
                """
                cur.execute(create_table_query)
                conn.commit()
                
                insert_query = """
                    INSERT INTO siem_findings
                    (finding_id, correlation_id, rule_name, severity, pattern, entities, count, recommended_action)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (finding_id) DO NOTHING
                """
                cur.execute(insert_query, (
                    finding['correlation_id'],
                    finding['correlation_id'],
                    finding['rule_name'],
                    finding['severity'],
                    finding['pattern'],
                    json.dumps(finding['entities']),
                    finding['count'],
                    finding['recommended_action']
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Error storing SIEM finding: {e}")
            if conn:
                conn.rollback()
        finally:
            return_db_connection(conn)


class SOARAutomation:
    """SOAR automatic response actions."""
    
    def __init__(self):
        self.siem = SIEMCorrelation()
    
    def execute_response(self, finding: Dict) -> Dict:
        """
        Execute automatic response based on correlation finding.
        
        Args:
            finding: Correlation finding dictionary
            
        Returns:
            Dict with action_result
        """
        action = finding.get('recommended_action')
        entities = finding.get('entities', {})
        
        result = {
            'action': action,
            'status': 'pending',
            'timestamp': datetime.now().isoformat()
        }
        
        if action == 'block_ip':
            ip_address = entities.get('ip_address')
            if ip_address:
                result = self._block_ip(ip_address)
        
        elif action == 'flag_user':
            wallet_address = entities.get('wallet_address')
            if wallet_address:
                result = self._flag_user(wallet_address)
        
        elif action == 'rate_limit_aggressive':
            ip_address = entities.get('ip_address')
            if ip_address:
                result = self._rate_limit_aggressive(ip_address)
        
        return result
    
    def _block_ip(self, ip_address: str) -> Dict:
        """Block IP address."""
        conn = get_db_connection()
        if not conn:
            return {'status': 'error', 'message': 'Database connection failed'}
        
        try:
            with conn.cursor() as cur:
                # Create banned_ips table if not exists
                create_table_query = """
                    CREATE TABLE IF NOT EXISTS banned_ips (
                        ip_address VARCHAR(255) PRIMARY KEY,
                        reason VARCHAR(255),
                        created_at TIMESTAMPTZ DEFAULT NOW(),
                        expires_at TIMESTAMPTZ
                    );
                """
                cur.execute(create_table_query)
                conn.commit()
                
                # Insert ban
                expires_at = datetime.now() + timedelta(hours=24)  # 24 hour ban
                insert_query = """
                    INSERT INTO banned_ips (ip_address, reason, expires_at)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (ip_address) DO UPDATE
                    SET expires_at = EXCLUDED.expires_at, created_at = NOW()
                """
                cur.execute(insert_query, (ip_address, 'SIEM automated ban', expires_at))
                conn.commit()
                
                logger.info(f"Blocked IP address: {ip_address}")
                return {
                    'status': 'success',
                    'action': 'block_ip',
                    'ip_address': ip_address,
                    'expires_at': expires_at.isoformat()
                }
        except Exception as e:
            logger.error(f"Error blocking IP: {e}")
            return {'status': 'error', 'message': str(e)}
        finally:
            return_db_connection(conn)
    
    def _flag_user(self, wallet_address: str) -> Dict:
        """Flag user for review."""
        conn = get_db_connection()
        if not conn:
            return {'status': 'error', 'message': 'Database connection failed'}
        
        try:
            with conn.cursor() as cur:
                # Create flagged_users table if not exists
                create_table_query = """
                    CREATE TABLE IF NOT EXISTS flagged_users (
                        wallet_address VARCHAR(255) PRIMARY KEY,
                        reason VARCHAR(255),
                        severity VARCHAR(50),
                        created_at TIMESTAMPTZ DEFAULT NOW()
                    );
                """
                cur.execute(create_table_query)
                conn.commit()
                
                insert_query = """
                    INSERT INTO flagged_users (wallet_address, reason, severity)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (wallet_address) DO UPDATE
                    SET reason = EXCLUDED.reason, created_at = NOW()
                """
                cur.execute(insert_query, (wallet_address, 'SIEM automated flag', 'MEDIUM'))
                conn.commit()
                
                logger.info(f"Flagged user: {wallet_address}")
                return {
                    'status': 'success',
                    'action': 'flag_user',
                    'wallet_address': wallet_address
                }
        except Exception as e:
            logger.error(f"Error flagging user: {e}")
            return {'status': 'error', 'message': str(e)}
        finally:
            return_db_connection(conn)
    
    def _rate_limit_aggressive(self, ip_address: str) -> Dict:
        """Apply aggressive rate limiting to IP."""
        # Store in Redis with reduced limit
        from data_control.db_connection import get_redis_client
        redis_client = get_redis_client()
        
        if redis_client:
            try:
                key = f"rate_limit:aggressive:{ip_address}"
                redis_client.setex(key, 3600, "true")  # 1 hour
                logger.info(f"Applied aggressive rate limiting to: {ip_address}")
                return {
                    'status': 'success',
                    'action': 'rate_limit_aggressive',
                    'ip_address': ip_address,
                    'duration_seconds': 3600
                }
            except Exception as e:
                logger.error(f"Error applying rate limit: {e}")
                return {'status': 'error', 'message': str(e)}
        
        return {'status': 'error', 'message': 'Redis not available'}
    
    def process_findings(self):
        """Process all open correlation findings and execute responses."""
        findings = self.siem.correlate_events()
        
        results = []
        for finding in findings:
            if finding.get('severity') in ['HIGH', 'CRITICAL']:
                result = self.execute_response(finding)
                results.append({
                    'finding': finding,
                    'response': result
                })
        
        return results


# Singleton instances
_siem = None
_soar = None

def get_siem() -> SIEMCorrelation:
    """Get singleton SIEM instance."""
    global _siem
    if _siem is None:
        _siem = SIEMCorrelation()
    return _siem

def get_soar() -> SOARAutomation:
    """Get singleton SOAR instance."""
    global _soar
    if _soar is None:
        _soar = SOARAutomation()
    return _soar

