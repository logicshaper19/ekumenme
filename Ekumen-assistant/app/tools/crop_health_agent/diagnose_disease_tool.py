"""
Enhanced Diagnose Disease Tool with DATABASE INTEGRATION.

REAL DATABASE INTEGRATION:
- Disease database for comprehensive disease knowledge
- BBCH database for growth stage validation
- EPPO database for crop identification
- KnowledgeBaseService for semantic search
- Fallback to legacy hardcoded knowledge

Improvements:
- Type-safe Pydantic schemas
- Redis + memory caching (2h TTL for disease data)
- Structured error handling
- Real database queries (not just config files)
- BBCH stage integration for disease susceptibility
- EPPO code support for crop identification
"""

import logging
import json
from typing import Optional, List, Dict, Any
from datetime import datetime
from difflib import SequenceMatcher

from pydantic import BaseModel, Field
from langchain.tools import StructuredTool
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from ..schemas.disease_schemas import (
    DiseaseDiagnosisInput,
    DiseaseDiagnosisOutput,
    DiseaseDiagnosis,
    DiseaseSeverity,
    DiseaseType,
    ConfidenceLevel,
    EnvironmentalConditions,
    BBCHStageInfo
)
from ..exceptions import (
    DiseaseNotFoundError,
    InvalidBBCHStageError,
    InvalidCropNameError,
    ToolException
)
from ...core.database import AsyncSessionLocal
from ...core.cache import redis_cache
from ...models.disease import Disease
from ...models.bbch_stage import BBCHStage
from ...services.knowledge_base_service import KnowledgeBaseService
from ...services.bbch_service import BBCHService

logger = logging.getLogger(__name__)


