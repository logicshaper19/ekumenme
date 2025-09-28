"""
Analyze Weather Risks Tool - Single Purpose Tool

Job: Analyze agricultural weather risks from weather data.
Input: JSON string of weather data from GetWeatherDataTool
Output: JSON string with risk analysis

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
class WeatherRisk:
    """Structured weather risk."""
    risk_type: str
    severity: str
    probability: float
    impact: str
    recommendations: List[str]

class AnalyzeWeatherRisksTool(BaseTool):
    """
    Tool: Analyze agricultural weather risks from weather data.
    
    Job: Take weather data and analyze agricultural risks.
    Input: JSON string of weather data from GetWeatherDataTool
    Output: JSON string with risk analysis
    """
    
    name: str = "analyze_weather_risks_tool"
    description: str = "Analyse les risques météorologiques agricoles"
    
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
            data = json.loads(weather_data_json)
            
            if "error" in data:
                return weather_data_json  # Pass through errors
            
            weather_conditions = data.get("weather_conditions", [])
            if not weather_conditions:
                return json.dumps({"error": "Aucune donnée météo fournie pour l'analyse des risques"})
            
            # Convert back to WeatherCondition objects for processing
            conditions = [WeatherCondition(**condition_dict) for condition_dict in weather_conditions]
            
            # Analyze risks
            risks = self._analyze_agricultural_risks(conditions, crop_type)
            
            # Calculate risk summary
            risk_summary = self._calculate_risk_summary(risks)
            
            # Generate risk insights
            risk_insights = self._generate_risk_insights(risks, crop_type)
            
            result = {
                "location": data.get("location", ""),
                "forecast_period_days": data.get("forecast_period_days", 0),
                "risks": [asdict(risk) for risk in risks],
                "risk_summary": risk_summary,
                "risk_insights": risk_insights,
                "crop_type": crop_type,
                "total_risks": len(risks)
            }
            
            return json.dumps(result, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"Analyze weather risks error: {e}")
            return json.dumps({"error": f"Erreur lors de l'analyse des risques: {str(e)}"})
    
    def _analyze_agricultural_risks(self, conditions: List[WeatherCondition], crop_type: str = None) -> List[WeatherRisk]:
        """Analyze weather risks for agricultural activities."""
        risks = []
        
        for condition in conditions:
            # Frost risk
            if condition.temperature_min < 2:
                risks.append(WeatherRisk(
                    risk_type="gel",
                    severity="élevée" if condition.temperature_min < -2 else "modérée",
                    probability=0.9,
                    impact="Dégâts sur cultures sensibles",
                    recommendations=["Protéger les cultures sensibles", "Surveiller les températures"]
                ))
            
            # Wind risk for spraying
            if condition.wind_speed > 15:
                risks.append(WeatherRisk(
                    risk_type="vent",
                    severity="élevée" if condition.wind_speed > 25 else "modérée",
                    probability=0.8,
                    impact="Dérive des produits phytosanitaires",
                    recommendations=["Éviter les pulvérisations", "Utiliser des buses anti-dérive"]
                ))
            
            # Heavy rain risk
            if condition.precipitation > 10:
                risks.append(WeatherRisk(
                    risk_type="pluie",
                    severity="élevée" if condition.precipitation > 20 else "modérée",
                    probability=0.7,
                    impact="Lessivage des sols, difficultés d'accès",
                    recommendations=["Éviter les travaux de sol", "Vérifier le drainage"]
                ))
            
            # Heat stress risk
            if condition.temperature_max > 35:
                risks.append(WeatherRisk(
                    risk_type="stress_thermique",
                    severity="élevée" if condition.temperature_max > 40 else "modérée",
                    probability=0.6,
                    impact="Stress hydrique des cultures",
                    recommendations=["Irrigation d'urgence", "Surveillance accrue"]
                ))
            
            # Drought risk
            if condition.precipitation < 1 and condition.humidity < 40:
                risks.append(WeatherRisk(
                    risk_type="sécheresse",
                    severity="modérée",
                    probability=0.5,
                    impact="Stress hydrique prolongé",
                    recommendations=["Planifier l'irrigation", "Surveiller l'humidité du sol"]
                ))
        
        return risks
    
    def _calculate_risk_summary(self, risks: List[WeatherRisk]) -> Dict[str, Any]:
        """Calculate risk summary statistics."""
        if not risks:
            return {"total_risks": 0, "high_severity_risks": 0, "risk_types": []}
        
        risk_types = [risk.risk_type for risk in risks]
        high_severity_risks = [risk for risk in risks if risk.severity == "élevée"]
        
        return {
            "total_risks": len(risks),
            "high_severity_risks": len(high_severity_risks),
            "risk_types": list(set(risk_types)),
            "most_common_risk": max(set(risk_types), key=risk_types.count) if risk_types else None
        }
    
    def _generate_risk_insights(self, risks: List[WeatherRisk], crop_type: str = None) -> List[str]:
        """Generate risk insights."""
        insights = []
        
        risk_types = [risk.risk_type for risk in risks]
        
        if "gel" in risk_types:
            insights.append("⚠️ Risque de gel - Protéger les cultures sensibles")
        if "vent" in risk_types:
            insights.append("⚠️ Vent fort - Éviter les pulvérisations")
        if "pluie" in risk_types:
            insights.append("⚠️ Pluie importante - Reporter les travaux de sol")
        if "stress_thermique" in risk_types:
            insights.append("🌡️ Stress thermique - Surveiller l'hydratation")
        if "sécheresse" in risk_types:
            insights.append("🌵 Sécheresse - Planifier l'irrigation")
        
        # General insights
        if not risks:
            insights.append("✅ Conditions météo favorables pour les travaux agricoles")
        
        # Crop-specific insights
        if crop_type:
            crop_insights = self._get_crop_specific_insights(crop_type, risks)
            insights.extend(crop_insights)
        
        return insights
    
    def _get_crop_specific_insights(self, crop_type: str, risks: List[WeatherRisk]) -> List[str]:
        """Get crop-specific weather insights."""
        insights = []
        
        if crop_type == "blé":
            if any(risk.risk_type == "gel" for risk in risks):
                insights.append("🌾 Blé: Surveiller les stades de développement sensibles au gel")
            if any(risk.risk_type == "pluie" for risk in risks):
                insights.append("🌾 Blé: Éviter les traitements en cas de pluie")
        
        elif crop_type == "maïs":
            if any(risk.risk_type == "stress_thermique" for risk in risks):
                insights.append("🌽 Maïs: Stress thermique possible - irrigation recommandée")
            if any(risk.risk_type == "vent" for risk in risks):
                insights.append("🌽 Maïs: Vent fort - risque de verse")
        
        elif crop_type == "colza":
            if any(risk.risk_type == "gel" for risk in risks):
                insights.append("🌻 Colza: Gel possible - protéger les fleurs")
            if any(risk.risk_type == "pluie" for risk in risks):
                insights.append("🌻 Colza: Pluie - risque de maladies fongiques")
        
        return insights
