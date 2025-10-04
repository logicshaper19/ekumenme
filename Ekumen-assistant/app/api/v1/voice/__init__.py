"""
Voice API module
"""

from .websocket import router as voice_websocket_router

__all__ = ["voice_websocket_router"]
