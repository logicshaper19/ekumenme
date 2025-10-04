"""
Streaming chat endpoints
Handles real-time streaming responses from AI agents
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import logging
import json

from app.core.database import get_async_db
from app.models.user import User
from app.schemas.chat import ChatMessage
from app.services.shared.auth_service import AuthService
from app.services.shared.chat_service import ChatService

from .dependencies import get_org_id_from_token

logger = logging.getLogger(__name__)

router = APIRouter()
auth_service = AuthService()
chat_service = ChatService()

@router.post("/conversations/{conversation_id}/messages/stream")
async def send_message_stream(
    conversation_id: str,
    message: ChatMessage,
    current_user: User = Depends(auth_service.get_current_user),
    org_id: Optional[str] = Depends(get_org_id_from_token),
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
                tokens_emitted = 0

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
                        tokens_emitted += 1
                        token_data = {"type": "token", "text": event}
                        yield f"data: {json.dumps(token_data)}\n\n"

                # If no incremental tokens were emitted but we have a final answer,
                # send it as a single token so the UI displays the message.
                if tokens_emitted == 0 and isinstance(final_response, str) and final_response:
                    fallback_token = {"type": "token", "text": final_response}
                    yield f"data: {json.dumps(fallback_token)}\n\n"

                # Map citations using service methods
                documents_retrieved = chat_service.map_citations_for_storage(source_docs)
                sources = chat_service.map_citations_for_frontend(documents_retrieved)

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
