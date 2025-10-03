"""
Knowledge Base Workflow API endpoints
Handles document submission, approval, and rejection workflow
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Form
from fastapi.security import HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.orm import selectinload

from app.core.database import get_async_db
from app.models.user import User
from app.models.knowledge_base import KnowledgeBaseDocument, KnowledgeBaseWorkflowAudit, KnowledgeBaseNotification
from app.models.organization import Organization
from app.services.auth_service import AuthService
from app.services.knowledge_base_workflow import KnowledgeBaseWorkflowService
from app.services.notification_service import NotificationService
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter()
security = HTTPBearer()

# Initialize services
auth_service = AuthService()
workflow_service = KnowledgeBaseWorkflowService()
notification_service = NotificationService()


@router.get("/submissions/pending", response_model=List[Dict[str, Any]])
async def get_pending_submissions(
    limit: int = Query(20, ge=1, le=100, description="Number of submissions to return"),
    offset: int = Query(0, ge=0, description="Number of submissions to skip"),
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get pending document submissions for superadmin review
    Only accessible by superadmin users
    """
    try:
        # Check if user is superadmin
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only superadmin users can access pending submissions"
            )
        
        # Get pending submissions
        result = await db.execute(
            select(KnowledgeBaseDocument)
            .options(
                selectinload(KnowledgeBaseDocument.organization),
                selectinload(KnowledgeBaseDocument.uploader)
            )
            .where(
                and_(
                    KnowledgeBaseDocument.submission_status == "under_review",
                    KnowledgeBaseDocument.processing_status == "processing"
                )
            )
            .order_by(desc(KnowledgeBaseDocument.created_at))
            .limit(limit)
            .offset(offset)
        )
        documents = result.scalars().all()
        
        submissions = []
        for doc in documents:
            submissions.append({
                "id": str(doc.id),
                "filename": doc.filename,
                "document_type": doc.document_type,
                "description": doc.description,
                "organization_name": doc.organization.name if doc.organization else "Unknown",
                "uploaded_by": doc.uploader.full_name if doc.uploader else "Unknown",
                "uploaded_at": doc.created_at.isoformat(),
                "quality_score": float(doc.quality_score) if doc.quality_score else 0.0,
                "quality_issues": doc.quality_issues or [],
                "quality_recommendations": doc.quality_recommendations or [],
                "expiration_date": doc.expiration_date.isoformat() if doc.expiration_date else None,
                "tags": doc.tags or [],
                "workflow_metadata": doc.workflow_metadata or {}
            })
        
        return submissions
        
    except Exception as e:
        logger.error(f"Error getting pending submissions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get pending submissions"
        )


@router.post("/submissions/{document_id}/approve")
async def approve_document(
    document_id: str,
    comments: Optional[str] = Form(None, description="Approval comments"),
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Approve a document submission
    Only accessible by superadmin users
    """
    try:
        # Check if user is superadmin
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only superadmin users can approve documents"
            )
        
        # Approve document
        result = await workflow_service.approve_document(
            document_id=document_id,
            approved_by=str(current_user.id),
            comments=comments,
            db=db
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error approving document {document_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to approve document"
        )


@router.post("/submissions/{document_id}/reject")
async def reject_document(
    document_id: str,
    reason: str = Form(..., description="Rejection reason"),
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Reject a document submission
    Only accessible by superadmin users
    """
    try:
        # Check if user is superadmin
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only superadmin users can reject documents"
            )
        
        # Reject document
        result = await workflow_service.reject_document(
            document_id=document_id,
            rejected_by=str(current_user.id),
            reason=reason,
            db=db
        )
        
        return result
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error rejecting document {document_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reject document"
        )


