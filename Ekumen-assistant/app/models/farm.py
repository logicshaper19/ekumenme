"""
Farm models for agricultural chatbot
Supports French agricultural data structure with SIRET, parcels, and interventions
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text, Numeric, Enum as SQLEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB
from sqlalchemy.orm import relationship, validates
from sqlalchemy.sql import func
from geoalchemy2 import Geography
import uuid
import enum

from app.core.database import Base


class FarmType(str, enum.Enum):
    """Types of agricultural operations"""
    INDIVIDUAL = "individual"
    COOPERATIVE = "cooperative"
    CORPORATE = "corporate"
    ORGANIC = "organic"
    CONVENTIONAL = "conventional"
    MIXED = "mixed"


class FarmStatus(str, enum.Enum):
    """Farm status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"


class Farm(Base):
    """Farm model for French agricultural operations"""
    
    __tablename__ = "farms"
    
    # Primary key - SIRET is the French business identifier
    siret = Column(String(14), primary_key=True, index=True)
    
    # Basic information
    farm_name = Column(String(255), nullable=False)
    legal_name = Column(String(255), nullable=True)
    legal_form = Column(String(100), nullable=True)  # SA, SARL, EARL, etc.
    
    # Ownership and management
    owner_user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    
    # Farm characteristics
    farm_type = Column(SQLEnum(FarmType), default=FarmType.INDIVIDUAL, nullable=False)
    status = Column(SQLEnum(FarmStatus), default=FarmStatus.ACTIVE, nullable=False)
    
    # Geographic information
    region_code = Column(String(20), nullable=False, index=True)
    department_code = Column(String(10), nullable=True)
    commune_insee = Column(String(10), nullable=True)
    address = Column(Text, nullable=True)
    postal_code = Column(String(10), nullable=True)
    coordinates = Column(Geography('POINT', srid=4326), nullable=True)
    
    # Agricultural data
    total_area_ha = Column(Numeric(10, 2), nullable=True)
    utilized_agricultural_area_ha = Column(Numeric(10, 2), nullable=True)
    organic_certified = Column(Boolean, default=False, nullable=False)
    organic_certification_date = Column(DateTime(timezone=True), nullable=True)
    organic_certification_body = Column(String(255), nullable=True)
    
    # Business information
    activity_codes = Column(ARRAY(String), nullable=True)  # NAF codes
    primary_productions = Column(ARRAY(String), nullable=True)  # Main crop types
    secondary_productions = Column(ARRAY(String), nullable=True)  # Secondary activities
    
    # Financial information
    annual_revenue = Column(Numeric(15, 2), nullable=True)
    employee_count = Column(Numeric(5, 0), nullable=True)
    
    # Additional data
    description = Column(Text, nullable=True)
    website = Column(String(500), nullable=True)
    social_media = Column(JSONB, nullable=True)  # Social media links
    
    # System fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    last_sync_with_api = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    owner = relationship("User", back_populates="farms", lazy="select")
    parcels = relationship("Parcel", back_populates="farm", cascade="all, delete-orphan", lazy="select")
    conversations = relationship("Conversation", back_populates="farm", cascade="all, delete-orphan", lazy="select")
    interventions = relationship("VoiceJournalEntry", back_populates="farm", cascade="all, delete-orphan", lazy="select")
    organization_access = relationship("OrganizationFarmAccess", back_populates="farm", cascade="all, delete-orphan", lazy="select")
    
    def __repr__(self):
        return f"<Farm(siret={self.siret}, name={self.farm_name}, type={self.farm_type})>"

    @validates('siret')
    def validate_siret(self, key, value):
        """Validate SIRET format (14 digits)"""
        if value and (len(value) != 14 or not value.isdigit()):
            raise ValueError("SIRET must be exactly 14 digits")
        return value

    @validates('total_area_ha')
    def validate_area(self, key, value):
        """Validate farm area is positive"""
        if value is not None and value <= 0:
            raise ValueError("Farm area must be positive")
        return value
    
    @property
    def is_organic(self) -> bool:
        """Check if farm is organic certified"""
        return self.organic_certified
    
    @property
    def display_name(self) -> str:
        """Get display name for the farm"""
        return self.farm_name or self.legal_name or f"Exploitation {self.siret}"


