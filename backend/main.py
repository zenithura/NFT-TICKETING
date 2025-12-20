"""Main FastAPI application."""
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import os
import logging
from dotenv import load_dotenv

from routers import auth, events, tickets, marketplace, admin, admin_auth, wallet, ml_services, ml_services_v2, chatbot
from security_middleware import security_middleware
from middleware_metrics import MetricsMiddleware
from web_requests_middleware import WebRequestsMiddleware

from contextlib import asynccontextmanager
from web3_client import load_contracts

# Monitoring imports
from sentry_config import init_sentry
from monitoring import get_metrics

# Data Science Integration
try:
    from data_science.core import data_logger, kpi_calculator, ab_test_manager
    from data_science.data_loader import DataLoader
    from database import get_supabase_admin
    
    # Import all models
    from data_science.models.risk_score import risk_model
    from data_science.models.bot_detection import bot_model
    from data_science.models.fair_price import fair_price_model
    from data_science.models.scalping_detection import scalping_model
    from data_science.models.wash_trading import wash_trading_model
    from data_science.models.recommender import recommender_model
    from data_science.models.segmentation import segmentation_model
    from data_science.models.market_trend import market_trend_model
    from data_science.models.decision_rule import decision_rule_model
    
    DATA_SCIENCE_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Data science modules not fully available: {e}")
    DATA_SCIENCE_AVAILABLE = False

load_dotenv()

logger = logging.getLogger(__name__)

# Initialize Sentry
init_sentry()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load smart contracts
    load_contracts()
    
    # Initialize data_loader for all ML models
    if DATA_SCIENCE_AVAILABLE:
        try:
            db = get_supabase_admin()
            data_loader = DataLoader(db)
            
            # Set data_loader for all models
            risk_model.data_loader = data_loader
            bot_model.data_loader = data_loader
            fair_price_model.data_loader = data_loader
            scalping_model.data_loader = data_loader
            wash_trading_model.data_loader = data_loader
            recommender_model.data_loader = data_loader
            segmentation_model.data_loader = data_loader
            market_trend_model.data_loader = data_loader
            decision_rule_model.data_loader = data_loader
            
            print("✓ Data loader initialized for all ML models")
        except Exception as e:
            print(f"Warning: Could not initialize data loader: {e}")
    
    yield

# Create FastAPI app
app = FastAPI(
    title="NFT Ticketing Platform API",
    description="Backend API for NFT-based event ticketing platform",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
# Default origins include localhost and common local network IPs
# Admin panel runs on port 4201 with non-guessable path
default_origins = "http://localhost:5173,http://localhost:3000,http://localhost:4201,http://10.230.33.197:3000"
CORS_ORIGINS = os.getenv("CORS_ORIGINS", default_origins).split(",")
# Strip whitespace from origins
CORS_ORIGINS = [origin.strip() for origin in CORS_ORIGINS]
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add response compression (gzip) - reduces payload size by 70-90%
app.add_middleware(GZipMiddleware, minimum_size=1000)

# Add metrics middleware for Prometheus
app.add_middleware(MetricsMiddleware)

# Add web requests logging middleware (must be before security middleware)
app.add_middleware(WebRequestsMiddleware, exclude_paths=['/health', '/metrics', '/docs', '/redoc', '/openapi.json'])

# Add security middleware (must be before routers)
app.middleware("http")(security_middleware)

# Include routers with /api prefix
app.include_router(auth.router, prefix="/api")
app.include_router(events.router, prefix="/api")
app.include_router(tickets.router, prefix="/api")
app.include_router(marketplace.router, prefix="/api")
app.include_router(wallet.router, prefix="/api")  # Wallet connection routes
app.include_router(admin_auth.router, prefix="/api")  # Admin auth routes
app.include_router(admin.router, prefix="/api")  # Admin dashboard routes (protected)
app.include_router(ml_services.router, prefix="/api")  # ML services routes (legacy)
app.include_router(ml_services_v2.router, prefix="/api")  # ML services routes (new - with DB integration)
app.include_router(chatbot.router, prefix="/api")  # Chatbot routes


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "NFT Ticketing Platform API",
        "version": "1.0.0",
        "docs": "/docs",
        "redoc": "/redoc"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}



# Mount Monitoring Dashboard
try:
    from a2wsgi import WSGIMiddleware
    from monitoring.dashboard import app as dashboard_app
    app.mount("/dashboard", WSGIMiddleware(dashboard_app.server))
except Exception as e:
    logger.warning(f"Monitoring dashboard not mounted: {e}")

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(content=get_metrics(), media_type="text/plain")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
