"""New ML Services Router - Direct integration with data science models."""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional, Dict, Any
from pydantic import BaseModel
from supabase import Client
from database import get_supabase_admin

# Import models
try:
    from data_science.models.risk_score import risk_model
    from data_science.models.bot_detection import bot_model
    from data_science.models.fair_price import fair_price_model
    from data_science.models.scalping_detection import scalping_model
    from data_science.models.wash_trading import wash_trading_model
    from data_science.models.recommender import recommender_model
    from data_science.models.segmentation import segmentation_model
    from data_science.models.market_trend import market_trend_model
    from data_science.models.decision_rule import decision_rule_model
    MODELS_AVAILABLE = True
except ImportError as e:
    print(f"Warning: ML models not available: {e}")
    MODELS_AVAILABLE = False

router = APIRouter(prefix="/ml/v2", tags=["ML Services V2"])


# Request/Response Models
class RiskScoreRequest(BaseModel):
    amount: float
    user_tx_count: Optional[int] = None
    user_id: Optional[str] = None
    transaction_id: Optional[str] = None


class BotDetectionRequest(BaseModel):
    request_freq: float
    ua_score: float = 1.0
    ip_reputation: float = 1.0


class FairPriceRequest(BaseModel):
    original_price: float
    popularity: int = 5
    days_left: int = 10


class ScalpingDetectionRequest(BaseModel):
    purchase_count: int
    resale_velocity: float
    holding_time: float


class WashTradingRequest(BaseModel):
    buyer_id: str
    seller_id: str
    nft_id: str
    transaction_id: Optional[str] = None


class RecommenderRequest(BaseModel):
    preferred_category: str = "concert"


class SegmentationRequest(BaseModel):
    avg_tx_value: float
    frequency: int


class MarketTrendRequest(BaseModel):
    day_index: int


class DecisionRuleRequest(BaseModel):
    value: float


# Endpoints
@router.get("/health")
async def health_check():
    """Check ML services health."""
    return {
        "status": "healthy" if MODELS_AVAILABLE else "degraded",
        "models_available": MODELS_AVAILABLE,
        "models": {
            "risk_score": risk_model.model is not None if MODELS_AVAILABLE else False,
            "bot_detection": bot_model.model is not None if MODELS_AVAILABLE else False,
            "fair_price": fair_price_model.model is not None if MODELS_AVAILABLE else False,
            "scalping": scalping_model.model is not None if MODELS_AVAILABLE else False,
        }
    }


@router.post("/predict/risk")
async def predict_risk(request: RiskScoreRequest):
    """
    Predict risk score for a transaction.
    
    Can provide either:
    - Direct features (amount, user_tx_count)
    - User ID (will fetch stats from DB)
    - Transaction ID (will fetch from DB)
    """
    if not MODELS_AVAILABLE:
        raise HTTPException(status_code=503, detail="ML models not available")
    
    try:
        inputs = request.dict(exclude_none=True)
        risk_score = risk_model.predict(inputs)
        
        return {
            "risk_score": risk_score,
            "risk_level": "high" if risk_score > 0.7 else "medium" if risk_score > 0.4 else "low",
            "model": "risk_score_v1"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


@router.post("/predict/bot")
async def predict_bot(request: BotDetectionRequest):
    """Detect if behavior is bot-like."""
    if not MODELS_AVAILABLE:
        raise HTTPException(status_code=503, detail="ML models not available")
    
    try:
        result = bot_model.predict(request.dict())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


@router.post("/predict/fair-price")
async def predict_fair_price(request: FairPriceRequest):
    """Predict fair market price for a ticket."""
    if not MODELS_AVAILABLE:
        raise HTTPException(status_code=503, detail="ML models not available")
    
    try:
        result = fair_price_model.predict(request.dict())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


@router.post("/predict/scalping")
async def predict_scalping(request: ScalpingDetectionRequest):
    """Detect if user is scalping tickets."""
    if not MODELS_AVAILABLE:
        raise HTTPException(status_code=503, detail="ML models not available")
    
    try:
        result = scalping_model.predict(request.dict())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


@router.post("/predict/wash-trading")
async def predict_wash_trading(request: WashTradingRequest):
    """Detect wash trading patterns."""
    if not MODELS_AVAILABLE:
        raise HTTPException(status_code=503, detail="ML models not available")
    
    try:
        result = wash_trading_model.predict(request.dict())
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


@router.post("/recommend")
async def recommend_events(request: RecommenderRequest):
    """Get event recommendations based on user preferences."""
    if not MODELS_AVAILABLE:
        raise HTTPException(status_code=503, detail="ML models not available")
    
    try:
        recommendations = recommender_model.predict(request.dict())
        return {"recommendations": recommendations}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


@router.post("/segment")
async def segment_user(request: SegmentationRequest):
    """Segment user into behavioral cluster."""
    if not MODELS_AVAILABLE:
        raise HTTPException(status_code=503, detail="ML models not available")
    
    try:
        segment = segmentation_model.predict(request.dict())
        segment_names = {0: "low_value", 1: "high_value", 2: "high_frequency"}
        
        return {
            "segment_id": segment,
            "segment_name": segment_names.get(segment, "unknown")
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


@router.post("/predict/trend")
async def predict_market_trend(request: MarketTrendRequest):
    """Predict market trend for future day."""
    if not MODELS_AVAILABLE:
        raise HTTPException(status_code=503, detail="ML models not available")
    
    try:
        prediction = market_trend_model.predict(request.dict())
        return {"predicted_value": prediction, "day_index": request.day_index}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


@router.post("/detect/anomaly")
async def detect_anomaly(request: DecisionRuleRequest):
    """Detect anomalies in real-time using decision rules."""
    if not MODELS_AVAILABLE:
        raise HTTPException(status_code=503, detail="ML models not available")
    
    try:
        decision = decision_rule_model.predict(request.dict())
        return {
            "decision": decision,
            "is_anomaly": decision == "ANOMALY",
            "value": request.value
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction error: {str(e)}")


@router.get("/models/stats")
async def get_model_stats(db: Client = Depends(get_supabase_admin)):
    """Get statistics about model predictions."""
    try:
        # Get prediction counts by model
        predictions = db.table("model_predictions") \
            .select("model_name", count="exact") \
            .execute()
        
        # Get latest metrics
        metrics = db.table("model_metrics") \
            .select("*") \
            .order("evaluation_date", desc=True) \
            .limit(10) \
            .execute()
        
        return {
            "total_predictions": predictions.count if predictions else 0,
            "recent_metrics": metrics.data if metrics else []
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats error: {str(e)}")
