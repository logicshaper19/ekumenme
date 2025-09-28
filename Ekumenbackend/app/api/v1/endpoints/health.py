"""
Health check endpoints.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
import time

router = APIRouter()


@router.get("/")
async def health_check():
    """Basic health check."""
    return {
        "status": "healthy",
        "version": settings.app_version,
        "timestamp": time.time(),
    }


@router.get("/detailed")
async def detailed_health_check(db: Session = Depends(get_db)):
    """Detailed health check with database connectivity."""
    try:
        # Test database connection
        db.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    return {
        "status": "healthy" if db_status == "healthy" else "unhealthy",
        "version": settings.app_version,
        "timestamp": time.time(),
        "database": db_status,
        "debug": settings.debug,
    }
