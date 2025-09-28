"""
Chat API endpoints
Handles conversations with agricultural AI agents
"""

from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import logging
import json

from app.core.database import get_async_db
from app.models.user import User
from app.schemas.chat import ChatMessage, ChatResponse, ConversationCreate, ConversationResponse
from app.services.auth_service import AuthService
from app.services.chat_service import ChatService
from app.services.agent_service import AgentService

logger = logging.getLogger(__name__)

router = APIRouter()
auth_service = AuthService()
chat_service = ChatService()
agent_service = AgentService()

@router.post("/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    conversation_data: ConversationCreate,
    current_user: User = Depends(auth_service.get_current_user),
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
        conversation = await chat_service.create_conversation(
            db=db,
            user_id=current_user.id,
            agent_type=conversation_data.agent_type,
            farm_siret=conversation_data.farm_siret,
            title=conversation_data.title
        )
        
        logger.info(f"New conversation created: {conversation.id} for user {current_user.email}")
        
        return ConversationResponse(
            id=conversation.id,
            title=conversation.title,
            agent_type=conversation.agent_type,
            farm_siret=conversation.farm_siret,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at
        )
        
    except Exception as e:
        logger.error(f"Conversation creation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create conversation"
        )

@router.get("/conversations", response_model=List[ConversationResponse])
async def get_user_conversations(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get user's conversations
    
    Args:
        skip: Number of conversations to skip
        limit: Maximum number of conversations to return
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List[ConversationResponse]: User's conversations
    """
    try:
        conversations = await chat_service.get_user_conversations(
            db=db,
            user_id=current_user.id,
            skip=skip,
            limit=limit
        )
        
        return [
            ConversationResponse(
                id=conv.id,
                title=conv.title,
                agent_type=conv.agent_type,
                farm_siret=conv.farm_siret,
                created_at=conv.created_at,
                updated_at=conv.updated_at
            )
            for conv in conversations
        ]
        
    except Exception as e:
        logger.error(f"Get conversations error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve conversations"
        )

@router.post("/conversations/{conversation_id}/messages", response_model=ChatResponse)
async def send_message(
    conversation_id: str,
    message: ChatMessage,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Send a message to an agricultural agent
    
    Args:
        conversation_id: ID of the conversation
        message: Message to send
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        ChatResponse: Agent's response
    """
    try:
        # Verify conversation belongs to user
        conversation = await chat_service.get_conversation(
            db=db,
            conversation_id=conversation_id,
            user_id=current_user.id
        )
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Process message with AI agent
        response_data = await chat_service.process_message_with_agent(
            db=db,
            conversation_id=conversation_id,
            user_id=current_user.id,
            message_content=message.content,
            farm_siret=conversation.farm_siret
        )
        
        logger.info(f"Message processed for conversation {conversation_id}")
        
        return ChatResponse(
            content=response_data["ai_response"]["content"],
            agent_type=response_data["ai_response"]["agent"],
            timestamp=response_data["ai_response"]["created_at"],
            metadata=response_data["ai_response"]["metadata"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Message processing error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process message"
        )

@router.get("/conversations/{conversation_id}/messages", response_model=List[ChatMessage])
async def get_conversation_messages(
    conversation_id: str,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get messages from a conversation
    
    Args:
        conversation_id: ID of the conversation
        skip: Number of messages to skip
        limit: Maximum number of messages to return
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List[ChatMessage]: Conversation messages
    """
    try:
        # Verify conversation belongs to user
        conversation = await chat_service.get_conversation(
            db=db,
            conversation_id=conversation_id,
            user_id=current_user.id
        )
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        messages = await chat_service.get_conversation_messages(
            db=db,
            conversation_id=conversation_id,
            skip=skip,
            limit=limit
        )
        
        return [
            ChatMessage(
                content=msg.content,
                sender=msg.sender,
                timestamp=msg.created_at
            )
            for msg in messages
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get messages error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve messages"
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
        logger.error(f"Get agents error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve available agents"
        )

@router.websocket("/ws/{conversation_id}")
async def websocket_chat(
    websocket: WebSocket,
    conversation_id: str,
    token: str
):
    """
    WebSocket endpoint for real-time chat
    
    Args:
        websocket: WebSocket connection
        conversation_id: ID of the conversation
        token: JWT authentication token
    """
    await websocket.accept()
    
    try:
        # Verify token and get user
        user = await auth_service.verify_websocket_token(token)
        if not user:
            await websocket.close(code=1008, reason="Invalid token")
            return
        
        # Verify conversation belongs to user
        db = next(get_async_db())
        conversation = await chat_service.get_conversation(
            db=db,
            conversation_id=conversation_id,
            user_id=user.id
        )
        
        if not conversation:
            await websocket.close(code=1008, reason="Conversation not found")
            return
        
        logger.info(f"WebSocket connection established for conversation {conversation_id}")
        
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            # Process message with agent
            response = await agent_service.process_message(
                db=db,
                conversation=conversation,
                message=message_data["content"],
                user=user
            )
            
            # Send response back to client
            await websocket.send_text(json.dumps({
                "content": response.content,
                "agent_type": conversation.agent_type,
                "timestamp": response.timestamp.isoformat(),
                "metadata": response.metadata
            }))
            
    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for conversation {conversation_id}")
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await websocket.close(code=1011, reason="Internal server error")
