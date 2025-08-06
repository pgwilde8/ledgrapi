"""
LedgrAPI Subscription Models
Billing tiers and subscription management
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base
import uuid

class SubscriptionTier(Base):
    __tablename__ = "subscription_tiers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)  # free, builder, pro, enterprise
    display_name = Column(String(100), nullable=False)
    description = Column(Text)
    
    # Pricing
    price_monthly = Column(Float, default=0.0)  # Price in USD cents
    price_yearly = Column(Float, default=0.0)  # Price in USD cents (with discount)
    
    # Limits
    api_limit = Column(Integer, default=1)  # -1 for unlimited
    calls_per_month = Column(Integer, default=1000)
    rate_limit_per_minute = Column(Integer, default=60)
    
    # Features
    features = Column(JSON)  # List of features included
    supported_networks = Column(JSON)  # Supported blockchain networks
    quant_integration = Column(Boolean, default=False)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=True)
    
    # Metadata
    meta_data = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    subscriptions = relationship("Subscription", back_populates="tier")
    
    def __repr__(self):
        return f"<SubscriptionTier(id={self.id}, name='{self.name}', price={self.price_monthly})>"

class Subscription(Base):
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    
    # User relationship
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    tier_id = Column(Integer, ForeignKey("subscription_tiers.id"), nullable=False)
    
    # Subscription details
    status = Column(String(50), default="active")  # active, suspended, cancelled, expired
    billing_cycle = Column(String(20), default="monthly")  # monthly, yearly
    
    # Billing
    amount = Column(Float, nullable=False)  # Amount in USD cents
    currency = Column(String(3), default="USD")
    next_billing_date = Column(DateTime)
    
    # Payment method
    payment_method_id = Column(Integer, ForeignKey("payment_methods.id"))
    
    # External references
    stripe_subscription_id = Column(String(255), index=True)
    stripe_customer_id = Column(String(255), index=True)
    
    # Metadata
    meta_data = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    cancelled_at = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="subscriptions")
    tier = relationship("SubscriptionTier", back_populates="subscriptions")
    payment_method = relationship("PaymentMethod")
    
    def __repr__(self):
        return f"<Subscription(id={self.id}, user_id={self.user_id}, tier='{self.tier.name}', status='{self.status}')>"
    
    @property
    def is_active(self) -> bool:
        """Check if subscription is active"""
        return self.status == "active"
    
    @property
    def days_until_renewal(self) -> int:
        """Get days until next billing date"""
        if not self.next_billing_date:
            return 0
        from datetime import datetime
        delta = self.next_billing_date - datetime.utcnow()
        return max(0, delta.days) 