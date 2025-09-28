"""
Generate Treatment Plan Tool - Vector Database Ready Tool

Job: Generate comprehensive treatment plans from disease, pest, and nutrient analyses.
Input: JSON strings from other crop health tools
Output: JSON string with comprehensive treatment plan

This tool does ONLY:
- Execute specific, well-defined function
- Take structured inputs, return structured outputs
- Contain domain-specific business logic
- Be stateless and reusable

Enhanced Features:
- External knowledge base (JSON file)
- Configurable analysis parameters
- Asynchronous support
- Comprehensive input validation
- Vector database ready architecture
- Semantic search capabilities

No prompting logic, no orchestration, no agent responsibilities.
"""

from typing import Dict, List, Any, Optional, Union
from langchain.tools import BaseTool
import logging
import json
import asyncio
import aiofiles
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from pathlib import Path
import os

# Import configuration system
from ...config.treatment_plan_config import (
    get_treatment_plan_config, 
    get_treatment_validation_config,
    TreatmentPlanConfig,
    TreatmentValidationConfig
)

# Import vector database interface
from ...data.treatment_vector_db_interface import (
    get_treatment_knowledge_base,
    set_treatment_knowledge_base,
    TreatmentKnowledgeBaseInterface,
    TreatmentKnowledge,
    TreatmentSearchResult
)

logger = logging.getLogger(__name__)

@dataclass
class TreatmentStep:
    """Structured treatment step."""
    step_name: str
    description: str
    priority: str
    timing: str
    cost_estimate: float
    effectiveness: str
    treatment_type: str
    application_method: str
    safety_class: str
    environmental_impact: str
    waiting_period: str
    compatibility: List[str]
    search_metadata: Optional[Dict[str, Any]] = None

@dataclass
class ValidationError:
    """Validation error information."""
    field: str
    message: str
    severity: str  # "error", "warning", "info"

