"""
Chat service for agricultural chatbot
Handles conversation management and message processing
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import selectinload

from app.models.conversation import Conversation, Message, ConversationStatus
from app.models.user import User
from app.schemas.chat import ConversationCreate, ChatMessage
from app.agents import orchestrator
from app.services.advanced_langchain_service import AdvancedLangChainService
from app.services.langgraph_workflow_service import LangGraphWorkflowService
from app.services.memory_service import MemoryService
from app.services.multi_agent_service import MultiAgentService
from app.services.performance_optimization_service import PerformanceOptimizationService, performance_monitor
import logging

logger = logging.getLogger(__name__)


class ChatService:
    """Service for managing chat conversations and messages"""

    def __init__(self):
        # Initialize all advanced services
        self.advanced_langchain_service = None
        self.workflow_service = None
        self.memory_service = None
        self.multi_agent_service = None
        self.performance_service = None
        self._initialize_all_services()

    def _initialize_all_services(self):
        """Initialize all advanced AI services"""
        try:
            # Initialize performance optimization first
            self.performance_service = PerformanceOptimizationService()
            logger.info("Performance optimization service initialized")

            # Initialize memory service
            self.memory_service = MemoryService()
            logger.info("Memory service initialized")

            # Initialize advanced LangChain service
            self.advanced_langchain_service = AdvancedLangChainService()
            logger.info("Advanced LangChain service initialized")

            # Initialize LangGraph workflow service
            self.workflow_service = LangGraphWorkflowService()
            logger.info("LangGraph workflow service initialized")

            # Initialize multi-agent service
            self.multi_agent_service = MultiAgentService()
            logger.info("Multi-agent service initialized")

            logger.info("🚀 ALL ADVANCED AI SERVICES INITIALIZED SUCCESSFULLY!")

        except Exception as e:
            logger.error(f"Failed to initialize advanced services: {e}")
            # Set fallback to None for failed services
            self.advanced_langchain_service = None
            self.workflow_service = None
            self.memory_service = None
            self.multi_agent_service = None
    
    async def create_conversation(
        self,
        db: AsyncSession,
        user_id: str,
        agent_type: str,
        farm_siret: Optional[str] = None,
        title: Optional[str] = None
    ) -> Conversation:
        """Create a new conversation"""
        # Generate title if not provided
        if not title:
            title = f"Conversation avec {agent_type.replace('_', ' ').title()}"
        
        conversation = Conversation(
            user_id=user_id,
            agent_type=agent_type,
            farm_siret=farm_siret,
            title=title,
            status=ConversationStatus.ACTIVE
        )
        
        db.add(conversation)
        await db.commit()
        await db.refresh(conversation)
        
        return conversation
    
    async def get_conversation(
        self,
        db: AsyncSession,
        conversation_id: str,
        user_id: str
    ) -> Optional[Conversation]:
        """Get a conversation by ID for a specific user"""
        result = await db.execute(
            select(Conversation)
            .where(
                and_(
                    Conversation.id == conversation_id,
                    Conversation.user_id == user_id
                )
            )
            .options(selectinload(Conversation.messages))
        )
        return result.scalar_one_or_none()
    
    async def get_user_conversations(
        self,
        db: AsyncSession,
        user_id: str,
        skip: int = 0,
        limit: int = 50
    ) -> List[Conversation]:
        """Get user's conversations"""
        result = await db.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(desc(Conversation.updated_at))
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_conversation_messages(
        self,
        db: AsyncSession,
        conversation_id: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Message]:
        """Get messages from a conversation"""
        result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at)
            .offset(skip)
            .limit(limit)
        )
        return result.scalars().all()
    
    async def save_message(
        self,
        db: AsyncSession,
        conversation_id: str,
        content: str,
        sender: str,
        agent_type: Optional[str] = None,
        message_type: str = "text",
        metadata: Optional[dict] = None
    ) -> Message:
        """Save a message to a conversation"""
        message = Message(
            conversation_id=conversation_id,
            content=content,
            sender=sender,
            agent_type=agent_type,
            message_type=message_type,
            metadata=metadata
        )
        
        db.add(message)
        
        # Update conversation's last message timestamp
        conversation = await db.get(Conversation, conversation_id)
        if conversation:
            conversation.last_message_at = message.created_at
        
        await db.commit()
        await db.refresh(message)
        
        return message
    
    async def update_conversation_title(
        self,
        db: AsyncSession,
        conversation_id: str,
        title: str
    ) -> Optional[Conversation]:
        """Update conversation title"""
        conversation = await db.get(Conversation, conversation_id)
        if conversation:
            conversation.title = title
            await db.commit()
            await db.refresh(conversation)
        return conversation
    
    async def archive_conversation(
        self,
        db: AsyncSession,
        conversation_id: str,
        user_id: str
    ) -> Optional[Conversation]:
        """Archive a conversation"""
        conversation = await self.get_conversation(db, conversation_id, user_id)
        if conversation:
            conversation.status = ConversationStatus.ARCHIVED
            await db.commit()
            await db.refresh(conversation)
        return conversation
    
    async def delete_conversation(
        self,
        db: AsyncSession,
        conversation_id: str,
        user_id: str
    ) -> bool:
        """Delete a conversation (soft delete)"""
        conversation = await self.get_conversation(db, conversation_id, user_id)
        if conversation:
            conversation.status = ConversationStatus.DELETED
            await db.commit()
            return True
        return False
    
    async def get_conversation_summary(
        self,
        db: AsyncSession,
        conversation_id: str
    ) -> Optional[dict]:
        """Get conversation summary with message count and last activity"""
        conversation = await db.get(Conversation, conversation_id)
        if not conversation:
            return None
        
        # Get message count
        result = await db.execute(
            select(Message)
            .where(Message.conversation_id == conversation_id)
        )
        messages = result.scalars().all()
        
        return {
            "id": str(conversation.id),
            "title": conversation.title,
            "agent_type": conversation.agent_type,
            "message_count": len(messages),
            "last_message_at": conversation.last_message_at,
            "created_at": conversation.created_at,
            "status": conversation.status
        }
    
    async def search_conversations(
        self,
        db: AsyncSession,
        user_id: str,
        query: str,
        agent_type: Optional[str] = None,
        limit: int = 20
    ) -> List[Conversation]:
        """Search conversations by title or content"""
        search_query = select(Conversation).where(
            and_(
                Conversation.user_id == user_id,
                Conversation.status == ConversationStatus.ACTIVE
            )
        )
        
        if query:
            search_query = search_query.where(
                Conversation.title.ilike(f"%{query}%")
            )
        
        if agent_type:
            search_query = search_query.where(
                Conversation.agent_type == agent_type
            )
        
        search_query = search_query.order_by(desc(Conversation.updated_at)).limit(limit)
        
        result = await db.execute(search_query)
        return result.scalars().all()
    
    async def get_conversation_statistics(
        self,
        db: AsyncSession,
        user_id: str
    ) -> dict:
        """Get conversation statistics for a user"""
        # Total conversations
        total_result = await db.execute(
            select(Conversation)
            .where(Conversation.user_id == user_id)
        )
        total_conversations = len(total_result.scalars().all())
        
        # Active conversations
        active_result = await db.execute(
            select(Conversation)
            .where(
                and_(
                    Conversation.user_id == user_id,
                    Conversation.status == ConversationStatus.ACTIVE
                )
            )
        )
        active_conversations = len(active_result.scalars().all())
        
        # Messages count
        messages_result = await db.execute(
            select(Message)
            .join(Conversation)
            .where(Conversation.user_id == user_id)
        )
        total_messages = len(messages_result.scalars().all())
        
        return {
            "total_conversations": total_conversations,
            "active_conversations": active_conversations,
            "total_messages": total_messages
        }
    
    @performance_monitor("process_message_with_agent")
    async def process_message_with_agent(
        self,
        db: AsyncSession,
        conversation_id: str,
        user_id: str,
        message_content: str,
        farm_siret: Optional[str] = None
    ) -> dict:
        """Process a user message with the most advanced AI capabilities available"""
        try:
            # Get conversation to determine agent type
            conversation = await self.get_conversation(db, conversation_id, user_id)
            if not conversation:
                raise ValueError("Conversation not found")

            # Create enhanced context
            context = {
                "conversation_id": conversation_id,
                "user_id": user_id,
                "farm_siret": farm_siret or conversation.farm_siret,
                "agent_type": conversation.agent_type,
                "conversation_title": conversation.title
            }

            # Determine processing strategy
            processing_strategy = self._determine_processing_strategy(message_content, context)
            logger.info(f"🎯 Processing strategy: {processing_strategy}")

            result = None

            # Strategy 1: Multi-Agent for complex queries
            if processing_strategy == "multi_agent" and self.multi_agent_service:
                try:
                    logger.info("🤖 Using MULTI-AGENT processing")
                    result = await self.multi_agent_service.process_multi_agent_query(
                        query=message_content,
                        context=context,
                        conversation_id=conversation_id
                    )
                    result["processing_method"] = "multi_agent"
                except Exception as e:
                    logger.warning(f"Multi-agent processing failed: {e}")

            # Strategy 2: LangGraph Workflow for structured queries
            if not result and processing_strategy in ["workflow", "multi_agent"] and self.workflow_service:
                try:
                    logger.info("🔄 Using LANGGRAPH WORKFLOW processing")
                    result = await self.workflow_service.process_agricultural_query(
                        query=message_content,
                        context=context
                    )
                    result["processing_method"] = "langgraph_workflow"
                except Exception as e:
                    logger.warning(f"LangGraph workflow processing failed: {e}")

            # Strategy 3: Advanced LangChain for general queries
            if not result and self.advanced_langchain_service:
                try:
                    logger.info("🧠 Using ADVANCED LANGCHAIN processing")

                    # Use performance optimization
                    if self.performance_service:
                        result = await self.performance_service.optimize_query_execution(
                            query_func=self.advanced_langchain_service.process_query,
                            query=message_content,
                            context=context,
                            cache_category="general_query"
                        )
                    else:
                        result = await self.advanced_langchain_service.process_query(
                            query=message_content,
                            context=context,
                            use_rag=True,
                            use_reasoning_chains=True,
                            use_tools=True
                        )

                    result["processing_method"] = "advanced_langchain"
                except Exception as e:
                    logger.warning(f"Advanced LangChain processing failed: {e}")

            # Try LangGraph workflow as secondary option
            if not result and self.langgraph_workflow_service:
                try:
                    logger.info("⚡ Using LANGGRAPH WORKFLOW (secondary)")

                    langgraph_result = await self.langgraph_workflow_service.process_agricultural_query(
                        query=message_content,
                        context=context
                    )

                    if langgraph_result.get("response"):
                        result = {
                            "response": langgraph_result["response"],
                            "agent_type": langgraph_result.get("agent_type", "langgraph"),
                            "confidence": langgraph_result.get("confidence", 0.8),
                            "processing_method": "langgraph_workflow",
                            "metadata": langgraph_result.get("metadata", {})
                        }

                except Exception as e:
                    logger.warning(f"LangGraph workflow processing failed: {e}")

            # Fallback to basic orchestrator (last resort)
            if not result:
                logger.info("⚡ Using BASIC ORCHESTRATOR (last resort)")
                from app.services.agent_orchestrator import AgentOrchestrator
                basic_orchestrator = AgentOrchestrator()

                basic_result = basic_orchestrator.process_message(
                    message=message_content,
                    user_id=user_id,
                    farm_id=farm_siret,
                    context=context
                )

                result = {
                    "response": basic_result.get("response", ""),
                    "agent_type": basic_result.get("agent", conversation.agent_type),
                    "confidence": 0.5,
                    "processing_method": "basic_orchestrator_fallback",
                    "metadata": basic_result.get("metadata", {})
                }

            # Save messages with memory enhancement
            user_message, ai_message = await self._save_enhanced_conversation_turn(
                db=db,
                conversation_id=conversation_id,
                user_message=message_content,
                ai_response=result.get("response", ""),
                user_id=user_id,
                farm_siret=context.get("farm_siret"),
                result_metadata=result
            )

            # Enhance result with additional metadata
            enhanced_result = self._enhance_result_metadata(result, conversation_id, processing_strategy)

            return {
                "user_message": {
                    "id": str(user_message.id),
                    "content": user_message.content,
                    "created_at": user_message.created_at.isoformat()
                },
                "ai_response": {
                    "id": str(ai_message.id),
                    "content": enhanced_result.get("response", ""),
                    "agent": enhanced_result.get("agent_type", conversation.agent_type),
                    "created_at": ai_message.created_at.isoformat(),
                    "metadata": enhanced_result.get("metadata", {}),
                    "processing_method": enhanced_result.get("processing_method", "unknown"),
                    "confidence": enhanced_result.get("confidence", 0.0)
                }
            }

        except Exception as e:
            logger.error(f"Error processing message with agent: {e}")
            raise

    def _determine_processing_strategy(self, message_content: str, context: Dict[str, Any]) -> str:
        """Determine the best processing strategy for the message"""
        message_lower = message_content.lower()

        # Complex multi-domain queries need multi-agent
        complexity_indicators = [
            "météo", "réglementation", "conformité", "traitement", "parcelle",
            "intervention", "planification", "optimisation"
        ]

        matching_domains = sum(1 for indicator in complexity_indicators if indicator in message_lower)

        if matching_domains >= 3:
            return "multi_agent"
        elif matching_domains >= 2:
            return "workflow"
        else:
            return "advanced"

    async def _save_enhanced_conversation_turn(
        self,
        db: AsyncSession,
        conversation_id: str,
        user_message: str,
        ai_response: str,
        user_id: str,
        farm_siret: Optional[str],
        result_metadata: Dict[str, Any]
    ) -> Tuple[Any, Any]:
        """Save conversation turn with memory enhancement"""

        # Save user message
        user_msg = await self.save_message(
            db=db,
            conversation_id=conversation_id,
            content=user_message,
            sender="user",
            message_type="text"
        )

        # Save AI response
        ai_msg = await self.save_message(
            db=db,
            conversation_id=conversation_id,
            content=ai_response,
            sender="assistant",
            agent_type=result_metadata.get("agent_type", "general"),
            message_type="text",
            metadata=result_metadata.get("metadata", {})
        )

        # Save to memory service if available
        if self.memory_service:
            try:
                self.memory_service.save_conversation_turn(
                    conversation_id=conversation_id,
                    user_id=user_id,
                    user_message=user_message,
                    ai_response=ai_response,
                    farm_siret=farm_siret
                )
            except Exception as e:
                logger.warning(f"Failed to save to memory service: {e}")

        return user_msg, ai_msg

    def _enhance_result_metadata(
        self,
        result: Dict[str, Any],
        conversation_id: str,
        processing_strategy: str
    ) -> Dict[str, Any]:
        """Enhance result with additional metadata"""

        enhanced = {
            **result,
            "conversation_id": conversation_id,
            "processing_strategy": processing_strategy,
            "timestamp": datetime.now().isoformat(),
            "services_available": {
                "advanced_langchain": self.advanced_langchain_service is not None,
                "workflow": self.workflow_service is not None,
                "multi_agent": self.multi_agent_service is not None,
                "memory": self.memory_service is not None,
                "performance": self.performance_service is not None
            }
        }

        # Add confidence indicator
        confidence = enhanced.get("confidence", 0.0)
        if confidence > 0.8:
            enhanced["confidence_level"] = "high"
        elif confidence > 0.6:
            enhanced["confidence_level"] = "medium"
        else:
            enhanced["confidence_level"] = "low"

        return enhanced

    def get_service_status(self) -> Dict[str, Any]:
        """Get status of all AI services"""
        return {
            "advanced_langchain": {
                "available": self.advanced_langchain_service is not None,
                "status": "active" if self.advanced_langchain_service else "inactive"
            },
            "workflow": {
                "available": self.workflow_service is not None,
                "status": "active" if self.workflow_service else "inactive"
            },
            "multi_agent": {
                "available": self.multi_agent_service is not None,
                "status": "active" if self.multi_agent_service else "inactive"
            },
            "memory": {
                "available": self.memory_service is not None,
                "status": "active" if self.memory_service else "inactive"
            },
            "performance": {
                "available": self.performance_service is not None,
                "status": "active" if self.performance_service else "inactive"
            }
        }

    def get_available_agents(self) -> List[dict]:
        """Get list of available AI agents"""
        try:
            agent_names = orchestrator.get_available_agents()
            agents = []
            
            for name in agent_names:
                agent_info = orchestrator.get_agent_info(name)
                if agent_info:
                    agents.append(agent_info)
            
            return agents
            
        except Exception as e:
            logger.error(f"Error getting available agents: {e}")
            return []