@router.get("/submissions/{document_id}/details", response_model=Dict[str, Any])
async def get_document_details(
    document_id: str,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get detailed information about a document submission
    Only accessible by superadmin users
    """
    try:
        # Check if user is superadmin
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only superadmin users can view document details"
            )
        
        # Get document details
        result = await db.execute(
            select(KnowledgeBaseDocument)
            .options(
                selectinload(KnowledgeBaseDocument.organization),
                selectinload(KnowledgeBaseDocument.uploader)
            )
            .where(KnowledgeBaseDocument.id == document_id)
        )
        document = result.scalar_one_or_none()
        
        if not document:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found"
            )
        
        # Get workflow audit trail
        audit_result = await db.execute(
            select(KnowledgeBaseWorkflowAudit)
            .where(KnowledgeBaseWorkflowAudit.document_id == document_id)
            .order_by(desc(KnowledgeBaseWorkflowAudit.performed_at))
        )
        audit_entries = audit_result.scalars().all()
        
        return {
            "id": str(document.id),
            "filename": document.filename,
            "file_path": document.file_path,
            "file_type": document.file_type,
            "file_size_bytes": document.file_size_bytes,
            "document_type": document.document_type,
            "description": document.description,
            "tags": document.tags or [],
            "visibility": document.visibility,
            "shared_with_organizations": document.shared_with_organizations or [],
            "shared_with_users": document.shared_with_users or [],
            "organization": {
                "id": str(document.organization.id),
                "name": document.organization.name,
                "organization_type": document.organization.organization_type
            } if document.organization else None,
            "uploader": {
                "id": str(document.uploader.id),
                "full_name": document.uploader.full_name,
                "email": document.uploader.email
            } if document.uploader else None,
            "processing_status": document.processing_status,
            "submission_status": document.submission_status,
            "quality_score": float(document.quality_score) if document.quality_score else 0.0,
            "quality_issues": document.quality_issues or [],
            "quality_recommendations": document.quality_recommendations or [],
            "expiration_date": document.expiration_date.isoformat() if document.expiration_date else None,
            "auto_renewal": document.auto_renewal,
            "version": document.version,
            "workflow_metadata": document.workflow_metadata or {},
            "created_at": document.created_at.isoformat(),
            "updated_at": document.updated_at.isoformat(),
            "audit_trail": [
                {
                    "id": str(entry.id),
                    "action": entry.action,
                    "performed_by": str(entry.performed_by) if entry.performed_by else None,
                    "performed_at": entry.performed_at.isoformat(),
                    "details": entry.details or {},
                    "comments": entry.comments
                }
                for entry in audit_entries
            ]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document details {document_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get document details"
        )


@router.get("/statistics", response_model=Dict[str, Any])
async def get_workflow_statistics(
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get workflow statistics for superadmin dashboard
    Only accessible by superadmin users
    """
    try:
        # Check if user is superadmin
        if not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only superadmin users can view workflow statistics"
            )
        
        # Get statistics
        stats = {}
        
        # Count by submission status
        status_counts = await db.execute(
            select(
                KnowledgeBaseDocument.submission_status,
                func.count(KnowledgeBaseDocument.id).label('count')
            )
            .group_by(KnowledgeBaseDocument.submission_status)
        )
        stats["submission_status_counts"] = {
            row.submission_status: row.count 
            for row in status_counts
        }
        
        # Count by document type
        type_counts = await db.execute(
            select(
                KnowledgeBaseDocument.document_type,
                func.count(KnowledgeBaseDocument.id).label('count')
            )
            .group_by(KnowledgeBaseDocument.document_type)
        )
        stats["document_type_counts"] = {
            row.document_type: row.count 
            for row in type_counts
        }
        
        # Count by organization
        org_counts = await db.execute(
            select(
                Organization.name,
                func.count(KnowledgeBaseDocument.id).label('count')
            )
            .join(KnowledgeBaseDocument, Organization.id == KnowledgeBaseDocument.organization_id)
            .group_by(Organization.name)
            .order_by(desc('count'))
            .limit(10)
        )
        stats["top_organizations"] = [
            {"name": row.name, "count": row.count}
            for row in org_counts
        ]
        
        # Recent activity (last 7 days)
        week_ago = datetime.utcnow() - timedelta(days=7)
        recent_activity = await db.execute(
            select(
                KnowledgeBaseWorkflowAudit.action,
                func.count(KnowledgeBaseWorkflowAudit.id).label('count')
            )
            .where(KnowledgeBaseWorkflowAudit.performed_at >= week_ago)
            .group_by(KnowledgeBaseWorkflowAudit.action)
        )
        stats["recent_activity"] = {
            row.action: row.count 
            for row in recent_activity
        }
        
        # Expiring documents (next 30 days)
        month_from_now = datetime.utcnow() + timedelta(days=30)
        expiring_count = await db.execute(
            select(func.count(KnowledgeBaseDocument.id))
            .where(
                and_(
                    KnowledgeBaseDocument.expiration_date <= month_from_now,
                    KnowledgeBaseDocument.expiration_date >= datetime.utcnow(),
                    KnowledgeBaseDocument.submission_status == "approved"
                )
            )
        )
        stats["expiring_documents_count"] = expiring_count.scalar()
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting workflow statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get workflow statistics"
        )


@router.get("/notifications", response_model=List[Dict[str, Any]])
async def get_workflow_notifications(
    limit: int = Query(20, ge=1, le=100, description="Number of notifications to return"),
    unread_only: bool = Query(False, description="Show only unread notifications"),
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get workflow notifications for the current user
    """
    try:
        # Build query
        query = select(KnowledgeBaseNotification).where(
            KnowledgeBaseNotification.user_id == current_user.id
        )
        
        if unread_only:
            query = query.where(KnowledgeBaseNotification.is_read == False)
        
        query = query.order_by(desc(KnowledgeBaseNotification.created_at)).limit(limit)
        
        result = await db.execute(query)
        notifications = result.scalars().all()
        
        return [
            {
                "id": str(notif.id),
                "notification_type": notif.notification_type,
                "title": notif.title,
                "message": notif.message,
                "is_read": notif.is_read,
                "read_at": notif.read_at.isoformat() if notif.read_at else None,
                "created_at": notif.created_at.isoformat(),
                "document_id": str(notif.document_id) if notif.document_id else None
            }
            for notif in notifications
        ]
        
    except Exception as e:
        logger.error(f"Error getting notifications: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get notifications"
        )


@router.post("/notifications/{notification_id}/mark-read")
async def mark_notification_read(
    notification_id: str,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Mark a notification as read
    """
    try:
        # Get notification
        result = await db.execute(
            select(KnowledgeBaseNotification).where(
                and_(
                    KnowledgeBaseNotification.id == notification_id,
                    KnowledgeBaseNotification.user_id == current_user.id
                )
            )
        )
        notification = result.scalar_one_or_none()
        
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        
        # Mark as read
        notification.is_read = True
        notification.read_at = datetime.utcnow()
        
        await db.commit()
        
        return {"success": True, "message": "Notification marked as read"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error marking notification as read: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark notification as read"
        )
