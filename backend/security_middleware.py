"""Security detection middleware for detecting attacks and suspicious activities."""
import re
import json
import logging
from typing import Optional, Dict, Any, List
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from datetime import datetime, timezone, timedelta
from collections import defaultdict
from supabase import Client

from database import get_supabase_admin

logger = logging.getLogger(__name__)

# In-memory rate limiting (in production, use Redis)
rate_limit_store: Dict[str, List[datetime]] = defaultdict(list)
failed_login_attempts: Dict[str, List[datetime]] = defaultdict(list)

# XSS Detection Patterns
XSS_PATTERNS = [
    r'<script[^>]*>',
    r'javascript:',
    r'onerror\s*=',
    r'onload\s*=',
    r'onclick\s*=',
    r'<img[^>]*onerror',
    r'<iframe[^>]*>',
    r'<svg[^>]*onload',
    r'<body[^>]*onload',
    r'<input[^>]*onfocus',
    r'eval\s*\(',
    r'alert\s*\(',
    r'document\.cookie',
    r'document\.write',
    r'innerHTML',
    r'<script',
    r'%3Cscript',
    r'%3C%2Fscript',
    r'&#60;script',
    r'&#x3C;script',
]

# SQL Injection Detection Patterns
SQL_INJECTION_PATTERNS = [
    r"('|(\\')|(;)|(\\;)|(--)|(\\--)|(/\*)|(\\/\*)|(\*/)|(\\\*/))",
    r"(\bOR\b|\bAND\b)\s+\d+\s*=\s*\d+",
    r"(\bOR\b|\bAND\b)\s+['\"]\w+['\"]\s*=\s*['\"]\w+['\"]",
    r"\bUNION\s+SELECT\b",
    r"\bSELECT\s+.*\bFROM\b",
    r"\bINSERT\s+INTO\b",
    r"\bUPDATE\s+.*\bSET\b",
    r"\bDELETE\s+FROM\b",
    r"\bDROP\s+TABLE\b",
    r"\bDROP\s+DATABASE\b",
    r"\bTRUNCATE\s+TABLE\b",
    r"\bEXEC\s*\(",
    r"\bEXECUTE\s*\(",
    r"information_schema",
    r"pg_catalog",
    r"sys\.tables",
    r"sys\.databases",
    r"sleep\s*\(",
    r"waitfor\s+delay",
    r"benchmark\s*\(",
]

# Command Injection Detection Patterns
COMMAND_INJECTION_PATTERNS = [
    r';\s*(rm|cat|ls|pwd|whoami|id|uname)',
    r'&&\s*(rm|cat|ls|pwd|whoami|id|uname)',
    r'\|\s*(rm|cat|ls|pwd|whoami|id|uname)',
    r'`[^`]*`',
    r'\$\([^)]+\)',
    r'<\([^>]+\)',
    r'curl\s+',
    r'wget\s+',
    r'bash\s+-c',
    r'sh\s+-c',
    r'nc\s+',
    r'python\s+-c',
    r'perl\s+-e',
]

# Suspicious User Agents
SUSPICIOUS_USER_AGENTS = [
    'sqlmap',
    'nikto',
    'nmap',
    'masscan',
    'zap',
    'burp',
    'w3af',
    'acunetix',
    'nessus',
    'openvas',
    'metasploit',
    'havij',
    'pangolin',
    'sqlninja',
    'wpscan',
    'dirb',
    'dirbuster',
    'gobuster',
    'wfuzz',
    'ffuf',
    'scanner',
    'bot',
    'crawler',
    'spider',
    'hack',
    'exploit',
    'inject',
    'test',
    'admin',
    'root',
]


def detect_xss(content: str) -> bool:
    """Detect XSS patterns in content."""
    if not content:
        return False
    
    content_lower = content.lower()
    for pattern in XSS_PATTERNS:
        if re.search(pattern, content_lower, re.IGNORECASE):
            return True
    return False


def detect_sql_injection(content: str) -> bool:
    """Detect SQL injection patterns in content."""
    if not content:
        return False
    
    content_lower = content.lower()
    for pattern in SQL_INJECTION_PATTERNS:
        if re.search(pattern, content_lower, re.IGNORECASE):
            return True
    return False


def detect_command_injection(content: str) -> bool:
    """Detect command injection patterns in content."""
    if not content:
        return False
    
    content_lower = content.lower()
    for pattern in COMMAND_INJECTION_PATTERNS:
        if re.search(pattern, content_lower, re.IGNORECASE):
            return True
    return False


