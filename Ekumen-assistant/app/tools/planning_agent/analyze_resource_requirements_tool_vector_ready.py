"""
Analyze Resource Requirements Tool - Vector Database Ready Tool

Job: Analyze resource requirements for planning tasks.
Input: JSON string of tasks from GeneratePlanningTasksTool
Output: JSON string with resource analysis

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
from ...config.resource_requirements_config import get_resource_requirements_config

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
class ResourceRequirement:
    """Structured resource requirement."""
    resource_type: str
    resource_name: str
    quantity: float
    unit: str
    duration_hours: float
    priority: int

@dataclass
class ValidationError:
    """Validation error information."""
    field: str
    message: str
    severity: str

class AnalyzeResourceRequirementsTool(BaseTool):
    """
    Vector Database Ready Tool: Analyze resource requirements for planning tasks.
    
    Job: Take planning tasks and analyze resource requirements.
    Input: JSON string of tasks from GeneratePlanningTasksTool
    Output: JSON string with resource analysis
    
    Enhanced Features:
    - External knowledge base (JSON file)
    - Configurable analysis parameters
    - Asynchronous support
    - Comprehensive input validation
    - Vector database ready architecture
    """
    
    name: str = "analyze_resource_requirements_tool"
    description: str = "Analyse les besoins en ressources avec analyse avancée"
    
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
        return str(current_dir.parent.parent / "data" / "resource_requirements_knowledge.json")
    
    def _get_config(self):
        """Get current configuration."""
        if self._config_cache is None:
            self._config_cache = get_resource_requirements_config()
        return self._config_cache
    
    def _load_knowledge_base(self) -> Dict[str, Any]:
        """Load knowledge base from JSON file."""
        try:
            with open(self.knowledge_base_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading resource requirements knowledge base: {e}")
            return {}
    
    def _validate_inputs(
        self, 
        tasks_json: str, 
        analysis_type: str
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
        
        # Validate analysis type
        if config.require_analysis_type and not analysis_type:
            errors.append(ValidationError("analysis_type", "Analysis type is required", "error"))
        
        return errors
    
    def _analyze_equipment_requirements(
        self, 
        tasks: List[PlanningTask], 
        knowledge_base: Dict[str, Any]
    ) -> List[ResourceRequirement]:
        """Analyze equipment requirements for tasks."""
        equipment_specs = knowledge_base.get("equipment_specifications", {})
        resource_constraints = knowledge_base.get("resource_constraints", {})
        equipment_availability = resource_constraints.get("equipment_availability", {})
        
        equipment_requirements = []
        equipment_usage = {}
        
        for task in tasks:
            equipment = task.equipment
            if equipment in equipment_specs:
                specs = equipment_specs[equipment]
                
                # Calculate equipment usage
                if equipment not in equipment_usage:
                    equipment_usage[equipment] = {
                        "total_hours": 0,
                        "power_requirement": specs.get("power_requirement_hp", 0),
                        "operator_requirement": specs.get("operator_requirement", 1)
                    }
                
                equipment_usage[equipment]["total_hours"] += task.duration_hours
        
        # Create resource requirements
        for equipment, usage in equipment_usage.items():
            specs = equipment_specs[equipment]
            peak_multiplier = equipment_availability.get("peak_season_multiplier", 0.8)
            maintenance_buffer = equipment_availability.get("maintenance_buffer_hours", 2.0)
            
            requirement = ResourceRequirement(
                resource_type="equipment",
                resource_name=equipment,
                quantity=1,
                unit="unit",
                duration_hours=usage["total_hours"] / peak_multiplier + maintenance_buffer,
                priority=1
            )
            equipment_requirements.append(requirement)
        
        return equipment_requirements
    
    def _analyze_labor_requirements(
        self, 
        tasks: List[PlanningTask], 
        knowledge_base: Dict[str, Any]
    ) -> List[ResourceRequirement]:
        """Analyze labor requirements for tasks."""
        labor_data = knowledge_base.get("labor_requirements", {})
        resource_constraints = knowledge_base.get("resource_constraints", {})
        labor_availability = resource_constraints.get("labor_availability", {})
        
        labor_requirements = []
        total_operator_hours = sum(task.duration_hours for task in tasks)
        
        # Calculate skilled operator requirements
        skilled_operator = labor_data.get("skilled_operator", {})
        daily_hours = skilled_operator.get("availability_hours_per_day", 8.0)
        seasonal_variation = labor_availability.get("seasonal_variation", 0.7)
        
        skilled_operators_needed = (total_operator_hours / daily_hours) / seasonal_variation
        
        if skilled_operators_needed > 0:
            requirement = ResourceRequirement(
                resource_type="labor",
                resource_name="skilled_operator",
                quantity=skilled_operators_needed,
                unit="person",
                duration_hours=total_operator_hours,
                priority=1
            )
            labor_requirements.append(requirement)
        
        return labor_requirements
    
    def _analyze_material_requirements(
        self, 
        tasks: List[PlanningTask], 
        knowledge_base: Dict[str, Any]
    ) -> List[ResourceRequirement]:
        """Analyze material requirements for tasks."""
        material_data = knowledge_base.get("material_requirements", {})
        resource_constraints = knowledge_base.get("resource_constraints", {})
        material_availability = resource_constraints.get("material_availability", {})
        
        material_requirements = []
        
        # Analyze materials based on task types
        for task in tasks:
            task_name = task.name.lower()
            
            if "semis" in task_name or "semoir" in task_name:
                # Seed requirements
                requirement = ResourceRequirement(
                    resource_type="material",
                    resource_name="seeds",
                    quantity=task.duration_hours * 10,  # Simplified calculation
                    unit="kg",
                    duration_hours=task.duration_hours,
                    priority=2
                )
                material_requirements.append(requirement)
            
            elif "fertilisation" in task_name or "épandeur" in task_name:
                # Fertilizer requirements
                requirement = ResourceRequirement(
                    resource_type="material",
                    resource_name="fertilizers",
                    quantity=task.duration_hours * 50,  # Simplified calculation
                    unit="kg",
                    duration_hours=task.duration_hours,
                    priority=2
                )
                material_requirements.append(requirement)
            
            elif "traitement" in task_name or "pulvérisateur" in task_name:
                # Pesticide requirements
                requirement = ResourceRequirement(
                    resource_type="material",
                    resource_name="pesticides",
                    quantity=task.duration_hours * 5,  # Simplified calculation
                    unit="L",
                    duration_hours=task.duration_hours,
                    priority=3
                )
                material_requirements.append(requirement)
        
        return material_requirements
    
    def _run(
        self, 
        tasks_json: str,
        analysis_type: str = "comprehensive",
        **kwargs
    ) -> str:
        """
        Analyze resource requirements for planning tasks.
        
        Args:
            tasks_json: JSON string of tasks from GeneratePlanningTasksTool
            analysis_type: Type of analysis (equipment, labor, materials, comprehensive)
        """
        try:
            # Validate inputs
            validation_errors = self._validate_inputs(tasks_json, analysis_type)
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
            
            if not tasks_data:
                return json.dumps({"error": "Aucune tâche fournie pour l'analyse des ressources"})
            
            # Convert to PlanningTask objects
            tasks = [PlanningTask(**task) for task in tasks_data]
            
            # Analyze resource requirements based on analysis type
            all_requirements = []
            
            if analysis_type in ["equipment", "comprehensive"] and config.validate_equipment_requirements:
                equipment_requirements = self._analyze_equipment_requirements(tasks, knowledge_base)
                all_requirements.extend(equipment_requirements)
            
            if analysis_type in ["labor", "comprehensive"] and config.validate_labor_requirements:
                labor_requirements = self._analyze_labor_requirements(tasks, knowledge_base)
                all_requirements.extend(labor_requirements)
            
            if analysis_type in ["materials", "comprehensive"] and config.validate_material_requirements:
                material_requirements = self._analyze_material_requirements(tasks, knowledge_base)
                all_requirements.extend(material_requirements)
            
            # Calculate summary statistics
            total_equipment_hours = sum(req.duration_hours for req in all_requirements if req.resource_type == "equipment")
            total_labor_hours = sum(req.duration_hours for req in all_requirements if req.resource_type == "labor")
            total_material_quantity = sum(req.quantity for req in all_requirements if req.resource_type == "material")
            
            result = {
                "analysis_type": analysis_type,
                "resource_requirements": [asdict(req) for req in all_requirements],
                "summary": {
                    "total_requirements": len(all_requirements),
                    "equipment_requirements": len([req for req in all_requirements if req.resource_type == "equipment"]),
                    "labor_requirements": len([req for req in all_requirements if req.resource_type == "labor"]),
                    "material_requirements": len([req for req in all_requirements if req.resource_type == "material"]),
                    "total_equipment_hours": round(total_equipment_hours, 2),
                    "total_labor_hours": round(total_labor_hours, 2),
                    "total_material_quantity": round(total_material_quantity, 2)
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
            logger.error(f"Analyze resource requirements error: {e}")
            return json.dumps({
                "error": f"Erreur lors de l'analyse des besoins en ressources: {str(e)}",
                "error_type": type(e).__name__
            })
    
    async def _arun(
        self, 
        tasks_json: str,
        analysis_type: str = "comprehensive",
        **kwargs
    ) -> str:
        """
        Asynchronous version of resource requirements analysis.
        """
        # For now, just call the sync version
        return self._run(tasks_json, analysis_type, **kwargs)
    
    def clear_cache(self):
        """Clear internal caches."""
        self._config_cache = None
        logger.info("Cleared tool caches")
