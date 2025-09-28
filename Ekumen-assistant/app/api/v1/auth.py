"""
Authentication API endpoints
Handles user authentication, registration, and JWT token management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import logging

from app.core.database import get_async_db
from app.core.config import settings
from app.models.user import User, UserRole
from app.schemas.auth import UserCreate, UserLogin, UserResponse, Token
from app.services.auth_service import AuthService

logger = logging.getLogger(__name__)

router = APIRouter()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Initialize auth service
auth_service = AuthService()

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_async_db)
):
    """
    Register a new user
    
    Args:
        user_data: User registration data
        db: Database session
        
    Returns:
        UserResponse: Created user information
        
    Raises:
        HTTPException: If email already exists or validation fails
    """
    try:
        # Check if user already exists
        existing_user = await auth_service.get_user_by_email(db, user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Create new user
        user = await auth_service.create_user(db, user_data)
        
        logger.info(f"New user registered: {user.email}")
        
        return UserResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name,
            role=user.role,
            status=user.status,
            language_preference=user.language_preference,
            region_code=user.region_code,
            is_active=user.is_active,
            created_at=user.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )

@router.post("/login", response_model=Token)
async def login_user(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Authenticate user and return access token
    
    Args:
        form_data: Login form data (username=email, password)
        db: Database session
        
    Returns:
        Token: Access token and token type
        
    Raises:
        HTTPException: If credentials are invalid
    """
    try:
        # Authenticate user
        user = await auth_service.authenticate_user(
            db, 
            email=form_data.username, 
            password=form_data.password
        )
        
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is inactive"
            )
        
        # Create access token
        access_token = auth_service.create_access_token(
            data={"sub": str(user.id), "email": user.email}
        )
        
        logger.info(f"User logged in: {user.email}")
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )

@router.get("/me", response_model=UserResponse)
async def get_current_user(
    current_user: User = Depends(auth_service.get_current_user)
):
    """
    Get current authenticated user information
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        UserResponse: Current user information
    """
    return UserResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        status=current_user.status,
        language_preference=current_user.language_preference,
        region_code=current_user.region_code,
        is_active=current_user.is_active,
        created_at=current_user.created_at
    )

@router.post("/logout")
async def logout_user(
    current_user: User = Depends(auth_service.get_current_user)
):
    """
    Logout current user (invalidate token on client side)
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        dict: Logout confirmation
    """
    logger.info(f"User logged out: {current_user.email}")
    
    return {
        "message": "Successfully logged out",
        "user_id": current_user.id
    }

@router.post("/refresh", response_model=Token)
async def refresh_token(
    current_user: User = Depends(auth_service.get_current_user)
):
    """
    Refresh access token
    
    Args:
        current_user: Current authenticated user
        
    Returns:
        Token: New access token
    """
    try:
        # Create new access token
        access_token = auth_service.create_access_token(
            data={"sub": str(current_user.id), "email": current_user.email}
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )
