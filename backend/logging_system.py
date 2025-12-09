"""
Advanced logging system with file rotation and structured logging.
Supports JSON and plain text formats, with automatic log rotation.
"""
import logging
import logging.handlers
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any
from enum import Enum
from supabase import Client

from database import get_supabase_admin


class LogType(str, Enum):
    """Log event types."""
    AUTH_LOGIN = "AUTH_LOGIN"
    AUTH_LOGOUT = "AUTH_LOGOUT"
    AUTH_FAILED_LOGIN = "AUTH_FAILED_LOGIN"
    AUTH_PASSWORD_CHANGE = "AUTH_PASSWORD_CHANGE"
    HTTP_REQUEST = "HTTP_REQUEST"
    ADMIN_ACTION = "ADMIN_ACTION"
    SYSTEM_WARNING = "SYSTEM_WARNING"
    SYSTEM_ERROR = "SYSTEM_ERROR"
    USER_CREATED = "USER_CREATED"
    USER_DELETED = "USER_DELETED"
    USER_SUSPENDED = "USER_SUSPENDED"
    USER_ACTIVATED = "USER_ACTIVATED"
    ALERT_CLEARED = "ALERT_CLEARED"
    ALERT_EXPORTED = "ALERT_EXPORTED"
    DATA_EXPORTED = "DATA_EXPORTED"


class LogLevel(str, Enum):
    """Log levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LoggingSystem:
    """Centralized logging system with file rotation and database storage."""
    
    def __init__(self, log_dir: str = "logs"):
        """Initialize logging system.
        
        Args:
            log_dir: Directory to store log files
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Setup file handlers
        self._setup_file_handlers()
        
        # Database client (lazy loaded)
        self._db: Optional[Client] = None
    
    def _setup_file_handlers(self):
        """Setup file handlers for JSON and plain text logs."""
        # JSON log handler (structured logs)
        json_handler = logging.handlers.RotatingFileHandler(
            filename=self.log_dir / "app.json.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=10,
            encoding='utf-8'
        )
        json_handler.setFormatter(JSONFormatter())
        json_handler.setLevel(logging.INFO)
        
        # Plain text log handler
        text_handler = logging.handlers.RotatingFileHandler(
            filename=self.log_dir / "app.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=10,
            encoding='utf-8'
        )
        text_handler.setFormatter(
            logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        )
        text_handler.setLevel(logging.INFO)
        
        # Error log handler (errors only)
        error_handler = logging.handlers.RotatingFileHandler(
            filename=self.log_dir / "errors.log",
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=20,  # Keep more error logs
            encoding='utf-8'
        )
        error_handler.setFormatter(JSONFormatter())
        error_handler.setLevel(logging.ERROR)
        
        # Get root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(json_handler)
        root_logger.addHandler(text_handler)
        root_logger.addHandler(error_handler)
    
    def log_event(
        self,
        log_type: LogType,
        message: str,
        log_level: LogLevel = LogLevel.INFO,
        user_id: Optional[int] = None,
        username: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        endpoint: Optional[str] = None,
        http_method: Optional[str] = None,
        status_code: Optional[int] = None,
        request_payload: Optional[Dict[str, Any]] = None,
        response_payload: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Log an event to both files and database.
        
        Args:
            log_type: Type of log event
            message: Log message
            log_level: Log level
            user_id: User ID if applicable
            username: Username if applicable
            ip_address: IP address
            user_agent: User agent string
            endpoint: API endpoint
            http_method: HTTP method
            status_code: HTTP status code
            request_payload: Request payload
            response_payload: Response payload
            metadata: Additional metadata
        """
        # Prepare log data
        log_data = {
            "log_type": log_type.value,
            "log_level": log_level.value,
            "message": message,
            "user_id": user_id,
            "username": username,
            "ip_address": ip_address,
            "user_agent": user_agent,
            "endpoint": endpoint,
            "http_method": http_method,
            "status_code": status_code,
            "request_payload": request_payload,
            "response_payload": response_payload,
            "metadata": metadata or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
        # Log to file
        logger = logging.getLogger(__name__)
        log_message = f"[{log_type.value}] {message}"
        
        if log_level == LogLevel.DEBUG:
            logger.debug(log_message, extra={"log_data": log_data})
        elif log_level == LogLevel.INFO:
            logger.info(log_message, extra={"log_data": log_data})
        elif log_level == LogLevel.WARNING:
            logger.warning(log_message, extra={"log_data": log_data})
        elif log_level == LogLevel.ERROR:
            logger.error(log_message, extra={"log_data": log_data})
        elif log_level == LogLevel.CRITICAL:
            logger.critical(log_message, extra={"log_data": log_data})
        
        # Store in database (async, don't block)
        try:
            self._store_in_database(log_data)
        except Exception as e:
            # Don't fail if database logging fails
            logger.error(f"Failed to store log in database: {e}")
    
    def _store_in_database(self, log_data: Dict[str, Any]):
        """Store log in database."""
        if not self._db:
            self._db = get_supabase_admin()
        
        try:
            # Prepare database record
            db_record = {
                "log_level": log_data["log_level"],
                "log_type": log_data["log_type"],
                "message": log_data["message"],
                "user_id": log_data.get("user_id"),
                "username": log_data.get("username"),
                "ip_address": log_data.get("ip_address"),
                "user_agent": log_data.get("user_agent"),
                "endpoint": log_data.get("endpoint"),
                "http_method": log_data.get("http_method"),
                "status_code": log_data.get("status_code"),
                "request_payload": log_data.get("request_payload"),
                "response_payload": log_data.get("response_payload"),
                "metadata": log_data.get("metadata"),
                "log_data": log_data,
            }
            
            self._db.table("application_logs").insert(db_record).execute()
        except Exception as e:
            # Log error but don't raise
            logging.getLogger(__name__).error(f"Database log storage failed: {e}")


class JSONFormatter(logging.Formatter):
    """Custom formatter for JSON logs."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.fromtimestamp(
                record.created, tz=timezone.utc
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add extra fields if present
        if hasattr(record, "log_data"):
            log_data.update(record.log_data)
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        return json.dumps(log_data, ensure_ascii=False)


# Global logging system instance
_logging_system: Optional[LoggingSystem] = None


def get_logging_system() -> LoggingSystem:
    """Get global logging system instance."""
    global _logging_system
    if _logging_system is None:
        _logging_system = LoggingSystem()
    return _logging_system

