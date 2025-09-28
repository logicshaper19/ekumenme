"""
Analyze Soil Health Tool - Vector Database Ready Tool

Job: Analyze soil health indicators and sustainability of agricultural practices.
Input: soil_indicators, practice_type, management_practices
Output: JSON string with soil health analysis

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
from ...config.soil_health_config import get_soil_health_config

logger = logging.getLogger(__name__)

@dataclass
class SoilHealthIndicator:
    """Structured soil health indicator."""
    indicator_type: str
    current_value: float
    optimal_range: Dict[str, float]
    health_status: str
    improvement_measures: List[str]

@dataclass
class ValidationError:
    """Validation error information."""
    field: str
    message: str
    severity: str

class AnalyzeSoilHealthTool(BaseTool):
    """
    Vector Database Ready Tool: Analyze soil health indicators and sustainability of agricultural practices.
    
    Job: Take soil indicators and practice data to analyze soil health.
    Input: soil_indicators, practice_type, management_practices
    Output: JSON string with soil health analysis
    
    Enhanced Features:
    - External knowledge base (JSON file)
    - Configurable analysis parameters
    - Asynchronous support
    - Comprehensive input validation
    - Vector database ready architecture
    """
    
    name: str = "analyze_soil_health_tool"
    description: str = "Analyse la santé du sol avec analyse avancée"
    
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
        return str(current_dir.parent.parent / "data" / "soil_health_knowledge.json")
    
    def _get_config(self):
        """Get current configuration."""
        if self._config_cache is None:
            self._config_cache = get_soil_health_config()
        return self._config_cache
    
    def _load_knowledge_base(self) -> Dict[str, Any]:
        """Load knowledge base from JSON file."""
        try:
            with open(self.knowledge_base_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading soil health knowledge base: {e}")
            return {}
    
    def _validate_inputs(
        self, 
        soil_indicators: Optional[Dict[str, float]] = None,
        practice_type: Optional[str] = None,
        management_practices: Optional[List[str]] = None
    ) -> List[ValidationError]:
        """Validate input parameters."""
        errors = []
        config = self._get_config()
        
        # Validate soil indicators
        if config.require_soil_indicators and not soil_indicators:
            errors.append(ValidationError("soil_indicators", "Soil indicators are required", "error"))
        
        # Validate indicator values if provided
        if soil_indicators and config.validate_indicator_values:
            for indicator, value in soil_indicators.items():
                if not isinstance(value, (int, float)):
                    errors.append(ValidationError(f"soil_indicators.{indicator}", "Value must be a number", "error"))
                elif indicator == "organic_matter" and (value < config.min_organic_matter or value > config.max_organic_matter):
                    errors.append(ValidationError(f"soil_indicators.{indicator}", f"Value must be between {config.min_organic_matter} and {config.max_organic_matter}", "error"))
                elif indicator == "ph_level" and (value < config.min_ph or value > config.max_ph):
                    errors.append(ValidationError(f"soil_indicators.{indicator}", f"Value must be between {config.min_ph} and {config.max_ph}", "error"))
                elif indicator == "nutrient_content" and (value < config.min_nutrients or value > config.max_nutrients):
                    errors.append(ValidationError(f"soil_indicators.{indicator}", f"Value must be between {config.min_nutrients} and {config.max_nutrients}", "error"))
        
        # Validate management practices if provided
        if management_practices:
            if not isinstance(management_practices, list):
                errors.append(ValidationError("management_practices", "Management practices must be a list", "error"))
            elif len(management_practices) == 0:
                errors.append(ValidationError("management_practices", "Management practices list cannot be empty", "warning"))
        
        return errors
    
    def _analyze_soil_indicator(
        self, 
        indicator_type: str, 
        current_value: float, 
        knowledge_base: Dict[str, Any]
    ) -> SoilHealthIndicator:
        """Analyze a specific soil health indicator."""
        soil_indicators = knowledge_base.get("soil_indicators", {})
        improvement_measures = knowledge_base.get("improvement_measures", {})
        
        indicator_info = soil_indicators.get(indicator_type, {})
        optimal_range = indicator_info.get("optimal_range", {"min": 0, "max": 100})
        
        # Determine health status
        if optimal_range["min"] <= current_value <= optimal_range["max"]:
            health_status = "optimal"
        elif current_value < optimal_range["min"]:
            health_status = "low"
        else:
            health_status = "high"
        
        # Get improvement measures
        measures = improvement_measures.get(indicator_type, [])
        
        return SoilHealthIndicator(
            indicator_type=indicator_type,
            current_value=current_value,
            optimal_range=optimal_range,
            health_status=health_status,
            improvement_measures=measures
        )
    
    def _assess_practice_impact(
        self, 
        practice_type: str, 
        knowledge_base: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess the impact of agricultural practices on soil health."""
        practice_impacts = knowledge_base.get("practice_impacts", {})
        
        # Find matching practice type
        practice_key = None
        for key in practice_impacts.keys():
            if practice_type and (practice_type.lower() in key.lower() or key.lower() in practice_type.lower()):
                practice_key = key
                break
        
        if not practice_key:
            return {
                "practice_type": practice_type,
                "impact_assessed": False,
                "sustainability_score": 0.5,
                "impacts": {}
            }
        
        practice_info = practice_impacts[practice_key]
        
        return {
            "practice_type": practice_type,
            "impact_assessed": True,
            "sustainability_score": practice_info.get("sustainability_score", 0.5),
            "impacts": {
                "organic_matter_impact": practice_info.get("organic_matter_impact", 0),
                "structure_impact": practice_info.get("structure_impact", 0),
                "biological_activity_impact": practice_info.get("biological_activity_impact", 0),
                "erosion_risk": practice_info.get("erosion_risk", 0.5)
            }
        }
    
    def _calculate_overall_soil_health(
        self, 
        soil_indicators: List[SoilHealthIndicator], 
        practice_impact: Dict[str, Any], 
        knowledge_base: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate overall soil health score."""
        if not soil_indicators:
            return {"overall_score": 0, "health_level": "unknown", "health_description": "No data available"}
        
        # Calculate weighted score based on indicator importance
        total_score = 0
        total_weight = 0
        
        for indicator in soil_indicators:
            indicator_info = knowledge_base.get("soil_indicators", {}).get(indicator.indicator_type, {})
            weight = indicator_info.get("weight", 0.1)
            
            # Calculate score based on health status
            if indicator.health_status == "optimal":
                score = 100
            elif indicator.health_status == "low":
                # Calculate how far below optimal
                optimal_range = indicator.optimal_range
                if optimal_range["min"] > 0:
                    score = max(0, (indicator.current_value / optimal_range["min"]) * 50)
                else:
                    score = 25
            else:  # high
                # Calculate how far above optimal
                optimal_range = indicator.optimal_range
                if optimal_range["max"] > optimal_range["min"]:
                    excess = indicator.current_value - optimal_range["max"]
                    max_excess = optimal_range["max"] * 0.5  # 50% above optimal is still good
                    score = max(50, 100 - (excess / max_excess) * 50)
                else:
                    score = 75
            
            total_score += score * weight
            total_weight += weight
        
        # Adjust for practice impact
        practice_adjustment = 0
        if practice_impact.get("impact_assessed", False):
            sustainability_score = practice_impact.get("sustainability_score", 0.5)
            practice_adjustment = (sustainability_score - 0.5) * 20  # Can adjust by ±10 points
        
        final_score = (total_score / total_weight) + practice_adjustment
        final_score = max(0, min(100, final_score))
        
        # Determine health level
        soil_health_levels = knowledge_base.get("soil_health_levels", {})
        health_level = "moderate"  # Default
        
        for level, info in soil_health_levels.items():
            score_range = info.get("score_range", [0, 100])
            if score_range[0] <= final_score <= score_range[1]:
                health_level = level
                break
        
        return {
            "overall_score": round(final_score, 2),
            "health_level": health_level,
            "health_description": soil_health_levels.get(health_level, {}).get("description", ""),
            "practice_adjustment": round(practice_adjustment, 2)
        }
    
    def _run(
        self,
        soil_indicators: Optional[Dict[str, float]] = None,
        practice_type: Optional[str] = None,
        management_practices: Optional[List[str]] = None,
        **kwargs
    ) -> str:
        """
        Analyze soil health indicators and sustainability of agricultural practices.
        
        Args:
            soil_indicators: Dictionary of soil health indicators and their values
            practice_type: Type of agricultural practice
            management_practices: List of management practices
        """
        try:
            # Validate inputs
            validation_errors = self._validate_inputs(soil_indicators, practice_type, management_practices)
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
            
            # Analyze soil indicators
            analyzed_indicators = []
            if soil_indicators:
                for indicator_type, value in soil_indicators.items():
                    indicator = self._analyze_soil_indicator(indicator_type, value, knowledge_base)
                    analyzed_indicators.append(indicator)
            
            # Assess practice impact
            practice_impact = self._assess_practice_impact(practice_type, knowledge_base)
            
            # Calculate overall soil health
            overall_health = self._calculate_overall_soil_health(analyzed_indicators, practice_impact, knowledge_base)
            
            result = {
                "soil_health_analysis": {
                    "soil_indicators": soil_indicators or {},
                    "practice_type": practice_type,
                    "management_practices": management_practices or [],
                    "overall_health": overall_health
                },
                "detailed_analysis": {
                    "analyzed_indicators": [asdict(indicator) for indicator in analyzed_indicators],
                    "practice_impact": practice_impact
                },
                "summary": {
                    "overall_score": overall_health["overall_score"],
                    "health_level": overall_health["health_level"],
                    "indicators_analyzed": len(analyzed_indicators),
                    "practice_impact_assessed": practice_impact.get("impact_assessed", False),
                    "management_practices_count": len(management_practices or [])
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
            logger.error(f"Analyze soil health error: {e}")
            return json.dumps({
                "error": f"Erreur lors de l'analyse de la santé du sol: {str(e)}",
                "error_type": type(e).__name__
            })
    
    async def _arun(
        self,
        soil_indicators: Optional[Dict[str, float]] = None,
        practice_type: Optional[str] = None,
        management_practices: Optional[List[str]] = None,
        **kwargs
    ) -> str:
        """
        Asynchronous version of soil health analysis.
        """
        # For now, just call the sync version
        return self._run(soil_indicators, practice_type, management_practices, **kwargs)
    
    def clear_cache(self):
        """Clear internal caches."""
        self._config_cache = None
        logger.info("Cleared tool caches")
