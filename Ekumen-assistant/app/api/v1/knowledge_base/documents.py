"""
Document operations and workflow endpoints for the Knowledge Base API
"""

import logging
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_

from app.core.database import get_async_db
from app.models.user import User
from app.models.knowledge_base import DocumentType
from app.services.knowledge_base import KnowledgeBaseWorkflowService
from app.services.shared import AuthService
from app.core.validation import validate_file_upload
from app.core.rate_limiting import check_rate_limit
from app.api.v1.knowledge_base.dependencies import require_user_organization
from app.api.v1.knowledge_base.schemas import (
    StandardErrorResponse, 
    PaginatedResponse, 
    create_paginated_response
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Knowledge Base - Documents"])

# Initialize services
auth_service = AuthService()
workflow_service = KnowledgeBaseWorkflowService()

@router.get("/search", response_model=List[Dict[str, Any]])
async def search_knowledge_base(
    query: str = Query(..., description="Search query"),
    document_type: Optional[str] = Query(None, description="Filter by document type"),
    limit: int = Query(10, ge=1, le=50, description="Number of results to return"),
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Search knowledge base with full user access
    Returns public, shared, and organization-specific content
    """
    try:
        from app.services.knowledge_base import RAGService
        
        rag_service = RAGService()
        
        # Get user's organization using reusable function
        user_org = await require_user_organization(current_user, db)
        
        # Get relevant documents with full user access
        documents = await rag_service.get_relevant_documents(
            query=query,
            user_id=str(current_user.id),
            organization_id=str(user_org),
            db=db,
            k=limit,
            include_ekumen_content=True
        )
        
        # Format response
        results = []
        for doc in documents:
            results.append({
                "content": doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content,
                "filename": doc.metadata.get("filename"),
                "document_type": doc.metadata.get("document_type"),
                "description": doc.metadata.get("description"),
                "tags": doc.metadata.get("tags", []),
                "is_ekumen_provided": doc.metadata.get("is_ekumen_provided", False),
                "version": doc.metadata.get("version", 1),
                "quality_score": doc.metadata.get("quality_score"),
                "organization_id": doc.metadata.get("organization_id"),
                "visibility": "public" if doc.metadata.get("is_ekumen_provided") else "shared"
            })
        
        return results
        
    except Exception as e:
        logger.error(f"Error in knowledge base search: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search knowledge base"
        )

@router.get("/documents", response_model=PaginatedResponse)
async def list_user_documents(
    document_type: Optional[str] = Query(None, description="Filter by document type"),
    visibility: Optional[str] = Query(None, description="Filter by visibility"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Number of records per page"),
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    List documents accessible to the current user with proper pagination
    """
    try:
        from app.models.organization import OrganizationMembership
        from app.models.knowledge_base import KnowledgeBaseDocument
        
        # Get user's organization using reusable function
        user_org = await require_user_organization(current_user, db)
        
        # Calculate skip value
        skip = (page - 1) * per_page
        
        # Build query with filters
        query = select(KnowledgeBaseDocument).where(
            KnowledgeBaseDocument.organization_id == str(user_org)
        )
        
        # Add filters
        conditions = []
        if document_type:
            conditions.append(KnowledgeBaseDocument.document_type == document_type)
        if visibility:
            conditions.append(KnowledgeBaseDocument.visibility == visibility)
        
        if conditions:
            query = query.where(and_(*conditions))
        
        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Get paginated results
        query = query.offset(skip).limit(per_page).order_by(KnowledgeBaseDocument.created_at.desc())
        result = await db.execute(query)
        documents = result.scalars().all()
        
        # Format response
        items = []
        for doc in documents:
            items.append({
                "id": str(doc.id),
                "filename": doc.filename,
                "document_type": doc.document_type.value if doc.document_type else "other",
                "description": doc.description or "",
                "tags": doc.tags or [],
                "visibility": doc.visibility or "internal",
                "status": doc.submission_status or "pending",
                "uploaded_by": str(doc.uploaded_by),
                "created_at": doc.created_at.isoformat() if doc.created_at else None,
                "file_size": doc.file_size_bytes or 0,
                "quality_score": doc.quality_score or 0.0,
                "version": doc.version or 1,
                "expiration_date": doc.expiration_date.isoformat() if doc.expiration_date else None
            })
        
        return create_paginated_response(items, total, page, per_page)
        
    except Exception as e:
        logger.error(f"Error listing user documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve documents"
        )

@router.post("/submit", response_model=Dict[str, Any])
async def submit_document(
    file: UploadFile = File(...),
    document_type: str = Form(...),
    description: Optional[str] = Form(None),
    tags: Optional[str] = Form(None),  # JSON string
    expiration_months: Optional[int] = Form(None),
    visibility: str = Form("internal"),
    shared_with_organizations: Optional[str] = Form(None),  # JSON string
    shared_with_users: Optional[str] = Form(None),  # JSON string
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_async_db),
    request: Request = None
):
    """
    Step 1: Document Submission Portal
    Submit a document for knowledge base contribution
    """
    try:
        # RATE LIMITING: Check upload rate limits
        if request:
            check_rate_limit(request, current_user, limit=5, window_seconds=300)  # 5 uploads per 5 minutes
        
        # SECURITY: Validate file upload
        validate_file_upload(file)
        
        # Validate document type
        try:
            doc_type = DocumentType(document_type)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid document type: {document_type}"
            )
        
        # Parse tags
        tag_list = []
        if tags:
            try:
                import json
                tag_list = json.loads(tags)
            except json.JSONDecodeError:
                # Fallback to comma-separated parsing
                tag_list = [tag.strip() for tag in tags.split(",") if tag.strip()]
        
        # Parse shared organizations
        shared_orgs = []
        if shared_with_organizations:
            try:
                import json
                shared_orgs = json.loads(shared_with_organizations)
            except json.JSONDecodeError:
                shared_orgs = [org.strip() for org in shared_with_organizations.split(",") if org.strip()]
        
        # Parse shared users
        shared_users = []
        if shared_with_users:
            try:
                import json
                shared_users = json.loads(shared_with_users)
            except json.JSONDecodeError:
                shared_users = [user.strip() for user in shared_with_users.split(",") if user.strip()]
        
        # Validate visibility
        if visibility not in ["internal", "shared", "public"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Visibility must be one of: internal, shared, public"
            )
        
        # Get user's organization using reusable function
        user_org = await require_user_organization(current_user, db)
        
        # Submit document
        result = await workflow_service.submit_document(
            organization_id=str(user_org),
            uploaded_by=str(current_user.id),
            file=file,
            filename=file.filename,
            file_type=file.filename.split('.')[-1].lower() if '.' in file.filename else '',
            document_type=doc_type,
            description=description,
            tags=tag_list,
            expiration_months=expiration_months,
            visibility=visibility,
            shared_with_organizations=shared_orgs,
            shared_with_users=shared_users,
            db=db
        )
        
        # Handle validation errors
        if not result.get("success") and result.get("error") == "validation_error":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": "validation_error",
                    "error_code": result.get("error_code", "VALIDATION_ERROR"),
                    "message": result["message"]
                }
            )
        
        # Handle duplicate file response
        if not result.get("success") and result.get("error") == "duplicate_file":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "duplicate_file",
                    "message": result["message"],
                    "existing_document_id": result["existing_document_id"],
                    "existing_filename": result["existing_filename"],
                    "uploaded_at": result.get("uploaded_at")
                }
            )
        
        # Handle file save errors
        if not result.get("success") and result.get("error") == "file_save_error":
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail={
                    "error": "file_save_error",
                    "error_code": result.get("error_code", "FILE_SAVE_ERROR"),
                    "message": result["message"]
                }
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to submit document"
        )

