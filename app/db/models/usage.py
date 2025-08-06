"""
LedgrAPI Usage Models
API call tracking and usage analytics
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, Float, BigInteger
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base
import uuid

class APIUsage(Base):
    __tablename__ = "api_usage"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    
    # Relationships
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    api_id = Column(Integer, ForeignKey("apis.id"), nullable=False)
    
    # Usage tracking
    calls_this_month = Column(BigInteger, default=0)
    calls_total = Column(BigInteger, default=0)
    
    # Billing
    cost_this_month = Column(Float, default=0.0)  # Cost in USD cents
    cost_total = Column(Float, default=0.0)  # Total cost in USD cents
    
    # Period tracking
    month = Column(String(7))  # YYYY-MM format
    year = Column(Integer)
    
    # Metadata
    meta_data = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="usage_logs")
    api = relationship("API", back_populates="usage_logs")
    
    def __repr__(self):
        return f"<APIUsage(id={self.id}, user_id={self.user_id}, api_id={self.api_id}, calls={self.calls_this_month})>"

class UsageLog(Base):
    __tablename__ = "usage_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    
    # Relationships
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    api_id = Column(Integer, ForeignKey("apis.id"), nullable=False)
    
    # Request details
    endpoint_path = Column(String(500), nullable=False)
    method = Column(String(10), nullable=False)
    request_id = Column(String(64), index=True)  # Unique request identifier
    
    # Response details
    status_code = Column(Integer)
    response_time_ms = Column(Integer)  # Response time in milliseconds
    response_size_bytes = Column(Integer)
    
    # Billing
    cost = Column(Float, default=0.0)  # Cost for this call in USD cents
    was_free = Column(Boolean, default=True)  # Whether this call was free
    
    # Client info
    client_ip = Column(String(45))  # IPv4 or IPv6
    user_agent = Column(String(500))
    referer = Column(String(500))
    
    # Error tracking
    error_message = Column(Text)
    error_type = Column(String(100))
    
    # Quant integration (for cross-chain calls)
    quant_message_id = Column(String(255), index=True)
    from_chain = Column(String(50))
    to_chain = Column(String(50))
    quant_status = Column(String(50))  # pending, completed, failed
    
    # Metadata
    request_headers = Column(JSON)
    request_body = Column(Text)  # Truncated request body
    response_body = Column(Text)  # Truncated response body
    meta_data = Column(JSON)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="usage_logs")
    api = relationship("API", back_populates="usage_logs")
    
    def __repr__(self):
        return f"<UsageLog(id={self.id}, user_id={self.user_id}, api_id={self.api_id}, method='{self.method}', path='{self.endpoint_path}')>"
    
    @property
    def is_success(self) -> bool:
        """Check if the API call was successful"""
        return 200 <= self.status_code < 300 if self.status_code else False
    
    @property
    def is_error(self) -> bool:
        """Check if the API call resulted in an error"""
        return self.status_code >= 400 if self.status_code else False
    
    @property
    def cost_usd(self) -> float:
        """Get cost in USD dollars"""
        return self.cost / 100.0 if self.cost else 0.0 