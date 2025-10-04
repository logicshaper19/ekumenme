"""
Knowledge Base Workflow Service
Handles document workflow operations like approval, rejection, and renewal
"""

import logging
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.orm import selectinload

from app.models.knowledge_base import KnowledgeBaseDocument, KnowledgeBaseWorkflowAudit, DocumentStatus
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
        Approve a document after human review and add to ChromaDB
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
            document.submission_status = "approved"
            document.approved_by = approved_by
            document.approved_at = datetime.utcnow()
            document.processing_status = DocumentStatus.PROCESSING
            
            await db.commit()
            
            # Process document and add to ChromaDB
            try:
                from app.services.knowledge_base.rag_service import RAGService
                from app.services.knowledge_base.document_processing_service import DocumentProcessingService
                
                rag_service = RAGService()
                processing_service = DocumentProcessingService()
                
                # Extract text content from the file
                content = await processing_service.extract_text_from_file(
                    document.file_path,
                    document.file_type,
                    document.filename
                )
                
                # Add to vector store
                success = await rag_service.add_document_to_vectorstore(document, content, db)
                
                if success:
                    document.processing_status = DocumentStatus.COMPLETED
                    logger.info(f"Document {document_id} added to ChromaDB successfully")
                else:
                    document.processing_status = DocumentStatus.FAILED
                    logger.error(f"Failed to add document {document_id} to ChromaDB")
                
                await db.commit()
                
            except Exception as e:
                logger.error(f"Error processing document for ChromaDB: {e}")
                document.processing_status = DocumentStatus.FAILED
                await db.commit()
            
            # Create audit record
            audit = KnowledgeBaseWorkflowAudit(
                document_id=document_id,
                action="approved",
                performed_by=approved_by,
                comments=comments or "Document approved and added to knowledge base",
                performed_at=datetime.utcnow()
            )
            db.add(audit)
            
            await db.commit()
            
            return {
                "success": True,
                "message": "Document approved successfully",
                "document_id": document_id,
                "processing_status": document.processing_status.value
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
        organization_id: str,
        uploaded_by: str,
        file,
        filename: str,
        file_type: str,
        document_type,
        description: Optional[str] = None,
        tags: Optional[List[str]] = None,
        expiration_months: Optional[int] = None,
        visibility: str = "internal",
        shared_with_organizations: Optional[List[str]] = None,
        shared_with_users: Optional[List[str]] = None,
        db: AsyncSession = None
    ) -> Dict[str, Any]:
        """
        Submit a new document for review with content-based file storage
        """
        try:
            from app.services.knowledge_base.supabase_storage_service import create_storage_service
            
            # Initialize file storage service (Supabase for production, local for dev)
            file_storage = create_storage_service()
            
            # Save file with content-based hashing
            save_result = await file_storage.save_file(
                file=file,
                organization_id=organization_id,
                user_id=uploaded_by,
                db=db
            )
            
            # Handle validation errors
            if save_result["status"] == "validation_error":
                return {
                    "success": False,
                    "error": "validation_error",
                    "error_code": save_result.get("error_code", "VALIDATION_ERROR"),
                    "message": save_result["message"]
                }
            
            # Handle duplicate files
            if save_result["status"] == "duplicate":
                return {
                    "success": False,
                    "error": "duplicate_file",
                    "message": save_result["message"],
                    "existing_document_id": save_result["document_id"],
                    "existing_filename": save_result["existing_filename"],
                    "uploaded_at": save_result.get("uploaded_at")
                }
            
            # Handle save errors
            if save_result["status"] == "error":
                return {
                    "success": False,
                    "error": "file_save_error",
                    "error_code": save_result.get("error_code", "FILE_SAVE_ERROR"),
                    "message": save_result["message"]
                }
            
            # Calculate expiration date if provided
            expiration_date = None
            if expiration_months:
                expiration_date = datetime.utcnow() + timedelta(days=expiration_months * 30)
            
            # Create document record
            document = KnowledgeBaseDocument(
                id=uuid.uuid4(),
                organization_id=organization_id,
                uploaded_by=uploaded_by,
                filename=filename,  # Original filename preserved
                file_path=save_result["file_path"],
                file_type=file_type,
                file_size_bytes=save_result["file_size"],
                file_hash=save_result["file_hash"],  # Hash for per-org duplicate detection
                document_type=document_type,
                description=description,
                tags=tags or [],
                visibility=visibility,
                shared_with_organizations=shared_with_organizations or [],
                shared_with_users=shared_with_users or [],
                processing_status="pending",
                submission_status="pending",
                expiration_date=expiration_date,
                workflow_metadata={
                    "submitted_at": datetime.utcnow().isoformat(),
                    "original_filename": filename,
                    "file_hash": save_result["file_hash"],
                    "storage_method": "simple_per_org_hash"
                }
            )
            
            db.add(document)
            await db.commit()
            await db.refresh(document)
            
            # Create audit record
            audit = KnowledgeBaseWorkflowAudit(
                document_id=str(document.id),
                action="submitted",
                performed_by=uploaded_by,
                comments="Document submitted for review",
                performed_at=datetime.utcnow()
            )
            db.add(audit)
            await db.commit()
            
            logger.info(f"Document submitted successfully: {document.id} (hash: {save_result['file_hash'][:8]}...)")
            
            return {
                "success": True,
                "message": "Document submitted successfully",
                "document_id": str(document.id),
                "filename": filename,
                "file_size": save_result["file_size"],
                "file_hash": save_result["file_hash"]
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
