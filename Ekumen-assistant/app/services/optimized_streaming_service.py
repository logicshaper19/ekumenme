"""
Optimized Streaming Service - Main orchestration service.

Integrates all optimization components:
1. Unified Router - Single routing decision
2. Parallel Executor - Parallel tool execution
3. Smart Tool Selector - Context-aware tool filtering
4. Optimized LLM - Smart model selection
5. Multi-Layer Cache - Aggressive caching
6. Optimized Database - Parallel queries

Goal: Reduce total query time from 60s to 5-11s
"""

import logging
import time
import asyncio
import uuid
import json
from typing import Dict, Any, Optional, AsyncGenerator
from dataclasses import dataclass
from fastapi import WebSocket

from app.services.unified_router_service import UnifiedRouterService, ExecutionPath, QueryComplexity
from app.services.parallel_executor_service import ParallelExecutorService
from app.services.smart_tool_selector_service import SmartToolSelectorService
from app.services.optimized_llm_service import OptimizedLLMService, LLMComplexity, LLMTask
from app.services.multi_layer_cache_service import MultiLayerCacheService

logger = logging.getLogger(__name__)


@dataclass
class StreamingMetrics:
    """Metrics for streaming response"""
    total_time: float
    routing_time: float
    tool_selection_time: float
    tool_execution_time: float
    synthesis_time: float
    cache_hit: bool
    tools_executed: int
    tools_filtered: int
    model_used: str


