"""
Calculate Evapotranspiration Tool - Single Purpose Tool

Job: Calculate evapotranspiration and water needs from weather data.
Input: JSON string of weather data from GetWeatherDataTool
Output: JSON string with evapotranspiration analysis

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
from dataclasses import dataclass

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

class CalculateEvapotranspirationTool(BaseTool):
    """
    Tool: Calculate evapotranspiration and water needs from weather data.
    
    Job: Take weather data and calculate evapotranspiration for crops.
    Input: JSON string of weather data from GetWeatherDataTool
    Output: JSON string with evapotranspiration analysis
    """
    
    name: str = "calculate_evapotranspiration_tool"
    description: str = "Calcule l'évapotranspiration et les besoins en eau"
    
    def _run(
        self, 
        weather_data_json: str,
        crop_type: str = None,
        **kwargs
    ) -> str:
        """
        Calculate evapotranspiration and water needs from weather data.
        
        Args:
            weather_data_json: JSON string from GetWeatherDataTool
            crop_type: Type of crop for crop-specific calculations
        """
        try:
            data = json.loads(weather_data_json)
            
            if "error" in data:
                return weather_data_json  # Pass through errors
            
            weather_conditions = data.get("weather_conditions", [])
            if not weather_conditions:
                return json.dumps({"error": "Aucune donnée météo fournie pour le calcul de l'ETP"})
            
            # Convert back to WeatherCondition objects for processing
            conditions = [WeatherCondition(**condition_dict) for condition_dict in weather_conditions]
            
            # Calculate evapotranspiration
            etp_data = self._calculate_evapotranspiration(conditions, crop_type)
            
            # Calculate water needs
            water_needs = self._calculate_water_needs(etp_data, crop_type)
            
            # Generate irrigation recommendations
            irrigation_recommendations = self._generate_irrigation_recommendations(etp_data, water_needs)
            
            result = {
                "location": data.get("location", ""),
                "forecast_period_days": data.get("forecast_period_days", 0),
                "crop_type": crop_type,
                "evapotranspiration": etp_data,
                "water_needs": water_needs,
                "irrigation_recommendations": irrigation_recommendations
            }
            
            return json.dumps(result, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"Calculate evapotranspiration error: {e}")
            return json.dumps({"error": f"Erreur lors du calcul de l'ETP: {str(e)}"})
    
    def _calculate_evapotranspiration(self, conditions: List[WeatherCondition], crop_type: str = None) -> Dict[str, Any]:
        """Calculate evapotranspiration for weather conditions."""
        # Simplified ETP calculation - in production would use Penman-Monteith
        total_etp = 0
        daily_etp = []
        
        for condition in conditions:
            # Simplified ETP calculation
            etp = (condition.temperature_max + condition.temperature_min) / 2 * 0.1
            if condition.humidity < 60:
                etp *= 1.2  # Higher ETP in dry conditions
            if condition.wind_speed > 15:
                etp *= 1.1  # Higher ETP with wind
            
            total_etp += etp
            daily_etp.append({
                "date": condition.date,
                "etp_mm": round(etp, 1)
            })
        
        # Crop-specific water needs
        crop_water_needs = {
            "blé": {"coefficient": 0.8, "critical_stage": "épiaison"},
            "maïs": {"coefficient": 1.2, "critical_stage": "floraison"},
            "colza": {"coefficient": 0.9, "critical_stage": "floraison"},
            "tournesol": {"coefficient": 1.0, "critical_stage": "floraison"}
        }
        
        crop_coefficient = crop_water_needs.get(crop_type, {"coefficient": 1.0})["coefficient"]
        crop_etp = total_etp * crop_coefficient
        
        return {
            "etp_totale_mm": round(total_etp, 1),
            "etp_culture_mm": round(crop_etp, 1),
            "etp_quotidienne": daily_etp,
            "coefficient_culture": crop_coefficient
        }
    
    def _calculate_water_needs(self, etp_data: Dict[str, Any], crop_type: str = None) -> Dict[str, Any]:
        """Calculate water needs based on ETP."""
        crop_etp = etp_data["etp_culture_mm"]
        
        # Assess irrigation needs
        if crop_etp > 5:
            irrigation_needs = "Élevés - Irrigation recommandée"
        elif crop_etp > 3:
            irrigation_needs = "Modérés - Surveillance nécessaire"
        else:
            irrigation_needs = "Faibles - Irrigation non nécessaire"
        
        return {
            "irrigation_needs": irrigation_needs,
            "etp_culture_mm": crop_etp,
            "water_deficit_risk": "Élevé" if crop_etp > 4 else "Modéré" if crop_etp > 2 else "Faible"
        }
    
    def _generate_irrigation_recommendations(self, etp_data: Dict[str, Any], water_needs: Dict[str, Any]) -> List[str]:
        """Generate irrigation recommendations."""
        recommendations = []
        
        crop_etp = etp_data["etp_culture_mm"]
        
        if crop_etp > 5:
            recommendations.append("Irrigation d'urgence recommandée")
            recommendations.append("Surveiller l'humidité du sol quotidiennement")
        elif crop_etp > 3:
            recommendations.append("Surveillance accrue de l'humidité")
            recommendations.append("Préparer l'irrigation si nécessaire")
        else:
            recommendations.append("Irrigation non nécessaire actuellement")
        
        # Daily recommendations
        daily_etp = etp_data["etp_quotidienne"]
        high_etp_days = [day for day in daily_etp if day["etp_mm"] > 3]
        if high_etp_days:
            recommendations.append(f"Jours à forte ETP: {', '.join([day['date'] for day in high_etp_days])}")
        
        return recommendations
