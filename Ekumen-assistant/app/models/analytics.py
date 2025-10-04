"""
Analytics models for the Analytics Dashboard
"""
import uuid
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum as PyEnum

from sqlalchemy import (
    Column, String, Integer, Numeric, Boolean, DateTime, Text, 
    ForeignKey, Index, func
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class AnalyticsEventType(str, PyEnum):
    """Types of analytics events"""
    QUERY_STARTED = "query_started"
    QUERY_COMPLETED = "query_completed"
    DOCUMENT_RETRIEVED = "document_retrieved"
    DOCUMENT_CITED = "document_cited"
    USER_INTERACTION = "user_interaction"
    SATISFACTION_FEEDBACK = "satisfaction_feedback"
    EXPORT_ACTION = "export_action"
    SHARE_ACTION = "share_action"


class DocumentAudience(str, PyEnum):
    """Document audience types"""
    PUBLIC = "public"
    INTERNAL = "internal"
    CUSTOMERS = "customers"


class UserRole(str, PyEnum):
    """User role types for analytics"""
    FARMER = "farmer"
    ADVISOR = "advisor"
    INSPECTOR = "inspector"
    ADMIN = "admin"


class AnalyticsEvent(Base):
    """Base analytics event tracking"""
    
    __tablename__ = "analytics_events"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign keys
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    session_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    conversation_id = Column(UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=True, index=True)
    
    # Event information
    event_type = Column(String(50), nullable=False, index=True)
    event_data = Column(JSONB, nullable=True)  # Flexible data storage
    
    # Request context
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    endpoint = Column(String(500), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_analytics_events_type_created', 'event_type', 'created_at'),
        Index('idx_analytics_events_user_created', 'user_id', 'created_at'),
    )

    def __repr__(self):
        return f"<AnalyticsEvent(id={self.id}, type={self.event_type}, created_at={self.created_at})>"


class DocumentAnalytics(Base):
    """Document performance analytics"""
    
    __tablename__ = "document_analytics"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Document information
    document_id = Column(String(255), nullable=False, index=True)  # Reference to knowledge base document
    document_name = Column(String(500), nullable=False)
    document_audience = Column(String(20), nullable=False, index=True)
    
    # Time period for aggregation
    period_start = Column(DateTime(timezone=True), nullable=False, index=True)
    period_end = Column(DateTime(timezone=True), nullable=False, index=True)
    period_type = Column(String(20), nullable=False, index=True)  # daily, weekly, monthly
    
    # Performance metrics
    retrievals = Column(Integer, default=0, nullable=False)  # Times document was retrieved
    citations = Column(Integer, default=0, nullable=False)   # Times document was cited
    user_interactions = Column(Integer, default=0, nullable=False)  # Clicks, downloads, etc.
    satisfaction_score = Column(Numeric(5, 2), nullable=True)  # Average satisfaction rating
    satisfaction_count = Column(Integer, default=0, nullable=False)  # Number of ratings
    
    # Calculated metrics
    citation_rate = Column(Numeric(5, 2), nullable=True)  # citations / retrievals * 100
    trend_percentage = Column(Numeric(5, 2), nullable=True)  # Change from previous period
    
    # Additional data
    extra_data = Column(JSONB, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_document_analytics_doc_period', 'document_id', 'period_start', 'period_end'),
        Index('idx_document_analytics_audience_period', 'document_audience', 'period_start'),
    )

    def __repr__(self):
        return f"<DocumentAnalytics(id={self.id}, document={self.document_name}, period={self.period_start})>"


class QueryAnalytics(Base):
    """Query and topic analytics"""
    
    __tablename__ = "query_analytics"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Query information
    query_text = Column(Text, nullable=False)
    query_hash = Column(String(64), nullable=False, index=True)  # Hash for deduplication
    query_topics = Column(JSONB, nullable=True)  # Extracted topics
    query_products = Column(JSONB, nullable=True)  # Mentioned products
    query_compliance_themes = Column(JSONB, nullable=True)  # Regulatory themes
    
    # User context
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    user_role = Column(String(20), nullable=True, index=True)
    user_region = Column(String(100), nullable=True, index=True)
    
    # Time period for aggregation
    period_start = Column(DateTime(timezone=True), nullable=False, index=True)
    period_end = Column(DateTime(timezone=True), nullable=False, index=True)
    period_type = Column(String(20), nullable=False, index=True)  # daily, weekly, monthly
    
    # Metrics
    query_count = Column(Integer, default=0, nullable=False)
    unique_users = Column(Integer, default=0, nullable=False)
    avg_response_time = Column(Numeric(8, 2), nullable=True)
    satisfaction_score = Column(Numeric(5, 2), nullable=True)
    satisfaction_count = Column(Integer, default=0, nullable=False)
    
    # Growth metrics
    growth_percentage = Column(Numeric(5, 2), nullable=True)  # Change from previous period
    
    # Additional data
    extra_data = Column(JSONB, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_query_analytics_hash_period', 'query_hash', 'period_start'),
        Index('idx_query_analytics_topics_period', 'query_topics', 'period_start'),
        Index('idx_query_analytics_products_period', 'query_products', 'period_start'),
    )

    def __repr__(self):
        return f"<QueryAnalytics(id={self.id}, query_hash={self.query_hash}, count={self.query_count})>"


class ContentGap(Base):
    """Content gap analysis and recommendations"""
    
    __tablename__ = "content_gaps"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Gap information
    gap_title = Column(String(500), nullable=False)
    gap_description = Column(Text, nullable=True)
    gap_category = Column(String(100), nullable=False, index=True)  # herbicide, fungicide, etc.
    
    # Query information
    related_queries = Column(JSONB, nullable=True)  # Array of related queries
    query_count = Column(Integer, default=0, nullable=False)
    unique_users = Column(Integer, default=0, nullable=False)
    
    # Priority and impact
    priority_score = Column(Integer, nullable=False, index=True)  # 1-10 scale
    impact_score = Column(Integer, nullable=False, index=True)  # 1-10 scale
    effort_score = Column(Integer, nullable=False, index=True)  # 1-10 scale
    
    # Audience and timing
    target_audience = Column(String(20), nullable=False, index=True)
    seasonal_relevance = Column(JSONB, nullable=True)  # Months when relevant
    due_date = Column(DateTime(timezone=True), nullable=True, index=True)
    
    # Status
    status = Column(String(20), default='identified', nullable=False, index=True)  # identified, planned, in_progress, completed
    assigned_to = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    
    # Additional data
    extra_data = Column(JSONB, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_content_gaps_priority_impact', 'priority_score', 'impact_score'),
        Index('idx_content_gaps_status_due', 'status', 'due_date'),
    )

    def __repr__(self):
        return f"<ContentGap(id={self.id}, title={self.gap_title}, priority={self.priority_score})>"


class UserSegmentAnalytics(Base):
    """User segment behavior analytics"""
    
    __tablename__ = "user_segment_analytics"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Segment information
    segment_type = Column(String(50), nullable=False, index=True)  # role, region, audience
    segment_value = Column(String(100), nullable=False, index=True)  # farmer, bretagne, public
    
    # Time period for aggregation
    period_start = Column(DateTime(timezone=True), nullable=False, index=True)
    period_end = Column(DateTime(timezone=True), nullable=False, index=True)
    period_type = Column(String(20), nullable=False, index=True)  # daily, weekly, monthly
    
    # Metrics
    total_queries = Column(Integer, default=0, nullable=False)
    unique_users = Column(Integer, default=0, nullable=False)
    avg_session_duration = Column(Numeric(8, 2), nullable=True)
    avg_queries_per_session = Column(Numeric(5, 2), nullable=True)
    
    # Content preferences
    top_topics = Column(JSONB, nullable=True)
    top_products = Column(JSONB, nullable=True)
    top_documents = Column(JSONB, nullable=True)
    
    # Satisfaction
    satisfaction_score = Column(Numeric(5, 2), nullable=True)
    satisfaction_count = Column(Integer, default=0, nullable=False)
    
    # Additional data
    extra_data = Column(JSONB, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_user_segment_analytics_segment_period', 'segment_type', 'segment_value', 'period_start'),
    )

    def __repr__(self):
        return f"<UserSegmentAnalytics(id={self.id}, segment={self.segment_type}:{self.segment_value}, queries={self.total_queries})>"


class AnalyticsAlert(Base):
    """Analytics alerts and notifications"""
    
    __tablename__ = "analytics_alerts"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Alert information
    alert_type = Column(String(50), nullable=False, index=True)  # performance_drop, content_gap, etc.
    alert_title = Column(String(500), nullable=False)
    alert_description = Column(Text, nullable=True)
    alert_severity = Column(String(20), nullable=False, index=True)  # low, medium, high, critical
    
    # Related entities
    document_id = Column(String(255), nullable=True, index=True)
    content_gap_id = Column(UUID(as_uuid=True), ForeignKey("content_gaps.id"), nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True, index=True)
    
    # Alert data
    alert_data = Column(JSONB, nullable=True)  # Specific data for the alert
    threshold_value = Column(Numeric(10, 2), nullable=True)
    current_value = Column(Numeric(10, 2), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    acknowledged_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    acknowledged_at = Column(DateTime(timezone=True), nullable=True)
    
    # Additional data
    extra_data = Column(JSONB, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Indexes for performance
    __table_args__ = (
        Index('idx_analytics_alerts_active_severity', 'is_active', 'alert_severity'),
        Index('idx_analytics_alerts_user_unread', 'user_id', 'is_read'),
    )

    def __repr__(self):
        return f"<AnalyticsAlert(id={self.id}, type={self.alert_type}, severity={self.alert_severity})>"
