"""
Pydantic schemas for disease diagnosis tools

Provides type-safe input/output schemas for crop disease diagnosis with:
- Disease diagnosis input/output
- EPPO code integration
- BBCH stage integration
- Environmental conditions
- Treatment recommendations
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


class DiseaseSeverity(str, Enum):
    """Disease severity levels"""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class DiseaseType(str, Enum):
    """Disease types"""
    FUNGAL = "fungal"
    BACTERIAL = "bacterial"
    VIRAL = "viral"
    NEMATODE = "nematode"
    PHYSIOLOGICAL = "physiological"
    UNKNOWN = "unknown"


class ConfidenceLevel(str, Enum):
    """Confidence levels for diagnosis"""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


class EnvironmentalConditions(BaseModel):
    """Environmental conditions for disease diagnosis"""
    
    temperature_c: Optional[float] = Field(
        default=None,
        ge=-20,
        le=50,
        description="Temperature in Celsius"
    )
    humidity_percent: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
        description="Relative humidity percentage"
    )
    rainfall_mm: Optional[float] = Field(
        default=None,
        ge=0,
        description="Recent rainfall in mm"
    )
    wind_speed_kmh: Optional[float] = Field(
        default=None,
        ge=0,
        description="Wind speed in km/h"
    )
    soil_moisture: Optional[str] = Field(
        default=None,
        description="Soil moisture level (dry, moderate, wet, saturated)"
    )
    recent_weather: Optional[str] = Field(
        default=None,
        description="Recent weather description"
    )
    
    class Config:
        use_enum_values = True


class DiseaseDiagnosisInput(BaseModel):
    """Input schema for disease diagnosis"""
    
    crop_type: str = Field(
        description="Type of crop (e.g., 'blé', 'maïs', 'colza')"
    )
    symptoms: List[str] = Field(
        min_items=1,
        description="List of observed symptoms"
    )
    environmental_conditions: Optional[EnvironmentalConditions] = Field(
        default=None,
        description="Environmental conditions"
    )
    bbch_stage: Optional[int] = Field(
        default=None,
        ge=0,
        le=99,
        description="BBCH growth stage (0-99)"
    )
    eppo_code: Optional[str] = Field(
        default=None,
        description="EPPO code for crop identification"
    )
    field_location: Optional[str] = Field(
        default=None,
        description="Field location (department, region)"
    )
    affected_area_percent: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
        description="Percentage of field affected"
    )
    
    @validator('symptoms')
    def validate_symptoms(cls, v):
        """Validate symptoms list"""
        if not v:
            raise ValueError("At least one symptom is required")
        # Remove empty strings
        return [s.strip() for s in v if s.strip()]
    
    class Config:
        use_enum_values = True


class DiseaseDiagnosis(BaseModel):
    """Individual disease diagnosis result"""
    
    disease_name: str = Field(description="Disease name")
    scientific_name: Optional[str] = Field(
        default=None,
        description="Scientific name of pathogen"
    )
    disease_type: DiseaseType = Field(description="Type of disease")
    confidence: float = Field(
        ge=0,
        le=1,
        description="Confidence score (0-1)"
    )
    severity: DiseaseSeverity = Field(description="Disease severity level")
    symptoms_matched: List[str] = Field(description="Matched symptoms")
    treatment_recommendations: List[str] = Field(
        description="Treatment recommendations"
    )
    prevention_measures: List[str] = Field(
        description="Prevention measures"
    )
    eppo_code: Optional[str] = Field(
        default=None,
        description="EPPO code for disease/pathogen"
    )
    susceptible_bbch_stages: Optional[List[int]] = Field(
        default=None,
        description="BBCH stages when crop is most susceptible"
    )
    favorable_conditions: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Favorable environmental conditions"
    )
    economic_impact: Optional[str] = Field(
        default=None,
        description="Potential economic impact"
    )
    spread_rate: Optional[str] = Field(
        default=None,
        description="Disease spread rate (slow, moderate, fast)"
    )
    
    class Config:
        use_enum_values = True


class DiseaseDiagnosisOutput(BaseModel):
    """Output schema for disease diagnosis"""
    
    success: bool = Field(description="Whether diagnosis was successful")
    crop_type: str = Field(description="Crop type analyzed")
    symptoms_observed: List[str] = Field(description="Symptoms that were analyzed")
    environmental_conditions: Optional[EnvironmentalConditions] = Field(
        default=None,
        description="Environmental conditions provided"
    )
    bbch_stage: Optional[int] = Field(
        default=None,
        description="BBCH growth stage"
    )
    bbch_stage_description: Optional[str] = Field(
        default=None,
        description="Description of BBCH stage"
    )
    diagnoses: List[DiseaseDiagnosis] = Field(
        description="List of possible disease diagnoses"
    )
    diagnosis_confidence: ConfidenceLevel = Field(
        description="Overall diagnosis confidence"
    )
    treatment_recommendations: List[str] = Field(
        description="Consolidated treatment recommendations"
    )
    total_diagnoses: int = Field(
        ge=0,
        description="Total number of diagnoses"
    )
    data_source: str = Field(
        description="Data source (database, legacy_hardcoded, hybrid)"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Diagnosis timestamp"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if diagnosis failed"
    )
    error_type: Optional[str] = Field(
        default=None,
        description="Error type (validation, data_missing, api_error, etc.)"
    )
    warnings: Optional[List[str]] = Field(
        default=None,
        description="Warning messages"
    )
    
    class Config:
        use_enum_values = True


class BBCHStageInfo(BaseModel):
    """BBCH stage information"""
    
    bbch_code: int = Field(ge=0, le=99, description="BBCH code")
    principal_stage: int = Field(ge=0, le=9, description="Principal growth stage")
    description_fr: str = Field(description="French description")
    description_en: Optional[str] = Field(
        default=None,
        description="English description"
    )
    typical_duration_days: Optional[int] = Field(
        default=None,
        description="Typical duration in days"
    )
    kc_value: Optional[float] = Field(
        default=None,
        description="Crop coefficient (Kc)"
    )
    notes: Optional[str] = Field(
        default=None,
        description="Additional notes"
    )
    
    class Config:
        use_enum_values = True

