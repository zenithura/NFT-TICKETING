"""
DLP/DCL (Data Leakage Prevention / Data Classification & Control)
Classifies and masks sensitive data in logs and ML outputs.
"""

import re
import hashlib
import logging
from typing import Dict, Any, Optional, List
from enum import Enum

logger = logging.getLogger(__name__)


class DataClassification(str, Enum):
    """Data classification levels."""
    PUBLIC = "PUBLIC"
    INTERNAL = "INTERNAL"
    CONFIDENTIAL = "CONFIDENTIAL"
    RESTRICTED = "RESTRICTED"


class SensitiveDataTypes(str, Enum):
    """Types of sensitive data."""
    WALLET_ADDRESS = "WALLET_ADDRESS"
    PRIVATE_KEY = "PRIVATE_KEY"
    API_KEY = "API_KEY"
    PASSWORD = "PASSWORD"
    EMAIL = "EMAIL"
    PHONE = "PHONE"
    CREDIT_CARD = "CREDIT_CARD"
    SSN = "SSN"
    IP_ADDRESS = "IP_ADDRESS"
    TRANSACTION_ID = "TRANSACTION_ID"


class DataClassifier:
    """
    Data Classification and Leakage Prevention.
    
    Identifies and classifies sensitive data, masks it in logs,
    and prevents leakage in ML outputs.
    """
    
    def __init__(self):
        """Initialize data classifier."""
        # Patterns for sensitive data detection
        self.patterns = {
            SensitiveDataTypes.WALLET_ADDRESS: [
                r'0x[a-fA-F0-9]{40}',  # Ethereum address
                r'[a-zA-Z0-9]{34}',  # Bitcoin address (base58)
            ],
            SensitiveDataTypes.PRIVATE_KEY: [
                r'-----BEGIN (?:RSA |EC )?PRIVATE KEY-----',
                r'[a-fA-F0-9]{64}',  # 64-char hex (potential private key)
            ],
            SensitiveDataTypes.API_KEY: [
                r'[Aa][Pp][Ii][_-]?[Kk][Ee][Yy][\s:=]+([a-zA-Z0-9_\-]{20,})',
                r'sk_[a-zA-Z0-9]{32,}',
                r'pk_[a-zA-Z0-9]{32,}',
            ],
            SensitiveDataTypes.PASSWORD: [
                r'[Pp]assword[\s:=]+([^\s]+)',
                r'[Pp]asswd[\s:=]+([^\s]+)',
                r'[Pp]wd[\s:=]+([^\s]+)',
            ],
            SensitiveDataTypes.EMAIL: [
                r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            ],
            SensitiveDataTypes.PHONE: [
                r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',
                r'\+?\d{10,15}',
            ],
            SensitiveDataTypes.CREDIT_CARD: [
                r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b',
            ],
            SensitiveDataTypes.SSN: [
                r'\b\d{3}-\d{2}-\d{4}\b',
            ],
            SensitiveDataTypes.IP_ADDRESS: [
                r'\b(?:\d{1,3}\.){3}\d{1,3}\b',
            ],
            SensitiveDataTypes.TRANSACTION_ID: [
                r'txn_[a-zA-Z0-9]{20,}',
                r'transaction_[a-zA-Z0-9]{20,}',
            ],
        }
        
        # Classification levels for each data type
        self.classification_levels = {
            SensitiveDataTypes.WALLET_ADDRESS: DataClassification.CONFIDENTIAL,
            SensitiveDataTypes.PRIVATE_KEY: DataClassification.RESTRICTED,
            SensitiveDataTypes.API_KEY: DataClassification.RESTRICTED,
            SensitiveDataTypes.PASSWORD: DataClassification.RESTRICTED,
            SensitiveDataTypes.EMAIL: DataClassification.CONFIDENTIAL,
            SensitiveDataTypes.PHONE: DataClassification.CONFIDENTIAL,
            SensitiveDataTypes.CREDIT_CARD: DataClassification.RESTRICTED,
            SensitiveDataTypes.SSN: DataClassification.RESTRICTED,
            SensitiveDataTypes.IP_ADDRESS: DataClassification.INTERNAL,
            SensitiveDataTypes.TRANSACTION_ID: DataClassification.INTERNAL,
        }
    
    def classify_data(self, data: Any) -> Dict[str, Any]:
        """
        Classify data and identify sensitive fields.
        
        Args:
            data: Data to classify (dict, string, etc.)
            
        Returns:
            Dict with classification results
        """
        result = {
            'classification': DataClassification.PUBLIC,
            'sensitive_fields': [],
            'risk_score': 0
        }
        
        data_str = self._to_string(data)
        
        # Check for sensitive patterns
        for data_type, patterns in self.patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, data_str, re.IGNORECASE)
                for match in matches:
                    field_info = {
                        'type': data_type.value,
                        'classification': self.classification_levels[data_type].value,
                        'position': match.span(),
                        'match': match.group()[:10] + '...' if len(match.group()) > 10 else match.group()
                    }
                    result['sensitive_fields'].append(field_info)
                    
                    # Update overall classification (highest level wins)
                    field_class = self.classification_levels[data_type]
                    if self._classification_level(result['classification']) < self._classification_level(field_class):
                        result['classification'] = field_class
        
        # Calculate risk score (0-100)
        if result['sensitive_fields']:
            result['risk_score'] = min(100, len(result['sensitive_fields']) * 20)
            if any(f['classification'] == DataClassification.RESTRICTED.value for f in result['sensitive_fields']):
                result['risk_score'] = 100
        
        return result
    
    def mask_sensitive_data(self, data: Any, mask_char: str = '*') -> Any:
        """
        Mask sensitive data in logs or outputs.
        
        Args:
            data: Data to mask
            mask_char: Character to use for masking
            
        Returns:
            Masked data
        """
        if isinstance(data, dict):
            return {k: self.mask_sensitive_data(v, mask_char) for k, v in data.items()}
        elif isinstance(data, list):
            return [self.mask_sensitive_data(item, mask_char) for item in data]
        elif isinstance(data, str):
            return self._mask_string(data, mask_char)
        else:
            return data
    
    def _mask_string(self, text: str, mask_char: str = '*') -> str:
        """Mask sensitive patterns in string."""
        masked = text
        
        # Mask wallet addresses (keep first 6 and last 4 chars)
        masked = re.sub(
            r'0x([a-fA-F0-9]{6})[a-fA-F0-9]{30}([a-fA-F0-9]{4})',
            lambda m: f"0x{m.group(1)}{mask_char * 30}{m.group(2)}",
            masked
        )
        
        # Mask API keys (keep first 8 chars)
        masked = re.sub(
            r'([Aa][Pp][Ii][_-]?[Kk][Ee][Yy][\s:=]+)([a-zA-Z0-9_\-]{8})([a-zA-Z0-9_\-]{12,})',
            lambda m: f"{m.group(1)}{m.group(2)}{mask_char * len(m.group(3))}",
            masked
        )
        
        # Mask passwords
        masked = re.sub(
            r'([Pp]assword[\s:=]+)([^\s]+)',
            lambda m: f"{m.group(1)}{mask_char * min(len(m.group(2)), 20)}",
            masked
        )
        
        # Mask emails (keep domain)
        masked = re.sub(
            r'\b([A-Za-z0-9._%+-]{1,3})[A-Za-z0-9._%+-]*@([A-Za-z0-9.-]+\.[A-Z|a-z]{2,})\b',
            lambda m: f"{m.group(1)}{mask_char * 5}@{m.group(2)}",
            masked
        )
        
        # Mask private keys
        masked = re.sub(
            r'-----BEGIN (?:RSA |EC )?PRIVATE KEY-----[^-]+-----END (?:RSA |EC )?PRIVATE KEY-----',
            f'-----BEGIN PRIVATE KEY-----{mask_char * 50}-----END PRIVATE KEY-----',
            masked,
            flags=re.DOTALL
        )
        
        return masked
    
    def sanitize_for_logging(self, data: Any) -> Any:
        """
        Sanitize data for safe logging.
        
        Args:
            data: Data to sanitize
            
        Returns:
            Sanitized data safe for logs
        """
        # Classify first
        classification = self.classify_data(data)
        
        # If restricted data found, mask it
        if classification['classification'] in [DataClassification.RESTRICTED, DataClassification.CONFIDENTIAL]:
            return self.mask_sensitive_data(data)
        
        # If internal, hash sensitive fields
        if classification['classification'] == DataClassification.INTERNAL:
            return self._hash_sensitive_fields(data)
        
        # Public data is safe
        return data
    
    def _hash_sensitive_fields(self, data: Any) -> Any:
        """Hash sensitive fields instead of masking (for internal use)."""
        if isinstance(data, dict):
            result = {}
            for k, v in data.items():
                # Hash wallet addresses and transaction IDs
                if 'wallet' in k.lower() or 'address' in k.lower() or 'transaction' in k.lower():
                    if isinstance(v, str):
                        result[k] = self._hash_value(v)
                    else:
                        result[k] = v
                else:
                    result[k] = self._hash_sensitive_fields(v)
            return result
        elif isinstance(data, list):
            return [self._hash_sensitive_fields(item) for item in data]
        else:
            return data
    
    def _hash_value(self, value: str) -> str:
        """Generate hash of value for logging."""
        return hashlib.sha256(value.encode()).hexdigest()[:16]
    
    def _to_string(self, data: Any) -> str:
        """Convert data to string for pattern matching."""
        if isinstance(data, str):
            return data
        elif isinstance(data, dict):
            import json
            return json.dumps(data, default=str)
        else:
            return str(data)
    
    def _classification_level(self, classification: DataClassification) -> int:
        """Get numeric level for classification comparison."""
        levels = {
            DataClassification.PUBLIC: 0,
            DataClassification.INTERNAL: 1,
            DataClassification.CONFIDENTIAL: 2,
            DataClassification.RESTRICTED: 3,
        }
        return levels.get(classification, 0)


# Singleton instance
_data_classifier = None

def get_data_classifier() -> DataClassifier:
    """Get singleton data classifier instance."""
    global _data_classifier
    if _data_classifier is None:
        _data_classifier = DataClassifier()
    return _data_classifier


if __name__ == "__main__":
    # Example usage
    classifier = get_data_classifier()
    
    # Test data
    test_data = {
        'wallet_address': '0x1234567890abcdef1234567890abcdef12345678',
        'email': 'user@example.com',
        'transaction_id': 'txn_abc123',
        'safe_field': 'public data'
    }
    
    # Classify
    classification = classifier.classify_data(test_data)
    print(f"Classification: {classification}")
    
    # Sanitize for logging
    sanitized = classifier.sanitize_for_logging(test_data)
    print(f"Sanitized: {sanitized}")