class Parcel(Base):
    """Parcel model for individual fields/plots"""
    
    __tablename__ = "parcels"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign keys
    farm_siret = Column(String(14), ForeignKey("farms.siret"), nullable=False, index=True)
    
    # Parcel identification
    parcel_number = Column(String(50), nullable=False, index=True)  # Internal parcel ID
    cadastral_reference = Column(String(50), nullable=True)  # French cadastral reference
    pac_parcel_id = Column(String(50), nullable=True)  # PAC (Common Agricultural Policy) ID
    
    # Geographic information
    area_ha = Column(Numeric(10, 4), nullable=False)
    coordinates = Column(Geography('POLYGON', srid=4326), nullable=True)
    centroid = Column(Geography('POINT', srid=4326), nullable=True)
    
    # Agricultural information
    current_crop = Column(String(100), nullable=True)
    crop_variety = Column(String(100), nullable=True)
    planting_date = Column(DateTime(timezone=True), nullable=True)
    expected_harvest_date = Column(DateTime(timezone=True), nullable=True)
    
    # Soil information
    soil_type = Column(String(100), nullable=True)  # clay, sand, loam, etc.
    ph_level = Column(Numeric(3, 1), nullable=True)
    organic_matter_percent = Column(Numeric(4, 2), nullable=True)
    
    # Management information
    irrigation_available = Column(Boolean, default=False, nullable=False)
    drainage_system = Column(Boolean, default=False, nullable=False)
    slope_percent = Column(Numeric(5, 2), nullable=True)
    exposure = Column(String(20), nullable=True)  # north, south, east, west
    
    # Additional data
    notes = Column(Text, nullable=True)
    parcel_metadata = Column(JSONB, nullable=True)  # Additional structured data
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    farm = relationship("Farm", back_populates="parcels", lazy="select")
    interventions = relationship("VoiceJournalEntry", back_populates="parcel", cascade="all, delete-orphan", lazy="select")
    
    def __repr__(self):
        return f"<Parcel(id={self.id}, number={self.parcel_number}, area={self.area_ha}ha)>"

    @validates('area_ha')
    def validate_area(self, key, value):
        """Validate parcel area is positive"""
        if value is not None and value <= 0:
            raise ValueError("Parcel area must be positive")
        return value
    
    @property
    def display_name(self) -> str:
        """Get display name for the parcel"""
        return f"Parcelle {self.parcel_number} ({self.area_ha} ha)"


class CropRotation(Base):
    """Crop rotation history for parcels"""
    
    __tablename__ = "crop_rotations"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign keys
    parcel_id = Column(UUID(as_uuid=True), ForeignKey("parcels.id"), nullable=False, index=True)
    
    # Crop information
    crop_name = Column(String(100), nullable=False)
    crop_variety = Column(String(100), nullable=True)
    crop_family = Column(String(50), nullable=True)  # cereals, legumes, etc.
    
    # Timing
    planting_date = Column(DateTime(timezone=True), nullable=False)
    harvest_date = Column(DateTime(timezone=True), nullable=True)
    season = Column(String(20), nullable=True)  # spring, summer, autumn, winter
    
    # Yield information
    yield_quantity = Column(Numeric(10, 2), nullable=True)
    yield_unit = Column(String(20), nullable=True)  # quintaux, tonnes, etc.
    yield_per_hectare = Column(Numeric(10, 2), nullable=True)
    
    # Quality information
    quality_grade = Column(String(20), nullable=True)
    moisture_percent = Column(Numeric(4, 2), nullable=True)
    protein_percent = Column(Numeric(4, 2), nullable=True)
    
    # Additional data
    notes = Column(Text, nullable=True)
    weather_conditions = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    
    def __repr__(self):
        return f"<CropRotation(id={self.id}, crop={self.crop_name}, season={self.season})>"
