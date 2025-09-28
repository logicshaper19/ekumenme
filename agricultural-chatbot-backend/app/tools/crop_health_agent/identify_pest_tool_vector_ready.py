"""
Identify Pest Tool - Vector Database Ready Tool

Job: Identify crop pests from symptoms and damage patterns.
Input: crop_type, damage_symptoms, pest_indicators
Output: JSON string with pest identification

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
from ...config.pest_analysis_config import (
    get_pest_analysis_config, 
    get_pest_validation_config,
    PestAnalysisConfig,
    PestValidationConfig
)

# Import vector database interface
from ...data.pest_vector_db_interface import (
    get_pest_knowledge_base,
    set_pest_knowledge_base,
    PestKnowledgeBaseInterface,
    PestKnowledge,
    PestSearchResult
)

logger = logging.getLogger(__name__)

@dataclass
class PestIdentification:
    """Structured pest identification."""
    pest_name: str
    scientific_name: str
    confidence: float
    severity: str
    damage_patterns_matched: List[str]
    pest_indicators_matched: List[str]
    treatment_recommendations: List[str]
    prevention_measures: List[str]
    critical_stages: Optional[List[str]] = None
    economic_threshold: Optional[str] = None
    monitoring_methods: Optional[List[str]] = None
    search_metadata: Optional[Dict[str, Any]] = None

@dataclass
class ValidationError:
    """Validation error information."""
    field: str
    message: str
    severity: str  # "error", "warning", "info"

class IdentifyPestTool(BaseTool):
    """
    Vector Database Ready Tool: Identify crop pests from symptoms and damage patterns.
    
    Job: Take crop damage symptoms and pest indicators to identify pests.
    Input: crop_type, damage_symptoms, pest_indicators
    Output: JSON string with pest identification
    
    Enhanced Features:
    - External knowledge base (JSON file)
    - Configurable analysis parameters
    - Asynchronous support
    - Comprehensive input validation
    - Vector database ready architecture
    - Semantic search capabilities
    """
    
    name: str = "identify_pest_tool"
    description: str = "Identifie les ravageurs des cultures à partir des symptômes de dégâts avec recherche sémantique"
    
    def __init__(
        self, 
        knowledge_base_path: Optional[str] = None,
        use_vector_search: bool = False,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.knowledge_base_path = knowledge_base_path or self._get_default_knowledge_path()
        self.use_vector_search = use_vector_search
        self._config_cache: Optional[PestAnalysisConfig] = None
        self._validation_cache: Optional[PestValidationConfig] = None
        self._knowledge_base: Optional[PestKnowledgeBaseInterface] = None
    
    def _get_default_knowledge_path(self) -> str:
        """Get default knowledge base file path."""
        current_dir = Path(__file__).parent
        return str(current_dir.parent.parent / "data" / "pest_identification_knowledge.json")
    
    def _get_knowledge_base(self) -> PestKnowledgeBaseInterface:
        """Get knowledge base instance."""
        if self._knowledge_base is None:
            if self.use_vector_search:
                # Use vector database (when implemented)
                self._knowledge_base = get_pest_knowledge_base()
            else:
                # Use JSON knowledge base
                from ...data.pest_vector_db_interface import JSONPestKnowledgeBase
                self._knowledge_base = JSONPestKnowledgeBase(self.knowledge_base_path)
        return self._knowledge_base
    
    def _get_config(self) -> PestAnalysisConfig:
        """Get current analysis configuration."""
        if self._config_cache is None:
            self._config_cache = get_pest_analysis_config()
        return self._config_cache
    
    def _get_validation_config(self) -> PestValidationConfig:
        """Get current validation configuration."""
        if self._validation_cache is None:
            self._validation_cache = get_pest_validation_config()
        return self._validation_cache
    
    def _validate_inputs(
        self, 
        crop_type: str, 
        damage_symptoms: List[str], 
        pest_indicators: Optional[List[str]]
    ) -> List[ValidationError]:
        """Validate input parameters."""
        errors = []
        validation_config = self._get_validation_config()
        
        # Validate crop type
        if validation_config.require_crop_type and not crop_type:
            errors.append(ValidationError("crop_type", "Crop type is required", "error"))
        elif crop_type and len(crop_type.strip()) < validation_config.min_symptom_length:
            errors.append(ValidationError("crop_type", "Crop type too short", "error"))
        
        # Validate damage symptoms
        if validation_config.require_damage_symptoms and not damage_symptoms:
            errors.append(ValidationError("damage_symptoms", "Damage symptoms are required", "error"))
        elif damage_symptoms:
            if len(damage_symptoms) < validation_config.min_symptoms:
                errors.append(ValidationError("damage_symptoms", f"Minimum {validation_config.min_symptoms} symptoms required", "error"))
            elif len(damage_symptoms) > validation_config.max_symptoms:
                errors.append(ValidationError("damage_symptoms", f"Maximum {validation_config.max_symptoms} symptoms allowed", "warning"))
            
            # Validate individual symptoms
            for i, symptom in enumerate(damage_symptoms):
                if not isinstance(symptom, str):
                    errors.append(ValidationError(f"damage_symptoms[{i}]", "Symptom must be a string", "error"))
                elif len(symptom) < validation_config.min_symptom_length:
                    errors.append(ValidationError(f"damage_symptoms[{i}]", "Symptom too short", "error"))
                elif len(symptom) > validation_config.max_symptom_length:
                    errors.append(ValidationError(f"damage_symptoms[{i}]", "Symptom too long", "warning"))
        
        # Validate pest indicators
        if pest_indicators:
            if len(pest_indicators) > validation_config.max_pest_indicators:
                errors.append(ValidationError("pest_indicators", f"Maximum {validation_config.max_pest_indicators} pest indicators allowed", "warning"))
            
            # Validate individual indicators
            for i, indicator in enumerate(pest_indicators):
                if not isinstance(indicator, str):
                    errors.append(ValidationError(f"pest_indicators[{i}]", "Pest indicator must be a string", "error"))
                elif len(indicator) < validation_config.min_symptom_length:
                    errors.append(ValidationError(f"pest_indicators[{i}]", "Pest indicator too short", "error"))
                elif len(indicator) > validation_config.max_symptom_length:
                    errors.append(ValidationError(f"pest_indicators[{i}]", "Pest indicator too long", "warning"))
        
        return errors
    
    async def _search_pest_knowledge(
        self,
        damage_symptoms: List[str],
        pest_indicators: List[str],
        crop_type: str
    ) -> List[PestSearchResult]:
        """Search pest knowledge using vector database or JSON fallback."""
        knowledge_base = self._get_knowledge_base()
        
        if self.use_vector_search:
            # Use vector-based semantic search
            damage_results = await knowledge_base.search_by_damage_patterns(
                damage_symptoms, crop_type, limit=10
            )
            indicator_results = await knowledge_base.search_by_pest_indicators(
                pest_indicators, crop_type, limit=10
            )
            
            # Combine and deduplicate results
            all_results = {}
            for result in damage_results + indicator_results:
                key = f"{result.pest_knowledge.crop_type}_{result.pest_knowledge.pest_name}"
                if key not in all_results or result.similarity_score > all_results[key].similarity_score:
                    all_results[key] = result
            
            return list(all_results.values())
        else:
            # Use traditional JSON-based search
            return await self._search_json_knowledge(damage_symptoms, pest_indicators, crop_type)
    
    async def _search_json_knowledge(
        self,
        damage_symptoms: List[str],
        pest_indicators: List[str],
        crop_type: str
    ) -> List[PestSearchResult]:
        """Fallback JSON-based search."""
        knowledge_base = self._get_knowledge_base()
        return await knowledge_base.search_by_damage_patterns(damage_symptoms, crop_type, limit=10)
    
    def _analyze_pest_identifications(
        self, 
        search_results: List[PestSearchResult],
        damage_symptoms: List[str],
        pest_indicators: List[str]
    ) -> List[PestIdentification]:
        """Analyze pest identifications based on search results."""
        identifications = []
        config = self._get_config()
        
        for result in search_results:
            pest_knowledge = result.pest_knowledge
            
            # Calculate damage pattern match
            damage_matches = [symptom for symptom in damage_symptoms if symptom in pest_knowledge.damage_patterns]
            damage_match_ratio = len(damage_matches) / len(pest_knowledge.damage_patterns) if pest_knowledge.damage_patterns else 0
            
            # Calculate pest indicator match
            indicator_matches = [indicator for indicator in pest_indicators if indicator in pest_knowledge.pest_indicators]
            indicator_match_ratio = len(indicator_matches) / len(pest_knowledge.pest_indicators) if pest_knowledge.pest_indicators else 0
            
            # Calculate overall confidence with configurable weights
            confidence = (
                damage_match_ratio * config.damage_pattern_weight + 
                indicator_match_ratio * config.pest_indicator_weight
            )
            
            # Add bonuses for matches
            if damage_matches:
                confidence += config.damage_match_bonus
            if indicator_matches:
                confidence += config.indicator_match_bonus
            
            # Use vector similarity if available
            if result.similarity_score > 0:
                confidence = max(confidence, result.similarity_score * 0.8)  # Blend with vector similarity
            
            # Cap confidence at 1.0
            confidence = min(confidence, 1.0)
            
            if confidence > config.minimum_confidence:
                identification = PestIdentification(
                    pest_name=pest_knowledge.pest_name,
                    scientific_name=pest_knowledge.scientific_name,
                    confidence=round(confidence, 3),
                    severity=pest_knowledge.severity,
                    damage_patterns_matched=damage_matches,
                    pest_indicators_matched=indicator_matches,
                    treatment_recommendations=pest_knowledge.treatment,
                    prevention_measures=pest_knowledge.prevention if config.include_prevention else [],
                    critical_stages=pest_knowledge.critical_stages,
                    economic_threshold=pest_knowledge.economic_threshold if config.include_economic_threshold else None,
                    monitoring_methods=pest_knowledge.monitoring_methods if config.include_monitoring else None,
                    search_metadata={
                        "search_method": "vector" if self.use_vector_search else "json",
                        "similarity_score": result.similarity_score,
                        "match_type": result.match_type
                    }
                )
                identifications.append(identification)
        
        # Sort by confidence and limit results
        identifications.sort(key=lambda x: x.confidence, reverse=True)
        return identifications[:config.max_identifications]
    
    def _calculate_identification_confidence(self, identifications: List[PestIdentification]) -> str:
        """Calculate overall identification confidence."""
        config = self._get_config()
        
        if not identifications:
            return "low"
        
        max_confidence = max(identification.confidence for identification in identifications)
        
        if max_confidence > config.high_confidence:
            return "high"
        elif max_confidence > config.moderate_confidence:
            return "moderate"
        else:
            return "low"
    
    def _generate_treatment_recommendations(self, identifications: List[PestIdentification]) -> List[str]:
        """Generate treatment recommendations based on pest identifications."""
        recommendations = []
        config = self._get_config()
        
        if not identifications:
            recommendations.append("Aucun ravageur identifié - Surveillance continue recommandée")
            return recommendations
        
        # Get top identification
        top_identification = identifications[0]
        
        if top_identification.confidence > config.moderate_confidence:
            recommendations.append(f"Ravageur principal: {top_identification.pest_name} ({top_identification.scientific_name}) - Confiance: {top_identification.confidence:.1%}")
            
            if top_identification.treatment_recommendations:
                recommendations.append("Traitements recommandés:")
                recommendations.extend([f"  • {treatment}" for treatment in top_identification.treatment_recommendations])
            
            if config.include_prevention and top_identification.prevention_measures:
                recommendations.append("Mesures préventives:")
                recommendations.extend([f"  • {prevention}" for prevention in top_identification.prevention_measures])
            
            if config.include_economic_threshold and top_identification.economic_threshold:
                recommendations.append(f"Seuil économique: {top_identification.economic_threshold}")
            
            if config.include_monitoring and top_identification.monitoring_methods:
                recommendations.append("Méthodes de surveillance:")
                recommendations.extend([f"  • {method}" for method in top_identification.monitoring_methods])
            
            if top_identification.critical_stages:
                recommendations.append(f"Stades critiques: {', '.join(top_identification.critical_stages)}")
            
            # Add search metadata if available
            if top_identification.search_metadata:
                search_method = top_identification.search_metadata.get("search_method", "unknown")
                recommendations.append(f"Méthode de recherche: {search_method}")
        else:
            recommendations.append("Identification incertaine - Consultation d'un expert recommandée")
            recommendations.append("Surveillance accrue des dégâts")
        
        return recommendations
    
    def _run(
        self,
        crop_type: str,
        damage_symptoms: List[str],
        pest_indicators: Optional[List[str]] = None,
        **kwargs
    ) -> str:
        """
        Identify crop pests from damage symptoms and pest indicators.
        
        Args:
            crop_type: Type of crop (e.g., "blé", "maïs", "colza")
            damage_symptoms: List of observed damage symptoms
            pest_indicators: List of pest indicators (eggs, larvae, adults)
        """
        try:
            # Validate inputs
            validation_errors = self._validate_inputs(crop_type, damage_symptoms, pest_indicators)
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
            
            # Search pest knowledge
            search_results = asyncio.run(self._search_pest_knowledge(
                damage_symptoms, 
                pest_indicators or [], 
                crop_type
            ))
            
            if not search_results:
                return json.dumps({
                    "error": f"No pest knowledge found for crop '{crop_type}'",
                    "suggestions": ["Check crop type spelling", "Verify symptoms are valid"]
                })
            
            # Analyze pest identifications
            identifications = self._analyze_pest_identifications(
                search_results,
                damage_symptoms, 
                pest_indicators or []
            )
            
            # Calculate identification confidence
            identification_confidence = self._calculate_identification_confidence(identifications)
            
            # Generate treatment recommendations
            treatment_recommendations = self._generate_treatment_recommendations(identifications)
            
            result = {
                "crop_type": crop_type,
                "damage_symptoms": damage_symptoms,
                "pest_indicators": pest_indicators or [],
                "pest_identifications": [asdict(identification) for identification in identifications],
                "identification_confidence": identification_confidence,
                "treatment_recommendations": treatment_recommendations,
                "total_identifications": len(identifications),
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
            logger.error(f"Identify pest error: {e}")
            return json.dumps({
                "error": f"Erreur lors de l'identification des ravageurs: {str(e)}",
                "error_type": type(e).__name__
            })
    
    async def _arun(
        self,
        crop_type: str,
        damage_symptoms: List[str],
        pest_indicators: Optional[List[str]] = None,
        **kwargs
    ) -> str:
        """
        Asynchronous version of pest identification.
        
        Args:
            crop_type: Type of crop (e.g., "blé", "maïs", "colza")
            damage_symptoms: List of observed damage symptoms
            pest_indicators: List of pest indicators (eggs, larvae, adults)
        """
        try:
            # Validate inputs
            validation_errors = self._validate_inputs(crop_type, damage_symptoms, pest_indicators)
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
            
            # Search pest knowledge asynchronously
            search_results = await self._search_pest_knowledge(
                damage_symptoms, 
                pest_indicators or [], 
                crop_type
            )
            
            if not search_results:
                return json.dumps({
                    "error": f"No pest knowledge found for crop '{crop_type}'",
                    "suggestions": ["Check crop type spelling", "Verify symptoms are valid"]
                })
            
            # Analyze pest identifications
            identifications = self._analyze_pest_identifications(
                search_results,
                damage_symptoms, 
                pest_indicators or []
            )
            
            # Calculate identification confidence
            identification_confidence = self._calculate_identification_confidence(identifications)
            
            # Generate treatment recommendations
            treatment_recommendations = self._generate_treatment_recommendations(identifications)
            
            result = {
                "crop_type": crop_type,
                "damage_symptoms": damage_symptoms,
                "pest_indicators": pest_indicators or [],
                "pest_identifications": [asdict(identification) for identification in identifications],
                "identification_confidence": identification_confidence,
                "treatment_recommendations": treatment_recommendations,
                "total_identifications": len(identifications),
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
            logger.error(f"Async identify pest error: {e}")
            return json.dumps({
                "error": f"Erreur lors de l'identification asynchrone des ravageurs: {str(e)}",
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
