"""
Enhanced Analyze Soil Health Tool.

Improvements:
- Type-safe Pydantic schemas
- Redis caching (2h TTL for soil analysis)
- Realistic soil health scoring based on agronomic standards
- Crop-specific optimal ranges
- Actionable improvement recommendations
- Critical issue identification
"""

import logging
from typing import Optional, List, Dict
from langchain.tools import StructuredTool

from app.tools.schemas.sustainability_schemas import (
    SoilHealthInput,
    SoilHealthOutput,
    SoilIndicator,
    SoilHealthStatus
)
from app.core.cache import redis_cache

logger = logging.getLogger(__name__)


class SoilHealthService:
    """
    Service for analyzing soil health with caching.
    
    Features:
    - Analyzes multiple soil indicators against optimal ranges
    - Crop-specific recommendations
    - Overall health scoring (0-10 scale)
    - Prioritized improvement recommendations
    - Estimated improvement timelines
    
    Cache Strategy:
    - TTL: 2 hours (7200s) - soil conditions change slowly
    - Category: sustainability
    - Keys include all soil indicators
    
    Agronomic Standards:
    - pH: 6.0-7.5 for most crops (varies by crop)
    - Organic matter: 3-6% optimal
    - NPK: Crop-specific ranges based on French agricultural standards
    """
    
    # Optimal ranges for common soil indicators (French agricultural standards)
    OPTIMAL_RANGES = {
        "ph": {"min": 6.0, "max": 7.5, "unit": "pH", "critical_low": 5.0, "critical_high": 8.5, "improvement_months": 4},
        "organic_matter_percent": {"min": 3.0, "max": 6.0, "unit": "%", "critical_low": 1.5, "critical_high": 10.0, "improvement_months": 36},
        "nitrogen_ppm": {"min": 20.0, "max": 40.0, "unit": "ppm", "critical_low": 10.0, "critical_high": 80.0, "improvement_months": 3},
        "phosphorus_ppm": {"min": 15.0, "max": 30.0, "unit": "ppm", "critical_low": 5.0, "critical_high": 60.0, "improvement_months": 3},
        "potassium_ppm": {"min": 100.0, "max": 200.0, "unit": "ppm", "critical_low": 50.0, "critical_high": 400.0, "improvement_months": 3},
        "calcium_ppm": {"min": 2000.0, "max": 4000.0, "unit": "ppm", "critical_low": 1000.0, "critical_high": 8000.0, "improvement_months": 6},
        "magnesium_ppm": {"min": 100.0, "max": 300.0, "unit": "ppm", "critical_low": 50.0, "critical_high": 600.0, "improvement_months": 6},
        "cec_meq": {"min": 10.0, "max": 25.0, "unit": "meq/100g", "critical_low": 5.0, "critical_high": 40.0, "improvement_months": 24}
    }

    # Crop-specific pH adjustments (some crops prefer different pH ranges)
    CROP_PH_ADJUSTMENTS = {
        "bleuets": {"min": 4.5, "max": 5.5},  # Acidic soil
        "myrtilles": {"min": 4.5, "max": 5.5},  # Acidic soil
        "pomme de terre": {"min": 5.5, "max": 6.5},  # Slightly acidic (scab prevention)
        "luzerne": {"min": 6.5, "max": 7.5},  # Neutral to alkaline
        "blé": {"min": 6.0, "max": 7.0},  # Standard
        "maïs": {"min": 6.0, "max": 7.0},  # Standard
        "soja": {"min": 6.0, "max": 7.0},  # Standard
        "tournesol": {"min": 6.0, "max": 7.5},  # Tolerant
    }
    
    @redis_cache(ttl=7200, model_class=SoilHealthOutput, category="sustainability")
    async def analyze_soil_health(self, input_data: SoilHealthInput) -> SoilHealthOutput:
        """
        Analyze soil health from provided indicators.
        
        Args:
            input_data: Validated input with soil indicators
            
        Returns:
            SoilHealthOutput with scores, status, and recommendations
            
        Raises:
            ValueError: If no indicators provided or analysis fails
        """
        try:
            # Collect all provided indicators
            indicators_data = {}
            if input_data.ph is not None:
                indicators_data["ph"] = input_data.ph
            if input_data.organic_matter_percent is not None:
                indicators_data["organic_matter_percent"] = input_data.organic_matter_percent
            if input_data.nitrogen_ppm is not None:
                indicators_data["nitrogen_ppm"] = input_data.nitrogen_ppm
            if input_data.phosphorus_ppm is not None:
                indicators_data["phosphorus_ppm"] = input_data.phosphorus_ppm
            if input_data.potassium_ppm is not None:
                indicators_data["potassium_ppm"] = input_data.potassium_ppm
            if input_data.calcium_ppm is not None:
                indicators_data["calcium_ppm"] = input_data.calcium_ppm
            if input_data.magnesium_ppm is not None:
                indicators_data["magnesium_ppm"] = input_data.magnesium_ppm
            if input_data.cec_meq is not None:
                indicators_data["cec_meq"] = input_data.cec_meq
            
            if not indicators_data:
                raise ValueError("Au moins un indicateur de sol doit être fourni")
            
            # Analyze each indicator
            analyzed_indicators = []
            critical_issues = []
            total_score = 0.0
            
            for indicator_name, current_value in indicators_data.items():
                optimal = self.OPTIMAL_RANGES[indicator_name].copy()

                # Apply crop-specific pH adjustments if applicable
                if indicator_name == "ph" and input_data.crop:
                    crop_lower = input_data.crop.lower()
                    if crop_lower in self.CROP_PH_ADJUSTMENTS:
                        optimal["min"] = self.CROP_PH_ADJUSTMENTS[crop_lower]["min"]
                        optimal["max"] = self.CROP_PH_ADJUSTMENTS[crop_lower]["max"]

                # Determine status and score
                status, score, deviation = self._evaluate_indicator(
                    current_value,
                    optimal["min"],
                    optimal["max"],
                    optimal["critical_low"],
                    optimal["critical_high"]
                )
                
                total_score += score
                
                analyzed_indicators.append(SoilIndicator(
                    indicator_name=indicator_name.replace("_", " ").title(),
                    current_value=round(current_value, 2),
                    optimal_min=optimal["min"],
                    optimal_max=optimal["max"],
                    unit=optimal["unit"],
                    status=status,
                    deviation_percent=round(deviation, 1) if deviation else None
                ))
                
                # Track critical issues
                if status == SoilHealthStatus.CRITICAL:
                    critical_issues.append(
                        f"🚨 {indicator_name.replace('_', ' ').title()}: {current_value} {optimal['unit']} "
                        f"(optimal: {optimal['min']}-{optimal['max']}) - Action urgente requise"
                    )
                elif status == SoilHealthStatus.POOR:
                    critical_issues.append(
                        f"⚠️ {indicator_name.replace('_', ' ').title()}: {current_value} {optimal['unit']} "
                        f"(optimal: {optimal['min']}-{optimal['max']}) - Amélioration nécessaire"
                    )
            
            # Calculate overall score (0-10 scale)
            overall_score = (total_score / len(indicators_data)) * 10
            overall_status = self._determine_overall_status(overall_score)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                analyzed_indicators,
                input_data.crop,
                input_data.location
            )

            # Estimate improvement time (based on worst indicator)
            improvement_time = self._estimate_improvement_time(analyzed_indicators, overall_status)
            
            logger.info(
                f"✅ Soil health analyzed: {len(indicators_data)} indicators, "
                f"score {overall_score:.1f}/10 ({overall_status.value})"
            )
            
            return SoilHealthOutput(
                success=True,
                overall_score=round(overall_score, 1),
                overall_status=overall_status,
                indicators_analyzed=analyzed_indicators,
                total_indicators=len(analyzed_indicators),
                critical_issues=critical_issues,
                improvement_recommendations=recommendations,
                estimated_improvement_time_months=improvement_time
            )
            
        except Exception as e:
            logger.error(f"Soil health analysis error: {e}", exc_info=True)
            raise ValueError(f"Erreur lors de l'analyse de la santé du sol: {str(e)}")
    
    def _evaluate_indicator(
        self,
        value: float,
        optimal_min: float,
        optimal_max: float,
        critical_low: float,
        critical_high: float
    ) -> tuple[SoilHealthStatus, float, Optional[float]]:
        """
        Evaluate single indicator.
        
        Returns: (status, score 0-1, deviation_percent)
        """
        # Check if in optimal range
        if optimal_min <= value <= optimal_max:
            return SoilHealthStatus.OPTIMAL, 1.0, 0.0
        
        # Check if critical
        if value < critical_low or value > critical_high:
            deviation = self._calculate_deviation(value, optimal_min, optimal_max)
            return SoilHealthStatus.CRITICAL, 0.2, deviation
        
        # Check if poor
        if value < optimal_min * 0.8 or value > optimal_max * 1.2:
            deviation = self._calculate_deviation(value, optimal_min, optimal_max)
            return SoilHealthStatus.POOR, 0.4, deviation
        
        # Check if moderate
        if value < optimal_min or value > optimal_max:
            deviation = self._calculate_deviation(value, optimal_min, optimal_max)
            return SoilHealthStatus.MODERATE, 0.7, deviation
        
        # Good (close to optimal)
        deviation = self._calculate_deviation(value, optimal_min, optimal_max)
        return SoilHealthStatus.GOOD, 0.9, deviation
    
    def _calculate_deviation(self, value: float, optimal_min: float, optimal_max: float) -> float:
        """Calculate % deviation from optimal range"""
        optimal_mid = (optimal_min + optimal_max) / 2
        return ((value - optimal_mid) / optimal_mid) * 100
    
    def _determine_overall_status(self, score: float) -> SoilHealthStatus:
        """Determine overall status from score (0-10)"""
        if score >= 9.0:
            return SoilHealthStatus.OPTIMAL
        elif score >= 7.0:
            return SoilHealthStatus.GOOD
        elif score >= 5.0:
            return SoilHealthStatus.MODERATE
        elif score >= 3.0:
            return SoilHealthStatus.POOR
        else:
            return SoilHealthStatus.CRITICAL
    
    def _generate_recommendations(
        self,
        indicators: List[SoilIndicator],
        crop: Optional[str],
        location: Optional[str]
    ) -> List[str]:
        """Generate prioritized improvement recommendations"""
        recommendations = []

        # Critical and poor indicators first
        for indicator in indicators:
            if indicator.status == SoilHealthStatus.CRITICAL:
                recommendations.extend(self._get_indicator_recommendations(indicator, urgent=True))
            elif indicator.status == SoilHealthStatus.POOR:
                recommendations.extend(self._get_indicator_recommendations(indicator, urgent=False))

        # Add improvement time disclaimer
        if any(ind.status in [SoilHealthStatus.CRITICAL, SoilHealthStatus.POOR] for ind in indicators):
            recommendations.append(
                "⏱️ Temps d'amélioration variable: pH 3-6 mois, Nutriments 1 saison, Matière organique 3-5 ans"
            )

        # General recommendations
        if crop:
            recommendations.append(f"📊 Adapter fertilisation aux besoins spécifiques de {crop}")

        if location:
            recommendations.append(f"� Consulter Chambre d'Agriculture de {location} pour recommandations locales")

        recommendations.append("�🔬 Effectuer analyse de sol complète tous les 3-5 ans")
        recommendations.append("♻️ Maintenir apports organiques réguliers (compost, fumier)")
        recommendations.append("🌱 Pratiquer rotation des cultures pour équilibre nutritif")

        return recommendations[:12]  # Limit to top 12
    
    def _get_indicator_recommendations(self, indicator: SoilIndicator, urgent: bool) -> List[str]:
        """Get specific recommendations for an indicator"""
        recommendations = []
        prefix = "🚨 URGENT:" if urgent else "⚠️"
        
        name_lower = indicator.indicator_name.lower()
        
        if "ph" in name_lower:
            if indicator.current_value < indicator.optimal_min:
                recommendations.append(f"{prefix} pH trop acide - Chaulage recommandé (2-4 t/ha)")
            else:
                recommendations.append(f"{prefix} pH trop basique - Apports organiques et soufre")
        
        elif "organic matter" in name_lower or "matière" in name_lower:
            recommendations.append(f"{prefix} Augmenter matière organique - Compost 20-30 t/ha ou engrais vert")
        
        elif "nitrogen" in name_lower or "azote" in name_lower:
            if indicator.current_value < indicator.optimal_min:
                recommendations.append(f"{prefix} Carence azote - Engrais azoté ou légumineuses en rotation")
        
        elif "phosphorus" in name_lower or "phosphore" in name_lower:
            if indicator.current_value < indicator.optimal_min:
                recommendations.append(f"{prefix} Carence phosphore - Engrais phosphaté ou compost")
        
        elif "potassium" in name_lower or "potasse" in name_lower:
            if indicator.current_value < indicator.optimal_min:
                recommendations.append(f"{prefix} Carence potassium - Engrais potassique ou cendres de bois")
        
        return recommendations
    
    def _estimate_improvement_time(
        self,
        indicators: List[SoilIndicator],
        status: SoilHealthStatus
    ) -> int:
        """
        Estimate months to reach good status based on worst indicator.

        Different indicators improve at different rates:
        - pH: 3-6 months (lime application)
        - Nutrients (NPK): 3 months (1 growing season)
        - Calcium/Magnesium: 6 months
        - Organic matter: 36 months (3-5 years, very slow)
        - CEC: 24 months (depends on organic matter)
        """
        if status == SoilHealthStatus.OPTIMAL or status == SoilHealthStatus.GOOD:
            return 0

        # Find worst indicator and use its improvement time
        max_improvement_time = 0
        for indicator in indicators:
            if indicator.status in [SoilHealthStatus.CRITICAL, SoilHealthStatus.POOR, SoilHealthStatus.MODERATE]:
                # Extract indicator name to match with OPTIMAL_RANGES
                indicator_key = indicator.indicator_name.lower().replace(" ", "_")
                if indicator_key in self.OPTIMAL_RANGES:
                    improvement_time = self.OPTIMAL_RANGES[indicator_key].get("improvement_months", 12)
                    max_improvement_time = max(max_improvement_time, improvement_time)

        # If no specific time found, use status-based estimate
        if max_improvement_time == 0:
            if status == SoilHealthStatus.MODERATE:
                return 6
            elif status == SoilHealthStatus.POOR:
                return 12
            else:  # CRITICAL
                return 24

        return max_improvement_time


