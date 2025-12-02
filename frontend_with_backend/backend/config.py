# File header: Centralized configuration management for backend services.
# Handles environment variable loading, validation, and provides type-safe configuration access.

"""
Configuration management module for NFT Ticketing Platform backend.
Provides centralized access to environment variables with validation.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

# Purpose: Load environment variables from .env file in backend directory.
# Side effects: Reads .env file, sets environment variables.
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Purpose: Configuration class for type-safe access to environment variables.
# Provides validation and default values for all configuration settings.
class Config:
    """Application configuration with environment variable validation."""
    
    # Purpose: Database configuration from Supabase.
    # Side effects: Reads SUPABASE_URL and SUPABASE_KEY from environment.
    @staticmethod
    def get_supabase_config() -> tuple[str, str]:
        """Get Supabase connection credentials."""
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_KEY')
        
        if not url or not key:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_KEY must be set in environment variables"
            )
        
        return url, key
    
    # Purpose: Blockchain configuration for Web3 connections.
    # Returns: Dictionary with blockchain settings.
    # Side effects: Reads blockchain-related environment variables.
    @staticmethod
    def get_blockchain_config() -> dict:
        """Get blockchain service configuration."""
        return {
            'rpc_url': os.getenv('BLOCKCHAIN_RPC_URL', 'http://127.0.0.1:8545'),
            'contract_address': os.getenv('SMART_CONTRACT_ADDRESS'),
            'private_key': os.getenv('SERVER_WALLET_PRIVATE_KEY'),
            'wallet_address': os.getenv('SERVER_WALLET_ADDRESS'),
        }
    
    # Purpose: Application settings (debug mode, logging level).
    # Returns: Dictionary with app configuration.
    # Side effects: Reads application environment variables.
    @staticmethod
    def get_app_config() -> dict:
        """Get application configuration."""
        debug = os.getenv('DEBUG', 'false').lower() == 'true'
        environment = os.getenv('ENVIRONMENT', 'development')
        
        return {
            'debug': debug,
            'environment': environment,
            'log_level': os.getenv('LOG_LEVEL', 'INFO'),
            'api_version': os.getenv('API_VERSION', '2.0.0'),
        }
    
    # Purpose: CORS configuration for API endpoints.
    # Returns: List of allowed origins.
    # Side effects: Reads CORS_ALLOWED_ORIGINS from environment.
    @staticmethod
    def get_cors_config() -> list[str]:
        """Get CORS allowed origins."""
        origins_env = os.getenv('CORS_ALLOWED_ORIGINS', '')
        if origins_env:
            return [origin.strip() for origin in origins_env.split(',')]
        
        # Default development origins
        return [
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5000",
            "http://127.0.0.1:5000",
        ]
    
    # Purpose: Security configuration (rate limiting, session timeout).
    # Returns: Dictionary with security settings.
    # Side effects: Reads security-related environment variables.
    @staticmethod
    def get_security_config() -> dict:
        """Get security configuration."""
        return {
            'rate_limit_per_minute': int(os.getenv('RATE_LIMIT_PER_MINUTE', '100')),
            'session_timeout_seconds': int(os.getenv('SESSION_TIMEOUT_SECONDS', '3600')),
            'max_request_size_mb': int(os.getenv('MAX_REQUEST_SIZE_MB', '10')),
        }
    
    # Purpose: JWT configuration for authentication tokens.
    # Returns: Dictionary with JWT settings.
    # Side effects: Reads JWT-related environment variables.
    @staticmethod
    def get_jwt_config() -> dict:
        """Get JWT configuration."""
        return {
            'secret': os.getenv('JWT_SECRET'),
            'algorithm': 'HS256',
            'access_token_expire_minutes': int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '15')),
            'refresh_token_expire_days': int(os.getenv('REFRESH_TOKEN_EXPIRE_DAYS', '7')),
            'max_login_attempts': int(os.getenv('MAX_LOGIN_ATTEMPTS', '5')),
            'lockout_duration_minutes': int(os.getenv('LOCKOUT_DURATION_MINUTES', '30')),
        }
    
    # Purpose: Validate that all required configuration is present.
    # Side effects: Raises ValueError if required config is missing.
    @staticmethod
    def validate() -> None:
        """Validate that all required configuration is present."""
        try:
            Config.get_supabase_config()
            logger.info("Configuration validation passed")
        except ValueError as e:
            logger.error(f"Configuration validation failed: {e}")
            raise

# Purpose: Initialize and validate configuration on module import.
# Side effects: Validates configuration, logs status.
try:
    Config.validate()
except ValueError:
    logger.warning("Configuration validation failed - some features may not work")

