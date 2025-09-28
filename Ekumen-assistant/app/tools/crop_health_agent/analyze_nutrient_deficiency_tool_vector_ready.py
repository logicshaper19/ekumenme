"""
Analyze Nutrient Deficiency Tool - Vector Database Ready Tool

Job: Analyze nutrient deficiencies from plant symptoms and soil conditions.
Input: crop_type, plant_symptoms, soil_conditions
Output: JSON string with nutrient deficiency analysis

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
from ...config.nutrient_analysis_config import (
    get_analysis_config, 
    get_validation_config,
    AnalysisConfig,
    ValidationConfig
)

# Import vector database interface
from ...data.vector_db_interface import (
    get_knowledge_base,
    set_knowledge_base,
    KnowledgeBaseInterface,
    NutrientKnowledge,
    SearchResult
)

logger = logging.getLogger(__name__)

@dataclass
class NutrientDeficiency:
    """Structured nutrient deficiency analysis."""
    nutrient: str
    nutrient_name: str
    symbol: str
    deficiency_level: str
    confidence: float
    symptoms_matched: List[str]
    soil_indicators: List[str]
    treatment_recommendations: List[str]
    prevention_measures: List[str]
    dosage_guidelines: Optional[Dict[str, str]] = None
    critical_stages: Optional[List[str]] = None
    search_metadata: Optional[Dict[str, Any]] = None

@dataclass
class ValidationError:
    """Validation error information."""
    field: str
    message: str
    severity: str  # "error", "warning", "info"

class AnalyzeNutrientDeficiencyTool(BaseTool):
    """
    Vector Database Ready Tool: Analyze nutrient deficiencies from plant symptoms and soil conditions.
    
    Job: Take plant symptoms and soil conditions to analyze nutrient deficiencies.
    Input: crop_type, plant_symptoms, soil_conditions
    Output: JSON string with nutrient deficiency analysis
    
    Enhanced Features:
    - External knowledge base (JSON file)
    - Configurable analysis parameters
    - Asynchronous support
    - Comprehensive input validation
    - Vector database ready architecture
    - Semantic search capabilities
    """
    
    name: str = "analyze_nutrient_deficiency_tool"
    description: str = "Analyse les carences nutritionnelles à partir des symptômes des plantes et conditions du sol avec recherche sémantique"
    
    def __init__(
        self, 
        knowledge_base_path: Optional[str] = None,
        use_vector_search: bool = False,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.knowledge_base_path = knowledge_base_path or self._get_default_knowledge_path()
        self.use_vector_search = use_vector_search
        self._config_cache: Optional[AnalysisConfig] = None
        self._validation_cache: Optional[ValidationConfig] = None
        self._knowledge_base: Optional[KnowledgeBaseInterface] = None
    
    def _get_default_knowledge_path(self) -> str:
        """Get default knowledge base file path."""
        current_dir = Path(__file__).parent
        return str(current_dir.parent.parent / "data" / "nutrient_deficiency_knowledge.json")
    
    def _get_knowledge_base(self) -> KnowledgeBaseInterface:
        """Get knowledge base instance."""
        if self._knowledge_base is None:
            if self.use_vector_search:
                # Use vector database (when implemented)
                self._knowledge_base = get_knowledge_base()
            else:
                # Use JSON knowledge base
                from ...data.vector_db_interface import JSONKnowledgeBase
                self._knowledge_base = JSONKnowledgeBase(self.knowledge_base_path)
        return self._knowledge_base
    
    def _get_config(self) -> AnalysisConfig:
        """Get current analysis configuration."""
        if self._config_cache is None:
            self._config_cache = get_analysis_config()
        return self._config_cache
    
    def _get_validation_config(self) -> ValidationConfig:
        """Get current validation configuration."""
        if self._validation_cache is None:
            self._validation_cache = get_validation_config()
        return self._validation_cache
    
    def _validate_inputs(
        self, 
        crop_type: str, 
        plant_symptoms: List[str], 
        soil_conditions: Optional[Dict[str, Any]]
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
        if validation_config.require_symptoms and not plant_symptoms:
            errors.append(ValidationError("plant_symptoms", "Plant symptoms are required", "error"))
        elif plant_symptoms:
            if len(plant_symptoms) < validation_config.min_symptoms:
                errors.append(ValidationError("plant_symptoms", f"Minimum {validation_config.min_symptoms} symptoms required", "error"))
            elif len(plant_symptoms) > validation_config.max_symptoms:
                errors.append(ValidationError("plant_symptoms", f"Maximum {validation_config.max_symptoms} symptoms allowed", "warning"))
            
            # Validate individual symptoms
            for i, symptom in enumerate(plant_symptoms):
                if not isinstance(symptom, str):
                    errors.append(ValidationError(f"plant_symptoms[{i}]", "Symptom must be a string", "error"))
                elif len(symptom) < validation_config.min_symptom_length:
                    errors.append(ValidationError(f"plant_symptoms[{i}]", "Symptom too short", "error"))
                elif len(symptom) > validation_config.max_symptom_length:
                    errors.append(ValidationError(f"plant_symptoms[{i}]", "Symptom too long", "warning"))
        
        # Validate soil conditions
        if soil_conditions and len(soil_conditions) > validation_config.max_soil_parameters:
            errors.append(ValidationError("soil_conditions", f"Maximum {validation_config.max_soil_parameters} soil parameters allowed", "warning"))
        
        return errors
    
    async def _search_nutrient_knowledge(
        self,
        plant_symptoms: List[str],
        soil_conditions: Dict[str, Any],
        crop_type: str
    ) -> List[SearchResult]:
        """Search nutrient knowledge using vector database or JSON fallback."""
        knowledge_base = self._get_knowledge_base()
        
        if self.use_vector_search:
            # Use vector-based semantic search
            symptom_results = await knowledge_base.search_by_symptoms(
                plant_symptoms, crop_type, limit=10
            )
            soil_results = await knowledge_base.search_by_soil_conditions(
                soil_conditions, crop_type, limit=10
            )
            
            # Combine and deduplicate results
            all_results = {}
            for result in symptom_results + soil_results:
                key = f"{result.nutrient_knowledge.crop_type}_{result.nutrient_knowledge.nutrient}"
                if key not in all_results or result.similarity_score > all_results[key].similarity_score:
                    all_results[key] = result
            
            return list(all_results.values())
        else:
            # Use traditional JSON-based search
            return await self._search_json_knowledge(plant_symptoms, soil_conditions, crop_type)
    
    async def _search_json_knowledge(
        self,
        plant_symptoms: List[str],
        soil_conditions: Dict[str, Any],
        crop_type: str
    ) -> List[SearchResult]:
        """Fallback JSON-based search."""
        knowledge_base = self._get_knowledge_base()
        return await knowledge_base.search_by_symptoms(plant_symptoms, crop_type, limit=10)
    
    def _analyze_nutrient_deficiencies(
        self, 
        search_results: List[SearchResult],
        plant_symptoms: List[str],
        soil_conditions: Dict[str, Any]
    ) -> List[NutrientDeficiency]:
        """Analyze nutrient deficiencies based on search results."""
        deficiencies = []
        config = self._get_config()
        
        for result in search_results:
            nutrient_knowledge = result.nutrient_knowledge
            
            # Calculate symptom match
            symptom_matches = [symptom for symptom in plant_symptoms if symptom in nutrient_knowledge.symptoms]
            symptom_match_ratio = len(symptom_matches) / len(nutrient_knowledge.symptoms) if nutrient_knowledge.symptoms else 0
            
            # Calculate soil indicator match
            soil_matches = [indicator for indicator in soil_conditions.keys() if indicator in nutrient_knowledge.soil_indicators]
            soil_match_ratio = len(soil_matches) / len(nutrient_knowledge.soil_indicators) if nutrient_knowledge.soil_indicators else 0
            
            # Calculate overall confidence with configurable weights
            confidence = (
                symptom_match_ratio * config.symptom_weight + 
                soil_match_ratio * config.soil_weight
            )
            
            # Add bonuses for matches
            if symptom_matches:
                confidence += config.symptom_match_bonus
            if soil_matches:
                confidence += config.soil_match_bonus
            
            # Use vector similarity if available
            if result.similarity_score > 0:
                confidence = max(confidence, result.similarity_score * 0.8)  # Blend with vector similarity
            
            # Cap confidence at 1.0
            confidence = min(confidence, 1.0)
            
            if confidence > config.minimum_confidence:
                deficiency = NutrientDeficiency(
                    nutrient=nutrient_knowledge.nutrient,
                    nutrient_name=nutrient_knowledge.nutrient_name,
                    symbol=nutrient_knowledge.symbol,
                    deficiency_level=nutrient_knowledge.deficiency_level,
                    confidence=round(confidence, 3),
                    symptoms_matched=symptom_matches,
                    soil_indicators=soil_matches,
                    treatment_recommendations=nutrient_knowledge.treatment,
                    prevention_measures=nutrient_knowledge.prevention if config.include_prevention else [],
                    dosage_guidelines=nutrient_knowledge.dosage_guidelines if config.include_dosage else None,
                    critical_stages=nutrient_knowledge.critical_stages,
                    search_metadata={
                        "search_method": "vector" if self.use_vector_search else "json",
                        "similarity_score": result.similarity_score,
                        "match_type": result.match_type
                    }
                )
                deficiencies.append(deficiency)
        
        # Sort by confidence and limit results
        deficiencies.sort(key=lambda x: x.confidence, reverse=True)
        return deficiencies[:config.max_deficiencies]
    
    def _calculate_analysis_confidence(self, deficiencies: List[NutrientDeficiency]) -> str:
        """Calculate overall analysis confidence."""
        config = self._get_config()
        
        if not deficiencies:
            return "low"
        
        max_confidence = max(deficiency.confidence for deficiency in deficiencies)
        
        if max_confidence > config.high_confidence:
            return "high"
        elif max_confidence > config.moderate_confidence:
            return "moderate"
        else:
            return "low"
    
    def _generate_treatment_recommendations(self, deficiencies: List[NutrientDeficiency]) -> List[str]:
        """Generate treatment recommendations based on nutrient deficiencies."""
        recommendations = []
        config = self._get_config()
        
        if not deficiencies:
            recommendations.append("Aucune carence nutritionnelle identifiée - Surveillance continue recommandée")
            return recommendations
        
        # Get top deficiency
        top_deficiency = deficiencies[0]
        
        if top_deficiency.confidence > config.moderate_confidence:
            recommendations.append(f"Carence principale: {top_deficiency.nutrient_name} ({top_deficiency.symbol}) - Confiance: {top_deficiency.confidence:.1%}")
            
            if top_deficiency.treatment_recommendations:
                recommendations.append("Traitements recommandés:")
                recommendations.extend([f"  • {treatment}" for treatment in top_deficiency.treatment_recommendations])
            
            if config.include_dosage and top_deficiency.dosage_guidelines:
                recommendations.append("Dosages recommandés:")
                for level, dosage in top_deficiency.dosage_guidelines.items():
                    recommendations.append(f"  • {level}: {dosage}")
            
            if config.include_prevention and top_deficiency.prevention_measures:
                recommendations.append("Mesures préventives:")
                recommendations.extend([f"  • {prevention}" for prevention in top_deficiency.prevention_measures])
            
            if top_deficiency.critical_stages:
                recommendations.append(f"Stades critiques: {', '.join(top_deficiency.critical_stages)}")
            
            # Add search metadata if available
            if top_deficiency.search_metadata:
                search_method = top_deficiency.search_metadata.get("search_method", "unknown")
                recommendations.append(f"Méthode de recherche: {search_method}")
        else:
            recommendations.append("Analyse incertaine - Analyse de sol recommandée")
            recommendations.append("Surveillance accrue des symptômes")
        
        return recommendations
    
    def _run(
        self,
        crop_type: str,
        plant_symptoms: List[str],
        soil_conditions: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """
        Analyze nutrient deficiencies from plant symptoms and soil conditions.
        
        Args:
            crop_type: Type of crop (e.g., "blé", "maïs", "colza")
            plant_symptoms: List of observed plant symptoms
            soil_conditions: Soil conditions (pH, organic_matter, etc.)
        """
        try:
            # Validate inputs
            validation_errors = self._validate_inputs(crop_type, plant_symptoms, soil_conditions)
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
            
            # Search nutrient knowledge
            search_results = asyncio.run(self._search_nutrient_knowledge(
                plant_symptoms, 
                soil_conditions or {}, 
                crop_type
            ))
            
            if not search_results:
                return json.dumps({
                    "error": f"No nutrient knowledge found for crop '{crop_type}'",
                    "suggestions": ["Check crop type spelling", "Verify symptoms are valid"]
                })
            
            # Analyze nutrient deficiencies
            deficiencies = self._analyze_nutrient_deficiencies(
                search_results,
                plant_symptoms, 
                soil_conditions or {}
            )
            
            # Calculate analysis confidence
            analysis_confidence = self._calculate_analysis_confidence(deficiencies)
            
            # Generate treatment recommendations
            treatment_recommendations = self._generate_treatment_recommendations(deficiencies)
            
            result = {
                "crop_type": crop_type,
                "plant_symptoms": plant_symptoms,
                "soil_conditions": soil_conditions or {},
                "nutrient_deficiencies": [asdict(deficiency) for deficiency in deficiencies],
                "analysis_confidence": analysis_confidence,
                "treatment_recommendations": treatment_recommendations,
                "total_deficiencies": len(deficiencies),
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
            logger.error(f"Analyze nutrient deficiency error: {e}")
            return json.dumps({
                "error": f"Erreur lors de l'analyse des carences: {str(e)}",
                "error_type": type(e).__name__
            })
    
    async def _arun(
        self,
        crop_type: str,
        plant_symptoms: List[str],
        soil_conditions: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """
        Asynchronous version of nutrient deficiency analysis.
        
        Args:
            crop_type: Type of crop (e.g., "blé", "maïs", "colza")
            plant_symptoms: List of observed plant symptoms
            soil_conditions: Soil conditions (pH, organic_matter, etc.)
        """
        try:
            # Validate inputs
            validation_errors = self._validate_inputs(crop_type, plant_symptoms, soil_conditions)
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
            
            # Search nutrient knowledge asynchronously
            search_results = await self._search_nutrient_knowledge(
                plant_symptoms, 
                soil_conditions or {}, 
                crop_type
            )
            
            if not search_results:
                return json.dumps({
                    "error": f"No nutrient knowledge found for crop '{crop_type}'",
                    "suggestions": ["Check crop type spelling", "Verify symptoms are valid"]
                })
            
            # Analyze nutrient deficiencies
            deficiencies = self._analyze_nutrient_deficiencies(
                search_results,
                plant_symptoms, 
                soil_conditions or {}
            )
            
            # Calculate analysis confidence
            analysis_confidence = self._calculate_analysis_confidence(deficiencies)
            
            # Generate treatment recommendations
            treatment_recommendations = self._generate_treatment_recommendations(deficiencies)
            
            result = {
                "crop_type": crop_type,
                "plant_symptoms": plant_symptoms,
                "soil_conditions": soil_conditions or {},
                "nutrient_deficiencies": [asdict(deficiency) for deficiency in deficiencies],
                "analysis_confidence": analysis_confidence,
                "treatment_recommendations": treatment_recommendations,
                "total_deficiencies": len(deficiencies),
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
            logger.error(f"Async analyze nutrient deficiency error: {e}")
            return json.dumps({
                "error": f"Erreur lors de l'analyse asynchrone des carences: {str(e)}",
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
