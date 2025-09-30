"""
Enhanced Pest Identification Tool

Integrates with Phase 2 database (Crop table + EPPO codes) for:
- Standardized crop identification
- Crop category-based risk assessment
- EPPO code integration
- Pydantic validation
- Redis caching
- Structured error handling
"""

from typing import Optional, List, Dict, Any
from langchain.tools import BaseTool
import logging
from datetime import datetime
import asyncio

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
from app.core.caching import redis_cache
from app.core.errors import DataError, ValidationError, APIError
from app.services.knowledge_base_service import KnowledgeBaseService

logger = logging.getLogger(__name__)


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


class IdentifyPestToolEnhanced(BaseTool):
    """
    Enhanced pest identification tool with Phase 2 database integration.
    
    Features:
    - Crop table integration with EPPO codes
    - Crop category-based risk assessment
    - Pydantic validation
    - Redis caching
    - Structured error handling
    """
    
    name: str = "identify_pest"
    description: str = "Identifie les ravageurs des cultures avec intégration base de données et codes EPPO"
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._knowledge_service = None
    
    @property
    def knowledge_service(self):
        """Lazy load knowledge service"""
        if self._knowledge_service is None:
            self._knowledge_service = KnowledgeBaseService()
        return self._knowledge_service
    
    @redis_cache(ttl=3600, category="crop_health")
    async def execute(self, input_data: PestIdentificationInput) -> PestIdentificationOutput:
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
                raise DataError(
                    f"Culture inconnue: {input_data.crop_type}",
                    error_type="crop_not_found"
                )
            
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
            
            # Step 5: Calculate overall confidence
            overall_confidence = self._calculate_overall_confidence(enhanced_identifications)
            
            # Step 6: Consolidate treatment recommendations
            treatment_recommendations = self._consolidate_treatments(enhanced_identifications)
            
            # Step 7: Build output
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
            
        except (DataError, ValidationError) as e:
            logger.error(f"Pest identification error: {e}")
            return PestIdentificationOutput(
                success=False,
                crop_type=input_data.crop_type,
                damage_symptoms=input_data.damage_symptoms,
                pest_identifications=[],
                identification_confidence=ConfidenceLevel.LOW,
                treatment_recommendations=[],
                total_identifications=0,
                data_source="error",
                error=str(e),
                error_type=getattr(e, 'error_type', 'unknown_error')
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
            
            identification = PestIdentification(
                pest_name=pest_data.get("name", "Unknown"),
                scientific_name=pest_data.get("scientific_name"),
                pest_type=PestType(pest_data.get("type", "unknown")),
                pest_stage=PestStage(pest_data.get("stage", "unknown")) if pest_data.get("stage") else None,
                confidence=pest_result.get("confidence_score", 0.5),
                severity=PestSeverity(pest_data.get("severity_level", "moderate")),
                damage_patterns=pest_result.get("matching_damage", []),
                treatment_recommendations=pest_data.get("treatment_options", []),
                prevention_measures=pest_data.get("prevention_methods", []),
                eppo_code=pest_data.get("eppo_code"),
                susceptible_bbch_stages=pest_data.get("susceptible_stages"),
                economic_threshold=pest_data.get("economic_threshold"),
                natural_enemies=pest_data.get("natural_enemies"),
                monitoring_methods=pest_data.get("monitoring_methods")
            )
            
            identifications.append(identification)
        
        # Add category-based insights if no database results
        if not identifications and risk_profile:
            identifications.append(
                PestIdentification(
                    pest_name=f"Ravageurs communs ({risk_profile.category})",
                    scientific_name=None,
                    pest_type=PestType.UNKNOWN,
                    confidence=0.4,
                    severity=PestSeverity.MODERATE,
                    damage_patterns=[],
                    treatment_recommendations=[
                        f"Surveiller: {', '.join(risk_profile.common_pests[:3])}"
                    ],
                    prevention_measures=risk_profile.prevention_strategies or []
                )
            )
        
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
        """Consolidate treatment recommendations"""
        treatments = set()
        for identification in identifications:
            treatments.update(identification.treatment_recommendations)
        return list(treatments)
    
    def _run(self, **kwargs) -> str:
        """Sync wrapper for LangChain compatibility"""
        try:
            # Validate input
            input_data = PestIdentificationInput(**kwargs)
            
            # Run async execute in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                output = loop.run_until_complete(self.execute(input_data))
                return output.model_dump_json(exclude_none=True)
            finally:
                loop.close()
                
        except Exception as e:
            logger.error(f"Error in _run: {e}")
            error_output = PestIdentificationOutput(
                success=False,
                crop_type=kwargs.get("crop_type", "unknown"),
                damage_symptoms=kwargs.get("damage_symptoms", []),
                pest_identifications=[],
                identification_confidence=ConfidenceLevel.LOW,
                treatment_recommendations=[],
                total_identifications=0,
                data_source="error",
                error=str(e),
                error_type="execution_error"
            )
            return error_output.model_dump_json(exclude_none=True)
    
    async def _arun(self, **kwargs) -> str:
        """Async wrapper for LangChain compatibility"""
        try:
            input_data = PestIdentificationInput(**kwargs)
            output = await self.execute(input_data)
            return output.model_dump_json(exclude_none=True)
        except Exception as e:
            logger.error(f"Error in _arun: {e}")
            error_output = PestIdentificationOutput(
                success=False,
                crop_type=kwargs.get("crop_type", "unknown"),
                damage_symptoms=kwargs.get("damage_symptoms", []),
                pest_identifications=[],
                identification_confidence=ConfidenceLevel.LOW,
                treatment_recommendations=[],
                total_identifications=0,
                data_source="error",
                error=str(e),
                error_type="execution_error"
            )
            return error_output.model_dump_json(exclude_none=True)


# Create tool instance
identify_pest_tool_enhanced = IdentifyPestToolEnhanced()

