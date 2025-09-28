"""
Get Weather Data Tool - Vector Database Ready Tool

Job: Retrieve weather forecast data for a location using real WeatherAPI.
Input: location, days
Output: JSON string of WeatherCondition objects

This tool does ONLY:
- Execute specific, well-defined function
- Take structured inputs, return structured outputs
- Contain domain-specific business logic
- Be stateless and reusable

Enhanced Features:
- External knowledge base (JSON file)
- Configurable analysis parameters
- Asynchronous support
- Comprehensive input validation
- Vector database ready architecture
- Real WeatherAPI integration
- Agricultural weather analysis

No prompting logic, no orchestration, no agent responsibilities.
"""

from typing import Dict, List, Any, Optional, Union
from langchain.tools import BaseTool
import logging
import json
import asyncio
import aiohttp
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path
import os

# Import configuration system
from ...config.weather_data_config import (
    get_weather_data_config, 
    get_weather_validation_config,
    WeatherDataConfig,
    WeatherValidationConfig
)

# Import vector database interface
from ...data.weather_vector_db_interface import (
    get_weather_knowledge_base,
    set_weather_knowledge_base,
    WeatherKnowledgeBaseInterface,
    WeatherKnowledge,
    WeatherSearchResult
)

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
    condition_code: int
    condition_description: str
    agricultural_impact: str
    recommended_activities: List[str]
    restrictions: List[str]
    search_metadata: Optional[Dict[str, Any]] = None

@dataclass
class ValidationError:
    """Validation error information."""
    field: str
    message: str
    severity: str  # "error", "warning", "info"

