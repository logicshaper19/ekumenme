"""
Enhanced Identify Intervention Windows Tool - With Caching and Type Safety

Enhancements:
- Pydantic schemas for type safety
- Redis + memory caching
- Structured error handling
- Async support
- Category-specific cache
"""

from typing import List, Dict, Any, Optional
from langchain.tools import StructuredTool
import logging
import json
from datetime import datetime
from pydantic import ValidationError

from app.tools.schemas.intervention_schemas import (
    InterventionWindowsInput,
    InterventionWindowsOutput,
    InterventionWindowDetail,
    WindowStatistics,
    DEFAULT_INTERVENTION_TYPES,
    INTERVENTION_CRITERIA
)
from app.tools.exceptions import (
    WeatherValidationError,
    WeatherDataError
)
from app.core.cache import redis_cache

logger = logging.getLogger(__name__)


class EnhancedInterventionWindowsService:
    """Service for identifying optimal intervention windows with caching"""
    
    @redis_cache(
        ttl=3600,  # 1 hour cache (intervention windows are derived data)
        model_class=InterventionWindowsOutput,
        category="weather"
    )
    async def identify_windows(
        self,
        weather_data_json: str,
        intervention_types: Optional[List[str]] = None
    ) -> InterventionWindowsOutput:
        """
        Identify optimal intervention windows from weather data
        
        Uses 1-hour cache since intervention windows are derived from weather data
        and don't change as frequently as raw weather data.
        
        Args:
            weather_data_json: JSON string from weather tool
            intervention_types: Optional list of intervention types to analyze
            
        Returns:
            InterventionWindowsOutput with identified windows and recommendations
            
        Raises:
            WeatherValidationError: If input data is invalid
            WeatherDataError: If weather data is missing or malformed
        """
        try:
            # Parse weather data
            data = json.loads(weather_data_json)
            
            # Check for errors in weather data
            if "error" in data:
                raise WeatherDataError(f"Weather data contains error: {data['error']}")
            
            # Extract weather conditions
            weather_conditions = data.get("weather_conditions", [])
            if not weather_conditions:
                raise WeatherDataError("Aucune donnée météo fournie pour l'analyse des fenêtres")
            
            # Use default intervention types if not specified
            if not intervention_types:
                intervention_types = DEFAULT_INTERVENTION_TYPES
            
            # Identify intervention windows
            windows = self._identify_intervention_windows(weather_conditions, intervention_types)
            
            # Calculate window statistics
            window_stats = self._calculate_window_statistics(windows)
            
            # Generate window insights
            window_insights = self._generate_window_insights(windows)
            
            # Build output
            result = InterventionWindowsOutput(
                location=data.get("location", ""),
                forecast_period_days=data.get("forecast_period_days", len(weather_conditions)),
                intervention_types=intervention_types,
                windows=windows,
                window_statistics=window_stats,
                window_insights=window_insights,
                total_windows=len(windows),
                data_source="intervention_analysis",
                analyzed_at=datetime.utcnow().isoformat() + "Z",
                success=True
            )
            
            return result
            
        except json.JSONDecodeError as e:
            raise WeatherValidationError(f"Invalid JSON in weather_data_json: {str(e)}")
        except KeyError as e:
            raise WeatherDataError(f"Missing required field in weather data: {str(e)}")
    
    def _identify_intervention_windows(
        self,
        weather_conditions: List[Dict[str, Any]],
        intervention_types: List[str]
    ) -> List[InterventionWindowDetail]:
        """Identify optimal windows for agricultural interventions"""
        windows = []
        
        for condition in weather_conditions:
            date = condition.get("date", "")
            temp_min = condition.get("temperature_min", 0)
            temp_max = condition.get("temperature_max", 0)
            humidity = condition.get("humidity", 0)
            wind_speed = condition.get("wind_speed", 0)
            precipitation = condition.get("precipitation", 0)
            
            # Check each intervention type
            for intervention_type in intervention_types:
                if intervention_type not in INTERVENTION_CRITERIA:
                    continue
                
                criteria = INTERVENTION_CRITERIA[intervention_type]
                is_suitable, quality, constraints = self._check_suitability(
                    condition, criteria, intervention_type
                )
                
                if is_suitable:
                    # Create weather summary
                    weather_summary = self._create_weather_summary(condition)
                    
                    windows.append(InterventionWindowDetail(
                        date=date,
                        intervention_type=intervention_type,
                        conditions=quality,
                        duration_hours=criteria["optimal_duration"],
                        confidence=criteria["confidence"],
                        weather_summary=weather_summary,
                        constraints=constraints
                    ))
        
        return windows
    
    def _check_suitability(
        self,
        condition: Dict[str, Any],
        criteria: Dict[str, Any],
        intervention_type: str
    ) -> tuple[bool, str, List[str]]:
        """
        Check if conditions are suitable for intervention
        
        Returns:
            (is_suitable, quality_level, constraints)
        """
        temp_min = condition.get("temperature_min", 0)
        humidity = condition.get("humidity", 0)
        wind_speed = condition.get("wind_speed", 0)
        precipitation = condition.get("precipitation", 0)
        
        constraints = []
        violations = 0
        
        # Check each criterion
        if "max_wind_speed" in criteria and wind_speed > criteria["max_wind_speed"]:
            if wind_speed > criteria["max_wind_speed"] * 1.5:
                return False, "médiocres", []  # Too windy
            violations += 1
            constraints.append(f"Vent modéré ({wind_speed:.0f} km/h)")
        
        if "max_precipitation" in criteria and precipitation > criteria["max_precipitation"]:
            if precipitation > criteria["max_precipitation"] * 2:
                return False, "médiocres", []  # Too much rain
            violations += 1
            constraints.append(f"Précipitations ({precipitation:.0f} mm)")
        
        if "min_temperature" in criteria and temp_min < criteria["min_temperature"]:
            if temp_min < criteria["min_temperature"] - 3:
                return False, "médiocres", []  # Too cold
            violations += 1
            constraints.append(f"Température fraîche ({temp_min:.0f}°C)")
        
        if "max_humidity" in criteria and humidity > criteria["max_humidity"]:
            violations += 1
            constraints.append(f"Humidité élevée ({humidity:.0f}%)")
        
        if "min_humidity" in criteria and humidity < criteria["min_humidity"]:
            violations += 1
            constraints.append(f"Humidité faible ({humidity:.0f}%)")
        
        # Determine quality based on violations
        if violations == 0:
            quality = "excellentes" if intervention_type == "récolte" else "optimales"
        elif violations == 1:
            quality = "bonnes"
        else:
            quality = "acceptables"
        
        return True, quality, constraints
    
    def _create_weather_summary(self, condition: Dict[str, Any]) -> str:
        """Create a brief weather summary"""
        temp_min = condition.get("temperature_min", 0)
        temp_max = condition.get("temperature_max", 0)
        wind_speed = condition.get("wind_speed", 0)
        precipitation = condition.get("precipitation", 0)
        
        summary_parts = []
        
        # Temperature
        summary_parts.append(f"{temp_min:.0f}-{temp_max:.0f}°C")
        
        # Wind
        if wind_speed < 5:
            summary_parts.append("vent calme")
        elif wind_speed < 15:
            summary_parts.append(f"vent modéré ({wind_speed:.0f} km/h)")
        else:
            summary_parts.append(f"vent fort ({wind_speed:.0f} km/h)")
        
        # Precipitation
        if precipitation < 1:
            summary_parts.append("sec")
        elif precipitation < 5:
            summary_parts.append(f"pluie légère ({precipitation:.0f} mm)")
        else:
            summary_parts.append(f"pluie ({precipitation:.0f} mm)")
        
        return ", ".join(summary_parts)
    
    def _calculate_window_statistics(
        self,
        windows: List[InterventionWindowDetail]
    ) -> WindowStatistics:
        """Calculate window statistics"""
        if not windows:
            return WindowStatistics(
                total_windows=0,
                windows_by_type={},
                average_confidence=0.0,
                best_window_date=None,
                best_window_type=None
            )
        
        # Count by type
        windows_by_type = {}
        total_confidence = 0
        
        for window in windows:
            if window.intervention_type not in windows_by_type:
                windows_by_type[window.intervention_type] = 0
            windows_by_type[window.intervention_type] += 1
            total_confidence += window.confidence
        
        # Find best window
        best_window = max(windows, key=lambda w: w.confidence)
        
        return WindowStatistics(
            total_windows=len(windows),
            windows_by_type=windows_by_type,
            average_confidence=round(total_confidence / len(windows), 2),
            best_window_date=best_window.date,
            best_window_type=best_window.intervention_type
        )
    
    def _generate_window_insights(
        self,
        windows: List[InterventionWindowDetail]
    ) -> List[str]:
        """Generate human-readable window insights"""
        insights = []
        
        if not windows:
            insights.append("❌ Aucune fenêtre d'intervention optimale identifiée")
            return insights
        
        # Group windows by type
        windows_by_type = {}
        for window in windows:
            if window.intervention_type not in windows_by_type:
                windows_by_type[window.intervention_type] = []
            windows_by_type[window.intervention_type].append(window)
        
        # Generate insights for each type
        for intervention_type, type_windows in windows_by_type.items():
            best_window = max(type_windows, key=lambda w: w.confidence)
            emoji = self._get_intervention_emoji(intervention_type)
            insights.append(
                f"{emoji} Meilleure fenêtre pour {intervention_type}: "
                f"{best_window.date} (confiance: {best_window.confidence:.0%})"
            )
        
        # Overall summary
        total_windows = len(windows)
        insights.append(f"✅ {total_windows} fenêtre(s) d'intervention identifiée(s)")
        
        return insights
    
    def _get_intervention_emoji(self, intervention_type: str) -> str:
        """Get emoji for intervention type"""
        emoji_map = {
            "pulvérisation": "💧",
            "travaux_champ": "🚜",
            "semis": "🌱",
            "récolte": "🌾",
            "fertilisation": "🧪",
            "irrigation": "💦"
        }
        return emoji_map.get(intervention_type, "📅")


