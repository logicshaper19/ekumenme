"""
Chat API endpoints
Handles conversations with agricultural AI agents
"""

from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import logging
import json
import asyncio
import time

from app.core.database import get_async_db
from app.models.user import User
from app.schemas.chat import ChatMessage, ChatResponse, ConversationCreate, ConversationResponse
from app.services.auth_service import AuthService
from app.services.chat_service import ChatService
from app.services.agent_service import AgentService
from app.services.streaming_service import StreamingService
from app.services.optimized_streaming_service import OptimizedStreamingService
from app.services.tool_registry_service import get_tool_registry

logger = logging.getLogger(__name__)

router = APIRouter()
auth_service = AuthService()
chat_service = ChatService()
agent_service = AgentService()

# OLD streaming service (kept for backward compatibility)
streaming_service_old = StreamingService()

# NEW optimized streaming service (5-10x faster)
tool_registry = get_tool_registry()
streaming_service = OptimizedStreamingService(tool_executor=tool_registry)

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
            id=str(conversation.id),  # Convert UUID to string explicitly
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
                id=str(conv.id),
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


@router.post("/conversations/{conversation_id}/messages/stream")
async def send_message_stream(
    conversation_id: str,
    message: ChatMessage,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Send a message and get streaming response from agricultural agent

    Args:
        conversation_id: ID of the conversation
        message: Message to send
        current_user: Current authenticated user
        db: Database session

    Returns:
        StreamingResponse: Real-time agent response
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

        # Save user message
        await chat_service.save_message(
            db=db,
            conversation_id=conversation_id,
            content=message.content,
            sender="user",
            message_type="text"
        )

        # Create context for streaming
        context = {
            "conversation_id": conversation_id,
            "farm_siret": conversation.farm_siret,
            "agent_type": conversation.agent_type,
            "user_id": current_user.id
        }

        # Create streaming generator
        async def generate_stream():
            try:
                async for chunk in streaming_service.stream_response(
                    query=message.content,
                    context=context,
                    use_workflow=True
                ):
                    # Format as Server-Sent Events
                    yield f"data: {json.dumps(chunk)}\n\n"

                    # Save final response if it's the complete result
                    if chunk.get("type") in ["workflow_result", "advanced_result"]:
                        await chat_service.save_message(
                            db=db,
                            conversation_id=conversation_id,
                            content=chunk.get("response", ""),
                            sender="assistant",
                            agent_type=chunk.get("agent_type", conversation.agent_type),
                            message_type="text",
                            metadata=chunk.get("metadata", {})
                        )

            except Exception as e:
                logger.error(f"Streaming error: {e}")
                error_chunk = {
                    "type": "error",
                    "message": f"Erreur de streaming: {str(e)}",
                    "timestamp": "2024-01-01T00:00:00"
                }
                yield f"data: {json.dumps(error_chunk)}\n\n"

        return StreamingResponse(
            generate_stream(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "*"
            }
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Streaming setup error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to setup streaming"
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
    Enhanced WebSocket endpoint for real-time streaming chat

    Args:
        websocket: WebSocket connection
        conversation_id: ID of the conversation
        token: JWT authentication token
    """
    connection_id = None

    try:
        # Verify token and get user
        user = await auth_service.verify_websocket_token(token)
        if not user:
            await websocket.close(code=1008, reason="Invalid token")
            return

        # Verify conversation belongs to user
        async for db in get_async_db():
            conversation = await chat_service.get_conversation(
                db=db,
                conversation_id=conversation_id,
                user_id=user.id
            )
            break

        if not conversation:
            await websocket.close(code=1008, reason="Conversation not found")
            return

        # IMPORTANT: Accept the WebSocket connection BEFORE any send operations
        await websocket.accept()

        # Connect to streaming service
        connection_id = await streaming_service.connect_websocket(websocket)
        logger.info(f"Enhanced WebSocket connection established: {connection_id}")

        # Send connection confirmation
        await websocket.send_json({
            "type": "connection",
            "connection_id": connection_id,
            "message": "Connected to Ekumen Assistant"
        })

        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message_data = json.loads(data)

            # Extract message content (handle both 'content' and 'message' keys)
            message_content = message_data.get("content") or message_data.get("message", "")
            if not message_content:
                logger.error(f"No message content found in: {message_data}")
                continue

            # Get thread_id from message data (frontend should provide this)
            thread_id = message_data.get("thread_id") or message_data.get("message_id") or f"thread-{int(time.time() * 1000)}"

            # Save user message and get message ID
            user_message_id = None
            async for db in get_async_db():
                user_message = await chat_service.save_message(
                    db=db,
                    conversation_id=conversation_id,
                    content=message_content,
                    sender="user",
                    message_type="text",
                    thread_id=thread_id
                )
                user_message_id = str(user_message.id)
                break

            # Create context with message and thread IDs
            context = {
                "conversation_id": conversation_id,
                "farm_siret": conversation.farm_siret,
                "agent_type": conversation.agent_type,
                "user_id": user.id,
                "message_id": user_message_id,
                "thread_id": thread_id
            }

            # Stream response through WebSocket
            final_response = ""
            async for chunk in streaming_service.stream_response(
                query=message_content,
                context=context,
                connection_id=connection_id,
                use_workflow=True
            ):
                # Extract final response for saving
                if chunk.get("type") in ["workflow_result", "advanced_result"]:
                    final_response = chunk.get("response", "")

            # Save AI response
            if final_response:
                async for db in get_async_db():
                    await chat_service.save_message(
                        db=db,
                        conversation_id=conversation_id,
                        content=final_response,
                        sender="assistant",
                        agent_type=conversation.agent_type,
                        message_type="text"
                    )
                    break

    except WebSocketDisconnect:
        logger.info(f"Enhanced WebSocket disconnected: {connection_id}")
    except Exception as e:
        logger.error(f"Enhanced WebSocket error: {e}")
        try:
            await websocket.close(code=1011, reason="Internal server error")
        except:
            pass
    finally:
        if connection_id:
            await streaming_service.disconnect_websocket(connection_id)
