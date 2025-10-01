"""
Optimized Streaming Service - Orchestrator-Based Implementation

This service provides optimized streaming responses using the orchestrator agent
with caching, parallel execution, and smart tool selection.

Architecture:
- Uses orchestrator agent for intelligent routing
- Multi-layer caching for performance
- Parallel tool execution where possible
- WebSocket support for real-time streaming
"""

import logging
import asyncio
import time
from typing import Dict, Any, Optional, AsyncGenerator, List
from dataclasses import dataclass
from fastapi import WebSocket
from langchain.agents import create_react_agent, AgentExecutor
from langchain_openai import ChatOpenAI
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler
from langchain.callbacks.base import AsyncCallbackHandler

from app.prompts.prompt_registry import get_agent_prompt
from app.services.tool_registry_service import get_tool_registry
from app.services.multi_layer_cache_service import MultiLayerCacheService
from app.services.parallel_executor_service import ParallelExecutorService
from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class StreamingMetrics:
    """Metrics for streaming response"""
    total_time: float = 0.0
    orchestrator_time: float = 0.0
    tool_execution_time: float = 0.0
    synthesis_time: float = 0.0
    cache_hit: bool = False
    tools_executed: int = 0
    model_used: str = "gpt-4"
    tokens_used: int = 0


class WebSocketCallback(AsyncCallbackHandler):
    """Callback handler for streaming to WebSocket"""

    def __init__(self, websocket: Optional[WebSocket] = None):
        self.websocket = websocket
        self.tokens = []

    async def on_llm_new_token(self, token: str, **kwargs) -> None:
        """Send new tokens to WebSocket"""
        if self.websocket:
            try:
                await self.websocket.send_json({
                    "type": "token",
                    "content": token
                })
                self.tokens.append(token)
            except Exception as e:
                logger.error(f"WebSocket send error: {e}")

    async def on_llm_end(self, response, **kwargs) -> None:
        """Send completion signal"""
        if self.websocket:
            try:
                await self.websocket.send_json({
                    "type": "stream_end",
                    "total_tokens": len(self.tokens)
                })
            except Exception as e:
                logger.error(f"WebSocket send error: {e}")


