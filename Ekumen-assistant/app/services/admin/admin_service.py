"""
Admin Service
Handles platform administration business logic
"""

from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, case
from datetime import datetime, timedelta
import logging
from uuid import UUID

from app.models.user import User
from app.models.organization import Organization, OrganizationMembership, OrganizationStatus
from app.models.conversation import Conversation, Message
from app.api.v1.knowledge_base.schemas import PaginatedResponse, create_paginated_response

logger = logging.getLogger(__name__)


class AdminService:
    """Service class for admin operations"""
    
    async def get_organizations_with_stats(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 50,
        status_filter: Optional[str] = None,
        search: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Get organizations with member/conversation counts in optimized query
        Returns (organizations_list, total_count)
        """
        # Build base query with joins to avoid N+1
        base_query = (
            select(
                Organization,
                func.count(OrganizationMembership.id).label('member_count'),
                func.count(Conversation.id).label('conversation_count')
            )
            .outerjoin(
                OrganizationMembership,
                and_(
                    OrganizationMembership.organization_id == Organization.id,
                    OrganizationMembership.is_active == True
                )
            )
            .outerjoin(Conversation, Conversation.organization_id == Organization.id)
            .group_by(Organization.id)
        )
        
        # Apply filters
        if status_filter:
            base_query = base_query.where(Organization.status == status_filter)
        
        if search:
            base_query = base_query.where(
                or_(
                    Organization.name.ilike(f"%{search}%"),
                    Organization.legal_name.ilike(f"%{search}%")
                )
            )
        
        # Get total count for pagination
        count_query = select(func.count()).select_from(
            base_query.subquery()
        )
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination and ordering
        query = base_query.order_by(Organization.created_at.desc()).offset(skip).limit(limit)
        
        # Execute query
        result = await db.execute(query)
        rows = result.fetchall()
        
        # Format response
        org_list = []
        for row in rows:
            org, member_count, conversation_count = row
            org_list.append({
                "id": str(org.id),
                "name": org.name,
                "legal_name": org.legal_name,
                "type": org.type,
                "status": org.status,
                "member_count": member_count or 0,
                "conversation_count": conversation_count or 0,
                "created_at": org.created_at,
                "updated_at": org.updated_at,
                "is_active": org.is_active
            })
        
        return org_list, total
    
    async def get_users_with_stats(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 50,
        role_filter: Optional[str] = None,
        status_filter: Optional[str] = None,
        search: Optional[str] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Get users with organization counts in optimized query
        Returns (users_list, total_count)
        """
        # Build base query with joins to avoid N+1
        base_query = (
            select(
                User,
                func.count(OrganizationMembership.id).label('organization_count')
            )
            .outerjoin(
                OrganizationMembership,
                and_(
                    OrganizationMembership.user_id == User.id,
                    OrganizationMembership.is_active == True
                )
            )
            .group_by(User.id)
        )
        
        # Apply filters
        if role_filter:
            base_query = base_query.where(User.role == role_filter)
        
        if status_filter:
            base_query = base_query.where(User.status == status_filter)
        
        if search:
            base_query = base_query.where(
                or_(
                    User.email.ilike(f"%{search}%"),
                    User.full_name.ilike(f"%{search}%")
                )
            )
        
        # Get total count for pagination
        count_query = select(func.count()).select_from(
            base_query.subquery()
        )
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Apply pagination and ordering
        query = base_query.order_by(User.created_at.desc()).offset(skip).limit(limit)
        
        # Execute query
        result = await db.execute(query)
        rows = result.fetchall()
        
        # Format response
        user_list = []
        for row in rows:
            user, organization_count = row
            user_list.append({
                "id": str(user.id),
                "email": user.email,
                "full_name": user.full_name,
                "role": user.role,
                "status": user.status,
                "is_superuser": user.is_superuser,
                "is_active": user.is_active,
                "is_verified": user.is_verified,
                "organization_count": organization_count or 0,
                "created_at": user.created_at,
                "last_login": user.last_login
            })
        
        return user_list, total
    
    async def update_organization_status(
        self,
        db: AsyncSession,
        organization_id: str,
        new_status: OrganizationStatus,
        reason: Optional[str] = None
    ) -> Organization:
        """
        Centralized organization status update logic
        """
        # Validate UUID format
        try:
            UUID(organization_id)
        except ValueError:
            raise ValueError(f"Invalid organization ID format: '{organization_id}'. Organization ID must be a valid UUID.")
        
        # Get organization
        result = await db.execute(
            select(Organization).where(Organization.id == organization_id)
        )
        organization = result.scalar_one_or_none()
        
        if not organization:
            raise ValueError(f"Organization with ID '{organization_id}' not found. Please verify the organization ID and try again.")
        
        # Validate status transition
        current_status = organization.status
        
        if new_status == OrganizationStatus.ACTIVE:
            if current_status not in [OrganizationStatus.PENDING, OrganizationStatus.SUSPENDED]:
                raise ValueError(f"Cannot activate organization '{organization.name}' (ID: {organization_id}). Current status is '{current_status.value}'. Only organizations with status 'pending' or 'suspended' can be activated.")
        elif new_status == OrganizationStatus.SUSPENDED:
            if current_status == OrganizationStatus.SUSPENDED:
                raise ValueError(f"Organization '{organization.name}' (ID: {organization_id}) is already suspended. Current status is '{current_status.value}'.")
        elif new_status == OrganizationStatus.PENDING:
            if current_status == OrganizationStatus.PENDING:
                raise ValueError(f"Organization '{organization.name}' (ID: {organization_id}) is already pending. Current status is '{current_status.value}'.")
        
        # Update status
        organization.status = new_status
        organization.updated_at = datetime.utcnow()
        
        await db.commit()
        
        return organization
    
    async def get_platform_analytics(
        self,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Get all platform analytics in optimized queries
        """
        # Single query to get all basic counts
        basic_counts_query = select(
            func.count(User.id).label('total_users'),
            func.count(Organization.id).label('total_organizations'),
            func.count(Conversation.id).label('total_conversations'),
            func.count(Message.id).label('total_messages')
        )
        basic_counts_result = await db.execute(basic_counts_query)
        basic_counts = basic_counts_result.fetchone()
        
        # Single query for active users and recent activity
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        
        activity_query = select(
            func.count(case((User.last_login >= thirty_days_ago, User.id))).label('active_users_30d'),
            func.count(case((Conversation.created_at >= seven_days_ago, Conversation.id))).label('recent_conversations'),
            func.count(case((Message.created_at >= seven_days_ago, Message.id))).label('recent_messages')
        )
        activity_result = await db.execute(activity_query)
        activity_data = activity_result.fetchone()
        
        # Single query for organization status breakdown
        org_status_result = await db.execute(
            select(Organization.status, func.count(Organization.id))
            .group_by(Organization.status)
        )
        org_status_breakdown = dict(org_status_result.fetchall())
        
        # Single query for user role breakdown
        user_role_result = await db.execute(
            select(User.role, func.count(User.id))
            .group_by(User.role)
        )
        user_role_breakdown = dict(user_role_result.fetchall())
        
        return {
            "overview": {
                "total_users": basic_counts.total_users,
                "total_organizations": basic_counts.total_organizations,
                "total_conversations": basic_counts.total_conversations,
                "total_messages": basic_counts.total_messages,
                "active_users_30d": activity_data.active_users_30d
            },
            "organization_breakdown": org_status_breakdown,
            "user_role_breakdown": user_role_breakdown,
            "recent_activity": {
                "conversations_7d": activity_data.recent_conversations,
                "messages_7d": activity_data.recent_messages
            },
            "generated_at": datetime.utcnow().isoformat()
        }
    
    async def check_system_health(
        self,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Check system health with proper error handling
        """
        try:
            # Test database connection
            await db.execute(select(1))
            db_status = "healthy"
            
            # Get basic metrics in single query
            metrics_query = select(
                func.count(User.id).label('total_users'),
                func.count(Organization.id).label('total_organizations')
            )
            metrics_result = await db.execute(metrics_query)
            metrics = metrics_result.fetchone()
            
            return {
                "status": "healthy",
                "database": db_status,
                "metrics": {
                    "total_users": metrics.total_users,
                    "total_organizations": metrics.total_organizations
                },
                "timestamp": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"System health check failed: {e}")
            raise Exception(f"System health check failed: {str(e)}")
