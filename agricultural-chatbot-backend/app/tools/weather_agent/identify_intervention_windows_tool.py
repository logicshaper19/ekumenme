"""
Identify Intervention Windows Tool - Single Purpose Tool

Job: Identify optimal intervention windows from weather data.
Input: JSON string of weather data from GetWeatherDataTool
Output: JSON string with intervention windows

This tool does ONLY:
- Execute specific, well-defined function
- Take structured inputs, return structured outputs
- Contain domain-specific business logic
- Be stateless and reusable

No prompting logic, no orchestration, no agent responsibilities.
"""

from typing import Dict, List, Any, Optional
from langchain.tools import BaseTool
import logging
import json
from dataclasses import dataclass, asdict

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

class IdentifyInterventionWindowsTool(BaseTool):
    """
    Tool: Identify optimal intervention windows from weather data.
    
    Job: Take weather data and identify optimal windows for agricultural interventions.
    Input: JSON string of weather data from GetWeatherDataTool
    Output: JSON string with intervention windows
    """
    
    name: str = "identify_intervention_windows_tool"
    description: str = "Identifie les fenêtres optimales pour les interventions agricoles"
    
    def _run(
        self, 
        weather_data_json: str,
        intervention_types: List[str] = None,
        **kwargs
    ) -> str:
        """
        Identify optimal intervention windows from weather data.
        
        Args:
            weather_data_json: JSON string from GetWeatherDataTool
            intervention_types: List of intervention types to analyze
        """
        try:
            data = json.loads(weather_data_json)
            
            if "error" in data:
                return weather_data_json  # Pass through errors
            
            weather_conditions = data.get("weather_conditions", [])
            if not weather_conditions:
                return json.dumps({"error": "Aucune donnée météo fournie pour l'analyse des fenêtres"})
            
            # Convert back to WeatherCondition objects for processing
            conditions = [WeatherCondition(**condition_dict) for condition_dict in weather_conditions]
            
            # Default intervention types if not specified
            if not intervention_types:
                intervention_types = ["pulvérisation", "travaux_champ", "semis", "récolte"]
            
            # Identify intervention windows
            windows = self._identify_intervention_windows(conditions, intervention_types)
            
            # Calculate window statistics
            window_stats = self._calculate_window_statistics(windows)
            
            # Generate window insights
            window_insights = self._generate_window_insights(windows)
            
            result = {
                "location": data.get("location", ""),
                "forecast_period_days": data.get("forecast_period_days", 0),
                "intervention_types": intervention_types,
                "windows": [asdict(window) for window in windows],
                "window_statistics": window_stats,
                "window_insights": window_insights,
                "total_windows": len(windows)
            }
            
            return json.dumps(result, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"Identify intervention windows error: {e}")
            return json.dumps({"error": f"Erreur lors de l'identification des fenêtres: {str(e)}"})
    
    def _identify_intervention_windows(self, conditions: List[WeatherCondition], intervention_types: List[str]) -> List[InterventionWindow]:
        """Identify optimal windows for agricultural interventions."""
        windows = []
        
        for condition in conditions:
            # Good conditions for spraying
            if "pulvérisation" in intervention_types and self._is_good_for_spraying(condition):
                windows.append(InterventionWindow(
                    date=condition.date,
                    intervention_type="pulvérisation",
                    conditions="optimales",
                    duration_hours=8.0,
                    confidence=0.9
                ))
            
            # Good conditions for field work
            if "travaux_champ" in intervention_types and self._is_good_for_field_work(condition):
                windows.append(InterventionWindow(
                    date=condition.date,
                    intervention_type="travaux_champ",
                    conditions="bonnes",
                    duration_hours=10.0,
                    confidence=0.8
                ))
            
            # Good conditions for planting
            if "semis" in intervention_types and self._is_good_for_planting(condition):
                windows.append(InterventionWindow(
                    date=condition.date,
                    intervention_type="semis",
                    conditions="favorables",
                    duration_hours=6.0,
                    confidence=0.7
                ))
            
            # Good conditions for harvesting
            if "récolte" in intervention_types and self._is_good_for_harvesting(condition):
                windows.append(InterventionWindow(
                    date=condition.date,
                    intervention_type="récolte",
                    conditions="excellentes",
                    duration_hours=12.0,
                    confidence=0.95
                ))
        
        return windows
    
    def _is_good_for_spraying(self, condition: WeatherCondition) -> bool:
        """Check if conditions are good for spraying."""
        return (condition.wind_speed < 10 and 
                condition.precipitation < 2 and 
                condition.humidity < 80 and
                condition.temperature_min > 5)
    
    def _is_good_for_field_work(self, condition: WeatherCondition) -> bool:
        """Check if conditions are good for field work."""
        return (condition.precipitation < 1 and 
                condition.temperature_min > 5 and
                condition.wind_speed < 20)
    
    def _is_good_for_planting(self, condition: WeatherCondition) -> bool:
        """Check if conditions are good for planting."""
        return (condition.temperature_min > 8 and
                condition.precipitation < 3 and
                condition.humidity > 60)
    
    def _is_good_for_harvesting(self, condition: WeatherCondition) -> bool:
        """Check if conditions are good for harvesting."""
        return (condition.precipitation < 1 and
                condition.humidity < 70 and
                condition.wind_speed < 15)
    
    def _calculate_window_statistics(self, windows: List[InterventionWindow]) -> Dict[str, Any]:
        """Calculate window statistics."""
        if not windows:
            return {"total_windows": 0, "windows_by_type": {}, "average_confidence": 0}
        
        windows_by_type = {}
        total_confidence = 0
        
        for window in windows:
            if window.intervention_type not in windows_by_type:
                windows_by_type[window.intervention_type] = 0
            windows_by_type[window.intervention_type] += 1
            total_confidence += window.confidence
        
        return {
            "total_windows": len(windows),
            "windows_by_type": windows_by_type,
            "average_confidence": round(total_confidence / len(windows), 2)
        }
    
    def _generate_window_insights(self, windows: List[InterventionWindow]) -> List[str]:
        """Generate window insights."""
        insights = []
        
        if not windows:
            insights.append("Aucune fenêtre d'intervention optimale identifiée")
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
            insights.append(f"Meilleure fenêtre pour {intervention_type}: {best_window.date} (confiance: {best_window.confidence:.0%})")
        
        return insights
