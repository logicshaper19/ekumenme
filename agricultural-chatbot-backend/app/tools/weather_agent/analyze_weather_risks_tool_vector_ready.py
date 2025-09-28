"""
Analyze Weather Risks Tool - Vector Database Ready Tool

Job: Analyze agricultural weather risks from weather data.
Input: JSON string of weather data from GetWeatherDataTool
Output: JSON string with risk analysis

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
from ...config.weather_risks_config import get_weather_risks_config

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
class WeatherRisk:
    """Structured weather risk."""
    risk_type: str
    severity: str
    probability: float
    impact: str
    recommendations: List[str]

@dataclass
class ValidationError:
    """Validation error information."""
    field: str
    message: str
    severity: str

class AnalyzeWeatherRisksTool(BaseTool):
    """
    Vector Database Ready Tool: Analyze agricultural weather risks from weather data.
    
    Job: Take weather data and analyze agricultural risks.
    Input: JSON string of weather data from GetWeatherDataTool
    Output: JSON string with risk analysis
    
    Enhanced Features:
    - External knowledge base (JSON file)
    - Configurable analysis parameters
    - Asynchronous support
    - Comprehensive input validation
    - Vector database ready architecture
    """
    
    name: str = "analyze_weather_risks_tool"
    description: str = "Analyse les risques météorologiques agricoles avec analyse avancée"
    
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
        return str(current_dir.parent.parent / "data" / "weather_risks_knowledge.json")
    
    def _get_config(self):
        """Get current configuration."""
        if self._config_cache is None:
            self._config_cache = get_weather_risks_config()
        return self._config_cache
    
    def _load_knowledge_base(self) -> Dict[str, Any]:
        """Load knowledge base from JSON file."""
        try:
            with open(self.knowledge_base_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading weather risks knowledge base: {e}")
            return {}
    
    def _validate_inputs(
        self, 
        weather_data_json: str, 
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
        
        # Validate crop type if provided
        if crop_type and config.validate_crop_type:
            knowledge_base = self._load_knowledge_base()
            crop_risks = knowledge_base.get("crop_specific_risks", {})
            if crop_type.lower() not in crop_risks:
                errors.append(ValidationError("crop_type", f"Unknown crop type: {crop_type}", "warning"))
        
        return errors
    
    def _analyze_agricultural_risks(
        self, 
        conditions: List[WeatherCondition], 
        crop_type: Optional[str], 
        knowledge_base: Dict[str, Any]
    ) -> List[WeatherRisk]:
        """Analyze agricultural risks from weather conditions."""
        risks = []
        risk_thresholds = knowledge_base.get("risk_thresholds", {})
        crop_risks = knowledge_base.get("crop_specific_risks", {})
        recommendations = knowledge_base.get("risk_recommendations", {})
        
        for condition in conditions:
            # Temperature risks
            temp_risks = risk_thresholds.get("temperature", {})
            if condition.temperature_min <= temp_risks.get("frost_risk", {}).get("min_temp", -2.0):
                risks.append(WeatherRisk(
                    risk_type="frost_risk",
                    severity="high",
                    probability=0.9,
                    impact="Dommages aux cultures sensibles",
                    recommendations=recommendations.get("frost_risk", [])
                ))
            
            if condition.temperature_max >= temp_risks.get("heat_stress", {}).get("max_temp", 35.0):
                risks.append(WeatherRisk(
                    risk_type="heat_stress",
                    severity="medium",
                    probability=0.7,
                    impact="Stress thermique des cultures",
                    recommendations=recommendations.get("heat_stress", [])
                ))
            
            # Wind risks
            wind_risks = risk_thresholds.get("wind", {})
            if condition.wind_speed >= wind_risks.get("strong_wind", {}).get("speed_kmh", 30.0):
                risks.append(WeatherRisk(
                    risk_type="strong_wind",
                    severity="medium",
                    probability=0.6,
                    impact="Difficultés d'intervention",
                    recommendations=recommendations.get("strong_wind", [])
                ))
            
            # Precipitation risks
            precip_risks = risk_thresholds.get("precipitation", {})
            if condition.precipitation >= precip_risks.get("heavy_rain", {}).get("mm_per_hour", 10.0):
                risks.append(WeatherRisk(
                    risk_type="heavy_rain",
                    severity="medium",
                    probability=0.8,
                    impact="Sol détrempé, érosion possible",
                    recommendations=recommendations.get("heavy_rain", [])
                ))
        
        return risks
    
    def _calculate_risk_summary(self, risks: List[WeatherRisk]) -> Dict[str, Any]:
        """Calculate risk summary statistics."""
        if not risks:
            return {"total_risks": 0, "high_severity": 0, "medium_severity": 0, "low_severity": 0}
        
        severity_counts = {"high": 0, "medium": 0, "low": 0}
        for risk in risks:
            severity_counts[risk.severity] += 1
        
        return {
            "total_risks": len(risks),
            "high_severity": severity_counts["high"],
            "medium_severity": severity_counts["medium"],
            "low_severity": severity_counts["low"],
            "average_probability": sum(risk.probability for risk in risks) / len(risks)
        }
    
    def _generate_risk_insights(
        self, 
        risks: List[WeatherRisk], 
        crop_type: Optional[str], 
        knowledge_base: Dict[str, Any]
    ) -> List[str]:
        """Generate risk insights and recommendations."""
        insights = []
        
        if not risks:
            insights.append("✅ Aucun risque météorologique significatif détecté")
            return insights
        
        # High severity risks
        high_risks = [r for r in risks if r.severity == "high"]
        if high_risks:
            insights.append(f"⚠️ {len(high_risks)} risque(s) de haute sévérité détecté(s)")
        
        # Crop-specific insights
        if crop_type:
            crop_risks = knowledge_base.get("crop_specific_risks", {}).get(crop_type.lower(), {})
            if crop_risks:
                insights.append(f"🌾 Analyse spécifique pour {crop_type}")
                insights.append(f"   - Tolérance au gel: {crop_risks.get('frost_tolerance', 'N/A')}°C")
                insights.append(f"   - Tolérance à la chaleur: {crop_risks.get('heat_tolerance', 'N/A')}°C")
        
        return insights
    
    def _run(
        self, 
        weather_data_json: str,
        crop_type: str = None,
        **kwargs
    ) -> str:
        """
        Analyze agricultural weather risks from weather data.
        
        Args:
            weather_data_json: JSON string from GetWeatherDataTool
            crop_type: Type of crop for crop-specific risk analysis
        """
        try:
            # Validate inputs
            validation_errors = self._validate_inputs(weather_data_json, crop_type)
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
                return json.dumps({"error": "Aucune donnée météo fournie pour l'analyse des risques"})
            
            # Convert to WeatherCondition objects
            conditions = [WeatherCondition(**condition_dict) for condition_dict in weather_conditions]
            
            # Analyze risks
            risks = self._analyze_agricultural_risks(conditions, crop_type, knowledge_base)
            
            # Calculate risk summary
            risk_summary = self._calculate_risk_summary(risks)
            
            # Generate risk insights
            risk_insights = self._generate_risk_insights(risks, crop_type, knowledge_base)
            
            result = {
                "location": data.get("location", ""),
                "forecast_period_days": data.get("forecast_period_days", 0),
                "risks": [asdict(risk) for risk in risks],
                "risk_summary": risk_summary,
                "risk_insights": risk_insights,
                "crop_type": crop_type,
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
            logger.error(f"Analyze weather risks error: {e}")
            return json.dumps({
                "error": f"Erreur lors de l'analyse des risques météo: {str(e)}",
                "error_type": type(e).__name__
            })
    
    async def _arun(
        self, 
        weather_data_json: str,
        crop_type: str = None,
        **kwargs
    ) -> str:
        """
        Asynchronous version of weather risk analysis.
        """
        # For now, just call the sync version
        return self._run(weather_data_json, crop_type, **kwargs)
    
    def clear_cache(self):
        """Clear internal caches."""
        self._config_cache = None
        logger.info("Cleared tool caches")
