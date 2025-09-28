"""
Calculate Carbon Footprint Tool - Vector Database Ready Tool

Job: Calculate carbon footprint for agricultural practices and operations.
Input: practice_type, inputs_used, area_ha, duration
Output: JSON string with carbon footprint analysis

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
from ...config.carbon_footprint_config import get_carbon_footprint_config

logger = logging.getLogger(__name__)

@dataclass
class CarbonFootprintComponent:
    """Structured carbon footprint component."""
    component_type: str
    emission_source: str
    co2_equivalent: float
    percentage: float
    reduction_potential: float

@dataclass
class ValidationError:
    """Validation error information."""
    field: str
    message: str
    severity: str

class CalculateCarbonFootprintTool(BaseTool):
    """
    Vector Database Ready Tool: Calculate carbon footprint for agricultural practices and operations.
    
    Job: Take agricultural practice data and calculate carbon footprint.
    Input: practice_type, inputs_used, area_ha, duration
    Output: JSON string with carbon footprint analysis
    
    Enhanced Features:
    - External knowledge base (JSON file)
    - Configurable analysis parameters
    - Asynchronous support
    - Comprehensive input validation
    - Vector database ready architecture
    """
    
    name: str = "calculate_carbon_footprint_tool"
    description: str = "Calcule l'empreinte carbone des pratiques agricoles avec analyse avancée"
    
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
        return str(current_dir.parent.parent / "data" / "carbon_footprint_knowledge.json")
    
    def _get_config(self):
        """Get current configuration."""
        if self._config_cache is None:
            self._config_cache = get_carbon_footprint_config()
        return self._config_cache
    
    def _load_knowledge_base(self) -> Dict[str, Any]:
        """Load knowledge base from JSON file."""
        try:
            with open(self.knowledge_base_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading carbon footprint knowledge base: {e}")
            return {}
    
    def _validate_inputs(
        self, 
        practice_type: str, 
        inputs_used: List[str], 
        area_ha: float, 
        duration_days: int
    ) -> List[ValidationError]:
        """Validate input parameters."""
        errors = []
        config = self._get_config()
        
        # Validate practice type
        if config.require_practice_type and not practice_type:
            errors.append(ValidationError("practice_type", "Practice type is required", "error"))
        
        # Validate area
        if config.validate_area_range:
            if area_ha < config.min_area_ha:
                errors.append(ValidationError("area_ha", f"Area too small (minimum {config.min_area_ha} ha)", "error"))
            elif area_ha > config.max_area_ha:
                errors.append(ValidationError("area_ha", f"Area too large (maximum {config.max_area_ha} ha)", "warning"))
        
        # Validate duration
        if duration_days < config.min_duration_days:
            errors.append(ValidationError("duration_days", f"Duration too short (minimum {config.min_duration_days} days)", "error"))
        elif duration_days > config.max_duration_days:
            errors.append(ValidationError("duration_days", f"Duration too long (maximum {config.max_duration_days} days)", "warning"))
        
        return errors
    
    def _calculate_carbon_components(
        self, 
        practice_type: str, 
        inputs_used: List[str], 
        area_ha: float, 
        duration_days: int, 
        knowledge_base: Dict[str, Any]
    ) -> List[CarbonFootprintComponent]:
        """Calculate carbon footprint components."""
        components = []
        emission_factors = knowledge_base.get("emission_factors", {})
        usage_rates = knowledge_base.get("default_usage_rates", {})
        
        # Calculate practice-specific emissions
        practices = emission_factors.get("practices", {})
        if practice_type in practices:
            practice_data = practices[practice_type]
            co2_equivalent = practice_data["co2_per_ha"] * area_ha
            component = CarbonFootprintComponent(
                component_type="practice",
                emission_source=practice_type,
                co2_equivalent=co2_equivalent,
                percentage=0.0,  # Will be calculated later
                reduction_potential=practice_data["reduction_potential"]
            )
            components.append(component)
        
        # Calculate input-specific emissions
        for input_type in inputs_used:
            input_lower = input_type.lower()
            
            # Check fertilizers
            fertilizers = emission_factors.get("fertilizers", {})
            if input_lower in fertilizers:
                fertilizer_data = fertilizers[input_lower]
                usage_rate = usage_rates.get("fertilizer_kg_per_ha", 0.1)
                co2_equivalent = fertilizer_data["co2_per_kg"] * area_ha * usage_rate
                component = CarbonFootprintComponent(
                    component_type="fertilizer",
                    emission_source=input_type,
                    co2_equivalent=co2_equivalent,
                    percentage=0.0,
                    reduction_potential=fertilizer_data["reduction_potential"]
                )
                components.append(component)
            
            # Check pesticides
            pesticides = emission_factors.get("pesticides", {})
            if input_lower in pesticides:
                pesticide_data = pesticides[input_lower]
                usage_rate = usage_rates.get("pesticide_kg_per_ha", 0.05)
                co2_equivalent = pesticide_data["co2_per_kg"] * area_ha * usage_rate
                component = CarbonFootprintComponent(
                    component_type="pesticide",
                    emission_source=input_type,
                    co2_equivalent=co2_equivalent,
                    percentage=0.0,
                    reduction_potential=pesticide_data["reduction_potential"]
                )
                components.append(component)
            
            # Check fuel
            fuel = emission_factors.get("fuel", {})
            if input_lower in fuel:
                fuel_data = fuel[input_lower]
                usage_rate = usage_rates.get("fuel_liters_per_ha", 2.0)
                co2_equivalent = fuel_data["co2_per_liter"] * area_ha * usage_rate
                component = CarbonFootprintComponent(
                    component_type="fuel",
                    emission_source=input_type,
                    co2_equivalent=co2_equivalent,
                    percentage=0.0,
                    reduction_potential=fuel_data["reduction_potential"]
                )
                components.append(component)
        
        # Calculate percentages
        total_emissions = sum(component.co2_equivalent for component in components)
        for component in components:
            component.percentage = (component.co2_equivalent / total_emissions * 100) if total_emissions > 0 else 0
        
        return components
    
    def _generate_reduction_recommendations(
        self, 
        carbon_components: List[CarbonFootprintComponent], 
        knowledge_base: Dict[str, Any]
    ) -> List[str]:
        """Generate carbon reduction recommendations."""
        recommendations = []
        config = self._get_config()
        reduction_strategies = knowledge_base.get("reduction_strategies", {})
        
        # Sort components by emission level
        sorted_components = sorted(carbon_components, key=lambda x: x.co2_equivalent, reverse=True)
        
        for component in sorted_components:
            if component.co2_equivalent > config.minimum_emission_threshold:
                component_type = component.component_type
                if component_type in reduction_strategies:
                    for strategy in reduction_strategies[component_type]:
                        recommendations.append(f"🌱 {strategy} (réduction potentielle: {component.reduction_potential:.0%})")
        
        # General recommendations
        recommendations.extend([
            "🌿 Considérer l'agriculture biologique pour réduire l'empreinte carbone",
            "♻️ Implémenter des pratiques de circularité (compost, rotation)",
            "🌱 Utiliser des variétés résistantes pour réduire les intrants"
        ])
        
        return recommendations
    
    def _run(
        self,
        practice_type: str,
        inputs_used: List[str] = None,
        area_ha: float = 1.0,
        duration_days: int = 1,
        **kwargs
    ) -> str:
        """
        Calculate carbon footprint for agricultural practices and operations.
        
        Args:
            practice_type: Type of agricultural practice (spraying, fertilization, etc.)
            inputs_used: List of inputs used (fertilizers, pesticides, fuel, etc.)
            area_ha: Area in hectares
            duration_days: Duration in days
        """
        try:
            # Validate inputs
            validation_errors = self._validate_inputs(practice_type, inputs_used or [], area_ha, duration_days)
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
            
            # Calculate carbon footprint components
            carbon_components = self._calculate_carbon_components(
                practice_type, inputs_used or [], area_ha, duration_days, knowledge_base
            )
            
            # Calculate total carbon footprint
            total_carbon_footprint = sum(component.co2_equivalent for component in carbon_components)
            
            # Calculate carbon intensity
            carbon_intensity = total_carbon_footprint / area_ha if area_ha > 0 else 0
            
            # Generate reduction recommendations
            reduction_recommendations = self._generate_reduction_recommendations(carbon_components, knowledge_base)
            
            result = {
                "practice_type": practice_type,
                "inputs_used": inputs_used or [],
                "area_ha": area_ha,
                "duration_days": duration_days,
                "carbon_components": [asdict(component) for component in carbon_components],
                "total_carbon_footprint": round(total_carbon_footprint, 2),
                "carbon_intensity": round(carbon_intensity, 2),
                "reduction_recommendations": reduction_recommendations,
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
            logger.error(f"Calculate carbon footprint error: {e}")
            return json.dumps({
                "error": f"Erreur lors du calcul de l'empreinte carbone: {str(e)}",
                "error_type": type(e).__name__
            })
    
    async def _arun(
        self,
        practice_type: str,
        inputs_used: List[str] = None,
        area_ha: float = 1.0,
        duration_days: int = 1,
        **kwargs
    ) -> str:
        """
        Asynchronous version of carbon footprint calculation.
        """
        # For now, just call the sync version
        return self._run(practice_type, inputs_used, area_ha, duration_days, **kwargs)
    
    def clear_cache(self):
        """Clear internal caches."""
        self._config_cache = None
        logger.info("Cleared tool caches")
