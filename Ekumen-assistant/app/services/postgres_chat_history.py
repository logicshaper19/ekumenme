"""
PostgreSQL-backed Chat Message History for LangChain
Integrates with existing messages table
"""

import logging
from typing import List
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from datetime import datetime

logger = logging.getLogger(__name__)


class PostgresChatMessageHistory(BaseChatMessageHistory):
    """
    Chat message history backed by PostgreSQL
    Integrates with existing messages table for automatic history management
    """
    
    def __init__(self, session_id: str, db_session: AsyncSession):
        """
        Initialize PostgreSQL chat history
        
        Args:
            session_id: Conversation ID (UUID as string)
            db_session: Async SQLAlchemy session
        """
        self.session_id = session_id
        self.db_session = db_session
        self._messages: List[BaseMessage] = []
        self._loaded = False
    
    @property
    def messages(self) -> List[BaseMessage]:
        """
        Get messages for this conversation
        Lazy loads from database on first access
        """
        if not self._loaded:
            # Synchronously load messages
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If we're in an async context, we need to handle this differently
                    # For now, return cached messages
                    return self._messages
                else:
                    self._messages = loop.run_until_complete(self._load_messages())
                    self._loaded = True
            except Exception as e:
                logger.error(f"Failed to load messages: {e}")
                return []
        
        return self._messages
    
    async def _load_messages(self) -> List[BaseMessage]:
        """Load messages from PostgreSQL"""
        try:
            # Convert session_id to UUID if it's a string
            from uuid import UUID
            try:
                conversation_uuid = UUID(self.session_id) if isinstance(self.session_id, str) else self.session_id
            except ValueError:
                # If not a valid UUID, return empty list
                logger.warning(f"Invalid UUID format for conversation_id: {self.session_id}")
                return []

            query = text("""
                SELECT content, sender, created_at
                FROM messages
                WHERE conversation_id = :conversation_id
                ORDER BY created_at ASC
                LIMIT 100
            """)

            result = await self.db_session.execute(
                query,
                {"conversation_id": conversation_uuid}
            )
            
            messages = []
            for row in result.fetchall():
                content, sender, created_at = row
                if sender == "user":
                    messages.append(HumanMessage(content=content))
                else:
                    messages.append(AIMessage(content=content))
            
            logger.info(f"Loaded {len(messages)} messages for conversation {self.session_id}")
            return messages
            
        except Exception as e:
            logger.error(f"Error loading messages from database: {e}")
            return []
    
    async def aget_messages(self) -> List[BaseMessage]:
        """Async get messages"""
        if not self._loaded:
            self._messages = await self._load_messages()
            self._loaded = True
        return self._messages
    
    def add_message(self, message: BaseMessage) -> None:
        """
        Add message to history
        Note: This is synchronous but schedules async save
        """
        # Add to cache immediately
        self._messages.append(message)
        
        # Schedule async save
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Create task to save message
                asyncio.create_task(self._save_message(message))
            else:
                loop.run_until_complete(self._save_message(message))
        except Exception as e:
            logger.error(f"Failed to save message: {e}")
    
    async def aadd_messages(self, messages: List[BaseMessage]) -> None:
        """Async add multiple messages"""
        for message in messages:
            await self._save_message(message)
            self._messages.append(message)
    
    async def _save_message(self, message: BaseMessage) -> None:
        """Save message to PostgreSQL"""
        try:
            # Convert session_id to UUID if it's a string
            from uuid import UUID
            try:
                conversation_uuid = UUID(self.session_id) if isinstance(self.session_id, str) else self.session_id
            except ValueError:
                logger.warning(f"Invalid UUID format for conversation_id: {self.session_id}")
                return

            query = text("""
                INSERT INTO messages
                (conversation_id, content, sender, message_type, created_at)
                VALUES (:conversation_id, :content, :sender, 'text', :created_at)
            """)

            sender = "user" if isinstance(message, HumanMessage) else "agent"

            await self.db_session.execute(query, {
                "conversation_id": conversation_uuid,
                "content": message.content,
                "sender": sender,
                "created_at": datetime.utcnow()
            })
            await self.db_session.commit()

            logger.debug(f"Saved {sender} message to conversation {self.session_id}")

        except Exception as e:
            logger.error(f"Error saving message to database: {e}")
            await self.db_session.rollback()
    
    def clear(self) -> None:
        """Clear all messages for this conversation"""
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.create_task(self._clear_messages())
            else:
                loop.run_until_complete(self._clear_messages())
        except Exception as e:
            logger.error(f"Failed to clear messages: {e}")
    
    async def aclear(self) -> None:
        """Async clear messages"""
        await self._clear_messages()
    
    async def _clear_messages(self) -> None:
        """Clear messages from database"""
        try:
            query = text("""
                DELETE FROM messages
                WHERE conversation_id = :conversation_id
            """)
            
            await self.db_session.execute(
                query,
                {"conversation_id": self.session_id}
            )
            await self.db_session.commit()
            
            self._messages = []
            self._loaded = True
            
            logger.info(f"Cleared messages for conversation {self.session_id}")
            
        except Exception as e:
            logger.error(f"Error clearing messages from database: {e}")
            await self.db_session.rollback()