async def analyze_soil_health(
    ph: Optional[float] = None,
    organic_matter_percent: Optional[float] = None,
    nitrogen_ppm: Optional[float] = None,
    phosphorus_ppm: Optional[float] = None,
    potassium_ppm: Optional[float] = None,
    calcium_ppm: Optional[float] = None,
    magnesium_ppm: Optional[float] = None,
    cec_meq: Optional[float] = None,
    crop: Optional[str] = None,
    location: Optional[str] = None
) -> str:
    """
    Async wrapper for analyze soil health tool
    
    Args:
        ph: Soil pH (3.0-10.0)
        organic_matter_percent: Organic matter percentage (0-100)
        nitrogen_ppm: Nitrogen in ppm
        phosphorus_ppm: Phosphorus in ppm
        potassium_ppm: Potassium in ppm
        calcium_ppm: Calcium in ppm (optional)
        magnesium_ppm: Magnesium in ppm (optional)
        cec_meq: Cation exchange capacity in meq/100g (optional)
        crop: Current or planned crop (optional)
        location: Location for regional recommendations (optional)
        
    Returns:
        JSON string with soil health analysis
    """
    try:
        # Validate inputs
        input_data = SoilHealthInput(
            ph=ph,
            organic_matter_percent=organic_matter_percent,
            nitrogen_ppm=nitrogen_ppm,
            phosphorus_ppm=phosphorus_ppm,
            potassium_ppm=potassium_ppm,
            calcium_ppm=calcium_ppm,
            magnesium_ppm=magnesium_ppm,
            cec_meq=cec_meq,
            crop=crop,
            location=location
        )
        
        # Execute service
        service = SoilHealthService()
        result = await service.analyze_soil_health(input_data)
        
        return result.model_dump_json(indent=2, exclude_none=True)
        
    except ValueError as e:
        # Validation or business logic error
        error_result = SoilHealthOutput(
            success=False,
            overall_score=0.0,
            overall_status=SoilHealthStatus.CRITICAL,
            total_indicators=0,
            error=str(e),
            error_type="validation"
        )
        return error_result.model_dump_json(indent=2)
    except Exception as e:
        # Unexpected error
        logger.error(f"Unexpected error in analyze_soil_health: {e}", exc_info=True)
        error_result = SoilHealthOutput(
            success=False,
            overall_score=0.0,
            overall_status=SoilHealthStatus.CRITICAL,
            total_indicators=0,
            error=f"Erreur inattendue: {str(e)}",
            error_type="unknown"
        )
        return error_result.model_dump_json(indent=2)


# Create the StructuredTool
analyze_soil_health_tool = StructuredTool.from_function(
    func=analyze_soil_health,
    name="analyze_soil_health",
    description="""Analyse la santé du sol à partir d'indicateurs mesurés.

Indicateurs analysés (au moins un requis):
- pH du sol (6.0-7.5 optimal)
- Matière organique (3-6% optimal)
- Azote (N), Phosphore (P), Potassium (K)
- Calcium, Magnésium (optionnels)
- CEC - Capacité d'échange cationique (optionnel)

Analyse fournie:
- Score global de santé du sol (0-10)
- Statut de chaque indicateur (optimal/bon/modéré/faible/critique)
- Problèmes critiques identifiés
- Recommandations d'amélioration priorisées
- Estimation du temps d'amélioration

Basé sur standards agronomiques français.
Recommandations adaptées à la culture si spécifiée.

Retourne analyse détaillée avec actions concrètes.""",
    args_schema=SoilHealthInput,
    return_direct=False,
    coroutine=analyze_soil_health,
    handle_validation_error=True
)

