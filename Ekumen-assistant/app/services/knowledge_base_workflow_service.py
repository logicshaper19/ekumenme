"""
Knowledge Base Workflow Service
Handles document workflow operations like approval, rejection, and renewal
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.orm import selectinload

from app.models.knowledge_base import KnowledgeBaseDocument, KnowledgeBaseWorkflowAudit
from app.models.user import User

logger = logging.getLogger(__name__)


class KnowledgeBaseWorkflowService:
    """Service for managing knowledge base document workflow operations"""
    
    def __init__(self):
        pass
    
    async def approve_document(
        self,
        document_id: str,
        approved_by: str,
        comments: Optional[str] = None,
        db: AsyncSession = None
    ) -> Dict[str, Any]:
        """
        Approve a document after human review
        """
        try:
            # Get document
            doc_result = await db.execute(
                select(KnowledgeBaseDocument).where(KnowledgeBaseDocument.id == document_id)
            )
            document = doc_result.scalar_one_or_none()
            
            if not document:
                return {"error": "Document not found"}
            
            # Update document status
            document.status = "approved"
            document.approved_by = approved_by
            document.approved_at = datetime.utcnow()
            document.comments = comments
            
            # Create audit record
            audit = KnowledgeBaseWorkflowAudit(
                document_id=document_id,
                action="approved",
                performed_by=approved_by,
                comments=comments,
                timestamp=datetime.utcnow()
            )
            db.add(audit)
            
            await db.commit()
            
            return {
                "success": True,
                "message": "Document approved successfully",
                "document_id": document_id
            }
            
        except Exception as e:
            logger.error(f"Error approving document: {e}")
            await db.rollback()
            return {"error": "Failed to approve document"}
    
    async def reject_document(
        self,
        document_id: str,
        rejected_by: str,
        reason: str,
        db: AsyncSession = None
    ) -> Dict[str, Any]:
        """
        Reject a document after human review
        """
        try:
            # Get document
            doc_result = await db.execute(
                select(KnowledgeBaseDocument).where(KnowledgeBaseDocument.id == document_id)
            )
            document = doc_result.scalar_one_or_none()
            
            if not document:
                return {"error": "Document not found"}
            
            # Update document status
            document.status = "rejected"
            document.rejected_by = rejected_by
            document.rejected_at = datetime.utcnow()
            document.rejection_reason = reason
            
            # Create audit record
            audit = KnowledgeBaseWorkflowAudit(
                document_id=document_id,
                action="rejected",
                performed_by=rejected_by,
                comments=reason,
                timestamp=datetime.utcnow()
            )
            db.add(audit)
            
            await db.commit()
            
            return {
                "success": True,
                "message": "Document rejected successfully",
                "document_id": document_id
            }
            
        except Exception as e:
            logger.error(f"Error rejecting document: {e}")
            await db.rollback()
            return {"error": "Failed to reject document"}
    
    async def submit_document(
        self,
        document_data: Dict[str, Any],
        submitted_by: str,
        db: AsyncSession = None
    ) -> Dict[str, Any]:
        """
        Submit a new document for review
        """
        try:
            # Create new document
            document = KnowledgeBaseDocument(
                title=document_data.get("title"),
                content=document_data.get("content"),
                document_type=document_data.get("document_type"),
                status="pending",
                submitted_by=submitted_by,
                submitted_at=datetime.utcnow()
            )
            
            db.add(document)
            await db.commit()
            await db.refresh(document)
            
            # Create audit record
            audit = KnowledgeBaseWorkflowAudit(
                document_id=str(document.id),
                action="submitted",
                performed_by=submitted_by,
                comments="Document submitted for review",
                timestamp=datetime.utcnow()
            )
            db.add(audit)
            await db.commit()
            
            return {
                "success": True,
                "message": "Document submitted successfully",
                "document_id": str(document.id)
            }
            
        except Exception as e:
            logger.error(f"Error submitting document: {e}")
            await db.rollback()
            return {"error": "Failed to submit document"}
    
    async def renew_document(
        self,
        document_id: str,
        renewed_by: str,
        new_expiry_date: Optional[datetime] = None,
        db: AsyncSession = None
    ) -> Dict[str, Any]:
        """
        Renew an expiring document
        """
        try:
            # Get document
            doc_result = await db.execute(
                select(KnowledgeBaseDocument).where(KnowledgeBaseDocument.id == document_id)
            )
            document = doc_result.scalar_one_or_none()
            
            if not document:
                return {"error": "Document not found"}
            
            # Update expiry date (default to 1 year from now)
            if new_expiry_date is None:
                new_expiry_date = datetime.utcnow() + timedelta(days=365)
            
            document.expiry_date = new_expiry_date
            document.renewed_by = renewed_by
            document.renewed_at = datetime.utcnow()
            
            # Create audit record
            audit = KnowledgeBaseWorkflowAudit(
                document_id=document_id,
                action="renewed",
                performed_by=renewed_by,
                comments=f"Document renewed until {new_expiry_date}",
                timestamp=datetime.utcnow()
            )
            db.add(audit)
            
            await db.commit()
            
            return {
                "success": True,
                "message": "Document renewed successfully",
                "document_id": document_id,
                "new_expiry_date": new_expiry_date
            }
            
        except Exception as e:
            logger.error(f"Error renewing document: {e}")
            await db.rollback()
            return {"error": "Failed to renew document"}
    
    async def check_expiring_documents(
        self,
        days_ahead: int = 30,
        db: AsyncSession = None
    ) -> Dict[str, Any]:
        """
        Check for documents expiring within the specified number of days
        """
        try:
            expiry_threshold = datetime.utcnow() + timedelta(days=days_ahead)
            
            # Get expiring documents
            result = await db.execute(
                select(KnowledgeBaseDocument)
                .where(
                    and_(
                        KnowledgeBaseDocument.expiry_date <= expiry_threshold,
                        KnowledgeBaseDocument.expiry_date > datetime.utcnow(),
                        KnowledgeBaseDocument.status == "approved"
                    )
                )
                .order_by(KnowledgeBaseDocument.expiry_date)
            )
            
            expiring_docs = result.scalars().all()
            
            return {
                "success": True,
                "expiring_documents": [
                    {
                        "id": str(doc.id),
                        "title": doc.title,
                        "expiry_date": doc.expiry_date,
                        "days_until_expiry": (doc.expiry_date - datetime.utcnow()).days
                    }
                    for doc in expiring_docs
                ],
                "count": len(expiring_docs)
            }
            
        except Exception as e:
            logger.error(f"Error checking expiring documents: {e}")
            return {"error": "Failed to check expiring documents"}
    
    async def deactivate_expired_documents(
        self,
        db: AsyncSession = None
    ) -> Dict[str, Any]:
        """
        Deactivate documents that have expired
        """
        try:
            # Get expired documents
            result = await db.execute(
                select(KnowledgeBaseDocument)
                .where(
                    and_(
                        KnowledgeBaseDocument.expiry_date <= datetime.utcnow(),
                        KnowledgeBaseDocument.status == "approved"
                    )
                )
            )
            
            expired_docs = result.scalars().all()
            deactivated_ids = []
            
            for doc in expired_docs:
                doc.status = "expired"
                doc.deactivated_at = datetime.utcnow()
                deactivated_ids.append(str(doc.id))
                
                # Create audit record
                audit = KnowledgeBaseWorkflowAudit(
                    document_id=str(doc.id),
                    action="deactivated",
                    performed_by="system",
                    comments="Document expired and deactivated",
                    timestamp=datetime.utcnow()
                )
                db.add(audit)
            
            await db.commit()
            
            return {
                "success": True,
                "message": f"Deactivated {len(deactivated_ids)} expired documents",
                "deactivated_ids": deactivated_ids,
                "count": len(deactivated_ids)
            }
            
        except Exception as e:
            logger.error(f"Error deactivating expired documents: {e}")
            await db.rollback()
            return {"error": "Failed to deactivate expired documents"}
