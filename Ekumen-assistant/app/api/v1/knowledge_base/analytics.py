"""
Production analytics endpoints for the Knowledge Base API
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.models.user import User
from app.services.auth_service import AuthService
from app.services.analytics_service import AnalyticsService
from app.api.v1.knowledge_base.dependencies import require_user_organization
from app.api.v1.knowledge_base.schemas import StandardErrorResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["Knowledge Base - Analytics"])

# Initialize services
auth_service = AuthService()
analytics_service = AnalyticsService()

@router.get("/document/{document_id}", response_model=Dict[str, Any])
async def get_document_analytics(
    document_id: str,
    period_days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get analytics for a specific document
    """
    try:
        analytics_data = await analytics_service.get_document_analytics(
            document_id=document_id,
            db=db,
            period_days=period_days
        )
        
        if "error" in analytics_data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=analytics_data["error"]
            )
        
        return analytics_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve document analytics"
        )

@router.post("/source-attribution", response_model=Dict[str, Any])
async def get_source_attribution(
    request: Dict[str, str],
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get detailed source attribution for a query
    Shows exactly which text/pages/sections were used to answer a question
    """
    try:
        query = request.get("query")
        if not query:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Query is required"
            )
        
        # Get user's organization using reusable function
        organization_id = await require_user_organization(current_user, db)
        
        # Get relevant documents using RAG service
        from app.services.rag_service import RAGService
        rag_service = RAGService()
        
        # Search for relevant documents
        search_results = await rag_service.get_relevant_documents(
            query=query,
            user_id=str(current_user.id),
            organization_id=organization_id,
            db=db,
            k=5  # Limit to top 5 most relevant sources
        )
        
        if not search_results:
            return StandardErrorResponse.create_success_response(
                data={
                    "query": query,
                    "sources": [],
                    "total_sources": 0
                },
                message="No relevant documents found for this query"
            )
        
        # Get detailed source attribution
        attribution_data = await rag_service.get_detailed_source_attribution(
            query=query,
            documents=search_results,
            db=db
        )
        
        return attribution_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting source attribution: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve source attribution"
        )

@router.get("/overview", response_model=Dict[str, Any])
async def get_knowledge_base_overview(
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get overview analytics for the knowledge base
    """
    try:
        # Get user's organization using reusable function
        organization_id = await require_user_organization(current_user, db)
        
        overview_data = await analytics_service.get_knowledge_base_overview(
            organization_id=organization_id,
            db=db
        )
        
        if "error" in overview_data:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=overview_data["error"]
            )
        
        return overview_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting knowledge base overview: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve knowledge base overview"
        )

@router.get("/document/{document_id}/chunks", response_model=Dict[str, Any])
async def get_document_chunk_analytics(
    document_id: str,
    period_days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get chunk-level analytics for a specific document
    Shows which chunks are most frequently accessed and their performance
    """
    try:
        from app.services.rag_service import RAGService
        
        rag_service = RAGService()
        
        chunk_analytics = await rag_service.get_chunk_analytics(
            document_id=document_id,
            db=db,
            period_days=period_days
        )
        
        if "error" in chunk_analytics:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=chunk_analytics["error"]
            )
        
        return chunk_analytics
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting document chunk analytics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve document chunk analytics"
        )
