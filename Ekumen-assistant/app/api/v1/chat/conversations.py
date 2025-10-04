"""
Conversation management endpoints
Handles conversation CRUD operations and agent listing
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import logging

from app.core.database import get_async_db
from app.models.user import User
from app.schemas.chat import ConversationCreate, ConversationResponse, ConversationUpdate
from app.services.shared.auth_service import AuthService
from app.services.shared.chat_service import ChatService
from app.services.infrastructure.agent_service import AgentService

from .dependencies import get_org_id_from_token

logger = logging.getLogger(__name__)

router = APIRouter()
auth_service = AuthService()
chat_service = ChatService()
agent_service = AgentService()

@router.post("/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conversation_data: ConversationCreate,
    current_user: User = Depends(auth_service.get_current_user),
    org_id: Optional[str] = Depends(get_org_id_from_token),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Create a new conversation with an agricultural agent

    Args:
        conversation_data: Conversation creation data
        current_user: Current authenticated user
        db: Database session

    Returns:
        ConversationResponse: Created conversation information
    """
    try:
        if not org_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Organization not selected. Call /api/v1/auth/organizations and /api/v1/auth/select-organization first.")
        conversation = await chat_service.create_conversation(
            db=db,
            user_id=current_user.id,
            agent_type=getattr(conversation_data, 'agent_type', None),
            organization_id=org_id,
            farm_siret=conversation_data.farm_siret,
            title=conversation_data.title
        )

        logger.info(f"New conversation created: {conversation.id} for user {current_user.email}")

        return ConversationResponse(
            id=str(conversation.id),  # Convert UUID to string explicitly
            title=conversation.title,
            agent_type=conversation.agent_type,
            farm_siret=conversation.farm_siret,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Conversation creation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create conversation"
        )

@router.patch("/conversations/{conversation_id}", response_model=ConversationResponse)
async def update_conversation(
    conversation_id: str,
    update: ConversationUpdate,
    current_user: User = Depends(auth_service.get_current_user),
    org_id: Optional[str] = Depends(get_org_id_from_token),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Update an existing conversation

    Args:
        conversation_id: ID of the conversation to update
        update: Update data
        current_user: Current authenticated user
        db: Database session

    Returns:
        ConversationResponse: Updated conversation information
    """
    try:
        if not org_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Organization not selected.")
        
        conversation = await chat_service.update_conversation(
            db=db,
            conversation_id=conversation_id,
            user_id=current_user.id,
            organization_id=org_id,
            update_data=update
        )

        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )

        return ConversationResponse(
            id=str(conversation.id),
            title=conversation.title,
            agent_type=conversation.agent_type,
            farm_siret=conversation.farm_siret,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Conversation update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update conversation"
        )

@router.get("/conversations/search", response_model=List[ConversationResponse])
async def search_conversations(
    query: str,
    current_user: User = Depends(auth_service.get_current_user),
    org_id: Optional[str] = Depends(get_org_id_from_token),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Search conversations by title or content

    Args:
        query: Search query
        current_user: Current authenticated user
        db: Database session

    Returns:
        List[ConversationResponse]: Matching conversations
    """
    try:
        if not org_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Organization not selected.")
        
        conversations = await chat_service.search_conversations(
            db=db,
            user_id=current_user.id,
            organization_id=org_id,
            query=query
        )

        return [
            ConversationResponse(
                id=str(conv.id),
                title=conv.title,
                agent_type=conv.agent_type,
                farm_siret=conv.farm_siret,
                created_at=conv.created_at,
                updated_at=conv.updated_at
            )
            for conv in conversations
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Conversation search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to search conversations"
        )

@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(auth_service.get_current_user),
    org_id: Optional[str] = Depends(get_org_id_from_token),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Delete a conversation

    Args:
        conversation_id: ID of the conversation to delete
        current_user: Current authenticated user
        db: Database session
    """
    try:
        if not org_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Organization not selected.")
        
        success = await chat_service.delete_conversation(
            db=db,
            conversation_id=conversation_id,
            user_id=current_user.id,
            organization_id=org_id
        )

        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Conversation deletion error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete conversation"
        )

@router.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(auth_service.get_current_user),
    org_id: Optional[str] = Depends(get_org_id_from_token),
    db: AsyncSession = Depends(get_async_db)
):
    """
    List conversations for the current user

    Args:
        skip: Number of conversations to skip
        limit: Maximum number of conversations to return
        current_user: Current authenticated user
        db: Database session

    Returns:
        List[ConversationResponse]: User's conversations
    """
    try:
        if not org_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Organization not selected.")
        
        conversations = await chat_service.get_user_conversations(
            db=db,
            user_id=current_user.id,
            organization_id=org_id,
            skip=skip,
            limit=limit
        )

        return [
            ConversationResponse(
                id=str(conv.id),
                title=conv.title,
                agent_type=conv.agent_type,
                farm_siret=conv.farm_siret,
                created_at=conv.created_at,
                updated_at=conv.updated_at
            )
            for conv in conversations
        ]

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Conversation listing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list conversations"
        )

@router.get("/agents")
async def get_available_agents(
    current_user: User = Depends(auth_service.get_current_user)
):
    """
    Get list of available agricultural AI agents

    Args:
        current_user: Current authenticated user

    Returns:
        List[dict]: Available agents with their descriptions
    """
    try:
        agents = chat_service.get_available_agents()

        return {
            "agents": agents,
            "count": len(agents)
        }

    except Exception as e:
        logger.error(f"Error getting available agents: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve available agents"
        )
