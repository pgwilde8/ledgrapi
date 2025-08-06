"""
LedgrAPI Authentication Endpoints
User registration, login, and wallet authentication
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext
import logging

from app.db.session import get_db
from app.db.models import User
from app.services.auth import create_access_token, get_current_user
from app.schemas.auth import UserCreate, UserLogin, UserResponse, TokenResponse

router = APIRouter()
logger = logging.getLogger(__name__)

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@router.post("/register", response_model=UserResponse)
async def register_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new developer account
    """
    # Check if user already exists
    query = select(User).where(User.email == user_data.email)
    result = await db.execute(query)
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email already exists"
        )
    
    # Check username availability
    query = select(User).where(User.username == user_data.username)
    result = await db.execute(query)
    existing_username = result.scalar_one_or_none()
    
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Create new user
    hashed_password = pwd_context.hash(user_data.password)
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        full_name=user_data.full_name,
        hashed_password=hashed_password,
        wallet_address=user_data.wallet_address,
        wallet_network=user_data.wallet_network
    )
    
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    logger.info(f"New user registered: {new_user.email}")
    
    return UserResponse.from_orm(new_user)

@router.post("/login", response_model=TokenResponse)
async def login_user(
    user_data: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    Login with email and password
    """
    # Find user by email
    query = select(User).where(User.email == user_data.email)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user or not pwd_context.verify(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Account is deactivated"
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": user.email})
    
    logger.info(f"User logged in: {user.email}")
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.from_orm(user)
    )

@router.post("/wallet", response_model=TokenResponse)
async def authenticate_wallet(
    wallet_data: dict,
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate using wallet signature (Web3)
    """
    # TODO: Implement wallet signature verification
    # This is a placeholder for wallet-based authentication
    
    wallet_address = wallet_data.get("address")
    signature = wallet_data.get("signature")
    message = wallet_data.get("message")
    
    if not all([wallet_address, signature, message]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Missing wallet authentication data"
        )
    
    # Find user by wallet address
    query = select(User).where(User.wallet_address == wallet_address)
    result = await db.execute(query)
    user = result.scalar_one_or_none()
    
    if not user:
        # Create new user with wallet
        user = User(
            email=f"{wallet_address[:8]}@wallet.local",
            username=f"wallet_{wallet_address[:8]}",
            wallet_address=wallet_address,
            wallet_network=wallet_data.get("network", "ethereum"),
            is_verified=True
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
    
    # Create access token
    access_token = create_access_token(data={"sub": user.email})
    
    logger.info(f"Wallet authentication: {wallet_address}")
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.from_orm(user)
    )

@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user information
    """
    return UserResponse.from_orm(current_user)

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    current_user: User = Depends(get_current_user)
):
    """
    Refresh access token
    """
    access_token = create_access_token(data={"sub": current_user.email})
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.from_orm(current_user)
    ) 