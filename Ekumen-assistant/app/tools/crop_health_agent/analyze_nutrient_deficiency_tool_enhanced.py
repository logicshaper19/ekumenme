"""
Enhanced Nutrient Deficiency Analysis Tool with Pydantic schemas, caching, and error handling

Improvements over original:
- ✅ Pydantic schemas for type safety
- ✅ Redis caching with 1-hour TTL
- ✅ Async support
- ✅ Granular error handling
- ✅ Database integration ready
- ✅ Follows PoC pattern (Service class + StructuredTool)
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
import json
import aiofiles
from pathlib import Path

from langchain.tools import StructuredTool
from pydantic import ValidationError

from app.tools.schemas.nutrient_schemas import (
    NutrientAnalysisInput,
    NutrientAnalysisOutput,
    NutrientDeficiency,
    SoilAnalysis,
    DeficiencyLevel,
    ConfidenceLevel,
    NutrientType,
)
from app.core.cache import redis_cache

logger = logging.getLogger(__name__)


class EnhancedNutrientService:
    """Service for nutrient deficiency analysis with caching"""

    def __init__(self, knowledge_base_path: Optional[str] = None):
        """Initialize service with optional knowledge base path"""
        self.knowledge_base_path = knowledge_base_path or self._get_default_knowledge_path()
        self._knowledge_cache: Optional[Dict[str, Any]] = None

    def _get_default_knowledge_path(self) -> str:
        """Get default knowledge base file path"""
        current_dir = Path(__file__).parent
        return str(current_dir.parent.parent / "data" / "nutrient_deficiency_knowledge.json")

    async def _load_knowledge_base_async(self) -> Dict[str, Any]:
        """Load knowledge base asynchronously"""
        if self._knowledge_cache is not None:
            return self._knowledge_cache

        try:
            async with aiofiles.open(self.knowledge_base_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                self._knowledge_cache = json.loads(content)
            logger.info(f"Loaded knowledge base from {self.knowledge_base_path}")
        except Exception as e:
            logger.error(f"Error loading knowledge base: {e}")
            self._knowledge_cache = self._get_fallback_knowledge_base()

        return self._knowledge_cache

    def _get_fallback_knowledge_base(self) -> Dict[str, Any]:
        """Get fallback knowledge base when file loading fails"""
        return {
            "metadata": {"version": "fallback"},
            "crops": {
                "blé": {
                    "nutrients": {
                        "nitrogen": {
                            "name": "Azote",
                            "symbol": "N",
                            "nutrient_type": "macronutrient",
                            "symptoms": ["Jaunissement des feuilles", "Croissance ralentie", "Feuilles pâles"],
                            "soil_indicators": ["pH bas", "Faible matière organique"],
                            "treatment": ["Apport d'engrais azoté (100-150 kg N/ha)", "Fractionnement en 2-3 apports"],
                            "prevention": ["Rotation avec légumineuses", "Apport de matière organique"],
                            "deficiency_level": "moderate"
                        }
                    }
                }
            }
        }

    def _parse_soil_analysis(self, soil_conditions: Optional[Dict[str, Any]]) -> Optional[SoilAnalysis]:
        """Parse soil conditions into SoilAnalysis schema"""
        if not soil_conditions:
            return None

        try:
            # Interpret pH
            pH = soil_conditions.get("pH")
            pH_interpretation = None
            if pH:
                if pH < 6.0:
                    pH_interpretation = "acidic"
                elif pH > 7.5:
                    pH_interpretation = "alkaline"
                else:
                    pH_interpretation = "neutral"

            return SoilAnalysis(
                pH=pH,
                pH_interpretation=pH_interpretation,
                organic_matter_percent=soil_conditions.get("organic_matter_percent"),
                texture=soil_conditions.get("texture"),
                drainage=soil_conditions.get("drainage"),
                cec=soil_conditions.get("cec"),
                nutrient_availability_factors=soil_conditions.get("nutrient_availability_factors", [])
            )
        except Exception as e:
            logger.warning(f"Error parsing soil analysis: {e}")
            return None

    def _analyze_nutrient_deficiencies(
        self,
        plant_symptoms: List[str],
        soil_conditions: Dict[str, Any],
        deficiency_knowledge: Dict[str, Any]
    ) -> List[NutrientDeficiency]:
        """Analyze nutrient deficiencies based on symptoms and soil conditions"""
        deficiencies = []

        for nutrient_key, nutrient_info in deficiency_knowledge.items():
            # Calculate symptom match
            symptoms = nutrient_info.get("symptoms", [])
            symptom_matches = [symptom for symptom in plant_symptoms if symptom in symptoms]
            symptom_match_ratio = len(symptom_matches) / len(symptoms) if symptoms else 0

            # Calculate soil indicator match
            soil_indicators = nutrient_info.get("soil_indicators", [])
            soil_matches = [indicator for indicator in soil_conditions.keys() if indicator in soil_indicators]
            soil_match_ratio = len(soil_matches) / len(soil_indicators) if soil_indicators else 0

            # Calculate overall confidence
            confidence = (symptom_match_ratio * 0.7 + soil_match_ratio * 0.3)

            # Add bonuses for matches
            if symptom_matches:
                confidence += 0.1
            if soil_matches:
                confidence += 0.05

            # Cap confidence at 1.0
            confidence = min(confidence, 1.0)

            if confidence > 0.3:  # Minimum confidence threshold
                # Map deficiency level string to enum
                deficiency_level_str = nutrient_info.get("deficiency_level", "moderate")
                try:
                    deficiency_level = DeficiencyLevel(deficiency_level_str)
                except ValueError:
                    deficiency_level = DeficiencyLevel.MODERATE

                # Map nutrient type
                nutrient_type_str = nutrient_info.get("nutrient_type", "macronutrient")
                try:
                    nutrient_type = NutrientType(nutrient_type_str)
                except ValueError:
                    nutrient_type = NutrientType.MACRONUTRIENT

                deficiency = NutrientDeficiency(
                    nutrient=nutrient_key,
                    nutrient_name=nutrient_info.get("name", nutrient_key),
                    symbol=nutrient_info.get("symbol", ""),
                    nutrient_type=nutrient_type,
                    deficiency_level=deficiency_level,
                    confidence=round(confidence, 3),
                    symptoms_matched=symptom_matches,
                    soil_indicators=soil_matches,
                    treatment_recommendations=nutrient_info.get("treatment", []),
                    prevention_measures=nutrient_info.get("prevention", []),
                    dosage_guidelines=nutrient_info.get("dosage_guidelines"),
                    critical_stages=nutrient_info.get("critical_stages")
                )
                deficiencies.append(deficiency)

        # Sort by confidence and limit results
        deficiencies.sort(key=lambda x: x.confidence, reverse=True)
        return deficiencies[:10]  # Max 10 deficiencies

    def _calculate_analysis_confidence(self, deficiencies: List[NutrientDeficiency]) -> ConfidenceLevel:
        """Calculate overall analysis confidence"""
        if not deficiencies:
            return ConfidenceLevel.LOW

        max_confidence = max(deficiency.confidence for deficiency in deficiencies)

        if max_confidence > 0.8:
            return ConfidenceLevel.VERY_HIGH
        elif max_confidence > 0.6:
            return ConfidenceLevel.HIGH
        elif max_confidence > 0.4:
            return ConfidenceLevel.MODERATE
        else:
            return ConfidenceLevel.LOW

    def _generate_treatment_recommendations(self, deficiencies: List[NutrientDeficiency]) -> List[str]:
        """Generate consolidated treatment recommendations"""
        recommendations = []

        if not deficiencies:
            recommendations.append("Aucune carence nutritionnelle identifiée - Surveillance continue recommandée")
            return recommendations

        # Get top deficiency
        top_deficiency = deficiencies[0]

        if top_deficiency.confidence > 0.5:
            recommendations.append(f"Carence principale: {top_deficiency.nutrient_name} ({top_deficiency.symbol}) - Confiance: {top_deficiency.confidence:.1%}")

            if top_deficiency.treatment_recommendations:
                recommendations.extend(top_deficiency.treatment_recommendations)
        else:
            recommendations.append("Analyse incertaine - Analyse de sol recommandée")
            recommendations.append("Surveillance accrue des symptômes")

        return recommendations

    def _generate_priority_actions(self, deficiencies: List[NutrientDeficiency]) -> List[str]:
        """Generate priority actions based on deficiency severity"""
        actions = []

        critical_deficiencies = [d for d in deficiencies if d.deficiency_level == DeficiencyLevel.CRITICAL]
        severe_deficiencies = [d for d in deficiencies if d.deficiency_level == DeficiencyLevel.SEVERE]

        if critical_deficiencies:
            actions.append(f"URGENT: Traiter immédiatement les carences critiques en {', '.join([d.nutrient_name for d in critical_deficiencies])}")

        if severe_deficiencies:
            actions.append(f"Traiter rapidement les carences sévères en {', '.join([d.nutrient_name for d in severe_deficiencies])}")

        if not actions:
            actions.append("Surveillance régulière et ajustements préventifs")

        return actions

    @redis_cache(ttl=3600, model_class=NutrientAnalysisOutput, category="crop_health")
    async def analyze_nutrient_deficiency(
        self,
        input_data: NutrientAnalysisInput
    ) -> NutrientAnalysisOutput:
        """
        Analyze nutrient deficiencies with caching

        Args:
            input_data: Nutrient analysis input parameters

        Returns:
            NutrientAnalysisOutput with deficiency analysis
        """
        try:
            # Load knowledge base
            knowledge_base = await self._load_knowledge_base_async()
            crops = knowledge_base.get("crops", {})

            # Check if crop is supported
            if input_data.crop_type not in crops:
                return NutrientAnalysisOutput(
                    success=False,
                    crop_type=input_data.crop_type,
                    crop_eppo_code=input_data.eppo_code,
                    crop_category=input_data.crop_category,
                    plant_symptoms=input_data.plant_symptoms,
                    nutrient_deficiencies=[],
                    analysis_confidence=ConfidenceLevel.LOW,
                    treatment_recommendations=[],
                    priority_actions=[],
                    prevention_measures=[],
                    total_deficiencies=0,
                    critical_deficiencies=0,
                    timestamp=datetime.now(),
                    error=f"Type de culture '{input_data.crop_type}' non supporté",
                    error_type="unsupported_crop"
                )

            # Get deficiency knowledge for crop
            deficiency_knowledge = crops[input_data.crop_type].get("nutrients", {})

            # Analyze deficiencies
            deficiencies = self._analyze_nutrient_deficiencies(
                input_data.plant_symptoms,
                input_data.soil_conditions or {},
                deficiency_knowledge
            )

            # Calculate confidence
            analysis_confidence = self._calculate_analysis_confidence(deficiencies)

            # Generate recommendations
            treatment_recommendations = self._generate_treatment_recommendations(deficiencies)
            priority_actions = self._generate_priority_actions(deficiencies)

            # Collect prevention measures
            prevention_measures = []
            for deficiency in deficiencies[:3]:  # Top 3 deficiencies
                prevention_measures.extend(deficiency.prevention_measures)
            prevention_measures = list(set(prevention_measures))  # Remove duplicates

            # Parse soil analysis
            soil_analysis = self._parse_soil_analysis(input_data.soil_conditions)

            # Count critical deficiencies
            critical_count = sum(1 for d in deficiencies if d.deficiency_level == DeficiencyLevel.CRITICAL)

            return NutrientAnalysisOutput(
                success=True,
                crop_type=input_data.crop_type,
                crop_eppo_code=input_data.eppo_code,
                crop_category=input_data.crop_category,
                plant_symptoms=input_data.plant_symptoms,
                soil_analysis=soil_analysis,
                bbch_stage=input_data.bbch_stage,
                nutrient_deficiencies=deficiencies,
                analysis_confidence=analysis_confidence,
                treatment_recommendations=treatment_recommendations,
                priority_actions=priority_actions,
                prevention_measures=prevention_measures,
                total_deficiencies=len(deficiencies),
                critical_deficiencies=critical_count,
                data_source="knowledge_base_enhanced",
                timestamp=datetime.now()
            )

        except Exception as e:
            logger.error(f"Nutrient analysis error: {e}", exc_info=True)
            return NutrientAnalysisOutput(
                success=False,
                crop_type=input_data.crop_type,
                crop_eppo_code=input_data.eppo_code,
                plant_symptoms=input_data.plant_symptoms,
                nutrient_deficiencies=[],
                analysis_confidence=ConfidenceLevel.LOW,
                treatment_recommendations=[],
                priority_actions=[],
                prevention_measures=[],
                total_deficiencies=0,
                timestamp=datetime.now(),
                error=f"Erreur lors de l'analyse: {str(e)}",
                error_type=type(e).__name__
            )



# Create service instance
_service = EnhancedNutrientService()


# Async wrapper function
async def analyze_nutrient_deficiency_enhanced(
    crop_type: str,
    plant_symptoms: List[str],
    soil_conditions: Optional[Dict[str, Any]] = None,
    eppo_code: Optional[str] = None,
    crop_category: Optional[str] = None,
    bbch_stage: Optional[int] = None,
    field_location: Optional[str] = None,
    previous_fertilization: Optional[List[str]] = None
) -> str:
    """
    Analyze nutrient deficiencies from plant symptoms and soil conditions

    Args:
        crop_type: Type of crop (e.g., 'blé', 'maïs', 'colza')
        plant_symptoms: List of observed plant symptoms
        soil_conditions: Soil conditions (pH, organic_matter, texture, etc.)
        eppo_code: Optional EPPO code for crop identification
        crop_category: Optional crop category (cereal, oilseed, etc.)
        bbch_stage: Optional BBCH growth stage (0-99)
        field_location: Optional field location
        previous_fertilization: Optional previous fertilization history

    Returns:
        JSON string with nutrient deficiency analysis
    """
    try:
        # Create input
        input_data = NutrientAnalysisInput(
            crop_type=crop_type,
            plant_symptoms=plant_symptoms,
            soil_conditions=soil_conditions,
            eppo_code=eppo_code,
            crop_category=crop_category,
            bbch_stage=bbch_stage,
            field_location=field_location,
            previous_fertilization=previous_fertilization
        )

        # Execute analysis
        result = await _service.analyze_nutrient_deficiency(input_data)

        # Return JSON
        return result.model_dump_json(indent=2)

    except ValidationError as e:
        logger.error(f"Nutrient analysis validation error: {e}")
        error_result = NutrientAnalysisOutput(
            success=False,
            crop_type=crop_type,
            plant_symptoms=plant_symptoms,
            nutrient_deficiencies=[],
            analysis_confidence=ConfidenceLevel.LOW,
            treatment_recommendations=[],
            priority_actions=[],
            prevention_measures=[],
            total_deficiencies=0,
            timestamp=datetime.now(),
            error="Erreur de validation des paramètres. Vérifiez les symptômes et conditions du sol.",
            error_type="validation_error"
        )
        return error_result.model_dump_json(indent=2)

    except Exception as e:
        logger.error(f"Unexpected nutrient analysis error: {e}", exc_info=True)
        error_result = NutrientAnalysisOutput(
            success=False,
            crop_type=crop_type,
            plant_symptoms=plant_symptoms,
            nutrient_deficiencies=[],
            analysis_confidence=ConfidenceLevel.LOW,
            treatment_recommendations=[],
            priority_actions=[],
            prevention_measures=[],
            total_deficiencies=0,
            timestamp=datetime.now(),
            error="Erreur inattendue lors de l'analyse des carences. Veuillez réessayer.",
            error_type="unknown"
        )
        return error_result.model_dump_json(indent=2)


# Create structured tool
analyze_nutrient_deficiency_tool_enhanced = StructuredTool.from_function(
    func=analyze_nutrient_deficiency_enhanced,
    name="analyze_nutrient_deficiency",
    description="""Analyse les carences nutritionnelles à partir des symptômes des plantes et conditions du sol.

Retourne une analyse détaillée avec:
- Carences nutritionnelles identifiées (N, P, K, Ca, Mg, etc.)
- Niveau de confiance de l'analyse
- Recommandations de traitement
- Actions prioritaires
- Mesures préventives

Utilisez cet outil quand les agriculteurs signalent des symptômes de plantes (jaunissement, croissance ralentie, etc.).""",
    args_schema=NutrientAnalysisInput,
    return_direct=False,
    coroutine=analyze_nutrient_deficiency_enhanced,
    handle_validation_error=True
)
