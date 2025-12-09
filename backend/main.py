"""Main FastAPI application."""
from fastapi import FastAPI, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
import os
from dotenv import load_dotenv

from routers import auth, events, tickets, marketplace, admin, admin_auth, wallet
from security_middleware import security_middleware
from middleware_metrics import MetricsMiddleware
from web_requests_middleware import WebRequestsMiddleware

from contextlib import asynccontextmanager
from web3_client import load_contracts

# Monitoring imports
from sentry_config import init_sentry
from monitoring import get_metrics

load_dotenv()

# Initialize Sentry
init_sentry()

@asynccontextmanager
async def lifespan(app: FastAPI):
    load_contracts()
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


@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(content=get_metrics(), media_type="text/plain")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
