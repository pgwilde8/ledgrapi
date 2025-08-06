"""
LedgrAPI Payment Models
Payment processing and transaction tracking
"""

from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, JSON, ForeignKey, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.db.session import Base
import uuid

class PaymentMethod(Base):
    __tablename__ = "payment_methods"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    
    # User relationship
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Payment method details
    type = Column(String(50), nullable=False)  # stripe_card, stripe_bank, usdc_wallet, qnt_wallet, crypto
    name = Column(String(255))  # Display name
    is_default = Column(Boolean, default=False)
    
    # Payment processor details
    processor = Column(String(50))  # stripe, coinbase, direct
    processor_id = Column(String(255), index=True)  # External processor ID
    
    # Wallet details (for crypto payments)
    wallet_address = Column(String(255))
    wallet_network = Column(String(50))  # ethereum, polygon, xdc, etc.
    
    # Card details (for Stripe)
    card_brand = Column(String(50))
    card_last4 = Column(String(4))
    card_exp_month = Column(Integer)
    card_exp_year = Column(Integer)
    
    # Status
    is_active = Column(Boolean, default=True)
    is_verified = Column(Boolean, default=False)
    
    # Metadata
    meta_data = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    user = relationship("User")
    payments = relationship("Payment", back_populates="payment_method")
    
    def __repr__(self):
        return f"<PaymentMethod(id={self.id}, type='{self.type}', user_id={self.user_id})>"

class Payment(Base):
    __tablename__ = "payments"
    
    id = Column(Integer, primary_key=True, index=True)
    uuid = Column(String(36), unique=True, index=True, default=lambda: str(uuid.uuid4()))
    
    # User relationship
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    payment_method_id = Column(Integer, ForeignKey("payment_methods.id"))
    
    # Payment details
    amount = Column(Float, nullable=False)  # Amount in USD cents
    currency = Column(String(3), default="USD")
    description = Column(Text)
    
    # Payment type
    type = Column(String(50), nullable=False)  # subscription, usage, one_time
    status = Column(String(50), default="pending")  # pending, processing, completed, failed, refunded
    
    # External references
    stripe_payment_intent_id = Column(String(255), index=True)
    stripe_charge_id = Column(String(255), index=True)
    coinbase_charge_id = Column(String(255), index=True)
    
    # Blockchain transaction (for crypto payments)
    blockchain_tx_hash = Column(String(255), index=True)
    blockchain_network = Column(String(50))
    blockchain_block_number = Column(Integer)
    
    # USDC/QNT specific
    usdc_amount = Column(Float)  # USDC amount if paid in USDC
    qnt_amount = Column(Float)   # QNT amount if paid in QNT
    
    # Error handling
    error_message = Column(Text)
    error_code = Column(String(100))
    
    # Metadata
    meta_data = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime)
    
    # Relationships
    user = relationship("User", back_populates="payments")
    payment_method = relationship("PaymentMethod", back_populates="payments")
    
    def __repr__(self):
        return f"<Payment(id={self.id}, user_id={self.user_id}, amount={self.amount}, status='{self.status}')>"
    
    @property
    def amount_usd(self) -> float:
        """Get amount in USD dollars"""
        return self.amount / 100.0 if self.amount else 0.0
    
    @property
    def is_successful(self) -> bool:
        """Check if payment was successful"""
        return self.status == "completed"
    
    @property
    def is_crypto_payment(self) -> bool:
        """Check if this is a cryptocurrency payment"""
        return self.payment_method and self.payment_method.type in ["usdc_wallet", "qnt_wallet", "crypto"] 