class GenerateTreatmentPlanTool(BaseTool):
    """
    Vector Database Ready Tool: Generate comprehensive treatment plans from disease, pest, and nutrient analyses.
    
    Job: Take results from other crop health tools and generate comprehensive treatment plan.
    Input: JSON strings from other crop health tools
    Output: JSON string with comprehensive treatment plan
    
    Enhanced Features:
    - External knowledge base (JSON file)
    - Configurable analysis parameters
    - Asynchronous support
    - Comprehensive input validation
    - Vector database ready architecture
    - Semantic search capabilities
    """
    
    name: str = "generate_treatment_plan_tool"
    description: str = "Génère un plan de traitement complet pour la santé des cultures avec recherche sémantique"
    
    def __init__(
        self, 
        knowledge_base_path: Optional[str] = None,
        use_vector_search: bool = False,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.knowledge_base_path = knowledge_base_path or self._get_default_knowledge_path()
        self.use_vector_search = use_vector_search
        self._config_cache: Optional[TreatmentPlanConfig] = None
        self._validation_cache: Optional[TreatmentValidationConfig] = None
        self._knowledge_base: Optional[TreatmentKnowledgeBaseInterface] = None
    
    def _get_default_knowledge_path(self) -> str:
        """Get default knowledge base file path."""
        current_dir = Path(__file__).parent
        return str(current_dir.parent.parent / "data" / "treatment_plan_knowledge.json")
    
    def _get_knowledge_base(self) -> TreatmentKnowledgeBaseInterface:
        """Get knowledge base instance."""
        if self._knowledge_base is None:
            if self.use_vector_search:
                # Use vector database (when implemented)
                self._knowledge_base = get_treatment_knowledge_base()
            else:
                # Use JSON knowledge base
                from ...data.treatment_vector_db_interface import JSONTreatmentKnowledgeBase
                self._knowledge_base = JSONTreatmentKnowledgeBase(self.knowledge_base_path)
        return self._knowledge_base
    
    def _get_config(self) -> TreatmentPlanConfig:
        """Get current treatment configuration."""
        if self._config_cache is None:
            self._config_cache = get_treatment_plan_config()
        return self._config_cache
    
    def _get_validation_config(self) -> TreatmentValidationConfig:
        """Get current validation configuration."""
        if self._validation_cache is None:
            self._validation_cache = get_treatment_validation_config()
        return self._validation_cache
    
    def _validate_inputs(
        self, 
        disease_analysis_json: Optional[str], 
        pest_analysis_json: Optional[str], 
        nutrient_analysis_json: Optional[str], 
        crop_type: Optional[str]
    ) -> List[ValidationError]:
        """Validate input parameters."""
        errors = []
        validation_config = self._get_validation_config()
        
        # Check if at least one analysis is provided
        analyses_provided = any([disease_analysis_json, pest_analysis_json, nutrient_analysis_json])
        if validation_config.require_at_least_one_analysis and not analyses_provided:
            errors.append(ValidationError("analyses", "At least one analysis is required", "error"))
        
        # Validate JSON format
        if validation_config.validate_json_format:
            for analysis_name, analysis_json in [
                ("disease_analysis", disease_analysis_json),
                ("pest_analysis", pest_analysis_json),
                ("nutrient_analysis", nutrient_analysis_json)
            ]:
                if analysis_json:
                    try:
                        json.loads(analysis_json)
                        if len(analysis_json) > validation_config.max_json_size:
                            errors.append(ValidationError(analysis_name, f"JSON too large (max {validation_config.max_json_size} characters)", "warning"))
                    except json.JSONDecodeError as e:
                        errors.append(ValidationError(analysis_name, f"Invalid JSON format: {str(e)}", "error"))
        
        # Validate crop type
        if crop_type and validation_config.validate_crop_type:
            config = self._get_config()
            if crop_type.lower() not in [c.lower() for c in config.supported_crops]:
                errors.append(ValidationError("crop_type", f"Crop type '{crop_type}' not supported", "warning"))
        
        return errors
    
    async def _search_treatment_knowledge(
        self,
        disease_analysis: Optional[Dict],
        pest_analysis: Optional[Dict],
        nutrient_analysis: Optional[Dict],
        crop_type: Optional[str]
    ) -> List[TreatmentSearchResult]:
        """Search treatment knowledge using vector database or JSON fallback."""
        knowledge_base = self._get_knowledge_base()
        all_results = []
        
        # Search for disease treatments
        if disease_analysis and "diagnoses" in disease_analysis:
            for diagnosis in disease_analysis["diagnoses"]:
                if diagnosis.get("confidence", 0) > self._get_config().minimum_confidence:
                    disease_results = await knowledge_base.search_by_disease(
                        diagnosis["disease_name"], crop_type, limit=5
                    )
                    all_results.extend(disease_results)
        
        # Search for pest treatments
        if pest_analysis and "pest_identifications" in pest_analysis:
            for identification in pest_analysis["pest_identifications"]:
                if identification.get("confidence", 0) > self._get_config().minimum_confidence:
                    pest_results = await knowledge_base.search_by_pest(
                        identification["pest_name"], crop_type, limit=5
                    )
                    all_results.extend(pest_results)
        
        # Search for nutrient treatments
        if nutrient_analysis and "nutrient_deficiencies" in nutrient_analysis:
            for deficiency in nutrient_analysis["nutrient_deficiencies"]:
                if deficiency.get("confidence", 0) > self._get_config().minimum_confidence:
                    nutrient_results = await knowledge_base.search_by_nutrient(
                        deficiency["nutrient"], crop_type, limit=5
                    )
                    all_results.extend(nutrient_results)
        
        # Search for crop-specific treatments
        if crop_type:
            crop_results = await knowledge_base.search_by_crop(crop_type, limit=10)
            all_results.extend(crop_results)
        
        # Remove duplicates and sort by similarity
        unique_results = {}
        for result in all_results:
            key = result.treatment_knowledge.treatment_name
            if key not in unique_results or result.similarity_score > unique_results[key].similarity_score:
                unique_results[key] = result
        
        return list(unique_results.values())
    
    def _generate_treatment_steps(
        self, 
        search_results: List[TreatmentSearchResult],
        disease_analysis: Optional[Dict],
        pest_analysis: Optional[Dict],
        nutrient_analysis: Optional[Dict]
    ) -> List[Dict[str, Any]]:
        """Generate treatment steps based on search results and analyses."""
        treatment_steps = []
        config = self._get_config()
        
        for result in search_results:
            treatment_knowledge = result.treatment_knowledge
            
            # Determine priority based on analysis type and severity
            priority = self._calculate_priority(treatment_knowledge, disease_analysis, pest_analysis, nutrient_analysis)
            
            # Determine timing based on treatment type and urgency
            timing = self._determine_timing(treatment_knowledge, priority)
            
            # Calculate cost with configurable factors
            cost_estimate = self._calculate_treatment_cost(treatment_knowledge, config)
            
            # Determine effectiveness based on confidence and treatment type
            effectiveness = self._determine_effectiveness(treatment_knowledge, result.similarity_score)
            
            step = TreatmentStep(
                step_name=f"Traitement {treatment_knowledge.category}: {treatment_knowledge.treatment_name}",
                description=f"Application de {treatment_knowledge.treatment_name} - {treatment_knowledge.application_method}",
                priority=priority,
                timing=timing,
                cost_estimate=cost_estimate,
                effectiveness=effectiveness,
                treatment_type=treatment_knowledge.category,
                application_method=treatment_knowledge.application_method,
                safety_class=treatment_knowledge.safety_class,
                environmental_impact=treatment_knowledge.environmental_impact,
                waiting_period=treatment_knowledge.waiting_period,
                compatibility=treatment_knowledge.compatibility,
                search_metadata={
                    "search_method": "vector" if self.use_vector_search else "json",
                    "similarity_score": result.similarity_score,
                    "match_type": result.match_type
                }
            )
            treatment_steps.append(asdict(step))
        
        # Sort by priority and limit results
        treatment_steps.sort(key=lambda x: 0 if x["priority"] == "high" else 1 if x["priority"] == "moderate" else 2)
        return treatment_steps[:config.max_treatment_steps]
    
    def _calculate_priority(
        self, 
        treatment_knowledge: TreatmentKnowledge,
        disease_analysis: Optional[Dict],
        pest_analysis: Optional[Dict],
        nutrient_analysis: Optional[Dict]
    ) -> str:
        """Calculate treatment priority based on analysis results."""
        config = self._get_config()
        
        # Check for high severity issues
        if disease_analysis and "diagnoses" in disease_analysis:
            for diagnosis in disease_analysis["diagnoses"]:
                if diagnosis.get("severity") == "high" and diagnosis.get("confidence", 0) > config.high_confidence:
                    if treatment_knowledge.treatment_name in str(diagnosis.get("treatment_recommendations", [])):
                        return "high"
        
        if pest_analysis and "pest_identifications" in pest_analysis:
            for identification in pest_analysis["pest_identifications"]:
                if identification.get("severity") == "high" and identification.get("confidence", 0) > config.high_confidence:
                    if treatment_knowledge.treatment_name in str(identification.get("treatment_recommendations", [])):
                        return "high"
        
        # Check for moderate severity issues
        if disease_analysis and "diagnoses" in disease_analysis:
            for diagnosis in disease_analysis["diagnoses"]:
                if diagnosis.get("severity") == "moderate" and diagnosis.get("confidence", 0) > config.moderate_confidence:
                    if treatment_knowledge.treatment_name in str(diagnosis.get("treatment_recommendations", [])):
                        return "moderate"
        
        if pest_analysis and "pest_identifications" in pest_analysis:
            for identification in pest_analysis["pest_identifications"]:
                if identification.get("severity") == "moderate" and identification.get("confidence", 0) > config.moderate_confidence:
                    if treatment_knowledge.treatment_name in str(identification.get("treatment_recommendations", [])):
                        return "moderate"
        
        # Default to low priority for nutrient treatments
        if treatment_knowledge.category == "nutrient_supplement":
            return "low"
        
        return "moderate"
    
    def _determine_timing(self, treatment_knowledge: TreatmentKnowledge, priority: str) -> str:
        """Determine treatment timing based on priority and treatment type."""
        if priority == "high":
            return "immédiat"
        elif priority == "moderate":
            return "prochain_arrosage"
        else:
            return "planifié"
    
    def _calculate_treatment_cost(self, treatment_knowledge: TreatmentKnowledge, config: TreatmentPlanConfig) -> float:
        """Calculate treatment cost with configurable factors."""
        base_cost = treatment_knowledge.cost_per_hectare
        return round(base_cost * config.cost_multiplier, 2)
    
    def _determine_effectiveness(self, treatment_knowledge: TreatmentKnowledge, similarity_score: float) -> str:
        """Determine treatment effectiveness based on knowledge and similarity."""
        if similarity_score > 0.8 and treatment_knowledge.effectiveness == "high":
            return "high"
        elif similarity_score > 0.6 and treatment_knowledge.effectiveness in ["high", "moderate"]:
            return "moderate"
        else:
            return "low"
    
    def _generate_executive_summary(
        self, 
        treatment_steps: List[Dict[str, Any]],
        disease_analysis: Optional[Dict],
        pest_analysis: Optional[Dict],
        nutrient_analysis: Optional[Dict]
    ) -> Dict[str, Any]:
        """Generate executive summary of treatment plan."""
        config = self._get_config()
        
        summary = {
            "total_issues_identified": 0,
            "total_treatments_recommended": len(treatment_steps),
            "priority_level": "low",
            "estimated_treatment_duration": config.low_priority_duration,
            "estimated_total_cost": sum(step["cost_estimate"] for step in treatment_steps)
        }
        
        # Count issues
        if disease_analysis and "diagnoses" in disease_analysis:
            summary["total_issues_identified"] += len(disease_analysis["diagnoses"])
        
        if pest_analysis and "pest_identifications" in pest_analysis:
            summary["total_issues_identified"] += len(pest_analysis["pest_identifications"])
        
        if nutrient_analysis and "nutrient_deficiencies" in nutrient_analysis:
            summary["total_issues_identified"] += len(nutrient_analysis["nutrient_deficiencies"])
        
        # Determine priority level
        if summary["total_issues_identified"] > config.high_priority_threshold:
            summary["priority_level"] = "high"
            summary["estimated_treatment_duration"] = config.high_priority_duration
        elif summary["total_issues_identified"] > config.moderate_priority_threshold:
            summary["priority_level"] = "moderate"
            summary["estimated_treatment_duration"] = config.moderate_priority_duration
        
        return summary
    
    def _generate_treatment_schedule(
        self, 
        treatment_steps: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate treatment schedule based on treatment steps."""
        schedule = {
            "immediate_actions": [],
            "short_term_actions": [],
            "long_term_actions": []
        }
        
        for step in treatment_steps:
            if step["priority"] == "high":
                schedule["immediate_actions"].append(step["step_name"])
            elif step["priority"] == "moderate":
                schedule["short_term_actions"].append(step["step_name"])
            else:
                schedule["long_term_actions"].append(step["step_name"])
        
        return schedule
    
    def _generate_cost_analysis(
        self, 
        treatment_steps: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate cost analysis for treatment plan."""
        config = self._get_config()
        
        total_cost = sum(step["cost_estimate"] for step in treatment_steps)
        cost_breakdown = {
            "disease_treatments": sum(step["cost_estimate"] for step in treatment_steps if step["treatment_type"] == "disease_control"),
            "pest_treatments": sum(step["cost_estimate"] for step in treatment_steps if step["treatment_type"] == "pest_control"),
            "nutrient_treatments": sum(step["cost_estimate"] for step in treatment_steps if step["treatment_type"] == "nutrient_supplement")
        }
        
        result = {
            "total_cost": round(total_cost, 2),
            "cost_breakdown": {k: round(v, 2) for k, v in cost_breakdown.items()}
        }
        
        if config.cost_per_hectare_calculation:
            result["cost_per_hectare"] = round(total_cost / config.default_hectares, 2)
        
        return result
    
    def _generate_monitoring_plan(
        self, 
        treatment_steps: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Generate monitoring plan."""
        config = self._get_config()
        
        monitoring_plan = {
            "monitoring_frequency": config.default_monitoring_frequency,
            "key_indicators": [],
            "monitoring_duration": config.default_monitoring_duration
        }
        
        # Add monitoring indicators based on treatment types
        treatment_types = set(step["treatment_type"] for step in treatment_steps)
        
        if "disease_control" in treatment_types:
            monitoring_plan["key_indicators"].extend(["symptômes_maladies", "progression_maladies"])
        
        if "pest_control" in treatment_types:
            monitoring_plan["key_indicators"].extend(["présence_ravageurs", "dégâts_ravageurs"])
        
        if "nutrient_supplement" in treatment_types:
            monitoring_plan["key_indicators"].extend(["symptômes_carences", "croissance_plantes"])
        
        return monitoring_plan
    
    def _generate_prevention_measures(
        self, 
        treatment_steps: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate prevention measures based on treatment steps."""
        prevention_measures = [
            "Mise en place de mesures préventives",
            "Surveillance accrue des cultures",
            "Amélioration des pratiques culturales"
        ]
        
        # Add specific prevention measures based on treatment types
        treatment_types = set(step["treatment_type"] for step in treatment_steps)
        
        if "disease_control" in treatment_types:
            prevention_measures.extend([
                "Rotation des cultures",
                "Variétés résistantes",
                "Drainage amélioré"
            ])
        
        if "pest_control" in treatment_types:
            prevention_measures.extend([
                "Pièges à phéromones",
                "Auxiliaires de culture",
                "Barrières physiques"
            ])
        
        if "nutrient_supplement" in treatment_types:
            prevention_measures.extend([
                "Analyse régulière du sol",
                "Fertilisation équilibrée",
                "Amendements organiques"
            ])
        
        return list(set(prevention_measures))  # Remove duplicates
    
    def _run(
        self,
        disease_analysis_json: Optional[str] = None,
        pest_analysis_json: Optional[str] = None,
        nutrient_analysis_json: Optional[str] = None,
        crop_type: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Generate comprehensive treatment plan from crop health analyses.
        
        Args:
            disease_analysis_json: JSON string from DiagnoseDiseaseTool (optional)
            pest_analysis_json: JSON string from IdentifyPestTool (optional)
            nutrient_analysis_json: JSON string from AnalyzeNutrientDeficiencyTool (optional)
            crop_type: Type of crop for crop-specific recommendations
        """
        try:
            # Validate inputs
            validation_errors = self._validate_inputs(
                disease_analysis_json, pest_analysis_json, nutrient_analysis_json, crop_type
            )
            validation_config = self._get_validation_config()
            
            if validation_errors and validation_config.strict_validation:
                error_messages = [f"{error.field}: {error.message}" for error in validation_errors if error.severity == "error"]
                if error_messages:
                    return json.dumps({
                        "error": "Validation errors",
                        "validation_errors": error_messages
                    })
            
            # Parse input data
            disease_analysis = json.loads(disease_analysis_json) if disease_analysis_json else None
            pest_analysis = json.loads(pest_analysis_json) if pest_analysis_json else None
            nutrient_analysis = json.loads(nutrient_analysis_json) if nutrient_analysis_json else None
            
            # Search treatment knowledge
            search_results = asyncio.run(self._search_treatment_knowledge(
                disease_analysis, pest_analysis, nutrient_analysis, crop_type
            ))
            
            if not search_results:
                return json.dumps({
                    "error": "No treatment recommendations found",
                    "suggestions": ["Check analysis data", "Verify crop type", "Ensure valid diagnoses"]
                })
            
            # Generate treatment steps
            treatment_steps = self._generate_treatment_steps(
                search_results, disease_analysis, pest_analysis, nutrient_analysis
            )
            
            # Generate comprehensive treatment plan
            treatment_plan = {
                "plan_metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "plan_type": "crop_health_treatment",
                    "version": "2.0",
                    "crop_type": crop_type,
                    "search_method": "vector" if self.use_vector_search else "json"
                },
                "executive_summary": self._generate_executive_summary(
                    treatment_steps, disease_analysis, pest_analysis, nutrient_analysis
                ),
                "treatment_steps": treatment_steps,
                "treatment_schedule": self._generate_treatment_schedule(treatment_steps) if self._get_config().include_treatment_schedule else None,
                "cost_analysis": self._generate_cost_analysis(treatment_steps) if self._get_config().include_cost_analysis else None,
                "monitoring_plan": self._generate_monitoring_plan(treatment_steps) if self._get_config().include_monitoring_plan else None,
                "prevention_measures": self._generate_prevention_measures(treatment_steps) if self._get_config().include_prevention_measures else None,
                "analysis_metadata": {
                    "search_method": "vector" if self.use_vector_search else "json",
                    "config_used": asdict(self._get_config()),
                    "search_results_count": len(search_results)
                }
            }
            
            # Add validation warnings if any
            if validation_errors and validation_config.return_validation_errors:
                warnings = [{"field": error.field, "message": error.message, "severity": error.severity} 
                           for error in validation_errors if error.severity in ["warning", "info"]]
                if warnings:
                    treatment_plan["validation_warnings"] = warnings
            
            return json.dumps(treatment_plan, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"Generate treatment plan error: {e}")
            return json.dumps({
                "error": f"Erreur lors de la génération du plan de traitement: {str(e)}",
                "error_type": type(e).__name__
            })
    
    async def _arun(
        self,
        disease_analysis_json: Optional[str] = None,
        pest_analysis_json: Optional[str] = None,
        nutrient_analysis_json: Optional[str] = None,
        crop_type: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Asynchronous version of treatment plan generation.
        
        Args:
            disease_analysis_json: JSON string from DiagnoseDiseaseTool (optional)
            pest_analysis_json: JSON string from IdentifyPestTool (optional)
            nutrient_analysis_json: JSON string from AnalyzeNutrientDeficiencyTool (optional)
            crop_type: Type of crop for crop-specific recommendations
        """
        try:
            # Validate inputs
            validation_errors = self._validate_inputs(
                disease_analysis_json, pest_analysis_json, nutrient_analysis_json, crop_type
            )
            validation_config = self._get_validation_config()
            
            if validation_errors and validation_config.strict_validation:
                error_messages = [f"{error.field}: {error.message}" for error in validation_errors if error.severity == "error"]
                if error_messages:
                    return json.dumps({
                        "error": "Validation errors",
                        "validation_errors": error_messages
                    })
            
            # Parse input data
            disease_analysis = json.loads(disease_analysis_json) if disease_analysis_json else None
            pest_analysis = json.loads(pest_analysis_json) if pest_analysis_json else None
            nutrient_analysis = json.loads(nutrient_analysis_json) if nutrient_analysis_json else None
            
            # Search treatment knowledge asynchronously
            search_results = await self._search_treatment_knowledge(
                disease_analysis, pest_analysis, nutrient_analysis, crop_type
            )
            
            if not search_results:
                return json.dumps({
                    "error": "No treatment recommendations found",
                    "suggestions": ["Check analysis data", "Verify crop type", "Ensure valid diagnoses"]
                })
            
            # Generate treatment steps
            treatment_steps = self._generate_treatment_steps(
                search_results, disease_analysis, pest_analysis, nutrient_analysis
            )
            
            # Generate comprehensive treatment plan
            treatment_plan = {
                "plan_metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "plan_type": "crop_health_treatment",
                    "version": "2.0",
                    "crop_type": crop_type,
                    "search_method": "vector" if self.use_vector_search else "json",
                    "execution_mode": "async"
                },
                "executive_summary": self._generate_executive_summary(
                    treatment_steps, disease_analysis, pest_analysis, nutrient_analysis
                ),
                "treatment_steps": treatment_steps,
                "treatment_schedule": self._generate_treatment_schedule(treatment_steps) if self._get_config().include_treatment_schedule else None,
                "cost_analysis": self._generate_cost_analysis(treatment_steps) if self._get_config().include_cost_analysis else None,
                "monitoring_plan": self._generate_monitoring_plan(treatment_steps) if self._get_config().include_monitoring_plan else None,
                "prevention_measures": self._generate_prevention_measures(treatment_steps) if self._get_config().include_prevention_measures else None,
                "analysis_metadata": {
                    "search_method": "vector" if self.use_vector_search else "json",
                    "config_used": asdict(self._get_config()),
                    "search_results_count": len(search_results),
                    "execution_mode": "async"
                }
            }
            
            # Add validation warnings if any
            if validation_errors and validation_config.return_validation_errors:
                warnings = [{"field": error.field, "message": error.message, "severity": error.severity} 
                           for error in validation_errors if error.severity in ["warning", "info"]]
                if warnings:
                    treatment_plan["validation_warnings"] = warnings
            
            return json.dumps(treatment_plan, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"Async generate treatment plan error: {e}")
            return json.dumps({
                "error": f"Erreur lors de la génération asynchrone du plan de traitement: {str(e)}",
                "error_type": type(e).__name__
            })
    
    def clear_cache(self):
        """Clear internal caches (useful for testing or config updates)."""
        self._config_cache = None
        self._validation_cache = None
        self._knowledge_base = None
        logger.info("Cleared tool caches")
    
    def enable_vector_search(self, enable: bool = True):
        """Enable or disable vector search."""
        self.use_vector_search = enable
        self._knowledge_base = None  # Reset knowledge base
        logger.info(f"Vector search {'enabled' if enable else 'disabled'}")
