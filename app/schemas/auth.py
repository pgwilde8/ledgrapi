"""
LedgrAPI Authentication Schemas
Pydantic models for authentication requests and responses
"""

from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

class UserCreate(BaseModel):
    """Schema for user registration"""
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    password: str
    wallet_address: Optional[str] = None
    wallet_network: Optional[str] = None

class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    """Schema for user response"""
    id: int
    uuid: str
    email: str
    username: str
    full_name: Optional[str]
    wallet_address: Optional[str]
    wallet_network: Optional[str]
    is_active: bool
    is_verified: bool
    current_tier: str
    subscription_status: str
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    """Schema for token response"""
    access_token: str
    token_type: str
    user: UserResponse

class WalletAuthRequest(BaseModel):
    """Schema for wallet authentication"""
    address: str
    signature: str
    message: str
    network: Optional[str] = "ethereum" 