class OptimizedStreamingService:
    """
    Main optimized streaming service that orchestrates all components.
    
    This replaces the old streaming_service.py with a fully optimized version.
    """
    
    def __init__(self, tool_executor: Optional[Any] = None):
        # Initialize all optimization components
        self.router = UnifiedRouterService()
        self.executor = ParallelExecutorService()
        self.tool_selector = SmartToolSelectorService()
        self.llm_service = OptimizedLLMService()
        self.cache = MultiLayerCacheService()

        # Tool executor (for actual tool execution)
        self.tool_executor = tool_executor

        # Statistics
        self.total_queries = 0
        self.cache_hits = 0
        self.total_time_saved = 0.0

        logger.info("✅ Initialized Optimized Streaming Service")

    def _map_query_complexity_to_llm(self, query_complexity: QueryComplexity) -> LLMComplexity:
        """Map QueryComplexity to LLMComplexity"""
        mapping = {
            QueryComplexity.SIMPLE: LLMComplexity.SIMPLE,
            QueryComplexity.FAST: LLMComplexity.SIMPLE,
            QueryComplexity.MEDIUM: LLMComplexity.MEDIUM,
            QueryComplexity.COMPLEX: LLMComplexity.COMPLEX
        }
        return mapping.get(query_complexity, LLMComplexity.MEDIUM)

    async def _handle_direct_answer(
        self,
        query: str,
        metrics: StreamingMetrics
    ) -> str:
        """Handle simple queries with direct LLM response (no tools)"""
        logger.info("📝 Direct answer path (no tools)")
        
        synthesis_start = time.time()
        
        task = LLMTask(
            task_id="direct_answer",
            prompt=query,
            complexity=LLMComplexity.SIMPLE,
            max_tokens=300,
            temperature=0.5,
            system_message="Tu es un assistant agricole amical. Réponds de manière concise et utile."
        )
        
        result = await self.llm_service.execute_task(task)
        
        metrics.synthesis_time = time.time() - synthesis_start
        metrics.model_used = result.model_used
        metrics.tools_executed = 0
        
        return result.response
    
    async def _handle_fast_path(
        self,
        query: str,
        routing_decision: Any,
        context: Optional[Dict[str, Any]],
        metrics: StreamingMetrics
    ) -> str:
        """Handle fast path queries (single tool, GPT-3.5)"""
        logger.info(f"⚡ Fast path: {routing_decision.required_tools}")
        
        # Execute single tool
        tool_start = time.time()
        # TODO: Implement actual tool execution
        tool_results = {"tool": "result"}  # Placeholder
        metrics.tool_execution_time = time.time() - tool_start
        metrics.tools_executed = 1
        
        # Synthesize with GPT-3.5
        synthesis_start = time.time()
        response = await self.llm_service.synthesize_response(
            query,
            tool_results,
            complexity=LLMComplexity.FAST,
            max_tokens=500
        )
        metrics.synthesis_time = time.time() - synthesis_start
        metrics.model_used = "gpt-3.5-turbo"
        
        return response
    
    async def _handle_standard_path(
        self,
        query: str,
        routing_decision: Any,
        context: Optional[Dict[str, Any]],
        metrics: StreamingMetrics
    ) -> str:
        """Handle standard path queries (multiple tools in parallel, GPT-3.5)"""
        logger.info(f"🔄 Standard path: {routing_decision.required_tools}")
        
        # Step 1: Smart tool selection
        selection_start = time.time()
        selected_tools = self.tool_selector.select_tools(
            query,
            routing_decision.required_tools,
            context
        )
        metrics.tool_selection_time = time.time() - selection_start
        metrics.tools_filtered = len(routing_decision.required_tools) - len(selected_tools)
        
        # Step 2: Execute tools in parallel
        tool_start = time.time()
        # TODO: Implement actual parallel tool execution
        tool_results = {tool: "result" for tool in selected_tools}  # Placeholder
        metrics.tool_execution_time = time.time() - tool_start
        metrics.tools_executed = len(selected_tools)
        
        # Step 3: Synthesize with GPT-3.5
        synthesis_start = time.time()
        response = await self.llm_service.synthesize_response(
            query,
            tool_results,
            complexity=LLMComplexity.MEDIUM,
            max_tokens=800
        )
        metrics.synthesis_time = time.time() - synthesis_start
        metrics.model_used = "gpt-3.5-turbo"
        
        return response
    
    async def _handle_workflow_path(
        self,
        query: str,
        routing_decision: Any,
        context: Optional[Dict[str, Any]],
        metrics: StreamingMetrics
    ) -> str:
        """Handle complex workflow queries (full workflow, GPT-4)"""
        logger.info(f"🔄 Workflow path: {routing_decision.required_tools}")
        
        # Step 1: Smart tool selection
        selection_start = time.time()
        selected_tools = self.tool_selector.select_tools(
            query,
            routing_decision.required_tools,
            context
        )
        metrics.tool_selection_time = time.time() - selection_start
        metrics.tools_filtered = len(routing_decision.required_tools) - len(selected_tools)
        
        # Step 2: Execute tools in parallel
        tool_start = time.time()
        # TODO: Implement actual parallel tool execution
        tool_results = {tool: "result" for tool in selected_tools}  # Placeholder
        metrics.tool_execution_time = time.time() - tool_start
        metrics.tools_executed = len(selected_tools)
        
        # Step 3: Synthesize with GPT-4 (high quality)
        synthesis_start = time.time()
        response = await self.llm_service.synthesize_response(
            query,
            tool_results,
            complexity=LLMComplexity.COMPLEX,
            max_tokens=1200
        )
        metrics.synthesis_time = time.time() - synthesis_start
        metrics.model_used = "gpt-4"
        
        return response
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        router_stats = self.router.get_cache_stats()
        executor_stats = self.executor.get_stats()
        llm_stats = self.llm_service.get_stats()
        cache_stats = self.cache.get_stats()

        return {
            "total_queries": self.total_queries,
            "cache_hits": self.cache_hits,
            "cache_hit_rate": self.cache_hits / self.total_queries if self.total_queries > 0 else 0,
            "router": router_stats,
            "executor": executor_stats,
            "llm": llm_stats,
            "cache": cache_stats
        }

    # WebSocket support methods (for backward compatibility with old streaming_service)

    async def connect_websocket(self, websocket: WebSocket) -> str:
        """
        Connect a WebSocket client.

        Returns:
            connection_id: Unique connection identifier
        """
        connection_id = str(uuid.uuid4())
        if not hasattr(self, 'websocket_connections'):
            self.websocket_connections = {}

        self.websocket_connections[connection_id] = websocket
        logger.info(f"✅ WebSocket connected: {connection_id}")

        # NOTE: Do NOT send messages here - websocket.accept() must be called first
        # The connection confirmation will be sent after accept() in the WebSocket handler

        return connection_id

    async def disconnect_websocket(self, connection_id: str):
        """Disconnect a WebSocket client"""
        if hasattr(self, 'websocket_connections') and connection_id in self.websocket_connections:
            del self.websocket_connections[connection_id]
            logger.info(f"❌ WebSocket disconnected: {connection_id}")

    async def stream_response(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        connection_id: Optional[str] = None,
        use_workflow: bool = True,
        conversation_id: Optional[str] = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """
        Stream optimized response (WebSocket-compatible version).

        This version yields dict objects compatible with WebSocket messaging.
        """
        start_time = time.time()
        self.total_queries += 1

        # Get WebSocket if connection_id provided
        websocket = None
        if connection_id and hasattr(self, 'websocket_connections'):
            websocket = self.websocket_connections.get(connection_id)

        # Initialize metrics
        metrics = {
            "routing_time": 0,
            "tool_selection_time": 0,
            "tool_execution_time": 0,
            "synthesis_time": 0,
            "cache_hit": False
        }

        try:
            # Send workflow start message
            if websocket:
                await websocket.send_json({
                    "type": "workflow_start",
                    "message": "Starting optimized query processing...",
                    "query": query,
                    "message_id": context.get("message_id") if context else None
                })

            yield {
                "type": "workflow_start",
                "message": "Starting optimized query processing...",
                "query": query
            }

            # Step 1: Check cache first
            cache_key = self.cache.generate_key(query, context)
            cached_response = await self.cache.get(cache_key, "agent_response")

            if cached_response:
                self.cache_hits += 1
                metrics["cache_hit"] = True

                if websocket:
                    await websocket.send_json({
                        "type": "workflow_result",
                        "response": cached_response,
                        "message_id": context.get("message_id") if context else None,
                        "metadata": {"cache_hit": True, "total_time": time.time() - start_time}
                    })

                yield {
                    "type": "workflow_result",
                    "response": cached_response,
                    "metadata": {"cache_hit": True}
                }
                return

            # Step 2: Route query
            routing_start = time.time()
            routing_decision = await self.router.route_query(query, context)
            metrics["routing_time"] = time.time() - routing_start

            if websocket:
                await websocket.send_json({
                    "type": "workflow_step",
                    "step": "routing",
                    "message": f"Query routed to {routing_decision.execution_path.value} path",
                    "message_id": context.get("message_id") if context else None
                })

            yield {
                "type": "workflow_step",
                "step": "routing",
                "message": f"Query routed to {routing_decision.execution_path.value} path"
            }

            # Step 3: Execute tools if needed
            tool_results = {}
            sources = []  # Collect sources from tool results
            if routing_decision.required_tools and self.tool_executor:
                tool_start = time.time()
                try:
                    # Execute tools in parallel
                    tool_results = await self.tool_executor.execute_tools(
                        tools=routing_decision.required_tools,
                        query=query,
                        context=context or {}
                    )
                    metrics["tool_execution_time"] = time.time() - tool_start

                    # Extract sources from tool results
                    for tool_name, tool_result in tool_results.items():
                        # Handle JSON string results
                        if isinstance(tool_result, str):
                            try:
                                tool_result = json.loads(tool_result)
                            except json.JSONDecodeError:
                                pass  # Not JSON, skip

                        # Extract sources if present
                        if isinstance(tool_result, dict) and "sources" in tool_result:
                            sources.extend(tool_result["sources"])

                    if websocket:
                        await websocket.send_json({
                            "type": "workflow_step",
                            "step": "tools",
                            "message": f"Executed {len(tool_results)} tools",
                            "message_id": context.get("message_id") if context else None
                        })
                except Exception as e:
                    logger.error(f"Tool execution error: {e}")
                    metrics["tool_execution_time"] = time.time() - tool_start

            # Step 4: Synthesize response using LLM
            synthesis_start = time.time()

            try:
                # Map QueryComplexity to LLMComplexity
                llm_complexity = self._map_query_complexity_to_llm(routing_decision.complexity)

                # Determine max_tokens based on complexity
                if routing_decision.complexity == QueryComplexity.COMPLEX:
                    max_tokens = 2000  # Detailed analytical responses
                elif routing_decision.complexity == QueryComplexity.SIMPLE:
                    max_tokens = 300   # Concise responses
                else:
                    max_tokens = 800   # Medium responses

                # Use the LLM service to generate actual response
                response = await self.llm_service.synthesize_response(
                    query=query,
                    tool_results=tool_results,
                    complexity=llm_complexity,
                    max_tokens=max_tokens
                )

                if websocket:
                    await websocket.send_json({
                        "type": "workflow_step",
                        "step": "synthesis",
                        "message": "Generated AI response",
                        "message_id": context.get("message_id") if context else None
                    })

            except Exception as e:
                logger.error(f"LLM synthesis error: {e}")
                # Fallback response
                response = f"Je suis désolé, j'ai rencontré une erreur lors de la génération de la réponse: {str(e)}"

            metrics["synthesis_time"] = time.time() - synthesis_start

            # Cache the response
            await self.cache.set(cache_key, response, "agent_response")

            # Send final result
            total_time = time.time() - start_time

            if websocket:
                await websocket.send_json({
                    "type": "workflow_result",
                    "response": response,
                    "sources": sources,  # Include sources in WebSocket message
                    "message_id": context.get("message_id") if context else None,
                    "metadata": {
                        "total_time": total_time,
                        "routing_time": metrics["routing_time"],
                        "synthesis_time": metrics["synthesis_time"],
                        "cache_hit": False,
                        "source_count": len(sources)
                    }
                })

            yield {
                "type": "workflow_result",
                "response": response,
                "sources": sources,  # Include sources in yield
                "metadata": {
                    "total_time": total_time,
                    "source_count": len(sources),
                    **metrics
                }
            }

        except Exception as e:
            logger.error(f"Error in optimized streaming: {e}")
            error_response = f"Error: {str(e)}"

            if websocket:
                await websocket.send_json({
                    "type": "error",
                    "message": error_response,
                    "message_id": context.get("message_id") if context else None
                })

            yield {
                "type": "error",
                "message": error_response
            }

