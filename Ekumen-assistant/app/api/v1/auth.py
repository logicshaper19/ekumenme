"""
Authentication API endpoints
Handles user authentication, registration, and JWT token management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional
import logging

from app.core.database import get_async_db
from app.core.config import settings
from app.models.user import User, UserRole
from app.models.organization import Organization, OrganizationMembership, OrganizationStatus
from app.schemas.auth import UserCreate, UserLogin, UserResponse, Token
from app.services.shared.auth_service import AuthService

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

        # Determine organization context (single active membership auto-selected)
        result = await db.execute(
            select(OrganizationMembership, Organization)
            .join(Organization, Organization.id == OrganizationMembership.organization_id)
            .where(
                OrganizationMembership.user_id == user.id,
                OrganizationMembership.is_active == True,
                Organization.status == OrganizationStatus.ACTIVE
            )
        )
        memberships = result.all()

        org_id_str = None
        if len(memberships) == 1:
            org_id_str = str(memberships[0][0].organization_id)

        # Create access token (include org_id if determined)
        token_payload = {"sub": str(user.id), "email": user.email}
        if org_id_str:
            token_payload["org_id"] = org_id_str
        # If multiple or zero memberships, client should call /auth/organizations then /auth/select-organization

        access_token = auth_service.create_access_token(data=token_payload)

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
    current_user: User = Depends(auth_service.get_current_user),
    token: str = Depends(oauth2_scheme)
):
    """Refresh access token, preserving org_id if present in the current token"""
    try:
        token_data = auth_service.verify_token(token)
        org_id_str = str(token_data.org_id) if token_data and token_data.org_id else None
        payload = {"sub": str(current_user.id), "email": current_user.email}
        if org_id_str:
            payload["org_id"] = org_id_str
        access_token = auth_service.create_access_token(data=payload)
        return Token(access_token=access_token, token_type="bearer", expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
    except Exception as e:
        logger.error(f"Token refresh error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Token refresh failed")

@router.get("/organizations")
async def list_user_organizations(
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """List organizations the current user belongs to"""
    result = await db.execute(
        select(OrganizationMembership, Organization)
        .join(Organization, Organization.id == OrganizationMembership.organization_id)
        .where(
            OrganizationMembership.user_id == current_user.id,
            OrganizationMembership.is_active == True
        )
    )
    rows = result.all()
    orgs = [
        {
            "id": str(row[1].id),
            "name": row[1].display_name,
            "status": row[1].status,
            "role": row[0].role,
            "access_level": row[0].access_level,
        }
        for row in rows
    ]
    return {"organizations": orgs, "count": len(orgs)}


from app.schemas.auth import OrganizationSelectRequest

@router.post("/select-organization", response_model=Token)
async def select_organization(
    payload: OrganizationSelectRequest,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """Issue a token bound to a specific org if the user is a member"""
    # Validate membership
    result = await db.execute(
        select(OrganizationMembership)
        .where(
            OrganizationMembership.user_id == current_user.id,
            OrganizationMembership.organization_id == payload.org_id,
            OrganizationMembership.is_active == True
        )
    )
    membership = result.scalar_one_or_none()
    if not membership:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member of this organization")

    # Verify org is active
    org_res = await db.execute(select(Organization).where(Organization.id == payload.org_id))
    org = org_res.scalar_one_or_none()
    if not org or not org.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Organization not active")

    # Create token including org_id
    access_token = auth_service.create_access_token(
        data={
            "sub": str(current_user.id),
            "email": current_user.email,
            "org_id": str(payload.org_id)
        }
    )
    return Token(access_token=access_token, token_type="bearer", expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60)
