"""
FastAPI dependencies for the Knowledge Base API
"""

import logging
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select

from app.models.user import User

logger = logging.getLogger(__name__)

async def get_user_organization(
    user: User,
    db: AsyncSession,
    require_active: bool = True
) -> Optional[str]:
    """
    Get user's primary organization ID using proper relationships
    Returns organization_id as string or None if not found
    FastAPI dependency function - returns value for Depends() injection
    """
    try:
        # Get user with organization memberships using eager loading
        user_result = await db.execute(
            select(User)
            .options(selectinload(User.organization_memberships))
            .where(User.id == user.id)
        )
        user_with_memberships = user_result.scalar_one_or_none()
        
        if not user_with_memberships:
            return None
        
        # Find active membership
        for membership in user_with_memberships.organization_memberships:
            if not require_active or membership.is_active:
                return str(membership.organization_id)
        
        return None
        
    except Exception as e:
        logger.error(f"Error getting user organization: {e}")
        return None

async def require_user_organization(
    user: User,
    db: AsyncSession
) -> str:
    """
    Get user's organization ID and raise HTTPException if not found
    Returns organization_id as string
    FastAPI dependency function - returns value for Depends() injection
    """
    organization_id = await get_user_organization(user, db, require_active=True)
    
    if not organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must be associated with an organization to access this resource"
        )
    
    return organization_id
