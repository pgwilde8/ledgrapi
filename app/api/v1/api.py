"""
LedgrAPI v1 API Router
Main router that includes all API endpoints
"""

from fastapi import APIRouter
from app.api.v1.endpoints import auth, apis, billing, quant, public

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(apis.router, prefix="/apis", tags=["APIs"])
api_router.include_router(billing.router, prefix="/billing", tags=["Billing"])
api_router.include_router(quant.router, prefix="/quant", tags=["Quant Integration"])
api_router.include_router(public.router, prefix="/public", tags=["Public"]) 