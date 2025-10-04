"""
Knowledge Base API Router Aggregation
Smart dev router registration - only includes dev endpoints in development mode
"""

from fastapi import APIRouter

from .documents import router as documents_router
from .admin import router as admin_router
from .analytics import router as analytics_router

# Import dev router and environment check
from .dev import router as dev_router
from app.core.rate_limiting import is_development_mode

# Create main router
main_router = APIRouter(prefix="/knowledge-base", tags=["Knowledge Base"])

# Include production routers
main_router.include_router(documents_router)
main_router.include_router(admin_router)
main_router.include_router(analytics_router)

# Only include dev router in development mode
if is_development_mode():
    main_router.include_router(dev_router)

# Export the main router
router = main_router
