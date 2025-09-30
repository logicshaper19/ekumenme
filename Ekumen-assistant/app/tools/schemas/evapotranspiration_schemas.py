"""
Pydantic schemas for Evapotranspiration Tool

Provides type-safe input/output schemas for evapotranspiration calculations
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import List, Optional, Dict, Any
from enum import Enum


class CropType(str, Enum):
    """Supported crop types for evapotranspiration calculations"""
    BLE = "blé"
    MAIS = "maïs"
    COLZA = "colza"
    ORGE = "orge"
    TOURNESOL = "tournesol"
    BETTERAVE = "betterave"
    POMME_DE_TERRE = "pomme de terre"
    VIGNE = "vigne"
    PRAIRIE = "prairie"
    GENERAL = "general"


class CropStage(str, Enum):
    """
    FAO-56 crop development stages (simplified 4-stage model)

    This is the standard FAO-56 approach for evapotranspiration calculations.
    Simple, user-friendly, and accurate enough for irrigation decisions.

    Maps to BBCH ranges when needed:
    - semis: BBCH 0-29 (germination to tillering)
    - croissance: BBCH 30-59 (stem elongation to heading)
    - floraison: BBCH 60-69 (flowering)
    - maturation: BBCH 70-99 (grain fill to ripening)
    """
    SEMIS = "semis"              # Initial stage: planting to ~10% ground cover
    CROISSANCE = "croissance"    # Development: ~10% to ~70-80% ground cover
    FLORAISON = "floraison"      # Mid-season: flowering, peak water demand
    MATURATION = "maturation"    # Late season: grain fill to harvest


class IrrigationMethod(str, Enum):
    """Irrigation methods"""
    ASPERSION = "aspersion"
    GOUTTE_A_GOUTTE = "goutte à goutte"
    PIVOT = "pivot"
    GRAVITAIRE = "gravitaire"
    MICRO_ASPERSION = "micro-aspersion"


class EvapotranspirationInput(BaseModel):
    """
    Input schema for evapotranspiration calculation

    Two-layer design:
    - User-friendly: 4 simple stages (semis, croissance, floraison, maturation)
    - Database integration: Optional BBCH code (auto-converts to simple stage)
    """

    weather_data_json: str = Field(
        description="JSON string from weather tool containing forecast data"
    )
    crop_type: Optional[str] = Field(
        default=None,
        description="Type de culture pour calculs spécifiques (blé, maïs, colza, etc.)"
    )

    # Simple stage (user-friendly, FAO-56 standard)
    crop_stage: Optional[CropStage] = Field(
        default=None,
        description="Stade de développement (semis, croissance, floraison, maturation)"
    )

    # BBCH code (optional, from database observations)
    bbch_code: Optional[int] = Field(
        default=None,
        ge=0,
        le=99,
        description="Code BBCH (0-99) depuis observations terrain. Auto-converti en stade simple."
    )

    @field_validator('weather_data_json')
    @classmethod
    def validate_weather_data(cls, v: str) -> str:
        """Validate weather data JSON is not empty"""
        if not v or not v.strip():
            raise ValueError("weather_data_json ne peut pas être vide")
        return v

    @model_validator(mode='after')
    def validate_stage_inputs(self):
        """Auto-convert BBCH to simple stage if needed"""
        if self.crop_type and not self.crop_stage and self.bbch_code is not None:
            # Auto-convert BBCH to simple stage
            self.crop_stage = self._bbch_to_simple_stage(self.bbch_code)
        elif self.crop_type and not self.crop_stage:
            # Default to croissance if no stage specified
            self.crop_stage = CropStage.CROISSANCE
        return self

    def _bbch_to_simple_stage(self, bbch: int) -> CropStage:
        """
        Convert BBCH code to simple FAO-56 stage

        Mapping for cereals (blé, maïs, orge):
        - BBCH 0-29: semis (germination to tillering)
        - BBCH 30-59: croissance (stem elongation to heading)
        - BBCH 60-69: floraison (flowering)
        - BBCH 70-99: maturation (grain fill to ripening)
        """
        if bbch <= 29:
            return CropStage.SEMIS
        elif bbch <= 59:
            return CropStage.CROISSANCE
        elif bbch <= 69:
            return CropStage.FLORAISON
        else:
            return CropStage.MATURATION

    @property
    def effective_stage(self) -> str:
        """Get effective stage for Kc lookup (always returns simple stage)"""
        return self.crop_stage.value if self.crop_stage else "croissance"

    class Config:
        json_schema_extra = {
            "example": {
                "weather_data_json": '{"location": "Paris", "weather_conditions": [...]}',
                "crop_type": "blé",
                "bbch_code": 65,  # Flowering
                "fao56_stage": None,  # Optional fallback
                "crop_stage": None  # Deprecated
            }
        }


class DailyEvapotranspiration(BaseModel):
    """Daily evapotranspiration data"""
    
    date: str = Field(description="Date (YYYY-MM-DD)")
    et0: float = Field(description="Évapotranspiration de référence (mm/jour)", ge=0)
    etc: Optional[float] = Field(
        default=None,
        description="Évapotranspiration de la culture (mm/jour)",
        ge=0
    )
    kc: Optional[float] = Field(
        default=None,
        description="Coefficient cultural",
        ge=0,
        le=2.0
    )
    temperature_avg: float = Field(description="Température moyenne (°C)")
    humidity_avg: float = Field(description="Humidité moyenne (%)", ge=0, le=100)
    wind_speed_avg: float = Field(description="Vitesse du vent moyenne (km/h)", ge=0)
    solar_radiation: Optional[float] = Field(
        default=None,
        description="Rayonnement solaire (MJ/m²/jour)",
        ge=0
    )


class WaterBalance(BaseModel):
    """Water balance for a period"""
    
    total_et0: float = Field(description="ETP totale de référence (mm)", ge=0)
    total_etc: Optional[float] = Field(
        default=None,
        description="ETP totale de la culture (mm)",
        ge=0
    )
    total_precipitation: float = Field(description="Précipitations totales (mm)", ge=0)
    water_deficit: float = Field(description="Déficit hydrique (mm)")
    water_surplus: float = Field(description="Excédent hydrique (mm)", ge=0)
    irrigation_needed: bool = Field(description="Irrigation nécessaire")
    irrigation_amount: Optional[float] = Field(
        default=None,
        description="Quantité d'irrigation recommandée (mm)",
        ge=0
    )


class IrrigationRecommendation(BaseModel):
    """Irrigation recommendation"""
    
    date: str = Field(description="Date recommandée (YYYY-MM-DD)")
    amount_mm: float = Field(description="Quantité d'eau (mm)", ge=0)
    amount_m3_ha: float = Field(description="Quantité d'eau (m³/ha)", ge=0)
    priority: str = Field(description="Priorité (haute, moyenne, basse)")
    reason: str = Field(description="Raison de la recommandation")
    optimal_time: Optional[str] = Field(
        default=None,
        description="Heure optimale (matin, soir, nuit)"
    )
    method_recommendation: Optional[str] = Field(
        default=None,
        description="Méthode d'irrigation recommandée"
    )


class EvapotranspirationOutput(BaseModel):
    """Output schema for evapotranspiration calculation"""

    location: str = Field(description="Localisation")
    forecast_period_days: int = Field(description="Période de prévision (jours)", ge=1)
    crop_type: Optional[str] = Field(default=None, description="Type de culture")
    crop_stage: Optional[str] = Field(default=None, description="Stade de développement (semis, croissance, floraison, maturation)")

    # Optional BBCH info (if provided in input)
    bbch_code: Optional[int] = Field(default=None, ge=0, le=99, description="Code BBCH source (si fourni)")
    bbch_description: Optional[str] = Field(default=None, description="Description du stade BBCH")
    
    # Daily evapotranspiration data
    daily_et: List[DailyEvapotranspiration] = Field(
        description="Données d'évapotranspiration quotidiennes"
    )
    
    # Water balance
    water_balance: WaterBalance = Field(description="Bilan hydrique")
    
    # Irrigation recommendations
    irrigation_recommendations: List[IrrigationRecommendation] = Field(
        default_factory=list,
        description="Recommandations d'irrigation"
    )
    
    # Summary statistics
    avg_et0: float = Field(description="ETP moyenne de référence (mm/jour)", ge=0)
    avg_etc: Optional[float] = Field(
        default=None,
        description="ETP moyenne de la culture (mm/jour)",
        ge=0
    )
    peak_et_date: Optional[str] = Field(
        default=None,
        description="Date du pic d'évapotranspiration"
    )
    peak_et_value: Optional[float] = Field(
        default=None,
        description="Valeur du pic d'évapotranspiration (mm/jour)",
        ge=0
    )
    
    # Metadata
    calculation_method: str = Field(
        default="Penman-Monteith FAO-56",
        description="Méthode de calcul utilisée"
    )
    data_source: str = Field(
        default="weather_analysis",
        description="Source des données"
    )
    calculated_at: str = Field(description="Date de calcul (ISO 8601)")
    
    # Error handling
    success: bool = Field(default=True, description="Succès de l'opération")
    error: Optional[str] = Field(default=None, description="Message d'erreur")
    error_type: Optional[str] = Field(default=None, description="Type d'erreur")
    warnings: List[str] = Field(
        default_factory=list,
        description="Avertissements (données manquantes, estimations, etc.)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "location": "Normandie",
                "forecast_period_days": 7,
                "crop_type": "blé",
                "crop_stage": "floraison",
                "daily_et": [
                    {
                        "date": "2025-09-30",
                        "et0": 4.2,
                        "etc": 5.5,
                        "kc": 1.3,
                        "temperature_avg": 18.5,
                        "humidity_avg": 65.0,
                        "wind_speed_avg": 12.0
                    }
                ],
                "water_balance": {
                    "total_et0": 29.4,
                    "total_etc": 38.5,
                    "total_precipitation": 15.0,
                    "water_deficit": 23.5,
                    "water_surplus": 0.0,
                    "irrigation_needed": True,
                    "irrigation_amount": 25.0
                },
                "irrigation_recommendations": [
                    {
                        "date": "2025-10-02",
                        "amount_mm": 25.0,
                        "amount_m3_ha": 250.0,
                        "priority": "haute",
                        "reason": "Déficit hydrique important pendant la floraison",
                        "optimal_time": "matin",
                        "method_recommendation": "aspersion"
                    }
                ],
                "avg_et0": 4.2,
                "avg_etc": 5.5,
                "peak_et_date": "2025-10-03",
                "peak_et_value": 6.8,
                "calculation_method": "Penman-Monteith FAO-56",
                "data_source": "weather_analysis",
                "calculated_at": "2025-09-30T10:00:00Z",
                "success": True,
                "warnings": []
            }
        }


# Crop coefficients (Kc) by crop type and development stage
# Based on FAO-56 Irrigation and Drainage Paper No. 56
#
# Simple 4-stage model (FAO-56 standard):
# - semis: Initial stage (planting to ~10% ground cover) → BBCH 0-29
# - croissance: Development stage (~10% to ~70-80% ground cover) → BBCH 30-59
# - floraison: Mid-season (flowering, peak water demand) → BBCH 60-69
# - maturation: Late season (grain fill to harvest) → BBCH 70-99
CROP_COEFFICIENTS = {
    "blé": {
        "semis": 0.3,
        "croissance": 0.7,
        "floraison": 1.15,
        "maturation": 0.4,
        "default": 0.8
    },
    "maïs": {
        "semis": 0.3,
        "croissance": 0.7,
        "floraison": 1.2,
        "maturation": 0.6,
        "default": 0.85
    },
    "colza": {
        "semis": 0.35,
        "croissance": 0.8,
        "floraison": 1.1,
        "maturation": 0.5,
        "default": 0.8
    },
    "orge": {
        "semis": 0.3,
        "croissance": 0.7,
        "floraison": 1.15,
        "maturation": 0.4,
        "default": 0.75
    },
    "tournesol": {
        "semis": 0.35,
        "croissance": 0.7,
        "floraison": 1.15,
        "maturation": 0.5,
        "default": 0.8
    },
    "betterave": {
        "semis": 0.35,
        "croissance": 0.75,
        "floraison": 1.2,
        "maturation": 0.9,
        "default": 0.9
    },
    "pomme de terre": {
        "semis": 0.5,
        "croissance": 0.75,
        "floraison": 1.15,
        "maturation": 0.75,
        "default": 0.85
    },
    "vigne": {
        "semis": 0.3,
        "croissance": 0.7,
        "floraison": 0.85,
        "maturation": 0.45,
        "default": 0.7
    },
    "prairie": {
        "default": 0.85
    },
    "general": {
        "default": 0.8
    }
}

