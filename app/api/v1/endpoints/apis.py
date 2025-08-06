"""
LedgrAPI Core API Endpoints
Publish APIs and call registered APIs
"""

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import httpx
import time
import uuid
import logging

from app.db.session import get_db
from app.db.models import User, API, APIEndpoint, UsageLog, APIUsage
from app.services.auth import get_current_user
from app.services.quant import QuantService
from app.core.logging import BusinessLogger
from app.schemas.api import (
    APICreate, APIResponse, APICallRequest, APICallResponse,
    APIListResponse, APIUsageResponse
)

router = APIRouter()
logger = logging.getLogger(__name__)
business_logger = BusinessLogger("api")

@router.post("/publish", response_model=APIResponse)
async def publish_api(
    api_data: APICreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Publish a new API to the LedgrAPI platform
    """
    # Check if user can publish more APIs
    if not current_user.can_publish_apis:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Your current tier ({current_user.current_tier}) doesn't allow publishing more APIs. Upgrade to publish more."
        )
    
    # Create new API
    new_api = API(
        name=api_data.name,
        description=api_data.description,
        base_url=api_data.base_url,
        auth_type=api_data.auth_type,
        auth_config=api_data.auth_config,
        pricing_model=api_data.pricing_model,
        price_per_call=api_data.price_per_call,
        free_calls_per_month=api_data.free_calls_per_month,
        tags=api_data.tags,
        owner_id=current_user.id
    )
    
    db.add(new_api)
    await db.commit()
    await db.refresh(new_api)
    
    logger.info(f"API published: {new_api.name} by user {current_user.id}")
    
    return APIResponse.from_orm(new_api)

@router.get("/", response_model=APIListResponse)
async def list_apis(
    skip: int = 0,
    limit: int = 100,
    category: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """
    List all published APIs
    """
    query = select(API).where(API.is_active == True, API.status == "published")
    
    if category:
        query = query.where(API.tags.contains([category]))
    
    query = query.offset(skip).limit(limit)
    
    result = await db.execute(query)
    apis = result.scalars().all()
    
    return APIListResponse(
        apis=[APIResponse.from_orm(api) for api in apis],
        total=len(apis),
        skip=skip,
        limit=limit
    )

@router.get("/my", response_model=APIListResponse)
async def list_my_apis(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    List APIs owned by the current user
    """
    query = select(API).where(API.owner_id == current_user.id)
    result = await db.execute(query)
    apis = result.scalars().all()
    
    return APIListResponse(
        apis=[APIResponse.from_orm(api) for api in apis],
        total=len(apis)
    )

@router.get("/{api_id}", response_model=APIResponse)
async def get_api(
    api_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Get API details by ID
    """
    query = select(API).where(API.id == api_id, API.is_active == True)
    result = await db.execute(query)
    api = result.scalar_one_or_none()
    
    if not api:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API not found"
        )
    
    return APIResponse.from_orm(api)

@router.post("/{api_id}/call", response_model=APICallResponse)
async def call_api(
    api_id: int,
    call_request: APICallRequest,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Call a registered API through LedgrAPI
    """
    # Get API details
    query = select(API).where(API.id == api_id, API.is_active == True, API.status == "published")
    result = await db.execute(query)
    api = result.scalar_one_or_none()
    
    if not api:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API not found or not published"
        )
    
    # Check if user has access to this API
    if not api.is_public and api.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this API"
        )
    
    # Check usage limits
    usage_query = select(APIUsage).where(
        APIUsage.user_id == current_user.id,
        APIUsage.api_id == api_id
    )
    result = await db.execute(usage_query)
    usage = result.scalar_one_or_none()
    
    if not usage:
        usage = APIUsage(
            user_id=current_user.id,
            api_id=api_id,
            calls_this_month=0,
            calls_total=0,
            cost_this_month=0.0,
            cost_total=0.0
        )
        db.add(usage)
    
    # Check monthly limits
    if usage.calls_this_month >= api.free_calls_per_month:
        # User has exceeded free calls, check if they can pay
        if not current_user.is_premium:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail="Monthly free call limit exceeded. Upgrade to continue."
            )
    
    # Prepare the API call
    start_time = time.time()
    request_id = str(uuid.uuid4())
    
    # Build the full URL
    full_url = f"{api.base_url.rstrip('/')}{call_request.endpoint}"
    
    # Prepare headers
    headers = call_request.headers or {}
    if api.auth_type == "api_key" and api.auth_config:
        headers[api.auth_config.get("header_name", "Authorization")] = api.auth_config.get("api_key")
    
    # Make the API call
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(
                method=call_request.method,
                url=full_url,
                headers=headers,
                params=call_request.params,
                json=call_request.data if call_request.method in ["POST", "PUT", "PATCH"] else None
            )
            
            # Calculate response time
            response_time_ms = int((time.time() - start_time) * 1000)
            
            # Determine cost
            cost = 0.0
            was_free = True
            
            if usage.calls_this_month >= api.free_calls_per_month:
                cost = api.price_per_call
                was_free = False
            
            # Log the usage
            usage_log = UsageLog(
                user_id=current_user.id,
                api_id=api_id,
                endpoint_path=call_request.endpoint,
                method=call_request.method,
                request_id=request_id,
                status_code=response.status_code,
                response_time_ms=response_time_ms,
                response_size_bytes=len(response.content),
                cost=cost,
                was_free=was_free,
                client_ip=request.client.host if request.client else None,
                user_agent=request.headers.get("user-agent"),
                request_headers=dict(call_request.headers) if call_request.headers else None,
                request_body=str(call_request.data)[:1000] if call_request.data else None,
                response_body=str(response.content)[:1000]
            )
            
            db.add(usage_log)
            
            # Update usage statistics
            usage.calls_this_month += 1
            usage.calls_total += 1
            usage.cost_this_month += cost
            usage.cost_total += cost
            
            await db.commit()
            
            # Log business event
            business_logger.api_call(
                api_id=str(api_id),
                user_id=str(current_user.id),
                endpoint=call_request.endpoint,
                cost=cost
            )
            
            return APICallResponse(
                request_id=request_id,
                status_code=response.status_code,
                response_time_ms=response_time_ms,
                cost=cost,
                was_free=was_free,
                data=response.json() if response.headers.get("content-type", "").startswith("application/json") else None,
                headers=dict(response.headers)
            )
            
    except httpx.TimeoutException:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="API call timed out"
        )
    except httpx.RequestError as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Error calling API: {str(e)}"
        )

@router.get("/{api_id}/usage", response_model=APIUsageResponse)
async def get_api_usage(
    api_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get usage statistics for a specific API
    """
    # Check if user owns the API
    query = select(API).where(API.id == api_id, API.owner_id == current_user.id)
    result = await db.execute(query)
    api = result.scalar_one_or_none()
    
    if not api:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="API not found or access denied"
        )
    
    # Get usage statistics
    usage_query = select(APIUsage).where(
        APIUsage.user_id == current_user.id,
        APIUsage.api_id == api_id
    )
    result = await db.execute(usage_query)
    usage = result.scalar_one_or_none()
    
    if not usage:
        usage = APIUsage(
            user_id=current_user.id,
            api_id=api_id,
            calls_this_month=0,
            calls_total=0,
            cost_this_month=0.0,
            cost_total=0.0
        )
    
    return APIUsageResponse.from_orm(usage) 