"""
Admin operations for the Knowledge Base API
"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Form, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.database import get_async_db
from app.models.user import User
from app.core.permissions import get_superuser
from app.services.knowledge_base import KnowledgeBaseWorkflowService
from app.api.v1.knowledge_base.schemas import StandardErrorResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Knowledge Base - Admin"])

# Initialize services
workflow_service = KnowledgeBaseWorkflowService()

@router.post("/approve/{document_id}")
async def approve_document(
    document_id: str,
    comments: Optional[str] = Form(None),
    current_user: User = Depends(get_superuser),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Step 3: Human Review & Approval (Super Admin only)
    Approve a document after human review
    """
    try:
        result = await workflow_service.approve_document(
            document_id=document_id,
            approved_by=str(current_user.id),
            comments=comments,
            db=db
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error approving document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to approve document"
        )

@router.post("/reject/{document_id}")
async def reject_document(
    document_id: str,
    reason: str = Form(...),
    current_user: User = Depends(get_superuser),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Step 3: Human Review & Rejection (Super Admin only)
    Reject a document with reason
    """
    try:
        result = await workflow_service.reject_document(
            document_id=document_id,
            rejected_by=str(current_user.id),
            reason=reason,
            db=db
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error rejecting document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to reject document"
        )

@router.get("/pending-review", response_model=List[Dict[str, Any]])
async def list_pending_review(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=100, description="Number of records to return"),
    current_user: User = Depends(get_superuser),
    db: AsyncSession = Depends(get_async_db)
):
    """
    List documents pending review (Super Admin only)
    """
    try:
        from app.models.knowledge_base import KnowledgeBaseDocument
        
        # Find documents under review
        query = select(KnowledgeBaseDocument).where(
            and_(
                KnowledgeBaseDocument.organization_metadata['submission_status'].astext == "under_review",
                KnowledgeBaseDocument.processing_status == "processing"
            )
        )
        
        # Apply pagination
        query = query.offset(skip).limit(limit).order_by(KnowledgeBaseDocument.created_at.desc())
        
        result = await db.execute(query)
        documents = result.scalars().all()
        
        # Format response
        pending_docs = []
        for doc in documents:
            metadata = doc.organization_metadata or {}
            pending_docs.append({
                "id": str(doc.id),
                "filename": doc.filename,
                "document_type": doc.document_type.value if doc.document_type else "other",
                "description": doc.description or "",
                "uploaded_by": str(doc.uploaded_by),
                "created_at": doc.created_at.isoformat() if doc.created_at else None,
                "file_size": doc.file_size_bytes or 0,
                "quality_score": doc.quality_score or 0.0,
                "version": doc.version or 1,
                "submission_status": metadata.get("submission_status", "pending"),
                "compliance_issues": metadata.get("compliance_issues", []),
                "quality_issues": doc.quality_issues or []
            })
        
        return pending_docs
        
    except Exception as e:
        logger.error(f"Error listing pending reviews: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve pending reviews"
        )

@router.post("/check-expirations")
async def check_expirations(
    current_user: User = Depends(get_superuser),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Check for expiring documents and send reminders (Super Admin only)
    This would typically be run as a scheduled task
    """
    try:
        expiring_docs = await workflow_service.check_expiring_documents(db=db)
        
        return StandardErrorResponse.create_success_response(
            data={
                "reminders_sent": len(expiring_docs),
                "documents": expiring_docs
            },
            message="Expiration reminders processed successfully"
        )
        
    except Exception as e:
        logger.error(f"Error checking expirations: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check expirations"
        )

@router.post("/deactivate-expired")
async def deactivate_expired(
    current_user: User = Depends(get_superuser),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Deactivate expired documents from RAG system (Super Admin only)
    This would typically be run as a scheduled task
    """
    try:
        deactivated_ids = await workflow_service.deactivate_expired_documents(db=db)
        
        return StandardErrorResponse.create_success_response(
            data={
                "deactivated_count": len(deactivated_ids),
                "deactivated_documents": deactivated_ids
            },
            message="Expired documents deactivated successfully"
        )
        
    except Exception as e:
        logger.error(f"Error deactivating expired documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate expired documents"
        )
