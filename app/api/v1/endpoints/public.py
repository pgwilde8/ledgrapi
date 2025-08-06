"""
LedgrAPI Public Endpoints
Endpoints that don't require authentication
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import logging
import json
from datetime import datetime

from app.db.session import get_db
from app.db.models import API, SubscriptionTier
from app.schemas.public import PublicAPIResponse, PricingTierResponse

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/apis", response_model=List[PublicAPIResponse])
async def list_public_apis(
    skip: int = 0,
    limit: int = 50,
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    List public APIs (no authentication required)
    """
    query = select(API).where(
        API.is_active == True,
        API.status == "published",
        API.is_public == True
    )
    
    if category:
        query = query.where(API.tags.contains([category]))
    
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    apis = result.scalars().all()
    
    return [PublicAPIResponse.from_orm(api) for api in apis]

@router.get("/pricing", response_model=List[PricingTierResponse])
async def get_pricing_tiers(
    db: AsyncSession = Depends(get_db)
):
    """
    Get public pricing information
    """
    query = select(SubscriptionTier).where(
        SubscriptionTier.is_active == True,
        SubscriptionTier.is_public == True
    )
    
    result = await db.execute(query)
    tiers = result.scalars().all()
    
    return [PricingTierResponse.from_orm(tier) for tier in tiers]

@router.post("/waitlist")
async def join_waitlist(
    request: Request,
    db: AsyncSession = Depends(get_db)
):
    """
    Join the LedgrAPI waitlist
    """
    try:
        # Parse form data
        form_data = await request.form()
        email = form_data.get("email")
        
        if not email:
            raise HTTPException(status_code=400, detail="Email is required")
        
        # Log the email (in production, you'd save to database)
        logger.info(f"Waitlist signup: {email}")
        
        # TODO: Save to database when user model is ready
        # For now, just log it
        
        return {
            "success": True,
            "message": "Thank you for joining our waitlist! We'll notify you when LedgrAPI launches.",
            "email": email
        }
        
    except Exception as e:
        logger.error(f"Waitlist signup error: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to join waitlist")

@router.get("/stats")
async def get_platform_stats(
    db: AsyncSession = Depends(get_db)
):
    """
    Get public platform statistics
    """
    # Count total APIs
    api_query = select(API).where(API.is_active == True, API.status == "published")
    result = await db.execute(api_query)
    total_apis = len(result.scalars().all())
    
    # Count public APIs
    public_api_query = select(API).where(
        API.is_active == True,
        API.status == "published",
        API.is_public == True
    )
    result = await db.execute(public_api_query)
    public_apis = len(result.scalars().all())
    
    # TODO: Add more statistics like total users, total API calls, etc.
    
    return {
        "total_apis": total_apis,
        "public_apis": public_apis,
        "supported_networks": ["ethereum", "polygon", "xdc", "xrpl", "quant"],
        "platform_status": "coming_soon"
    }

@router.get("/docs")
async def get_api_documentation():
    """
    Get API documentation links
    """
    return {
        "swagger_ui": "/api/docs",
        "redoc": "/api/redoc",
        "openapi_spec": "/api/openapi.json",
        "github": "https://github.com/ledgrapi/ledgrapi",
        "website": "https://ledgrapi.com"
    } 