class OptimizedStreamingService:
    """
    Optimized streaming service using orchestrator-first architecture.

    Features:
    - Orchestrator agent for intelligent routing
    - Multi-layer caching (Redis + memory)
    - Parallel tool execution
    - WebSocket streaming support
    - Performance metrics tracking
    """

    def __init__(self, tool_executor: Optional[Any] = None):
        """Initialize optimized streaming service with orchestrator"""

        # Initialize caching
        self.cache = MultiLayerCacheService()

        # Initialize parallel executor
        self.parallel_executor = ParallelExecutorService()

        # Get tool registry
        self.tool_registry = get_tool_registry()
        self.tools = self.tool_registry.get_all_tools()

        # Initialize LLM with streaming
        self.llm = ChatOpenAI(
            model=settings.OPENAI_DEFAULT_MODEL,
            temperature=0,
            streaming=True,
            openai_api_key=settings.OPENAI_API_KEY
        )

        # Get orchestrator prompt
        self.orchestrator_prompt = get_agent_prompt("orchestrator", include_examples=True)

        # Create orchestrator agent
        self.orchestrator = create_react_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=self.orchestrator_prompt
        )

        # Statistics
        self.total_queries = 0
        self.cache_hits = 0
        self.total_time_saved = 0.0

        # WebSocket connections
        self.websocket_connections = {}

        logger.info("=" * 80)
        logger.info("✅ Optimized Streaming Service Initialized")
        logger.info(f"✅ Orchestrator agent created with {len(self.tools)} tools")
        logger.info(f"✅ Model: {settings.OPENAI_DEFAULT_MODEL}")
        logger.info(f"✅ Caching: Multi-layer (Redis + Memory)")
        logger.info(f"✅ Streaming: Enabled")
        logger.info("=" * 80)

    async def register_websocket(self, connection_id: str, websocket: WebSocket):
        """Register a WebSocket connection"""
        self.websocket_connections[connection_id] = websocket
        logger.info(f"✅ WebSocket registered: {connection_id}")

        # Send connection confirmation
        try:
            await websocket.send_json({
                "type": "connection_established",
                "connection_id": connection_id,
                "message": "Streaming service ready"
            })
        except Exception as e:
            logger.error(f"Failed to send connection confirmation: {e}")

    async def unregister_websocket(self, connection_id: str):
        """Unregister a WebSocket connection"""
        if connection_id in self.websocket_connections:
            del self.websocket_connections[connection_id]
            logger.info(f"❌ WebSocket unregistered: {connection_id}")

    async def stream_response(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        connection_id: Optional[str] = None,
        use_workflow: bool = True,
        conversation_id: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream response using orchestrator agent with caching and optimization.

        Args:
            query: User query
            context: Additional context (farm_siret, user_id, etc.)
            connection_id: WebSocket connection ID
            use_workflow: Whether to use workflow (always True for orchestrator)
            conversation_id: Conversation ID for history

        Yields:
            Dict with streaming chunks and final response
        """
        start_time = time.time()
        self.total_queries += 1
        context = context or {}

        logger.info(f"🚀 Processing query with orchestrator: {query[:100]}...")

        # Get WebSocket if connection_id provided
        websocket = None
        if connection_id and connection_id in self.websocket_connections:
            websocket = self.websocket_connections[connection_id]

        # Send start message
        start_msg = {
            "type": "workflow_start",
            "message": "Analyse de votre demande...",
            "query": query,
            "timestamp": time.time()
        }

        if websocket:
            try:
                await websocket.send_json(start_msg)
            except Exception as e:
                logger.error(f"WebSocket send error: {e}")

        yield start_msg

        # Check cache first
        cache_key = self.cache.generate_key(query, context)
        cached_response = await self.cache.get(cache_key)

        if cached_response:
            self.cache_hits += 1
            cache_time = time.time() - start_time
            self.total_time_saved += cache_time

            logger.info(f"✅ Cache hit! Saved {cache_time:.2f}s")

            cache_msg = {
                "type": "cache_hit",
                "message": "Réponse trouvée en cache",
                "time_saved": cache_time
            }

            if websocket:
                try:
                    await websocket.send_json(cache_msg)
                except Exception as e:
                    logger.error(f"WebSocket send error: {e}")

            yield cache_msg

            # Send cached response
            final_msg = {
                "type": "workflow_result",
                "response": cached_response,
                "metadata": {
                    "cache_hit": True,
                    "total_time": cache_time,
                    "model_used": "cache"
                }
            }

            if websocket:
                try:
                    await websocket.send_json(final_msg)
                except Exception as e:
                    logger.error(f"WebSocket send error: {e}")

            yield final_msg
            return

        # Execute with orchestrator
        orchestrator_start = time.time()

        try:
            # Create agent executor with streaming callback
            ws_callback = WebSocketCallback(websocket)

            agent_executor = AgentExecutor(
                agent=self.orchestrator,
                tools=self.tools,
                verbose=True,
                handle_parsing_errors=True,
                max_iterations=10,
                callbacks=[ws_callback] if websocket else []
            )

            # Prepare input with context
            agent_input = {
                "input": query,
                **context
            }

            # Send orchestrator start message
            orchestrator_msg = {
                "type": "orchestrator_thinking",
                "message": "L'orchestrateur analyse votre demande..."
            }

            if websocket:
                try:
                    await websocket.send_json(orchestrator_msg)
                except Exception as e:
                    logger.error(f"WebSocket send error: {e}")

            yield orchestrator_msg

            # Execute orchestrator
            result = await agent_executor.ainvoke(agent_input)

            orchestrator_time = time.time() - orchestrator_start
            total_time = time.time() - start_time

            # Extract response
            response_text = result.get("output", "Désolé, je n'ai pas pu générer une réponse.")

            # Cache the response
            await self.cache.set(cache_key, response_text)

            # Build metrics
            metrics = StreamingMetrics(
                total_time=total_time,
                orchestrator_time=orchestrator_time,
                cache_hit=False,
                tools_executed=len(result.get("intermediate_steps", [])),
                model_used=settings.OPENAI_DEFAULT_MODEL,
                tokens_used=len(ws_callback.tokens)
            )

            # Send final response
            final_msg = {
                "type": "workflow_result",
                "response": response_text,
                "metadata": {
                    "cache_hit": False,
                    "total_time": total_time,
                    "orchestrator_time": orchestrator_time,
                    "tools_executed": metrics.tools_executed,
                    "model_used": metrics.model_used,
                    "tokens_used": metrics.tokens_used
                }
            }

            if websocket:
                try:
                    await websocket.send_json(final_msg)
                except Exception as e:
                    logger.error(f"WebSocket send error: {e}")

            yield final_msg

            logger.info(f"✅ Query processed in {total_time:.2f}s (orchestrator: {orchestrator_time:.2f}s)")

        except Exception as e:
            logger.error(f"❌ Error processing query: {e}", exc_info=True)

            error_msg = {
                "type": "error",
                "message": f"Erreur lors du traitement: {str(e)}",
                "error": str(e)
            }

            if websocket:
                try:
                    await websocket.send_json(error_msg)
                except Exception as ws_error:
                    logger.error(f"WebSocket send error: {ws_error}")

            yield error_msg

    def get_performance_stats(self) -> Dict[str, Any]:
        """Get performance statistics"""
        cache_hit_rate = (self.cache_hits / self.total_queries * 100) if self.total_queries > 0 else 0

        return {
            "total_queries": self.total_queries,
            "cache_hits": self.cache_hits,
            "cache_hit_rate": f"{cache_hit_rate:.1f}%",
            "total_time_saved": f"{self.total_time_saved:.2f}s",
            "avg_time_saved_per_hit": f"{self.total_time_saved / self.cache_hits:.2f}s" if self.cache_hits > 0 else "0s",
            "active_websockets": len(self.websocket_connections),
            "tools_available": len(self.tools)
        }

    async def process_query(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process a query without streaming"""

        # Collect all streaming chunks
        chunks = []
        async for chunk in self.stream_response(query, context):
            chunks.append(chunk)

        # Return final result
        final_chunk = chunks[-1] if chunks else {"type": "error", "message": "No response"}

        return {
            "response": final_chunk.get("response", ""),
            "metadata": final_chunk.get("metadata", {}),
            "chunks": chunks
        }


# Export for compatibility
__all__ = ["OptimizedStreamingService", "StreamingMetrics", "WebSocketCallback"]

