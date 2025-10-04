"""
Permission system for Ekumen platform
Handles super admin and organization-level permissions
"""

from functools import wraps
from typing import Optional
from fastapi import HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.models.user import User
from app.services.shared.auth_service import AuthService

auth_service = AuthService()


def require_superuser(func):
    """
    Decorator to require superuser permissions for API endpoints
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Find the current_user parameter
        current_user = None
        for key, value in kwargs.items():
            if isinstance(value, User):
                current_user = value
                break
        
        if not current_user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required"
            )
        
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Super admin access required"
            )
        
        return await func(*args, **kwargs)
    
    return wrapper


async def get_superuser(
    current_user: User = Depends(auth_service.get_current_user)
) -> User:
    """
    Dependency to get current superuser
    """
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Super admin access required"
        )
    return current_user


async def check_organization_permission(
    user: User,
    organization_id: str,
    permission: str,
    db: AsyncSession
) -> bool:
    """
    Check if user has specific permission in organization
    """
    from app.models.organization import OrganizationMembership
    
    # Superusers have all permissions
    if user.is_superuser:
        return True
    
    # Check organization membership
    from sqlalchemy import select
    result = await db.execute(
        select(OrganizationMembership).where(
            OrganizationMembership.user_id == user.id,
            OrganizationMembership.organization_id == organization_id,
            OrganizationMembership.is_active == True
        )
    )
    membership = result.scalar_one_or_none()
    
    if not membership:
        return False
    
    # Define role permissions
    role_permissions = {
        "owner": {
            "view_farm_data": True,
            "edit_farm_data": True,
            "delete_farm_data": True,
            "manage_members": True,
            "grant_farm_access": True,
            "view_billing": True,
            "manage_billing": True,
        },
        "admin": {
            "view_farm_data": True,
            "edit_farm_data": True,
            "delete_farm_data": False,
            "manage_members": True,
            "grant_farm_access": True,
            "view_billing": True,
            "manage_billing": False,
        },
        "advisor": {
            "view_farm_data": True,
            "edit_farm_data": True,
            "delete_farm_data": False,
            "manage_members": False,
            "grant_farm_access": False,
            "view_billing": False,
            "manage_billing": False,
        },
        "member": {
            "view_farm_data": True,
            "edit_farm_data": True,
            "delete_farm_data": False,
            "manage_members": False,
            "grant_farm_access": False,
            "view_billing": False,
            "manage_billing": False,
        },
        "viewer": {
            "view_farm_data": True,
            "edit_farm_data": False,
            "delete_farm_data": False,
            "manage_members": False,
            "grant_farm_access": False,
            "view_billing": False,
            "manage_billing": False,
        },
    }
    
    user_permissions = role_permissions.get(membership.role, {})
    return user_permissions.get(permission, False)


class SuperAdminPermissions:
    """Super admin permission constants"""
    
    # Organization Management
    VIEW_ALL_ORGANIZATIONS = "view_all_organizations"
    APPROVE_ORGANIZATIONS = "approve_organizations"
    SUSPEND_ORGANIZATIONS = "suspend_organizations"
    DELETE_ORGANIZATIONS = "delete_organizations"
    
    # User Management
    VIEW_ALL_USERS = "view_all_users"
    SUSPEND_USERS = "suspend_users"
    DELETE_USERS = "delete_users"
    
    # Platform Management
    ACCESS_ANALYTICS = "access_analytics"
    MANAGE_PLATFORM_SETTINGS = "manage_platform_settings"
    VIEW_SYSTEM_LOGS = "view_system_logs"
    
    # Knowledge Base Management
    MANAGE_PUBLIC_KNOWLEDGE = "manage_public_knowledge"
    APPROVE_DOCUMENTS = "approve_documents"
    
    @classmethod
    def get_all_permissions(cls) -> list:
        """Get all super admin permissions"""
        return [
            cls.VIEW_ALL_ORGANIZATIONS,
            cls.APPROVE_ORGANIZATIONS,
            cls.SUSPEND_ORGANIZATIONS,
            cls.DELETE_ORGANIZATIONS,
            cls.VIEW_ALL_USERS,
            cls.SUSPEND_USERS,
            cls.DELETE_USERS,
            cls.ACCESS_ANALYTICS,
            cls.MANAGE_PLATFORM_SETTINGS,
            cls.VIEW_SYSTEM_LOGS,
            cls.MANAGE_PUBLIC_KNOWLEDGE,
            cls.APPROVE_DOCUMENTS,
        ]