def detect_suspicious_user_agent(user_agent: Optional[str]) -> bool:
    """Detect suspicious user agent strings."""
    if not user_agent:
        return False
    
    user_agent_lower = user_agent.lower()
    for suspicious in SUSPICIOUS_USER_AGENTS:
        if suspicious in user_agent_lower:
            return True
    return False


def calculate_risk_score(attack_type: str, severity: str, payload: Optional[str] = None) -> int:
    """Calculate risk score (0-100) based on attack type and severity."""
    base_scores = {
        'XSS': 60,
        'SQL_INJECTION': 80,
        'COMMAND_INJECTION': 90,
        'BRUTE_FORCE': 50,
        'UNAUTHORIZED_ACCESS': 70,
        'API_ABUSE': 40,
        'SUSPICIOUS_ACTIVITY': 30,
        'RATE_LIMIT_EXCEEDED': 35,
        'INVALID_TOKEN': 45,
        'PENETRATION_TEST': 75,
    }
    
    severity_multipliers = {
        'LOW': 0.5,
        'MEDIUM': 0.75,
        'HIGH': 1.0,
        'CRITICAL': 1.25,
    }
    
    base_score = base_scores.get(attack_type, 50)
    multiplier = severity_multipliers.get(severity, 1.0)
    risk_score = int(base_score * multiplier)
    
    # Adjust based on payload complexity
    if payload and len(payload) > 200:
        risk_score = min(100, risk_score + 10)
    
    return min(100, max(0, risk_score))


def determine_severity(attack_type: str, risk_score: int) -> str:
    """Determine severity based on attack type and risk score."""
    if risk_score >= 80:
        return 'CRITICAL'
    elif risk_score >= 60:
        return 'HIGH'
    elif risk_score >= 40:
        return 'MEDIUM'
    else:
        return 'LOW'


def sanitize_payload(payload: str) -> str:
    """Sanitize payload to prevent XSS when displaying in admin panel."""
    if not payload:
        return ""
    
    # Escape HTML special characters
    payload = payload.replace('&', '&amp;')
    payload = payload.replace('<', '&lt;')
    payload = payload.replace('>', '&gt;')
    payload = payload.replace('"', '&quot;')
    payload = payload.replace("'", '&#x27;')
    
    # Truncate if too long
    if len(payload) > 1000:
        payload = payload[:1000] + "... [truncated]"
    
    return payload