class AsyncPostgresChatMessageHistory(BaseChatMessageHistory):
    """
    Fully async version of PostgreSQL chat history
    Use this for async contexts
    """
    
    def __init__(self, session_id: str, db_session: AsyncSession):
        self.session_id = session_id
        self.db_session = db_session
        self._messages: List[BaseMessage] = []
        self._loaded = False
    
    @property
    def messages(self) -> List[BaseMessage]:
        """Return cached messages"""
        return self._messages
    
    async def aget_messages(self) -> List[BaseMessage]:
        """Async get messages - loads from DB if not loaded"""
        if not self._loaded:
            await self._load_messages()
        return self._messages
    
    async def _load_messages(self) -> None:
        """Load messages from PostgreSQL"""
        try:
            # Convert session_id to UUID if it's a string
            from uuid import UUID
            try:
                conversation_uuid = UUID(self.session_id) if isinstance(self.session_id, str) else self.session_id
            except ValueError:
                logger.warning(f"Invalid UUID format for conversation_id: {self.session_id}")
                self._messages = []
                return

            query = text("""
                SELECT content, sender, created_at, message_metadata
                FROM messages
                WHERE conversation_id = :conversation_id
                ORDER BY created_at ASC
                LIMIT 100
            """)

            result = await self.db_session.execute(
                query,
                {"conversation_id": conversation_uuid}
            )
            
            self._messages = []
            for row in result.fetchall():
                content, sender, created_at, metadata = row
                if sender == "user":
                    self._messages.append(HumanMessage(content=content))
                else:
                    self._messages.append(AIMessage(content=content))
            
            self._loaded = True
            logger.info(f"Loaded {len(self._messages)} messages for conversation {self.session_id}")
            
        except Exception as e:
            logger.error(f"Error loading messages: {e}")
            self._messages = []
    
    def add_message(self, message: BaseMessage) -> None:
        """Add message (sync interface)"""
        self._messages.append(message)
    
    async def aadd_messages(self, messages: List[BaseMessage]) -> None:
        """Async add multiple messages"""
        for message in messages:
            await self._save_message(message)
            self._messages.append(message)
    
    async def _save_message(self, message: BaseMessage) -> None:
        """Save message to database"""
        try:
            # Convert session_id to UUID if it's a string
            from uuid import UUID
            try:
                conversation_uuid = UUID(self.session_id) if isinstance(self.session_id, str) else self.session_id
            except ValueError:
                logger.warning(f"Invalid UUID format for conversation_id: {self.session_id}")
                return

            query = text("""
                INSERT INTO messages
                (conversation_id, content, sender, message_type, created_at)
                VALUES (:conversation_id, :content, :sender, 'text', :created_at)
            """)

            sender = "user" if isinstance(message, HumanMessage) else "agent"

            await self.db_session.execute(query, {
                "conversation_id": conversation_uuid,
                "content": message.content,
                "sender": sender,
                "created_at": datetime.utcnow()
            })
            await self.db_session.commit()

        except Exception as e:
            logger.error(f"Error saving message: {e}")
            await self.db_session.rollback()
    
    def clear(self) -> None:
        """Clear messages (sync interface)"""
        self._messages = []
    
    async def aclear(self) -> None:
        """Async clear messages"""
        try:
            query = text("""
                DELETE FROM messages
                WHERE conversation_id = :conversation_id
            """)
            
            await self.db_session.execute(
                query,
                {"conversation_id": self.session_id}
            )
            await self.db_session.commit()
            
            self._messages = []
            self._loaded = True
            
        except Exception as e:
            logger.error(f"Error clearing messages: {e}")
            await self.db_session.rollback()


def get_session_history(session_id: str, db_session: AsyncSession) -> BaseChatMessageHistory:
    """
    Factory function to get message history for a session
    Used by RunnableWithMessageHistory
    
    Args:
        session_id: Conversation ID
        db_session: Database session
        
    Returns:
        BaseChatMessageHistory instance
    """
    return AsyncPostgresChatMessageHistory(session_id, db_session)

