"""
User models for agricultural chatbot
Supports farmers, advisors, inspectors, and administrators
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.core.database import Base


class UserRole(str, enum.Enum):
    """User roles in the agricultural system"""
    FARMER = "farmer"
    ADVISOR = "advisor"
    INSPECTOR = "inspector"
    ADMIN = "admin"


class UserStatus(str, enum.Enum):
    """User account status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"


class User(Base):
    """User model for agricultural chatbot system"""
    
    __tablename__ = "users"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Basic information
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    
    # Role and permissions
    role = Column(SQLEnum(UserRole), default=UserRole.FARMER, nullable=False)
    status = Column(SQLEnum(UserStatus), default=UserStatus.PENDING_VERIFICATION, nullable=False)
    
    # Preferences
    language_preference = Column(String(10), default="fr", nullable=False)
    timezone = Column(String(50), default="Europe/Paris", nullable=False)
    notification_preferences = Column(Text, nullable=True)  # JSON string
    
    # Profile information
    profile_picture_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)
    experience_years = Column(String(10), nullable=True)  # e.g., "5-10", "10+"
    specialization = Column(ARRAY(String), nullable=True)  # e.g., ["cereals", "livestock"]
    
    # Location information
    region_code = Column(String(20), nullable=True)
    department_code = Column(String(10), nullable=True)
    commune_insee = Column(String(10), nullable=True)
    
    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    is_verified = Column(Boolean, default=False, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_login = Column(DateTime(timezone=True), nullable=True)
    email_verified_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    farms = relationship("Farm", back_populates="owner", cascade="all, delete-orphan", lazy="select")
    conversations = relationship("Conversation", back_populates="user", cascade="all, delete-orphan", lazy="select")
    interventions = relationship("VoiceJournalEntry", back_populates="user", cascade="all, delete-orphan", lazy="select")
    # organization_memberships = relationship("OrganizationMembership", back_populates="user", cascade="all, delete-orphan", lazy="select")
    
    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, role={self.role})>"
    
    @property
    def is_farmer(self) -> bool:
        """Check if user is a farmer"""
        return self.role == UserRole.FARMER
    
    @property
    def is_advisor(self) -> bool:
        """Check if user is an advisor"""
        return self.role == UserRole.ADVISOR
    
    @property
    def is_inspector(self) -> bool:
        """Check if user is an inspector"""
        return self.role == UserRole.INSPECTOR
    
    @property
    def is_admin(self) -> bool:
        """Check if user is an admin"""
        return self.role == UserRole.ADMIN
    
    @property
    def display_name(self) -> str:
        """Get display name for the user"""
        return self.full_name or self.email.split('@')[0]


class UserSession(Base):
    """User session tracking for security and analytics"""
    
    __tablename__ = "user_sessions"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign keys
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    # Session information
    session_token = Column(String(500), unique=True, nullable=False, index=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 support
    user_agent = Column(Text, nullable=True)
    device_type = Column(String(50), nullable=True)  # mobile, desktop, tablet
    
    # Location information
    country = Column(String(100), nullable=True)
    region = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    
    # Session status
    is_active = Column(Boolean, default=True, nullable=False)
    last_activity = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    
    def __repr__(self):
        return f"<UserSession(id={self.id}, user_id={self.user_id}, active={self.is_active})>"


class UserActivity(Base):
    """User activity tracking for analytics and monitoring"""
    
    __tablename__ = "user_activities"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign keys
    user_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    session_id = Column(UUID(as_uuid=True), nullable=True, index=True)
    
    # Activity information
    activity_type = Column(String(100), nullable=False, index=True)  # login, chat, voice, etc.
    activity_description = Column(Text, nullable=True)
    activity_metadata = Column(Text, nullable=True)  # JSON string for additional data
    
    # Request information
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    endpoint = Column(String(500), nullable=True)
    method = Column(String(10), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<UserActivity(id={self.id}, user_id={self.user_id}, type={self.activity_type})>"
