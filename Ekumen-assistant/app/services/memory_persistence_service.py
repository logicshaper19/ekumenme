"""
Memory Persistence Service for Agricultural AI
Conversation context retention across sessions with agricultural context
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import json
import pickle
import hashlib

from langchain.memory import ConversationBufferWindowMemory, ConversationSummaryMemory
from langchain.schema import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


class MemoryPersistenceService:
    """Advanced memory persistence for agricultural conversations"""
    
    def __init__(self):
        self.llm = None
        self.session_memories = {}  # In-memory cache
        self.conversation_summaries = {}
        self.agricultural_context = {}
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize memory persistence components"""
        try:
            # Initialize LLM for summarization
            self.llm = ChatOpenAI(
                model_name="gpt-4",
                temperature=0.1,
                openai_api_key=settings.OPENAI_API_KEY
            )
            
            logger.info("Memory persistence service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize memory persistence: {e}")
            raise
    
    async def get_conversation_memory(
        self,
        user_id: str,
        conversation_id: Optional[str] = None,
        memory_type: str = "buffer_window"
    ) -> ConversationBufferWindowMemory:
        """Get or create conversation memory for user"""
        try:
            # Create memory key
            memory_key = f"{user_id}_{conversation_id or 'default'}"
            
            # Check cache first
            if memory_key in self.session_memories:
                return self.session_memories[memory_key]
            
            # Load from database
            memory = await self._load_memory_from_db(user_id, conversation_id, memory_type)
            
            # Cache memory
            self.session_memories[memory_key] = memory
            
            return memory
            
        except Exception as e:
            logger.error(f"Failed to get conversation memory: {e}")
            # Return default memory
            return ConversationBufferWindowMemory(
                k=10,
                memory_key="chat_history",
                return_messages=True
            )
    
    async def save_conversation_memory(
        self,
        user_id: str,
        memory: ConversationBufferWindowMemory,
        conversation_id: Optional[str] = None,
        agricultural_context: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Save conversation memory to database"""
        try:
            memory_key = f"{user_id}_{conversation_id or 'default'}"
            
            # Update cache
            self.session_memories[memory_key] = memory
            
            # Save agricultural context
            if agricultural_context:
                self.agricultural_context[memory_key] = agricultural_context
            
            # Save to database
            success = await self._save_memory_to_db(user_id, memory, conversation_id, agricultural_context)
            
            # Create conversation summary if needed
            if len(memory.chat_memory.messages) > 20:
                await self._create_conversation_summary(user_id, memory, conversation_id)
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to save conversation memory: {e}")
            return False
    
    async def get_agricultural_context(
        self,
        user_id: str,
        conversation_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get agricultural context for user conversations"""
        try:
            memory_key = f"{user_id}_{conversation_id or 'default'}"
            
            # Check cache
            if memory_key in self.agricultural_context:
                return self.agricultural_context[memory_key]
            
            # Load from database
            context = await self._load_agricultural_context_from_db(user_id, conversation_id)
            
            # Cache context
            self.agricultural_context[memory_key] = context
            
            return context
            
        except Exception as e:
            logger.error(f"Failed to get agricultural context: {e}")
            return {}
    
    async def update_agricultural_context(
        self,
        user_id: str,
        context_updates: Dict[str, Any],
        conversation_id: Optional[str] = None
    ) -> bool:
        """Update agricultural context with new information"""
        try:
            memory_key = f"{user_id}_{conversation_id or 'default'}"
            
            # Get existing context
            current_context = await self.get_agricultural_context(user_id, conversation_id)
            
            # Merge updates
            current_context.update(context_updates)
            
            # Update cache
            self.agricultural_context[memory_key] = current_context
            
            # Save to database
            return await self._save_agricultural_context_to_db(user_id, current_context, conversation_id)
            
        except Exception as e:
            logger.error(f"Failed to update agricultural context: {e}")
            return False
    
    async def get_conversation_summary(
        self,
        user_id: str,
        conversation_id: Optional[str] = None
    ) -> Optional[str]:
        """Get conversation summary for context"""
        try:
            memory_key = f"{user_id}_{conversation_id or 'default'}"
            
            # Check cache
            if memory_key in self.conversation_summaries:
                return self.conversation_summaries[memory_key]
            
            # Load from database
            summary = await self._load_conversation_summary_from_db(user_id, conversation_id)
            
            # Cache summary
            if summary:
                self.conversation_summaries[memory_key] = summary
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to get conversation summary: {e}")
            return None
    
    async def _load_memory_from_db(
        self,
        user_id: str,
        conversation_id: Optional[str],
        memory_type: str
    ) -> ConversationBufferWindowMemory:
        """Load memory from database"""
        try:
            async with AsyncSessionLocal() as session:
                # Query conversation history
                query = text("""
                    SELECT message_content, message_type, created_at, metadata
                    FROM conversation_history 
                    WHERE user_id = :user_id 
                    AND (:conversation_id IS NULL OR conversation_id = :conversation_id)
                    ORDER BY created_at ASC
                    LIMIT 50
                """)
                
                result = await session.execute(query, {
                    "user_id": user_id,
                    "conversation_id": conversation_id
                })
                
                messages = []
                for row in result.fetchall():
                    content, msg_type, created_at, metadata = row
                    
                    if msg_type == "human":
                        messages.append(HumanMessage(content=content))
                    elif msg_type == "ai":
                        messages.append(AIMessage(content=content))
                
                # Create memory with loaded messages
                if memory_type == "summary":
                    memory = ConversationSummaryMemory(
                        llm=self.llm,
                        memory_key="chat_history",
                        return_messages=True
                    )
                else:
                    memory = ConversationBufferWindowMemory(
                        k=20,
                        memory_key="chat_history",
                        return_messages=True
                    )
                
                # Add messages to memory
                for message in messages:
                    memory.chat_memory.add_message(message)
                
                return memory
                
        except Exception as e:
            logger.error(f"Failed to load memory from database: {e}")
            # Return default memory
            return ConversationBufferWindowMemory(
                k=10,
                memory_key="chat_history",
                return_messages=True
            )
    
    async def _save_memory_to_db(
        self,
        user_id: str,
        memory: ConversationBufferWindowMemory,
        conversation_id: Optional[str],
        agricultural_context: Optional[Dict[str, Any]]
    ) -> bool:
        """Save memory to database"""
        try:
            async with AsyncSessionLocal() as session:
                # Get recent messages from memory
                messages = memory.chat_memory.messages[-10:]  # Save last 10 messages
                
                for message in messages:
                    # Check if message already exists
                    message_hash = hashlib.md5(
                        f"{user_id}_{message.content}_{type(message).__name__}".encode()
                    ).hexdigest()
                    
                    check_query = text("""
                        SELECT id FROM conversation_history 
                        WHERE message_hash = :message_hash
                    """)
                    
                    existing = await session.execute(check_query, {"message_hash": message_hash})
                    
                    if not existing.fetchone():
                        # Insert new message
                        insert_query = text("""
                            INSERT INTO conversation_history 
                            (user_id, conversation_id, message_content, message_type, 
                             message_hash, agricultural_context, created_at)
                            VALUES (:user_id, :conversation_id, :content, :msg_type, 
                                    :message_hash, :agricultural_context, :created_at)
                        """)
                        
                        await session.execute(insert_query, {
                            "user_id": user_id,
                            "conversation_id": conversation_id,
                            "content": message.content,
                            "msg_type": "human" if isinstance(message, HumanMessage) else "ai",
                            "message_hash": message_hash,
                            "agricultural_context": json.dumps(agricultural_context) if agricultural_context else None,
                            "created_at": datetime.utcnow()
                        })
                
                await session.commit()
                return True
                
        except Exception as e:
            logger.error(f"Failed to save memory to database: {e}")
            return False
    
    async def _create_conversation_summary(
        self,
        user_id: str,
        memory: ConversationBufferWindowMemory,
        conversation_id: Optional[str]
    ) -> Optional[str]:
        """Create conversation summary using LLM"""
        try:
            # Get conversation messages
            messages = memory.chat_memory.messages
            
            if len(messages) < 5:
                return None
            
            # Create summary prompt
            conversation_text = "\n".join([
                f"{'Utilisateur' if isinstance(msg, HumanMessage) else 'Assistant'}: {msg.content}"
                for msg in messages[-20:]  # Last 20 messages
            ])
            
            summary_prompt = f"""
            Résumez cette conversation agricole en conservant les informations importantes:
            
            {conversation_text}
            
            Résumé (max 200 mots):
            - Contexte agricole principal
            - Questions posées
            - Recommandations données
            - Informations techniques importantes
            """
            
            summary = self.llm.predict(summary_prompt)
            
            # Save summary
            memory_key = f"{user_id}_{conversation_id or 'default'}"
            self.conversation_summaries[memory_key] = summary
            
            # Save to database
            await self._save_conversation_summary_to_db(user_id, summary, conversation_id)
            
            return summary
            
        except Exception as e:
            logger.error(f"Failed to create conversation summary: {e}")
            return None

    async def _load_agricultural_context_from_db(
        self,
        user_id: str,
        conversation_id: Optional[str]
    ) -> Dict[str, Any]:
        """Load agricultural context from database"""
        try:
            async with AsyncSessionLocal() as session:
                query = text("""
                    SELECT agricultural_context
                    FROM conversation_history
                    WHERE user_id = :user_id
                    AND (:conversation_id IS NULL OR conversation_id = :conversation_id)
                    AND agricultural_context IS NOT NULL
                    ORDER BY created_at DESC
                    LIMIT 1
                """)

                result = await session.execute(query, {
                    "user_id": user_id,
                    "conversation_id": conversation_id
                })

                row = result.fetchone()
                if row and row[0]:
                    return json.loads(row[0])

                return {}

        except Exception as e:
            logger.error(f"Failed to load agricultural context: {e}")
            return {}

    async def cleanup_old_memories(self, days_to_keep: int = 30) -> int:
        """Clean up old conversation memories"""
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

            async with AsyncSessionLocal() as session:
                # Delete old conversation history
                delete_query = text("""
                    DELETE FROM conversation_history
                    WHERE created_at < :cutoff_date
                """)

                result = await session.execute(delete_query, {"cutoff_date": cutoff_date})
                deleted_count = result.rowcount

                await session.commit()

                logger.info(f"Cleaned up {deleted_count} old conversation records")
                return deleted_count

        except Exception as e:
            logger.error(f"Failed to cleanup old memories: {e}")
            return 0
