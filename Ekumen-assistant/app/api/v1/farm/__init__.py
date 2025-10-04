"""
Farm Data API module
Provides endpoints for accessing farm data (parcelles, interventions, exploitations)
"""

from fastapi import APIRouter

from .parcelles import router as parcelles_router
from .interventions import router as interventions_router
from .exploitation import router as exploitation_router
from .dashboard import router as dashboard_router
from .websocket import router as websocket_router

# Main router for farm API
router = APIRouter(prefix="/farm", tags=["Farm Data"])

# Include all sub-routers
router.include_router(parcelles_router)
router.include_router(interventions_router)
router.include_router(exploitation_router)
router.include_router(dashboard_router)
router.include_router(websocket_router)
