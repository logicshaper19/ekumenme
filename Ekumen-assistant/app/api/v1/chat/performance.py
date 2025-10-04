"""
Performance monitoring endpoints
Handles performance statistics and cache management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from app.models.user import User
from app.services.auth_service import AuthService
from app.services.optimized_streaming_service import OptimizedStreamingService
from app.services.shared.tool_registry_service import get_tool_registry
from app.api.v1.knowledge_base.schemas import StandardErrorResponse
import logging

logger = logging.getLogger(__name__)

router = APIRouter()
auth_service = AuthService()

# Initialize optimized streaming service for performance endpoints
tool_registry = get_tool_registry()
streaming_service = OptimizedStreamingService(tool_executor=tool_registry)

@router.get("/performance/stats")
async def get_performance_stats(
    current_user: User = Depends(auth_service.get_current_user)
):
    """
    Get performance statistics from optimized services.
    
    Returns:
        Performance metrics including:
        - Average query time
        - Cache hit rate
        - LLM usage statistics
        - Cost savings
    """
    try:
        stats = streaming_service.get_performance_stats()
        
        return StandardErrorResponse.create_success_response(
            data={"stats": stats},
            message="Performance statistics retrieved successfully"
        )
        
    except Exception as e:
        logger.error(f"Stats retrieval error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve performance stats"
        )

@router.post("/performance/clear-cache")
async def clear_performance_cache(
    current_user: User = Depends(auth_service.get_current_user)
):
    """
    Clear performance cache (admin only).
    
    This will clear all cached responses, forcing fresh computation.
    """
    try:
        # Check if user has admin privileges
        if not hasattr(current_user, 'is_superuser') or not current_user.is_superuser:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, 
                detail="Admin access required"
            )
        
        # Clear cache
        streaming_service.cache.clear_all()
        
        return StandardErrorResponse.create_success_response(
            message="Cache cleared successfully"
        )
        
    except Exception as e:
        logger.error(f"Cache clear error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clear cache"
        )
