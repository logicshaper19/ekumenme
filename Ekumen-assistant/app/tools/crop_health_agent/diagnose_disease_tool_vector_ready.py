"""
Diagnose Disease Tool - Vector Database Ready Tool

Job: Diagnose crop diseases from symptoms and environmental conditions.
Input: crop_type, symptoms, environmental_conditions
Output: JSON string with disease diagnosis

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
from dataclasses import dataclass, asdict
from pathlib import Path
import os

# Import configuration system
from ...config.disease_analysis_config import (
    get_disease_analysis_config, 
    get_disease_validation_config,
    DiseaseAnalysisConfig,
    DiseaseValidationConfig
)

# Import vector database interface
from ...data.disease_vector_db_interface import (
    get_disease_knowledge_base,
    set_disease_knowledge_base,
    DiseaseKnowledgeBaseInterface,
    DiseaseKnowledge,
    DiseaseSearchResult
)

logger = logging.getLogger(__name__)

@dataclass
class DiseaseDiagnosis:
    """Structured disease diagnosis."""
    disease_name: str
    scientific_name: str
    confidence: float
    severity: str
    symptoms_matched: List[str]
    environmental_conditions_matched: List[str]
    treatment_recommendations: List[str]
    prevention_measures: List[str]
    critical_stages: Optional[List[str]] = None
    economic_threshold: Optional[str] = None
    monitoring_methods: Optional[List[str]] = None
    spread_conditions: Optional[Dict[str, Any]] = None
    search_metadata: Optional[Dict[str, Any]] = None

@dataclass
class ValidationError:
    """Validation error information."""
    field: str
    message: str
    severity: str  # "error", "warning", "info"

class DiagnoseDiseaseTool(BaseTool):
    """
    Vector Database Ready Tool: Diagnose crop diseases from symptoms and environmental conditions.
    
    Job: Take crop symptoms and environmental conditions to diagnose diseases.
    Input: crop_type, symptoms, environmental_conditions
    Output: JSON string with disease diagnosis
    
    Enhanced Features:
    - External knowledge base (JSON file)
    - Configurable analysis parameters
    - Asynchronous support
    - Comprehensive input validation
    - Vector database ready architecture
    - Semantic search capabilities
    """
    
    name: str = "diagnose_disease_tool"
    description: str = "Diagnostique les maladies des cultures à partir des symptômes avec recherche sémantique"
    
    def __init__(
        self, 
        knowledge_base_path: Optional[str] = None,
        use_vector_search: bool = False,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.knowledge_base_path = knowledge_base_path or self._get_default_knowledge_path()
        self.use_vector_search = use_vector_search
        self._config_cache: Optional[DiseaseAnalysisConfig] = None
        self._validation_cache: Optional[DiseaseValidationConfig] = None
        self._knowledge_base: Optional[DiseaseKnowledgeBaseInterface] = None
    
    def _get_default_knowledge_path(self) -> str:
        """Get default knowledge base file path."""
        current_dir = Path(__file__).parent
        return str(current_dir.parent.parent / "data" / "disease_diagnosis_knowledge.json")
    
    def _get_knowledge_base(self) -> DiseaseKnowledgeBaseInterface:
        """Get knowledge base instance."""
        if self._knowledge_base is None:
            if self.use_vector_search:
                # Use vector database (when implemented)
                self._knowledge_base = get_disease_knowledge_base()
            else:
                # Use JSON knowledge base
                from ...data.disease_vector_db_interface import JSONDiseaseKnowledgeBase
                self._knowledge_base = JSONDiseaseKnowledgeBase(self.knowledge_base_path)
        return self._knowledge_base
    
    def _get_config(self) -> DiseaseAnalysisConfig:
        """Get current analysis configuration."""
        if self._config_cache is None:
            self._config_cache = get_disease_analysis_config()
        return self._config_cache
    
    def _get_validation_config(self) -> DiseaseValidationConfig:
        """Get current validation configuration."""
        if self._validation_cache is None:
            self._validation_cache = get_disease_validation_config()
        return self._validation_cache
    
    def _validate_inputs(
        self, 
        crop_type: str, 
        symptoms: List[str], 
        environmental_conditions: Optional[Dict[str, Any]]
    ) -> List[ValidationError]:
        """Validate input parameters."""
        errors = []
        validation_config = self._get_validation_config()
        
        # Validate crop type
        if validation_config.require_crop_type and not crop_type:
            errors.append(ValidationError("crop_type", "Crop type is required", "error"))
        elif crop_type and len(crop_type.strip()) < validation_config.min_symptom_length:
            errors.append(ValidationError("crop_type", "Crop type too short", "error"))
        
        # Validate symptoms
        if validation_config.require_symptoms and not symptoms:
            errors.append(ValidationError("symptoms", "Symptoms are required", "error"))
        elif symptoms:
            if len(symptoms) < validation_config.min_symptoms:
                errors.append(ValidationError("symptoms", f"Minimum {validation_config.min_symptoms} symptoms required", "error"))
            elif len(symptoms) > validation_config.max_symptoms:
                errors.append(ValidationError("symptoms", f"Maximum {validation_config.max_symptoms} symptoms allowed", "warning"))
            
            # Validate individual symptoms
            for i, symptom in enumerate(symptoms):
                if not isinstance(symptom, str):
                    errors.append(ValidationError(f"symptoms[{i}]", "Symptom must be a string", "error"))
                elif len(symptom) < validation_config.min_symptom_length:
                    errors.append(ValidationError(f"symptoms[{i}]", "Symptom too short", "error"))
                elif len(symptom) > validation_config.max_symptom_length:
                    errors.append(ValidationError(f"symptoms[{i}]", "Symptom too long", "warning"))
        
        # Validate environmental conditions
        if environmental_conditions:
            if len(environmental_conditions) > validation_config.max_environmental_conditions:
                errors.append(ValidationError("environmental_conditions", f"Maximum {validation_config.max_environmental_conditions} environmental conditions allowed", "warning"))
            
            # Validate individual environmental conditions
            for condition, value in environmental_conditions.items():
                if not isinstance(condition, str):
                    errors.append(ValidationError("environmental_conditions", "Environmental condition key must be a string", "error"))
                elif len(condition) < validation_config.min_symptom_length:
                    errors.append(ValidationError("environmental_conditions", "Environmental condition key too short", "error"))
                elif validation_config.validate_environmental_values:
                    if not isinstance(value, (str, int, float)):
                        errors.append(ValidationError("environmental_conditions", f"Environmental condition value for '{condition}' must be a string, int, or float", "error"))
        
        return errors
    
    async def _search_disease_knowledge(
        self,
        symptoms: List[str],
        environmental_conditions: Dict[str, Any],
        crop_type: str
    ) -> List[DiseaseSearchResult]:
        """Search disease knowledge using vector database or JSON fallback."""
        knowledge_base = self._get_knowledge_base()
        
        if self.use_vector_search:
            # Use vector-based semantic search
            symptom_results = await knowledge_base.search_by_symptoms(
                symptoms, crop_type, limit=10
            )
            environmental_results = await knowledge_base.search_by_environmental_conditions(
                environmental_conditions, crop_type, limit=10
            )
            
            # Combine and deduplicate results
            all_results = {}
            for result in symptom_results + environmental_results:
                key = f"{result.disease_knowledge.crop_type}_{result.disease_knowledge.disease_name}"
                if key not in all_results or result.similarity_score > all_results[key].similarity_score:
                    all_results[key] = result
            
            return list(all_results.values())
        else:
            # Use traditional JSON-based search
            return await self._search_json_knowledge(symptoms, environmental_conditions, crop_type)
    
    async def _search_json_knowledge(
        self,
        symptoms: List[str],
        environmental_conditions: Dict[str, Any],
        crop_type: str
    ) -> List[DiseaseSearchResult]:
        """Fallback JSON-based search."""
        knowledge_base = self._get_knowledge_base()
        return await knowledge_base.search_by_symptoms(symptoms, crop_type, limit=10)
    
    def _analyze_disease_diagnoses(
        self, 
        search_results: List[DiseaseSearchResult],
        symptoms: List[str],
        environmental_conditions: Dict[str, Any]
    ) -> List[DiseaseDiagnosis]:
        """Analyze disease diagnoses based on search results."""
        diagnoses = []
        config = self._get_config()
        
        for result in search_results:
            disease_knowledge = result.disease_knowledge
            
            # Calculate symptom match
            symptom_matches = [symptom for symptom in symptoms if symptom in disease_knowledge.symptoms]
            symptom_match_ratio = len(symptom_matches) / len(disease_knowledge.symptoms) if disease_knowledge.symptoms else 0
            
            # Calculate environmental condition match
            environmental_matches = []
            environmental_match_ratio = 0
            
            if environmental_conditions and disease_knowledge.environmental_conditions:
                matches = 0
                total_conditions = 0
                
                for condition, value in environmental_conditions.items():
                    if condition in disease_knowledge.environmental_conditions:
                        total_conditions += 1
                        if self._condition_matches(disease_knowledge.environmental_conditions[condition], value):
                            matches += 1
                            environmental_matches.append(condition)
                
                environmental_match_ratio = matches / total_conditions if total_conditions > 0 else 0
            
            # Calculate overall confidence with configurable weights
            confidence = (
                symptom_match_ratio * config.symptom_weight + 
                environmental_match_ratio * config.environmental_weight
            )
            
            # Add bonuses for matches
            if symptom_matches:
                confidence += config.symptom_match_bonus
            if environmental_matches:
                confidence += config.environmental_match_bonus
            
            # Use vector similarity if available
            if result.similarity_score > 0:
                confidence = max(confidence, result.similarity_score * 0.8)  # Blend with vector similarity
            
            # Cap confidence at 1.0
            confidence = min(confidence, 1.0)
            
            if confidence > config.minimum_confidence:
                diagnosis = DiseaseDiagnosis(
                    disease_name=disease_knowledge.disease_name,
                    scientific_name=disease_knowledge.scientific_name,
                    confidence=round(confidence, 3),
                    severity=disease_knowledge.severity,
                    symptoms_matched=symptom_matches,
                    environmental_conditions_matched=environmental_matches,
                    treatment_recommendations=disease_knowledge.treatment,
                    prevention_measures=disease_knowledge.prevention if config.include_prevention else [],
                    critical_stages=disease_knowledge.critical_stages,
                    economic_threshold=disease_knowledge.economic_threshold if config.include_economic_threshold else None,
                    monitoring_methods=disease_knowledge.monitoring_methods if config.include_monitoring else None,
                    spread_conditions=disease_knowledge.spread_conditions if config.include_spread_conditions else None,
                    search_metadata={
                        "search_method": "vector" if self.use_vector_search else "json",
                        "similarity_score": result.similarity_score,
                        "match_type": result.match_type
                    }
                )
                diagnoses.append(diagnosis)
        
        # Sort by confidence and limit results
        diagnoses.sort(key=lambda x: x.confidence, reverse=True)
        return diagnoses[:config.max_diagnoses]
    
    def _condition_matches(self, expected: str, actual: Any) -> bool:
        """Check if environmental condition matches expected value."""
        config = self._get_config()
        
        # Use configurable thresholds
        if expected == "high" and actual > config.humidity_thresholds.get("high", 70):
            return True
        elif expected == "moderate" and config.humidity_thresholds.get("low", 40) <= actual <= config.humidity_thresholds.get("moderate", 70):
            return True
        elif expected == "low" and actual < config.humidity_thresholds.get("low", 40):
            return True
        elif expected == "very_high" and actual > config.humidity_thresholds.get("very_high", 80):
            return True
        elif expected == "cool" and actual < config.temperature_thresholds.get("cool", 20):
            return True
        elif expected == "warm" and actual > config.temperature_thresholds.get("warm", 30):
            return True
        return False
    
    def _calculate_diagnosis_confidence(self, diagnoses: List[DiseaseDiagnosis]) -> str:
        """Calculate overall diagnosis confidence."""
        config = self._get_config()
        
        if not diagnoses:
            return "low"
        
        max_confidence = max(diagnosis.confidence for diagnosis in diagnoses)
        
        if max_confidence > config.high_confidence:
            return "high"
        elif max_confidence > config.moderate_confidence:
            return "moderate"
        else:
            return "low"
    
    def _generate_treatment_recommendations(self, diagnoses: List[DiseaseDiagnosis]) -> List[str]:
        """Generate treatment recommendations based on disease diagnoses."""
        recommendations = []
        config = self._get_config()
        
        if not diagnoses:
            recommendations.append("Aucune maladie identifiée - Surveillance continue recommandée")
            return recommendations
        
        # Get top diagnosis
        top_diagnosis = diagnoses[0]
        
        if top_diagnosis.confidence > config.moderate_confidence:
            recommendations.append(f"Diagnostic principal: {top_diagnosis.disease_name} ({top_diagnosis.scientific_name}) - Confiance: {top_diagnosis.confidence:.1%}")
            
            if top_diagnosis.treatment_recommendations:
                recommendations.append("Traitements recommandés:")
                recommendations.extend([f"  • {treatment}" for treatment in top_diagnosis.treatment_recommendations])
            
            if config.include_prevention and top_diagnosis.prevention_measures:
                recommendations.append("Mesures préventives:")
                recommendations.extend([f"  • {prevention}" for prevention in top_diagnosis.prevention_measures])
            
            if config.include_economic_threshold and top_diagnosis.economic_threshold:
                recommendations.append(f"Seuil économique: {top_diagnosis.economic_threshold}")
            
            if config.include_monitoring and top_diagnosis.monitoring_methods:
                recommendations.append("Méthodes de surveillance:")
                recommendations.extend([f"  • {method}" for method in top_diagnosis.monitoring_methods])
            
            if top_diagnosis.critical_stages:
                recommendations.append(f"Stades critiques: {', '.join(top_diagnosis.critical_stages)}")
            
            if config.include_spread_conditions and top_diagnosis.spread_conditions:
                recommendations.append("Conditions de propagation:")
                for condition, value in top_diagnosis.spread_conditions.items():
                    recommendations.append(f"  • {condition}: {value}")
            
            # Add search metadata if available
            if top_diagnosis.search_metadata:
                search_method = top_diagnosis.search_metadata.get("search_method", "unknown")
                recommendations.append(f"Méthode de recherche: {search_method}")
        else:
            recommendations.append("Diagnostic incertain - Consultation d'un expert recommandée")
            recommendations.append("Surveillance accrue des symptômes")
        
        return recommendations
    
    def _run(
        self,
        crop_type: str,
        symptoms: List[str],
        environmental_conditions: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """
        Diagnose crop diseases from symptoms and environmental conditions.
        
        Args:
            crop_type: Type of crop (e.g., "blé", "maïs", "colza")
            symptoms: List of observed symptoms
            environmental_conditions: Environmental conditions (humidity, temperature, etc.)
        """
        try:
            # Validate inputs
            validation_errors = self._validate_inputs(crop_type, symptoms, environmental_conditions)
            validation_config = self._get_validation_config()
            
            if validation_errors and validation_config.strict_validation:
                error_messages = [f"{error.field}: {error.message}" for error in validation_errors if error.severity == "error"]
                if error_messages:
                    return json.dumps({
                        "error": "Validation errors",
                        "validation_errors": error_messages
                    })
            
            # Check if crop is supported
            if crop_type not in self._get_config().supported_crops:
                return json.dumps({
                    "error": f"Crop type '{crop_type}' not supported",
                    "supported_crops": self._get_config().supported_crops
                })
            
            # Search disease knowledge
            search_results = asyncio.run(self._search_disease_knowledge(
                symptoms, 
                environmental_conditions or {}, 
                crop_type
            ))
            
            if not search_results:
                return json.dumps({
                    "error": f"No disease knowledge found for crop '{crop_type}'",
                    "suggestions": ["Check crop type spelling", "Verify symptoms are valid"]
                })
            
            # Analyze disease diagnoses
            diagnoses = self._analyze_disease_diagnoses(
                search_results,
                symptoms, 
                environmental_conditions or {}
            )
            
            # Calculate diagnosis confidence
            diagnosis_confidence = self._calculate_diagnosis_confidence(diagnoses)
            
            # Generate treatment recommendations
            treatment_recommendations = self._generate_treatment_recommendations(diagnoses)
            
            result = {
                "crop_type": crop_type,
                "symptoms_observed": symptoms,
                "environmental_conditions": environmental_conditions or {},
                "diagnoses": [asdict(diagnosis) for diagnosis in diagnoses],
                "diagnosis_confidence": diagnosis_confidence,
                "treatment_recommendations": treatment_recommendations,
                "total_diagnoses": len(diagnoses),
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
                    result["validation_warnings"] = warnings
            
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"Diagnose disease error: {e}")
            return json.dumps({
                "error": f"Erreur lors du diagnostic: {str(e)}",
                "error_type": type(e).__name__
            })
    
    async def _arun(
        self,
        crop_type: str,
        symptoms: List[str],
        environmental_conditions: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """
        Asynchronous version of disease diagnosis.
        
        Args:
            crop_type: Type of crop (e.g., "blé", "maïs", "colza")
            symptoms: List of observed symptoms
            environmental_conditions: Environmental conditions (humidity, temperature, etc.)
        """
        try:
            # Validate inputs
            validation_errors = self._validate_inputs(crop_type, symptoms, environmental_conditions)
            validation_config = self._get_validation_config()
            
            if validation_errors and validation_config.strict_validation:
                error_messages = [f"{error.field}: {error.message}" for error in validation_errors if error.severity == "error"]
                if error_messages:
                    return json.dumps({
                        "error": "Validation errors",
                        "validation_errors": error_messages
                    })
            
            # Check if crop is supported
            if crop_type not in self._get_config().supported_crops:
                return json.dumps({
                    "error": f"Crop type '{crop_type}' not supported",
                    "supported_crops": self._get_config().supported_crops
                })
            
            # Search disease knowledge asynchronously
            search_results = await self._search_disease_knowledge(
                symptoms, 
                environmental_conditions or {}, 
                crop_type
            )
            
            if not search_results:
                return json.dumps({
                    "error": f"No disease knowledge found for crop '{crop_type}'",
                    "suggestions": ["Check crop type spelling", "Verify symptoms are valid"]
                })
            
            # Analyze disease diagnoses
            diagnoses = self._analyze_disease_diagnoses(
                search_results,
                symptoms, 
                environmental_conditions or {}
            )
            
            # Calculate diagnosis confidence
            diagnosis_confidence = self._calculate_diagnosis_confidence(diagnoses)
            
            # Generate treatment recommendations
            treatment_recommendations = self._generate_treatment_recommendations(diagnoses)
            
            result = {
                "crop_type": crop_type,
                "symptoms_observed": symptoms,
                "environmental_conditions": environmental_conditions or {},
                "diagnoses": [asdict(diagnosis) for diagnosis in diagnoses],
                "diagnosis_confidence": diagnosis_confidence,
                "treatment_recommendations": treatment_recommendations,
                "total_diagnoses": len(diagnoses),
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
                    result["validation_warnings"] = warnings
            
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"Async diagnose disease error: {e}")
            return json.dumps({
                "error": f"Erreur lors du diagnostic asynchrone: {str(e)}",
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
