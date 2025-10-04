"""
Super Admin API endpoints
Handles platform administration, organization management, and system monitoring
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from typing import List, Optional, Dict, Any
import logging
from datetime import datetime, timedelta
from uuid import UUID

from app.core.database import get_async_db
from app.models.user import User
from app.models.organization import Organization, OrganizationMembership, OrganizationStatus
from app.models.conversation import Conversation
from app.models.conversation import Message
from app.core.permissions import get_superuser, SuperAdminPermissions
from app.services.auth_service import AuthService
from app.services.admin_service import AdminService
from app.api.v1.knowledge_base.schemas import StandardErrorResponse, PaginatedResponse, create_paginated_response_from_skip

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Super Admin"])
auth_service = AuthService()
admin_service = AdminService()


@router.get("/organizations", response_model=PaginatedResponse)
async def list_all_organizations(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=1000, description="Number of records to return"),
    status_filter: Optional[str] = Query(None, description="Filter by organization status"),
    search: Optional[str] = Query(None, description="Search by organization name"),
    current_user: User = Depends(get_superuser),
    db: AsyncSession = Depends(get_async_db)
):
    """
    List all organizations in the platform (super admin only)
    """
    try:
        # Use service to get organizations with stats in optimized query
        org_list, total = await admin_service.get_organizations_with_stats(
            db=db,
            skip=skip,
            limit=limit,
            status_filter=status_filter,
            search=search
        )
        
        # Create paginated response using helper function
        return create_paginated_response_from_skip(org_list, total, skip, limit)
        
    except Exception as e:
        logger.error(f"Error listing organizations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve organizations"
        )


@router.post("/organizations/{organization_id}/approve")
async def approve_organization(
    organization_id: str,
    current_user: User = Depends(get_superuser),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Approve a pending organization (super admin only)
    """
    try:
        # Use service to update organization status
        organization = await admin_service.update_organization_status(
            db=db,
            organization_id=organization_id,
            new_status=OrganizationStatus.ACTIVE
        )
        
        logger.info(f"Organization {organization_id} approved by super admin {current_user.email}")
        
        return StandardErrorResponse.create_success_response(
            data={
                "organization_id": organization_id,
                "new_status": "active",
                "organization_name": organization.name
            },
            message="Organization approved successfully"
        )
        
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    except Exception as e:
        logger.error(f"Error approving organization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to approve organization"
        )


@router.post("/organizations/{organization_id}/suspend")
async def suspend_organization(
    organization_id: str,
    reason: Optional[str] = Query(None, max_length=500, description="Reason for suspension"),
    current_user: User = Depends(get_superuser),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Suspend an organization (super admin only)
    """
    try:
        # Use service to update organization status
        organization = await admin_service.update_organization_status(
            db=db,
            organization_id=organization_id,
            new_status=OrganizationStatus.SUSPENDED,
            reason=reason
        )
        
        logger.info(f"Organization {organization_id} suspended by super admin {current_user.email}. Reason: {reason}")
        
        return StandardErrorResponse.create_success_response(
            data={
                "organization_id": organization_id,
                "new_status": "suspended",
                "organization_name": organization.name,
                "reason": reason
            },
            message="Organization suspended successfully"
        )
        
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    except Exception as e:
        logger.error(f"Error suspending organization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to suspend organization"
        )


@router.post("/organizations/{organization_id}/activate")
async def activate_organization(
    organization_id: str,
    current_user: User = Depends(get_superuser),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Activate a suspended organization (super admin only)
    """
    try:
        # Use service to update organization status
        organization = await admin_service.update_organization_status(
            db=db,
            organization_id=organization_id,
            new_status=OrganizationStatus.ACTIVE
        )
        
        logger.info(f"Organization {organization_id} activated by super admin {current_user.email}")
        
        return StandardErrorResponse.create_success_response(
            data={
                "organization_id": organization_id,
                "new_status": "active",
                "organization_name": organization.name
            },
            message="Organization activated successfully"
        )
        
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=str(e)
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
    except Exception as e:
        logger.error(f"Error activating organization: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate organization"
        )


@router.get("/users", response_model=PaginatedResponse)
async def list_all_users(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=1000, description="Number of records to return"),
    role_filter: Optional[str] = Query(None, description="Filter by user role"),
    status_filter: Optional[str] = Query(None, description="Filter by user status"),
    search: Optional[str] = Query(None, description="Search by email or name"),
    current_user: User = Depends(get_superuser),
    db: AsyncSession = Depends(get_async_db)
):
    """
    List all users in the platform (super admin only)
    """
    try:
        # Use service to get users with stats in optimized query
        user_list, total = await admin_service.get_users_with_stats(
            db=db,
            skip=skip,
            limit=limit,
            role_filter=role_filter,
            status_filter=status_filter,
            search=search
        )
        
        # Create paginated response using helper function
        return create_paginated_response_from_skip(user_list, total, skip, limit)
        
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )


@router.get("/analytics", response_model=Dict[str, Any])
async def get_platform_analytics(
    current_user: User = Depends(get_superuser),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get platform analytics and metrics (super admin only)
    """
    try:
        # Use service to get analytics in optimized queries
        analytics_data = await admin_service.get_platform_analytics(db=db)
        
        return StandardErrorResponse.create_success_response(
            data=analytics_data,
            message="Analytics retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Error getting analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve analytics"
        )


@router.get("/health", response_model=Dict[str, Any])
async def get_system_health(
    current_user: User = Depends(get_superuser),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get system health status (super admin only)
    """
    try:
        # Use service to check system health
        health_data = await admin_service.check_system_health(db=db)
        
        return StandardErrorResponse.create_success_response(
            data=health_data,
            message="System health check completed"
        )
        
    except Exception as e:
        logger.error(f"Error checking system health: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"System health check failed: {str(e)}"
        )