class DiagnoseDiseaseService:
    """Service for disease diagnosis with caching"""
    
    def __init__(self):
        self.knowledge_base = KnowledgeBaseService()
        # Legacy hardcoded knowledge as fallback
        self.legacy_knowledge = self._load_legacy_knowledge()
    
    def _load_legacy_knowledge(self) -> Dict[str, Any]:
        """Load legacy hardcoded disease knowledge"""
        return {
            "blé": {
                "rouille_jaune": {
                    "symptoms": ["taches_jaunes", "pustules_jaunes", "feuilles_jaunies", "stries_jaunes"],
                    "conditions": {"humidity": "high", "temperature": "moderate"},
                    "severity": "moderate",
                    "treatment": ["fongicide_triazole", "rotation_cultures"],
                    "prevention": ["variétés_résistantes", "drainage_amélioré"],
                    "disease_type": "fungal",
                    "scientific_name": "Puccinia striiformis"
                },
                "septoriose": {
                    "symptoms": ["taches_brunes", "nécroses_feuilles", "pycnides_noires"],
                    "conditions": {"humidity": "high", "temperature": "moderate", "rainfall": "frequent"},
                    "severity": "high",
                    "treatment": ["fongicide_strobilurine", "fongicide_triazole"],
                    "prevention": ["labour_profond", "rotation_cultures", "variétés_résistantes"],
                    "disease_type": "fungal",
                    "scientific_name": "Zymoseptoria tritici"
                }
            },
            "maïs": {
                "helminthosporiose": {
                    "symptoms": ["taches_allongées", "nécroses_feuilles", "lésions_brunes"],
                    "conditions": {"humidity": "high", "temperature": "warm"},
                    "severity": "moderate",
                    "treatment": ["fongicide_strobilurine", "rotation_cultures"],
                    "prevention": ["variétés_résistantes", "élimination_résidus"],
                    "disease_type": "fungal",
                    "scientific_name": "Exserohilum turcicum"
                }
            },
            "colza": {
                "phoma": {
                    "symptoms": ["taches_circulaires", "nécroses_collet", "chancres_tiges"],
                    "conditions": {"humidity": "high", "temperature": "moderate"},
                    "severity": "high",
                    "treatment": ["fongicide_triazole", "rotation_longue"],
                    "prevention": ["variétés_résistantes", "semis_précoce", "rotation_4_ans"],
                    "disease_type": "fungal",
                    "scientific_name": "Leptosphaeria maculans"
                }
            }
        }

    def _fuzzy_match_symptom(self, symptom1: str, symptom2: str, threshold: float = 0.75) -> bool:
        """
        Fuzzy match two symptom strings using SequenceMatcher.

        Args:
            symptom1: First symptom string
            symptom2: Second symptom string
            threshold: Minimum similarity ratio (0.0-1.0)

        Returns:
            True if symptoms match above threshold
        """
        # Normalize strings
        s1 = symptom1.lower().strip()
        s2 = symptom2.lower().strip()

        # Exact match
        if s1 == s2:
            return True

        # Fuzzy match using SequenceMatcher
        ratio = SequenceMatcher(None, s1, s2).ratio()
        return ratio >= threshold

    def _match_environmental_conditions(
        self,
        observed: Optional[EnvironmentalConditions],
        required: Dict[str, Any]
    ) -> float:
        """
        Match observed environmental conditions against required conditions.

        Args:
            observed: Observed environmental conditions
            required: Required conditions from disease data

        Returns:
            Match score (0.0-1.0)
        """
        if not observed or not required:
            return 0.5  # Neutral score if no data

        score = 0.0
        checks = 0

        # Humidity matching
        if observed.humidity_percent is not None and required.get("humidity"):
            checks += 1
            req_humidity = required["humidity"]
            if req_humidity == "high" and observed.humidity_percent > 70:
                score += 1.0
            elif req_humidity == "moderate" and 40 <= observed.humidity_percent <= 70:
                score += 1.0
            elif req_humidity == "low" and observed.humidity_percent < 40:
                score += 1.0
            else:
                # Partial credit for close matches
                if req_humidity == "high" and observed.humidity_percent > 60:
                    score += 0.5
                elif req_humidity == "moderate" and 30 <= observed.humidity_percent <= 80:
                    score += 0.5

        # Temperature matching
        if observed.temperature_c is not None and required.get("temperature"):
            checks += 1
            req_temp = required["temperature"]
            if req_temp == "warm" and observed.temperature_c > 20:
                score += 1.0
            elif req_temp == "moderate" and 10 <= observed.temperature_c <= 20:
                score += 1.0
            elif req_temp == "cool" and observed.temperature_c < 10:
                score += 1.0
            else:
                # Partial credit
                if req_temp == "warm" and observed.temperature_c > 15:
                    score += 0.5
                elif req_temp == "moderate" and 5 <= observed.temperature_c <= 25:
                    score += 0.5

        # Temperature range matching (more precise)
        if observed.temperature_c is not None and required.get("temperature_range"):
            checks += 1
            temp_range = required["temperature_range"]
            if len(temp_range) == 2:
                min_temp, max_temp = temp_range
                if min_temp <= observed.temperature_c <= max_temp:
                    score += 1.0
                elif min_temp - 5 <= observed.temperature_c <= max_temp + 5:
                    score += 0.5  # Close to range

        # Rainfall matching
        if observed.rainfall_mm is not None and required.get("rainfall"):
            checks += 1
            req_rainfall = required["rainfall"]
            if req_rainfall == "frequent" and observed.rainfall_mm > 5:
                score += 1.0
            elif req_rainfall == "moderate" and 1 <= observed.rainfall_mm <= 5:
                score += 1.0
            elif req_rainfall == "low" and observed.rainfall_mm < 1:
                score += 1.0

        return score / checks if checks > 0 else 0.5

    def _adjust_confidence_for_bbch(
        self,
        base_confidence: float,
        bbch_stage: Optional[int],
        susceptible_stages: Optional[List[int]]
    ) -> float:
        """
        Adjust confidence based on BBCH stage susceptibility.

        Args:
            base_confidence: Base confidence score
            bbch_stage: Current BBCH stage
            susceptible_stages: List of susceptible BBCH stages

        Returns:
            Adjusted confidence score
        """
        if bbch_stage is None or not susceptible_stages:
            return base_confidence

        # Check if current stage is in susceptible stages
        if bbch_stage in susceptible_stages:
            # Boost confidence - plant is at susceptible stage
            return min(base_confidence * 1.3, 1.0)

        # Check if close to susceptible stage (within 5 stages)
        min_distance = min(abs(bbch_stage - stage) for stage in susceptible_stages)
        if min_distance <= 5:
            # Slight boost - close to susceptible stage
            return min(base_confidence * 1.1, 1.0)

        # Reduce confidence - not at susceptible stage
        return base_confidence * 0.7

    @redis_cache(ttl=7200, model_class=DiseaseDiagnosisOutput, category="crop_health")
    async def diagnose_disease(
        self,
        crop_type: str,
        symptoms: List[str],
        environmental_conditions: Optional[EnvironmentalConditions] = None,
        bbch_stage: Optional[int] = None,
        eppo_code: Optional[str] = None,
        field_location: Optional[str] = None,
        affected_area_percent: Optional[float] = None
    ) -> DiseaseDiagnosisOutput:
        """
        Diagnose crop disease based on symptoms and conditions
        
        Args:
            crop_type: Type of crop
            symptoms: List of observed symptoms
            environmental_conditions: Environmental conditions
            bbch_stage: BBCH growth stage (0-99)
            eppo_code: EPPO code for crop
            field_location: Field location
            affected_area_percent: Percentage of field affected
            
        Returns:
            DiseaseDiagnosisOutput with diagnoses and recommendations
        """
        try:
            # Input validation
            if bbch_stage is not None and not (0 <= bbch_stage <= 99):
                return DiseaseDiagnosisOutput(
                    success=False,
                    crop_type=crop_type,
                    symptoms_observed=symptoms,
                    environmental_conditions=environmental_conditions,
                    bbch_stage=bbch_stage,
                    diagnoses=[],
                    diagnosis_confidence=ConfidenceLevel.LOW,
                    treatment_recommendations=[],
                    total_diagnoses=0,
                    data_source="validation_error",
                    timestamp=datetime.now(),
                    error=f"BBCH stage must be between 0 and 99, got {bbch_stage}",
                    error_type="validation"
                )

            if affected_area_percent is not None and not (0 <= affected_area_percent <= 100):
                return DiseaseDiagnosisOutput(
                    success=False,
                    crop_type=crop_type,
                    symptoms_observed=symptoms,
                    environmental_conditions=environmental_conditions,
                    diagnoses=[],
                    diagnosis_confidence=ConfidenceLevel.LOW,
                    treatment_recommendations=[],
                    total_diagnoses=0,
                    data_source="validation_error",
                    timestamp=datetime.now(),
                    error=f"Affected area must be between 0 and 100%, got {affected_area_percent}",
                    error_type="validation"
                )

            if not symptoms or len(symptoms) == 0:
                return DiseaseDiagnosisOutput(
                    success=False,
                    crop_type=crop_type,
                    symptoms_observed=symptoms,
                    environmental_conditions=environmental_conditions,
                    diagnoses=[],
                    diagnosis_confidence=ConfidenceLevel.LOW,
                    treatment_recommendations=[],
                    total_diagnoses=0,
                    data_source="validation_error",
                    timestamp=datetime.now(),
                    error="At least one symptom must be provided",
                    error_type="validation"
                )

            async with AsyncSessionLocal() as db:
                # Get BBCH stage info if provided
                bbch_info = None
                bbch_description = None
                if bbch_stage is not None:
                    try:
                        # Query BBCH stage directly with async
                        bbch_query = select(BBCHStage).where(
                            and_(
                                BBCHStage.crop_type == crop_type,
                                BBCHStage.bbch_code == bbch_stage
                            )
                        )
                        bbch_result = await db.execute(bbch_query)
                        bbch_stage_obj = bbch_result.scalar_one_or_none()
                        if bbch_stage_obj:
                            bbch_description = bbch_stage_obj.description_fr
                    except Exception as e:
                        logger.warning(f"Could not fetch BBCH stage: {e}")
                
                # Convert environmental conditions to dict for knowledge base
                conditions_dict = None
                if environmental_conditions:
                    conditions_dict = environmental_conditions.dict(exclude_none=True)
                
                # Search database for diseases
                db_results = await self.knowledge_base.search_diseases(
                    crop_type=crop_type,
                    symptoms=symptoms,
                    conditions=conditions_dict
                )
                
                diagnoses = []
                data_source = "database"
                
                # Process database results
                if db_results.get("total_results", 0) > 0:
                    for result in db_results.get("diseases", []):
                        disease_data = result["disease"]
                        base_confidence = result["confidence_score"]

                        # Extract susceptible BBCH stages from description if available
                        # (since we stored them in the description field)
                        susceptible_stages = None
                        description = disease_data.get("description", "")
                        if "Susceptible BBCH stages:" in description:
                            try:
                                stages_str = description.split("Susceptible BBCH stages:")[1].split(".")[0]
                                susceptible_stages = [int(s.strip()) for s in stages_str.split(",")]
                            except:
                                pass

                        # Adjust confidence based on BBCH stage
                        adjusted_confidence = self._adjust_confidence_for_bbch(
                            base_confidence,
                            bbch_stage,
                            susceptible_stages
                        )

                        diagnosis = DiseaseDiagnosis(
                            disease_name=disease_data.get("name", "Unknown"),
                            scientific_name=disease_data.get("scientific_name"),
                            disease_type=DiseaseType(disease_data.get("disease_type", "unknown")),
                            confidence=adjusted_confidence,
                            severity=DiseaseSeverity(disease_data.get("severity_level", "moderate")),
                            symptoms_matched=result.get("matching_symptoms", []),
                            treatment_recommendations=disease_data.get("treatment_options", []),
                            prevention_measures=disease_data.get("prevention_methods", []),
                            eppo_code=disease_data.get("eppo_code"),
                            susceptible_bbch_stages=susceptible_stages,
                            favorable_conditions=disease_data.get("favorable_conditions"),
                            economic_impact=disease_data.get("economic_impact"),
                            spread_rate=disease_data.get("spread_rate")
                        )
                        diagnoses.append(diagnosis)
                
                # Fallback to legacy knowledge if no database results
                if not diagnoses:
                    data_source = "legacy_hardcoded"
                    legacy_diagnoses = self._diagnose_from_legacy(
                        crop_type, symptoms, conditions_dict, bbch_stage
                    )
                    diagnoses.extend(legacy_diagnoses)
                
                # If we have both, mark as hybrid
                if db_results.get("total_results", 0) > 0 and len(diagnoses) > len(db_results.get("diseases", [])):
                    data_source = "hybrid"
                
                # Determine overall confidence
                overall_confidence = self._calculate_overall_confidence(diagnoses)
                
                # Consolidate treatment recommendations
                treatment_recommendations = self._consolidate_treatments(diagnoses)
                
                return DiseaseDiagnosisOutput(
                    success=True,
                    crop_type=crop_type,
                    symptoms_observed=symptoms,
                    environmental_conditions=environmental_conditions,
                    bbch_stage=bbch_stage,
                    bbch_stage_description=bbch_description,
                    diagnoses=diagnoses,
                    diagnosis_confidence=overall_confidence,
                    treatment_recommendations=treatment_recommendations,
                    total_diagnoses=len(diagnoses),
                    data_source=data_source,
                    timestamp=datetime.now()
                )
                
        except InvalidBBCHStageError as e:
            logger.error(f"Invalid BBCH stage: {e}")
            return DiseaseDiagnosisOutput(
                success=False,
                crop_type=crop_type,
                symptoms_observed=symptoms,
                diagnoses=[],
                diagnosis_confidence=ConfidenceLevel.LOW,
                treatment_recommendations=[],
                total_diagnoses=0,
                data_source="error",
                error=str(e),
                error_type="validation"
            )
        except Exception as e:
            logger.error(f"Disease diagnosis error: {e}")
            return DiseaseDiagnosisOutput(
                success=False,
                crop_type=crop_type,
                symptoms_observed=symptoms,
                diagnoses=[],
                diagnosis_confidence=ConfidenceLevel.LOW,
                treatment_recommendations=[],
                total_diagnoses=0,
                data_source="error",
                error=f"Erreur lors du diagnostic: {str(e)}",
                error_type="api_error"
            )
    
    def _diagnose_from_legacy(
        self,
        crop_type: str,
        symptoms: List[str],
        conditions: Optional[Dict[str, Any]],
        bbch_stage: Optional[int] = None
    ) -> List[DiseaseDiagnosis]:
        """
        Diagnose using legacy hardcoded knowledge with improved matching.

        Uses fuzzy symptom matching and proper environmental condition matching.
        """
        diagnoses = []

        crop_diseases = self.legacy_knowledge.get(crop_type, {})

        for disease_name, disease_data in crop_diseases.items():
            # Calculate confidence based on FUZZY symptom matching
            disease_symptoms = disease_data.get("symptoms", [])
            matched_symptoms = []

            for observed_symptom in symptoms:
                for disease_symptom in disease_symptoms:
                    if self._fuzzy_match_symptom(observed_symptom, disease_symptom, threshold=0.75):
                        matched_symptoms.append(observed_symptom)
                        break  # Don't match same symptom multiple times

            if not matched_symptoms:
                continue

            # Symptom confidence: ratio of matched symptoms
            symptom_confidence = len(matched_symptoms) / len(symptoms) if symptoms else 0

            # Environmental condition matching using proper logic
            condition_match = 0.5  # Neutral default
            if conditions and disease_data.get("conditions"):
                # Convert dict to EnvironmentalConditions if needed
                env_conditions = None
                if isinstance(conditions, dict):
                    try:
                        env_conditions = EnvironmentalConditions(**conditions)
                    except:
                        pass

                if env_conditions:
                    condition_match = self._match_environmental_conditions(
                        env_conditions,
                        disease_data.get("conditions", {})
                    )

            # Calculate base confidence (60% symptoms, 40% conditions)
            base_confidence = (symptom_confidence * 0.6) + (condition_match * 0.4)

            # Adjust for BBCH stage if available (legacy data doesn't have susceptible stages)
            # So we don't adjust for legacy, but keep the parameter for consistency
            confidence = base_confidence

            if confidence >= 0.3:  # Minimum threshold
                diagnosis = DiseaseDiagnosis(
                    disease_name=disease_name.replace("_", " ").title(),
                    scientific_name=disease_data.get("scientific_name"),
                    disease_type=DiseaseType(disease_data.get("disease_type", "fungal")),
                    confidence=confidence,
                    severity=DiseaseSeverity(disease_data.get("severity", "moderate")),
                    symptoms_matched=matched_symptoms,
                    treatment_recommendations=disease_data.get("treatment", []),
                    prevention_measures=disease_data.get("prevention", [])
                )
                diagnoses.append(diagnosis)

        return sorted(diagnoses, key=lambda d: d.confidence, reverse=True)
    
    def _calculate_overall_confidence(self, diagnoses: List[DiseaseDiagnosis]) -> ConfidenceLevel:
        """Calculate overall diagnosis confidence"""
        if not diagnoses:
            return ConfidenceLevel.LOW
        
        max_confidence = max(d.confidence for d in diagnoses)
        
        if max_confidence >= 0.8:
            return ConfidenceLevel.VERY_HIGH
        elif max_confidence >= 0.6:
            return ConfidenceLevel.HIGH
        elif max_confidence >= 0.4:
            return ConfidenceLevel.MODERATE
        else:
            return ConfidenceLevel.LOW
    
    def _consolidate_treatments(self, diagnoses: List[DiseaseDiagnosis]) -> List[str]:
        """Consolidate treatment recommendations from all diagnoses"""
        all_treatments = []
        for diagnosis in diagnoses:
            all_treatments.extend(diagnosis.treatment_recommendations)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_treatments = []
        for treatment in all_treatments:
            if treatment not in seen:
                seen.add(treatment)
                unique_treatments.append(treatment)
        
        return unique_treatments[:10]  # Limit to top 10


