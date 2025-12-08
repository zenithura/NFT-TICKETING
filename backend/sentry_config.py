"""Sentry error tracking configuration."""
import os

def init_sentry():
    """Initialize Sentry for error tracking."""
    sentry_dsn = os.getenv("SENTRY_DSN")
    environment = os.getenv("ENVIRONMENT", "development")
    
    if not sentry_dsn:
        return False
    
    try:
        import sentry_sdk
        from sentry_sdk.integrations.fastapi import FastApiIntegration
        
        integrations = [FastApiIntegration(transaction_style="endpoint")]
        
        # Only add SQLAlchemy integration if it's available
        try:
            from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
            integrations.append(SqlalchemyIntegration())
        except Exception:
            # SQLAlchemy not installed or integration not available
            pass
        
        sentry_sdk.init(
            dsn=sentry_dsn,
            environment=environment,
            integrations=integrations,
            traces_sample_rate=0.1 if environment == "production" else 1.0,
            profiles_sample_rate=0.1 if environment == "production" else 1.0,
            send_default_pii=False,
            attach_stacktrace=True,
            release=os.getenv("VERSION", "1.0.0"),
        )
        return True
    except ImportError:
        # Sentry SDK not installed
        return False
    except Exception:
        # Other errors during initialization
        return False

