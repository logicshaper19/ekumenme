"""
Intervention models for agricultural chatbot
Handles voice journal entries and agricultural interventions
"""

from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey, Enum as SQLEnum, Numeric, Integer
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
import enum

from app.core.database import Base


class InterventionType(str, enum.Enum):
    """Types of agricultural interventions"""
    PLANTING = "planting"
    FERTILIZATION = "fertilization"
    PEST_CONTROL = "pest_control"
    DISEASE_CONTROL = "disease_control"
    WEED_CONTROL = "weed_control"
    HARVESTING = "harvesting"
    IRRIGATION = "irrigation"
    SOIL_TREATMENT = "soil_treatment"
    PRUNING = "pruning"
    OTHER = "other"


class ValidationStatus(str, enum.Enum):
    """Validation status for interventions"""
    PENDING = "pending"
    VALIDATED = "validated"
    WARNING = "warning"
    ERROR = "error"
    MANUAL_REVIEW = "manual_review"


class WeatherCondition(str, enum.Enum):
    """Weather conditions during intervention"""
    SUNNY = "sunny"
    CLOUDY = "cloudy"
    RAINY = "rainy"
    WINDY = "windy"
    FOGGY = "foggy"
    STORMY = "stormy"


class VoiceJournalEntry(Base):
    """Voice journal entry model for field logging"""
    
    __tablename__ = "voice_journal_entries"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign keys
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    farm_siret = Column(String(14), ForeignKey("farms.siret"), nullable=False, index=True)
    parcel_id = Column(UUID(as_uuid=True), ForeignKey("parcels.id"), nullable=True, index=True)
    
    # Entry information
    content = Column(Text, nullable=False)  # Transcribed text
    intervention_type = Column(SQLEnum(InterventionType), nullable=False, index=True)
    
    # Voice data
    audio_file_path = Column(String(500), nullable=True)  # Path to audio file
    audio_duration_seconds = Column(Numeric(8, 2), nullable=True)
    transcription_confidence = Column(Numeric(3, 2), nullable=True)  # 0.00 to 1.00
    
    # Intervention details
    products_used = Column(JSONB, nullable=True)  # List of products with quantities
    equipment_used = Column(JSONB, nullable=True)  # Equipment and settings
    weather_conditions = Column(SQLEnum(WeatherCondition), nullable=True)
    temperature_celsius = Column(Numeric(4, 1), nullable=True)
    humidity_percent = Column(Numeric(5, 2), nullable=True)
    wind_speed_kmh = Column(Numeric(5, 2), nullable=True)
    
    # Validation and compliance
    validation_status = Column(SQLEnum(ValidationStatus), default=ValidationStatus.PENDING, nullable=False)
    validation_notes = Column(Text, nullable=True)
    compliance_issues = Column(JSONB, nullable=True)  # List of compliance issues
    safety_alerts = Column(JSONB, nullable=True)  # Safety warnings
    
    # Additional data
    notes = Column(Text, nullable=True)
    intervention_metadata = Column(JSONB, nullable=True)  # Additional structured data
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    intervention_date = Column(DateTime(timezone=True), nullable=True)  # When intervention actually occurred
    
    # Relationships
    user = relationship("User", back_populates="interventions", lazy="select")
    farm = relationship("Farm", back_populates="interventions", lazy="select")
    parcel = relationship("Parcel", back_populates="interventions", lazy="select")
    
    def __repr__(self):
        return f"<VoiceJournalEntry(id={self.id}, type={self.intervention_type}, status={self.validation_status})>"
    
    @property
    def is_validated(self) -> bool:
        """Check if entry is validated"""
        return self.validation_status == ValidationStatus.VALIDATED
    
    @property
    def has_warnings(self) -> bool:
        """Check if entry has warnings"""
        return self.validation_status == ValidationStatus.WARNING
    
    @property
    def has_errors(self) -> bool:
        """Check if entry has errors"""
        return self.validation_status == ValidationStatus.ERROR


class ProductUsage(Base):
    """Product usage tracking for interventions"""
    
    __tablename__ = "product_usage"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign keys
    journal_entry_id = Column(UUID(as_uuid=True), ForeignKey("voice_journal_entries.id"), nullable=False, index=True)
    
    # Product information
    product_name = Column(String(255), nullable=False)
    amm_number = Column(String(20), nullable=True)  # French AMM number
    active_ingredients = Column(JSONB, nullable=True)  # List of active ingredients
    
    # Usage details
    quantity_used = Column(Numeric(10, 3), nullable=False)
    unit = Column(String(20), nullable=False)  # L, kg, g, etc.
    concentration = Column(Numeric(5, 2), nullable=True)  # Concentration percentage
    application_rate = Column(Numeric(8, 2), nullable=True)  # L/ha or kg/ha
    
    # Safety and compliance
    phi_days = Column(Integer, nullable=True)  # Pre-harvest interval in days
    reentry_period_hours = Column(Integer, nullable=True)  # Re-entry period
    epi_required = Column(JSONB, nullable=True)  # Required protective equipment
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    journal_entry = relationship("VoiceJournalEntry", lazy="select")
    
    def __repr__(self):
        return f"<ProductUsage(id={self.id}, product={self.product_name}, quantity={self.quantity_used}{self.unit})>"


class InterventionHistory(Base):
    """Historical intervention data for analytics"""
    
    __tablename__ = "intervention_history"
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    
    # Foreign keys
    farm_siret = Column(String(14), ForeignKey("farms.siret"), nullable=False, index=True)
    parcel_id = Column(UUID(as_uuid=True), ForeignKey("parcels.id"), nullable=True, index=True)
    
    # Intervention information
    intervention_type = Column(SQLEnum(InterventionType), nullable=False, index=True)
    intervention_date = Column(DateTime(timezone=True), nullable=False, index=True)
    
    # Crop information
    crop_name = Column(String(100), nullable=True)
    growth_stage = Column(String(50), nullable=True)
    
    # Weather data
    weather_conditions = Column(SQLEnum(WeatherCondition), nullable=True)
    temperature_celsius = Column(Numeric(4, 1), nullable=True)
    humidity_percent = Column(Numeric(5, 2), nullable=True)
    wind_speed_kmh = Column(Numeric(5, 2), nullable=True)
    
    # Results and outcomes
    effectiveness_rating = Column(Integer, nullable=True)  # 1-5 scale
    yield_impact = Column(Numeric(5, 2), nullable=True)  # Percentage impact
    cost_per_hectare = Column(Numeric(8, 2), nullable=True)
    
    # Additional data
    notes = Column(Text, nullable=True)
    history_metadata = Column(JSONB, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    farm = relationship("Farm", lazy="select")
    parcel = relationship("Parcel", lazy="select")
    
    def __repr__(self):
        return f"<InterventionHistory(id={self.id}, type={self.intervention_type}, date={self.intervention_date})>"