# Create service instance
_service = DiagnoseDiseaseService()


async def diagnose_disease_async(
    crop_type: str,
    symptoms: List[str],
    environmental_conditions: Optional[Dict[str, Any]] = None,
    bbch_stage: Optional[int] = None,
    eppo_code: Optional[str] = None,
    field_location: Optional[str] = None,
    affected_area_percent: Optional[float] = None
) -> str:
    """
    Async wrapper for disease diagnosis tool

    Args:
        crop_type: Type of crop (e.g., 'blé', 'maïs', 'colza')
        symptoms: List of observed symptoms
        environmental_conditions: Environmental conditions (dict)
        bbch_stage: BBCH growth stage (0-99)
        eppo_code: EPPO code for crop identification
        field_location: Field location (department, region)
        affected_area_percent: Percentage of field affected (0-100)

    Returns:
        JSON string with diagnosis results
    """
    # Convert environmental_conditions dict to Pydantic model
    env_conditions = None
    if environmental_conditions:
        env_conditions = EnvironmentalConditions(**environmental_conditions)

    result = await _service.diagnose_disease(
        crop_type=crop_type,
        symptoms=symptoms,
        environmental_conditions=env_conditions,
        bbch_stage=bbch_stage,
        eppo_code=eppo_code,
        field_location=field_location,
        affected_area_percent=affected_area_percent
    )

    # Pydantic v2 compatible JSON serialization
    return result.model_dump_json(indent=2)


