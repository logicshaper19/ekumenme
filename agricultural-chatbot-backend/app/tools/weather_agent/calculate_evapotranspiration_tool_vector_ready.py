"""
Calculate Evapotranspiration Tool - Vector Database Ready Tool

Job: Calculate evapotranspiration and water needs from weather data.
Input: JSON string of weather data from GetWeatherDataTool
Output: JSON string with evapotranspiration analysis

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
import math

# Import configuration system
from ...config.evapotranspiration_config import get_evapotranspiration_config

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
class EvapotranspirationResult:
    """Structured evapotranspiration result."""
    date: str
    reference_et: float
    crop_et: float
    water_deficit: float
    irrigation_need: float

@dataclass
class ValidationError:
    """Validation error information."""
    field: str
    message: str
    severity: str

class CalculateEvapotranspirationTool(BaseTool):
    """
    Vector Database Ready Tool: Calculate evapotranspiration and water needs from weather data.
    
    Job: Take weather data and calculate evapotranspiration for crops.
    Input: JSON string of weather data from GetWeatherDataTool
    Output: JSON string with evapotranspiration analysis
    
    Enhanced Features:
    - External knowledge base (JSON file)
    - Configurable analysis parameters
    - Asynchronous support
    - Comprehensive input validation
    - Vector database ready architecture
    """
    
    name: str = "calculate_evapotranspiration_tool"
    description: str = "Calcule l'évapotranspiration et les besoins en eau avec analyse avancée"
    
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
        return str(current_dir.parent.parent / "data" / "evapotranspiration_knowledge.json")
    
    def _get_config(self):
        """Get current configuration."""
        if self._config_cache is None:
            self._config_cache = get_evapotranspiration_config()
        return self._config_cache
    
    def _load_knowledge_base(self) -> Dict[str, Any]:
        """Load knowledge base from JSON file."""
        try:
            with open(self.knowledge_base_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading evapotranspiration knowledge base: {e}")
            return {}
    
    def _validate_inputs(
        self, 
        weather_data_json: str, 
        crop_type: str,
        soil_type: str = "loam"
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
        
        # Validate crop type
        if config.validate_crop_type:
            knowledge_base = self._load_knowledge_base()
            crop_coefficients = knowledge_base.get("crop_coefficients", {})
            if crop_type.lower() not in crop_coefficients:
                errors.append(ValidationError("crop_type", f"Unknown crop type: {crop_type}", "error"))
        
        # Validate soil type
        if config.validate_soil_type:
            knowledge_base = self._load_knowledge_base()
            soil_characteristics = knowledge_base.get("soil_characteristics", {})
            if soil_type.lower() not in soil_characteristics:
                errors.append(ValidationError("soil_type", f"Unknown soil type: {soil_type}", "error"))
        
        return errors
    
    def _calculate_reference_et(
        self, 
        condition: WeatherCondition, 
        knowledge_base: Dict[str, Any]
    ) -> float:
        """Calculate reference evapotranspiration using Penman-Monteith method."""
        calc_params = knowledge_base.get("calculation_parameters", {}).get("penman_monteith", {})
        
        # Calculate mean temperature
        temp_mean = (condition.temperature_min + condition.temperature_max) / 2
        
        # Calculate saturation vapor pressure
        es = 0.6108 * math.exp(17.27 * temp_mean / (temp_mean + 237.3))
        
        # Calculate actual vapor pressure
        ea = es * condition.humidity / 100
        
        # Calculate vapor pressure deficit
        vpd = es - ea
        
        # Calculate slope of saturation vapor pressure curve
        delta = 4098 * es / ((temp_mean + 237.3) ** 2)
        
        # Calculate psychrometric constant
        gamma = calc_params.get("psychrometric_constant", 0.0665)
        
        # Calculate net radiation (simplified)
        rn = calc_params.get("solar_constant", 1367.0) * (1 - calc_params.get("albedo", 0.23)) * (1 - condition.cloud_cover / 100)
        
        # Calculate soil heat flux (simplified)
        g = 0.1 * rn
        
        # Calculate reference ET
        et0 = (0.408 * delta * (rn - g) + gamma * 900 / (temp_mean + 273) * condition.wind_speed * vpd) / (delta + gamma * (1 + 0.34 * condition.wind_speed))
        
        return max(0, et0)
    
    def _get_crop_coefficient(self, crop_type: str, growth_stage: str, knowledge_base: Dict[str, Any]) -> float:
        """Get crop coefficient for specific growth stage."""
        crop_coefficients = knowledge_base.get("crop_coefficients", {})
        crop_data = crop_coefficients.get(crop_type.lower(), {})
        
        stage_mapping = {
            "initial": "initial_stage",
            "development": "development_stage", 
            "mid": "mid_stage",
            "late": "late_stage"
        }
        
        stage_key = stage_mapping.get(growth_stage.lower(), "mid_stage")
        return crop_data.get(stage_key, 1.0)
    
    def _calculate_evapotranspiration(
        self, 
        conditions: List[WeatherCondition], 
        crop_type: str,
        soil_type: str,
        growth_stage: str,
        knowledge_base: Dict[str, Any]
    ) -> List[EvapotranspirationResult]:
        """Calculate evapotranspiration for all weather conditions."""
        results = []
        soil_characteristics = knowledge_base.get("soil_characteristics", {}).get(soil_type.lower(), {})
        irrigation_recommendations = knowledge_base.get("irrigation_recommendations", {})
        
        for condition in conditions:
            # Calculate reference ET
            reference_et = self._calculate_reference_et(condition, knowledge_base)
            
            # Get crop coefficient
            crop_coefficient = self._get_crop_coefficient(crop_type, growth_stage, knowledge_base)
            
            # Calculate crop ET
            crop_et = reference_et * crop_coefficient
            
            # Calculate water deficit (simplified)
            water_holding_capacity = soil_characteristics.get("water_holding_capacity", 0.3)
            water_deficit = max(0, crop_et - condition.precipitation)
            
            # Calculate irrigation need
            irrigation_need = water_deficit * 10  # Convert to mm
            
            result = EvapotranspirationResult(
                date=condition.date,
                reference_et=round(reference_et, 2),
                crop_et=round(crop_et, 2),
                water_deficit=round(water_deficit, 2),
                irrigation_need=round(irrigation_need, 2)
            )
            results.append(result)
        
        return results
    
    def _run(
        self, 
        weather_data_json: str,
        crop_type: str,
        soil_type: str = "loam",
        growth_stage: str = "mid",
        **kwargs
    ) -> str:
        """
        Calculate evapotranspiration and water needs from weather data.
        
        Args:
            weather_data_json: JSON string from GetWeatherDataTool
            crop_type: Type of crop for crop-specific calculations
            soil_type: Type of soil (clay, loam, sandy)
            growth_stage: Growth stage of the crop (initial, development, mid, late)
        """
        try:
            # Validate inputs
            validation_errors = self._validate_inputs(weather_data_json, crop_type, soil_type)
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
                return json.dumps({"error": "Aucune donnée météo fournie pour le calcul d'évapotranspiration"})
            
            # Convert to WeatherCondition objects
            conditions = [WeatherCondition(**condition_dict) for condition_dict in weather_conditions]
            
            # Calculate evapotranspiration
            et_results = self._calculate_evapotranspiration(conditions, crop_type, soil_type, growth_stage, knowledge_base)
            
            # Calculate summary statistics
            total_et = sum(result.crop_et for result in et_results)
            total_irrigation = sum(result.irrigation_need for result in et_results)
            avg_et = total_et / len(et_results) if et_results else 0
            
            result = {
                "location": data.get("location", ""),
                "forecast_period_days": data.get("forecast_period_days", 0),
                "crop_type": crop_type,
                "soil_type": soil_type,
                "growth_stage": growth_stage,
                "evapotranspiration_results": [asdict(result) for result in et_results],
                "summary": {
                    "total_crop_et": round(total_et, 2),
                    "average_daily_et": round(avg_et, 2),
                    "total_irrigation_need": round(total_irrigation, 2),
                    "average_daily_irrigation": round(total_irrigation / len(et_results), 2) if et_results else 0
                },
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
            logger.error(f"Calculate evapotranspiration error: {e}")
            return json.dumps({
                "error": f"Erreur lors du calcul d'évapotranspiration: {str(e)}",
                "error_type": type(e).__name__
            })
    
    async def _arun(
        self, 
        weather_data_json: str,
        crop_type: str,
        soil_type: str = "loam",
        growth_stage: str = "mid",
        **kwargs
    ) -> str:
        """
        Asynchronous version of evapotranspiration calculation.
        """
        # For now, just call the sync version
        return self._run(weather_data_json, crop_type, soil_type, growth_stage, **kwargs)
    
    def clear_cache(self):
        """Clear internal caches."""
        self._config_cache = None
        logger.info("Cleared tool caches")
