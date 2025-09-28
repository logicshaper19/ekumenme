"""
Analyze Nutrient Deficiency Tool - Enhanced Production-Ready Tool

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

@dataclass
class ValidationError:
    """Validation error information."""
    field: str
    message: str
    severity: str  # "error", "warning", "info"

class AnalyzeNutrientDeficiencyTool(BaseTool):
    """
    Enhanced Tool: Analyze nutrient deficiencies from plant symptoms and soil conditions.
    
    Job: Take plant symptoms and soil conditions to analyze nutrient deficiencies.
    Input: crop_type, plant_symptoms, soil_conditions
    Output: JSON string with nutrient deficiency analysis
    
    Enhanced Features:
    - External knowledge base (JSON file)
    - Configurable analysis parameters
    - Asynchronous support
    - Comprehensive input validation
    - Vector database ready architecture
    """
    
    name: str = "analyze_nutrient_deficiency_tool"
    description: str = "Analyse les carences nutritionnelles à partir des symptômes des plantes et conditions du sol"
    
    def __init__(self, knowledge_base_path: Optional[str] = None, **kwargs):
        super().__init__(**kwargs)
        self.knowledge_base_path = knowledge_base_path or self._get_default_knowledge_path()
        self._knowledge_cache: Optional[Dict[str, Any]] = None
        self._config_cache: Optional[AnalysisConfig] = None
        self._validation_cache: Optional[ValidationConfig] = None
    
    def _get_default_knowledge_path(self) -> str:
        """Get default knowledge base file path."""
        current_dir = Path(__file__).parent
        return str(current_dir.parent.parent / "data" / "nutrient_deficiency_knowledge.json")
    
    def _load_knowledge_base(self) -> Dict[str, Any]:
        """Load knowledge base from external file."""
        if self._knowledge_cache is not None:
            return self._knowledge_cache
        
        try:
            with open(self.knowledge_base_path, 'r', encoding='utf-8') as f:
                self._knowledge_cache = json.load(f)
            logger.info(f"Loaded knowledge base from {self.knowledge_base_path}")
        except Exception as e:
            logger.error(f"Error loading knowledge base: {e}")
            self._knowledge_cache = {}
        
        return self._knowledge_cache
    
    async def _load_knowledge_base_async(self) -> Dict[str, Any]:
        """Load knowledge base asynchronously."""
        if self._knowledge_cache is not None:
            return self._knowledge_cache
        
        try:
            async with aiofiles.open(self.knowledge_base_path, 'r', encoding='utf-8') as f:
                content = await f.read()
                self._knowledge_cache = json.loads(content)
            logger.info(f"Loaded knowledge base asynchronously from {self.knowledge_base_path}")
        except Exception as e:
            logger.error(f"Error loading knowledge base asynchronously: {e}")
            self._knowledge_cache = {}
        
        return self._knowledge_cache
    
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
    
    def _get_deficiency_knowledge_base(self, crop_type: str) -> Dict[str, Any]:
        """Get nutrient deficiency knowledge base for specific crop."""
        knowledge_base = self._load_knowledge_base()
        crops = knowledge_base.get("crops", {})
        
        if crop_type not in crops:
            logger.warning(f"Crop type '{crop_type}' not found in knowledge base")
            return {}
        
        return crops[crop_type].get("nutrients", {})
    
    def _analyze_nutrient_deficiencies(
        self, 
        plant_symptoms: List[str], 
        soil_conditions: Dict[str, Any], 
        deficiency_knowledge: Dict[str, Any]
    ) -> List[NutrientDeficiency]:
        """Analyze nutrient deficiencies based on symptoms and soil conditions."""
        deficiencies = []
        config = self._get_config()
        
        for nutrient_key, nutrient_info in deficiency_knowledge.items():
            # Calculate symptom match
            symptoms = nutrient_info.get("symptoms", [])
            symptom_matches = [symptom for symptom in plant_symptoms if symptom in symptoms]
            symptom_match_ratio = len(symptom_matches) / len(symptoms) if symptoms else 0
            
            # Calculate soil indicator match
            soil_indicators = nutrient_info.get("soil_indicators", [])
            soil_matches = [indicator for indicator in soil_conditions.keys() if indicator in soil_indicators]
            soil_match_ratio = len(soil_matches) / len(soil_indicators) if soil_indicators else 0
            
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
            
            # Cap confidence at 1.0
            confidence = min(confidence, 1.0)
            
            if confidence > config.minimum_confidence:
                deficiency = NutrientDeficiency(
                    nutrient=nutrient_key,
                    nutrient_name=nutrient_info.get("name", nutrient_key),
                    symbol=nutrient_info.get("symbol", ""),
                    deficiency_level=nutrient_info.get("deficiency_level", "moderate"),
                    confidence=round(confidence, 3),
                    symptoms_matched=symptom_matches,
                    soil_indicators=soil_matches,
                    treatment_recommendations=nutrient_info.get("treatment", []),
                    prevention_measures=nutrient_info.get("prevention", []) if config.include_prevention else [],
                    dosage_guidelines=nutrient_info.get("dosage_guidelines") if config.include_dosage else None,
                    critical_stages=nutrient_info.get("critical_stages")
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
            
            # Get nutrient deficiency knowledge base
            deficiency_knowledge = self._get_deficiency_knowledge_base(crop_type)
            
            if not deficiency_knowledge:
                return json.dumps({
                    "error": f"Crop type '{crop_type}' not supported",
                    "supported_crops": self._get_config().supported_crops
                })
            
            # Analyze nutrient deficiencies
            deficiencies = self._analyze_nutrient_deficiencies(
                plant_symptoms, 
                soil_conditions or {}, 
                deficiency_knowledge
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
                    "knowledge_base_version": self._load_knowledge_base().get("metadata", {}).get("version", "unknown"),
                    "config_used": asdict(self._get_config())
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
            
            # Load knowledge base asynchronously
            knowledge_base = await self._load_knowledge_base_async()
            crops = knowledge_base.get("crops", {})
            
            if crop_type not in crops:
                return json.dumps({
                    "error": f"Crop type '{crop_type}' not supported",
                    "supported_crops": self._get_config().supported_crops
                })
            
            deficiency_knowledge = crops[crop_type].get("nutrients", {})
            
            # Analyze nutrient deficiencies
            deficiencies = self._analyze_nutrient_deficiencies(
                plant_symptoms, 
                soil_conditions or {}, 
                deficiency_knowledge
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
                    "knowledge_base_version": knowledge_base.get("metadata", {}).get("version", "unknown"),
                    "config_used": asdict(self._get_config()),
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
        self._knowledge_cache = None
        self._config_cache = None
        self._validation_cache = None
        logger.info("Cleared tool caches")