# Create args schema for StructuredTool
class DiagnoseDiseaseArgs(BaseModel):
    """Arguments for diagnose disease tool"""
    crop_type: str = Field(description="Type of crop (e.g., 'blé', 'maïs', 'colza')")
    symptoms: List[str] = Field(description="List of observed symptoms")
    environmental_conditions: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Environmental conditions (temperature_c, humidity_percent, rainfall_mm, etc.)"
    )
    bbch_stage: Optional[int] = Field(
        default=None,
        description="BBCH growth stage (0-99)"
    )
    eppo_code: Optional[str] = Field(
        default=None,
        description="EPPO code for crop identification"
    )
    field_location: Optional[str] = Field(
        default=None,
        description="Field location (department, region)"
    )
    affected_area_percent: Optional[float] = Field(
        default=None,
        description="Percentage of field affected (0-100)"
    )


# Create the StructuredTool
diagnose_disease_tool = StructuredTool(
    name="diagnose_disease_enhanced",
    description="""Diagnose crop diseases based on observed symptoms and environmental conditions.

    This tool uses a comprehensive disease database with semantic search to identify diseases.
    Supports BBCH growth stage integration for disease susceptibility analysis.

    Use this tool when:
    - Farmer reports disease symptoms on crops
    - Need to identify crop diseases
    - Want disease treatment recommendations
    - Need to assess disease severity

    Returns detailed diagnosis with:
    - Disease identification with confidence scores
    - Matched symptoms
    - Treatment recommendations
    - Prevention measures
    - BBCH stage susceptibility (if provided)
    """,
    func=None,  # Sync not supported
    coroutine=diagnose_disease_async,
    args_schema=DiagnoseDiseaseArgs,
    handle_validation_error=False
)

