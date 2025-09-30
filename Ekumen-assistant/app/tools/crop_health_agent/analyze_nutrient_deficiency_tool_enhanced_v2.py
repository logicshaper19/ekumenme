"""
Enhanced Nutrient Deficiency Analysis Tool - PoC Pattern

Follows the proven PoC pattern:
- Service class with caching
- Async wrapper function
- StructuredTool creation
- Pydantic validation
- Crop model integration (Phase 2 database)

Features:
- Crop table integration with EPPO codes
- Crop category-based nutrient requirements
- Pydantic validation
- Redis caching
- Structured error handling
"""

from typing import Optional, List, Dict, Any
from langchain.tools import StructuredTool
import logging
from datetime import datetime

from app.models.crop import Crop
from app.tools.schemas.nutrient_schemas import (
    NutrientAnalysisInput,
    NutrientAnalysisOutput,
    NutrientDeficiency,
    SoilAnalysis,
    DeficiencyLevel,
    NutrientType,
    ConfidenceLevel
)
from app.core.caching import redis_cache
from app.core.errors import DataError, ValidationError
from app.services.knowledge_base_service import KnowledgeBaseService

logger = logging.getLogger(__name__)


# Crop-specific nutrient requirements
CROP_NUTRIENT_REQUIREMENTS = {
    "cereal": {
        "critical_nutrients": ["N", "P", "K"],
        "secondary_nutrients": ["S", "Mg"],
        "micronutrients": ["Mn", "Zn", "Cu"],
        "critical_stages": ["BBCH 30-39 (montaison)", "BBCH 50-59 (épiaison)"]
    },
    "oilseed": {
        "critical_nutrients": ["N", "S", "B"],
        "secondary_nutrients": ["P", "K", "Mg"],
        "micronutrients": ["Mo", "Mn"],
        "critical_stages": ["BBCH 20-29 (rosette)", "BBCH 60-69 (floraison)"]
    },
    "root_crop": {
        "critical_nutrients": ["N", "P", "K"],
        "secondary_nutrients": ["B", "Mg"],
        "micronutrients": ["Mn", "Zn"],
        "critical_stages": ["BBCH 10-19 (levée)", "BBCH 40-49 (tubérisation)"]
    },
    "legume": {
        "critical_nutrients": ["P", "K", "Mo"],
        "secondary_nutrients": ["Ca", "Mg", "S"],
        "micronutrients": ["B", "Fe", "Zn"],
        "critical_stages": ["BBCH 10-19 (levée)", "BBCH 60-69 (floraison)"]
    },
    "fruit": {
        "critical_nutrients": ["N", "P", "K"],
        "secondary_nutrients": ["Ca", "Mg"],
        "micronutrients": ["B", "Zn", "Fe", "Mn"],
        "critical_stages": ["BBCH 60-69 (floraison)", "BBCH 70-79 (fructification)"]
    },
    "vegetable": {
        "critical_nutrients": ["N", "P", "K"],
        "secondary_nutrients": ["Ca", "Mg"],
        "micronutrients": ["B", "Fe", "Mn"],
        "critical_stages": ["BBCH 10-19 (levée)", "BBCH 40-49 (développement)"]
    },
    "forage": {
        "critical_nutrients": ["N", "P", "K"],
        "secondary_nutrients": ["S", "Mg"],
        "micronutrients": ["Cu", "Se"],
        "critical_stages": ["BBCH 20-29 (tallage)", "BBCH 50-59 (épiaison)"]
    }
}


