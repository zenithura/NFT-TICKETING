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


def get_ml_integration_backend(db_client=None):
    """Get or create ML integration backend instance."""
    global _ml_integration
    if _ml_integration is None:
        try:
            from integration.ml_integration_backend import get_ml_integration_backend as _get_integration
            # Pass Supabase client to ensure feature engineering uses it
            _ml_integration = _get_integration(db_client=db_client)
        except Exception as e:
            print(f"Warning: Could not load ML integration backend: {e}")
            _ml_integration = None
    else:
        # Update db_client if provided
        if db_client is not None and hasattr(_ml_integration, 'feature_engineer'):
            _ml_integration.feature_engineer._db_client = db_client
    return _ml_integration


@router.get("/health")
async def ml_health_check(db: Client = Depends(get_supabase_admin)):
    """Check ML services health."""
    integration = get_ml_integration_backend(db_client=db)
    
    return {
        "status": "healthy" if integration else "unavailable",
        "integration_backend": integration is not None,
        "data_source": "supabase",
        "storage": "duckdb",
        "models": {
            "fraud_detection": hasattr(integration, 'fraud_model') if integration else False,
            "anomaly_detection": hasattr(integration, 'anomaly_detector') if integration else False,
            "user_clustering": hasattr(integration, 'clustering_model') if integration else False,
            "recommendation_engine": hasattr(integration, 'recommendation_engine') if integration else False,
            "pricing_bandit": hasattr(integration, 'pricing_bandit') if integration else False,
            "risk_scoring_heuristic": hasattr(integration, 'risk_scoring_heuristic') if integration else False
        }
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
        # Ensure integration has the Supabase client
        integration = get_ml_integration_backend(db_client=db)
        if integration and hasattr(integration, 'feature_engineer'):
            integration.feature_engineer._db_client = db
        
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
    transaction_data: Optional[Dict[str, Any]] = None,
    db: Client = Depends(get_supabase_admin)
):
    """Analyze risk for a wallet/transaction using ML ensemble."""
    integration = get_ml_integration_backend(db_client=db)
    
    if not integration:
        raise HTTPException(
            status_code=503,
            detail="ML services not available"
        )
    
    try:
        # Ensure integration has the Supabase client
        if integration and hasattr(integration, 'feature_engineer'):
            integration.feature_engineer._db_client = db
        
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


@router.post("/recommend/events")
async def recommend_events(
    wallet_address: str,
    events: list,
    db: Client = Depends(get_supabase_admin)
):
    """
    Get event recommendations for a user using ML models.
    
    Data Flow:
    - User features from Supabase
    - Clustering and recommendation models
    - Returns sorted list of recommended events
    """
    integration = get_ml_integration_backend()
    
    if not integration:
        raise HTTPException(
            status_code=503,
            detail="ML services not available"
        )
    
    try:
        # Ensure integration has the Supabase client
        if integration and hasattr(integration, 'feature_engineer'):
            integration.feature_engineer._db_client = db
        
        # Get user features from Supabase
        user_features = integration.feature_engineer.compute_features(
            transaction_id=f"recommend_{wallet_address}",
            wallet_address=wallet_address,
            event_id=None
        )
        
        recommendations = integration.recommend_events(
            user_id=wallet_address,
            user_features=user_features,
            events=events
        )
        
        return {
            "wallet_address": wallet_address,
            "recommendations": recommendations,
            "count": len(recommendations),
            "data_source": "supabase"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Recommendation error: {str(e)}")


@router.post("/pricing/dynamic")
async def get_dynamic_pricing(
    base_price: float,
    event_id: int,
    wallet_address: str,
    db: Client = Depends(get_supabase_admin)
):
    """
    Get dynamic pricing for an event using ML bandit.
    
    Data Flow:
    - User and event features from Supabase
    - Pricing bandit selects optimal strategy
    - Returns final price and pricing strategy
    """
    integration = get_ml_integration_backend()
    
    if not integration:
        raise HTTPException(
            status_code=503,
            detail="ML services not available"
        )
    
    try:
        # Ensure integration has the Supabase client
        if integration and hasattr(integration, 'feature_engineer'):
            integration.feature_engineer._db_client = db
        
        # Get user features from Supabase
        user_features = integration.feature_engineer.compute_features(
            transaction_id=f"pricing_{wallet_address}_{event_id}",
            wallet_address=wallet_address,
            event_id=event_id
        )
        
        # Get event features (simplified - would query events table)
        event_features = {
            'event_id': event_id,
            'event_popularity_score': user_features.get('event_popularity_score', 0.5)
        }
        
        pricing_result = integration.get_pricing(
            base_price=base_price,
            event_id=event_id,
            user_features=user_features,
            event_features=event_features
        )
        
        return {
            "event_id": event_id,
            "wallet_address": wallet_address,
            "pricing": pricing_result,
            "data_source": "supabase",
            "results_stored_in": "duckdb"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pricing error: {str(e)}")


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

