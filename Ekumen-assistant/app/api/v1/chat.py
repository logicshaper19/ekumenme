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
from app.schemas.chat import ChatMessage, ChatResponse, ConversationCreate, ConversationResponse, ConversationUpdate
from app.services.auth_service import AuthService
from app.services.auth_service import oauth2_scheme

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
    token: str = Depends(oauth2_scheme),
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
        token_data = auth_service.verify_token(token)
        org_id = str(token_data.org_id) if token_data and token_data.org_id else None
        if not org_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Organization not selected. Call /api/v1/auth/organizations and /api/v1/auth/select-organization first.")
        conversation = await chat_service.create_conversation(
            db=db,
            user_id=current_user.id,
            agent_type=conversation_data.agent_type,
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
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Update conversation details (currently supports title and farm_siret)
    """
    try:
        token_data = auth_service.verify_token(token)
        org_id = str(token_data.org_id) if token_data and token_data.org_id else None
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
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

        if update.title:
            conversation = await chat_service.update_conversation_title(
                db=db,
                conversation_id=conversation_id,
                title=update.title
            )
        # Update farm_siret directly if provided
        if update.farm_siret is not None:
            convo_obj = await db.get(type(conversation), conversation_id)
            if convo_obj:
                convo_obj.farm_siret = update.farm_siret
                await db.commit()
                await db.refresh(convo_obj)
                conversation = convo_obj

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

@router.get("/conversations/search", response_model=List[ConversationResponse])
async def search_conversations(
    q: str,
    agent_type: Optional[str] = None,
    limit: int = 20,
    current_user: User = Depends(auth_service.get_current_user),
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Search conversations by title. For now, only title is searched.
    """
    try:
        token_data = auth_service.verify_token(token)
        org_id = str(token_data.org_id) if token_data and token_data.org_id else None
        if not org_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Organization not selected.")
        conversations = await chat_service.search_conversations(
            db=db,
            user_id=current_user.id,
            query=q,
            agent_type=agent_type,
            limit=limit,
            organization_id=org_id
        )
        return [
            ConversationResponse(
                id=str(c.id),
                title=c.title,
                agent_type=c.agent_type,
                farm_siret=c.farm_siret,
                created_at=c.created_at,
                updated_at=c.updated_at
            ) for c in conversations
        ]
    except Exception as e:
        logger.error(f"Search conversations error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to search conversations")



@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(auth_service.get_current_user),
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Soft delete a conversation
    """
    try:
        token_data = auth_service.verify_token(token)
        org_id = str(token_data.org_id) if token_data and token_data.org_id else None
        if not org_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Organization not selected.")
        ok = await chat_service.delete_conversation(
            db=db,
            conversation_id=conversation_id,
            user_id=current_user.id,
            organization_id=org_id
        )
        if not ok:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")
        return None
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete conversation error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to delete conversation")

@router.get("/conversations", response_model=List[ConversationResponse])
async def get_user_conversations(
    skip: int = 0,
    limit: int = 50,
    current_user: User = Depends(auth_service.get_current_user),
    token: str = Depends(oauth2_scheme),
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
        token_data = auth_service.verify_token(token)
        org_id = str(token_data.org_id) if token_data and token_data.org_id else None
        if not org_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Organization not selected.")
        conversations = await chat_service.get_user_conversations(
            db=db,
            user_id=current_user.id,
            skip=skip,
            limit=limit,
            organization_id=org_id
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
    token: str = Depends(oauth2_scheme),
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
        token_data = auth_service.verify_token(token)
        org_id = str(token_data.org_id) if token_data and token_data.org_id else None
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

        # Process message with LCEL + RAG (org-scoped)
        response_data = await chat_service.process_message_with_lcel(
            db=db,
            conversation_id=conversation_id,
            user_id=current_user.id,
            message_content=message.content,
            use_rag=True,
            organization_id=org_id
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
    token: str = Depends(oauth2_scheme),
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
        token_data = auth_service.verify_token(token)
        org_id = str(token_data.org_id) if token_data and token_data.org_id else None
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

        # Create streaming generator (LCEL astream with RAG + org scoping)
        async def generate_stream():
            try:
                final_response = ""
                source_docs = []

                async for event in chat_service.lcel_service.stream_message(
                    db_session=db,
                    conversation_id=conversation_id,
                    message=message.content,
                    use_rag=True,
                    organization_id=org_id
                ):
                    # Final event carries full answer and context
                    if isinstance(event, dict) and "final" in event:
                        final_payload = event.get("final") or {}
                        ans = final_payload.get("answer")
                        if isinstance(ans, str) and ans:
                            final_response = ans
                        ctx = final_payload.get("context")
                        if isinstance(ctx, list):
                            source_docs = ctx
                        continue

                    # Token streaming (string chunks)
                    if isinstance(event, str):
                        final_response += event
                        yield f"data: {json.dumps({'type': 'token', 'text': event})}\n\n"

                # Map citations from source_docs
                def _map_citations(docs):
                    items = []
                    for idx, doc in enumerate(docs):
                        try:
                            meta = getattr(doc, "metadata", {}) or {}
                            page_number = meta.get("page") or meta.get("page_number")
                            filename = meta.get("filename") or "Document"
                            chunk_text = (getattr(doc, "page_content", "") or "")[:500]
                            relevance = meta.get("score")
                            # Internal representation (persisted)
                            items.append({
                                "document_id": meta.get("document_id"),
                                "filename": filename,
                                "relevance_score": relevance,
                                "chunk_index": meta.get("chunk_index"),
                                "page_number": page_number,
                                "chunk_text": chunk_text,
                                "rank": idx + 1
                            })
                        except Exception:
                            continue
                    return items

                documents_retrieved = _map_citations(source_docs)

                # Map to frontend-friendly sources (optional)
                def _map_sources(docs):
                    src = []
                    for d in docs:
                        try:
                            title = f"{d.get('filename') or 'Document'}" + (f" (p. {d.get('page_number')})" if d.get('page_number') else "")
                            src.append({
                                "title": title,
                                "url": "#",
                                "snippet": d.get("chunk_text") or "",
                                "relevance": d.get("relevance_score"),
                                "type": "document"
                            })
                        except Exception:
                            continue
                    return src

                sources = _map_sources(documents_retrieved)

                # After stream completion, persist assistant message with citations
                saved = await chat_service.save_message(
                    db=db,
                    conversation_id=conversation_id,
                    content=final_response,
                    sender="agent",
                    agent_type=conversation.agent_type,
                    message_type="text",
                    metadata={
                        "processing_method": "lcel_with_automatic_history",
                        "use_rag": True,
                        "knowledge_base_used": len(documents_retrieved) > 0,
                        "documents_retrieved": documents_retrieved
                    }
                )

                # Final SSE event indicating completion (unified format)
                yield f"data: {json.dumps({'type': 'done', 'message_id': str(saved.id), 'citation_count': len(documents_retrieved), 'sources': sources})}\n\n"

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



@router.get("/messages/{message_id}/citations")
async def get_message_citations(
    message_id: str,
    current_user: User = Depends(auth_service.get_current_user),
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Return citations/sources for a message if available in message_metadata.documents_retrieved
    """
    try:
        message = await chat_service.get_message_by_id(db=db, message_id=message_id)
        if not message:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found")
        # Best-effort: ensure the user owns the conversation
        token_data = auth_service.verify_token(token)
        org_id = str(token_data.org_id) if token_data and token_data.org_id else None
        if not org_id:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Organization not selected.")
        conversation = await chat_service.get_conversation(
            db=db,
            conversation_id=str(message.conversation_id),
            user_id=current_user.id,
            organization_id=org_id
        )
        if not conversation:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
        metadata = message.message_metadata or {}
        citations = metadata.get("documents_retrieved") or []
        return {"message_id": str(message.id), "citations": citations}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get citations error: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Failed to get citations")


@router.get("/conversations/{conversation_id}/messages", response_model=List[ChatMessage])
async def get_conversation_messages(
    conversation_id: str,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(auth_service.get_current_user),
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get messages for a conversation
    """
    try:
        token_data = auth_service.verify_token(token)
        org_id = str(token_data.org_id) if token_data and token_data.org_id else None
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

        # Verify conversation belongs to user (org-scoped)
        token_data = auth_service.verify_token(token)
        org_id = str(token_data.org_id) if token_data and token_data.org_id else None
        if not org_id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return
        async for db in get_async_db():
            conversation = await chat_service.get_conversation(
                db=db,
                conversation_id=conversation_id,
                user_id=user.id,
                organization_id=org_id
            )
            break

        if not conversation:
            await websocket.close(code=1008, reason="Conversation not found")
            return

        # Accept the WebSocket connection BEFORE any send operations
        await websocket.accept()
        logger.info(f"Unified WebSocket connection established for conversation {conversation_id}")

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

            # Stream LCEL response with unified events
            final_response = ""
            source_docs = []

            # Signal streaming start so frontend creates placeholder message
            await websocket.send_json({"type": "llm_start", "message_id": user_message_id})

            # Use org-scoped LCEL astream
            async for event in chat_service.lcel_service.stream_message(
                db_session=db,
                conversation_id=conversation_id,
                message=message_content,
                use_rag=True,
                organization_id=org_id
            ):
                # Final event carries full answer and context
                if isinstance(event, dict) and "final" in event:
                    final_payload = event.get("final") or {}
                    ans = final_payload.get("answer")
                    if isinstance(ans, str) and ans:
                        final_response = ans
                    ctx = final_payload.get("context")
                    if isinstance(ctx, list):
                        source_docs = ctx
                    continue

                # Token streaming (string chunks)
                if isinstance(event, str):
                    final_response += event
                    await websocket.send_json({"type": "token", "text": event})

            # Map citations from source_docs (persisted + frontend-friendly)
            def _map_citations(docs):
                items = []
                for idx, doc in enumerate(docs):
                    try:
                        meta = getattr(doc, "metadata", {}) or {}
                        page_number = meta.get("page") or meta.get("page_number")
                        filename = meta.get("filename") or "Document"
                        chunk_text = (getattr(doc, "page_content", "") or "")[:500]
                        relevance = meta.get("score")
                        items.append({
                            "document_id": meta.get("document_id"),
                            "filename": filename,
                            "relevance_score": relevance,
                            "chunk_index": meta.get("chunk_index"),
                            "page_number": page_number,
                            "chunk_text": chunk_text,
                            "rank": idx + 1
                        })
                    except Exception:
                        continue
                return items

            def _map_sources(docs):
                src = []
                for d in docs:
                    try:
                        title = f"{d.get('filename') or 'Document'}" + (f" (p. {d.get('page_number')})" if d.get('page_number') else "")
                        src.append({
                            "title": title,
                            "url": "#",
                            "snippet": d.get("chunk_text") or "",
                            "relevance": d.get("relevance_score"),
                            "type": "document"
                        })
                    except Exception:
                        continue
                return src

            documents_retrieved = _map_citations(source_docs)
            sources = _map_sources(documents_retrieved)

            # Persist assistant message with citations
            async for db in get_async_db():
                saved = await chat_service.save_message(
                    db=db,
                    conversation_id=conversation_id,
                    content=final_response,
                    sender="agent",
                    agent_type=conversation.agent_type,
                    message_type="text",
                    metadata={
                        "processing_method": "lcel_with_automatic_history",
                        "use_rag": True,
                        "knowledge_base_used": len(documents_retrieved) > 0,
                        "documents_retrieved": documents_retrieved
                    }
                )
                message_id = str(saved.id)
                break

            # Unified completion event
            await websocket.send_json({
                "type": "done",
                "message_id": message_id,
                "citation_count": len(documents_retrieved),
                "sources": sources
            })

    except WebSocketDisconnect:
        logger.info(f"Unified WebSocket disconnected for conversation {conversation_id}")
    except Exception as e:
        logger.error(f"Unified WebSocket error: {e}")
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
            await websocket.close(code=1011, reason="Internal server error")
        except:
            pass
    finally:
        # No connection registry to clean up in unified LCEL streaming
        pass