class GetWeatherDataTool(BaseTool):
    """
    Vector Database Ready Tool: Retrieve weather forecast data for a location using real WeatherAPI.
    
    Job: Get weather forecast data from real WeatherAPI with agricultural analysis.
    Input: location, days
    Output: JSON string of WeatherCondition objects
    
    Enhanced Features:
    - External knowledge base (JSON file)
    - Configurable analysis parameters
    - Asynchronous support
    - Comprehensive input validation
    - Vector database ready architecture
    - Real WeatherAPI integration
    - Agricultural weather analysis
    """
    
    name: str = "get_weather_data_tool"
    description: str = "Récupère les données de prévision météorologique avec analyse agricole"
    
    def __init__(
        self, 
        knowledge_base_path: Optional[str] = None,
        use_vector_search: bool = False,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.knowledge_base_path = knowledge_base_path or self._get_default_knowledge_path()
        self.use_vector_search = use_vector_search
        self._config_cache: Optional[WeatherDataConfig] = None
        self._validation_cache: Optional[WeatherValidationConfig] = None
        self._knowledge_base: Optional[WeatherKnowledgeBaseInterface] = None
    
    def _get_default_knowledge_path(self) -> str:
        """Get default knowledge base file path."""
        current_dir = Path(__file__).parent
        return str(current_dir.parent.parent / "data" / "weather_data_knowledge.json")
    
    def _get_knowledge_base(self) -> WeatherKnowledgeBaseInterface:
        """Get knowledge base instance."""
        if self._knowledge_base is None:
            if self.use_vector_search:
                # Use vector database (when implemented)
                self._knowledge_base = get_weather_knowledge_base()
            else:
                # Use JSON knowledge base
                from ...data.weather_vector_db_interface import JSONWeatherKnowledgeBase
                self._knowledge_base = JSONWeatherKnowledgeBase(self.knowledge_base_path)
        return self._knowledge_base
    
    def _get_config(self) -> WeatherDataConfig:
        """Get current weather configuration."""
        if self._config_cache is None:
            self._config_cache = get_weather_data_config()
        return self._config_cache
    
    def _get_validation_config(self) -> WeatherValidationConfig:
        """Get current validation configuration."""
        if self._validation_cache is None:
            self._validation_cache = get_weather_validation_config()
        return self._validation_cache
    
    def _validate_inputs(
        self, 
        location: str, 
        days: int
    ) -> List[ValidationError]:
        """Validate input parameters."""
        errors = []
        validation_config = self._get_validation_config()
        
        # Validate location
        if validation_config.require_location and not location:
            errors.append(ValidationError("location", "Location is required", "error"))
        elif location:
            if len(location.strip()) < validation_config.min_location_length:
                errors.append(ValidationError("location", f"Location too short (minimum {validation_config.min_location_length} characters)", "error"))
            elif len(location.strip()) > validation_config.max_location_length:
                errors.append(ValidationError("location", f"Location too long (maximum {validation_config.max_location_length} characters)", "warning"))
        
        # Validate days
        if validation_config.validate_days_range:
            if days < validation_config.min_days:
                errors.append(ValidationError("days", f"Days too low (minimum {validation_config.min_days})", "error"))
            elif days > validation_config.max_days:
                errors.append(ValidationError("days", f"Days too high (maximum {validation_config.max_days})", "error"))
        
        return errors
    
    async def _fetch_weather_data(
        self,
        location: str,
        days: int
    ) -> Dict[str, Any]:
        """Fetch weather data from WeatherAPI."""
        config = self._get_config()
        
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=config.timeout_seconds)) as session:
                url = f"{config.base_url}/forecast.json"
                params = {
                    "key": config.api_key,
                    "q": location,
                    "days": days,
                    "aqi": "no",
                    "alerts": "yes"
                }
                
                async with session.get(url, params=params) as response:
                    if response.status == 200:
                        data = await response.json()
                        return data
                    else:
                        error_text = await response.text()
                        logger.error(f"WeatherAPI error {response.status}: {error_text}")
                        return {"error": f"WeatherAPI error {response.status}: {error_text}"}
        
        except asyncio.TimeoutError:
            logger.error("WeatherAPI request timeout")
            return {"error": "WeatherAPI request timeout"}
        except Exception as e:
            logger.error(f"WeatherAPI request error: {e}")
            return {"error": f"WeatherAPI request error: {str(e)}"}
    
    async def _analyze_weather_conditions(
        self,
        weather_data: Dict[str, Any]
    ) -> List[WeatherCondition]:
        """Analyze weather conditions using knowledge base."""
        weather_conditions = []
        
        if "forecast" in weather_data and "forecastday" in weather_data["forecast"]:
            for day_data in weather_data["forecast"]["forecastday"]:
                date = day_data["date"]
                day_info = day_data["day"]
                
                # Get condition information
                condition_code = day_info.get("condition", {}).get("code", 1000)
                condition_text = day_info.get("condition", {}).get("text", "Unknown")
                
                # Search for agricultural analysis
                agricultural_analysis = await self._get_agricultural_analysis(
                    condition_code, condition_text, day_info
                )
                
                weather_condition = WeatherCondition(
                    date=date,
                    temperature_min=day_info.get("mintemp_c", 0.0),
                    temperature_max=day_info.get("maxtemp_c", 0.0),
                    humidity=day_info.get("avghumidity", 0.0),
                    wind_speed=day_info.get("maxwind_kph", 0.0) / 3.6,  # Convert to m/s
                    wind_direction="N",  # WeatherAPI doesn't provide direction in forecast
                    precipitation=day_info.get("totalprecip_mm", 0.0),
                    cloud_cover=day_info.get("cloud", 0.0),
                    uv_index=day_info.get("uv", 0.0),
                    condition_code=condition_code,
                    condition_description=condition_text,
                    agricultural_impact=agricultural_analysis.get("agricultural_impact", "unknown"),
                    recommended_activities=agricultural_analysis.get("recommended_activities", []),
                    restrictions=agricultural_analysis.get("restrictions", []),
                    search_metadata={
                        "search_method": "vector" if self.use_vector_search else "json",
                        "condition_code": condition_code,
                        "analysis_confidence": agricultural_analysis.get("confidence", 0.5)
                    }
                )
                
                weather_conditions.append(weather_condition)
        
        return weather_conditions
    
    async def _get_agricultural_analysis(
        self,
        condition_code: int,
        condition_text: str,
        day_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Get agricultural analysis for weather conditions."""
        knowledge_base = self._get_knowledge_base()
        
        # Search for weather condition in knowledge base
        search_results = await knowledge_base.search_by_condition(condition_text, limit=1)
        
        if search_results:
            weather_knowledge = search_results[0].weather_knowledge
            return {
                "agricultural_impact": weather_knowledge.agricultural_impact,
                "recommended_activities": weather_knowledge.recommended_activities,
                "restrictions": weather_knowledge.restrictions,
                "confidence": search_results[0].similarity_score
            }
        else:
            # Fallback analysis based on weather parameters
            return self._fallback_agricultural_analysis(day_info)
    
    def _fallback_agricultural_analysis(self, day_info: Dict[str, Any]) -> Dict[str, Any]:
        """Fallback agricultural analysis when knowledge base search fails."""
        temperature = day_info.get("avgtemp_c", 15.0)
        humidity = day_info.get("avghumidity", 70.0)
        wind_speed = day_info.get("maxwind_kph", 10.0) / 3.6
        precipitation = day_info.get("totalprecip_mm", 0.0)
        
        # Simple rule-based analysis
        if precipitation > 5.0:
            return {
                "agricultural_impact": "défavorable",
                "recommended_activities": ["irrigation_naturelle"],
                "restrictions": ["éviter_traitements", "éviter_récolte"],
                "confidence": 0.7
            }
        elif wind_speed > 25.0:
            return {
                "agricultural_impact": "défavorable",
                "recommended_activities": [],
                "restrictions": ["éviter_traitements", "risque_dérive"],
                "confidence": 0.6
            }
        elif 10.0 <= temperature <= 25.0 and 40.0 <= humidity <= 80.0:
            return {
                "agricultural_impact": "favorable",
                "recommended_activities": ["traitements_phytosanitaires", "récolte"],
                "restrictions": [],
                "confidence": 0.8
            }
        else:
            return {
                "agricultural_impact": "modéré",
                "recommended_activities": ["traitements_phytosanitaires"],
                "restrictions": [],
                "confidence": 0.5
            }
    
    def _generate_agricultural_summary(
        self,
        weather_conditions: List[WeatherCondition]
    ) -> Dict[str, Any]:
        """Generate agricultural summary from weather conditions."""
        config = self._get_config()
        
        summary = {
            "total_days": len(weather_conditions),
            "favorable_days": 0,
            "moderate_days": 0,
            "unfavorable_days": 0,
            "treatment_opportunities": 0,
            "harvest_opportunities": 0,
            "planting_opportunities": 0,
            "weather_alerts": []
        }
        
        for condition in weather_conditions:
            # Count impact categories
            if condition.agricultural_impact == "favorable":
                summary["favorable_days"] += 1
            elif condition.agricultural_impact == "modéré":
                summary["moderate_days"] += 1
            else:
                summary["unfavorable_days"] += 1
            
            # Count activity opportunities
            if "traitements_phytosanitaires" in condition.recommended_activities:
                summary["treatment_opportunities"] += 1
            if "récolte" in condition.recommended_activities:
                summary["harvest_opportunities"] += 1
            if "semis" in condition.recommended_activities:
                summary["planting_opportunities"] += 1
            
            # Check for weather alerts
            if condition.restrictions:
                summary["weather_alerts"].extend(condition.restrictions)
        
        # Remove duplicate alerts
        summary["weather_alerts"] = list(set(summary["weather_alerts"]))
        
        return summary
    
    def _run(
        self,
        location: str,
        days: int = 7,
        **kwargs
    ) -> str:
        """
        Retrieve weather forecast data for a location.
        
        Args:
            location: Location for weather forecast
            days: Number of days to forecast
        """
        try:
            # Validate inputs
            validation_errors = self._validate_inputs(location, days)
            validation_config = self._get_validation_config()
            
            if validation_errors and validation_config.strict_validation:
                error_messages = [f"{error.field}: {error.message}" for error in validation_errors if error.severity == "error"]
                if error_messages:
                    return json.dumps({
                        "error": "Validation errors",
                        "validation_errors": error_messages
                    })
            
            # Fetch weather data
            weather_data = asyncio.run(self._fetch_weather_data(location, days))
            
            if "error" in weather_data:
                return json.dumps({
                    "error": f"Failed to fetch weather data: {weather_data['error']}",
                    "location": location,
                    "days": days
                })
            
            # Analyze weather conditions
            weather_conditions = asyncio.run(self._analyze_weather_conditions(weather_data))
            
            if not weather_conditions:
                return json.dumps({
                    "error": "No weather data available",
                    "location": location,
                    "days": days
                })
            
            # Generate agricultural summary
            agricultural_summary = self._generate_agricultural_summary(weather_conditions)
            
            result = {
                "location": location,
                "forecast_period_days": days,
                "weather_conditions": [asdict(condition) for condition in weather_conditions],
                "agricultural_summary": agricultural_summary,
                "total_days": len(weather_conditions),
                "retrieved_at": datetime.now().isoformat(),
                "data_source": "WeatherAPI",
                "analysis_metadata": {
                    "search_method": "vector" if self.use_vector_search else "json",
                    "config_used": asdict(self._get_config()),
                    "api_success": True
                }
            }
            
            # Add validation warnings if any
            if validation_errors and validation_config.return_validation_errors:
                warnings = [{"field": error.field, "message": error.message, "severity": error.severity} 
                           for error in validation_errors if error.severity in ["warning", "info"]]
                if warnings:
                    result["validation_warnings"] = warnings
            
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"Get weather data error: {e}")
            return json.dumps({
                "error": f"Erreur lors de la récupération des données météo: {str(e)}",
                "error_type": type(e).__name__
            })
    
    async def _arun(
        self,
        location: str,
        days: int = 7,
        **kwargs
    ) -> str:
        """
        Asynchronous version of weather data retrieval.
        
        Args:
            location: Location for weather forecast
            days: Number of days to forecast
        """
        try:
            # Validate inputs
            validation_errors = self._validate_inputs(location, days)
            validation_config = self._get_validation_config()
            
            if validation_errors and validation_config.strict_validation:
                error_messages = [f"{error.field}: {error.message}" for error in validation_errors if error.severity == "error"]
                if error_messages:
                    return json.dumps({
                        "error": "Validation errors",
                        "validation_errors": error_messages
                    })
            
            # Fetch weather data asynchronously
            weather_data = await self._fetch_weather_data(location, days)
            
            if "error" in weather_data:
                return json.dumps({
                    "error": f"Failed to fetch weather data: {weather_data['error']}",
                    "location": location,
                    "days": days
                })
            
            # Analyze weather conditions asynchronously
            weather_conditions = await self._analyze_weather_conditions(weather_data)
            
            if not weather_conditions:
                return json.dumps({
                    "error": "No weather data available",
                    "location": location,
                    "days": days
                })
            
            # Generate agricultural summary
            agricultural_summary = self._generate_agricultural_summary(weather_conditions)
            
            result = {
                "location": location,
                "forecast_period_days": days,
                "weather_conditions": [asdict(condition) for condition in weather_conditions],
                "agricultural_summary": agricultural_summary,
                "total_days": len(weather_conditions),
                "retrieved_at": datetime.now().isoformat(),
                "data_source": "WeatherAPI",
                "analysis_metadata": {
                    "search_method": "vector" if self.use_vector_search else "json",
                    "config_used": asdict(self._get_config()),
                    "api_success": True,
                    "execution_mode": "async"
                }
            }
            
            # Add validation warnings if any
            if validation_errors and validation_config.return_validation_errors:
                warnings = [{"field": error.field, "message": error.message, "severity": error.severity} 
                           for error in validation_errors if error.severity in ["warning", "info"]]
                if warnings:
                    result["validation_warnings"] = warnings
            
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"Async get weather data error: {e}")
            return json.dumps({
                "error": f"Erreur lors de la récupération asynchrone des données météo: {str(e)}",
                "error_type": type(e).__name__
            })
    
    def clear_cache(self):
        """Clear internal caches (useful for testing or config updates)."""
        self._config_cache = None
        self._validation_cache = None
        self._knowledge_base = None
        logger.info("Cleared tool caches")
    
    def enable_vector_search(self, enable: bool = True):
        """Enable or disable vector search."""
        self.use_vector_search = enable
        self._knowledge_base = None  # Reset knowledge base
        logger.info(f"Vector search {'enabled' if enable else 'disabled'}")
