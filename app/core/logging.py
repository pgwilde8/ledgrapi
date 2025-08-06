"""
LedgrAPI Logging Configuration
Structured logging setup for production and development
"""

import logging
import logging.config
import sys
from typing import Dict, Any
from app.core.config import settings

def setup_logging():
    """Setup logging configuration for the application"""
    
    # Define log format
    log_format = settings.LOG_FORMAT
    
    # Configure logging
    logging_config: Dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": log_format,
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
            "json": {
                "format": '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "name": "%(name)s", "message": "%(message)s"}',
                "datefmt": "%Y-%m-%d %H:%M:%S",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "level": settings.LOG_LEVEL,
                "formatter": "default" if settings.ENVIRONMENT == "development" else "json",
                "stream": sys.stdout,
            },
            "file": {
                "class": "logging.handlers.RotatingFileHandler",
                "level": settings.LOG_LEVEL,
                "formatter": "json",
                "filename": "logs/ledgrapi.log",
                "maxBytes": 10485760,  # 10MB
                "backupCount": 5,
            },
        },
        "loggers": {
            "": {  # Root logger
                "handlers": ["console", "file"],
                "level": settings.LOG_LEVEL,
                "propagate": False,
            },
            "app": {
                "handlers": ["console", "file"],
                "level": settings.LOG_LEVEL,
                "propagate": False,
            },
            "uvicorn": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
            "uvicorn.access": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
            "sqlalchemy": {
                "handlers": ["console"],
                "level": "WARNING",
                "propagate": False,
            },
        },
    }
    
    # Apply configuration
    logging.config.dictConfig(logging_config)
    
    # Create logs directory if it doesn't exist
    import os
    os.makedirs("logs", exist_ok=True)

def get_logger(name: str) -> logging.Logger:
    """Get a logger instance with the given name"""
    return logging.getLogger(f"app.{name}")

# Custom log levels for business events
class BusinessLogger:
    """Custom logger for business events and API usage tracking"""
    
    def __init__(self, name: str):
        self.logger = get_logger(f"business.{name}")
    
    def api_call(self, api_id: str, user_id: str, endpoint: str, cost: float = 0.0):
        """Log API call for billing and analytics"""
        self.logger.info(
            f"API_CALL api_id={api_id} user_id={user_id} endpoint={endpoint} cost={cost}",
            extra={
                "event_type": "api_call",
                "api_id": api_id,
                "user_id": user_id,
                "endpoint": endpoint,
                "cost": cost,
            }
        )
    
    def payment_received(self, user_id: str, amount: float, currency: str, payment_method: str):
        """Log payment received"""
        self.logger.info(
            f"PAYMENT_RECEIVED user_id={user_id} amount={amount} currency={currency} method={payment_method}",
            extra={
                "event_type": "payment_received",
                "user_id": user_id,
                "amount": amount,
                "currency": currency,
                "payment_method": payment_method,
            }
        )
    
    def subscription_created(self, user_id: str, tier: str, price: float):
        """Log subscription creation"""
        self.logger.info(
            f"SUBSCRIPTION_CREATED user_id={user_id} tier={tier} price={price}",
            extra={
                "event_type": "subscription_created",
                "user_id": user_id,
                "tier": tier,
                "price": price,
            }
        )
    
    def quant_transaction(self, from_chain: str, to_chain: str, message_id: str, status: str):
        """Log Quant cross-chain transaction"""
        self.logger.info(
            f"QUANT_TRANSACTION from={from_chain} to={to_chain} message_id={message_id} status={status}",
            extra={
                "event_type": "quant_transaction",
                "from_chain": from_chain,
                "to_chain": to_chain,
                "message_id": message_id,
                "status": status,
            }
        ) 