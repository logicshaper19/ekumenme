"""
Chat API schemas
Pydantic models and response classes for chat endpoints
"""

from pydantic import BaseModel
from typing import List
from app.schemas.chat import ChatMessage

class PaginatedMessagesResponse(BaseModel):
    """Paginated response format for message listings"""
    items: List[ChatMessage]
    total: int
    skip: int
    limit: int
    has_more: bool
