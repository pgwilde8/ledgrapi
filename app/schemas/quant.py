"""
LedgrAPI Quant Integration Schemas
Pydantic models for Quant cross-chain messaging and transactions
"""

from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class QuantMessageRequest(BaseModel):
    """Schema for Quant cross-chain message request"""
    from_chain: str
    to_chain: str
    message: str
    sender_address: str
    recipient_address: Optional[str] = None

class QuantMessageResponse(BaseModel):
    """Schema for Quant cross-chain message response"""
    message_id: str
    status: str
    from_chain: str
    to_chain: str
    transaction_hash: Optional[str] = None
    estimated_cost: float = 0.0
    details: Optional[str] = None

class QuantTransactionRequest(BaseModel):
    """Schema for Quant cross-chain transaction request"""
    from_chain: str
    to_chain: str
    type: str  # transfer, contract_call, etc.
    amount: float
    sender_address: str
    recipient_address: str
    contract_address: Optional[str] = None
    function_name: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = None

class QuantTransactionResponse(BaseModel):
    """Schema for Quant cross-chain transaction response"""
    transaction_id: str
    status: str
    from_chain: str
    to_chain: str
    transaction_hash: Optional[str] = None
    estimated_cost: float = 0.0
    gas_used: Optional[int] = None
    block_number: Optional[int] = None

class NetworkBalanceResponse(BaseModel):
    """Schema for network balance response"""
    network: str
    address: str
    balance: Dict[str, float]
    timestamp: datetime

class NetworkInfoResponse(BaseModel):
    """Schema for network information response"""
    name: str
    chain_id: Optional[int] = None
    rpc_url: Optional[str] = None
    supported: bool 