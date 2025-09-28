"""
Chat schemas for agricultural chatbot
Pydantic models for chat and conversation management
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.conversation import AgentType


class ConversationCreate(BaseModel):
    """Schema for creating a new conversation"""
    agent_type: AgentType
    farm_siret: Optional[str] = Field(None, max_length=14)
    title: Optional[str] = Field(None, max_length=255)
    
    @validator('farm_siret')
    def validate_siret(cls, v):
        if v and len(v) != 14:
            raise ValueError('SIRET must be exactly 14 characters')
        return v


class ConversationResponse(BaseModel):
    """Schema for conversation response"""
    id: str
    title: str
    agent_type: AgentType
    farm_siret: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ChatMessage(BaseModel):
    """Schema for chat message"""
    content: str = Field(..., min_length=1, max_length=10000)
    sender: str = Field(..., pattern="^(user|agent)$")
    timestamp: Optional[datetime] = None
    
    @validator('content')
    def validate_content(cls, v):
        if not v.strip():
            raise ValueError('Message content cannot be empty')
        return v.strip()


class ChatResponse(BaseModel):
    """Schema for chat response from agent"""
    content: str
    agent_type: AgentType
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None
    
    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    """Schema for creating a new message"""
    content: str = Field(..., min_length=1, max_length=10000)
    
    @validator('content')
    def validate_content(cls, v):
        if not v.strip():
            raise ValueError('Message content cannot be empty')
        return v.strip()


class ConversationUpdate(BaseModel):
    """Schema for updating conversation"""
    title: Optional[str] = Field(None, max_length=255)
    farm_siret: Optional[str] = Field(None, max_length=14)
    
    @validator('farm_siret')
    def validate_siret(cls, v):
        if v and len(v) != 14:
            raise ValueError('SIRET must be exactly 14 characters')
        return v


class ConversationSummary(BaseModel):
    """Schema for conversation summary"""
    id: str
    title: str
    agent_type: AgentType
    message_count: int
    last_message_at: Optional[datetime]
    created_at: datetime
    
    class Config:
        from_attributes = True


class AgentCapabilities(BaseModel):
    """Schema for agent capabilities"""
    agent_type: AgentType
    name: str
    description: str
    capabilities: List[str]
    supported_farm_types: List[str]
    language: str = "fr"


class ChatContext(BaseModel):
    """Schema for chat context"""
    user_id: str
    farm_siret: Optional[str]
    agent_type: AgentType
    conversation_id: Optional[str]
    context_data: Optional[Dict[str, Any]] = None
