"""
Response Feedback Model
Tracks user feedback (thumbs up/down) on AI responses
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Enum as SQLEnum, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.core.database import Base


class FeedbackType(str, enum.Enum):
    """Types of feedback"""
    THUMBS_UP = "thumbs_up"
    THUMBS_DOWN = "thumbs_down"


class FeedbackCategory(str, enum.Enum):
    """Categories for negative feedback"""
    INCORRECT = "incorrect"
    INCOMPLETE = "incomplete"
    IRRELEVANT = "irrelevant"
    UNCLEAR = "unclear"
    SLOW = "slow"
    OTHER = "other"


class ResponseFeedback(Base):
    """
    Response feedback model for tracking user satisfaction with AI responses.
    
    Allows users to:
    - Give thumbs up/down on responses
    - Provide detailed feedback comments
    - Categorize issues with responses
    """
    
    __tablename__ = "response_feedback"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign keys
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False, index=True)
    message_id = Column(UUID(as_uuid=True), ForeignKey("messages.id"), nullable=False, index=True)
    
    # Feedback information
    feedback_type = Column(SQLEnum(FeedbackType), nullable=False, index=True)
    feedback_category = Column(SQLEnum(FeedbackCategory), nullable=True)  # Only for thumbs down
    
    # User comments
    comment = Column(Text, nullable=True)  # Optional detailed feedback
    
    # Context at time of feedback
    query_text = Column(Text, nullable=True)  # The user's original query
    response_text = Column(Text, nullable=True)  # The AI's response

    # Additional context
    context_metadata = Column(JSONB, nullable=True)  # Additional context (routing info, tools used, etc.)
    
    # Review status
    reviewed = Column(Boolean, default=False, nullable=False, index=True)
    reviewed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    review_notes = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], lazy="select")
    conversation = relationship("Conversation", lazy="select")
    message = relationship("Message", lazy="select")
    reviewer = relationship("User", foreign_keys=[reviewed_by], lazy="select")
    
    def __repr__(self):
        return f"<ResponseFeedback(id={self.id}, type={self.feedback_type}, reviewed={self.reviewed})>"
    
    @property
    def is_positive(self) -> bool:
        """Check if feedback is positive"""
        return self.feedback_type == FeedbackType.THUMBS_UP
    
    @property
    def is_negative(self) -> bool:
        """Check if feedback is negative"""
        return self.feedback_type == FeedbackType.THUMBS_DOWN
    
    @property
    def needs_review(self) -> bool:
        """Check if feedback needs review (negative feedback not yet reviewed)"""
        return self.is_negative and not self.reviewed

