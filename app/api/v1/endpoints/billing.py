"""
LedgrAPI Billing Endpoints
Subscription management and payment processing
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import logging

from app.db.session import get_db
from app.db.models import User, Subscription, SubscriptionTier, Payment
from app.services.auth import get_current_user
from app.services.billing import BillingService
from app.schemas.billing import (
    SubscriptionCreate, SubscriptionResponse, PaymentResponse,
    BillingUsageResponse
)

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/tiers", response_model=List[dict])
async def get_subscription_tiers(
    db: AsyncSession = Depends(get_db)
):
    """
    Get available subscription tiers
    """
    query = select(SubscriptionTier).where(SubscriptionTier.is_active == True, SubscriptionTier.is_public == True)
    result = await db.execute(query)
    tiers = result.scalars().all()
    
    return [
        {
            "id": tier.id,
            "name": tier.name,
            "display_name": tier.display_name,
            "description": tier.description,
            "price_monthly": tier.price_monthly,
            "price_yearly": tier.price_yearly,
            "api_limit": tier.api_limit,
            "calls_per_month": tier.calls_per_month,
            "rate_limit_per_minute": tier.rate_limit_per_minute,
            "features": tier.features,
            "supported_networks": tier.supported_networks,
            "quant_integration": tier.quant_integration
        }
        for tier in tiers
    ]

@router.post("/subscribe", response_model=SubscriptionResponse)
async def create_subscription(
    subscription_data: SubscriptionCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new subscription
    """
    # Get tier details
    query = select(SubscriptionTier).where(SubscriptionTier.id == subscription_data.tier_id)
    result = await db.execute(query)
    tier = result.scalar_one_or_none()
    
    if not tier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subscription tier not found"
        )
    
    # Check if user already has an active subscription
    query = select(Subscription).where(
        Subscription.user_id == current_user.id,
        Subscription.status == "active"
    )
    result = await db.execute(query)
    existing_subscription = result.scalar_one_or_none()
    
    if existing_subscription:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User already has an active subscription"
        )
    
    # Calculate amount based on billing cycle
    amount = tier.price_monthly if subscription_data.billing_cycle == "monthly" else tier.price_yearly
    
    # Create subscription
    new_subscription = Subscription(
        user_id=current_user.id,
        tier_id=tier.id,
        billing_cycle=subscription_data.billing_cycle,
        amount=amount,
        currency="USD"
    )
    
    db.add(new_subscription)
    await db.commit()
    await db.refresh(new_subscription)
    
    # Update user's current tier
    current_user.current_tier = tier.name
    await db.commit()
    
    logger.info(f"Subscription created: {tier.name} for user {current_user.id}")
    
    return SubscriptionResponse.from_orm(new_subscription)

@router.get("/subscription", response_model=SubscriptionResponse)
async def get_current_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current user's subscription
    """
    query = select(Subscription).where(
        Subscription.user_id == current_user.id,
        Subscription.status == "active"
    )
    result = await db.execute(query)
    subscription = result.scalar_one_or_none()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found"
        )
    
    return SubscriptionResponse.from_orm(subscription)

@router.post("/subscription/cancel")
async def cancel_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Cancel current subscription
    """
    query = select(Subscription).where(
        Subscription.user_id == current_user.id,
        Subscription.status == "active"
    )
    result = await db.execute(query)
    subscription = result.scalar_one_or_none()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active subscription found"
        )
    
    # Cancel subscription
    subscription.status = "cancelled"
    current_user.current_tier = "free"
    
    await db.commit()
    
    logger.info(f"Subscription cancelled for user {current_user.id}")
    
    return {"message": "Subscription cancelled successfully"}

@router.get("/usage", response_model=BillingUsageResponse)
async def get_billing_usage(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get current billing usage
    """
    # Get current subscription
    query = select(Subscription).where(
        Subscription.user_id == current_user.id,
        Subscription.status == "active"
    )
    result = await db.execute(query)
    subscription = result.scalar_one_or_none()
    
    if not subscription:
        # Return free tier usage
        return BillingUsageResponse(
            tier="free",
            calls_used=0,
            calls_limit=1000,
            cost_this_month=0.0,
            days_until_reset=30
        )
    
    # Calculate usage for current month
    from datetime import datetime, timedelta
    now = datetime.utcnow()
    start_of_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    
    # TODO: Implement actual usage calculation from UsageLog table
    # For now, return mock data
    calls_used = 0  # This should be calculated from UsageLog
    cost_this_month = 0.0  # This should be calculated from UsageLog
    
    return BillingUsageResponse(
        tier=subscription.tier.name,
        calls_used=calls_used,
        calls_limit=subscription.tier.calls_per_month,
        cost_this_month=cost_this_month,
        days_until_reset=(start_of_month + timedelta(days=32)).replace(day=1) - now
    )

@router.get("/payments", response_model=List[PaymentResponse])
async def get_payment_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get payment history for current user
    """
    query = select(Payment).where(Payment.user_id == current_user.id).order_by(Payment.created_at.desc())
    result = await db.execute(query)
    payments = result.scalars().all()
    
    return [PaymentResponse.from_orm(payment) for payment in payments]

@router.post("/webhook/stripe")
async def stripe_webhook(
    request: dict,
    db: AsyncSession = Depends(get_db)
):
    """
    Handle Stripe webhooks
    """
    # TODO: Implement Stripe webhook handling
    # This should verify the webhook signature and process events
    logger.info("Stripe webhook received")
    
    return {"status": "processed"} 