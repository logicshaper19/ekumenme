"""
Identify Intervention Windows Tool - Vector Database Ready Tool

Job: Identify optimal intervention windows from weather data.
Input: JSON string of weather data from GetWeatherDataTool
Output: JSON string with intervention windows

Enhanced Features:
- External knowledge base (JSON file)
- Configurable analysis parameters
- Asynchronous support
- Comprehensive input validation
- Vector database ready architecture

No prompting logic, no orchestration, no agent responsibilities.
"""

from typing import Dict, List, Any, Optional
from langchain.tools import BaseTool
import logging
import json
import asyncio
from datetime import datetime
from dataclasses import dataclass, asdict
from pathlib import Path

# Import configuration system
from ...config.intervention_windows_config import get_intervention_windows_config

logger = logging.getLogger(__name__)

@dataclass
class WeatherCondition:
    """Structured weather condition."""
    date: str
    temperature_min: float
    temperature_max: float
    humidity: float
    wind_speed: float
    wind_direction: str
    precipitation: float
    cloud_cover: float
    uv_index: float

@dataclass
class InterventionWindow:
    """Structured intervention window."""
    date: str
    intervention_type: str
    conditions: str
    duration_hours: float
    confidence: float

@dataclass
class ValidationError:
    """Validation error information."""
    field: str
    message: str
    severity: str

