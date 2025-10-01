"""
Enhanced Analyze Weather Risks Tool - With Caching and Type Safety

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

from app.tools.schemas.risk_schemas import (
    RiskAnalysisInput,
    RiskAnalysisOutput,
    WeatherRiskDetail,
    RiskSummary,
    CROP_RISK_PROFILES
)
from app.tools.exceptions import (
    WeatherValidationError,
    WeatherDataError
)
from app.core.cache import redis_cache

logger = logging.getLogger(__name__)


class EnhancedRiskAnalysisService:
    """Service for analyzing agricultural weather risks with caching"""
    
    @redis_cache(
        ttl=3600,  # 1 hour cache (risk analysis is derived data)
        model_class=RiskAnalysisOutput,
        category="weather"
    )
    async def analyze_risks(
        self,
        weather_data_json: str,
        crop_type: Optional[str] = None
    ) -> RiskAnalysisOutput:
        """
        Analyze agricultural weather risks from weather data
        
        Uses 1-hour cache since risk analysis is derived from weather data
        and doesn't change as frequently as raw weather data.
        
        Args:
            weather_data_json: JSON string from weather tool
            crop_type: Optional crop type for crop-specific analysis
            
        Returns:
            RiskAnalysisOutput with identified risks and recommendations
            
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
                raise WeatherDataError("Aucune donnée météo fournie pour l'analyse des risques")
            
            # Analyze risks
            risks = self._analyze_agricultural_risks(weather_conditions, crop_type)
            
            # Calculate risk summary
            risk_summary = self._calculate_risk_summary(risks)
            
            # Generate risk insights
            risk_insights = self._generate_risk_insights(risks, crop_type)
            
            # Build output
            result = RiskAnalysisOutput(
                location=data.get("location", ""),
                forecast_period_days=data.get("forecast_period_days", len(weather_conditions)),
                risks=risks,
                risk_summary=risk_summary,
                risk_insights=risk_insights,
                crop_type=crop_type,
                total_risks=len(risks),
                data_source="weather_analysis",
                analyzed_at=datetime.utcnow().isoformat() + "Z",
                success=True
            )
            
            return result
            
        except json.JSONDecodeError as e:
            raise WeatherValidationError(f"Invalid JSON in weather_data_json: {str(e)}")
        except KeyError as e:
            raise WeatherDataError(f"Missing required field in weather data: {str(e)}")
    
    def _analyze_agricultural_risks(
        self,
        weather_conditions: List[Dict[str, Any]],
        crop_type: Optional[str] = None
    ) -> List[WeatherRiskDetail]:
        """Analyze weather risks for agricultural activities"""
        risks = []
        
        # Get crop profile if specified
        crop_profile = CROP_RISK_PROFILES.get(crop_type.lower()) if crop_type else None
        
        for condition in weather_conditions:
            date = condition.get("date", "")
            temp_min = condition.get("temperature_min", 0)
            temp_max = condition.get("temperature_max", 0)
            humidity = condition.get("humidity", 0)
            wind_speed = condition.get("wind_speed", 0)
            precipitation = condition.get("precipitation", 0)
            
            # Frost risk
            frost_threshold = crop_profile.frost_tolerance if crop_profile else 2
            if temp_min < frost_threshold:
                severity = "élevée" if temp_min < (frost_threshold - 4) else "modérée"
                risks.append(WeatherRiskDetail(
                    risk_type="gel",
                    severity=severity,
                    probability=0.9,
                    impact=f"Dégâts sur cultures sensibles (température: {temp_min:.1f}°C)",
                    recommendations=[
                        "Protéger les cultures sensibles",
                        "Surveiller les températures nocturnes",
                        "Prévoir des mesures de protection (voiles, irrigation)"
                    ],
                    affected_date=date
                ))
            
            # Wind risk for spraying
            if wind_speed > 15:
                severity = "élevée" if wind_speed > 25 else "modérée"
                risks.append(WeatherRiskDetail(
                    risk_type="vent",
                    severity=severity,
                    probability=0.8,
                    impact=f"Dérive des produits phytosanitaires (vent: {wind_speed:.0f} km/h)",
                    recommendations=[
                        "Éviter les pulvérisations",
                        "Utiliser des buses anti-dérive",
                        "Reporter les traitements"
                    ],
                    affected_date=date
                ))
            
            # Heavy rain risk
            if precipitation > 10:
                severity = "élevée" if precipitation > 20 else "modérée"
                risks.append(WeatherRiskDetail(
                    risk_type="pluie",
                    severity=severity,
                    probability=0.7,
                    impact=f"Lessivage des sols, difficultés d'accès ({precipitation:.0f} mm)",
                    recommendations=[
                        "Éviter les travaux de sol",
                        "Vérifier le drainage",
                        "Reporter les interventions au champ"
                    ],
                    affected_date=date
                ))
            
            # Heat stress risk
            heat_threshold = crop_profile.heat_tolerance if crop_profile else 35
            if temp_max > heat_threshold:
                severity = "élevée" if temp_max > (heat_threshold + 5) else "modérée"
                risks.append(WeatherRiskDetail(
                    risk_type="stress_thermique",
                    severity=severity,
                    probability=0.6,
                    impact=f"Stress hydrique des cultures (température: {temp_max:.1f}°C)",
                    recommendations=[
                        "Irrigation d'urgence si possible",
                        "Surveillance accrue des cultures",
                        "Éviter les interventions stressantes"
                    ],
                    affected_date=date
                ))
            
            # Drought risk
            if precipitation < 1 and humidity < 40:
                risks.append(WeatherRiskDetail(
                    risk_type="sécheresse",
                    severity="modérée",
                    probability=0.5,
                    impact=f"Stress hydrique prolongé (humidité: {humidity:.0f}%)",
                    recommendations=[
                        "Planifier l'irrigation",
                        "Surveiller l'humidité du sol",
                        "Adapter les interventions"
                    ],
                    affected_date=date
                ))
        
        return risks
    
    def _calculate_risk_summary(self, risks: List[WeatherRiskDetail]) -> RiskSummary:
        """Calculate risk summary statistics"""
        if not risks:
            return RiskSummary(
                total_risks=0,
                high_severity_risks=0,
                risk_types=[],
                most_common_risk=None
            )
        
        risk_types = [risk.risk_type for risk in risks]
        high_severity_risks = [risk for risk in risks if risk.severity == "élevée"]
        
        # Find most common risk
        most_common = max(set(risk_types), key=risk_types.count) if risk_types else None
        
        return RiskSummary(
            total_risks=len(risks),
            high_severity_risks=len(high_severity_risks),
            risk_types=list(set(risk_types)),
            most_common_risk=most_common
        )
    
    def _generate_risk_insights(
        self,
        risks: List[WeatherRiskDetail],
        crop_type: Optional[str] = None
    ) -> List[str]:
        """Generate human-readable risk insights"""
        insights = []
        
        risk_types = [risk.risk_type for risk in risks]
        
        # General risk insights
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
        
        # No risks
        if not risks:
            insights.append("✅ Conditions météo favorables pour les travaux agricoles")
        
        # Crop-specific insights
        if crop_type and crop_type.lower() in CROP_RISK_PROFILES:
            crop_insights = self._get_crop_specific_insights(crop_type, risks)
            insights.extend(crop_insights)
        
        return insights
    
    def _get_crop_specific_insights(
        self,
        crop_type: str,
        risks: List[WeatherRiskDetail]
    ) -> List[str]:
        """Get crop-specific weather insights"""
        insights = []
        crop_name = crop_type.lower()
        
        if crop_name == "blé":
            if any(risk.risk_type == "gel" for risk in risks):
                insights.append("🌾 Blé: Surveiller les stades de développement sensibles au gel")
            if any(risk.risk_type == "pluie" for risk in risks):
                insights.append("🌾 Blé: Éviter les traitements en cas de pluie")
        
        elif crop_name == "maïs":
            if any(risk.risk_type == "stress_thermique" for risk in risks):
                insights.append("🌽 Maïs: Stress thermique possible - irrigation recommandée")
            if any(risk.risk_type == "vent" for risk in risks):
                insights.append("🌽 Maïs: Vent fort - risque de verse")
        
        elif crop_name == "colza":
            if any(risk.risk_type == "gel" for risk in risks):
                insights.append("🌻 Colza: Gel possible - protéger les fleurs")
            if any(risk.risk_type == "pluie" for risk in risks):
                insights.append("🌻 Colza: Pluie - risque de maladies fongiques")
        
        return insights


