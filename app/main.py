"""
LedgrAPI - Main FastAPI Application
Quant-Powered Web3 API Monetization Platform
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import time
import logging

from app.core.config import settings
from app.core.logging import setup_logging
from app.api.v1.api import api_router
from app.core.middleware import RequestLoggingMiddleware

# Setup logging
setup_logging()
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="LedgrAPI",
    description="Quant-Powered Web3 API Monetization Platform",
    version="1.0.0",
    docs_url="/api/docs" if settings.DEBUG else None,
    redoc_url="/api/redoc" if settings.DEBUG else None,
    openapi_url="/api/openapi.json" if settings.DEBUG else None,
)

# Security middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.ALLOWED_HOSTS
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom middleware
app.add_middleware(RequestLoggingMiddleware)

# Mount static files
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Templates
templates = Jinja2Templates(directory="app/templates")

# Include API routes
app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root(request: Request):
    """Landing page for LedgrAPI"""
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "title": "LedgrAPI - Web3 API Monetization"}
    )

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "LedgrAPI",
        "version": "1.0.0",
        "timestamp": time.time()
    }

@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info("🚀 Starting LedgrAPI - Quant-Powered Web3 API Monetization Platform")
    logger.info(f"Environment: {settings.ENVIRONMENT}")
    logger.info(f"Debug mode: {settings.DEBUG}")

@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logger.info("🛑 Shutting down LedgrAPI")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=9176,
        reload=settings.DEBUG,
        log_level="info"
    ) 