"""
Assess Water Management Tool - Vector Database Ready Tool

Job: Assess water management efficiency and sustainability of agricultural practices.
Input: water_usage, irrigation_system, water_quality, efficiency_measures
Output: JSON string with water management assessment

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
from ...config.water_management_config import get_water_management_config

logger = logging.getLogger(__name__)

@dataclass
class WaterManagementIndicator:
    """Structured water management indicator."""
    indicator_type: str
    current_value: float
    optimal_range: Dict[str, float]
    efficiency_status: str
    improvement_measures: List[str]

@dataclass
class ValidationError:
    """Validation error information."""
    field: str
    message: str
    severity: str

class AssessWaterManagementTool(BaseTool):
    """
    Vector Database Ready Tool: Assess water management efficiency and sustainability of agricultural practices.
    
    Job: Take water management data and assess efficiency and sustainability.
    Input: water_usage, irrigation_system, water_quality, efficiency_measures
    Output: JSON string with water management assessment
    
    Enhanced Features:
    - External knowledge base (JSON file)
    - Configurable analysis parameters
    - Asynchronous support
    - Comprehensive input validation
    - Vector database ready architecture
    """
    
    name: str = "assess_water_management_tool"
    description: str = "Évalue l'efficacité de la gestion de l'eau avec analyse avancée"
    
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
        return str(current_dir.parent.parent / "data" / "water_management_knowledge.json")
    
    def _get_config(self):
        """Get current configuration."""
        if self._config_cache is None:
            self._config_cache = get_water_management_config()
        return self._config_cache
    
    def _load_knowledge_base(self) -> Dict[str, Any]:
        """Load knowledge base from JSON file."""
        try:
            with open(self.knowledge_base_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading water management knowledge base: {e}")
            return {}
    
    def _validate_inputs(
        self, 
        water_usage: Optional[Dict[str, float]] = None,
        irrigation_system: Optional[str] = None,
        water_quality: Optional[Dict[str, float]] = None,
        efficiency_measures: Optional[List[str]] = None
    ) -> List[ValidationError]:
        """Validate input parameters."""
        errors = []
        config = self._get_config()
        
        # Validate water usage
        if config.require_water_usage and not water_usage:
            errors.append(ValidationError("water_usage", "Water usage data is required", "error"))
        
        # Validate water quality if provided
        if water_quality and config.validate_water_quality:
            for param, value in water_quality.items():
                if not isinstance(value, (int, float)):
                    errors.append(ValidationError(f"water_quality.{param}", "Value must be a number", "error"))
                elif param == "ph_level" and (value < config.min_ph or value > config.max_ph):
                    errors.append(ValidationError(f"water_quality.{param}", f"pH must be between {config.min_ph} and {config.max_ph}", "error"))
                elif param == "salinity" and (value < config.min_salinity or value > config.max_salinity):
                    errors.append(ValidationError(f"water_quality.{param}", f"Salinity must be between {config.min_salinity} and {config.max_salinity}", "error"))
        
        # Validate efficiency measures if provided
        if efficiency_measures:
            if not isinstance(efficiency_measures, list):
                errors.append(ValidationError("efficiency_measures", "Efficiency measures must be a list", "error"))
            elif len(efficiency_measures) == 0:
                errors.append(ValidationError("efficiency_measures", "Efficiency measures list cannot be empty", "warning"))
        
        return errors
    
    def _analyze_water_indicator(
        self, 
        indicator_type: str, 
        current_value: float, 
        knowledge_base: Dict[str, Any]
    ) -> WaterManagementIndicator:
        """Analyze a specific water management indicator."""
        water_indicators = knowledge_base.get("water_indicators", {})
        efficiency_measures = knowledge_base.get("efficiency_measures", {})
        
        indicator_info = water_indicators.get(indicator_type, {})
        optimal_range = indicator_info.get("optimal_range", {"min": 0, "max": 100})
        
        # Determine efficiency status
        if optimal_range["min"] <= current_value <= optimal_range["max"]:
            efficiency_status = "optimal"
        elif current_value < optimal_range["min"]:
            efficiency_status = "low"
        else:
            efficiency_status = "high"
        
        # Get improvement measures based on indicator type
        measures = []
        if indicator_type == "water_use_efficiency":
            measures = ["Surveillance de l'humidité du sol", "Irrigation de précision", "Paillage"]
        elif indicator_type == "irrigation_efficiency":
            measures = ["Maintenance du système", "Calibrage des équipements", "Formation des opérateurs"]
        elif indicator_type == "water_quality_score":
            measures = ["Filtrage de l'eau", "Traitement des eaux usées", "Surveillance de la qualité"]
        elif indicator_type == "water_conservation":
            measures = ["Recyclage de l'eau", "Récupération des eaux de pluie", "Variétés résistantes à la sécheresse"]
        elif indicator_type == "runoff_control":
            measures = ["Aménagement des pentes", "Cultures de couverture", "Systèmes de drainage"]
        
        return WaterManagementIndicator(
            indicator_type=indicator_type,
            current_value=current_value,
            optimal_range=optimal_range,
            efficiency_status=efficiency_status,
            improvement_measures=measures
        )
    
    def _assess_irrigation_system(
        self, 
        irrigation_system: str, 
        knowledge_base: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess the efficiency and sustainability of an irrigation system."""
        irrigation_systems = knowledge_base.get("irrigation_systems", {})
        
        # Find matching irrigation system
        system_key = None
        for key in irrigation_systems.keys():
            if irrigation_system and (irrigation_system.lower() in key.lower() or key.lower() in irrigation_system.lower()):
                system_key = key
                break
        
        if not system_key:
            return {
                "irrigation_system": irrigation_system,
                "system_assessed": False,
                "efficiency": 0.5,
                "sustainability_score": 0.5
            }
        
        system_info = irrigation_systems[system_key]
        
        return {
            "irrigation_system": irrigation_system,
            "system_assessed": True,
            "efficiency": system_info.get("efficiency", 0.5),
            "water_savings": system_info.get("water_savings", 0),
            "cost_effectiveness": system_info.get("cost_effectiveness", 0.5),
            "sustainability_score": system_info.get("sustainability_score", 0.5),
            "description": system_info.get("description", "")
        }
    
    def _assess_water_quality(
        self, 
        water_quality: Dict[str, float], 
        knowledge_base: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess water quality parameters."""
        if not water_quality:
            return {"quality_assessed": False, "overall_quality_score": 0}
        
        water_quality_parameters = knowledge_base.get("water_quality_parameters", {})
        total_score = 0
        total_weight = 0
        
        for param, value in water_quality.items():
            param_info = water_quality_parameters.get(param, {})
            optimal_range = param_info.get("optimal_range", {"min": 0, "max": 100})
            weight = param_info.get("impact_weight", 0.1)
            
            # Calculate score based on how close to optimal range
            if optimal_range["min"] <= value <= optimal_range["max"]:
                score = 100
            else:
                # Calculate distance from optimal range
                if value < optimal_range["min"]:
                    distance = optimal_range["min"] - value
                    max_distance = optimal_range["min"]
                else:
                    distance = value - optimal_range["max"]
                    max_distance = optimal_range["max"]
                
                score = max(0, 100 - (distance / max_distance) * 100)
            
            total_score += score * weight
            total_weight += weight
        
        overall_quality_score = total_score / total_weight if total_weight > 0 else 0
        
        return {
            "quality_assessed": True,
            "overall_quality_score": round(overall_quality_score, 2),
            "parameters_assessed": len(water_quality),
            "quality_details": water_quality
        }
    
    def _assess_efficiency_measures(
        self, 
        efficiency_measures: List[str], 
        knowledge_base: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Assess the impact of efficiency measures."""
        if not efficiency_measures:
            return {"measures_assessed": 0, "total_improvement": 0, "recommendations": []}
        
        efficiency_data = knowledge_base.get("efficiency_measures", {})
        total_improvement = 0
        measures_assessed = 0
        recommendations = []
        
        for measure in efficiency_measures:
            # Find matching efficiency measure
            measure_key = None
            for key in efficiency_data.keys():
                if measure.lower() in key.lower() or key.lower() in measure.lower():
                    measure_key = key
                    break
            
            if measure_key:
                measure_info = efficiency_data[measure_key]
                total_improvement += measure_info.get("efficiency_improvement", 0)
                measures_assessed += 1
                
                # Add recommendations based on measure effectiveness
                if measure_info.get("cost_effectiveness", 0) > 0.8:
                    recommendations.append(f"Mesure {measure} très rentable")
                elif measure_info.get("implementation_difficulty") == "easy":
                    recommendations.append(f"Mesure {measure} facile à implémenter")
        
        return {
            "measures_assessed": measures_assessed,
            "total_improvement": round(total_improvement, 2),
            "average_improvement": round(total_improvement / measures_assessed, 2) if measures_assessed > 0 else 0,
            "recommendations": recommendations
        }
    
    def _calculate_overall_water_management(
        self, 
        water_indicators: List[WaterManagementIndicator], 
        irrigation_assessment: Dict[str, Any], 
        water_quality_assessment: Dict[str, Any], 
        efficiency_assessment: Dict[str, Any], 
        knowledge_base: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate overall water management score."""
        if not water_indicators:
            return {"overall_score": 0, "management_level": "unknown", "management_description": "No data available"}
        
        # Calculate weighted score based on indicator importance
        total_score = 0
        total_weight = 0
        
        for indicator in water_indicators:
            indicator_info = knowledge_base.get("water_indicators", {}).get(indicator.indicator_type, {})
            weight = indicator_info.get("weight", 0.1)
            
            # Calculate score based on efficiency status
            if indicator.efficiency_status == "optimal":
                score = 100
            elif indicator.efficiency_status == "low":
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
        
        # Adjust for irrigation system
        irrigation_adjustment = 0
        if irrigation_assessment.get("system_assessed", False):
            irrigation_efficiency = irrigation_assessment.get("efficiency", 0.5)
            irrigation_adjustment = (irrigation_efficiency - 0.5) * 20  # Can adjust by ±10 points
        
        # Adjust for water quality
        quality_adjustment = 0
        if water_quality_assessment.get("quality_assessed", False):
            quality_score = water_quality_assessment.get("overall_quality_score", 0)
            quality_adjustment = (quality_score - 50) * 0.2  # Can adjust by ±10 points
        
        # Adjust for efficiency measures
        efficiency_adjustment = efficiency_assessment.get("total_improvement", 0) * 10  # Can add up to 10 points
        
        final_score = (total_score / total_weight) + irrigation_adjustment + quality_adjustment + efficiency_adjustment
        final_score = max(0, min(100, final_score))
        
        # Determine management level
        water_management_levels = knowledge_base.get("water_management_levels", {})
        management_level = "moderate"  # Default
        
        for level, info in water_management_levels.items():
            score_range = info.get("score_range", [0, 100])
            if score_range[0] <= final_score <= score_range[1]:
                management_level = level
                break
        
        return {
            "overall_score": round(final_score, 2),
            "management_level": management_level,
            "management_description": water_management_levels.get(management_level, {}).get("description", ""),
            "irrigation_adjustment": round(irrigation_adjustment, 2),
            "quality_adjustment": round(quality_adjustment, 2),
            "efficiency_adjustment": round(efficiency_adjustment, 2)
        }
    
    def _run(
        self,
        water_usage: Optional[Dict[str, float]] = None,
        irrigation_system: Optional[str] = None,
        water_quality: Optional[Dict[str, float]] = None,
        efficiency_measures: Optional[List[str]] = None,
        **kwargs
    ) -> str:
        """
        Assess water management efficiency and sustainability of agricultural practices.
        
        Args:
            water_usage: Dictionary of water usage indicators
            irrigation_system: Type of irrigation system
            water_quality: Dictionary of water quality parameters
            efficiency_measures: List of efficiency measures implemented
        """
        try:
            # Validate inputs
            validation_errors = self._validate_inputs(water_usage, irrigation_system, water_quality, efficiency_measures)
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
            
            # Analyze water indicators
            analyzed_indicators = []
            if water_usage:
                for indicator_type, value in water_usage.items():
                    indicator = self._analyze_water_indicator(indicator_type, value, knowledge_base)
                    analyzed_indicators.append(indicator)
            
            # Assess irrigation system
            irrigation_assessment = self._assess_irrigation_system(irrigation_system, knowledge_base)
            
            # Assess water quality
            water_quality_assessment = self._assess_water_quality(water_quality, knowledge_base)
            
            # Assess efficiency measures
            efficiency_assessment = self._assess_efficiency_measures(efficiency_measures or [], knowledge_base)
            
            # Calculate overall water management
            overall_management = self._calculate_overall_water_management(
                analyzed_indicators, irrigation_assessment, water_quality_assessment, 
                efficiency_assessment, knowledge_base
            )
            
            result = {
                "water_management_assessment": {
                    "water_usage": water_usage or {},
                    "irrigation_system": irrigation_system,
                    "water_quality": water_quality or {},
                    "efficiency_measures": efficiency_measures or [],
                    "overall_management": overall_management
                },
                "detailed_analysis": {
                    "analyzed_indicators": [asdict(indicator) for indicator in analyzed_indicators],
                    "irrigation_assessment": irrigation_assessment,
                    "water_quality_assessment": water_quality_assessment,
                    "efficiency_assessment": efficiency_assessment
                },
                "summary": {
                    "overall_score": overall_management["overall_score"],
                    "management_level": overall_management["management_level"],
                    "indicators_analyzed": len(analyzed_indicators),
                    "irrigation_system_assessed": irrigation_assessment.get("system_assessed", False),
                    "water_quality_assessed": water_quality_assessment.get("quality_assessed", False),
                    "efficiency_measures_count": len(efficiency_measures or [])
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
            logger.error(f"Assess water management error: {e}")
            return json.dumps({
                "error": f"Erreur lors de l'évaluation de la gestion de l'eau: {str(e)}",
                "error_type": type(e).__name__
            })
    
    async def _arun(
        self,
        water_usage: Optional[Dict[str, float]] = None,
        irrigation_system: Optional[str] = None,
        water_quality: Optional[Dict[str, float]] = None,
        efficiency_measures: Optional[List[str]] = None,
        **kwargs
    ) -> str:
        """
        Asynchronous version of water management assessment.
        """
        # For now, just call the sync version
        return self._run(water_usage, irrigation_system, water_quality, efficiency_measures, **kwargs)
    
    def clear_cache(self):
        """Clear internal caches."""
        self._config_cache = None
        logger.info("Cleared tool caches")
