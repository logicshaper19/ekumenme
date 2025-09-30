"""
Pydantic schemas for pest identification tools

Provides type-safe input/output schemas for crop pest identification with:
- Pest identification input/output
- EPPO code integration
- Crop category integration
- Damage pattern analysis
- Treatment recommendations
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


class PestSeverity(str, Enum):
    """Pest severity levels"""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class PestType(str, Enum):
    """Pest types"""
    INSECT = "insect"
    MITE = "mite"
    SLUG = "slug"
    RODENT = "rodent"
    BIRD = "bird"
    NEMATODE = "nematode"
    UNKNOWN = "unknown"


class PestStage(str, Enum):
    """Pest life cycle stages"""
    EGG = "egg"
    LARVA = "larva"
    PUPA = "pupa"
    ADULT = "adult"
    NYMPH = "nymph"
    UNKNOWN = "unknown"


class ConfidenceLevel(str, Enum):
    """Confidence levels for identification"""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


class PestIdentificationInput(BaseModel):
    """Input schema for pest identification"""
    
    crop_type: str = Field(
        description="Type of crop (e.g., 'blé', 'maïs', 'colza')",
        min_length=1,
        max_length=100
    )
    damage_symptoms: List[str] = Field(
        min_items=1,
        max_items=50,
        description="List of observed damage symptoms"
    )
    pest_indicators: Optional[List[str]] = Field(
        default=None,
        description="List of pest indicators (eggs, larvae, adults observed)"
    )

    @validator('pest_indicators')
    def clean_indicators(cls, v):
        """Remove empty strings and limit to 30 items"""
        if v is None:
            return None
        cleaned = [s.strip() for s in v if s and s.strip()]
        return cleaned[:30] if len(cleaned) > 30 else cleaned
    eppo_code: Optional[str] = Field(
        default=None,
        description="EPPO code for crop identification"
    )
    crop_category: Optional[str] = Field(
        default=None,
        description="Crop category (cereal, oilseed, root_crop, etc.)"
    )
    bbch_stage: Optional[int] = Field(
        default=None,
        ge=0,
        le=99,
        description="BBCH growth stage (0-99)"
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
    infestation_level: Optional[str] = Field(
        default=None,
        description="Infestation level (low, moderate, high)"
    )
    
    @validator('damage_symptoms')
    def validate_symptoms(cls, v):
        """Validate damage symptoms list"""
        if not v:
            raise ValueError("At least one damage symptom is required")
        # Remove empty strings
        return [s.strip() for s in v if s.strip()]
    
    class Config:
        use_enum_values = True


class PestIdentification(BaseModel):
    """Individual pest identification result"""
    
    pest_name: str = Field(description="Pest name")
    scientific_name: Optional[str] = Field(
        default=None,
        description="Scientific name of pest"
    )
    pest_type: PestType = Field(description="Type of pest")
    pest_stage: Optional[PestStage] = Field(
        default=None,
        description="Life cycle stage observed"
    )
    confidence: float = Field(
        ge=0,
        le=1,
        description="Confidence score (0-1)"
    )
    severity: PestSeverity = Field(description="Pest severity level")
    damage_patterns: List[str] = Field(description="Matched damage patterns")
    treatment_recommendations: List[str] = Field(
        description="Treatment recommendations"
    )
    prevention_measures: List[str] = Field(
        description="Prevention measures"
    )
    eppo_code: Optional[str] = Field(
        default=None,
        description="EPPO code for pest"
    )
    susceptible_bbch_stages: Optional[List[int]] = Field(
        default=None,
        description="BBCH stages when crop is most susceptible"
    )
    economic_threshold: Optional[str] = Field(
        default=None,
        description="Economic threshold for intervention"
    )
    natural_enemies: Optional[List[str]] = Field(
        default=None,
        description="Natural enemies for biological control"
    )
    monitoring_methods: Optional[List[str]] = Field(
        default=None,
        description="Monitoring methods"
    )
    
    class Config:
        use_enum_values = True


class PestIdentificationOutput(BaseModel):
    """Output schema for pest identification"""
    
    success: bool = Field(description="Whether identification was successful")
    crop_type: str = Field(description="Crop type analyzed")
    crop_eppo_code: Optional[str] = Field(
        default=None,
        description="EPPO code for crop"
    )
    crop_category: Optional[str] = Field(
        default=None,
        description="Crop category"
    )
    damage_symptoms: List[str] = Field(description="Damage symptoms analyzed")
    pest_indicators: Optional[List[str]] = Field(
        default=None,
        description="Pest indicators provided"
    )
    bbch_stage: Optional[int] = Field(
        default=None,
        description="BBCH growth stage"
    )
    pest_identifications: List[PestIdentification] = Field(
        description="List of possible pest identifications"
    )
    identification_confidence: ConfidenceLevel = Field(
        description="Overall identification confidence"
    )
    treatment_recommendations: List[str] = Field(
        description="Consolidated treatment recommendations"
    )
    total_identifications: int = Field(
        ge=0,
        description="Total number of pest identifications"
    )
    data_source: str = Field(
        description="Data source (database, legacy_hardcoded, hybrid)"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Identification timestamp"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if identification failed"
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


class CropCategoryRiskProfile(BaseModel):
    """Risk profile for crop category"""
    
    category: str = Field(description="Crop category")
    common_pests: List[str] = Field(description="Common pests for this category")
    high_risk_periods: Optional[List[str]] = Field(
        default=None,
        description="High risk periods (BBCH stages or months)"
    )
    prevention_strategies: Optional[List[str]] = Field(
        default=None,
        description="Category-specific prevention strategies"
    )
    
    class Config:
        use_enum_values = True

