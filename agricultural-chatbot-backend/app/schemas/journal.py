"""
Journal schemas for agricultural chatbot
Pydantic models for voice journal and intervention management
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from app.models.intervention import InterventionType, ValidationStatus, WeatherCondition


class JournalEntryCreate(BaseModel):
    """Schema for creating a journal entry"""
    content: str = Field(..., min_length=1, max_length=10000)
    intervention_type: InterventionType
    parcel_id: Optional[str] = None
    products_used: Optional[List[Dict[str, Any]]] = None
    weather_conditions: Optional[WeatherCondition] = None
    temperature_celsius: Optional[Decimal] = Field(None, ge=-50, le=60)
    humidity_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    wind_speed_kmh: Optional[Decimal] = Field(None, ge=0, le=200)
    notes: Optional[str] = None
    
    @validator('content')
    def validate_content(cls, v):
        if not v.strip():
            raise ValueError('Journal entry content cannot be empty')
        return v.strip()


class JournalEntryResponse(BaseModel):
    """Schema for journal entry response"""
    id: str
    content: str
    intervention_type: InterventionType
    parcel_id: Optional[str]
    products_used: Optional[List[Dict[str, Any]]]
    weather_conditions: Optional[WeatherCondition]
    validation_status: ValidationStatus
    created_at: datetime
    
    class Config:
        from_attributes = True


class ValidationResult(BaseModel):
    """Schema for validation result"""
    is_valid: bool
    status: ValidationStatus
    error_message: Optional[str] = None
    warnings: Optional[List[str]] = None
    compliance_issues: Optional[List[str]] = None
    safety_alerts: Optional[List[str]] = None
    recommendations: Optional[List[str]] = None


class ProductUsageCreate(BaseModel):
    """Schema for product usage"""
    product_name: str = Field(..., max_length=255)
    amm_number: Optional[str] = Field(None, max_length=20)
    quantity_used: Decimal = Field(..., gt=0)
    unit: str = Field(..., max_length=20)
    concentration: Optional[Decimal] = Field(None, ge=0, le=100)
    application_rate: Optional[Decimal] = Field(None, gt=0)


class ProductUsageResponse(BaseModel):
    """Schema for product usage response"""
    id: str
    product_name: str
    amm_number: Optional[str]
    quantity_used: Decimal
    unit: str
    concentration: Optional[Decimal]
    application_rate: Optional[Decimal]
    phi_days: Optional[int]
    reentry_period_hours: Optional[int]
    epi_required: Optional[List[str]]
    created_at: datetime
    
    class Config:
        from_attributes = True


class InterventionHistoryCreate(BaseModel):
    """Schema for intervention history"""
    intervention_type: InterventionType
    intervention_date: datetime
    parcel_id: Optional[str] = None
    crop_name: Optional[str] = Field(None, max_length=100)
    growth_stage: Optional[str] = Field(None, max_length=50)
    weather_conditions: Optional[WeatherCondition] = None
    temperature_celsius: Optional[Decimal] = Field(None, ge=-50, le=60)
    humidity_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    wind_speed_kmh: Optional[Decimal] = Field(None, ge=0, le=200)
    effectiveness_rating: Optional[int] = Field(None, ge=1, le=5)
    yield_impact: Optional[Decimal] = None
    cost_per_hectare: Optional[Decimal] = Field(None, ge=0)
    notes: Optional[str] = None


class InterventionHistoryResponse(BaseModel):
    """Schema for intervention history response"""
    id: str
    intervention_type: InterventionType
    intervention_date: datetime
    crop_name: Optional[str]
    growth_stage: Optional[str]
    weather_conditions: Optional[WeatherCondition]
    effectiveness_rating: Optional[int]
    yield_impact: Optional[Decimal]
    cost_per_hectare: Optional[Decimal]
    created_at: datetime
    
    class Config:
        from_attributes = True


class VoiceTranscriptionRequest(BaseModel):
    """Schema for voice transcription request"""
    audio_file_path: str
    language: str = "fr"
    model: str = "whisper-1"


class VoiceTranscriptionResponse(BaseModel):
    """Schema for voice transcription response"""
    text: str
    confidence: float
    language: str
    duration: Optional[float] = None


class JournalEntryUpdate(BaseModel):
    """Schema for updating journal entry"""
    content: Optional[str] = Field(None, min_length=1, max_length=10000)
    intervention_type: Optional[InterventionType] = None
    parcel_id: Optional[str] = None
    products_used: Optional[List[Dict[str, Any]]] = None
    weather_conditions: Optional[WeatherCondition] = None
    temperature_celsius: Optional[Decimal] = Field(None, ge=-50, le=60)
    humidity_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    wind_speed_kmh: Optional[Decimal] = Field(None, ge=0, le=200)
    notes: Optional[str] = None
    
    @validator('content')
    def validate_content(cls, v):
        if v is not None and not v.strip():
            raise ValueError('Journal entry content cannot be empty')
        return v.strip() if v else v


class JournalEntryFilter(BaseModel):
    """Schema for filtering journal entries"""
    farm_siret: Optional[str] = None
    parcel_id: Optional[str] = None
    intervention_type: Optional[InterventionType] = None
    validation_status: Optional[ValidationStatus] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    limit: int = Field(default=50, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)