# Global service instance
intervention_windows_service = EnhancedInterventionWindowsService()


async def identify_intervention_windows_enhanced(
    weather_data_json: str,
    intervention_types: Optional[List[str]] = None
) -> str:
    """
    Identify optimal intervention windows from weather data
    
    Args:
        weather_data_json: JSON string from weather tool containing forecast data
        intervention_types: Optional list of intervention types to analyze
        
    Returns:
        JSON string with intervention windows, statistics, and recommendations
    """
    try:
        # Validate input
        input_data = InterventionWindowsInput(
            weather_data_json=weather_data_json,
            intervention_types=intervention_types
        )
        
        # Identify windows
        result = await intervention_windows_service.identify_windows(
            weather_data_json=input_data.weather_data_json,
            intervention_types=input_data.intervention_types
        )
        
        # Return as JSON
        return result.model_dump_json(indent=2, exclude_none=True)
        
    except ValidationError as e:
        logger.error(f"Intervention windows Pydantic validation error: {e}")
        error_result = InterventionWindowsOutput(
            location="",
            forecast_period_days=0,
            intervention_types=[],
            windows=[],
            window_statistics=WindowStatistics(
                total_windows=0,
                windows_by_type={},
                average_confidence=0.0
            ),
            window_insights=[],
            total_windows=0,
            data_source="error",
            analyzed_at=datetime.utcnow().isoformat() + "Z",
            success=False,
            error=f"Paramètres invalides: {str(e)}",
            error_type="validation"
        )
        return error_result.model_dump_json(indent=2)
        
    except WeatherValidationError as e:
        logger.error(f"Intervention windows validation error: {e}")
        error_result = InterventionWindowsOutput(
            location="",
            forecast_period_days=0,
            intervention_types=[],
            windows=[],
            window_statistics=WindowStatistics(
                total_windows=0,
                windows_by_type={},
                average_confidence=0.0
            ),
            window_insights=[],
            total_windows=0,
            data_source="error",
            analyzed_at=datetime.utcnow().isoformat() + "Z",
            success=False,
            error=str(e),
            error_type="validation"
        )
        return error_result.model_dump_json(indent=2)

    except WeatherDataError as e:
        logger.error(f"Intervention windows data error: {e}")
        error_result = InterventionWindowsOutput(
            location="",
            forecast_period_days=0,
            intervention_types=[],
            windows=[],
            window_statistics=WindowStatistics(
                total_windows=0,
                windows_by_type={},
                average_confidence=0.0
            ),
            window_insights=[],
            total_windows=0,
            data_source="error",
            analyzed_at=datetime.utcnow().isoformat() + "Z",
            success=False,
            error=str(e),
            error_type="data_missing"
        )
        return error_result.model_dump_json(indent=2)

    except Exception as e:
        logger.error(f"Unexpected intervention windows error: {e}", exc_info=True)
        error_result = InterventionWindowsOutput(
            location="",
            forecast_period_days=0,
            intervention_types=[],
            windows=[],
            window_statistics=WindowStatistics(
                total_windows=0,
                windows_by_type={},
                average_confidence=0.0
            ),
            window_insights=[],
            total_windows=0,
            data_source="error",
            analyzed_at=datetime.utcnow().isoformat() + "Z",
            success=False,
            error="Erreur inattendue lors de l'identification des fenêtres. Veuillez réessayer.",
            error_type="unknown"
        )
        return error_result.model_dump_json(indent=2)


# Create the enhanced tool
identify_intervention_windows_tool = StructuredTool.from_function(
    func=identify_intervention_windows_enhanced,
    name="identify_intervention_windows",
    description="""Identifie les fenêtres optimales pour les interventions agricoles à partir des données météo.

    Analyse les conditions météo pour identifier les moments optimaux pour:
    - Pulvérisation (vent faible, pas de pluie)
    - Travaux au champ (sol sec, températures favorables)
    - Semis (températures adéquates, humidité suffisante)
    - Récolte (conditions sèches, vent modéré)
    - Fertilisation, irrigation, etc.

    Entrée: JSON de données météo + types d'interventions (optionnel)
    Sortie: Fenêtres d'intervention avec confiance et recommandations""",
    args_schema=InterventionWindowsInput,
    return_direct=False,
    coroutine=identify_intervention_windows_enhanced,
    handle_validation_error=False  # We handle errors ourselves
)

