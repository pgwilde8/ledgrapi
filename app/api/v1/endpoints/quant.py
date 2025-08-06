"""
LedgrAPI Quant Integration Endpoints
Cross-chain messaging and transaction routing
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import logging

from app.db.session import get_db
from app.db.models import User, UsageLog
from app.services.auth import get_current_user
from app.services.quant import QuantService
from app.core.logging import BusinessLogger
from app.schemas.quant import (
    QuantMessageRequest, QuantMessageResponse, QuantTransactionResponse
)

router = APIRouter()
logger = logging.getLogger(__name__)
business_logger = BusinessLogger("quant")

@router.post("/message", response_model=QuantMessageResponse)
async def send_cross_chain_message(
    message_data: QuantMessageRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Send a cross-chain message using Quant Overledger
    """
    # Check if user has Quant integration access
    if current_user.current_tier not in ["pro", "enterprise"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Quant integration requires Pro or Enterprise tier"
        )
    
    # Initialize Quant service
    quant_service = QuantService()
    
    try:
        # Send cross-chain message
        result = await quant_service.send_message(
            from_chain=message_data.from_chain,
            to_chain=message_data.to_chain,
            message=message_data.message,
            sender_address=message_data.sender_address,
            recipient_address=message_data.recipient_address
        )
        
        # Log the transaction
        business_logger.quant_transaction(
            from_chain=message_data.from_chain,
            to_chain=message_data.to_chain,
            message_id=result.get("message_id", "unknown"),
            status="completed"
        )
        
        return QuantMessageResponse(
            message_id=result.get("message_id"),
            status="completed",
            from_chain=message_data.from_chain,
            to_chain=message_data.to_chain,
            transaction_hash=result.get("transaction_hash"),
            estimated_cost=result.get("estimated_cost", 0.0)
        )
        
    except Exception as e:
        logger.error(f"Quant message error: {str(e)}")
        business_logger.quant_transaction(
            from_chain=message_data.from_chain,
            to_chain=message_data.to_chain,
            message_id="failed",
            status="failed"
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send cross-chain message: {str(e)}"
        )

@router.get("/message/{message_id}", response_model=QuantMessageResponse)
async def get_message_status(
    message_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get status of a cross-chain message
    """
    # Check if user has Quant integration access
    if current_user.current_tier not in ["pro", "enterprise"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Quant integration requires Pro or Enterprise tier"
        )
    
    # Initialize Quant service
    quant_service = QuantService()
    
    try:
        # Get message status
        status_info = await quant_service.get_message_status(message_id)
        
        return QuantMessageResponse(
            message_id=message_id,
            status=status_info.get("status", "unknown"),
            from_chain=status_info.get("from_chain"),
            to_chain=status_info.get("to_chain"),
            transaction_hash=status_info.get("transaction_hash"),
            estimated_cost=status_info.get("estimated_cost", 0.0),
            details=status_info.get("details")
        )
        
    except Exception as e:
        logger.error(f"Error getting message status: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get message status: {str(e)}"
        )

@router.post("/transaction", response_model=QuantTransactionResponse)
async def execute_cross_chain_transaction(
    transaction_data: dict,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Execute a cross-chain transaction using Quant Overledger
    """
    # Check if user has Quant integration access
    if current_user.current_tier not in ["enterprise"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cross-chain transactions require Enterprise tier"
        )
    
    # Initialize Quant service
    quant_service = QuantService()
    
    try:
        # Execute cross-chain transaction
        result = await quant_service.execute_transaction(
            from_chain=transaction_data.get("from_chain"),
            to_chain=transaction_data.get("to_chain"),
            transaction_type=transaction_data.get("type"),
            amount=transaction_data.get("amount"),
            sender_address=transaction_data.get("sender_address"),
            recipient_address=transaction_data.get("recipient_address"),
            contract_address=transaction_data.get("contract_address"),
            function_name=transaction_data.get("function_name"),
            parameters=transaction_data.get("parameters")
        )
        
        # Log the transaction
        business_logger.quant_transaction(
            from_chain=transaction_data.get("from_chain"),
            to_chain=transaction_data.get("to_chain"),
            message_id=result.get("transaction_id", "unknown"),
            status="completed"
        )
        
        return QuantTransactionResponse(
            transaction_id=result.get("transaction_id"),
            status="completed",
            from_chain=transaction_data.get("from_chain"),
            to_chain=transaction_data.get("to_chain"),
            transaction_hash=result.get("transaction_hash"),
            estimated_cost=result.get("estimated_cost", 0.0),
            gas_used=result.get("gas_used"),
            block_number=result.get("block_number")
        )
        
    except Exception as e:
        logger.error(f"Quant transaction error: {str(e)}")
        business_logger.quant_transaction(
            from_chain=transaction_data.get("from_chain"),
            to_chain=transaction_data.get("to_chain"),
            message_id="failed",
            status="failed"
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute cross-chain transaction: {str(e)}"
        )

@router.get("/networks")
async def get_supported_networks(
    current_user: User = Depends(get_current_user)
):
    """
    Get list of supported blockchain networks
    """
    # Initialize Quant service
    quant_service = QuantService()
    
    try:
        networks = await quant_service.get_supported_networks()
        return {"networks": networks}
        
    except Exception as e:
        logger.error(f"Error getting supported networks: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get supported networks: {str(e)}"
        )

@router.get("/balance/{network}/{address}")
async def get_network_balance(
    network: str,
    address: str,
    current_user: User = Depends(get_current_user)
):
    """
    Get balance for a specific network and address
    """
    # Initialize Quant service
    quant_service = QuantService()
    
    try:
        balance = await quant_service.get_balance(network, address)
        return {
            "network": network,
            "address": address,
            "balance": balance
        }
        
    except Exception as e:
        logger.error(f"Error getting balance: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get balance: {str(e)}"
        )

@router.get("/history")
async def get_quant_history(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
    limit: int = 50
):
    """
    Get Quant transaction history for current user
    """
    # Get user's Quant transactions from usage logs
    from sqlalchemy import select
    query = select(UsageLog).where(
        UsageLog.user_id == current_user.id,
        UsageLog.quant_message_id.isnot(None)
    ).order_by(UsageLog.created_at.desc()).limit(limit)
    
    result = await db.execute(query)
    transactions = result.scalars().all()
    
    return {
        "transactions": [
            {
                "message_id": tx.quant_message_id,
                "from_chain": tx.from_chain,
                "to_chain": tx.to_chain,
                "status": tx.quant_status,
                "created_at": tx.created_at,
                "cost": tx.cost
            }
            for tx in transactions
        ]
    } 