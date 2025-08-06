"""
LedgrAPI User Model
Developer accounts and authentication
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base
import uuid

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    
    # Basic info
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(255))
    
    # Authentication
    hashed_password = Column(String(255))
    api_key = Column(String(64), unique=True, index=True, default=lambda: str(uuid.uuid4()).replace('-', ''))
    
    # Wallet integration
    wallet_address = Column(String(42), index=True)  # Ethereum-style address
    wallet_network = Column(String(50))  # ethereum, polygon, xdc, etc.
    
    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    email_verified_at = Column(DateTime)
    
    # Subscription info
    current_tier = Column(String(50), default="free")  # free, builder, pro, enterprise
    subscription_status = Column(String(50), default="active")  # active, suspended, cancelled
    
    # Metadata
    meta_data = Column(JSON)  # Additional user data
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    apis = relationship("API", back_populates="owner")
    subscriptions = relationship("Subscription", back_populates="user")
    payments = relationship("Payment", back_populates="user")
    usage_logs = relationship("UsageLog", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', tier='{self.current_tier}')>"
    
    @property
    def is_premium(self) -> bool:
        """Check if user has a paid subscription"""
        return self.current_tier in ["builder", "pro", "enterprise"]
    
    @property
    def can_publish_apis(self) -> bool:
        """Check if user can publish new APIs based on tier"""
        if self.current_tier == "free":
            return len(self.apis) < 1
        elif self.current_tier == "builder":
            return len(self.apis) < 3
        elif self.current_tier == "pro":
            return len(self.apis) < 10
        else:  # enterprise
            return True
    
    def get_rate_limit(self) -> int:
        """Get rate limit based on subscription tier"""
        limits = {
            "free": 60,      # 60 calls per minute
            "builder": 300,  # 300 calls per minute
            "pro": 1000,     # 1000 calls per minute
            "enterprise": 5000  # 5000 calls per minute
        }
        return limits.get(self.current_tier, 60) 