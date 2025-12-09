"""ML Services Router - Integration with Sprint3 ML models."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, Dict, Any
from supabase import Client
from database import get_supabase_admin
import sys
import os
from pathlib import Path

# Add sprint3 to path if available
sprint3_path = Path(__file__).parent.parent.parent / "sprint3"
if sprint3_path.exists():
    sys.path.insert(0, str(sprint3_path.parent))

router = APIRouter(prefix="/ml", tags=["ML Services"])

# Lazy import sprint3 components
_integration_layer = None
_model_ensemble = None


def get_integration_layer():
    """Get or create integration layer singleton."""
    global _integration_layer
    if _integration_layer is None:
        try:
            from integration.integration_layer import get_integration_layer as _get_integration
            _integration_layer = _get_integration()
        except Exception as e:
            print(f"Warning: Could not load integration layer: {e}")
            _integration_layer = None
    return _integration_layer


def get_model_ensemble():
    """Get or create model ensemble singleton."""
    global _model_ensemble
    if _model_ensemble is None:
        try:
            from ml_pipeline.models_ensemble import ModelEnsemble
            _model_ensemble = ModelEnsemble()
        except Exception as e:
            print(f"Warning: Could not load model ensemble: {e}")
            _model_ensemble = None
    return _model_ensemble


@router.get("/health")
async def ml_health_check():
    """Check ML services health."""
    integration = get_integration_layer()
    ensemble = get_model_ensemble()
    
    return {
        "status": "healthy" if (integration or ensemble) else "degraded",
        "integration_layer": integration is not None,
        "model_ensemble": ensemble is not None
    }


@router.post("/predict/fraud")
async def predict_fraud(
    transaction_id: str,
    wallet_address: str,
    event_id: Optional[int] = None,
    price_paid: float = 0.0,
    db: Client = Depends(get_supabase_admin)
):
    """Predict fraud risk for a transaction using ML models."""
    integration = get_integration_layer()
    
    if not integration:
        raise HTTPException(
            status_code=503,
            detail="ML services not available. Ensure sprint3 components are properly configured."
        )
    
    try:
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
    ensemble = get_model_ensemble()
    
    if not ensemble:
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

