"""Main FastAPI application."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

from routers import auth, events, tickets, marketplace, admin, admin_auth, wallet
from security_middleware import security_middleware

from contextlib import asynccontextmanager
from web3_client import load_contracts

load_dotenv()

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
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
