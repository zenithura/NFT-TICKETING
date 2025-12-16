"""
ML Services Router - Legacy Router (Deprecated)

Note: This router is deprecated. Use ml_services_backend.py instead.
This file is kept for backward compatibility but will be removed in future versions.
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, Dict, Any
from supabase import Client
from database import get_supabase_admin
import sys
from pathlib import Path

# Try to use ML folder integration layer
ml_path = Path(__file__).parent.parent.parent / "Machine Learning"
if ml_path.exists():
    sys.path.insert(0, str(ml_path.parent))

router = APIRouter(prefix="/ml", tags=["ML Services (Legacy)"])

# Lazy import ML components from Machine Learning folder
_ml_integration = None


def get_ml_integration():
    """Get or create ML integration layer from Machine Learning folder."""
    global _ml_integration
    if _ml_integration is None:
        try:
            from integration.ml_integration_backend import get_ml_integration_backend
            _ml_integration = get_ml_integration_backend()
        except Exception as e:
            print(f"Warning: Could not load ML integration: {e}")
            _ml_integration = None
    return _ml_integration


@router.get("/health")
async def ml_health_check():
    """Check ML services health (legacy endpoint)."""
    ml_integration = get_ml_integration()
    
    return {
        "status": "healthy" if ml_integration else "degraded",
        "ml_integration": ml_integration is not None,
        "note": "This is a legacy endpoint. Use /ml_backend/health instead."
    }


@router.post("/predict/fraud")
async def predict_fraud(
    transaction_id: str,
    wallet_address: str,
    event_id: Optional[int] = None,
    price_paid: float = 0.0,
    db: Client = Depends(get_supabase_admin)
):
    """Predict fraud risk for a transaction using ML models (legacy endpoint)."""
    ml_integration = get_ml_integration()
    
    if not ml_integration:
        raise HTTPException(
            status_code=503,
            detail="ML services not available. Ensure Machine Learning components are properly configured."
        )
    
    try:
        result = ml_integration.process_transaction(
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
    """Analyze risk for a wallet/transaction (legacy endpoint)."""
    ml_integration = get_ml_integration()
    
    if not ml_integration:
        raise HTTPException(
            status_code=503,
            detail="ML models not available. Ensure sprint3 models are properly configured."
        )
    
    try:
        # Convert transaction data to features format
        features = transaction_data or {}
        features.setdefault("wallet_address", wallet_address)
        
        event_features = {"event_id": event_id} if event_id else {}
        
        result = ensemble.predict_all(
            features=features,
            event_features=event_features
        )
        
        return {
            "wallet_address": wallet_address,
            "event_id": event_id,
            "analysis": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Risk analysis error: {str(e)}")


@router.get("/metrics/kpis")
async def get_ml_kpis():
    """Get ML-related KPIs."""
    integration = get_integration_layer()
    
    if not integration:
        raise HTTPException(
            status_code=503,
            detail="ML services not available"
        )
    
    try:
        metrics = integration.get_all_metrics()
        return metrics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching KPIs: {str(e)}")

