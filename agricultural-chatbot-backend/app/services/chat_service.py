"""
Chat service for agricultural chatbot
Handles conversation management and message processing
"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, desc
from sqlalchemy.orm import selectinload

from app.models.conversation import Conversation, Message, ConversationStatus
from app.models.user import User
from app.schemas.chat import ConversationCreate, ChatMessage
from app.agents import orchestrator
import logging

logger = logging.getLogger(__name__)


class ChatService:
    """Service for managing chat conversations and messages"""
    
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
    
    async def process_message_with_agent(
        self,
        db: AsyncSession,
        conversation_id: str,
        user_id: str,
        message_content: str,
        farm_siret: Optional[str] = None
    ) -> dict:
        """Process a user message with the appropriate AI agent"""
        try:
            # Get conversation to determine agent type
            conversation = await self.get_conversation(db, conversation_id, user_id)
            if not conversation:
                raise ValueError("Conversation not found")
            
            # Save user message
            user_message = await self.save_message(
                db=db,
                conversation_id=conversation_id,
                content=message_content,
                sender="user",
                message_type="text"
            )
            
            # Process with AI agent using orchestrator
            context = {
                "conversation_id": conversation_id,
                "farm_siret": farm_siret,
                "agent_type": conversation.agent_type
            }
            
            agent_response = orchestrator.process_message(
                message=message_content,
                user_id=user_id,
                farm_id=farm_siret,
                context=context
            )
            
            # Save AI response
            ai_message = await self.save_message(
                db=db,
                conversation_id=conversation_id,
                content=agent_response["response"],
                sender="assistant",
                agent_type=agent_response.get("agent", conversation.agent_type),
                message_type="text",
                metadata=agent_response.get("metadata", {})
            )
            
            return {
                "user_message": {
                    "id": str(user_message.id),
                    "content": user_message.content,
                    "created_at": user_message.created_at.isoformat()
                },
                "ai_response": {
                    "id": str(ai_message.id),
                    "content": ai_message.content,
                    "agent": agent_response.get("agent", conversation.agent_type),
                    "created_at": ai_message.created_at.isoformat(),
                    "metadata": agent_response.get("metadata", {})
                }
            }
            
        except Exception as e:
            logger.error(f"Error processing message with agent: {e}")
            raise
    
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
