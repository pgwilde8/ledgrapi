"""
LedgrAPI API Schemas
Pydantic models for API requests and responses
"""

from pydantic import BaseModel, HttpUrl
from typing import Optional, Dict, Any, List
from datetime import datetime

class APICreate(BaseModel):
    """Schema for creating a new API"""
    name: str
    description: Optional[str] = None
    base_url: HttpUrl
    auth_type: str = "none"  # none, api_key, oauth, wallet
    auth_config: Optional[Dict[str, Any]] = None
    pricing_model: str = "per_call"  # per_call, subscription, freemium
    price_per_call: float = 0.0  # Price in USD cents
    free_calls_per_month: int = 0
    tags: Optional[List[str]] = None

class APIResponse(BaseModel):
    """Schema for API response"""
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
    is_active: bool
    is_public: bool
    status: str
    tags: Optional[List[str]]
    total_endpoints: int
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class APICallRequest(BaseModel):
    """Schema for API call request"""
    endpoint: str
    method: str = "GET"
    headers: Optional[Dict[str, str]] = None
    params: Optional[Dict[str, Any]] = None
    data: Optional[Dict[str, Any]] = None

class APICallResponse(BaseModel):
    """Schema for API call response"""
    request_id: str
    status_code: int
    response_time_ms: int
    cost: float
    was_free: bool
    data: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None

class APIListResponse(BaseModel):
    """Schema for API list response"""
    apis: List[APIResponse]
    total: int
    skip: int = 0
    limit: int = 100

class APIUsageResponse(BaseModel):
    """Schema for API usage response"""
    api_id: int
    calls_this_month: int
    calls_total: int
    cost_this_month: float
    cost_total: float
    month: Optional[str] = None
    year: Optional[int] = None
    
    class Config:
        from_attributes = True 