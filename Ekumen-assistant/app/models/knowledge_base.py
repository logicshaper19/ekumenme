"""
Knowledge Base models for document management and workflow
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Enum as SQLEnum, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum
from datetime import datetime
from typing import Optional

from app.core.database import Base


class DocumentType(str, enum.Enum):
    """Types of knowledge base documents"""
    PRODUCT_SPEC = "product_spec"
    REGULATION = "regulation"
    MANUAL = "manual"
    TECHNICAL_SHEET = "technical_sheet"
    RESEARCH_PAPER = "research_paper"
    BEST_PRACTICE = "best_practice"
    SAFETY_GUIDE = "safety_guide"
    OTHER = "other"


class DocumentStatus(str, enum.Enum):
    """Document processing status"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class KnowledgeBaseDocument(Base):
    """Knowledge base document model with workflow support"""
    
    __tablename__ = "knowledge_base_documents"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Organization and user references
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    uploaded_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Document information
    filename = Column(String(500), nullable=False)
    file_path = Column(String(500), nullable=False)  # Local file path
    file_type = Column(String(50), nullable=True)  # 'pdf', 'docx', 'txt', 'csv'
    file_size_bytes = Column(Integer, nullable=True)
    
    # Processing status
    processing_status = Column(SQLEnum(DocumentStatus), default=DocumentStatus.PENDING, nullable=False)
    chunk_count = Column(Integer, nullable=True)
    embedding_model = Column(String(100), default="text-embedding-ada-002", nullable=True)
    
    # Document metadata
    document_type = Column(SQLEnum(DocumentType), nullable=False)
    tags = Column(JSONB, nullable=True)  # Array of tags
    description = Column(Text, nullable=True)
    
    # Sharing permissions
    visibility = Column(String(50), default="internal", nullable=False)  # 'internal', 'shared', 'public'
    shared_with_organizations = Column(JSONB, nullable=True)  # Array of org IDs
    shared_with_users = Column(JSONB, nullable=True)  # Array of user IDs
    is_ekumen_provided = Column(Boolean, default=False, nullable=False)
    
    # Workflow metadata (JSONB for flexibility)
    organization_metadata = Column(JSONB, nullable=True)  # Workflow-specific data
    
    # Workflow fields
    workflow_metadata = Column(JSONB, default={}, nullable=True)
    submission_status = Column(String(50), default="draft", nullable=True)
    approved_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)
    expiration_date = Column(DateTime(timezone=True), nullable=True)
    auto_renewal = Column(Boolean, default=False, nullable=True)
    quality_score = Column(Numeric(3, 2), default=0.0, nullable=True)
    quality_issues = Column(JSONB, default=[], nullable=True)
    quality_recommendations = Column(JSONB, default=[], nullable=True)
    version = Column(Integer, default=1, nullable=True)
    parent_document_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_base_documents.id"), nullable=True)
    
    # Analytics
    query_count = Column(Integer, default=0, nullable=False)
    last_accessed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    organization = relationship("Organization", back_populates="knowledge_documents", lazy="select")
    uploader = relationship("User", foreign_keys=[uploaded_by], lazy="select")
    
    def __repr__(self):
        return f"<KnowledgeBaseDocument(id={self.id}, filename={self.filename}, status={self.processing_status})>"
    
    @property
    def is_active(self) -> bool:
        """Check if document is active in the knowledge base"""
        return (
            self.processing_status == DocumentStatus.COMPLETED and
            self.visibility in ["shared", "public"]
        )
    
    @property
    def is_expired(self) -> bool:
        """Check if document has expired"""
        if not self.organization_metadata:
            return False
        
        expiration_date_str = self.organization_metadata.get("expiration_date")
        if not expiration_date_str:
            return False
        
        try:
            expiration_date = datetime.fromisoformat(expiration_date_str.replace('Z', '+00:00'))
            return datetime.utcnow() > expiration_date
        except (ValueError, TypeError):
            return False
    
    @property
    def days_until_expiration(self) -> Optional[int]:
        """Get days until expiration"""
        if not self.organization_metadata:
            return None
        
        expiration_date_str = self.organization_metadata.get("expiration_date")
        if not expiration_date_str:
            return None
        
        try:
            expiration_date = datetime.fromisoformat(expiration_date_str.replace('Z', '+00:00'))
            delta = expiration_date.date() - datetime.utcnow().date()
            return delta.days
        except (ValueError, TypeError):
            return None
    
    # Remove the property since we have the actual column
    
    # Remove the property since we have the actual column
    
    # Remove the property since we have the actual column


class KnowledgeBaseWorkflowAudit(Base):
    """Audit trail for knowledge base workflow actions"""
    
    __tablename__ = "knowledge_base_workflow_audit"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # References
    document_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_base_documents.id"), nullable=False, index=True)
    performed_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    
    # Action details
    action = Column(String(50), nullable=False, index=True)  # 'submitted', 'reviewed', 'approved', 'rejected', 'expired', 'renewed'
    details = Column(JSONB, default={}, nullable=True)
    comments = Column(Text, nullable=True)
    
    # Timestamps
    performed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    document = relationship("KnowledgeBaseDocument", lazy="select")
    performer = relationship("User", foreign_keys=[performed_by], lazy="select")
    
    def __repr__(self):
        return f"<KnowledgeBaseWorkflowAudit(id={self.id}, action={self.action}, document_id={self.document_id})>"


class KnowledgeBaseNotification(Base):
    """Notifications for knowledge base workflow events"""
    
    __tablename__ = "knowledge_base_notifications"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # References
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    document_id = Column(UUID(as_uuid=True), ForeignKey("knowledge_base_documents.id"), nullable=True, index=True)
    
    # Notification details
    notification_type = Column(String(50), nullable=False, index=True)  # 'submission_received', 'approval_needed', 'document_approved', 'document_rejected', 'expiration_warning'
    title = Column(String(255), nullable=False)
    message = Column(Text, nullable=False)
    
    # Read status
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], lazy="select")
    document = relationship("KnowledgeBaseDocument", foreign_keys=[document_id], lazy="select")
    
    def __repr__(self):
        return f"<KnowledgeBaseNotification(id={self.id}, type={self.notification_type}, user_id={self.user_id})>"
