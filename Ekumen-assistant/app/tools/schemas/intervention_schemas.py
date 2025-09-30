"""
Pydantic schemas for intervention windows tool

Provides type-safe input/output schemas for identifying optimal agricultural intervention windows.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from enum import Enum


class InterventionType(str, Enum):
    """Types of agricultural interventions"""
    SPRAYING = "pulvérisation"
    FIELD_WORK = "travaux_champ"
    PLANTING = "semis"
    HARVESTING = "récolte"
    FERTILIZATION = "fertilisation"
    IRRIGATION = "irrigation"


class WindowCondition(str, Enum):
    """Quality of intervention window conditions"""
    EXCELLENT = "excellentes"
    OPTIMAL = "optimales"
    GOOD = "bonnes"
    FAVORABLE = "favorables"
    ACCEPTABLE = "acceptables"
    POOR = "médiocres"


class InterventionWindowsInput(BaseModel):
    """Input schema for intervention windows tool"""
    weather_data_json: str = Field(
        description="JSON string from weather tool containing forecast data"
    )
    intervention_types: Optional[List[str]] = Field(
        default=None,
        description="List of intervention types to analyze (pulvérisation, travaux_champ, semis, récolte, etc.)"
    )
    
    @field_validator('weather_data_json')
    @classmethod
    def validate_json_string(cls, v: str) -> str:
        """Validate that weather_data_json is a non-empty string"""
        if not v or not v.strip():
            raise ValueError("weather_data_json cannot be empty")
        return v
    
    @field_validator('intervention_types')
    @classmethod
    def validate_intervention_types(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        """Validate intervention types if provided"""
        if v is not None:
            if len(v) == 0:
                raise ValueError("intervention_types cannot be empty list")
            # Validate each type
            valid_types = [t.value for t in InterventionType]
            for intervention_type in v:
                if intervention_type not in valid_types:
                    raise ValueError(
                        f"Invalid intervention type: {intervention_type}. "
                        f"Valid types: {', '.join(valid_types)}"
                    )
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "weather_data_json": '{"location": "Paris", "weather_conditions": [...]}',
                "intervention_types": ["pulvérisation", "semis"]
            }
        }


class InterventionWindowDetail(BaseModel):
    """Detailed intervention window information"""
    date: str = Field(description="Date of the intervention window (ISO format)")
    intervention_type: str = Field(description="Type of intervention (pulvérisation, semis, etc.)")
    conditions: str = Field(description="Quality of conditions (excellentes, optimales, bonnes, etc.)")
    duration_hours: float = Field(
        ge=0,
        le=24,
        description="Estimated duration of optimal window in hours"
    )
    confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Confidence level in the window quality (0-1)"
    )
    weather_summary: Optional[str] = Field(
        default=None,
        description="Brief summary of weather conditions"
    )
    constraints: Optional[List[str]] = Field(
        default_factory=list,
        description="Any constraints or warnings for this window"
    )


class WindowStatistics(BaseModel):
    """Statistics for intervention windows"""
    total_windows: int = Field(ge=0, description="Total number of windows identified")
    windows_by_type: Dict[str, int] = Field(
        default_factory=dict,
        description="Count of windows by intervention type"
    )
    average_confidence: float = Field(
        ge=0.0,
        le=1.0,
        description="Average confidence across all windows"
    )
    best_window_date: Optional[str] = Field(
        default=None,
        description="Date of the best overall window"
    )
    best_window_type: Optional[str] = Field(
        default=None,
        description="Type of the best overall window"
    )


class InterventionWindowsOutput(BaseModel):
    """Output schema for intervention windows tool"""
    location: str = Field(description="Location name")
    forecast_period_days: int = Field(
        ge=0,  # Allow 0 for error cases
        le=14,
        description="Number of forecast days analyzed"
    )
    intervention_types: List[str] = Field(
        default_factory=list,
        description="List of intervention types analyzed"
    )
    windows: List[InterventionWindowDetail] = Field(
        default_factory=list,
        description="List of identified intervention windows"
    )
    window_statistics: WindowStatistics = Field(
        description="Summary statistics for windows"
    )
    window_insights: List[str] = Field(
        default_factory=list,
        description="Human-readable insights and recommendations"
    )
    total_windows: int = Field(ge=0, description="Total number of windows identified")
    data_source: str = Field(
        default="intervention_analysis",
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
                "intervention_types": ["pulvérisation", "semis"],
                "windows": [
                    {
                        "date": "2025-09-30",
                        "intervention_type": "pulvérisation",
                        "conditions": "optimales",
                        "duration_hours": 8.0,
                        "confidence": 0.9,
                        "weather_summary": "Vent faible, pas de pluie",
                        "constraints": []
                    }
                ],
                "window_statistics": {
                    "total_windows": 5,
                    "windows_by_type": {"pulvérisation": 3, "semis": 2},
                    "average_confidence": 0.85,
                    "best_window_date": "2025-09-30",
                    "best_window_type": "pulvérisation"
                },
                "window_insights": [
                    "Meilleure fenêtre pour pulvérisation: 2025-09-30 (confiance: 90%)"
                ],
                "total_windows": 5,
                "data_source": "intervention_analysis",
                "analyzed_at": "2025-09-30T10:00:00Z",
                "success": True
            }
        }


# Default intervention types if none specified
DEFAULT_INTERVENTION_TYPES = [
    InterventionType.SPRAYING.value,
    InterventionType.FIELD_WORK.value,
    InterventionType.PLANTING.value,
    InterventionType.HARVESTING.value
]


# Intervention criteria (thresholds for optimal conditions)
INTERVENTION_CRITERIA = {
    "pulvérisation": {
        "max_wind_speed": 10,  # km/h
        "max_precipitation": 2,  # mm
        "max_humidity": 80,  # %
        "min_temperature": 5,  # °C
        "optimal_duration": 8,  # hours
        "confidence": 0.9
    },
    "travaux_champ": {
        "max_precipitation": 1,  # mm
        "min_temperature": 5,  # °C
        "max_wind_speed": 20,  # km/h
        "optimal_duration": 10,  # hours
        "confidence": 0.8
    },
    "semis": {
        "min_temperature": 8,  # °C
        "max_precipitation": 3,  # mm
        "min_humidity": 60,  # %
        "optimal_duration": 6,  # hours
        "confidence": 0.7
    },
    "récolte": {
        "max_precipitation": 1,  # mm
        "max_humidity": 70,  # %
        "max_wind_speed": 15,  # km/h
        "optimal_duration": 12,  # hours
        "confidence": 0.95
    },
    "fertilisation": {
        "max_wind_speed": 15,  # km/h
        "max_precipitation": 2,  # mm
        "min_temperature": 5,  # °C
        "optimal_duration": 8,  # hours
        "confidence": 0.85
    },
    "irrigation": {
        "max_precipitation": 5,  # mm (avoid if recent rain)
        "min_temperature": 10,  # °C
        "max_wind_speed": 25,  # km/h
        "optimal_duration": 6,  # hours
        "confidence": 0.75
    }
}