# Global service instance
risk_analysis_service = EnhancedRiskAnalysisService()


async def analyze_weather_risks_enhanced(
    weather_data_json: str,
    crop_type: Optional[str] = None
) -> str:
    """
    Analyze agricultural weather risks from weather data
    
    Args:
        weather_data_json: JSON string from weather tool containing forecast data
        crop_type: Optional crop type for crop-specific analysis
        
    Returns:
        JSON string with risk analysis, summary, and recommendations
    """
    try:
        # Validate input
        input_data = RiskAnalysisInput(
            weather_data_json=weather_data_json,
            crop_type=crop_type
        )

        # Analyze risks
        result = await risk_analysis_service.analyze_risks(
            weather_data_json=input_data.weather_data_json,
            crop_type=input_data.crop_type
        )

        # Return as JSON
        return result.model_dump_json(indent=2, exclude_none=True)

    except ValidationError as e:
        logger.error(f"Risk analysis Pydantic validation error: {e}")
        error_result = RiskAnalysisOutput(
            location="",
            forecast_period_days=0,
            risks=[],
            risk_summary=RiskSummary(total_risks=0, high_severity_risks=0, risk_types=[]),
            risk_insights=[],
            total_risks=0,
            data_source="error",
            analyzed_at=datetime.utcnow().isoformat() + "Z",
            success=False,
            error=f"Paramètres invalides: {str(e)}",
            error_type="validation"
        )
        return error_result.model_dump_json(indent=2)

    except WeatherValidationError as e:
        logger.error(f"Risk analysis validation error: {e}")
        error_result = RiskAnalysisOutput(
            location="",
            forecast_period_days=0,
            risks=[],
            risk_summary=RiskSummary(total_risks=0, high_severity_risks=0, risk_types=[]),
            risk_insights=[],
            total_risks=0,
            data_source="error",
            analyzed_at=datetime.utcnow().isoformat() + "Z",
            success=False,
            error=str(e),
            error_type="validation"
        )
        return error_result.model_dump_json(indent=2)
        
    except WeatherDataError as e:
        logger.error(f"Risk analysis data error: {e}")
        error_result = RiskAnalysisOutput(
            location="",
            forecast_period_days=0,
            risks=[],
            risk_summary=RiskSummary(total_risks=0, high_severity_risks=0, risk_types=[]),
            risk_insights=[],
            total_risks=0,
            data_source="error",
            analyzed_at=datetime.utcnow().isoformat() + "Z",
            success=False,
            error=str(e),
            error_type="data_missing"
        )
        return error_result.model_dump_json(indent=2)
        
    except Exception as e:
        logger.error(f"Unexpected risk analysis error: {e}", exc_info=True)
        error_result = RiskAnalysisOutput(
            location="",
            forecast_period_days=0,
            risks=[],
            risk_summary=RiskSummary(total_risks=0, high_severity_risks=0, risk_types=[]),
            risk_insights=[],
            total_risks=0,
            data_source="error",
            analyzed_at=datetime.utcnow().isoformat() + "Z",
            success=False,
            error="Erreur inattendue lors de l'analyse des risques. Veuillez réessayer.",
            error_type="unknown"
        )
        return error_result.model_dump_json(indent=2)


# Create the enhanced tool
analyze_weather_risks_tool = StructuredTool.from_function(
    func=analyze_weather_risks_enhanced,
    name="analyze_weather_risks",
    description="""Analyse les risques météorologiques agricoles à partir des données météo.

    Identifie les risques (gel, vent, pluie, stress thermique, sécheresse) et fournit
    des recommandations adaptées. Supporte l'analyse spécifique par culture (blé, maïs, colza, etc.).

    Entrée: JSON de données météo + type de culture (optionnel)
    Sortie: Analyse des risques avec recommandations""",
    args_schema=RiskAnalysisInput,
    return_direct=False,
    coroutine=analyze_weather_risks_enhanced,
    handle_validation_error=False  # We handle errors ourselves
)

