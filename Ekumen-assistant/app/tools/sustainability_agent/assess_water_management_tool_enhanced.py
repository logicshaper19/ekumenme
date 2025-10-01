"""
Enhanced Assess Water Management Tool.

Improvements:
- Type-safe Pydantic schemas
- Redis caching (2h TTL for water management assessments)
- Multiple water efficiency indicators
- Research-based irrigation efficiency standards
- Crop-specific water requirements
- Actionable improvement recommendations
"""

import logging
from typing import Optional, List
from langchain.tools import StructuredTool

from app.tools.schemas.sustainability_schemas import (
    WaterManagementInput,
    WaterManagementOutput,
    WaterIndicatorScore,
    WaterManagementIndicator
)
from app.core.cache import redis_cache

logger = logging.getLogger(__name__)


class EnhancedWaterManagementService:
    """
    Service for assessing agricultural water management with caching.
    
    Features:
    - Multiple water efficiency indicators
    - Irrigation system efficiency (drip, sprinkler, flood, pivot)
    - Crop-specific water requirements
    - Water savings potential calculation
    - Prioritized recommendations
    
    Cache Strategy:
    - TTL: 2 hours (7200s) - irrigation systems change slowly
    - Category: sustainability
    - Keys include all indicators
    
    Water Efficiency Standards:
    - Drip irrigation: 90-95% efficiency (best)
    - Center pivot: 85-90% efficiency (good)
    - Sprinkler: 75-85% efficiency (moderate)
    - Flood/furrow: 50-70% efficiency (poor)
    
    Water Usage Benchmarks (m³/ha/year, temperate climate):
    - Wheat: 1,500-3,000 m³/ha
    - Corn: 4,000-6,000 m³/ha
    - Vegetables: 3,000-5,000 m³/ha
    - Orchards: 2,000-4,000 m³/ha
    """
    
    # Irrigation system efficiency ranges (%)
    IRRIGATION_EFFICIENCY = {
        "drip": {"min": 90, "max": 95, "typical": 92},
        "goutte-à-goutte": {"min": 90, "max": 95, "typical": 92},  # French
        "sprinkler": {"min": 75, "max": 85, "typical": 80},
        "aspersion": {"min": 75, "max": 85, "typical": 80},  # French
        "flood": {"min": 50, "max": 70, "typical": 60},
        "gravitaire": {"min": 50, "max": 70, "typical": 60},  # French
        "submersion": {"min": 50, "max": 70, "typical": 60},  # French
        "center_pivot": {"min": 85, "max": 90, "typical": 87},
        "pivot": {"min": 85, "max": 90, "typical": 87},  # French
        "pivot_central": {"min": 85, "max": 90, "typical": 87},  # French
    }
    
    # Crop water requirements (m³/ha/year, temperate climate)
    CROP_WATER_REQUIREMENTS = {
        "blé": {"min": 1500, "max": 3000, "optimal": 2200},
        "maïs": {"min": 4000, "max": 6000, "optimal": 5000},
        "tournesol": {"min": 2000, "max": 3500, "optimal": 2800},
        "soja": {"min": 3000, "max": 4500, "optimal": 3800},
        "pomme de terre": {"min": 3000, "max": 5000, "optimal": 4000},
        "tomate": {"min": 4000, "max": 6000, "optimal": 5000},
        "vigne": {"min": 1000, "max": 2500, "optimal": 1800},
    }
    
    @redis_cache(ttl=7200, model_class=WaterManagementOutput, category="sustainability")
    async def assess_water_management(self, input_data: WaterManagementInput) -> WaterManagementOutput:
        """
        Assess farm water management efficiency.
        
        Args:
            input_data: Validated input with water management data
            
        Returns:
            WaterManagementOutput with efficiency scores and recommendations
            
        Raises:
            ValueError: If assessment fails
        """
        try:
            indicator_scores = []

            # Calculate irrigation system efficiency
            irrigation_score = self._score_irrigation_system(
                input_data.irrigation_method
            )
            indicator_scores.append(irrigation_score)

            # Calculate water usage efficiency (if data available)
            if input_data.annual_water_usage_m3:
                usage_score = self._score_water_usage(
                    input_data.annual_water_usage_m3,
                    input_data.surface_ha,
                    input_data.crop
                )
                indicator_scores.append(usage_score)

            # Calculate water conservation practices
            conservation_score = self._score_conservation_practices(
                input_data.soil_moisture_monitoring,
                input_data.weather_based_irrigation,
                False,  # rainwater_harvesting not in schema
                input_data.mulching_used
            )
            indicator_scores.append(conservation_score)

            # Overall efficiency score (weighted average)
            # Weighting rationale:
            # - System efficiency: 40% (foundational - bad system = 30-50% losses)
            # - Usage optimization: 35% (direct consumption impact)
            # - Conservation: 25% (supplementary practices)
            if input_data.annual_water_usage_m3:
                overall_score = (
                    irrigation_score.score * 0.4 +  # 40% weight
                    usage_score.score * 0.35 +      # 35% weight
                    conservation_score.score * 0.25  # 25% weight
                )
            else:
                # No usage data - weight irrigation and conservation only
                overall_score = (
                    irrigation_score.score * 0.6 +  # 60% weight
                    conservation_score.score * 0.4  # 40% weight
                )

            overall_status = self._determine_status(overall_score)

            # Calculate water savings potential
            savings_potential = self._calculate_savings_potential(
                input_data,
                irrigation_score,
                conservation_score
            )

            # Generate recommendations
            recommendations = self._generate_recommendations(
                input_data,
                irrigation_score,
                indicator_scores[1] if len(indicator_scores) > 1 else irrigation_score,
                conservation_score
            )

            # Calculate water use efficiency (m³/ha)
            water_use_efficiency = None
            if input_data.annual_water_usage_m3:
                water_use_efficiency = input_data.annual_water_usage_m3 / input_data.surface_ha

            logger.info(
                f"✅ Water management assessed: {input_data.surface_ha} ha, "
                f"score {overall_score:.1f}/10 ({overall_status})"
            )

            return WaterManagementOutput(
                success=True,
                surface_ha=input_data.surface_ha,
                crop=input_data.crop,
                overall_water_score=round(overall_score, 1),
                overall_status=overall_status,
                indicator_scores=indicator_scores,
                water_use_efficiency=round(water_use_efficiency, 1) if water_use_efficiency else None,
                estimated_water_savings_potential_m3=round(savings_potential, 0) if savings_potential > 0 else None,
                improvement_recommendations=recommendations,
                critical_issues=[]  # Could add critical issues logic later
            )
            
        except Exception as e:
            logger.error(f"Water management assessment error: {e}", exc_info=True)
            raise ValueError(f"Erreur lors de l'évaluation de la gestion de l'eau: {str(e)}")
    
    def _score_irrigation_system(self, system: Optional[str]) -> WaterIndicatorScore:
        """
        Score irrigation system efficiency.

        Based on FAO irrigation efficiency standards.
        """
        if not system:
            return WaterIndicatorScore(
                indicator=WaterManagementIndicator.IRRIGATION_EFFICIENCY,
                score=5.0,
                status="moderate",
                description="Système irrigation non spécifié - Score neutre"
            )

        system_lower = system.lower()
        efficiency_data = self.IRRIGATION_EFFICIENCY.get(system_lower)

        if not efficiency_data:
            # Unknown system - use moderate default
            return WaterIndicatorScore(
                indicator=WaterManagementIndicator.IRRIGATION_EFFICIENCY,
                score=6.0,
                status="moderate",
                description=f"Système '{system}' non reconnu - Score estimé"
            )

        typical_efficiency = efficiency_data["typical"]

        # Convert efficiency % to 0-10 score
        score = (typical_efficiency / 100.0) * 10.0

        # Determine status based on efficiency
        if typical_efficiency >= 90:
            status = "excellent"
            description = f"Irrigation goutte-à-goutte ({typical_efficiency}% efficacité) - Système optimal"
        elif typical_efficiency >= 85:
            status = "good"
            description = f"Pivot central ({typical_efficiency}% efficacité) - Bon système"
        elif typical_efficiency >= 75:
            status = "moderate"
            description = f"Aspersion ({typical_efficiency}% efficacité) - Système correct, amélioration possible"
        else:
            status = "poor"
            description = f"Gravitaire/submersion ({typical_efficiency}% efficacité) - Système peu efficace, upgrade recommandé"

        return WaterIndicatorScore(
            indicator=WaterManagementIndicator.IRRIGATION_EFFICIENCY,
            score=round(score, 1),
            status=status,
            description=description
        )
    
    def _score_water_usage(
        self,
        annual_usage_m3: float,
        surface_ha: float,
        crop: str
    ) -> WaterIndicatorScore:
        """
        Score water usage efficiency compared to crop requirements.
        
        LIMITATION: Uses temperate climate benchmarks. Actual requirements vary by:
        - Climate zone (Mediterranean vs Continental)
        - Soil type (sandy vs clay)
        - Rainfall distribution
        - Crop variety
        """
        usage_per_ha = annual_usage_m3 / surface_ha if surface_ha > 0 else 0
        
        crop_lower = crop.lower()
        if crop_lower in self.CROP_WATER_REQUIREMENTS:
            requirements = self.CROP_WATER_REQUIREMENTS[crop_lower]
            optimal = requirements["optimal"]
            max_acceptable = requirements["max"]
            
            # Calculate efficiency
            if usage_per_ha <= optimal:
                # Under or at optimal - excellent
                score = 10.0
                status = "excellent"
                description = f"Usage {usage_per_ha:.0f} m³/ha ≤ optimal {optimal} m³/ha pour {crop} - Excellent"
            elif usage_per_ha <= max_acceptable:
                # Between optimal and max - good
                excess_pct = ((usage_per_ha - optimal) / optimal) * 100
                score = max(7.0 - (excess_pct / 20), 5.0)  # Degrade from 7 to 5
                status = "good"
                description = f"Usage {usage_per_ha:.0f} m³/ha acceptable pour {crop} (+{excess_pct:.0f}% vs optimal)"
            elif usage_per_ha <= max_acceptable * 1.3:
                # 30% over max - moderate
                excess_pct = ((usage_per_ha - optimal) / optimal) * 100
                score = 4.0
                status = "moderate"
                description = f"Usage {usage_per_ha:.0f} m³/ha élevé pour {crop} (+{excess_pct:.0f}% vs optimal)"
            else:
                # Very high usage - poor
                excess_pct = ((usage_per_ha - optimal) / optimal) * 100
                score = 2.0
                status = "poor"
                description = f"Usage {usage_per_ha:.0f} m³/ha très élevé pour {crop} (+{excess_pct:.0f}% vs optimal)"
        else:
            # Unknown crop - use generic benchmark (3000 m³/ha)
            generic_optimal = 3000
            if usage_per_ha <= generic_optimal:
                score = 7.0
                status = "good"
                description = f"Usage {usage_per_ha:.0f} m³/ha (culture {crop} non référencée, benchmark générique)"
            else:
                excess_pct = ((usage_per_ha - generic_optimal) / generic_optimal) * 100
                score = max(5.0 - (excess_pct / 30), 2.0)
                status = "moderate"
                description = f"Usage {usage_per_ha:.0f} m³/ha (culture {crop} non référencée, +{excess_pct:.0f}% vs benchmark)"
        
        return WaterIndicatorScore(
            indicator=WaterManagementIndicator.WATER_CONSERVATION,
            score=round(score, 1),
            status=status,
            description=description
        )
    
    def _score_conservation_practices(
        self,
        sensors: bool,
        weather_scheduling: bool,
        rainwater: bool,
        mulching: bool
    ) -> WaterIndicatorScore:
        """
        Score water conservation practices.
        
        Each practice contributes to overall water efficiency:
        - Soil moisture sensors: 30% (most impactful)
        - Weather-based scheduling: 25%
        - Rainwater harvesting: 25%
        - Mulching: 20%
        """
        score = 0.0
        practices_used = []
        
        if sensors:
            score += 3.0
            practices_used.append("capteurs humidité sol")
        if weather_scheduling:
            score += 2.5
            practices_used.append("pilotage météo")
        if rainwater:
            score += 2.5
            practices_used.append("récupération eau pluie")
        if mulching:
            score += 2.0
            practices_used.append("paillage")
        
        count = len(practices_used)
        
        if count >= 3:
            status = "excellent"
            description = f"{count}/4 pratiques conservation: {', '.join(practices_used)} - Excellent"
        elif count >= 2:
            status = "good"
            description = f"{count}/4 pratiques conservation: {', '.join(practices_used)} - Bon"
        elif count >= 1:
            status = "moderate"
            description = f"{count}/4 pratiques conservation: {', '.join(practices_used)} - Amélioration possible"
        else:
            status = "poor"
            description = "0/4 pratiques conservation - Aucune pratique identifiée"
        
        return WaterIndicatorScore(
            indicator=WaterManagementIndicator.WATER_CONSERVATION,
            score=round(score, 1),
            status=status,
            description=description
        )
    
    def _determine_status(self, score: float) -> str:
        """Determine overall status from score"""
        if score >= 8.0:
            return "excellent"
        elif score >= 6.0:
            return "good"
        elif score >= 4.0:
            return "moderate"
        else:
            return "poor"
    
    def _calculate_savings_potential(
        self,
        input_data: WaterManagementInput,
        irrigation_score: WaterIndicatorScore,
        conservation_score: WaterIndicatorScore
    ) -> float:
        """
        Calculate potential water savings (m³/year) if recommendations implemented.

        IMPORTANT: Savings are compounded (applied sequentially), not additive.
        Each practice saves a percentage of the REMAINING usage after previous savings.

        Weighting rationale:
        - System efficiency: 40% (foundational - bad system = 30-50% losses)
        - Usage optimization: 35% (direct consumption impact)
        - Conservation: 25% (supplementary practices)

        Savings potential (applied in order of impact):
        - Upgrade to drip: 20-40% savings vs flood/sprinkler
        - Add sensors: 15-25% savings (of remaining)
        - Weather scheduling: 10-20% savings (of remaining)
        - Mulching: 10-20% savings (of remaining)
        - Rainwater harvesting: 5-15% savings (of remaining)
        """
        if not input_data.annual_water_usage_m3:
            return 0.0

        remaining_usage = input_data.annual_water_usage_m3
        total_savings = 0.0

        # 1. Irrigation system upgrade potential (highest impact first)
        if input_data.irrigation_method:
            system_lower = input_data.irrigation_method.lower()
            if system_lower in ["flood", "gravitaire", "submersion"]:
                # Upgrade to drip could save 30-40%
                savings = remaining_usage * 0.35
                total_savings += savings
                remaining_usage -= savings
            elif system_lower in ["sprinkler", "aspersion"]:
                # Upgrade to drip could save 15-20%
                savings = remaining_usage * 0.17
                total_savings += savings
                remaining_usage -= savings
            elif system_lower in ["center_pivot", "pivot", "pivot_central"]:
                # Upgrade to drip could save 5-10%
                savings = remaining_usage * 0.07
                total_savings += savings
                remaining_usage -= savings

        # 2. Conservation practices (applied to remaining usage after system upgrade)
        if not input_data.soil_moisture_monitoring:
            # Sensors: 20% of remaining
            savings = remaining_usage * 0.20
            total_savings += savings
            remaining_usage -= savings

        if not input_data.weather_based_irrigation:
            # Weather scheduling: 15% of remaining
            savings = remaining_usage * 0.15
            total_savings += savings
            remaining_usage -= savings

        if not input_data.mulching_used:
            # Mulching: 15% of remaining
            savings = remaining_usage * 0.15
            total_savings += savings
            remaining_usage -= savings

        # Note: rainwater_harvesting not in schema, skipping

        return total_savings
    
    def _generate_recommendations(
        self,
        input_data: WaterManagementInput,
        irrigation_score: WaterIndicatorScore,
        usage_score: WaterIndicatorScore,
        conservation_score: WaterIndicatorScore
    ) -> List[str]:
        """Generate prioritized water management recommendations"""
        recommendations = []

        # Irrigation system recommendations
        if input_data.irrigation_method:
            system_lower = input_data.irrigation_method.lower()
            if system_lower in ["flood", "gravitaire", "submersion"]:
                recommendations.append(
                    "💧 PRIORITÉ 1: Upgrade système irrigation gravitaire → goutte-à-goutte "
                    "(économie 30-40%, ROI 3-5 ans)"
                )
            elif system_lower in ["sprinkler", "aspersion"]:
                recommendations.append(
                    "💧 Considérer upgrade aspersion → goutte-à-goutte "
                    "(économie 15-20%, meilleure uniformité)"
                )

        # Conservation practices recommendations
        if not input_data.soil_moisture_monitoring:
            recommendations.append(
                "📊 PRIORITÉ 2: Installer capteurs humidité sol "
                "(économie 15-25%, irrigation précise selon besoins réels)"
            )

        if not input_data.weather_based_irrigation:
            recommendations.append(
                "🌦️ Implémenter pilotage irrigation météo "
                "(économie 10-20%, éviter irrigation avant pluie)"
            )

        if not input_data.mulching_used:
            recommendations.append(
                "🌾 Utiliser paillage/mulch "
                "(économie 10-20%, réduit évaporation, améliore sol)"
            )
        
        # Usage-based recommendations
        if usage_score.score < 6.0:
            recommendations.append(
                "⚠️ Usage eau élevé - Audit irrigation recommandé "
                "(fuites, uniformité, durées)"
            )
        
        # General recommendations
        recommendations.append("📅 Planifier irrigation selon stades phénologiques (besoins variables)")
        recommendations.append("🔧 Entretien régulier système (fuites = 10-30% pertes)")
        
        return recommendations[:8]  # Limit to top 8


