"""
Organization models for agricultural chatbot
Handles multi-organization support (companies, cooperatives, farm enterprises)
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Enum as SQLEnum, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.core.database import Base


class OrganizationType(str, enum.Enum):
    """Types of agricultural organizations"""
    FARM = "farm"
    COOPERATIVE = "cooperative"
    INPUT_COMPANY = "input_company"
    ADVISOR = "advisor"
    RESEARCH_INSTITUTE = "research_institute"
    GOVERNMENT_AGENCY = "government_agency"


class OrganizationStatus(str, enum.Enum):
    """Organization status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_APPROVAL = "pending_approval"


class AccessType(str, enum.Enum):
    """Types of access to farms"""
    OWNER = "owner"
    ADMIN = "admin"
    ADVISOR = "advisor"
    VIEWER = "viewer"
    READONLY = "readonly"


class Organization(Base):
    """Organization model for multi-tenant support"""
    
    __tablename__ = "organizations"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Organization identification
    name = Column(String(255), nullable=False, index=True)
    legal_name = Column(String(255), nullable=True)
    siret = Column(String(14), nullable=True, unique=True, index=True)  # French business identifier
    siren = Column(String(9), nullable=True, index=True)  # French business identifier
    
    # Organization details
    organization_type = Column(SQLEnum(OrganizationType), nullable=False, index=True)
    status = Column(SQLEnum(OrganizationStatus), default=OrganizationStatus.ACTIVE, nullable=False)
    
    # Contact information
    email = Column(String(255), nullable=True)
    phone = Column(String(20), nullable=True)
    website = Column(String(500), nullable=True)
    
    # Address information
    address = Column(Text, nullable=True)
    postal_code = Column(String(10), nullable=True)
    city = Column(String(100), nullable=True)
    region_code = Column(String(20), nullable=True, index=True)
    country = Column(String(100), default="France", nullable=False)
    
    # Business information
    legal_form = Column(String(100), nullable=True)  # SA, SARL, etc.
    activity_codes = Column(JSONB, nullable=True)  # NAF codes
    employee_count = Column(Numeric(5, 0), nullable=True)
    annual_revenue = Column(Numeric(15, 2), nullable=True)
    
    # Agricultural specific
    specialization = Column(JSONB, nullable=True)  # Agricultural specializations
    certifications = Column(JSONB, nullable=True)  # Certifications held
    services_offered = Column(JSONB, nullable=True)  # Services provided
    
    # Additional data
    description = Column(Text, nullable=True)
    organization_metadata = Column(JSONB, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    memberships = relationship("OrganizationMembership", back_populates="organization", cascade="all, delete-orphan", lazy="select")
    farm_access = relationship("OrganizationFarmAccess", back_populates="organization", cascade="all, delete-orphan", lazy="select")
    knowledge_documents = relationship("KnowledgeBaseDocument", back_populates="organization", cascade="all, delete-orphan", lazy="select")
    
    def __repr__(self):
        return f"<Organization(id={self.id}, name={self.name}, type={self.organization_type})>"
    
    @property
    def is_active(self) -> bool:
        """Check if organization is active"""
        return self.status == OrganizationStatus.ACTIVE
    
    @property
    def display_name(self) -> str:
        """Get display name for the organization"""
        return self.name or self.legal_name or f"Organization {self.id}"


class OrganizationMembership(Base):
    """Organization membership model"""
    
    __tablename__ = "organization_memberships"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign keys
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    
    # Membership details
    role = Column(String(50), nullable=False)  # admin, member, advisor, etc.
    access_level = Column(SQLEnum(AccessType), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Permissions
    permissions = Column(JSONB, nullable=True)  # Specific permissions
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="organization_memberships", lazy="select")
    organization = relationship("Organization", back_populates="memberships", lazy="select")
    
    def __repr__(self):
        return f"<OrganizationMembership(id={self.id}, user_id={self.user_id}, org_id={self.organization_id})>"


class OrganizationFarmAccess(Base):
    """Organization access to farms"""
    
    __tablename__ = "organization_farm_access"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign keys
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=False, index=True)
    farm_siret = Column(String(14), nullable=False, index=True)  # TODO: Re-enable FK when Farm model is restored
    
    # Access details
    access_type = Column(SQLEnum(AccessType), nullable=False)
    granted_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Access scope
    access_scope = Column(JSONB, nullable=True)  # Specific data access permissions
    restrictions = Column(JSONB, nullable=True)  # Access restrictions
    
    # Timestamps
    granted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    revoked_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    organization = relationship("Organization", back_populates="farm_access", lazy="select")
    # farm = relationship("Farm", back_populates="organization_access", lazy="select")  # TODO: Re-enable when Farm model is restored
    granted_by_user = relationship("User", foreign_keys=[granted_by], lazy="select")
    
    def __repr__(self):
        return f"<OrganizationFarmAccess(id={self.id}, org_id={self.organization_id}, farm_siret={self.farm_siret})>"


class KnowledgeBaseEntry(Base):
    """Knowledge base entries for shared agricultural knowledge"""
    
    __tablename__ = "knowledge_base_entries"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign keys
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id"), nullable=True, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Entry information
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    category = Column(String(100), nullable=False, index=True)  # crops, pests, regulations, etc.
    tags = Column(JSONB, nullable=True)  # List of tags
    
    # Content details
    content_type = Column(String(50), nullable=False)  # article, guide, regulation, etc.
    language = Column(String(10), default="fr", nullable=False)
    version = Column(String(20), default="1.0", nullable=False)
    
    # Sharing and visibility
    is_public = Column(Boolean, default=False, nullable=False)
    is_shared = Column(Boolean, default=False, nullable=False)  # Shared within organization
    access_level = Column(SQLEnum(AccessType), default=AccessType.VIEWER, nullable=False)
    
    # Quality and validation
    is_validated = Column(Boolean, default=False, nullable=False)
    validated_by = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    validation_notes = Column(Text, nullable=True)
    
    # Usage statistics
    view_count = Column(Numeric(10, 0), default=0, nullable=False)
    like_count = Column(Numeric(10, 0), default=0, nullable=False)
    
    # Additional data
    organization_metadata = Column(JSONB, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    validated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    organization = relationship("Organization", lazy="select")
    creator = relationship("User", foreign_keys=[created_by], lazy="select")
    validator = relationship("User", foreign_keys=[validated_by], lazy="select")
    
    def __repr__(self):
        return f"<KnowledgeBaseEntry(id={self.id}, title={self.title}, category={self.category})>"
