"""
ML Services Router - DEPRECATED
This router is deprecated. Please use ml_services_v2.py instead.

This file is kept for backward compatibility but redirects to the new implementation.
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, Dict, Any
from supabase import Client
from database import get_supabase_admin
import warnings

router = APIRouter(prefix="/ml", tags=["ML Services (Deprecated)"])

# Import models from consolidated data_science module
try:
    from data_science.models.risk_score import risk_model
    from data_science.models.bot_detection import bot_model
    from data_science.core import kpi_calculator
    MODELS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: ML models not available: {e}")
    MODELS_AVAILABLE = False


def _deprecation_warning():
    """Show deprecation warning."""
    warnings.warn(
        "This endpoint is deprecated. Please use /api/ml/v2/ endpoints instead.",
        DeprecationWarning,
        stacklevel=3
    )


@router.get("/health")
async def ml_health_check():
    """Check ML services health (DEPRECATED - use /api/ml/v2/health)."""
    _deprecation_warning()
    
    return {
        "status": "healthy" if MODELS_AVAILABLE else "degraded",
        "deprecated": True,
        "message": "This endpoint is deprecated. Use /api/ml/v2/health instead.",
        "models_available": MODELS_AVAILABLE
    }


@router.post("/predict/fraud")
async def predict_fraud(
    transaction_id: str,
    wallet_address: str,
    event_id: Optional[int] = None,
    price_paid: float = 0.0,
    db: Client = Depends(get_supabase_admin)
):
    """Predict fraud risk (DEPRECATED - use /api/ml/v2/predict/risk)."""
    _deprecation_warning()
    
    if not MODELS_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="ML services not available. Use /api/ml/v2/predict/risk instead."
        )
    
    try:
        # Use consolidated risk model
        risk_score = risk_model.predict({
            "transaction_id": transaction_id,
            "user_id": wallet_address,
            "amount": price_paid
        })
        
        return {
            "deprecated": True,
            "message": "Use /api/ml/v2/predict/risk instead",
            "transaction_id": transaction_id,
            "risk_score": risk_score,
            "risk_level": "high" if risk_score > 0.7 else "medium" if risk_score > 0.4 else "low"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"ML prediction error: {str(e)}")


@router.post("/analyze/risk")
async def analyze_risk(
    wallet_address: str,
    event_id: Optional[int] = None,
    transaction_data: Optional[Dict[str, Any]] = None
):
    """Analyze risk (DEPRECATED - use /api/ml/v2/predict/risk)."""
    _deprecation_warning()
    
    if not MODELS_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="ML models not available. Use /api/ml/v2/predict/risk instead."
        )
    
    try:
        # Use consolidated risk model
        features = transaction_data or {}
        risk_score = risk_model.predict({
            "user_id": wallet_address,
            "amount": features.get("amount", 0),
            "user_tx_count": features.get("user_tx_count", 0)
        })
        
        return {
            "deprecated": True,
            "message": "Use /api/ml/v2/predict/risk instead",
            "wallet_address": wallet_address,
            "event_id": event_id,
            "risk_score": risk_score
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Risk analysis error: {str(e)}")


@router.get("/metrics/kpis")
async def get_ml_kpis():
    """Get ML-related KPIs (DEPRECATED - use data_science.core.kpi_calculator)."""
    _deprecation_warning()
    
    if not MODELS_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="ML services not available"
        )
    
    try:
        # Use consolidated KPI calculator
        conversion_rate = kpi_calculator.get_conversion_rate()
        avg_time_to_finality = kpi_calculator.get_avg_time_to_finality()
        
        return {
            "deprecated": True,
            "message": "Use data_science.core.kpi_calculator directly",
            "conversion_rate": conversion_rate,
            "avg_time_to_finality": avg_time_to_finality
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching KPIs: {str(e)}")

