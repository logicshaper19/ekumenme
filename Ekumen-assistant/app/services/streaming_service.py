"""
Streaming Service for Real-time Agricultural AI Responses
Implements Server-Sent Events and WebSocket streaming
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, AsyncGenerator, Callable
from datetime import datetime
import uuid

from fastapi import WebSocket
from langchain.callbacks.base import BaseCallbackHandler
from langchain.schema import BaseMessage

from app.services.advanced_langchain_service import AdvancedLangChainService
from app.services.langgraph_workflow_service import LangGraphWorkflowService
from app.services.conditional_routing_service import ConditionalRoutingService

logger = logging.getLogger(__name__)


class StreamingCallbackHandler(BaseCallbackHandler):
    """Callback handler for streaming LangChain responses"""
    
    def __init__(self, websocket: WebSocket = None, callback: Callable = None, message_id: str = None):
        self.websocket = websocket
        self.callback = callback
        self.message_id = message_id
        self.tokens = []
        self.current_step = ""
    
    async def on_llm_start(self, serialized: Dict[str, Any], prompts: List[str], **kwargs) -> None:
        """Called when LLM starts generating"""
        message_data = {
            "type": "llm_start",
            "message": "🤖 Analyse en cours...",
            "timestamp": datetime.now().isoformat()
        }

        # Add message_id if available
        if hasattr(self, 'message_id') and self.message_id:
            message_data["message_id"] = self.message_id

        if self.websocket:
            await self.websocket.send_text(json.dumps(message_data))
        elif self.callback:
            await self.callback(message_data)
    
    async def on_llm_new_token(self, token: str, **kwargs) -> None:
        """Called when LLM generates a new token"""
        self.tokens.append(token)

        message_data = {
            "type": "token",
            "token": token,
            "partial_response": "".join(self.tokens),
            "timestamp": datetime.now().isoformat()
        }

        # Add message_id if available
        if hasattr(self, 'message_id') and self.message_id:
            message_data["message_id"] = self.message_id

        if self.websocket:
            await self.websocket.send_text(json.dumps(message_data))
        elif self.callback:
            await self.callback(message_data)
    
    async def on_llm_end(self, response, **kwargs) -> None:
        """Called when LLM finishes generating"""
        message_data = {
            "type": "complete",
            "message": "✅ Analyse terminée",
            "final_response": "".join(self.tokens),
            "timestamp": datetime.now().isoformat()
        }

        # Add message_id if available
        if hasattr(self, 'message_id') and self.message_id:
            message_data["message_id"] = self.message_id

        if self.websocket:
            await self.websocket.send_text(json.dumps(message_data))
        elif self.callback:
            await self.callback(message_data)
    
    async def on_tool_start(self, serialized: Dict[str, Any], input_str: str, **kwargs) -> None:
        """Called when a tool starts executing"""
        tool_name = serialized.get("name", "Unknown")
        
        if self.websocket:
            await self.websocket.send_text(json.dumps({
                "type": "tool_start",
                "tool_name": tool_name,
                "message": f"🔧 Utilisation de l'outil: {tool_name}",
                "timestamp": datetime.now().isoformat()
            }))
        elif self.callback:
            await self.callback({
                "type": "tool_start",
                "tool_name": tool_name,
                "message": f"🔧 Utilisation de l'outil: {tool_name}",
                "timestamp": datetime.now().isoformat()
            })
    
    async def on_tool_end(self, output: str, **kwargs) -> None:
        """Called when a tool finishes executing"""
        if self.websocket:
            await self.websocket.send_text(json.dumps({
                "type": "tool_end",
                "message": "✅ Outil terminé",
                "timestamp": datetime.now().isoformat()
            }))
        elif self.callback:
            await self.callback({
                "type": "tool_end",
                "message": "✅ Outil terminé",
                "timestamp": datetime.now().isoformat()
            })


class StreamingService:
    """Service for streaming agricultural AI responses"""
    
    def __init__(self):
        self.advanced_service = None
        self.workflow_service = None
        self.active_connections: Dict[str, WebSocket] = {}
        self._initialize_services()
    
    def _initialize_services(self):
        """Initialize AI services"""
        try:
            self.advanced_service = AdvancedLangChainService()
            self.workflow_service = LangGraphWorkflowService()
            logger.info("Streaming service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize streaming service: {e}")
    
    async def connect_websocket(self, websocket: WebSocket, connection_id: str = None) -> str:
        """Connect a WebSocket client"""
        if not connection_id:
            connection_id = str(uuid.uuid4())
        
        await websocket.accept()
        self.active_connections[connection_id] = websocket
        
        # Send welcome message
        await websocket.send_text(json.dumps({
            "type": "connection",
            "message": "🌾 Connecté à l'assistant agricole",
            "connection_id": connection_id,
            "timestamp": datetime.now().isoformat()
        }))
        
        logger.info(f"WebSocket connected: {connection_id}")
        return connection_id
    
    async def disconnect_websocket(self, connection_id: str):
        """Disconnect a WebSocket client"""
        if connection_id in self.active_connections:
            del self.active_connections[connection_id]
            logger.info(f"WebSocket disconnected: {connection_id}")
    
    async def stream_response(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        connection_id: str = None,
        use_workflow: bool = True
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream agricultural AI response"""
        try:
            # Send initial status
            initial_message = {
                "type": "start",
                "message": "🌾 Traitement de votre demande agricole...",
                "query": query,
                "timestamp": datetime.now().isoformat()
            }
            
            if connection_id and connection_id in self.active_connections:
                websocket = self.active_connections[connection_id]
                await websocket.send_text(json.dumps(initial_message))
            
            yield initial_message
            
            # Process query
            if use_workflow and self.workflow_service:
                # Use LangGraph workflow
                async for chunk in self._stream_workflow_response(query, context, connection_id):
                    yield chunk
            elif self.advanced_service:
                # Use advanced LangChain service
                async for chunk in self._stream_advanced_response(query, context, connection_id):
                    yield chunk
            else:
                # Fallback response when services are not available
                async for chunk in self._stream_fallback_response(query, context, connection_id):
                    yield chunk
            
            # Send completion message
            completion_message = {
                "type": "complete",
                "message": "✅ Traitement terminé",
                "timestamp": datetime.now().isoformat()
            }
            
            if connection_id and connection_id in self.active_connections:
                websocket = self.active_connections[connection_id]
                await websocket.send_text(json.dumps(completion_message))
            
            yield completion_message
            
        except Exception as e:
            error_message = {
                "type": "error",
                "message": f"❌ Erreur: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
            
            if connection_id and connection_id in self.active_connections:
                websocket = self.active_connections[connection_id]
                await websocket.send_text(json.dumps(error_message))
            
            yield error_message

    async def _stream_fallback_response(
        self,
        query: str,
        context: Optional[Dict[str, Any]],
        connection_id: str = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Fallback response when AI services are not available"""
        try:
            websocket = None
            if connection_id and connection_id in self.active_connections:
                websocket = self.active_connections[connection_id]

            # Send fallback message
            fallback_message = {
                "type": "fallback_response",
                "message": f"🌾 Merci pour votre question: '{query}'. Je suis un assistant agricole en cours de configuration. Voici une réponse basique:",
                "timestamp": datetime.now().isoformat()
            }

            if websocket:
                await websocket.send_text(json.dumps(fallback_message))
            yield fallback_message

            # Simple response based on keywords
            response_text = self._generate_simple_response(query)

            # Stream the response word by word
            words = response_text.split()
            for i, word in enumerate(words):
                token_message = {
                    "type": "token",
                    "token": word + (" " if i < len(words) - 1 else ""),
                    "timestamp": datetime.now().isoformat()
                }

                if websocket:
                    await websocket.send_text(json.dumps(token_message))
                yield token_message

                # Small delay for streaming effect
                await asyncio.sleep(0.05)

            # Final response
            final_message = {
                "type": "workflow_result",
                "response": response_text,
                "timestamp": datetime.now().isoformat()
            }

            if websocket:
                await websocket.send_text(json.dumps(final_message))
            yield final_message

        except Exception as e:
            error_message = {
                "type": "error",
                "message": f"❌ Erreur dans la réponse de secours: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }

            if connection_id and connection_id in self.active_connections:
                websocket = self.active_connections[connection_id]
                await websocket.send_text(json.dumps(error_message))

            yield error_message

    def _generate_simple_response(self, query: str) -> str:
        """Generate a simple response based on keywords"""
        query_lower = query.lower()

        if any(word in query_lower for word in ['météo', 'temps', 'pluie', 'soleil']):
            return "Pour les informations météorologiques, je recommande de consulter Météo-France ou votre station météo locale. Les conditions météo sont cruciales pour planifier vos interventions agricoles."

        elif any(word in query_lower for word in ['traitement', 'produit', 'phyto', 'pesticide']):
            return "Pour les traitements phytosanitaires, vérifiez toujours l'autorisation des produits sur le site e-phy.fr. Respectez les doses homologuées et les délais avant récolte."

        elif any(word in query_lower for word in ['semis', 'plantation', 'culture']):
            return "Pour les semis et plantations, tenez compte de votre région, du type de sol et de la période optimale pour chaque culture. Consultez les calendriers agricoles locaux."

        elif any(word in query_lower for word in ['récolte', 'moisson']):
            return "Pour la récolte, surveillez la maturité des cultures et les conditions météorologiques. Planifiez vos équipements et main-d'œuvre en conséquence."

        else:
            return "Je suis votre assistant agricole. Posez-moi des questions sur la météo, les traitements, les semis, ou la récolte. Je peux vous aider avec des conseils pratiques pour votre exploitation."

    async def _stream_workflow_response(
        self,
        query: str,
        context: Optional[Dict[str, Any]],
        connection_id: str = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream response using LangGraph workflow"""
        try:
            websocket = None
            if connection_id and connection_id in self.active_connections:
                websocket = self.active_connections[connection_id]
            
            # Send workflow start message
            workflow_start = {
                "type": "workflow_start",
                "message": "🔄 Démarrage du workflow agricole...",
                "timestamp": datetime.now().isoformat()
            }
            
            if websocket:
                await websocket.send_text(json.dumps(workflow_start))
            yield workflow_start
            
            # Execute workflow with streaming updates
            result = await self.workflow_service.process_agricultural_query(query, context)
            
            # Stream processing steps
            for step in result.get("processing_steps", []):
                step_message = {
                    "type": "workflow_step",
                    "step": step,
                    "message": f"📋 Étape: {step}",
                    "timestamp": datetime.now().isoformat()
                }
                
                if websocket:
                    await websocket.send_text(json.dumps(step_message))
                yield step_message
                
                # Add small delay for better UX
                await asyncio.sleep(0.5)
            
            # Send final result
            final_result = {
                "type": "workflow_result",
                "response": result.get("response", ""),
                "agent_type": result.get("agent_type", "unknown"),
                "confidence": result.get("confidence", 0.0),
                "recommendations": result.get("recommendations", []),
                "metadata": result.get("metadata", {}),
                "message_id": context.get("message_id"),
                "thread_id": context.get("thread_id"),
                "timestamp": datetime.now().isoformat()
            }
            
            if websocket:
                await websocket.send_text(json.dumps(final_result))
            yield final_result
            
        except Exception as e:
            logger.error(f"Workflow streaming failed: {e}")
            raise
    
    async def _stream_advanced_response(
        self,
        query: str,
        context: Optional[Dict[str, Any]],
        connection_id: str = None
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream response using advanced LangChain service"""
        try:
            websocket = None
            if connection_id and connection_id in self.active_connections:
                websocket = self.active_connections[connection_id]
            
            # Create streaming callback with message_id
            message_id = context.get("message_id") if context else None
            callback_handler = StreamingCallbackHandler(websocket=websocket, message_id=message_id)
            
            # Send advanced processing start
            advanced_start = {
                "type": "advanced_start",
                "message": "🧠 Traitement avancé avec LangChain...",
                "timestamp": datetime.now().isoformat()
            }
            
            if websocket:
                await websocket.send_text(json.dumps(advanced_start))
            yield advanced_start
            
            # Process with advanced service
            result = await self.advanced_service.process_query(
                query=query,
                context=context,
                use_rag=True,
                use_reasoning_chains=True,
                use_tools=True
            )
            
            # Send final result
            final_result = {
                "type": "advanced_result",
                "response": result.get("response", ""),
                "agent_type": result.get("agent_type", "unknown"),
                "confidence": result.get("confidence", 0.0),
                "sources": result.get("sources", []),
                "recommendations": result.get("recommendations", []),
                "regulatory_compliance": result.get("regulatory_compliance"),
                "metadata": result.get("metadata", {}),
                "timestamp": datetime.now().isoformat()
            }
            
            if websocket:
                await websocket.send_text(json.dumps(final_result))
            yield final_result
            
        except Exception as e:
            logger.error(f"Advanced streaming failed: {e}")
            raise
    
    async def broadcast_message(self, message: Dict[str, Any]):
        """Broadcast message to all connected clients"""
        disconnected = []
        
        for connection_id, websocket in self.active_connections.items():
            try:
                await websocket.send_text(json.dumps(message))
            except Exception as e:
                logger.warning(f"Failed to send to {connection_id}: {e}")
                disconnected.append(connection_id)
        
        # Clean up disconnected clients
        for connection_id in disconnected:
            await self.disconnect_websocket(connection_id)
    
    def get_connection_count(self) -> int:
        """Get number of active connections"""
        return len(self.active_connections)