async def assess_water_management_enhanced(
    surface_ha: float,
    crop: str,
    irrigated: bool = False,
    irrigation_method: Optional[str] = None,
    annual_water_usage_m3: Optional[float] = None,
    soil_moisture_monitoring: bool = False,
    weather_based_irrigation: bool = False,
    mulching_used: bool = False,
    cover_crops_for_water: bool = False,
    drainage_system: bool = False,
    buffer_strips: bool = False,
    contour_farming: bool = False,
    location: Optional[str] = None,
    rainfall_mm_annual: Optional[float] = None
) -> str:
    """
    Async wrapper for assess water management tool

    Args:
        surface_ha: Surface area in hectares
        crop: Crop type
        irrigated: Whether the field is irrigated
        irrigation_method: Type of irrigation (drip, sprinkler, flood, pivot, etc.)
        annual_water_usage_m3: Annual water usage in cubic meters (optional)
        soil_moisture_monitoring: Whether soil moisture sensors are used
        weather_based_irrigation: Whether weather-based irrigation scheduling is used
        mulching_used: Whether mulching is used
        cover_crops_for_water: Whether cover crops are used for water management
        drainage_system: Whether drainage system is present
        buffer_strips: Whether buffer strips are used
        contour_farming: Whether contour farming is practiced
        location: Location for regional context (optional)
        rainfall_mm_annual: Annual rainfall in mm (optional)

    Returns:
        JSON string with water management assessment

    LIMITATION: Water requirements based on temperate climate.
    Mediterranean: +50%, Oceanic: -30%, Arid: irrigation essential.
    """
    try:
        # Validate inputs
        input_data = WaterManagementInput(
            surface_ha=surface_ha,
            crop=crop,
            irrigated=irrigated,
            irrigation_method=irrigation_method,
            annual_water_usage_m3=annual_water_usage_m3,
            soil_moisture_monitoring=soil_moisture_monitoring,
            weather_based_irrigation=weather_based_irrigation,
            mulching_used=mulching_used,
            cover_crops_for_water=cover_crops_for_water,
            drainage_system=drainage_system,
            buffer_strips=buffer_strips,
            contour_farming=contour_farming,
            location=location,
            rainfall_mm_annual=rainfall_mm_annual
        )
        
        # Execute service
        service = EnhancedWaterManagementService()
        result = await service.assess_water_management(input_data)
        
        return result.model_dump_json(indent=2, exclude_none=True)
        
    except ValueError as e:
        # Validation or business logic error
        error_result = WaterManagementOutput(
            success=False,
            surface_ha=surface_ha,
            crop=crop,
            overall_water_score=0.0,
            overall_status="poor",
            error=str(e),
            error_type="validation"
        )
        return error_result.model_dump_json(indent=2)
    except Exception as e:
        # Unexpected error
        logger.error(f"Unexpected error in assess_water_management_enhanced: {e}", exc_info=True)
        error_result = WaterManagementOutput(
            success=False,
            surface_ha=surface_ha,
            crop=crop,
            overall_water_score=0.0,
            overall_status="poor",
            error=f"Erreur inattendue: {str(e)}",
            error_type="unknown"
        )
        return error_result.model_dump_json(indent=2)