@router.get("/submissions", response_model=List[Dict[str, Any]])
async def list_submissions(
    status_filter: Optional[str] = Query(None, description="Filter by submission status"),
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    List document submissions for the current user's organization
    """
    try:
        from app.models.knowledge_base import KnowledgeBaseDocument
        from sqlalchemy import select, and_
        
        # Get user's organization using reusable function
        user_org = await require_user_organization(current_user, db)
        
        # Build query
        query = select(KnowledgeBaseDocument).where(
            KnowledgeBaseDocument.organization_id == user_org
        )
        
        if status_filter:
            # Filter by submission status in metadata
            query = query.where(
                KnowledgeBaseDocument.organization_metadata['submission_status'].astext == status_filter
            )
        
        # Apply pagination
        query = query.order_by(KnowledgeBaseDocument.created_at.desc()).limit(50)
        
        result = await db.execute(query)
        documents = result.scalars().all()
        
        # Format response
        submissions = []
        for doc in documents:
            metadata = doc.organization_metadata or {}
            submissions.append({
                "id": str(doc.id),
                "filename": doc.filename,
                "document_type": doc.document_type.value if doc.document_type else "other",
                "description": doc.description or "",
                "status": metadata.get("submission_status", "pending"),
                "uploaded_by": str(doc.uploaded_by),
                "created_at": doc.created_at.isoformat() if doc.created_at else None,
                "file_size": doc.file_size_bytes or 0,
                "quality_score": doc.quality_score or 0.0,
                "version": doc.version or 1
            })
        
        return submissions
        
    except Exception as e:
        logger.error(f"Error listing submissions: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve submissions"
        )

@router.post("/renew/{document_id}")
async def renew_document(
    document_id: str,
    months: int = Form(12, ge=1, le=60),
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Renew a document's expiration date
    """
    try:
        result = await workflow_service.renew_document(
            document_id=document_id,
            months=months,
            user_id=str(current_user.id),
            db=db
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error renewing document: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to renew document"
        )

@router.get("/expiring", response_model=List[Dict[str, Any]])
async def list_expiring_documents(
    days_ahead: int = Query(90, ge=1, le=365, description="Number of days ahead to check"),
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    List documents expiring soon for the current user's organization
    """
    try:
        from app.models.knowledge_base import KnowledgeBaseDocument
        from sqlalchemy import select, and_, func
        from datetime import datetime, timedelta
        
        # Get user's organization using reusable function
        user_org = await require_user_organization(current_user, db)
        
        # Find documents expiring in the next 90 days
        future_date = datetime.utcnow() + timedelta(days=days_ahead)
        
        query = select(KnowledgeBaseDocument).where(
            and_(
                KnowledgeBaseDocument.organization_id == user_org,
                KnowledgeBaseDocument.processing_status == "completed",
                KnowledgeBaseDocument.visibility == "shared",
                func.json_extract_path_text(
                    KnowledgeBaseDocument.organization_metadata, 
                    'expiration_date'
                ).cast(func.date) <= future_date.date()
            )
        )
        
        result = await db.execute(query)
        documents = result.scalars().all()
        
        # Format response
        expiring_docs = []
        for doc in documents:
            metadata = doc.organization_metadata or {}
            expiration_date = datetime.fromisoformat(metadata.get("expiration_date", ""))
            days_remaining = (expiration_date.date() - datetime.utcnow().date()).days
            
            expiring_docs.append({
                "id": str(doc.id),
                "filename": doc.filename,
                "document_type": doc.document_type.value if doc.document_type else "other",
                "description": doc.description or "",
                "expiration_date": expiration_date.isoformat(),
                "days_remaining": days_remaining,
                "uploaded_by": str(doc.uploaded_by),
                "created_at": doc.created_at.isoformat() if doc.created_at else None,
                "quality_score": doc.quality_score or 0.0,
                "version": doc.version or 1
            })
        
        return expiring_docs
        
    except Exception as e:
        logger.error(f"Error listing expiring documents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve expiring documents"
        )
