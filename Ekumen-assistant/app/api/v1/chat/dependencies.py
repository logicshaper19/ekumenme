"""
Chat API dependencies
Shared dependency functions for chat endpoints
"""

from typing import Optional
from fastapi import Depends
from app.services.auth_service import AuthService, oauth2_scheme
import logging

logger = logging.getLogger(__name__)

auth_service = AuthService()

async def get_org_id_from_token(token: str = Depends(oauth2_scheme)) -> Optional[str]:
    """
    Extract organization ID from JWT token
    Dependency function to avoid code duplication across chat endpoints
    """
    try:
        token_data = auth_service.verify_token(token)
        return str(token_data.org_id) if token_data and token_data.org_id else None
    except Exception as e:
        logger.error(f"Error extracting org_id from token: {e}")
        return None
