"""
Assess Biodiversity Tool - Vector Database Ready Tool

Job: Assess biodiversity impact and conservation potential of agricultural practices.
Input: practice_type, land_use, conservation_measures
Output: JSON string with biodiversity assessment

Enhanced Features:
- External knowledge base (JSON file)
- Configurable analysis parameters
- Asynchronous support
- Comprehensive input validation
- Vector database ready architecture

No prompting logic, no orchestration, no agent responsibilities.
"""

from typing import Dict, List, Any, Optional
from langchain.tools import BaseTool
import logging
import json
import asyncio
from datetime import datetime
from dataclasses import dataclass, asdict
from pathlib import Path

# Import configuration system
from ...config.biodiversity_assessment_config import get_biodiversity_assessment_config

logger = logging.getLogger(__name__)

@dataclass
class BiodiversityImpact:
    """Structured biodiversity impact."""
    impact_type: str
    species_affected: str
    impact_level: str
    conservation_value: float
    mitigation_measures: List[str]

@dataclass
class ValidationError:
    """Validation error information."""
    field: str
    message: str
    severity: str

class AssessBiodiversityTool(BaseTool):
    """
    Vector Database Ready Tool: Assess biodiversity impact and conservation potential of agricultural practices.
    
    Job: Take agricultural practice data and assess biodiversity impact.
    Input: practice_type, land_use, conservation_measures
    Output: JSON string with biodiversity assessment
    
    Enhanced Features:
    - External knowledge base (JSON file)
    - Configurable analysis parameters
    - Asynchronous support
    - Comprehensive input validation
    - Vector database ready architecture
    """
    
    name: str = "assess_biodiversity_tool"
    description: str = "Évalue l'impact sur la biodiversité avec analyse avancée"
    
    def __init__(
        self, 
        knowledge_base_path: Optional[str] = None,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.knowledge_base_path = knowledge_base_path or self._get_default_knowledge_path()
        self._config_cache = None
    
    def _get_default_knowledge_path(self) -> str:
        """Get default knowledge base file path."""
        current_dir = Path(__file__).parent
        return str(current_dir.parent.parent / "data" / "biodiversity_assessment_knowledge.json")
    
    def _get_config(self):
        """Get current configuration."""
        if self._config_cache is None:
            self._config_cache = get_biodiversity_assessment_config()
        return self._config_cache
    
    def _load_knowledge_base(self) -> Dict[str, Any]:
        """Load knowledge base from JSON file."""
        try:
            with open(self.knowledge_base_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading biodiversity assessment knowledge base: {e}")
            return {}
    
    def _validate_inputs(
        self, 
        practice_type: str,
        land_use: Optional[str] = None,
        conservation_measures: Optional[List[str]] = None
    ) -> List[ValidationError]:
        """Validate input parameters."""
        errors = []
        config = self._get_config()
        
        # Validate practice type
        if config.require_practice_type and not practice_type:
            errors.append(ValidationError("practice_type", "Practice type is required", "error"))
        
        # Validate land use if provided
        if config.validate_land_use and land_use:
            if len(land_use.strip()) < 2:
                errors.append(ValidationError("land_use", "Land use must be at least 2 characters", "warning"))
        
        # Validate conservation measures if provided
        if conservation_measures:
            if not isinstance(conservation_measures, list):
                errors.append(ValidationError("conservation_measures", "Conservation measures must be a list", "error"))
            elif len(conservation_measures) == 0:
                errors.append(ValidationError("conservation_measures", "Conservation measures list cannot be empty", "warning"))
        
        return errors
    
    def _assess_practice_impact(
        self, 
        practice_type: str, 
        knowledge_base: Dict[str, Any]
    ) -> Optional[BiodiversityImpact]:
        """Assess biodiversity impact of a specific practice type."""
        practice_impacts = knowledge_base.get("practice_impacts", {})
        
        # Find matching practice type
        practice_key = None
        for key in practice_impacts.keys():
            if practice_type.lower() in key.lower() or key.lower() in practice_type.lower():
                practice_key = key
                break
        
        if not practice_key:
            return None
        
        practice_info = practice_impacts[practice_key]
        
        return BiodiversityImpact(
            impact_type=practice_type,
            species_affected=", ".join(practice_info.get("species_affected", [])),
            impact_level=practice_info.get("impact_level", "unknown"),
            conservation_value=practice_info.get("conservation_value", 0.5),
            mitigation_measures=self._get_mitigation_measures(practice_type, knowledge_base)
        )
    
    def _get_mitigation_measures(
        self, 
        practice_type: str, 
        knowledge_base: Dict[str, Any]
    ) -> List[str]:
        """Get mitigation measures for a practice type."""
        conservation_measures = knowledge_base.get("conservation_measures", {})
        
        # Get relevant conservation measures based on practice type
        measures = []
        
        if "intensive" in practice_type.lower() or "pesticide" in practice_type.lower():
            measures.extend([
                "Implanter des bandes fleuries",
                "Créer des haies",
                "Réduire l'utilisation de pesticides",
                "Pratiquer la rotation des cultures"
            ])
        elif "organic" in practice_type.lower():
            measures.extend([
                "Maintenir les pratiques biologiques",
                "Diversifier les cultures",
                "Créer des habitats pour la faune"
            ])
        else:
            measures.extend([
                "Évaluer l'impact sur la biodiversité",
                "Considérer des mesures de conservation",
                "Surveiller les espèces présentes"
            ])
        
        return measures
    
    def _assess_conservation_measures(
        self, 
        conservation_measures: List[str], 
        knowledge_base: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess the impact of conservation measures."""
        if not conservation_measures:
            return {"total_benefit": 0, "measures_assessed": 0, "recommendations": []}
        
        conservation_data = knowledge_base.get("conservation_measures", {})
        total_benefit = 0
        measures_assessed = 0
        recommendations = []
        
        for measure in conservation_measures:
            # Find matching conservation measure
            measure_key = None
            for key in conservation_data.keys():
                if measure.lower() in key.lower() or key.lower() in measure.lower():
                    measure_key = key
                    break
            
            if measure_key:
                measure_info = conservation_data[measure_key]
                total_benefit += measure_info.get("biodiversity_benefit", 0)
                measures_assessed += 1
                
                # Add recommendations based on measure effectiveness
                if measure_info.get("cost_effectiveness", 0) > 0.7:
                    recommendations.append(f"Mesure {measure} très efficace")
                elif measure_info.get("implementation_difficulty") == "easy":
                    recommendations.append(f"Mesure {measure} facile à implémenter")
        
        return {
            "total_benefit": round(total_benefit, 2),
            "measures_assessed": measures_assessed,
            "average_benefit": round(total_benefit / measures_assessed, 2) if measures_assessed > 0 else 0,
            "recommendations": recommendations
        }
    
    def _calculate_biodiversity_score(
        self, 
        practice_impact: Optional[BiodiversityImpact], 
        conservation_assessment: Dict[str, Any], 
        knowledge_base: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate overall biodiversity score."""
        biodiversity_indicators = knowledge_base.get("biodiversity_indicators", {})
        
        # Base score from practice impact
        base_score = 50  # Default neutral score
        if practice_impact:
            base_score = practice_impact.conservation_value * 100
        
        # Adjust for conservation measures
        conservation_benefit = conservation_assessment.get("total_benefit", 0)
        adjusted_score = base_score + (conservation_benefit * 20)  # Conservation measures can add up to 20 points
        
        # Ensure score is within bounds
        final_score = max(0, min(100, adjusted_score))
        
        # Determine biodiversity level
        biodiversity_levels = knowledge_base.get("biodiversity_levels", {})
        biodiversity_level = "moderate"  # Default
        
        for level, info in biodiversity_levels.items():
            score_range = info.get("score_range", [0, 100])
            if score_range[0] <= final_score <= score_range[1]:
                biodiversity_level = level
                break
        
        return {
            "biodiversity_score": round(final_score, 2),
            "biodiversity_level": biodiversity_level,
            "biodiversity_description": biodiversity_levels.get(biodiversity_level, {}).get("description", ""),
            "base_score": base_score,
            "conservation_adjustment": round(conservation_benefit * 20, 2)
        }
    
    def _run(
        self,
        practice_type: str,
        land_use: Optional[str] = None,
        conservation_measures: Optional[List[str]] = None,
        **kwargs
    ) -> str:
        """
        Assess biodiversity impact and conservation potential of agricultural practices.
        
        Args:
            practice_type: Type of agricultural practice
            land_use: Type of land use (optional)
            conservation_measures: List of conservation measures (optional)
        """
        try:
            # Validate inputs
            validation_errors = self._validate_inputs(practice_type, land_use, conservation_measures)
            config = self._get_config()
            
            if validation_errors and config.strict_validation:
                error_messages = [f"{error.field}: {error.message}" for error in validation_errors if error.severity == "error"]
                if error_messages:
                    return json.dumps({
                        "error": "Validation errors",
                        "validation_errors": error_messages
                    })
            
            # Load knowledge base
            knowledge_base = self._load_knowledge_base()
            
            # Assess practice impact
            practice_impact = self._assess_practice_impact(practice_type, knowledge_base)
            
            # Assess conservation measures
            conservation_assessment = self._assess_conservation_measures(conservation_measures or [], knowledge_base)
            
            # Calculate biodiversity score
            biodiversity_score = self._calculate_biodiversity_score(practice_impact, conservation_assessment, knowledge_base)
            
            result = {
                "biodiversity_assessment": {
                    "practice_type": practice_type,
                    "land_use": land_use,
                    "conservation_measures": conservation_measures or [],
                    "biodiversity_score": biodiversity_score
                },
                "practice_impact": asdict(practice_impact) if practice_impact else None,
                "conservation_assessment": conservation_assessment,
                "summary": {
                    "biodiversity_score": biodiversity_score["biodiversity_score"],
                    "biodiversity_level": biodiversity_score["biodiversity_level"],
                    "conservation_measures_count": len(conservation_measures or []),
                    "impact_assessed": bool(practice_impact),
                    "conservation_benefit": conservation_assessment.get("total_benefit", 0)
                },
                "analysis_metadata": {
                    "config_used": asdict(config),
                    "knowledge_base_version": knowledge_base.get("metadata", {}).get("version", "unknown")
                }
            }
            
            # Add validation warnings if any
            if validation_errors and config.return_validation_errors:
                warnings = [{"field": error.field, "message": error.message, "severity": error.severity} 
                           for error in validation_errors if error.severity in ["warning", "info"]]
                if warnings:
                    result["validation_warnings"] = warnings
            
            return json.dumps(result, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"Assess biodiversity error: {e}")
            return json.dumps({
                "error": f"Erreur lors de l'évaluation de la biodiversité: {str(e)}",
                "error_type": type(e).__name__
            })
    
    async def _arun(
        self,
        practice_type: str,
        land_use: Optional[str] = None,
        conservation_measures: Optional[List[str]] = None,
        **kwargs
    ) -> str:
        """
        Asynchronous version of biodiversity assessment.
        """
        # For now, just call the sync version
        return self._run(practice_type, land_use, conservation_measures, **kwargs)
    
    def clear_cache(self):
        """Clear internal caches."""
        self._config_cache = None
        logger.info("Cleared tool caches")
