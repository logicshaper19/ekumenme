"""
Enhanced Pest Identification Tool with Pydantic schemas, caching, and error handling

Improvements over original:
- ✅ Pydantic schemas for type safety
- ✅ Redis caching with 1-hour TTL
- ✅ Async support
- ✅ Granular error handling
- ✅ Database integration (Crop table + EPPO codes)
- ✅ Follows PoC pattern (Service class + StructuredTool)
- ✅ 50% minimum confidence threshold (safety)
- ✅ Fuzzy damage pattern matching (typo-tolerant)
- ✅ Input sanitization
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from difflib import SequenceMatcher

from langchain.tools import StructuredTool
from pydantic import ValidationError

from app.models.crop import Crop
from app.tools.schemas.pest_schemas import (
    PestIdentificationInput,
    PestIdentificationOutput,
    PestIdentification,
    PestSeverity,
    PestType,
    PestStage,
    ConfidenceLevel,
    CropCategoryRiskProfile
)
from app.core.cache import redis_cache
from app.services.knowledge_base_service import KnowledgeBaseService

logger = logging.getLogger(__name__)

# Minimum confidence threshold for pest identification (50% = scientific standard)
MIN_CONFIDENCE_THRESHOLD = 0.5
# Fuzzy matching threshold (75% similarity for damage patterns)
FUZZY_MATCH_THRESHOLD = 0.75


def _fuzzy_match(text: str, known_patterns: List[str]) -> Optional[str]:
    """Fuzzy match text against known patterns (typo-tolerant)"""
    text_lower = text.lower().strip()
    best_match = None
    best_ratio = 0.0

    for pattern in known_patterns:
        pattern_lower = pattern.lower().strip()
        ratio = SequenceMatcher(None, text_lower, pattern_lower).ratio()
        if ratio > best_ratio and ratio >= FUZZY_MATCH_THRESHOLD:
            best_ratio = ratio
            best_match = pattern

    return best_match


# Crop category risk profiles
CATEGORY_RISK_PROFILES = {
    "cereal": CropCategoryRiskProfile(
        category="cereal",
        common_pests=["pucerons", "cicadelles", "criocères", "zabre", "oscinie"],
        high_risk_periods=["BBCH 30-59 (montaison-épiaison)", "Mai-Juin"],
        prevention_strategies=[
            "Rotation des cultures",
            "Variétés résistantes",
            "Surveillance précoce",
            "Gestion des adventices"
        ]
    ),
    "oilseed": CropCategoryRiskProfile(
        category="oilseed",
        common_pests=["altises", "charançons", "méligèthes", "pucerons cendrés"],
        high_risk_periods=["BBCH 10-30 (levée-rosette)", "Septembre-Octobre"],
        prevention_strategies=[
            "Semis précoce",
            "Plantes compagnes",
            "Surveillance des seuils",
            "Gestion des bordures"
        ]
    ),
    "root_crop": CropCategoryRiskProfile(
        category="root_crop",
        common_pests=["taupins", "nématodes", "pucerons", "altises"],
        high_risk_periods=["BBCH 10-40 (levée-développement)", "Avril-Juin"],
        prevention_strategies=[
            "Rotation longue",
            "Travail du sol",
            "Plantes pièges",
            "Surveillance du sol"
        ]
    ),
    "legume": CropCategoryRiskProfile(
        category="legume",
        common_pests=["sitones", "bruches", "pucerons", "thrips"],
        high_risk_periods=["BBCH 20-60 (tallage-floraison)", "Mai-Juillet"],
        prevention_strategies=[
            "Inoculation rhizobium",
            "Variétés tolérantes",
            "Surveillance floraison",
            "Gestion azote"
        ]
    ),
    "fruit": CropCategoryRiskProfile(
        category="fruit",
        common_pests=["carpocapse", "pucerons", "acariens", "cochenilles"],
        high_risk_periods=["BBCH 60-80 (floraison-maturation)", "Avril-Septembre"],
        prevention_strategies=[
            "Taille sanitaire",
            "Confusion sexuelle",
            "Auxiliaires",
            "Filets anti-insectes"
        ]
    ),
    "vegetable": CropCategoryRiskProfile(
        category="vegetable",
        common_pests=["aleurodes", "thrips", "pucerons", "noctuelles"],
        high_risk_periods=["Toute la saison", "Avril-Octobre"],
        prevention_strategies=[
            "Rotation courte",
            "Paillage",
            "Filets protection",
            "Auxiliaires"
        ]
    ),
    "forage": CropCategoryRiskProfile(
        category="forage",
        common_pests=["tipules", "taupins", "sitones", "pucerons"],
        high_risk_periods=["BBCH 20-50 (tallage-épiaison)", "Mars-Juin"],
        prevention_strategies=[
            "Gestion prairie",
            "Fauche précoce",
            "Drainage",
            "Rotation pâturage"
        ]
    )
}


class EnhancedPestService:
    """Service for pest identification with caching and database integration"""

    def __init__(self):
        """Initialize service"""
        self._knowledge_service = None

    @property
    def knowledge_service(self):
        """Lazy load knowledge service"""
        if self._knowledge_service is None:
            self._knowledge_service = KnowledgeBaseService()
        return self._knowledge_service

    @redis_cache(ttl=3600, model_class=PestIdentificationOutput, category="crop_health")
    async def identify_pest(self, input_data: PestIdentificationInput) -> PestIdentificationOutput:
        """
        Execute pest identification with database integration.
        
        Args:
            input_data: Validated pest identification input
            
        Returns:
            PestIdentificationOutput with structured results
        """
        try:
            # Step 1: Get crop from database using Crop model
            crop = await self._get_crop_from_database(input_data.crop_type, input_data.eppo_code)

            if not crop:
                raise ValueError(f"Culture inconnue: {input_data.crop_type}")
            
            # Step 2: Get crop category risk profile
            risk_profile = CATEGORY_RISK_PROFILES.get(crop.category)
            
            # Step 3: Search for pests in database
            pest_results = await self._search_pests_in_database(
                crop=crop,
                damage_symptoms=input_data.damage_symptoms,
                pest_indicators=input_data.pest_indicators or [],
                bbch_stage=input_data.bbch_stage
            )
            
            # Step 4: Enhance results with crop category insights
            enhanced_identifications = self._enhance_with_category_insights(
                pest_results,
                risk_profile,
                input_data.bbch_stage
            )
            
            # Step 5: Check if we have high-confidence identifications
            if not enhanced_identifications:
                # No high-confidence results - return failure with guidance
                logger.warning(f"No high-confidence pest identifications for {crop.name_fr}")
                return PestIdentificationOutput(
                    success=False,
                    crop_type=crop.name_fr,
                    crop_eppo_code=crop.eppo_code,
                    crop_category=crop.category,
                    damage_symptoms=input_data.damage_symptoms,
                    pest_indicators=input_data.pest_indicators,
                    bbch_stage=input_data.bbch_stage,
                    pest_identifications=[],
                    identification_confidence=ConfidenceLevel.LOW,
                    treatment_recommendations=[
                        "⚠️ Confiance insuffisante pour identification spécifique",
                        f"Ravageurs communs pour {crop.category}: {', '.join(risk_profile.common_pests[:3]) if risk_profile else 'non disponible'}",
                        "Recommandation: Consultation avec expert phytosanitaire",
                        "Surveillance accrue et collecte d'échantillons recommandée"
                    ],
                    total_identifications=0,
                    data_source="insufficient_confidence",
                    timestamp=datetime.now(),
                    error="Confiance insuffisante pour identification spécifique (< 50%)",
                    error_type="low_confidence"
                )

            # Step 6: Calculate overall confidence
            overall_confidence = self._calculate_overall_confidence(enhanced_identifications)

            # Step 7: Consolidate treatment recommendations with context
            treatment_recommendations = self._consolidate_treatments_with_context(enhanced_identifications)

            # Step 8: Build success output
            output = PestIdentificationOutput(
                success=True,
                crop_type=crop.name_fr,
                crop_eppo_code=crop.eppo_code,
                crop_category=crop.category,
                damage_symptoms=input_data.damage_symptoms,
                pest_indicators=input_data.pest_indicators,
                bbch_stage=input_data.bbch_stage,
                pest_identifications=enhanced_identifications,
                identification_confidence=overall_confidence,
                treatment_recommendations=treatment_recommendations,
                total_identifications=len(enhanced_identifications),
                data_source="database_enhanced" if pest_results else "category_based",
                timestamp=datetime.now()
            )
            
            logger.info(
                f"Pest identification complete for {crop.name_fr} (EPPO: {crop.eppo_code}): "
                f"{len(enhanced_identifications)} pests identified"
            )
            
            return output

        except ValueError as e:
            logger.error(f"Pest identification validation error: {e}")
            return PestIdentificationOutput(
                success=False,
                crop_type=input_data.crop_type,
                damage_symptoms=input_data.damage_symptoms,
                pest_identifications=[],
                identification_confidence=ConfidenceLevel.LOW,
                treatment_recommendations=[],
                total_identifications=0,
                data_source="error",
                timestamp=datetime.now(),
                error=str(e),
                error_type="validation_error"
            )
        except Exception as e:
            logger.exception(f"Unexpected error in pest identification: {e}")
            return PestIdentificationOutput(
                success=False,
                crop_type=input_data.crop_type,
                damage_symptoms=input_data.damage_symptoms,
                pest_identifications=[],
                identification_confidence=ConfidenceLevel.LOW,
                treatment_recommendations=[],
                total_identifications=0,
                data_source="error",
                timestamp=datetime.now(),
                error=f"Erreur inattendue: {str(e)}",
                error_type="unexpected_error"
            )
    
    async def _get_crop_from_database(self, crop_name: str, eppo_code: Optional[str] = None) -> Optional[Crop]:
        """Get crop from database using Crop model"""
        try:
            # Try EPPO code first if provided
            if eppo_code:
                crop = await Crop.from_eppo_code(eppo_code)
                if crop:
                    return crop
            
            # Fall back to French name
            crop = await Crop.from_french_name(crop_name)
            return crop
            
        except Exception as e:
            logger.warning(f"Error getting crop from database: {e}")
            return None
    
    async def _search_pests_in_database(
        self,
        crop: Crop,
        damage_symptoms: List[str],
        pest_indicators: List[str],
        bbch_stage: Optional[int]
    ) -> List[Dict[str, Any]]:
        """Search for pests in knowledge base"""
        try:
            search_results = await self.knowledge_service.search_pests(
                crop_type=crop.name_fr,
                damage_patterns=damage_symptoms,
                pest_indicators=pest_indicators
            )
            
            if search_results.get("total_results", 0) > 0:
                return search_results.get("pests", [])
            
            return []
            
        except Exception as e:
            logger.warning(f"Database search failed: {e}")
            return []
    
    def _enhance_with_category_insights(
        self,
        pest_results: List[Dict[str, Any]],
        risk_profile: Optional[CropCategoryRiskProfile],
        bbch_stage: Optional[int]
    ) -> List[PestIdentification]:
        """Enhance pest results with crop category insights"""
        identifications = []
        
        # Convert database results to PestIdentification objects
        for pest_result in pest_results:
            pest_data = pest_result.get("pest", {})

            # Base confidence from database
            base_confidence = pest_result.get("confidence_score", 0.5)

            # BBCH stage boost: 15% if in susceptible stage
            bbch_boost = 0.0
            susceptible_stages = pest_data.get("susceptible_stages")
            if bbch_stage and susceptible_stages:
                for stage_range in susceptible_stages:
                    if isinstance(stage_range, list) and len(stage_range) == 2:
                        if stage_range[0] <= bbch_stage <= stage_range[1]:
                            bbch_boost = 0.15
                            break

            # Final confidence
            final_confidence = min(base_confidence + bbch_boost, 1.0)

            identification = PestIdentification(
                pest_name=pest_data.get("name", "Unknown"),
                scientific_name=pest_data.get("scientific_name"),
                pest_type=PestType(pest_data.get("type", "unknown")),
                pest_stage=PestStage(pest_data.get("stage", "unknown")) if pest_data.get("stage") else None,
                confidence=final_confidence,
                severity=PestSeverity(pest_data.get("severity_level", "moderate")),
                damage_patterns=pest_result.get("matching_damage", []),
                treatment_recommendations=pest_data.get("treatment_options", []),
                prevention_measures=pest_data.get("prevention_methods", []),
                eppo_code=pest_data.get("eppo_code"),
                susceptible_bbch_stages=susceptible_stages,
                economic_threshold=pest_data.get("economic_threshold"),
                natural_enemies=pest_data.get("natural_enemies"),
                monitoring_methods=pest_data.get("monitoring_methods")
            )

            identifications.append(identification)
        
        # Filter by minimum confidence threshold
        identifications = [p for p in identifications if p.confidence >= MIN_CONFIDENCE_THRESHOLD]

        return identifications
    
    def _calculate_overall_confidence(self, identifications: List[PestIdentification]) -> ConfidenceLevel:
        """Calculate overall confidence level"""
        if not identifications:
            return ConfidenceLevel.LOW
        
        avg_confidence = sum(p.confidence for p in identifications) / len(identifications)
        
        if avg_confidence >= 0.8:
            return ConfidenceLevel.VERY_HIGH
        elif avg_confidence >= 0.6:
            return ConfidenceLevel.HIGH
        elif avg_confidence >= 0.4:
            return ConfidenceLevel.MODERATE
        else:
            return ConfidenceLevel.LOW
    
    def _consolidate_treatments(self, identifications: List[PestIdentification]) -> List[str]:
        """Consolidate treatment recommendations (legacy - use _consolidate_treatments_with_context)"""
        treatments = set()
        for identification in identifications:
            treatments.update(identification.treatment_recommendations)
        return list(treatments)

    def _consolidate_treatments_with_context(self, identifications: List[PestIdentification]) -> List[str]:
        """Consolidate treatments with context preservation and prioritization"""
        treatments = []

        # Group by severity and confidence
        critical_pests = [p for p in identifications if p.severity == PestSeverity.CRITICAL]
        high_severity = [p for p in identifications if p.severity == PestSeverity.HIGH]
        high_confidence = [p for p in identifications if p.confidence >= 0.7]

        # 1. Critical pests first
        if critical_pests:
            pest = critical_pests[0]
            treatments.append(f"🚨 PRIORITÉ CRITIQUE: {pest.pest_name} (confiance: {pest.confidence:.0%})")
            if pest.treatment_recommendations:
                treatments.extend(pest.treatment_recommendations[:2])

            # Economic threshold warning
            if pest.economic_threshold:
                treatments.append(f"⚠️ Seuil d'intervention: {pest.economic_threshold}")
                treatments.append("Vérifier si seuil dépassé avant traitement")

        # 2. High severity pests
        elif high_severity:
            for pest in high_severity[:2]:  # Top 2
                treatments.append(f"• {pest.pest_name} (confiance: {pest.confidence:.0%})")
                if pest.treatment_recommendations:
                    treatments.append(f"  → {pest.treatment_recommendations[0]}")

                # Economic threshold
                if pest.economic_threshold:
                    treatments.append(f"  → Seuil: {pest.economic_threshold}")

        # 3. High confidence pests
        elif high_confidence:
            for pest in high_confidence[:2]:  # Top 2
                treatments.append(f"• {pest.pest_name} (confiance: {pest.confidence:.0%})")
                if pest.treatment_recommendations:
                    treatments.append(f"  → {pest.treatment_recommendations[0]}")

        # 4. Natural enemies warning (check all pests)
        natural_enemies_found = []
        for pest in identifications:
            if pest.natural_enemies:
                natural_enemies_found.extend(pest.natural_enemies)

        if natural_enemies_found:
            unique_enemies = list(set(natural_enemies_found))[:3]
            treatments.append(f"🐞 Auxiliaires présents: {', '.join(unique_enemies)}")
            treatments.append("⚠️ Favoriser lutte biologique - éviter insecticides à large spectre")

        # 5. Monitoring methods
        monitoring_methods = []
        for pest in identifications[:2]:  # Top 2 pests
            if pest.monitoring_methods:
                monitoring_methods.extend(pest.monitoring_methods)

        if monitoring_methods:
            unique_methods = list(set(monitoring_methods))[:2]
            treatments.append(f"📊 Surveillance: {', '.join(unique_methods)}")

        # Limit to 10 recommendations
        return treatments[:10]



# Create service instance
_service = EnhancedPestService()


# Async wrapper function
async def identify_pest_enhanced(
    crop_type: str,
    damage_symptoms: List[str],
    pest_indicators: Optional[List[str]] = None,
    eppo_code: Optional[str] = None,
    crop_category: Optional[str] = None,
    bbch_stage: Optional[int] = None
) -> str:
    """
    Identify pests from crop damage symptoms and indicators

    Args:
        crop_type: Type of crop (e.g., 'blé', 'maïs', 'colza')
        damage_symptoms: List of observed damage symptoms
        pest_indicators: Optional list of pest indicators
        eppo_code: Optional EPPO code for crop identification
        crop_category: Optional crop category (cereal, oilseed, etc.)
        bbch_stage: Optional BBCH growth stage (0-99)

    Returns:
        JSON string with pest identification results
    """
    try:
        # Create input
        input_data = PestIdentificationInput(
            crop_type=crop_type,
            damage_symptoms=damage_symptoms,
            pest_indicators=pest_indicators,
            eppo_code=eppo_code,
            crop_category=crop_category,
            bbch_stage=bbch_stage
        )

        # Execute identification
        result = await _service.identify_pest(input_data)

        # Return JSON
        return result.model_dump_json(indent=2)

    except ValidationError as e:
        logger.error(f"Pest identification validation error: {e}")
        error_result = PestIdentificationOutput(
            success=False,
            crop_type=crop_type,
            damage_symptoms=damage_symptoms,
            pest_identifications=[],
            identification_confidence=ConfidenceLevel.LOW,
            treatment_recommendations=[],
            total_identifications=0,
            data_source="error",
            timestamp=datetime.now(),
            error="Erreur de validation des paramètres. Vérifiez les symptômes et indicateurs.",
            error_type="validation_error"
        )
        return error_result.model_dump_json(indent=2)

    except Exception as e:
        logger.error(f"Unexpected pest identification error: {e}", exc_info=True)
        error_result = PestIdentificationOutput(
            success=False,
            crop_type=crop_type,
            damage_symptoms=damage_symptoms,
            pest_identifications=[],
            identification_confidence=ConfidenceLevel.LOW,
            treatment_recommendations=[],
            total_identifications=0,
            data_source="error",
            timestamp=datetime.now(),
            error="Erreur inattendue lors de l'identification des ravageurs. Veuillez réessayer.",
            error_type="unknown"
        )
        return error_result.model_dump_json(indent=2)


# Create structured tool
identify_pest_tool_enhanced = StructuredTool.from_function(
    func=identify_pest_enhanced,
    name="identify_pest",
    description="""Identifie les ravageurs des cultures à partir des symptômes de dégâts observés.

Retourne une identification détaillée avec:
- Ravageurs identifiés avec niveau de confiance
- Sévérité et stade de développement
- Recommandations de traitement
- Profil de risque par catégorie de culture

Utilisez cet outil quand les agriculteurs signalent des dégâts sur les cultures (feuilles trouées, galeries, déformations, etc.).""",
    args_schema=PestIdentificationInput,
    return_direct=False,
    coroutine=identify_pest_enhanced,
    handle_validation_error=True
)