# Create the StructuredTool
assess_water_management_tool_enhanced = StructuredTool.from_function(
    func=assess_water_management_enhanced,
    name="assess_water_management",
    description="""Évalue l'efficacité de la gestion de l'eau agricole.

Analyse 3 dimensions:
1. Système irrigation (efficacité %)
   - Goutte-à-goutte: 90-95% (optimal)
   - Pivot central: 85-90% (bon)
   - Aspersion: 75-85% (correct)
   - Gravitaire: 50-70% (faible)

2. Usage eau (m³/ha vs besoins culture)
   - Compare usage réel aux besoins optimaux
   - Identifie sur-irrigation
   - Benchmarks par culture

3. Pratiques conservation
   - Capteurs humidité sol (20% économie)
   - Pilotage météo (15% économie)
   - Récupération eau pluie (10% économie)
   - Paillage (15% économie)

Retourne:
- Score efficacité global (0-10)
- Scores par dimension
- Potentiel économie eau (m³/an)
- Recommandations priorisées avec ROI

LIMITATION: Benchmarks climat tempéré. Ajuster selon zone climatique.

Aide optimiser ressource eau, réduire coûts, améliorer durabilité.""",
    args_schema=WaterManagementInput,
    return_direct=False,
    coroutine=assess_water_management_enhanced,
    handle_validation_error=True
)

