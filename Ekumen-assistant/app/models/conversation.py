"""
Conversation models for agricultural chatbot
Handles chat conversations with AI agents
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Enum as SQLEnum, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.core.database import Base


class AgentType(str, enum.Enum):
    """Types of agricultural AI agents"""
    FARM_DATA = "farm_data"
    REGULATORY = "regulatory"
    WEATHER = "weather"
    CROP_HEALTH = "crop_health"
    PLANNING = "planning"
    SUSTAINABILITY = "sustainability"


class ConversationStatus(str, enum.Enum):
    """Conversation status"""
    ACTIVE = "active"
    ARCHIVED = "archived"
    DELETED = "deleted"


class Conversation(Base):
    """Conversation model for chat sessions with AI agents"""
    
    __tablename__ = "conversations"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign keys
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    farm_siret = Column(String(14), ForeignKey("farms.siret"), nullable=True, index=True)
    
    # Conversation information
    title = Column(String(255), nullable=False)
    agent_type = Column(SQLEnum(AgentType), nullable=False, index=True)
    status = Column(SQLEnum(ConversationStatus), default=ConversationStatus.ACTIVE, nullable=False)
    
    # Context and metadata
    context_data = Column(JSONB, nullable=True)  # Additional context for the agent
    summary = Column(Text, nullable=True)  # Conversation summary
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_message_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="conversations", lazy="select")
    farm = relationship("Farm", back_populates="conversations", lazy="select")
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", lazy="select")
    
    def __repr__(self):
        return f"<Conversation(id={self.id}, agent_type={self.agent_type}, status={self.status})>"
    
    @property
    def message_count(self) -> int:
        """Get the number of messages in this conversation"""
        return len(self.messages) if self.messages else 0
    
    @property
    def is_active(self) -> bool:
        """Check if conversation is active"""
        return self.status == ConversationStatus.ACTIVE


class Message(Base):
    """Message model for individual chat messages"""
    
    __tablename__ = "messages"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign keys
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False, index=True)
    
    # Message information
    content = Column(Text, nullable=False)
    sender = Column(String(20), nullable=False, index=True)  # "user" or "agent"
    agent_type = Column(SQLEnum(AgentType), nullable=True)  # Only for agent messages

    # Threading information
    thread_id = Column(String(100), nullable=True, index=True)  # For tracking message threads
    parent_message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id"), nullable=True)  # For message replies

    # Message metadata
    message_type = Column(String(50), nullable=True)  # "text", "voice", "image", etc.
    message_metadata = Column(JSONB, nullable=True)  # Additional message data
    
    # Processing information
    processing_time_ms = Column(Integer, nullable=True)  # Time taken to process
    token_count = Column(Integer, nullable=True)  # Number of tokens used
    cost_usd = Column(Numeric(10, 6), nullable=True)  # Cost of processing
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages", lazy="select")
    
    def __repr__(self):
        return f"<Message(id={self.id}, sender={self.sender}, conversation_id={self.conversation_id})>"
    
    @property
    def is_from_user(self) -> bool:
        """Check if message is from user"""
        return self.sender == "user"
    
    @property
    def is_from_agent(self) -> bool:
        """Check if message is from agent"""
        return self.sender == "agent"


class AgentResponse(Base):
    """Agent response tracking for analytics and monitoring"""
    
    __tablename__ = "agent_responses"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign keys
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id"), nullable=False, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False, index=True)
    
    # Agent information
    agent_type = Column(SQLEnum(AgentType), nullable=False, index=True)
    model_used = Column(String(100), nullable=True)  # OpenAI model used
    
    # Response metrics
    response_time_ms = Column(Integer, nullable=False)
    token_count_input = Column(Integer, nullable=True)
    token_count_output = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)
    cost_usd = Column(Numeric(10, 6), nullable=True)
    
    # Quality metrics
    confidence_score = Column(Numeric(3, 2), nullable=True)  # 0.00 to 1.00
    user_rating = Column(Integer, nullable=True)  # 1-5 star rating
    feedback = Column(Text, nullable=True)  # User feedback
    
    # Response data
    response_data = Column(JSONB, nullable=True)  # Full response data
    tools_used = Column(JSONB, nullable=True)  # Tools called during response
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<AgentResponse(id={self.id}, agent_type={self.agent_type}, response_time={self.response_time_ms}ms)>"
    
    @property
    def cost_per_token(self) -> float:
        """Calculate cost per token"""
        if self.total_tokens and self.cost_usd:
            return float(self.cost_usd) / self.total_tokens
        return 0.0
