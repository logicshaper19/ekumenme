"""
Pydantic schemas for weather tools

Provides type safety and validation for weather data.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum


class WindDirection(str, Enum):
    """Wind direction enum"""
    N = "N"
    NE = "NE"
    E = "E"
    SE = "SE"
    S = "S"
    SO = "SO"
    SW = "SW"
    O = "O"
    W = "W"
    NO = "NO"
    NW = "NW"


class WeatherCondition(BaseModel):
    """Single day weather condition"""
    date: str = Field(description="Date in YYYY-MM-DD format")
    temperature_min: float = Field(ge=-50, le=60, description="Minimum temperature in °C")
    temperature_max: float = Field(ge=-50, le=60, description="Maximum temperature in °C")
    humidity: float = Field(ge=0, le=100, description="Humidity percentage")
    wind_speed: float = Field(ge=0, description="Wind speed in km/h")
    wind_direction: str = Field(description="Wind direction (N, NE, E, SE, S, SO, O, NO)")
    precipitation: float = Field(ge=0, description="Precipitation in mm")
    cloud_cover: float = Field(ge=0, le=100, description="Cloud cover percentage")
    uv_index: float = Field(ge=0, le=15, description="UV index")
    
    @field_validator('date')
    @classmethod
    def validate_date(cls, v: str) -> str:
        """Validate date format"""
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError('Date must be in YYYY-MM-DD format')
    
    @field_validator('temperature_max')
    @classmethod
    def validate_temp_range(cls, v: float, info) -> float:
        """Validate that max temp is greater than min temp"""
        if 'temperature_min' in info.data and v < info.data['temperature_min']:
            raise ValueError('temperature_max must be >= temperature_min')
        return v


class RiskSeverity(str, Enum):
    """Risk severity levels"""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class WeatherRisk(BaseModel):
    """Agricultural weather risk"""
    risk_type: str = Field(description="Type of risk (frost, heat, wind, drought, etc.)")
    severity: RiskSeverity = Field(description="Severity level")
    probability: float = Field(ge=0, le=1, description="Probability of occurrence (0-1)")
    impact: str = Field(description="Impact description in French")
    recommendations: List[str] = Field(description="Recommended actions in French")
    affected_dates: List[str] = Field(default_factory=list, description="Dates affected by this risk")
    
    class Config:
        json_schema_extra = {
            "example": {
                "risk_type": "frost",
                "severity": "high",
                "probability": 0.8,
                "impact": "Risque de gel sur cultures sensibles",
                "recommendations": [
                    "Reporter les semis",
                    "Protéger les cultures sensibles",
                    "Surveiller les prévisions"
                ],
                "affected_dates": ["2024-03-22", "2024-03-23"]
            }
        }


class InterventionWindow(BaseModel):
    """Optimal intervention window for field operations"""
    start_date: str = Field(description="Window start date (YYYY-MM-DD)")
    end_date: str = Field(description="Window end date (YYYY-MM-DD)")
    suitability_score: float = Field(ge=0, le=1, description="Suitability score (0-1)")
    conditions: str = Field(description="Expected conditions in French")
    recommendations: str = Field(description="Recommendations in French")
    intervention_types: List[str] = Field(
        default_factory=list,
        description="Suitable intervention types (semis, traitement, récolte, etc.)"
    )
    
    @field_validator('start_date', 'end_date')
    @classmethod
    def validate_date(cls, v: str) -> str:
        """Validate date format"""
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError('Date must be in YYYY-MM-DD format')
    
    class Config:
        json_schema_extra = {
            "example": {
                "start_date": "2024-03-25",
                "end_date": "2024-03-27",
                "suitability_score": 0.9,
                "conditions": "Vent faible (8 km/h), pas de pluie, température modérée",
                "recommendations": "Conditions optimales pour traitements phytosanitaires",
                "intervention_types": ["traitement", "épandage"]
            }
        }


class Coordinates(BaseModel):
    """Geographic coordinates"""
    lat: float = Field(ge=-90, le=90, description="Latitude")
    lon: float = Field(ge=-180, le=180, description="Longitude")


class WeatherInput(BaseModel):
    """Input schema for weather data tool"""
    location: str = Field(
        description="Location name (e.g., 'Normandie', 'Calvados')",
        min_length=2,
        max_length=100
    )
    days: int = Field(
        default=7,
        ge=1,
        le=14,
        description="Number of forecast days (1-14)"
    )
    coordinates: Optional[Coordinates] = Field(
        default=None,
        description="Optional lat/lon coordinates"
    )
    use_real_api: bool = Field(
        default=True,
        description="Whether to use real weather APIs (default: True)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "location": "Normandie",
                "days": 7,
                "coordinates": {"lat": 49.18, "lon": 0.37},
                "use_real_api": True
            }
        }


class WeatherOutput(BaseModel):
    """Output schema for weather data tool"""
    location: str = Field(description="Location name")
    coordinates: Coordinates = Field(description="Geographic coordinates")
    forecast_period_days: int = Field(description="Number of forecast days")
    weather_conditions: List[WeatherCondition] = Field(
        default_factory=list,
        description="Daily weather forecast"
    )
    risks: List[WeatherRisk] = Field(
        default_factory=list,
        description="Agricultural risks identified"
    )
    intervention_windows: List[InterventionWindow] = Field(
        default_factory=list,
        description="Optimal intervention windows"
    )
    total_days: int = Field(description="Total number of forecast days returned")
    data_source: str = Field(description="Data source (weatherapi.com, openweathermap, mock_data, error)")
    retrieved_at: str = Field(description="Timestamp when data was retrieved (ISO format)")

    # Error handling fields
    success: bool = Field(default=True, description="Whether the request was successful")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    error_type: Optional[str] = Field(
        default=None,
        description="Error type (validation, api, timeout, location_not_found, unknown)"
    )
    
    @field_validator('retrieved_at')
    @classmethod
    def validate_timestamp(cls, v: str) -> str:
        """Validate ISO timestamp format"""
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except ValueError:
            raise ValueError('retrieved_at must be in ISO format')
    
    class Config:
        json_schema_extra = {
            "example": {
                "location": "Normandie",
                "coordinates": {"lat": 49.18, "lon": 0.37},
                "forecast_period_days": 7,
                "weather_conditions": [
                    {
                        "date": "2024-03-22",
                        "temperature_min": 8.5,
                        "temperature_max": 18.2,
                        "humidity": 72,
                        "wind_speed": 12,
                        "wind_direction": "SO",
                        "precipitation": 0,
                        "cloud_cover": 30,
                        "uv_index": 4
                    }
                ],
                "risks": [
                    {
                        "risk_type": "wind",
                        "severity": "moderate",
                        "probability": 0.6,
                        "impact": "Vent modéré - attention aux traitements",
                        "recommendations": ["Éviter les traitements en milieu de journée"],
                        "affected_dates": ["2024-03-23"]
                    }
                ],
                "intervention_windows": [
                    {
                        "start_date": "2024-03-25",
                        "end_date": "2024-03-27",
                        "suitability_score": 0.9,
                        "conditions": "Conditions optimales",
                        "recommendations": "Fenêtre idéale pour interventions",
                        "intervention_types": ["traitement", "semis"]
                    }
                ],
                "total_days": 7,
                "data_source": "weatherapi.com",
                "retrieved_at": "2024-03-22T10:00:00Z"
            }
        }


class WeatherRiskAnalysisInput(BaseModel):
    """Input for weather risk analysis"""
    weather_conditions: List[WeatherCondition] = Field(description="Weather forecast to analyze")
    crop_type: Optional[str] = Field(default=None, description="Crop type for specific risk analysis")
    growth_stage: Optional[str] = Field(default=None, description="Current growth stage")


class InterventionWindowInput(BaseModel):
    """Input for intervention window identification"""
    weather_conditions: List[WeatherCondition] = Field(description="Weather forecast to analyze")
    intervention_type: str = Field(
        description="Type of intervention (traitement, semis, récolte, épandage)"
    )
    min_duration_days: int = Field(
        default=1,
        ge=1,
        description="Minimum duration required (days)"
    )