async def log_security_alert(
    db: Client,
    attack_type: str,
    request: Request,
    user_id: Optional[int] = None,
    payload: Optional[str] = None,
    endpoint: Optional[str] = None,
    severity: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """Log security alert to database with deduplication."""
    try:
        ip_address = request.client.host if request.client else "unknown"
        user_agent = request.headers.get("user-agent", "unknown")
        endpoint_path = endpoint or str(request.url.path)
        
        # DEDUPLICATION: Check for duplicate alert in last 5 seconds
        # This prevents multiple alerts for the same attack attempt
        five_seconds_ago = datetime.now(timezone.utc) - timedelta(seconds=5)
        
        duplicate_check = db.table("security_alerts").select("alert_id").eq(
            "ip_address", ip_address
        ).eq("attack_type", attack_type).eq("endpoint", endpoint_path)
        
        if user_id:
            duplicate_check = duplicate_check.eq("user_id", user_id)
        else:
            duplicate_check = duplicate_check.is_("user_id", "null")
        
        # Check for recent duplicate (same attack type, same IP, same endpoint, within 5 seconds)
        duplicate_check = duplicate_check.gte("created_at", five_seconds_ago.isoformat()).limit(1).execute()
        
        if duplicate_check.data:
            # Duplicate alert detected - skip insertion
            logger.debug(
                f"Skipping duplicate alert: {attack_type} from {ip_address} at {endpoint_path} "
                f"(duplicate found within 5 seconds)"
            )
            return None
        
        # Calculate risk score and severity
        risk_score = calculate_risk_score(attack_type, severity or "MEDIUM", payload)
        if not severity:
            severity = determine_severity(attack_type, risk_score)
        
        # Sanitize payload
        sanitized_payload = sanitize_payload(payload) if payload else None
        
        # Prepare alert data
        alert_data = {
            "user_id": user_id,
            "ip_address": ip_address,
            "attack_type": attack_type,
            "payload": sanitized_payload,
            "endpoint": endpoint_path,
            "severity": severity,
            "risk_score": risk_score,
            "status": "NEW",
            "user_agent": user_agent,
            "metadata": json.dumps(metadata or {})
        }
        
        # Insert alert
        result = db.table("security_alerts").insert(alert_data).execute()
        
        alert_id = result.data[0].get("alert_id") if result.data else None
        
        logger.warning(f"Security alert logged: {attack_type} from {ip_address} at {endpoint}")
        
        # Check for auto-ban conditions (legacy)
        await check_auto_ban_conditions(db, user_id, ip_address, attack_type, severity)
        
        # NEW: Track attack and check for auto-suspension/ban (2+ = suspend, 10+ = ban)
        from attack_tracking import track_attack_and_check_suspension
        suspension_result = await track_attack_and_check_suspension(
            db, user_id, ip_address, attack_type, alert_id
        )
        
        if suspension_result.get("action"):
            logger.warning(
                f"User {user_id} {suspension_result['action']} automatically "
                f"due to {suspension_result.get('attack_count', 0)} attack attempts"
            )
        
        return result.data[0] if result.data else None
        
    except Exception as e:
        logger.error(f"Error logging security alert: {e}", exc_info=True)
        return None


async def check_auto_ban_conditions(
    db: Client,
    user_id: Optional[int],
    ip_address: str,
    attack_type: str,
    severity: str
):
    """Check if auto-ban conditions are met."""
    try:
        # Rule 1: 3+ critical alerts from same user → auto ban
        if user_id and severity == 'CRITICAL':
            critical_count = db.table("security_alerts").select("alert_id", count="exact").eq("user_id", user_id).eq("severity", "CRITICAL").eq("status", "NEW").execute()
            
            if critical_count.count and critical_count.count >= 3:
                # Auto-ban user
                ban_data = {
                    "user_id": user_id,
                    "ban_type": "USER",
                    "ban_reason": f"Auto-banned: 3+ critical security alerts",
                    "ban_duration": "PERMANENT",
                    "is_active": True
                }
                db.table("bans").insert(ban_data).execute()
                
                # Update user status
                db.table("users").update({"is_active": False}).eq("user_id", user_id).execute()
                
                logger.warning(f"Auto-banned user {user_id} due to 3+ critical alerts")
        
        # Rule 2: Same IP triggers >10 alerts in 5 minutes → temp block
        five_min_ago = datetime.now(timezone.utc) - timedelta(minutes=5)
        recent_alerts = db.table("security_alerts").select("alert_id", count="exact").eq("ip_address", ip_address).gte("created_at", five_min_ago.isoformat()).execute()
        
        if recent_alerts.count and recent_alerts.count > 10:
            # Check if IP is already banned
            existing_ban = db.table("bans").select("ban_id").eq("ip_address", ip_address).eq("is_active", True).execute()
            
            if not existing_ban.data:
                # Auto-ban IP temporarily (1 hour)
                expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
                ban_data = {
                    "ip_address": ip_address,
                    "ban_type": "IP",
                    "ban_reason": f"Auto-banned: {recent_alerts.count} alerts in 5 minutes",
                    "ban_duration": "TEMPORARY",
                    "expires_at": expires_at.isoformat(),
                    "is_active": True
                }
                db.table("bans").insert(ban_data).execute()
                
                logger.warning(f"Auto-banned IP {ip_address} temporarily due to excessive alerts")
                
    except Exception as e:
        logger.error(f"Error checking auto-ban conditions: {e}", exc_info=True)


def is_banned(db: Client, user_id: Optional[int] = None, ip_address: Optional[str] = None) -> bool:
    """Check if user or IP is banned."""
    try:
        now = datetime.now(timezone.utc)
        
        # Check user ban
        if user_id:
            user_ban = db.table("bans").select("ban_id").eq("user_id", user_id).eq("is_active", True).execute()
            if user_ban.data:
                # Check if temporary ban expired
                ban_details = db.table("bans").select("*").eq("user_id", user_id).eq("is_active", True).execute()
                for ban in ban_details.data:
                    if ban.get("expires_at"):
                        expires = datetime.fromisoformat(ban["expires_at"].replace("Z", "+00:00"))
                        if expires > now:
                            return True
                        else:
                            # Ban expired, deactivate it
                            db.table("bans").update({"is_active": False}).eq("ban_id", ban["ban_id"]).execute()
                    else:
                        return True  # Permanent ban
        
        # Check IP ban
        if ip_address:
            ip_ban = db.table("bans").select("ban_id").eq("ip_address", ip_address).eq("is_active", True).execute()
            if ip_ban.data:
                # Check if temporary ban expired
                ban_details = db.table("bans").select("*").eq("ip_address", ip_address).eq("is_active", True).execute()
                for ban in ban_details.data:
                    if ban.get("expires_at"):
                        expires = datetime.fromisoformat(ban["expires_at"].replace("Z", "+00:00"))
                        if expires > now:
                            return True
                        else:
                            # Ban expired, deactivate it
                            db.table("bans").update({"is_active": False}).eq("ban_id", ban["ban_id"]).execute()
                    else:
                        return True  # Permanent ban
        
        return False
        
    except Exception as e:
        logger.error(f"Error checking ban status: {e}", exc_info=True)
        return False


async def security_middleware(request: Request, call_next):
    """Main security middleware that detects attacks."""
    db = get_supabase_admin()
    
    # Get client info
    ip_address = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    # Check if IP or user is banned
    user_id = None
    try:
        # Try to get current user from Authorization header (optional)
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            from auth_utils import verify_token
            token = auth_header.replace("Bearer ", "")
            payload = verify_token(token, token_type="access")
            if payload and payload.get("type") == "access":
                user_id = int(payload.get("sub", 0)) if payload.get("sub") else None
    except:
        pass
    
    if is_banned(db, user_id, ip_address):
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"detail": "Access denied: Your account or IP has been banned"}
        )
    
    # Get request body for inspection
    body = None
    try:
        if request.method in ["POST", "PUT", "PATCH"]:
            body_bytes = await request.body()
            if body_bytes:
                try:
                    body = json.loads(body_bytes.decode('utf-8'))
                    body_str = json.dumps(body)
                except:
                    body_str = body_bytes.decode('utf-8', errors='ignore')
                else:
                    body_str = json.dumps(body)
            else:
                body_str = ""
        else:
            body_str = ""
            # Check query parameters
            query_str = str(request.query_params)
    except Exception as e:
        logger.error(f"Error reading request body: {e}")
        body_str = ""
    
    # Check query parameters
    query_str = str(request.query_params)
    endpoint = str(request.url.path)
    
    # Detection checks
    attack_detected = False
    attack_type = None
    severity = None
    payload = None
    
    # 1. XSS Detection
    if body_str and detect_xss(body_str):
        attack_detected = True
        attack_type = "XSS"
        severity = "HIGH"
        payload = body_str[:500]  # Limit payload size
    elif query_str and detect_xss(query_str):
        attack_detected = True
        attack_type = "XSS"
        severity = "HIGH"
        payload = query_str[:500]
    
    # 2. SQL Injection Detection
    if not attack_detected:
        if body_str and detect_sql_injection(body_str):
            attack_detected = True
            attack_type = "SQL_INJECTION"
            severity = "CRITICAL"
            payload = body_str[:500]
        elif query_str and detect_sql_injection(query_str):
            attack_detected = True
            attack_type = "SQL_INJECTION"
            severity = "CRITICAL"
            payload = query_str[:500]
    
    # 3. Command Injection Detection
    if not attack_detected:
        if body_str and detect_command_injection(body_str):
            attack_detected = True
            attack_type = "COMMAND_INJECTION"
            severity = "CRITICAL"
            payload = body_str[:500]
        elif query_str and detect_command_injection(query_str):
            attack_detected = True
            attack_type = "COMMAND_INJECTION"
            severity = "CRITICAL"
            payload = query_str[:500]
    
    # 4. Suspicious User Agent
    if not attack_detected and detect_suspicious_user_agent(user_agent):
        attack_detected = True
        attack_type = "PENETRATION_TEST"
        severity = "MEDIUM"
        payload = user_agent
    
    # 5. Rate Limiting Check
    rate_limit_key = f"{ip_address}:{endpoint}"
    now = datetime.now(timezone.utc)
    rate_limit_store[rate_limit_key] = [
        ts for ts in rate_limit_store[rate_limit_key]
        if now - ts < timedelta(minutes=1)
    ]
    
    if len(rate_limit_store[rate_limit_key]) > 100:  # 100 requests per minute
        attack_detected = True
        attack_type = "RATE_LIMIT_EXCEEDED"
        severity = "MEDIUM"
        payload = f"Rate limit exceeded: {len(rate_limit_store[rate_limit_key])} requests"
    
    rate_limit_store[rate_limit_key].append(now)
    
    # Log attack if detected
    if attack_detected:
        await log_security_alert(
            db=db,
            attack_type=attack_type,
            request=request,
            user_id=user_id,
            payload=payload,
            endpoint=endpoint,
            severity=severity,
            metadata={
                "method": request.method,
                "user_agent": user_agent,
                "headers": dict(request.headers)
            }
        )
        
        # Block critical attacks
        if severity in ["CRITICAL", "HIGH"]:
            return JSONResponse(
                status_code=status.HTTP_403_FORBIDDEN,
                content={
                    "detail": "Request blocked due to security policy violation",
                    "error_code": "SECURITY_VIOLATION"
                }
            )
    
    # Continue with request
    response = await call_next(request)
    return response

