"""
Pydantic schemas for nutrient deficiency analysis

Provides type-safe input/output schemas for nutrient analysis with:
- Nutrient deficiency input/output
- Crop-specific nutrient requirements
- Soil condition analysis
- Treatment recommendations
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


class DeficiencyLevel(str, Enum):
    """Nutrient deficiency severity levels"""
    NONE = "none"
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    CRITICAL = "critical"


class ConfidenceLevel(str, Enum):
    """Confidence levels for nutrient analysis"""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


class NutrientType(str, Enum):
    """Types of nutrients"""
    MACRONUTRIENT = "macronutrient"
    SECONDARY_NUTRIENT = "secondary_nutrient"
    MICRONUTRIENT = "micronutrient"


class SoilAnalysis(BaseModel):
    """Soil condition analysis"""
    
    pH: Optional[float] = Field(
        default=None,
        ge=3.0,
        le=10.0,
        description="Soil pH"
    )
    pH_interpretation: Optional[str] = Field(
        default=None,
        description="pH interpretation (acidic, neutral, alkaline)"
    )
    organic_matter_percent: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=100.0,
        description="Organic matter percentage"
    )
    texture: Optional[str] = Field(
        default=None,
        description="Soil texture (clay, loam, sand, etc.)"
    )
    drainage: Optional[str] = Field(
        default=None,
        description="Drainage quality (poor, moderate, good)"
    )
    cec: Optional[float] = Field(
        default=None,
        description="Cation exchange capacity (meq/100g)"
    )
    nutrient_availability_factors: List[str] = Field(
        default_factory=list,
        description="Factors affecting nutrient availability"
    )
    
    class Config:
        use_enum_values = True


class NutrientAnalysisInput(BaseModel):
    """Input schema for nutrient deficiency analysis"""
    
    crop_type: str = Field(
        description="Type of crop (e.g., 'blé', 'maïs', 'colza')"
    )
    plant_symptoms: List[str] = Field(
        min_items=1,
        description="List of observed plant symptoms"
    )
    soil_conditions: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Soil conditions (pH, organic_matter, texture, etc.)"
    )
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
    previous_fertilization: Optional[List[str]] = Field(
        default=None,
        description="Previous fertilization history"
    )
    
    @validator('plant_symptoms')
    def validate_symptoms(cls, v: List[str]) -> List[str]:
        """Validate plant symptoms"""
        if not v:
            raise ValueError("At least one plant symptom is required")
        if len(v) > 20:
            raise ValueError("Maximum 20 symptoms allowed")
        return v
    
    class Config:
        use_enum_values = True
        json_schema_extra = {
            "example": {
                "crop_type": "blé",
                "plant_symptoms": [
                    "Jaunissement des feuilles",
                    "Croissance ralentie",
                    "Feuilles pâles"
                ],
                "soil_conditions": {
                    "pH": 6.5,
                    "organic_matter_percent": 2.5,
                    "texture": "limon"
                },
                "bbch_stage": 30
            }
        }


class NutrientDeficiency(BaseModel):
    """Individual nutrient deficiency result"""
    
    nutrient: str = Field(
        description="Nutrient identifier (N, P, K, etc.)"
    )
    nutrient_name: str = Field(
        description="Full nutrient name (Azote, Phosphore, etc.)"
    )
    symbol: str = Field(
        description="Chemical symbol (N, P, K, Ca, Mg, etc.)"
    )
    nutrient_type: NutrientType = Field(
        description="Type of nutrient"
    )
    deficiency_level: DeficiencyLevel = Field(
        description="Severity of deficiency"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence score (0-1)"
    )
    symptoms_matched: List[str] = Field(
        default_factory=list,
        description="Symptoms that matched this deficiency"
    )
    soil_indicators: List[str] = Field(
        default_factory=list,
        description="Soil indicators supporting this diagnosis"
    )
    treatment_recommendations: List[str] = Field(
        default_factory=list,
        description="Treatment recommendations"
    )
    prevention_measures: List[str] = Field(
        default_factory=list,
        description="Prevention measures for future"
    )
    dosage_guidelines: Optional[Dict[str, str]] = Field(
        default=None,
        description="Dosage guidelines for treatment"
    )
    critical_stages: Optional[List[str]] = Field(
        default=None,
        description="Critical growth stages for this nutrient"
    )
    optimal_range: Optional[Dict[str, float]] = Field(
        default=None,
        description="Optimal nutrient range in soil"
    )
    current_level: Optional[float] = Field(
        default=None,
        description="Current nutrient level if known"
    )
    
    class Config:
        use_enum_values = True
        json_schema_extra = {
            "example": {
                "nutrient": "nitrogen",
                "nutrient_name": "Azote",
                "symbol": "N",
                "nutrient_type": "macronutrient",
                "deficiency_level": "moderate",
                "confidence": 0.85,
                "symptoms_matched": ["Jaunissement des feuilles", "Croissance ralentie"],
                "soil_indicators": ["pH bas", "Faible matière organique"],
                "treatment_recommendations": [
                    "Apport d'engrais azoté (100-150 kg N/ha)",
                    "Fractionnement en 2-3 apports"
                ],
                "prevention_measures": [
                    "Rotation avec légumineuses",
                    "Apport de matière organique"
                ]
            }
        }


class NutrientAnalysisOutput(BaseModel):
    """Output schema for nutrient deficiency analysis"""
    
    success: bool = Field(
        description="Whether analysis was successful"
    )
    crop_type: str = Field(
        description="Crop type analyzed"
    )
    crop_eppo_code: Optional[str] = Field(
        default=None,
        description="EPPO code for crop"
    )
    crop_category: Optional[str] = Field(
        default=None,
        description="Crop category"
    )
    plant_symptoms: List[str] = Field(
        default_factory=list,
        description="Plant symptoms analyzed"
    )
    soil_analysis: Optional[SoilAnalysis] = Field(
        default=None,
        description="Soil condition analysis"
    )
    bbch_stage: Optional[int] = Field(
        default=None,
        description="BBCH growth stage"
    )
    
    # Analysis results
    nutrient_deficiencies: List[NutrientDeficiency] = Field(
        default_factory=list,
        description="Identified nutrient deficiencies"
    )
    analysis_confidence: ConfidenceLevel = Field(
        description="Overall analysis confidence"
    )
    
    # Recommendations
    treatment_recommendations: List[str] = Field(
        default_factory=list,
        description="Consolidated treatment recommendations"
    )
    priority_actions: List[str] = Field(
        default_factory=list,
        description="Priority actions to take"
    )
    prevention_measures: List[str] = Field(
        default_factory=list,
        description="Long-term prevention measures"
    )
    
    # Metadata
    total_deficiencies: int = Field(
        ge=0,
        description="Total number of deficiencies identified"
    )
    critical_deficiencies: int = Field(
        default=0,
        ge=0,
        description="Number of critical deficiencies"
    )
    data_source: str = Field(
        default="database_enhanced",
        description="Data source used for analysis"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Analysis timestamp"
    )
    
    # Error handling
    error: Optional[str] = Field(
        default=None,
        description="Error message if analysis failed"
    )
    error_type: Optional[str] = Field(
        default=None,
        description="Error type if analysis failed"
    )
    validation_warnings: Optional[List[str]] = Field(
        default=None,
        description="Validation warnings"
    )
    
    class Config:
        use_enum_values = True
