"""
Generate Planning Tasks Tool - Single Purpose Tool

Job: Generate planning tasks for specific crops and surface area.
Input: crops, surface, planning_objective
Output: JSON string of PlanningTask objects

This tool does ONLY:
- Execute specific, well-defined function
- Take structured inputs, return structured outputs
- Contain domain-specific business logic
- Be stateless and reusable

No prompting logic, no orchestration, no agent responsibilities.
"""

from typing import Dict, List, Any, Optional
from langchain.tools import BaseTool
import logging
import json
import os
from dataclasses import dataclass, asdict

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

class GeneratePlanningTasksTool(BaseTool):
    """
    Tool: Generate planning tasks for specific crops and surface area.
    
    Job: Generate standard agricultural tasks for given crops and surface.
    Input: crops, surface, planning_objective
    Output: JSON string of PlanningTask objects
    """
    
    name: str = "generate_planning_tasks_tool"
    description: str = "Génère les tâches de planification pour les cultures spécifiées à partir de la configuration"

    @property
    def config(self):
        """Load planning tasks configuration."""
        if not hasattr(self, '_config'):
            config_path = os.path.join(os.path.dirname(__file__), '..', '..', 'config', 'planning_tasks_config.json')
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load planning tasks config: {e}")
                self._config = self._get_fallback_config()
        return self._config
    
    def _run(
        self, 
        crops: List[str],
        surface: float,
        planning_objective: str = "balanced_optimization",
        **kwargs
    ) -> str:
        """
        Generate planning tasks for crops and surface area.
        
        Args:
            crops: List of crop names (e.g., ["blé", "maïs"])
            surface: Surface area in hectares
            planning_objective: "cost_optimization", "time_optimization", "yield_optimization", "balanced_optimization"
        """
        try:
            tasks = []
            
            for crop in crops:
                crop_tasks = self._get_standard_crop_tasks(crop, surface, planning_objective)
                tasks.extend(crop_tasks)
            
            # Convert to JSON-serializable format
            tasks_as_dicts = [asdict(task) for task in tasks]
            
            return json.dumps({
                "tasks": tasks_as_dicts,
                "total_tasks": len(tasks),
                "crops_planned": crops,
                "surface_ha": surface,
                "planning_objective": planning_objective
            }, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"Generate planning tasks error: {e}")
            return json.dumps({"error": f"Erreur lors de la génération des tâches: {str(e)}"})
    
    def _get_standard_crop_tasks(self, crop: str, surface: float, objective: str) -> List[PlanningTask]:
        """Get standard tasks for a specific crop from configuration."""
        tasks = []

        # Get task templates from configuration
        task_templates = self.config.get("task_templates", {})
        crop_config = task_templates.get(crop, task_templates.get("blé", {}))

        if not crop_config:
            logger.warning(f"No task templates found for crop: {crop}, using fallback")
            return self._get_fallback_tasks(crop, surface, objective)

        crop_tasks = crop_config.get("tasks", [])

        for task_config in crop_tasks:
            task = PlanningTask(
                name=f"{task_config['name']} - {crop}",
                duration_hours=task_config["duration_hours"],
                equipment=task_config["equipment"],
                priority=task_config["priority"],
                dependencies=task_config["dependencies"],
                cost_per_hectare=task_config["cost_per_hectare"],
                yield_impact=task_config["yield_impact"]
            )
            tasks.append(task)

        return tasks

    def _get_fallback_config(self) -> Dict[str, Any]:
        """Fallback configuration if config file cannot be loaded."""
        return {
            "task_templates": {
                "blé": {
                    "tasks": [
                        {
                            "name": "Préparation sol",
                            "duration_hours": 2.0,
                            "equipment": "tracteur_120cv",
                            "priority": 1,
                            "dependencies": [],
                            "cost_per_hectare": 45.0,
                            "yield_impact": 0.05
                        },
                        {
                            "name": "Semis",
                            "duration_hours": 3.0,
                            "equipment": "tracteur_120cv",
                            "priority": 2,
                            "dependencies": ["Préparation sol"],
                            "cost_per_hectare": 85.0,
                            "yield_impact": 0.12
                        },
                        {
                            "name": "Récolte",
                            "duration_hours": 4.0,
                            "equipment": "moissonneuse",
                            "priority": 5,
                            "dependencies": ["Semis"],
                            "cost_per_hectare": 80.0,
                            "yield_impact": 0.0
                        }
                    ]
                }
            }
        }

    def _get_fallback_tasks(self, crop: str, surface: float, objective: str) -> List[PlanningTask]:
        """Get fallback tasks when configuration is not available."""
        fallback_config = self._get_fallback_config()
        crop_config = fallback_config["task_templates"]["blé"]

        tasks = []
        for task_config in crop_config["tasks"]:
            task = PlanningTask(
                name=f"{task_config['name']} - {crop}",
                duration_hours=task_config["duration_hours"],
                equipment=task_config["equipment"],
                priority=task_config["priority"],
                dependencies=task_config["dependencies"],
                cost_per_hectare=task_config["cost_per_hectare"],
                yield_impact=task_config["yield_impact"]
            )
            tasks.append(task)

        return tasks
