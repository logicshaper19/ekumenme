"""
Development endpoints for the Knowledge Base API
These endpoints are only available in development mode
"""

import logging
from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_db
from app.core.rate_limiting import is_development_mode
from app.api.v1.knowledge_base.schemas import StandardErrorResponse
from app.services.farm_data.analytics_service import AnalyticsService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/analytics", tags=["Knowledge Base - Development"])

# Initialize services
analytics_service = AnalyticsService()

@router.post("/source-attribution-dev", response_model=Dict[str, Any])
async def get_source_attribution_dev(
    request: Dict[str, str],
    db: AsyncSession = Depends(get_async_db)
):
    """
    Development fallback for source attribution without authentication
    SECURITY: Only available in development mode
    """
    # SECURITY CHECK: Only allow in development mode
    if not is_development_mode():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Development endpoints are not available in production"
        )
    
    try:
        query = request.get("query")
        if not query:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Query is required"
            )
        
        # Use mock user and organization for dev
        mock_user_id = "7e7f983c-ec79-4916-9253-29eba33931cb"
        mock_organization_id = "48359c04-d103-4cdd-b165-502ceefda04a"
        
        # Get relevant documents using RAG service
        from app.services.knowledge_base.rag_service import RAGService
        rag_service = RAGService()
        
        # Search for relevant documents
        search_results = await rag_service.get_relevant_documents(
            query=query,
            user_id=mock_user_id,
            organization_id=mock_organization_id,
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
        logger.error(f"Error getting dev source attribution: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dev source attribution"
        )

@router.get("/overview-dev", response_model=Dict[str, Any])
async def get_knowledge_base_overview_dev(
    db: AsyncSession = Depends(get_async_db)
):
    """
    Development fallback for getting knowledge base overview without authentication
    SECURITY: Only available in development mode
    """
    # SECURITY CHECK: Only allow in development mode
    if not is_development_mode():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Development endpoints are not available in production"
        )
    
    try:
        overview_data = await analytics_service.get_knowledge_base_overview(
            organization_id=None,  # Get all documents for dev
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
