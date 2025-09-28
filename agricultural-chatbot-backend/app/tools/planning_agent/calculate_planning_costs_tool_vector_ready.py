"""
Calculate Planning Costs Tool - Vector Database Ready Tool

Job: Calculate costs and economic impact of planning tasks.
Input: JSON string of tasks from GeneratePlanningTasksTool
Output: JSON string with cost analysis

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
from ...config.planning_costs_config import get_planning_costs_config

logger = logging.getLogger(__name__)

@dataclass
class PlanningTask:
    """Structured planning task."""
    name: str
    duration_hours: float
    equipment: str
    priority: int
    dependencies: List[str]
    cost_per_hectare: float
    yield_impact: float

@dataclass
class CostBreakdown:
    """Structured cost breakdown."""
    labor_cost: float
    equipment_cost: float
    material_cost: float
    total_cost: float
    cost_per_hectare: float

@dataclass
class ValidationError:
    """Validation error information."""
    field: str
    message: str
    severity: str

class CalculatePlanningCostsTool(BaseTool):
    """
    Vector Database Ready Tool: Calculate costs and economic impact of planning tasks.
    
    Job: Take planning tasks and calculate detailed cost analysis.
    Input: JSON string of tasks from GeneratePlanningTasksTool
    Output: JSON string with cost analysis
    
    Enhanced Features:
    - External knowledge base (JSON file)
    - Configurable analysis parameters
    - Asynchronous support
    - Comprehensive input validation
    - Vector database ready architecture
    """
    
    name: str = "calculate_planning_costs_tool"
    description: str = "Calcule les coûts et l'impact économique avec analyse avancée"
    
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
        return str(current_dir.parent.parent / "data" / "planning_costs_knowledge.json")
    
    def _get_config(self):
        """Get current configuration."""
        if self._config_cache is None:
            self._config_cache = get_planning_costs_config()
        return self._config_cache
    
    def _load_knowledge_base(self) -> Dict[str, Any]:
        """Load knowledge base from JSON file."""
        try:
            with open(self.knowledge_base_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading planning costs knowledge base: {e}")
            return {}
    
    def _validate_inputs(
        self, 
        tasks_json: str, 
        region: str = "france"
    ) -> List[ValidationError]:
        """Validate input parameters."""
        errors = []
        config = self._get_config()
        
        # Validate tasks JSON
        if config.require_tasks:
            try:
                data = json.loads(tasks_json)
                if "error" in data:
                    errors.append(ValidationError("tasks_json", "Tasks data contains errors", "error"))
                elif not data.get("tasks"):
                    errors.append(ValidationError("tasks_json", "No tasks provided", "error"))
                else:
                    tasks = data.get("tasks", [])
                    if len(tasks) < config.min_tasks:
                        errors.append(ValidationError("tasks_json", f"Minimum {config.min_tasks} tasks required", "error"))
                    elif len(tasks) > config.max_tasks:
                        errors.append(ValidationError("tasks_json", f"Maximum {config.max_tasks} tasks allowed", "error"))
            except json.JSONDecodeError:
                errors.append(ValidationError("tasks_json", "Invalid JSON format", "error"))
        
        # Validate region
        if config.require_region and not region:
            errors.append(ValidationError("region", "Region is required", "error"))
        
        return errors
    
    def _calculate_task_costs(
        self, 
        task: PlanningTask, 
        surface_ha: float,
        region: str,
        knowledge_base: Dict[str, Any]
    ) -> CostBreakdown:
        """Calculate detailed costs for a single task."""
        cost_components = knowledge_base.get("cost_components", {})
        regional_factors = knowledge_base.get("regional_factors", {}).get(region.lower(), {})
        
        # Labor costs
        labor_data = cost_components.get("labor", {})
        labor_cost = 0.0
        if self._get_config().include_labor_costs:
            hourly_rate = labor_data.get("hourly_rate", 15.0)
            benefits_multiplier = 1.0 + labor_data.get("benefits_percentage", 0.25)
            regional_multiplier = regional_factors.get("labor_cost_multiplier", 1.0)
            labor_cost = task.duration_hours * hourly_rate * benefits_multiplier * regional_multiplier
        
        # Equipment costs
        equipment_cost = 0.0
        if self._get_config().include_equipment_costs:
            equipment_data = cost_components.get("equipment", {})
            hourly_rates = equipment_data.get("hourly_rates", {})
            equipment_rate = hourly_rates.get(task.equipment, 30.0)
            maintenance_multiplier = 1.0 + equipment_data.get("maintenance_percentage", 0.15)
            fuel_cost = equipment_data.get("fuel_cost_per_hour", 5.0)
            regional_multiplier = regional_factors.get("equipment_cost_multiplier", 1.0)
            equipment_cost = (task.duration_hours * equipment_rate * maintenance_multiplier + 
                            task.duration_hours * fuel_cost) * regional_multiplier
        
        # Material costs
        material_cost = 0.0
        if self._get_config().include_material_costs:
            regional_multiplier = regional_factors.get("material_cost_multiplier", 1.0)
            material_cost = task.cost_per_hectare * surface_ha * regional_multiplier
        
        # Total cost
        total_cost = labor_cost + equipment_cost + material_cost
        cost_per_hectare = total_cost / surface_ha if surface_ha > 0 else 0
        
        return CostBreakdown(
            labor_cost=round(labor_cost, 2),
            equipment_cost=round(equipment_cost, 2),
            material_cost=round(material_cost, 2),
            total_cost=round(total_cost, 2),
            cost_per_hectare=round(cost_per_hectare, 2)
        )
    
    def _calculate_economic_impact(
        self, 
        tasks: List[PlanningTask], 
        surface_ha: float,
        knowledge_base: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate economic impact of planning tasks."""
        economic_indicators = knowledge_base.get("economic_indicators", {})
        crop_prices = economic_indicators.get("crop_prices", {})
        yield_impact_multipliers = economic_indicators.get("yield_impact_multipliers", {})
        
        # Calculate total yield impact
        total_yield_impact = sum(task.yield_impact for task in tasks)
        
        # Estimate crop type (simplified - would need more sophisticated logic)
        crop_type = "blé"  # Default assumption
        crop_price = crop_prices.get(crop_type, 200.0)
        
        # Calculate potential revenue impact
        yield_multiplier = yield_impact_multipliers.get("medium", 1.0)  # Default to medium
        if total_yield_impact > 0.5:
            yield_multiplier = yield_impact_multipliers.get("high", 1.2)
        elif total_yield_impact < 0.2:
            yield_multiplier = yield_impact_multipliers.get("low", 0.8)
        
        # Estimate revenue impact (simplified calculation)
        estimated_yield = 70.0  # q/ha - would need actual yield data
        revenue_impact = (yield_multiplier - 1.0) * estimated_yield * crop_price * surface_ha
        
        return {
            "total_yield_impact": round(total_yield_impact, 2),
            "yield_multiplier": round(yield_multiplier, 2),
            "estimated_revenue_impact": round(revenue_impact, 2),
            "crop_type_assumed": crop_type,
            "crop_price_used": crop_price
        }
    
    def _run(
        self, 
        tasks_json: str,
        region: str = "france",
        **kwargs
    ) -> str:
        """
        Calculate costs and economic impact of planning tasks.
        
        Args:
            tasks_json: JSON string of tasks from GeneratePlanningTasksTool
            region: Region for cost calculations (france, europe)
        """
        try:
            # Validate inputs
            validation_errors = self._validate_inputs(tasks_json, region)
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
            
            # Parse tasks data
            data = json.loads(tasks_json)
            
            if "error" in data:
                return tasks_json  # Pass through errors
            
            tasks_data = data.get("tasks", [])
            surface_ha = data.get("surface_ha", 1.0)
            
            if not tasks_data:
                return json.dumps({"error": "Aucune tâche fournie pour le calcul des coûts"})
            
            # Convert to PlanningTask objects
            tasks = [PlanningTask(**task) for task in tasks_data]
            
            # Calculate costs for each task
            task_costs = []
            for task in tasks:
                cost_breakdown = self._calculate_task_costs(task, surface_ha, region, knowledge_base)
                task_costs.append({
                    "task_name": task.name,
                    "cost_breakdown": asdict(cost_breakdown)
                })
            
            # Calculate total costs
            total_labor_cost = sum(cost["cost_breakdown"]["labor_cost"] for cost in task_costs)
            total_equipment_cost = sum(cost["cost_breakdown"]["equipment_cost"] for cost in task_costs)
            total_material_cost = sum(cost["cost_breakdown"]["material_cost"] for cost in task_costs)
            total_cost = total_labor_cost + total_equipment_cost + total_material_cost
            
            # Calculate economic impact
            economic_impact = self._calculate_economic_impact(tasks, surface_ha, knowledge_base)
            
            result = {
                "region": region,
                "surface_ha": surface_ha,
                "task_costs": task_costs,
                "total_costs": {
                    "labor_cost": round(total_labor_cost, 2),
                    "equipment_cost": round(total_equipment_cost, 2),
                    "material_cost": round(total_material_cost, 2),
                    "total_cost": round(total_cost, 2),
                    "cost_per_hectare": round(total_cost / surface_ha, 2) if surface_ha > 0 else 0
                },
                "economic_impact": economic_impact,
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
            logger.error(f"Calculate planning costs error: {e}")
            return json.dumps({
                "error": f"Erreur lors du calcul des coûts de planification: {str(e)}",
                "error_type": type(e).__name__
            })
    
    async def _arun(
        self, 
        tasks_json: str,
        region: str = "france",
        **kwargs
    ) -> str:
        """
        Asynchronous version of planning cost calculation.
        """
        # For now, just call the sync version
        return self._run(tasks_json, region, **kwargs)
    
    def clear_cache(self):
        """Clear internal caches."""
        self._config_cache = None
        logger.info("Cleared tool caches")
