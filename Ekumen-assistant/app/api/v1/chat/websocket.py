"""
WebSocket chat endpoints
Handles real-time WebSocket communication for chat
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException, status
from app.services.shared import AuthService
from app.services.shared import ChatService
import logging
import json
import time
import uuid

logger = logging.getLogger(__name__)

router = APIRouter()
auth_service = AuthService()
chat_service = ChatService()

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
        # Verify token and get user BEFORE accepting connection
        user = await auth_service.verify_websocket_token(token)
        if not user:
            await websocket.close(code=1008, reason="Invalid token")
            return

        # Extract org_id from token for WebSocket (can't use dependency injection)
        token_data = auth_service.verify_token(token)
        org_id = str(token_data.org_id) if token_data and token_data.org_id else None
        
        # Verify conversation belongs to user (org-scoped)
        if not org_id:
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Organization not selected")
            return

        # Accept the WebSocket connection ONLY after verification
        await websocket.accept()
        logger.info(f"WebSocket connection accepted for conversation {conversation_id}")

        # Get initial database session to verify conversation
        # NOTE: WebSocket endpoints cannot use FastAPI dependency injection (Depends())
        # This is a known limitation - WebSocket connections are established before
        # dependency resolution occurs. Using AsyncSessionLocal() directly is the
        # standard workaround for this FastAPI limitation.
        from app.core.database import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            conversation = await chat_service.get_conversation(
                db=db,
                conversation_id=conversation_id,
                user_id=user.id,
                organization_id=org_id
            )

        if not conversation:
            await websocket.close(code=1008, reason="Conversation not found")
            return

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
            thread_id = message_data.get("thread_id") or message_data.get("message_id") or str(uuid.uuid4())
            
            # Extract mode from message data (for Tavily routing)
            mode = message_data.get("mode")
            logger.info(f"🔍 Processing message with mode: {mode}")
            logger.info(f"🔍 Full message data: {message_data}")

            # Create a new database session for this message processing
            async with AsyncSessionLocal() as db:
                # Save user message and get message ID
                user_message = await chat_service.save_message(
                    db=db,
                    conversation_id=conversation_id,
                    content=message_content,
                    sender="user",
                    message_type="text",
                    thread_id=thread_id
                )
                user_message_id = str(user_message.id)
                await db.commit()  # Commit the user message

                # Stream LCEL response with unified events
                final_response = ""
                source_docs = []
                tokens_emitted = 0

                # Create assistant message ID upfront for streaming
                assistant_message_id = f"msg-{int(time.time() * 1000)}"

                # Signal streaming start so frontend creates placeholder message
                await websocket.send_json({"type": "llm_start", "message_id": assistant_message_id})

                # Use LCEL service with mode-aware tools
                # For supplier/internet modes, use Tavily only (no RAG)
                # For other modes, use RAG
                use_rag = mode not in ["supplier", "internet"]
                reformulated_query = None
                async for event in chat_service.lcel_service.stream_message(
                    db_session=db,
                    conversation_id=conversation_id,
                    message=message_content,
                    use_rag=use_rag,
                    organization_id=org_id,
                    mode=mode  # Pass mode to LCEL service for tool selection
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
                        # Capture reformulated query
                        reformulated_query = final_payload.get("reformulated_query")
                        continue

                    # Token streaming (string chunks) - INCLUDE message_id!
                    if isinstance(event, str):
                        final_response += event
                        tokens_emitted += 1
                        await websocket.send_json({"type": "token", "text": event, "message_id": assistant_message_id})

                # If no tokens were emitted but we have a final answer, emit it once
                if tokens_emitted == 0 and isinstance(final_response, str) and final_response:
                    await websocket.send_json({"type": "token", "text": final_response, "message_id": assistant_message_id})

                # Save assistant message to database
                if final_response:
                    assistant_message = await chat_service.save_message(
                        db=db,
                        conversation_id=conversation_id,
                        content=final_response,
                        sender="agent",
                        agent_type=mode if mode in ["internet", "supplier"] else "farm_data",
                        message_type="text",
                        thread_id=thread_id
                    )
                    await db.commit()

                # Map citations using service methods
                documents_retrieved = chat_service.map_citations_for_storage(source_docs)
                sources = chat_service.map_citations_for_frontend(documents_retrieved)

                # Update the existing assistant message with citations (don't create a new one)
                if assistant_message:
                    assistant_message.message_metadata = {
                        "processing_method": "lcel_with_automatic_history",
                        "use_rag": True,
                        "knowledge_base_used": len(documents_retrieved) > 0,
                        "documents_retrieved": documents_retrieved,
                        "reformulated_query": reformulated_query,
                        "original_query": message_content
                    }
                    await db.commit()
                    saved = assistant_message
                else:
                    # Fallback: create new message if assistant_message doesn't exist
                    saved = await chat_service.save_message(
                        db=db,
                        conversation_id=conversation_id,
                        content=final_response,
                        sender="agent",
                        agent_type=mode if mode in ["internet", "supplier"] else "farm_data",
                        message_type="text",
                        metadata={
                            "processing_method": "lcel_with_automatic_history",
                            "use_rag": True,
                            "knowledge_base_used": len(documents_retrieved) > 0,
                            "documents_retrieved": documents_retrieved,
                            "reformulated_query": reformulated_query,
                            "original_query": message_content
                        }
                    )
                message_id = str(saved.id)
                await db.commit()  # Commit the agent message

                # Unified completion event
                await websocket.send_json({
                    "type": "done",
                    "message_id": message_id,
                    "citation_count": len(documents_retrieved),
                    "sources": sources,
                    "reformulated_query": reformulated_query,
                    "original_query": message_content
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