class EnhancedNutrientService:
    """
    Enhanced nutrient deficiency analysis service with Phase 2 database integration.
    
    Features:
    - Crop model integration
    - EPPO code support
    - Crop category-based requirements
    - Redis caching
    - Structured error handling
    """
    
    def __init__(self):
        self._knowledge_service = None
    
    @property
    def knowledge_service(self):
        """Lazy load knowledge service"""
        if self._knowledge_service is None:
            self._knowledge_service = KnowledgeBaseService()
        return self._knowledge_service
    
    @redis_cache(ttl=3600, model_class=NutrientAnalysisOutput, category="crop_health")
    async def analyze_nutrient_deficiency(
        self,
        crop_type: str,
        plant_symptoms: List[str],
        soil_conditions: Optional[Dict[str, Any]] = None,
        eppo_code: Optional[str] = None,
        crop_category: Optional[str] = None,
        bbch_stage: Optional[int] = None,
        field_location: Optional[str] = None,
        previous_fertilization: Optional[List[str]] = None
    ) -> NutrientAnalysisOutput:
        """
        Analyze nutrient deficiencies with database integration.
        
        Args:
            crop_type: Crop name in French
            plant_symptoms: List of observed symptoms
            soil_conditions: Soil analysis data
            eppo_code: EPPO code for crop
            crop_category: Crop category
            bbch_stage: Growth stage
            field_location: Field location
            previous_fertilization: Fertilization history
            
        Returns:
            NutrientAnalysisOutput with deficiency analysis
        """
        try:
            # Step 1: Get crop from database
            crop = await self._get_crop_from_database(crop_type, eppo_code)
            
            if not crop:
                raise DataError(
                    f"Culture inconnue: {crop_type}",
                    error_type="crop_not_found"
                )
            
            # Step 2: Analyze soil conditions
            soil_analysis = self._analyze_soil_conditions(soil_conditions) if soil_conditions else None
            
            # Step 3: Get crop nutrient requirements
            nutrient_requirements = CROP_NUTRIENT_REQUIREMENTS.get(crop.category, {})
            
            # Step 4: Search for nutrient deficiencies
            deficiencies = await self._search_nutrient_deficiencies(
                crop=crop,
                plant_symptoms=plant_symptoms,
                soil_analysis=soil_analysis,
                nutrient_requirements=nutrient_requirements,
                bbch_stage=bbch_stage
            )
            
            # Step 5: Calculate overall confidence
            overall_confidence = self._calculate_overall_confidence(deficiencies)
            
            # Step 6: Generate recommendations
            treatment_recommendations = self._generate_treatment_recommendations(deficiencies)
            priority_actions = self._generate_priority_actions(deficiencies)
            prevention_measures = self._generate_prevention_measures(crop, deficiencies)
            
            # Step 7: Count critical deficiencies
            critical_count = sum(1 for d in deficiencies if d.deficiency_level in [DeficiencyLevel.SEVERE, DeficiencyLevel.CRITICAL])
            
            # Step 8: Build output
            output = NutrientAnalysisOutput(
                success=True,
                crop_type=crop.name_fr,
                crop_eppo_code=crop.eppo_code,
                crop_category=crop.category,
                plant_symptoms=plant_symptoms,
                soil_analysis=soil_analysis,
                bbch_stage=bbch_stage,
                nutrient_deficiencies=deficiencies,
                analysis_confidence=overall_confidence,
                treatment_recommendations=treatment_recommendations,
                priority_actions=priority_actions,
                prevention_measures=prevention_measures,
                total_deficiencies=len(deficiencies),
                critical_deficiencies=critical_count,
                data_source="database_enhanced",
                timestamp=datetime.now()
            )
            
            logger.info(
                f"Nutrient analysis complete for {crop.name_fr} (EPPO: {crop.eppo_code}): "
                f"{len(deficiencies)} deficiencies identified"
            )
            
            return output
            
        except (DataError, ValidationError) as e:
            logger.error(f"Nutrient analysis error: {e}")
            return NutrientAnalysisOutput(
                success=False,
                crop_type=crop_type,
                plant_symptoms=plant_symptoms,
                nutrient_deficiencies=[],
                analysis_confidence=ConfidenceLevel.LOW,
                treatment_recommendations=[],
                priority_actions=[],
                prevention_measures=[],
                total_deficiencies=0,
                critical_deficiencies=0,
                data_source="error",
                error=str(e),
                error_type=getattr(e, 'error_type', 'unknown_error')
            )
        except Exception as e:
            logger.exception(f"Unexpected error in nutrient analysis: {e}")
            return NutrientAnalysisOutput(
                success=False,
                crop_type=crop_type,
                plant_symptoms=plant_symptoms,
                nutrient_deficiencies=[],
                analysis_confidence=ConfidenceLevel.LOW,
                treatment_recommendations=[],
                priority_actions=[],
                prevention_measures=[],
                total_deficiencies=0,
                critical_deficiencies=0,
                data_source="error",
                error=f"Erreur inattendue: {str(e)}",
                error_type="unexpected_error"
            )
    
    async def _get_crop_from_database(self, crop_name: str, eppo_code: Optional[str] = None) -> Optional[Crop]:
        """Get crop from database using Crop model"""
        try:
            if eppo_code:
                crop = await Crop.from_eppo_code(eppo_code)
                if crop:
                    return crop
            
            crop = await Crop.from_french_name(crop_name)
            return crop
            
        except Exception as e:
            logger.warning(f"Error getting crop from database: {e}")
            return None
    
    def _analyze_soil_conditions(self, soil_conditions: Dict[str, Any]) -> SoilAnalysis:
        """Analyze soil conditions"""
        pH = soil_conditions.get("pH") or soil_conditions.get("ph")
        organic_matter = soil_conditions.get("organic_matter_percent") or soil_conditions.get("organic_matter")
        
        # Interpret pH
        pH_interpretation = None
        if pH:
            if pH < 6.0:
                pH_interpretation = "acidic"
            elif pH > 7.5:
                pH_interpretation = "alkaline"
            else:
                pH_interpretation = "neutral"
        
        # Identify nutrient availability factors
        availability_factors = []
        if pH and pH < 5.5:
            availability_factors.append("pH très acide - limite disponibilité P, Ca, Mg")
        if pH and pH > 8.0:
            availability_factors.append("pH très alcalin - limite disponibilité Fe, Mn, Zn")
        if organic_matter and organic_matter < 2.0:
            availability_factors.append("Faible matière organique - limite rétention nutriments")
        
        return SoilAnalysis(
            pH=pH,
            pH_interpretation=pH_interpretation,
            organic_matter_percent=organic_matter,
            texture=soil_conditions.get("texture"),
            drainage=soil_conditions.get("drainage"),
            cec=soil_conditions.get("cec"),
            nutrient_availability_factors=availability_factors
        )
    
    async def _search_nutrient_deficiencies(
        self,
        crop: Crop,
        plant_symptoms: List[str],
        soil_analysis: Optional[SoilAnalysis],
        nutrient_requirements: Dict[str, Any],
        bbch_stage: Optional[int]
    ) -> List[NutrientDeficiency]:
        """Search for nutrient deficiencies"""
        try:
            # Search in knowledge base
            search_results = await self.knowledge_service.search_nutrient_deficiencies(
                crop_type=crop.name_fr,
                symptoms=plant_symptoms,
                soil_conditions=soil_analysis.model_dump() if soil_analysis else None
            )
            
            deficiencies = []
            if search_results.get("total_results", 0) > 0:
                for result in search_results.get("deficiencies", []):
                    deficiency_data = result.get("deficiency", {})
                    
                    deficiency = NutrientDeficiency(
                        nutrient=deficiency_data.get("nutrient", "unknown"),
                        nutrient_name=deficiency_data.get("nutrient_name", "Unknown"),
                        symbol=deficiency_data.get("symbol", "?"),
                        nutrient_type=NutrientType(deficiency_data.get("nutrient_type", "macronutrient")),
                        deficiency_level=DeficiencyLevel(deficiency_data.get("deficiency_level", "moderate")),
                        confidence=result.get("confidence_score", 0.5),
                        symptoms_matched=result.get("matching_symptoms", []),
                        soil_indicators=result.get("soil_indicators", []),
                        treatment_recommendations=deficiency_data.get("treatment_recommendations", []),
                        prevention_measures=deficiency_data.get("prevention_measures", []),
                        dosage_guidelines=deficiency_data.get("dosage_guidelines"),
                        critical_stages=deficiency_data.get("critical_stages"),
                        optimal_range=deficiency_data.get("optimal_range"),
                        current_level=deficiency_data.get("current_level")
                    )
                    
                    deficiencies.append(deficiency)
            
            return deficiencies
            
        except Exception as e:
            logger.warning(f"Database search failed: {e}")
            return []
    
    def _calculate_overall_confidence(self, deficiencies: List[NutrientDeficiency]) -> ConfidenceLevel:
        """Calculate overall confidence level"""
        if not deficiencies:
            return ConfidenceLevel.LOW
        
        avg_confidence = sum(d.confidence for d in deficiencies) / len(deficiencies)
        
        if avg_confidence >= 0.8:
            return ConfidenceLevel.VERY_HIGH
        elif avg_confidence >= 0.6:
            return ConfidenceLevel.HIGH
        elif avg_confidence >= 0.4:
            return ConfidenceLevel.MODERATE
        else:
            return ConfidenceLevel.LOW
    
    def _generate_treatment_recommendations(self, deficiencies: List[NutrientDeficiency]) -> List[str]:
        """Generate consolidated treatment recommendations"""
        recommendations = set()
        for deficiency in deficiencies:
            recommendations.update(deficiency.treatment_recommendations)
        return list(recommendations)
    
    def _generate_priority_actions(self, deficiencies: List[NutrientDeficiency]) -> List[str]:
        """Generate priority actions"""
        actions = []
        
        critical = [d for d in deficiencies if d.deficiency_level == DeficiencyLevel.CRITICAL]
        severe = [d for d in deficiencies if d.deficiency_level == DeficiencyLevel.SEVERE]
        
        if critical:
            actions.append(f"URGENT: Corriger carences critiques en {', '.join(d.symbol for d in critical)}")
        if severe:
            actions.append(f"PRIORITAIRE: Traiter carences sévères en {', '.join(d.symbol for d in severe)}")
        
        return actions
    
    def _generate_prevention_measures(self, crop: Crop, deficiencies: List[NutrientDeficiency]) -> List[str]:
        """Generate prevention measures"""
        measures = set()
        
        # Crop-specific measures
        if crop.category == "cereal":
            measures.add("Rotation avec légumineuses pour enrichir le sol en azote")
        elif crop.category == "oilseed":
            measures.add("Apport de soufre systématique pour colza")
        
        # Deficiency-specific measures
        for deficiency in deficiencies:
            measures.update(deficiency.prevention_measures)
        
        # General measures
        measures.add("Analyse de sol régulière (tous les 3-5 ans)")
        measures.add("Apport de matière organique")
        
        return list(measures)


