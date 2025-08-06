"""
LedgrAPI Configuration Settings
Environment-based configuration using Pydantic Settings
"""

from pydantic_settings import BaseSettings
from typing import List, Optional, Dict, Any, ClassVar
from pydantic import field_validator
import os

class Settings(BaseSettings):
    # Application
    APP_NAME: str = "LedgrAPI"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 9176
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://ledgrapi_user:Securepass@localhost/ledgrapi_db"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 30
    
    # Redis (for Celery and caching)
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:8000",
        "https://ledgrapi.com",
        "https://www.ledgrapi.com"
    ]
    
    # Allowed Hosts
    ALLOWED_HOSTS: List[str] = [
        "localhost",
        "127.0.0.1",
        "24.144.67.150",
        "ledgrapi.com",
        "www.ledgrapi.com"
    ]
    
    @field_validator('CORS_ORIGINS', mode='before')
    @classmethod
    def parse_cors_origins(cls, v):
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',') if origin.strip()]
        return v
    
    @field_validator('ALLOWED_HOSTS', mode='before')
    @classmethod
    def parse_allowed_hosts(cls, v):
        if isinstance(v, str):
            return [host.strip() for host in v.split(',') if host.strip()]
        return v
    
    # Blockchain Configuration
    # Ethereum
    ETHEREUM_RPC_URL: str = "https://mainnet.infura.io/v3/your-project-id"
    ETHEREUM_CHAIN_ID: int = 1
    
    # Polygon
    POLYGON_RPC_URL: str = "https://polygon-rpc.com"
    POLYGON_CHAIN_ID: int = 137
    
    # XDC Network
    XDC_RPC_URL: str = "https://erpc.xinfin.network"
    XDC_CHAIN_ID: int = 50
    
    # XRPL
    XRPL_RPC_URL: str = "https://xrplcluster.com"
    
    # Quant Network (placeholder for future integration)
    QUANT_RPC_URL: Optional[str] = None
    QUANT_API_KEY: Optional[str] = None
    
    # Payment Configuration
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    COINBASE_COMMERCE_API_KEY: Optional[str] = None
    
    # USDC Configuration
    USDC_CONTRACT_ADDRESS_ETH: str = "0xA0b86a33E6441b8c4C8C8C8C8C8C8C8C8C8C8C8C"
    USDC_CONTRACT_ADDRESS_POLYGON: str = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
    
    # QNT Configuration
    QNT_CONTRACT_ADDRESS: str = "0x4a220e6096b25eadb88358cb44068a3248254675"
    
    # API Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # Pricing Tiers (in USD cents)
    PRICING_TIERS: ClassVar[Dict[str, Dict[str, Any]]] = {
        "free": {
            "price": 0,
            "calls_per_month": 1000,
            "apis_limit": 1,
            "networks": ["testnet"]
        },
        "builder": {
            "price": 4900,  # $49.00
            "calls_per_month": 10000,
            "apis_limit": 3,
            "networks": ["ethereum", "polygon", "xdc", "xrpl"]
        },
        "pro": {
            "price": 19900,  # $199.00
            "calls_per_month": 100000,
            "apis_limit": 10,
            "networks": ["ethereum", "polygon", "xdc", "xrpl", "quant"]
        },
        "enterprise": {
            "price": 100000,  # $1000.00
            "calls_per_month": 1000000,
            "apis_limit": -1,  # Unlimited
            "networks": ["all"]
        }
    }
    
    # Logging
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Email (for notifications)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USERNAME: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_USE_TLS: bool = True
    
    # Monitoring
    SENTRY_DSN: Optional[str] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create settings instance
settings = Settings()

# Validate critical settings
def validate_settings():
    """Validate critical settings on startup"""
    if settings.ENVIRONMENT == "production":
        if settings.SECRET_KEY == "your-secret-key-change-in-production":
            raise ValueError("SECRET_KEY must be set in production")
        
        if not settings.STRIPE_SECRET_KEY:
            print("Warning: STRIPE_SECRET_KEY not set - payment features disabled")
        
        if not settings.QUANT_API_KEY:
            print("Warning: QUANT_API_KEY not set - Quant integration disabled")

# Run validation
validate_settings() 