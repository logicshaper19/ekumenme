"""
Generate Planning Tasks Tool - Vector Database Ready Tool

Job: Generate planning tasks for specific crops and surface area.
Input: crops, surface, planning_objective
Output: JSON string of PlanningTask objects

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
from ...config.planning_tasks_config import get_planning_tasks_config

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
class ValidationError:
    """Validation error information."""
    field: str
    message: str
    severity: str

class GeneratePlanningTasksTool(BaseTool):
    """
    Vector Database Ready Tool: Generate planning tasks for specific crops and surface area.
    
    Job: Generate standard agricultural tasks for given crops and surface.
    Input: crops, surface, planning_objective
    Output: JSON string of PlanningTask objects
    
    Enhanced Features:
    - External knowledge base (JSON file)
    - Configurable analysis parameters
    - Asynchronous support
    - Comprehensive input validation
    - Vector database ready architecture
    """
    
    name: str = "generate_planning_tasks_tool"
    description: str = "Génère les tâches de planification avec analyse avancée"
    
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
        return str(current_dir.parent.parent / "data" / "planning_tasks_knowledge.json")
    
    def _get_config(self):
        """Get current configuration."""
        if self._config_cache is None:
            self._config_cache = get_planning_tasks_config()
        return self._config_cache
    
    def _load_knowledge_base(self) -> Dict[str, Any]:
        """Load knowledge base from JSON file."""
        try:
            with open(self.knowledge_base_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading planning tasks knowledge base: {e}")
            return {}
    
    def _validate_inputs(
        self, 
        crops: List[str], 
        surface_ha: float,
        planning_objective: str
    ) -> List[ValidationError]:
        """Validate input parameters."""
        errors = []
        config = self._get_config()
        
        # Validate crops
        if config.require_crops:
            if not crops:
                errors.append(ValidationError("crops", "At least one crop must be specified", "error"))
            elif len(crops) < config.min_crops:
                errors.append(ValidationError("crops", f"Minimum {config.min_crops} crops required", "error"))
            elif len(crops) > config.max_crops:
                errors.append(ValidationError("crops", f"Maximum {config.max_crops} crops allowed", "error"))
        
        # Validate surface area
        if config.validate_surface_area:
            if surface_ha < config.min_surface_ha:
                errors.append(ValidationError("surface_ha", f"Surface too small (minimum {config.min_surface_ha} ha)", "error"))
            elif surface_ha > config.max_surface_ha:
                errors.append(ValidationError("surface_ha", f"Surface too large (maximum {config.max_surface_ha} ha)", "warning"))
        
        # Validate planning objective
        if config.validate_planning_objective and not planning_objective:
            errors.append(ValidationError("planning_objective", "Planning objective is required", "error"))
        
        return errors
    
    def _generate_tasks_for_crop(
        self, 
        crop: str, 
        surface_ha: float, 
        planning_objective: str,
        knowledge_base: Dict[str, Any]
    ) -> List[PlanningTask]:
        """Generate tasks for a specific crop."""
        tasks = []
        crop_tasks = knowledge_base.get("crop_tasks", {}).get(crop.lower(), {})
        task_dependencies = knowledge_base.get("task_dependencies", {})
        
        # Generate tasks for each phase
        for phase, phase_tasks in crop_tasks.items():
            for task_data in phase_tasks:
                # Get dependencies
                dependencies = task_dependencies.get(task_data["name"], [])
                
                # Create PlanningTask object
                task = PlanningTask(
                    name=task_data["name"],
                    duration_hours=task_data["duration_hours"] * surface_ha,
                    equipment=task_data["equipment"],
                    priority=task_data["priority"],
                    dependencies=dependencies,
                    cost_per_hectare=task_data["cost_per_hectare"],
                    yield_impact=task_data["yield_impact"]
                )
                tasks.append(task)
        
        return tasks
    
    def _run(
        self, 
        crops: List[str],
        surface_ha: float,
        planning_objective: str,
        **kwargs
    ) -> str:
        """
        Generate planning tasks for specific crops and surface area.
        
        Args:
            crops: List of crop types
            surface_ha: Surface area in hectares
            planning_objective: Planning objective (e.g., "maximize_yield", "minimize_cost")
        """
        try:
            # Validate inputs
            validation_errors = self._validate_inputs(crops, surface_ha, planning_objective)
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
            
            # Generate tasks for each crop
            all_tasks = []
            for crop in crops:
                crop_tasks = self._generate_tasks_for_crop(crop, surface_ha, planning_objective, knowledge_base)
                all_tasks.extend(crop_tasks)
            
            # Calculate summary statistics
            total_duration = sum(task.duration_hours for task in all_tasks)
            total_cost = sum(task.cost_per_hectare * surface_ha for task in all_tasks)
            total_yield_impact = sum(task.yield_impact for task in all_tasks)
            
            result = {
                "crops": crops,
                "surface_ha": surface_ha,
                "planning_objective": planning_objective,
                "tasks": [asdict(task) for task in all_tasks],
                "summary": {
                    "total_tasks": len(all_tasks),
                    "total_duration_hours": round(total_duration, 2),
                    "total_cost_eur": round(total_cost, 2),
                    "total_yield_impact": round(total_yield_impact, 2),
                    "cost_per_hectare": round(total_cost / surface_ha, 2) if surface_ha > 0 else 0
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
            logger.error(f"Generate planning tasks error: {e}")
            return json.dumps({
                "error": f"Erreur lors de la génération des tâches de planification: {str(e)}",
                "error_type": type(e).__name__
            })
    
    async def _arun(
        self, 
        crops: List[str],
        surface_ha: float,
        planning_objective: str,
        **kwargs
    ) -> str:
        """
        Asynchronous version of planning task generation.
        """
        # For now, just call the sync version
        return self._run(crops, surface_ha, planning_objective, **kwargs)
    
    def clear_cache(self):
        """Clear internal caches."""
        self._config_cache = None
        logger.info("Cleared tool caches")
