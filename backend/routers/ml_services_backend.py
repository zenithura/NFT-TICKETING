"""
ML Services Router - Backend Integration with Machine Learning/ Folder
Uses Supabase feature engineering and DuckDB storage.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, Dict, Any
from supabase import Client
from database import get_supabase_admin
import sys
from pathlib import Path

# Add Machine Learning folder to path
ml_path = Path(__file__).parent.parent.parent / "Machine Learning"
if ml_path.exists():
    sys.path.insert(0, str(ml_path.parent))

router = APIRouter(prefix="/ml", tags=["ML Services"])

# Lazy import ML integration
_ml_integration = None


def get_ml_integration_backend():
    """Get or create ML integration backend instance."""
    global _ml_integration
    if _ml_integration is None:
        try:
            from integration.ml_integration_backend import get_ml_integration_backend
            # Pass Supabase client from backend
            _ml_integration = get_ml_integration_backend()
        except Exception as e:
            print(f"Warning: Could not load ML integration backend: {e}")
            _ml_integration = None
    return _ml_integration


@router.get("/health")
async def ml_health_check():
    """Check ML services health."""
    integration = get_ml_integration_backend()
    
    return {
        "status": "healthy" if integration else "unavailable",
        "integration_backend": integration is not None,
        "data_source": "supabase",
        "storage": "duckdb"
    }


@router.post("/predict/fraud")
async def predict_fraud(
    transaction_id: str,
    wallet_address: str,
    event_id: Optional[int] = None,
    price_paid: float = 0.0,
    db: Client = Depends(get_supabase_admin)
):
    """
    Predict fraud risk for a transaction using ML models.
    
    Data Flow:
    - Features from Supabase PostgreSQL
    - ML model inference
    - Results stored in DuckDB
    - Returns to backend for decision logic
    """
    integration = get_ml_integration_backend()
    
    if not integration:
        raise HTTPException(
            status_code=503,
            detail="ML services not available. Ensure Machine Learning components are properly configured."
        )
    
    try:
        # Pass Supabase client to integration
        # Note: Integration already has Supabase client from initialization
        result = integration.process_transaction(
            transaction_id=transaction_id,
            wallet_address=wallet_address,
            event_id=event_id,
            price_paid=price_paid
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ML prediction error: {str(e)}")


@router.post("/analyze/risk")
async def analyze_risk(
    wallet_address: str,
    event_id: Optional[int] = None,
    transaction_data: Optional[Dict[str, Any]] = None
):
    """Analyze risk for a wallet/transaction using ML ensemble."""
    integration = get_ml_integration_backend()
    
    if not integration:
        raise HTTPException(
            status_code=503,
            detail="ML services not available"
        )
    
    try:
        # Note: This endpoint expects features to be computed from Supabase
        # transaction_data is optional metadata, not feature source
        result = integration.process_transaction(
            transaction_id=transaction_data.get('transaction_id', 'unknown') if transaction_data else 'unknown',
            wallet_address=wallet_address,
            event_id=event_id,
            price_paid=transaction_data.get('price_paid', 0.0) if transaction_data else 0.0
        )
        
        return {
            "wallet_address": wallet_address,
            "event_id": event_id,
            "analysis": result.get('model_outputs', {}),
            "data_source": "supabase",
            "results_stored_in": "duckdb"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Risk analysis error: {str(e)}")


@router.get("/analytics")
async def get_ml_analytics(days: int = 7):
    """Get ML analytics from DuckDB."""
    integration = get_ml_integration_backend()
    
    if not integration:
        raise HTTPException(
            status_code=503,
            detail="ML services not available"
        )
    
    try:
        analytics = integration.get_analytics(days=days)
        return {
            "analytics": analytics,
            "data_source": "duckdb",
            "period_days": days
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching analytics: {str(e)}")

