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
    description: str = "Génère les tâches de planification pour les cultures spécifiées"
    
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
        """Get standard tasks for a specific crop."""
        # Crop-specific task definitions with economic data
        crop_task_templates = {
            "blé": [
                ("Préparation sol", 2.0, "tracteur_120cv", 1, [], 45.0, 0.05),
                ("Semis", 3.0, "tracteur_120cv", 2, ["Préparation sol"], 85.0, 0.12),
                ("Fertilisation", 1.5, "tracteur_80cv", 3, ["Semis"], 280.0, 0.15),
                ("Protection phytosanitaire", 1.0, "tracteur_80cv", 4, ["Fertilisation"], 120.0, 0.08),
                ("Récolte", 4.0, "moissonneuse", 5, ["Protection phytosanitaire"], 80.0, 0.0)
            ],
            "maïs": [
                ("Préparation sol", 2.5, "tracteur_120cv", 1, [], 50.0, 0.05),
                ("Semis", 2.0, "tracteur_120cv", 2, ["Préparation sol"], 220.0, 0.12),
                ("Fertilisation", 1.0, "tracteur_80cv", 3, ["Semis"], 350.0, 0.20),
                ("Désherbage", 1.5, "tracteur_80cv", 4, ["Fertilisation"], 150.0, 0.10),
                ("Récolte", 5.0, "moissonneuse", 5, ["Désherbage"], 100.0, 0.0)
            ],
            "colza": [
                ("Préparation sol", 2.0, "tracteur_120cv", 1, [], 45.0, 0.05),
                ("Semis", 2.5, "tracteur_120cv", 2, ["Préparation sol"], 65.0, 0.15),
                ("Fertilisation", 1.0, "tracteur_80cv", 3, ["Semis"], 320.0, 0.18),
                ("Protection phytosanitaire", 1.5, "tracteur_80cv", 4, ["Fertilisation"], 180.0, 0.12),
                ("Récolte", 3.5, "moissonneuse", 5, ["Protection phytosanitaire"], 90.0, 0.0)
            ]
        }
        
        tasks = []
        task_templates = crop_task_templates.get(crop, crop_task_templates["blé"])
        
        for name, duration, equipment, priority, deps, cost, yield_impact in task_templates:
            task = PlanningTask(
                name=f"{name} - {crop}",
                duration_hours=duration,
                equipment=equipment,
                priority=priority,
                dependencies=deps,
                cost_per_hectare=cost,
                yield_impact=yield_impact
            )
            tasks.append(task)
        
        return tasks