# Service instance
_nutrient_service = EnhancedNutrientService()


# Async wrapper function
async def analyze_nutrient_deficiency_async(
    crop_type: str,
    plant_symptoms: List[str],
    soil_conditions: Optional[Dict[str, Any]] = None,
    eppo_code: Optional[str] = None,
    crop_category: Optional[str] = None,
    bbch_stage: Optional[int] = None,
    field_location: Optional[str] = None,
    previous_fertilization: Optional[List[str]] = None
) -> str:
    """Async wrapper for nutrient deficiency analysis"""
    result = await _nutrient_service.analyze_nutrient_deficiency(
        crop_type=crop_type,
        plant_symptoms=plant_symptoms,
        soil_conditions=soil_conditions,
        eppo_code=eppo_code,
        crop_category=crop_category,
        bbch_stage=bbch_stage,
        field_location=field_location,
        previous_fertilization=previous_fertilization
    )
    return result.model_dump_json(indent=2)


# Create StructuredTool
analyze_nutrient_deficiency_tool_enhanced = StructuredTool.from_function(
    coroutine=analyze_nutrient_deficiency_async,
    name="analyze_nutrient_deficiency",
    description="""Analyse les carences nutritionnelles à partir des symptômes des plantes et conditions du sol.

Utilise:
- Base de données Crop avec codes EPPO
- Catégories de cultures pour besoins nutritionnels
- Analyse des conditions du sol
- Cache Redis (1h TTL)

Paramètres:
- crop_type: Type de culture (ex: 'blé', 'maïs', 'colza')
- plant_symptoms: Liste des symptômes observés
- soil_conditions: Conditions du sol (pH, matière organique, texture)
- eppo_code: Code EPPO pour identification précise
- bbch_stage: Stade de croissance BBCH (0-99)

Retourne: Analyse des carences avec recommandations de traitement et prévention.""",
    args_schema=NutrientAnalysisInput,
    handle_validation_error=False
)

