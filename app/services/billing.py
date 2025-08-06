"""
LedgrAPI Billing Service
Handles subscription management and payment processing
"""

from typing import Optional, Dict, Any, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from app.db.models.subscription import Subscription, SubscriptionTier
from app.db.models.payment import Payment, PaymentMethod
from app.db.models.user import User
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)

class BillingService:
    """Service for handling billing and subscription operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_subscription_tiers(self) -> List[SubscriptionTier]:
        """Get all available subscription tiers"""
        result = await self.db.execute(
            select(SubscriptionTier).where(SubscriptionTier.is_active == True)
        )
        return result.scalars().all()
    
    async def get_user_subscription(self, user_id: int) -> Optional[Subscription]:
        """Get user's current active subscription"""
        result = await self.db.execute(
            select(Subscription)
            .where(
                and_(
                    Subscription.user_id == user_id,
                    Subscription.status == "active"
                )
            )
            .order_by(Subscription.created_at.desc())
        )
        return result.scalar_one_or_none()
    
    async def create_subscription(
        self, 
        user_id: int, 
        tier_id: int, 
        payment_method_id: Optional[int] = None,
        stripe_subscription_id: Optional[str] = None
    ) -> Subscription:
        """Create a new subscription for a user"""
        # Get the tier
        tier_result = await self.db.execute(
            select(SubscriptionTier).where(SubscriptionTier.id == tier_id)
        )
        tier = tier_result.scalar_one()
        
        if not tier:
            raise ValueError(f"Subscription tier {tier_id} not found")
        
        # Cancel any existing active subscription
        await self.cancel_user_subscription(user_id)
        
        # Create new subscription
        subscription = Subscription(
            user_id=user_id,
            tier_id=tier_id,
            status="active",
            billing_cycle="monthly",
            amount=tier.price_monthly,
            currency="USD",
            payment_method_id=payment_method_id,
            stripe_subscription_id=stripe_subscription_id
        )
        
        self.db.add(subscription)
        await self.db.commit()
        await self.db.refresh(subscription)
        
        logger.info(f"Created subscription {subscription.id} for user {user_id}")
        return subscription
    
    async def cancel_user_subscription(self, user_id: int) -> bool:
        """Cancel user's active subscription"""
        result = await self.db.execute(
            select(Subscription)
            .where(
                and_(
                    Subscription.user_id == user_id,
                    Subscription.status == "active"
                )
            )
        )
        subscription = result.scalar_one_or_none()
        
        if subscription:
            subscription.status = "cancelled"
            await self.db.commit()
            logger.info(f"Cancelled subscription {subscription.id} for user {user_id}")
            return True
        
        return False
    
    async def get_user_payment_history(self, user_id: int, limit: int = 50) -> List[Payment]:
        """Get user's payment history"""
        result = await self.db.execute(
            select(Payment)
            .where(Payment.user_id == user_id)
            .order_by(Payment.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
    
    async def create_payment(
        self,
        user_id: int,
        amount: float,
        currency: str = "USD",
        payment_type: str = "subscription",
        payment_method_id: Optional[int] = None,
        description: Optional[str] = None,
        stripe_payment_intent_id: Optional[str] = None
    ) -> Payment:
        """Create a new payment record"""
        payment = Payment(
            user_id=user_id,
            payment_method_id=payment_method_id,
            amount=amount,
            currency=currency,
            type=payment_type,
            description=description,
            stripe_payment_intent_id=stripe_payment_intent_id,
            status="pending"
        )
        
        self.db.add(payment)
        await self.db.commit()
        await self.db.refresh(payment)
        
        logger.info(f"Created payment {payment.id} for user {user_id}")
        return payment
    
    async def update_payment_status(
        self, 
        payment_id: int, 
        status: str, 
        stripe_charge_id: Optional[str] = None
    ) -> Payment:
        """Update payment status"""
        result = await self.db.execute(
            select(Payment).where(Payment.id == payment_id)
        )
        payment = result.scalar_one()
        
        if not payment:
            raise ValueError(f"Payment {payment_id} not found")
        
        payment.status = status
        if stripe_charge_id:
            payment.stripe_charge_id = stripe_charge_id
        
        if status == "completed":
            payment.completed_at = payment.updated_at
        
        await self.db.commit()
        await self.db.refresh(payment)
        
        logger.info(f"Updated payment {payment_id} status to {status}")
        return payment
    
    async def get_user_billing_usage(self, user_id: int) -> Dict[str, Any]:
        """Get user's current billing usage (mock implementation)"""
        # TODO: Implement actual usage calculation from UsageLog
        return {
            "current_month_calls": 0,
            "current_month_cost": 0.0,
            "total_calls": 0,
            "total_cost": 0.0,
            "subscription_tier": "free",
            "calls_remaining": 1000,
            "cost_remaining": 0.0
        } 