class IdentifyInterventionWindowsTool(BaseTool):
    """
    Vector Database Ready Tool: Identify optimal intervention windows from weather data.
    
    Job: Take weather data and identify optimal intervention windows.
    Input: JSON string of weather data from GetWeatherDataTool
    Output: JSON string with intervention windows
    
    Enhanced Features:
    - External knowledge base (JSON file)
    - Configurable analysis parameters
    - Asynchronous support
    - Comprehensive input validation
    - Vector database ready architecture
    """
    
    name: str = "identify_intervention_windows_tool"
    description: str = "Identifie les fenêtres d'intervention optimales avec analyse avancée"
    
    def __init__(
        self, 
        knowledge_base_path: Optional[str] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.knowledge_base_path = knowledge_base_path or self._get_default_knowledge_path()
        self._config_cache = None
    
    def _get_default_knowledge_path(self) -> str:
        """Get default knowledge base file path."""
        current_dir = Path(__file__).parent
        return str(current_dir.parent.parent / "data" / "intervention_windows_knowledge.json")
    
    def _get_config(self):
        """Get current configuration."""
        if self._config_cache is None:
            self._config_cache = get_intervention_windows_config()
        return self._config_cache
    
    def _load_knowledge_base(self) -> Dict[str, Any]:
        """Load knowledge base from JSON file."""
        try:
            with open(self.knowledge_base_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading intervention windows knowledge base: {e}")
            return {}
    
    def _validate_inputs(
        self, 
        weather_data_json: str, 
        intervention_type: str,
        crop_type: Optional[str] = None
    ) -> List[ValidationError]:
        """Validate input parameters."""
        errors = []
        config = self._get_config()
        
        # Validate weather data
        if config.require_weather_data:
            try:
                data = json.loads(weather_data_json)
                if "error" in data:
                    errors.append(ValidationError("weather_data", "Weather data contains errors", "error"))
                elif not data.get("weather_conditions"):
                    errors.append(ValidationError("weather_data", "No weather conditions provided", "error"))
            except json.JSONDecodeError:
                errors.append(ValidationError("weather_data", "Invalid JSON format", "error"))
        
        # Validate intervention type
        if config.validate_intervention_type:
            knowledge_base = self._load_knowledge_base()
            intervention_conditions = knowledge_base.get("intervention_conditions", {})
            if intervention_type.lower() not in intervention_conditions:
                errors.append(ValidationError("intervention_type", f"Unknown intervention type: {intervention_type}", "error"))
        
        return errors
    
    def _identify_intervention_windows(
        self, 
        conditions: List[WeatherCondition], 
        intervention_type: str,
        crop_type: Optional[str],
        knowledge_base: Dict[str, Any]
    ) -> List[InterventionWindow]:
        """Identify optimal intervention windows from weather conditions."""
        windows = []
        intervention_conditions = knowledge_base.get("intervention_conditions", {})
        crop_timing = knowledge_base.get("crop_specific_timing", {})
        
        if intervention_type.lower() not in intervention_conditions:
            return windows
        
        conditions_config = intervention_conditions[intervention_type.lower()]
        
        for condition in conditions:
            # Check if conditions are suitable
            is_suitable, confidence = self._evaluate_conditions(condition, conditions_config)
            
            if is_suitable and confidence >= self._get_config().default_confidence_threshold:
                window = InterventionWindow(
                    date=condition.date,
                    intervention_type=intervention_type,
                    conditions=self._describe_conditions(condition),
                    duration_hours=conditions_config.get("min_duration_hours", 4.0),
                    confidence=confidence
                )
                windows.append(window)
        
        return windows
    
    def _evaluate_conditions(self, condition: WeatherCondition, conditions_config: Dict[str, Any]) -> tuple[bool, float]:
        """Evaluate if weather conditions are suitable for intervention."""
        confidence = 1.0
        
        # Check temperature
        temp_config = conditions_config.get("optimal_temperature", {})
        temp_min = temp_config.get("min", 5.0)
        temp_max = temp_config.get("max", 30.0)
        
        if condition.temperature_min < temp_min or condition.temperature_max > temp_max:
            confidence *= 0.5
        
        # Check humidity
        humidity_config = conditions_config.get("optimal_humidity", {})
        humidity_min = humidity_config.get("min", 30.0)
        humidity_max = humidity_config.get("max", 80.0)
        
        if condition.humidity < humidity_min or condition.humidity > humidity_max:
            confidence *= 0.7
        
        # Check wind speed
        max_wind = conditions_config.get("max_wind_speed", 20.0)
        if condition.wind_speed > max_wind:
            confidence *= 0.3
        
        # Check precipitation
        precip_tolerance = conditions_config.get("precipitation_tolerance", 0.0)
        if condition.precipitation > precip_tolerance:
            confidence *= 0.2
        
        is_suitable = confidence >= 0.5
        return is_suitable, confidence
    
    def _describe_conditions(self, condition: WeatherCondition) -> str:
        """Describe weather conditions in a readable format."""
        return f"Temp: {condition.temperature_min}-{condition.temperature_max}°C, " \
               f"Humidité: {condition.humidity}%, " \
               f"Vent: {condition.wind_speed} km/h, " \
               f"Pluie: {condition.precipitation} mm"
    
    def _run(
        self, 
        weather_data_json: str,
        intervention_type: str,
        crop_type: str = None,
        **kwargs
    ) -> str:
        """
        Identify optimal intervention windows from weather data.
        
        Args:
            weather_data_json: JSON string from GetWeatherDataTool
            intervention_type: Type of intervention (spraying, fertilization, etc.)
            crop_type: Type of crop for crop-specific timing
        """
        try:
            # Validate inputs
            validation_errors = self._validate_inputs(weather_data_json, intervention_type, crop_type)
            config = self._get_config()
            
            if validation_errors and config.strict_validation:
                error_messages = [f"{error.field}: {error.message}" for error in validation_errors if error.severity == "error"]
                if error_messages:
                    return json.dumps({
                        "error": "Validation errors",
                        "validation_errors": error_messages
                    })
            
            # Load knowledge base
            knowledge_base = self._load_knowledge_base()
            
            # Parse weather data
            data = json.loads(weather_data_json)
            
            if "error" in data:
                return weather_data_json  # Pass through errors
            
            weather_conditions = data.get("weather_conditions", [])
            if not weather_conditions:
                return json.dumps({"error": "Aucune donnée météo fournie pour l'analyse des fenêtres"})
            
            # Convert to WeatherCondition objects
            conditions = [WeatherCondition(**condition_dict) for condition_dict in weather_conditions]
            
            # Identify intervention windows
            windows = self._identify_intervention_windows(conditions, intervention_type, crop_type, knowledge_base)
            
            result = {
                "location": data.get("location", ""),
                "forecast_period_days": data.get("forecast_period_days", 0),
                "intervention_type": intervention_type,
                "crop_type": crop_type,
                "intervention_windows": [asdict(window) for window in windows],
                "total_windows": len(windows),
                "analysis_metadata": {
                    "config_used": asdict(config),
                    "knowledge_base_version": knowledge_base.get("metadata", {}).get("version", "unknown")
                }
            }
            
            # Add validation warnings if any
            if validation_errors and config.return_validation_errors:
                warnings = [{"field": error.field, "message": error.message, "severity": error.severity} 
                           for error in validation_errors if error.severity in ["warning", "info"]]
                if warnings:
                    result["validation_warnings"] = warnings
            
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"Identify intervention windows error: {e}")
            return json.dumps({
                "error": f"Erreur lors de l'identification des fenêtres d'intervention: {str(e)}",
                "error_type": type(e).__name__
            })
    
    async def _arun(
        self, 
        weather_data_json: str,
        intervention_type: str,
        crop_type: str = None,
        **kwargs
    ) -> str:
        """
        Asynchronous version of intervention window identification.
        """
        # For now, just call the sync version
        return self._run(weather_data_json, intervention_type, crop_type, **kwargs)
    
    def clear_cache(self):
        """Clear internal caches."""
        self._config_cache = None
        logger.info("Cleared tool caches")
