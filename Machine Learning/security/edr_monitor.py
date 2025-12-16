"""
EDR (Endpoint Detection & Response) Monitoring for ML Execution Environment
Monitors ML processes, detects suspicious behavior, and logs security events.
"""

import os
import sys
import psutil
import logging
from typing import Dict, Optional, List
from datetime import datetime, timezone
from pathlib import Path
import hashlib

logger = logging.getLogger(__name__)


class MLEDRMonitor:
    """
    EDR-like monitoring for ML execution environment.
    
    Monitors:
    - ML process execution
    - File access patterns
    - Suspicious process behavior
    - Unauthorized access attempts
    - Resource anomalies
    """
    
    def __init__(self, log_file: Optional[Path] = None):
        """
        Initialize EDR monitor.
        
        Args:
            log_file: Path to log file for EDR events
        """
        self.log_file = log_file or Path(__file__).parent.parent / "logs" / "edr_events.log"
        self.log_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Baseline process hashes for integrity checking
        self.baseline_processes = self._get_baseline_processes()
        
        # Suspicious process patterns
        self.suspicious_patterns = [
            'nc', 'netcat', 'ncat',
            'sh', 'bash', '-c',
            'python -c', 'python -m',
            'curl', 'wget',
            'base64', 'xxd',
            'dd if=', 'cat /etc/passwd',
            'rm -rf',
            'mkfifo',
            'telnet',
            'ssh', 'scp'
        ]
    
    def _get_baseline_processes(self) -> Dict[str, str]:
        """Get baseline process hashes for integrity checking."""
        baseline = {}
        try:
            current_process = psutil.Process()
            baseline['python'] = self._hash_process(current_process)
            
            # Hash parent process if available
            try:
                parent = current_process.parent()
                if parent:
                    baseline['parent'] = self._hash_process(parent)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        except Exception as e:
            logger.warning(f"Could not establish baseline processes: {e}")
        
        return baseline
    
    def _hash_process(self, process: psutil.Process) -> str:
        """Generate hash for process identification."""
        try:
            info = {
                'name': process.name(),
                'exe': process.exe() if process.exe() else '',
                'cmdline': ' '.join(process.cmdline()) if process.cmdline() else ''
            }
            content = f"{info['name']}:{info['exe']}:{info['cmdline']}"
            return hashlib.sha256(content.encode()).hexdigest()[:16]
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return "unknown"
    
    def monitor_ml_execution(self, operation: str, context: Dict) -> Dict:
        """
        Monitor ML operation execution.
        
        Args:
            operation: Operation name (e.g., 'model_predict', 'feature_engineering')
            context: Context information (model_name, inputs, etc.)
            
        Returns:
            Dict with monitoring result and alerts
        """
        result = {
            'operation': operation,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'status': 'ok',
            'alerts': []
        }
        
        try:
            # Check current process
            current_process = psutil.Process()
            process_info = {
                'pid': current_process.pid,
                'name': current_process.name(),
                'exe': current_process.exe() if current_process.exe() else 'unknown',
                'cmdline': current_process.cmdline() if current_process.cmdline() else [],
                'cpu_percent': current_process.cpu_percent(interval=0.1),
                'memory_mb': current_process.memory_info().rss / 1024 / 1024,
            }
            result['process_info'] = process_info
            
            # Check for suspicious command line arguments
            cmdline_str = ' '.join(process_info['cmdline'])
            for pattern in self.suspicious_patterns:
                if pattern.lower() in cmdline_str.lower():
                    alert = {
                        'severity': 'HIGH',
                        'type': 'SUSPICIOUS_COMMAND',
                        'pattern': pattern,
                        'cmdline': cmdline_str
                    }
                    result['alerts'].append(alert)
                    self._log_edr_event('SUSPICIOUS_COMMAND', alert, process_info)
            
            # Check resource usage anomalies
            if process_info['cpu_percent'] > 90:
                alert = {
                    'severity': 'MEDIUM',
                    'type': 'HIGH_CPU_USAGE',
                    'cpu_percent': process_info['cpu_percent']
                }
                result['alerts'].append(alert)
                self._log_edr_event('HIGH_CPU_USAGE', alert, process_info)
            
            if process_info['memory_mb'] > 4096:  # 4GB threshold
                alert = {
                    'severity': 'MEDIUM',
                    'type': 'HIGH_MEMORY_USAGE',
                    'memory_mb': process_info['memory_mb']
                }
                result['alerts'].append(alert)
                self._log_edr_event('HIGH_MEMORY_USAGE', alert, process_info)
            
            # Check child processes
            try:
                children = current_process.children(recursive=True)
                if len(children) > 5:  # Unusual number of child processes
                    alert = {
                        'severity': 'MEDIUM',
                        'type': 'EXCESSIVE_CHILD_PROCESSES',
                        'child_count': len(children)
                    }
                    result['alerts'].append(alert)
                    self._log_edr_event('EXCESSIVE_CHILD_PROCESSES', alert, process_info)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
            
            # Update status if alerts found
            if result['alerts']:
                result['status'] = 'alert'
            
            # Log normal operation
            self._log_edr_event('ML_OPERATION', {
                'operation': operation,
                'context': context
            }, process_info)
            
        except Exception as e:
            logger.error(f"EDR monitoring error: {e}", exc_info=True)
            result['status'] = 'error'
            result['error'] = str(e)
        
        return result
    
    def monitor_file_access(self, file_path: Path, operation: str) -> Dict:
        """
        Monitor file access patterns.
        
        Args:
            file_path: Path to file being accessed
            operation: Operation type ('read', 'write', 'execute')
            
        Returns:
            Dict with monitoring result
        """
        result = {
            'file_path': str(file_path),
            'operation': operation,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'status': 'ok',
            'alerts': []
        }
        
        try:
            # Check for sensitive file access
            sensitive_patterns = [
                '/etc/passwd',
                '/etc/shadow',
                '.env',
                '.ssh',
                'private_key',
                'secret',
                'credentials'
            ]
            
            file_path_str = str(file_path).lower()
            for pattern in sensitive_patterns:
                if pattern in file_path_str:
                    alert = {
                        'severity': 'HIGH',
                        'type': 'SENSITIVE_FILE_ACCESS',
                        'pattern': pattern,
                        'file_path': str(file_path)
                    }
                    result['alerts'].append(alert)
                    self._log_edr_event('SENSITIVE_FILE_ACCESS', alert, {})
                    break
            
            # Check for unauthorized directory access
            if operation == 'write':
                # ML should only write to specific directories
                allowed_dirs = [
                    'Machine Learning/artifacts',
                    'Machine Learning/logs',
                    'backend/logs'
                ]
                is_allowed = any(allowed_dir in str(file_path) for allowed_dir in allowed_dirs)
                
                if not is_allowed and 'artifacts' not in str(file_path) and 'logs' not in str(file_path):
                    alert = {
                        'severity': 'MEDIUM',
                        'type': 'UNAUTHORIZED_WRITE',
                        'file_path': str(file_path)
                    }
                    result['alerts'].append(alert)
                    self._log_edr_event('UNAUTHORIZED_WRITE', alert, {})
            
        except Exception as e:
            logger.error(f"File access monitoring error: {e}", exc_info=True)
            result['status'] = 'error'
        
        return result
    
    def _log_edr_event(self, event_type: str, data: Dict, process_info: Dict):
        """Log EDR event to file."""
        try:
            event = {
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'event_type': event_type,
                'data': data,
                'process_info': process_info
            }
            
            with open(self.log_file, 'a') as f:
                import json
                f.write(json.dumps(event) + '\n')
            
            logger.warning(f"EDR Event: {event_type} - {data}")
        except Exception as e:
            logger.error(f"EDR logging error: {e}")


# Singleton instance
_edr_monitor = None

def get_edr_monitor() -> MLEDRMonitor:
    """Get singleton EDR monitor instance."""
    global _edr_monitor
    if _edr_monitor is None:
        _edr_monitor = MLEDRMonitor()
    return _edr_monitor


if __name__ == "__main__":
    # Example usage
    monitor = get_edr_monitor()
    
    # Monitor ML operation
    result = monitor.monitor_ml_execution('model_predict', {
        'model_name': 'fraud_detection',
        'input_size': 10
    })
    print(f"Monitoring result: {result}")

