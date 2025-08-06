"""
LedgrAPI Billing Schemas
Pydantic models for billing and subscription requests and responses
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class SubscriptionCreate(BaseModel):
    """Schema for creating a subscription"""
    tier_id: int
    billing_cycle: str = "monthly"  # monthly, yearly

class SubscriptionResponse(BaseModel):
    """Schema for subscription response"""
    id: int
    uuid: str
    user_id: int
    tier_name: str
    status: str
    billing_cycle: str
    amount: float
    currency: str
    next_billing_date: Optional[datetime]
    created_at: datetime
    updated_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class PaymentResponse(BaseModel):
    """Schema for payment response"""
    id: int
    uuid: str
    user_id: int
    amount: float
    currency: str
    type: str
    status: str
    blockchain_tx_hash: Optional[str]
    blockchain_network: Optional[str]
    usdc_amount: Optional[float]
    qnt_amount: Optional[float]
    created_at: datetime
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True

class BillingUsageResponse(BaseModel):
    """Schema for billing usage response"""
    tier: str
    calls_used: int
    calls_limit: int
    cost_this_month: float
    days_until_reset: int

class PaymentMethodResponse(BaseModel):
    """Schema for payment method response"""
    id: int
    uuid: str
    type: str
    name: Optional[str]
    is_default: bool
    wallet_address: Optional[str]
    wallet_network: Optional[str]
    card_brand: Optional[str]
    card_last4: Optional[str]
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True 