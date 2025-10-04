"""
Message management endpoints
Handles message operations and citations
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import logging

from app.core.database import get_async_db
from app.models.user import User
from app.schemas.chat import ChatMessage, ChatResponse
from app.services.shared.auth_service import AuthService
from app.services.shared.chat_service import ChatService

from .dependencies import get_org_id_from_token
from .schemas import PaginatedMessagesResponse

logger = logging.getLogger(__name__)

router = APIRouter()
auth_service = AuthService()
chat_service = ChatService()

@router.post("/conversations/{conversation_id}/messages", response_model=ChatResponse)
async def send_message(
    conversation_id: str,
    message: ChatMessage,
    current_user: User = Depends(auth_service.get_current_user),
    org_id: Optional[str] = Depends(get_org_id_from_token),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Send a message in a conversation

    Args:
        conversation_id: ID of the conversation
        message: Message content
        current_user: Current authenticated user
        db: Database session

    Returns:
        ChatResponse: Response from the AI agent
    """
    try:
        if not org_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Organization not selected.")
        
        # Verify conversation belongs to user
        conversation = await chat_service.get_conversation(
            db=db,
            conversation_id=conversation_id,
            user_id=current_user.id,
            organization_id=org_id
        )
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )

        # Save user message
        user_message = await chat_service.save_message(
            db=db,
            conversation_id=conversation_id,
            content=message.content,
            sender="user",
            agent_type=conversation.agent_type,
            message_type="text"
        )

        # Get AI response
        response = await chat_service.get_ai_response(
            db=db,
            conversation_id=conversation_id,
            user_message=message.content,
            agent_type=conversation.agent_type,
            organization_id=org_id
        )

        return ChatResponse(
            message=response,
            conversation_id=conversation_id,
            message_id=str(user_message.id)
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Message sending error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to send message"
        )

@router.get("/conversations/{conversation_id}/messages", response_model=PaginatedMessagesResponse)
async def get_conversation_messages(
    conversation_id: str,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(auth_service.get_current_user),
    org_id: Optional[str] = Depends(get_org_id_from_token),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get messages for a conversation
    """
    try:
        if not org_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Organization not selected.")
        conversation = await chat_service.get_conversation(
            db=db,
            conversation_id=conversation_id,
            user_id=current_user.id,
            organization_id=org_id
        )
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )

        # Get messages and total count
        messages = await chat_service.get_conversation_messages(
            db=db,
            conversation_id=conversation_id,
            skip=skip,
            limit=limit
        )
        
        # Get total count for pagination
        total_count = await chat_service.get_conversation_message_count(
            db=db,
            conversation_id=conversation_id
        )

        # Convert to response format
        message_items = [
            ChatMessage(
                content=msg.content,
                sender=msg.sender,
                timestamp=msg.created_at
            )
            for msg in messages
        ]

        return PaginatedMessagesResponse(
            items=message_items,
            total=total_count,
            skip=skip,
            limit=limit,
            has_more=(skip + len(messages)) < total_count
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get messages error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve messages"
        )

@router.get("/messages/{message_id}/citations")
async def get_message_citations(
    message_id: str,
    current_user: User = Depends(auth_service.get_current_user),
    org_id: Optional[str] = Depends(get_org_id_from_token),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get citations/sources for a message if available in message_metadata.documents_retrieved
    """
    try:
        if not org_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Organization not selected.")
        
        message = await chat_service.get_message_by_id(
            db=db,
            message_id=message_id,
            user_id=current_user.id,
            organization_id=org_id
        )
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )

        metadata = message.message_metadata or {}
        citations = metadata.get("documents_retrieved") or []
        return {"message_id": str(message.id), "citations": citations}

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get citations error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get citations")
