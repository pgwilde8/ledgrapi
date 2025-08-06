"""
LedgrAPI Public Schemas
Pydantic models for public endpoints
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class PublicAPIResponse(BaseModel):
    """Schema for public API response"""
    id: int
    uuid: str
    name: str
    description: Optional[str]
    version: str
    base_url: str
    auth_type: str
    pricing_model: str
    price_per_call: float
    free_calls_per_month: int
    tags: Optional[List[str]]
    total_endpoints: int
    created_at: datetime
    
    class Config:
        from_attributes = True

class PricingTierResponse(BaseModel):
    """Schema for public pricing tier response"""
    id: int
    name: str
    display_name: str
    description: Optional[str]
    price_monthly: float
    price_yearly: float
    api_limit: int
    calls_per_month: int
    rate_limit_per_minute: int
    features: Optional[List[str]]
    supported_networks: Optional[List[str]]
    quant_integration: bool
    
    class Config:
        from_attributes = True

class PlatformStatsResponse(BaseModel):
    """Schema for platform statistics response"""
    total_apis: int
    public_apis: int
    supported_networks: List[str]
    platform_status: str 