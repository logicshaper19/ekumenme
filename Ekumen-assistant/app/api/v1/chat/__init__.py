"""
Chat API module
Aggregates all chat-related routers into a single module
"""

from fastapi import APIRouter

from .conversations import router as conversations_router
from .messages import router as messages_router
from .streaming import router as streaming_router
from .websocket import router as websocket_router
from .performance import router as performance_router

# Main router for chat API
router = APIRouter(prefix="/chat", tags=["Chat"])

# Include all sub-routers
router.include_router(conversations_router)
router.include_router(messages_router)
router.include_router(streaming_router)
router.include_router(websocket_router)
router.include_router(performance_router)
