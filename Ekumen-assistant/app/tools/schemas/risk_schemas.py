"""
Pydantic schemas for weather risk analysis tool

Provides type-safe input/output schemas for agricultural risk analysis.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from enum import Enum


class RiskSeverity(str, Enum):
    """Risk severity levels"""
    LOW = "faible"
    MODERATE = "modérée"
    HIGH = "élevée"
    CRITICAL = "critique"


class RiskType(str, Enum):
    """Types of agricultural weather risks"""
    FROST = "gel"
    WIND = "vent"
    HEAVY_RAIN = "pluie"
    HEAT_STRESS = "stress_thermique"
    DROUGHT = "sécheresse"
    HAIL = "grêle"
    STORM = "orage"


class RiskAnalysisInput(BaseModel):
    """Input schema for risk analysis tool"""
    weather_data_json: str = Field(
        description="JSON string from weather tool containing forecast data"
    )
    crop_type: Optional[str] = Field(
        default=None,
        description="Type of crop for crop-specific risk analysis (blé, maïs, colza, etc.)"
    )
    
    @field_validator('weather_data_json')
    @classmethod
    def validate_json_string(cls, v: str) -> str:
        """Validate that weather_data_json is a non-empty string"""
        if not v or not v.strip():
            raise ValueError("weather_data_json cannot be empty")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "weather_data_json": '{"location": "Paris", "weather_conditions": [...]}',
                "crop_type": "blé"
            }
        }


class WeatherRiskDetail(BaseModel):
    """Detailed weather risk information"""
    risk_type: str = Field(description="Type of risk (gel, vent, pluie, etc.)")
    severity: str = Field(description="Severity level (faible, modérée, élevée, critique)")
    probability: float = Field(
        ge=0.0,
        le=1.0,
        description="Probability of risk occurrence (0-1)"
    )
    impact: str = Field(description="Description of potential impact")
    recommendations: List[str] = Field(
        default_factory=list,
        description="List of recommended actions"
    )
    affected_date: Optional[str] = Field(
        default=None,
        description="Date when risk is expected (ISO format)"
    )


class RiskSummary(BaseModel):
    """Summary statistics for risk analysis"""
    total_risks: int = Field(ge=0, description="Total number of risks identified")
    high_severity_risks: int = Field(ge=0, description="Number of high severity risks")
    risk_types: List[str] = Field(
        default_factory=list,
        description="List of unique risk types identified"
    )
    most_common_risk: Optional[str] = Field(
        default=None,
        description="Most frequently occurring risk type"
    )


class RiskAnalysisOutput(BaseModel):
    """Output schema for risk analysis tool"""
    location: str = Field(description="Location name")
    forecast_period_days: int = Field(
        ge=0,  # Allow 0 for error cases
        le=14,
        description="Number of forecast days analyzed"
    )
    risks: List[WeatherRiskDetail] = Field(
        default_factory=list,
        description="List of identified weather risks"
    )
    risk_summary: RiskSummary = Field(description="Summary statistics")
    risk_insights: List[str] = Field(
        default_factory=list,
        description="Human-readable risk insights and recommendations"
    )
    crop_type: Optional[str] = Field(
        default=None,
        description="Crop type analyzed (if specified)"
    )
    total_risks: int = Field(ge=0, description="Total number of risks identified")
    data_source: str = Field(
        default="weather_analysis",
        description="Source of the analysis"
    )
    analyzed_at: str = Field(description="Timestamp when analysis was performed (ISO format)")
    
    # Error handling fields
    success: bool = Field(default=True, description="Whether the analysis was successful")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    error_type: Optional[str] = Field(
        default=None,
        description="Error type (validation, data_missing, analysis_failed, unknown)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "location": "Paris",
                "forecast_period_days": 7,
                "risks": [
                    {
                        "risk_type": "gel",
                        "severity": "élevée",
                        "probability": 0.9,
                        "impact": "Dégâts sur cultures sensibles",
                        "recommendations": ["Protéger les cultures sensibles"],
                        "affected_date": "2025-09-30"
                    }
                ],
                "risk_summary": {
                    "total_risks": 3,
                    "high_severity_risks": 1,
                    "risk_types": ["gel", "vent"],
                    "most_common_risk": "gel"
                },
                "risk_insights": [
                    "⚠️ Risque de gel - Protéger les cultures sensibles"
                ],
                "crop_type": "blé",
                "total_risks": 3,
                "data_source": "weather_analysis",
                "analyzed_at": "2025-09-30T10:00:00Z",
                "success": True
            }
        }


class CropRiskProfile(BaseModel):
    """Crop-specific risk profile"""
    crop_name: str = Field(description="Name of the crop")
    frost_tolerance: float = Field(description="Minimum temperature tolerance (°C)")
    heat_tolerance: float = Field(description="Maximum temperature tolerance (°C)")
    wind_sensitivity: str = Field(description="Wind sensitivity level (low, moderate, high)")
    water_requirements: str = Field(description="Water requirements (low, moderate, high)")
    critical_growth_stages: List[str] = Field(
        default_factory=list,
        description="Critical growth stages sensitive to weather"
    )


# Predefined crop risk profiles
CROP_RISK_PROFILES: Dict[str, CropRiskProfile] = {
    "blé": CropRiskProfile(
        crop_name="Blé",
        frost_tolerance=-5.0,
        heat_tolerance=32.0,
        wind_sensitivity="moderate",
        water_requirements="moderate",
        critical_growth_stages=["tallage", "épiaison", "floraison"]
    ),
    "maïs": CropRiskProfile(
        crop_name="Maïs",
        frost_tolerance=0.0,
        heat_tolerance=38.0,
        wind_sensitivity="high",
        water_requirements="high",
        critical_growth_stages=["levée", "floraison", "remplissage"]
    ),
    "colza": CropRiskProfile(
        crop_name="Colza",
        frost_tolerance=-8.0,
        heat_tolerance=30.0,
        wind_sensitivity="moderate",
        water_requirements="moderate",
        critical_growth_stages=["floraison", "formation_siliques"]
    ),
    "tournesol": CropRiskProfile(
        crop_name="Tournesol",
        frost_tolerance=-2.0,
        heat_tolerance=35.0,
        wind_sensitivity="high",
        water_requirements="moderate",
        critical_growth_stages=["levée", "floraison"]
    ),
    "vigne": CropRiskProfile(
        crop_name="Vigne",
        frost_tolerance=-2.0,
        heat_tolerance=40.0,
        wind_sensitivity="low",
        water_requirements="low",
        critical_growth_stages=["débourrement", "floraison", "véraison"]
    )
}

