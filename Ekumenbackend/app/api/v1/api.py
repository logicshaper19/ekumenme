"""
API router configuration.
"""

from fastapi import APIRouter
from app.api.v1.endpoints import (
    exploitations,
    parcelles,
    interventions,
    compliance,
    tasks,
    ephy,
    health,
)

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(exploitations.router, prefix="/exploitations", tags=["exploitations"])
api_router.include_router(parcelles.router, prefix="/parcelles", tags=["parcelles"])
api_router.include_router(interventions.router, prefix="/interventions", tags=["interventions"])
api_router.include_router(compliance.router, prefix="/compliance", tags=["compliance"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
api_router.include_router(ephy.router, prefix="/ephy", tags=["ephy"])
