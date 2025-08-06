"""
LedgrAPI API Models
Published APIs and endpoints
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base
import uuid

class API(Base):
    __tablename__ = "apis"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    
    # Basic info
    name = Column(String(255), nullable=False)
    description = Column(Text)
    version = Column(String(50), default="1.0.0")
    
    # Owner
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Configuration
    base_url = Column(String(500), nullable=False)
    auth_type = Column(String(50), default="none")  # none, api_key, oauth, wallet
    auth_config = Column(JSON)  # Authentication configuration
    
    # Pricing
    pricing_model = Column(String(50), default="per_call")  # per_call, subscription, freemium
    price_per_call = Column(Float, default=0.0)  # Price in USD cents
    free_calls_per_month = Column(Integer, default=0)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_public = Column(Boolean, default=False)
    status = Column(String(50), default="draft")  # draft, published, deprecated
    
    # Metadata
    tags = Column(JSON)  # API tags/categories
    documentation_url = Column(String(500))
    support_email = Column(String(255))
    meta_data = Column(JSON)  # Additional API data
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    published_at = Column(DateTime)
    
    # Relationships
    owner = relationship("User", back_populates="apis")
    endpoints = relationship("APIEndpoint", back_populates="api", cascade="all, delete-orphan")
    usage_logs = relationship("UsageLog", back_populates="api")
    
    def __repr__(self):
        return f"<API(id={self.id}, name='{self.name}', owner_id={self.owner_id})>"
    
    @property
    def total_endpoints(self) -> int:
        """Get total number of endpoints"""
        return len(self.endpoints)
    
    @property
    def is_published(self) -> bool:
        """Check if API is published"""
        return self.status == "published" and self.is_active

class APIEndpoint(Base):
    __tablename__ = "api_endpoints"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    
    # API relationship
    api_id = Column(Integer, ForeignKey("apis.id"), nullable=False)
    
    # Endpoint info
    path = Column(String(500), nullable=False)  # /users/{id}
    method = Column(String(10), nullable=False)  # GET, POST, PUT, DELETE
    name = Column(String(255))
    description = Column(Text)
    
    # Configuration
    request_schema = Column(JSON)  # Request validation schema
    response_schema = Column(JSON)  # Response schema
    headers_required = Column(JSON)  # Required headers
    query_params = Column(JSON)  # Query parameters
    
    # Rate limiting
    rate_limit_per_minute = Column(Integer, default=60)
    rate_limit_per_hour = Column(Integer, default=1000)
    
    # Pricing
    price_per_call = Column(Float, default=0.0)  # Override API-level pricing
    free_calls_per_month = Column(Integer, default=0)  # Override API-level free calls
    
    # Status
    is_active = Column(Boolean, default=True)
    status = Column(String(50), default="active")  # active, deprecated, maintenance
    
    # Metadata
    meta_data = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    api = relationship("API", back_populates="endpoints")
    
    def __repr__(self):
        return f"<APIEndpoint(id={self.id}, method='{self.method}', path='{self.path}')>"
    
    @property
    def full_path(self) -> str:
        """Get full endpoint path"""
        return f"{self.api.base_url.rstrip('/')}{self.path}"
    
    @property
    def effective_price(self) -> float:
        """Get effective price (endpoint overrides API)"""
        return self.price_per_call if self.price_per_call > 0 else self.api.price_per_call
    
    @property
    def effective_free_calls(self) -> int:
        """Get effective free calls (endpoint overrides API)"""
        return self.free_calls_per_month if self.free_calls_per_month > 0 else self.api.free_calls_per_month 