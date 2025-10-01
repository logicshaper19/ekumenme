"""
Enhanced Assess Biodiversity Tool.

Improvements:
- Type-safe Pydantic schemas
- Redis caching (2h TTL for biodiversity assessments)
- Multiple biodiversity indicators (rotation, margins, hedgerows, etc.)
- Scoring based on agricultural biodiversity research
- Actionable improvement recommendations
- Potential score calculation
"""

import logging
from typing import Optional, List
from langchain.tools import StructuredTool

from app.tools.schemas.sustainability_schemas import (
    BiodiversityInput,
    BiodiversityOutput,
    BiodiversityScore,
    BiodiversityIndicator
)
from app.core.cache import redis_cache

logger = logging.getLogger(__name__)


class EnhancedBiodiversityService:
    """
    Service for assessing agricultural biodiversity with caching.
    
    Features:
    - Multiple biodiversity indicators (7 total)
    - Research-based scoring (0-10 scale)
    - Identifies strengths and weaknesses
    - Calculates improvement potential
    - Prioritized recommendations
    
    Cache Strategy:
    - TTL: 2 hours (7200s) - farm features change slowly
    - Category: sustainability
    - Keys include all indicators
    
    Biodiversity Indicators (based on French agricultural biodiversity research):
    1. Crop rotation diversity (1-20 crops, 1-10 years)
    2. Field margins (0-100% of field perimeter)
    3. Hedgerows (linear meters per hectare)
    4. Water features (ponds, streams, wetlands)
    5. Organic practices (certified organic)
    6. Pesticide use intensity (applications per year)
    7. Cover crops (soil cover between main crops)
    """
    
    @redis_cache(ttl=7200, model_class=BiodiversityOutput, category="sustainability")
    async def assess_biodiversity(self, input_data: BiodiversityInput) -> BiodiversityOutput:
        """
        Assess farm biodiversity from multiple indicators.
        
        Args:
            input_data: Validated input with biodiversity indicators
            
        Returns:
            BiodiversityOutput with scores, strengths, weaknesses, and recommendations
            
        Raises:
            ValueError: If assessment fails
        """
        try:
            indicator_scores = []
            
            # 1. Crop Rotation Diversity
            rotation_score = self._score_crop_rotation(
                input_data.crops_in_rotation,
                input_data.rotation_years
            )
            indicator_scores.append(rotation_score)
            
            # 2. Field Margins
            margin_score = self._score_field_margins(
                input_data.field_margin_percent
            )
            indicator_scores.append(margin_score)
            
            # 3. Hedgerows
            hedgerow_score = self._score_hedgerows(
                input_data.hedgerow_length_m,
                input_data.surface_ha
            )
            indicator_scores.append(hedgerow_score)
            
            # 4. Water Features
            water_score = self._score_water_features(
                input_data.water_features
            )
            indicator_scores.append(water_score)
            
            # 5. Organic Practices
            organic_score = self._score_organic_practices(
                input_data.organic_certified
            )
            indicator_scores.append(organic_score)
            
            # 6. Pesticide Use
            pesticide_score = self._score_pesticide_use(
                input_data.pesticide_applications_per_year
            )
            indicator_scores.append(pesticide_score)
            
            # 7. Cover Crops
            cover_crop_score = self._score_cover_crops(
                input_data.cover_crops_used
            )
            indicator_scores.append(cover_crop_score)
            
            # Calculate overall score
            overall_score = sum(s.score for s in indicator_scores) / len(indicator_scores)
            overall_status = self._determine_status(overall_score)
            
            # Identify strengths and weaknesses
            strengths = [
                f"✅ {s.indicator.value.replace('_', ' ').title()}: {s.score:.1f}/10 - {s.impact_description}"
                for s in indicator_scores if s.score >= 7.0
            ]
            
            weaknesses = [
                f"⚠️ {s.indicator.value.replace('_', ' ').title()}: {s.score:.1f}/10 - {s.impact_description}"
                for s in indicator_scores if s.score < 5.0
            ]
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                indicator_scores
            )
            
            # Calculate potential improvement
            potential_score = self._calculate_potential_score(
                indicator_scores
            )
            
            logger.info(
                f"✅ Biodiversity assessed: {input_data.surface_ha} ha, "
                f"score {overall_score:.1f}/10 ({overall_status})"
            )
            
            return BiodiversityOutput(
                success=True,
                surface_ha=input_data.surface_ha,
                overall_biodiversity_score=round(overall_score, 1),
                overall_status=overall_status,
                indicator_scores=indicator_scores,
                strengths=strengths,
                weaknesses=weaknesses,
                improvement_recommendations=recommendations,
                potential_score_improvement=round(potential_score - overall_score, 1)
            )
            
        except Exception as e:
            logger.error(f"Biodiversity assessment error: {e}", exc_info=True)
            raise ValueError(f"Erreur lors de l'évaluation de la biodiversité: {str(e)}")
    
    def _score_crop_rotation(self, crops: int, years: int) -> BiodiversityScore:
        """
        Score crop rotation diversity.

        Research shows:
        - 1-2 crops: monoculture/simple rotation (poor biodiversity)
        - 3-4 crops: moderate diversity
        - 5+ crops: good diversity
        - Longer rotations (4+ years) better than short

        Scoring: 70% crop diversity, 30% rotation duration
        """
        # Crop diversity component (70% weight, max 7 points)
        crop_component = min((crops / 5.0) * 7.0, 7.0)

        # Rotation duration component (30% weight, max 3 points)
        duration_component = min((years / 5.0) * 3.0, 3.0)

        # Combined score
        score = min(crop_component + duration_component, 10.0)

        if score >= 8:
            status = "excellent"
            description = f"Rotation diversifiée ({crops} cultures, {years} ans) - Excellent pour biodiversité"
        elif score >= 6:
            status = "good"
            description = f"Rotation correcte ({crops} cultures, {years} ans) - Bon pour biodiversité"
        elif score >= 4:
            status = "moderate"
            description = f"Rotation limitée ({crops} cultures, {years} ans) - Amélioration possible"
        else:
            status = "poor"
            description = f"Rotation faible ({crops} cultures, {years} ans) - Risque pour biodiversité"

        return BiodiversityScore(
            indicator=BiodiversityIndicator.CROP_ROTATION,
            score=round(score, 1),
            status=status,
            impact_description=description
        )
    
    def _score_field_margins(self, margin_percent: float) -> BiodiversityScore:
        """
        Score field margins.
        
        Field margins provide habitat for beneficial insects, birds, small mammals.
        Target: 5-10% of field perimeter
        """
        if margin_percent >= 10:
            score = 10.0
            status = "excellent"
            description = f"Bandes enherbées excellentes ({margin_percent}%) - Habitat riche"
        elif margin_percent >= 5:
            score = 7.0
            status = "good"
            description = f"Bandes enherbées bonnes ({margin_percent}%) - Habitat correct"
        elif margin_percent >= 2:
            score = 4.0
            status = "moderate"
            description = f"Bandes enherbées limitées ({margin_percent}%) - Habitat insuffisant"
        else:
            score = 1.0
            status = "poor"
            description = f"Bandes enherbées absentes/faibles ({margin_percent}%) - Pas d'habitat"
        
        return BiodiversityScore(
            indicator=BiodiversityIndicator.FIELD_MARGINS,
            score=round(score, 1),
            status=status,
            impact_description=description
        )
    
    def _score_hedgerows(self, length_m: float, surface_ha: float) -> BiodiversityScore:
        """
        Score hedgerows.
        
        Hedgerows are critical for biodiversity (birds, insects, small mammals).
        Target: 100+ m/ha (1 km per 10 ha)
        """
        length_per_ha = length_m / surface_ha if surface_ha > 0 else 0
        
        if length_per_ha >= 100:
            score = 10.0
            status = "excellent"
            description = f"Haies excellentes ({length_per_ha:.0f} m/ha) - Corridors écologiques"
        elif length_per_ha >= 50:
            score = 7.0
            status = "good"
            description = f"Haies bonnes ({length_per_ha:.0f} m/ha) - Bon réseau"
        elif length_per_ha >= 20:
            score = 4.0
            status = "moderate"
            description = f"Haies limitées ({length_per_ha:.0f} m/ha) - Réseau insuffisant"
        else:
            score = 1.0
            status = "poor"
            description = f"Haies absentes/faibles ({length_per_ha:.0f} m/ha) - Pas de corridors"
        
        return BiodiversityScore(
            indicator=BiodiversityIndicator.HEDGEROWS,
            score=round(score, 1),
            status=status,
            impact_description=description
        )
    
    def _score_water_features(self, has_water: bool) -> BiodiversityScore:
        """
        Score water features (ponds, streams, wetlands).

        LIMITATION: Binary scoring (yes/no). Actual biodiversity value varies:
        - Small pond vs large wetland
        - Drainage ditch vs natural stream
        - Single feature vs multiple features

        Future enhancement: water_feature_count, water_area_m2, buffer_width_m
        """
        if has_water:
            return BiodiversityScore(
                indicator=BiodiversityIndicator.WATER_FEATURES,
                score=10.0,
                status="excellent",
                impact_description="Points d'eau présents - Biodiversité aquatique et amphibiens (valeur réelle varie selon type/taille)"
            )
        else:
            return BiodiversityScore(
                indicator=BiodiversityIndicator.WATER_FEATURES,
                score=3.0,
                status="poor",
                impact_description="Pas de points d'eau - Biodiversité aquatique limitée"
            )
    
    def _score_organic_practices(self, is_organic: bool) -> BiodiversityScore:
        """
        Score organic certification.

        NOTE: Focuses on organic practices BEYOND pesticide use (already scored separately).
        Organic certification implies:
        - Organic fertilizers (compost, manure)
        - Biological pest control
        - Heritage/diverse varieties
        - Soil health focus

        Non-organic farms can still score well on pesticide use if they use IPM.
        """
        if is_organic:
            return BiodiversityScore(
                indicator=BiodiversityIndicator.ORGANIC_PRACTICES,
                score=10.0,
                status="excellent",
                impact_description="Agriculture biologique - Pratiques holistiques favorables biodiversité"
            )
        else:
            return BiodiversityScore(
                indicator=BiodiversityIndicator.ORGANIC_PRACTICES,
                score=5.0,
                status="moderate",
                impact_description="Agriculture conventionnelle - Pratiques biologiques possibles sans certification"
            )
    
    def _score_pesticide_use(self, applications: int) -> BiodiversityScore:
        """
        Score pesticide use intensity.

        Lower is better for biodiversity.
        Target: <5 applications/year (HVE level 3)

        LIMITATION: Scoring based on application count, not toxicity or type.
        Actual biodiversity impact varies significantly:
        - Herbicide vs broad-spectrum insecticide
        - Timing (flowering vs pre-emergence)
        - Application method (spot vs broadcast)

        This provides a rough proxy - fewer applications generally = less impact.
        """
        if applications == 0:
            score = 10.0
            status = "excellent"
            description = "Aucun pesticide - Excellent pour biodiversité"
        elif applications <= 3:
            score = 8.0
            status = "good"
            description = f"Usage pesticides faible ({applications}/an) - Bon pour biodiversité (impact réel varie selon type)"
        elif applications <= 6:
            score = 5.0
            status = "moderate"
            description = f"Usage pesticides modéré ({applications}/an) - Impact modéré (impact réel varie selon type)"
        elif applications <= 10:
            score = 3.0
            status = "poor"
            description = f"Usage pesticides élevé ({applications}/an) - Impact négatif"
        else:
            score = 1.0
            status = "poor"
            description = f"Usage pesticides très élevé ({applications}/an) - Impact fort"

        return BiodiversityScore(
            indicator=BiodiversityIndicator.PESTICIDE_USE,
            score=round(score, 1),
            status=status,
            impact_description=description
        )
    
    def _score_cover_crops(self, uses_cover: bool) -> BiodiversityScore:
        """Score cover crop usage"""
        if uses_cover:
            return BiodiversityScore(
                indicator=BiodiversityIndicator.HABITAT_DIVERSITY,
                score=9.0,
                status="excellent",
                impact_description="Couverts végétaux - Sol vivant et habitat continu"
            )
        else:
            return BiodiversityScore(
                indicator=BiodiversityIndicator.HABITAT_DIVERSITY,
                score=4.0,
                status="moderate",
                impact_description="Pas de couverts - Sol nu en hiver, habitat discontinu"
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
    
    def _generate_recommendations(
        self,
        scores: List[BiodiversityScore]
    ) -> List[str]:
        """Generate prioritized recommendations"""
        recommendations = []
        
        # Address weakest indicators first
        weak_indicators = sorted([s for s in scores if s.score < 6.0], key=lambda x: x.score)
        
        for indicator in weak_indicators[:3]:  # Top 3 weaknesses
            if indicator.indicator == BiodiversityIndicator.CROP_ROTATION:
                recommendations.append(
                    f"🌾 Diversifier rotation: Ajouter légumineuses, cultures de printemps/hiver, "
                    f"allonger cycle à 4-5 ans minimum"
                )
            elif indicator.indicator == BiodiversityIndicator.FIELD_MARGINS:
                recommendations.append(
                    "🌿 Implanter bandes enherbées: 5-10% périmètre parcelle, "
                    "mélange graminées/légumineuses/fleurs"
                )
            elif indicator.indicator == BiodiversityIndicator.HEDGEROWS:
                recommendations.append(
                    "🌳 Planter haies: Essences locales variées, 100+ m/ha, "
                    "créer corridors écologiques"
                )
            elif indicator.indicator == BiodiversityIndicator.PESTICIDE_USE:
                recommendations.append(
                    "🐛 Réduire pesticides: Lutte intégrée (IPM), seuils intervention, "
                    "auxiliaires, variétés résistantes"
                )
            elif indicator.indicator == BiodiversityIndicator.HABITAT_DIVERSITY:
                recommendations.append(
                    "🌱 Implanter couverts végétaux: Entre cultures principales, "
                    "mélange multi-espèces, maintenir sol vivant"
                )
        
        # General recommendations
        recommendations.append("🦋 Créer zones refuge: 2-5% surface non cultivée (jachères fleuries)")
        recommendations.append("💧 Protéger points d'eau: Bandes tampons, zones humides, mares")
        recommendations.append("📊 Suivre biodiversité: Comptages oiseaux, insectes, vers de terre")
        
        return recommendations[:8]  # Limit to top 8
    
    def _calculate_potential_score(
        self,
        scores: List[BiodiversityScore]
    ) -> float:
        """
        Calculate potential score if recommendations implemented.

        Improvement potential varies by indicator:
        - Cover crops: 80% (easy, one season)
        - Pesticide use: 60% (moderate, requires training/IPM)
        - Field margins: 70% (moderate, one season)
        - Crop rotation: 50% (takes years to implement)
        - Hedgerows: 30% (very slow, 5-10 years to mature)
        - Water features: 20% (often not feasible, expensive)
        - Organic practices: 40% (3-year transition period)
        """
        # Realistic improvement potential by indicator
        IMPROVEMENT_POTENTIAL = {
            BiodiversityIndicator.HABITAT_DIVERSITY: 0.8,  # Cover crops - easy
            BiodiversityIndicator.PESTICIDE_USE: 0.6,  # Moderate effort
            BiodiversityIndicator.FIELD_MARGINS: 0.7,  # Moderate, one season
            BiodiversityIndicator.CROP_ROTATION: 0.5,  # Takes years
            BiodiversityIndicator.HEDGEROWS: 0.3,  # Very slow
            BiodiversityIndicator.WATER_FEATURES: 0.2,  # Often not feasible
            BiodiversityIndicator.ORGANIC_PRACTICES: 0.4,  # 3-year transition
        }

        potential_scores = []

        for score in scores:
            if score.score < 7.0:
                # Use indicator-specific improvement potential
                improvement_rate = IMPROVEMENT_POTENTIAL.get(score.indicator, 0.5)
                potential = min(score.score + (10.0 - score.score) * improvement_rate, 10.0)
            else:
                # Already good, minor improvement
                potential = min(score.score + 0.5, 10.0)
            potential_scores.append(potential)

        return sum(potential_scores) / len(potential_scores)


async def assess_biodiversity_enhanced(
    surface_ha: float,
    crops_in_rotation: int,
    rotation_years: int,
    field_margin_percent: Optional[float] = 0.0,
    hedgerow_length_m: Optional[float] = 0.0,
    water_features: bool = False,
    organic_certified: bool = False,
    pesticide_applications_per_year: int = 0,
    cover_crops_used: bool = False,
    location: Optional[str] = None
) -> str:
    """
    Async wrapper for assess biodiversity tool
    
    Args:
        surface_ha: Surface area in hectares
        crops_in_rotation: Number of different crops in rotation (1-20)
        rotation_years: Rotation cycle length in years (1-10)
        field_margin_percent: Percentage of field with margins (0-100)
        hedgerow_length_m: Total hedgerow length in meters (optional)
        water_features: Presence of ponds, streams, wetlands
        organic_certified: Whether farm is organic certified
        pesticide_applications_per_year: Number of pesticide applications (0-50)
        cover_crops_used: Whether cover crops are used
        location: Location for regional context (optional)
        
    Returns:
        JSON string with biodiversity assessment
    """
    try:
        # Validate inputs
        input_data = BiodiversityInput(
            surface_ha=surface_ha,
            crops_in_rotation=crops_in_rotation,
            rotation_years=rotation_years,
            field_margin_percent=field_margin_percent,
            hedgerow_length_m=hedgerow_length_m,
            water_features=water_features,
            organic_certified=organic_certified,
            pesticide_applications_per_year=pesticide_applications_per_year,
            cover_crops_used=cover_crops_used,
            location=location
        )
        
        # Execute service
        service = EnhancedBiodiversityService()
        result = await service.assess_biodiversity(input_data)
        
        return result.model_dump_json(indent=2, exclude_none=True)
        
    except ValueError as e:
        # Validation or business logic error
        error_result = BiodiversityOutput(
            success=False,
            surface_ha=surface_ha,
            overall_biodiversity_score=0.0,
            overall_status="poor",
            error=str(e),
            error_type="validation"
        )
        return error_result.model_dump_json(indent=2)
    except Exception as e:
        # Unexpected error
        logger.error(f"Unexpected error in assess_biodiversity_enhanced: {e}", exc_info=True)
        error_result = BiodiversityOutput(
            success=False,
            surface_ha=surface_ha,
            overall_biodiversity_score=0.0,
            overall_status="poor",
            error=f"Erreur inattendue: {str(e)}",
            error_type="unknown"
        )
        return error_result.model_dump_json(indent=2)


# Create the StructuredTool
assess_biodiversity_tool_enhanced = StructuredTool.from_function(
    func=assess_biodiversity_enhanced,
    name="assess_biodiversity",
    description="""Évalue la biodiversité agricole à partir de multiples indicateurs.

7 indicateurs analysés:
1. Rotation cultures (diversité et durée)
2. Bandes enherbées (% périmètre)
3. Haies (mètres/hectare)
4. Points d'eau (mares, ruisseaux, zones humides)
5. Agriculture biologique (certification)
6. Usage pesticides (applications/an)
7. Couverts végétaux (entre cultures)

Évaluation fournie:
- Score global biodiversité (0-10)
- Score par indicateur avec statut
- Points forts identifiés
- Points faibles identifiés
- Recommandations priorisées d'amélioration
- Potentiel d'amélioration du score

Basé sur recherche biodiversité agricole française.
Cibles: rotation 5+ cultures, bandes 5-10%, haies 100+ m/ha, pesticides <5/an.

Retourne évaluation détaillée avec actions concrètes.""",
    args_schema=BiodiversityInput,
    return_direct=False,
    coroutine=assess_biodiversity_enhanced,
    handle_validation_error=True
)

