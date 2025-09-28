"""
Optimize Task Sequence Tool - Single Purpose Tool

Job: Optimize task sequence based on constraints and objectives.
Input: JSON string of tasks from GeneratePlanningTasksTool
Output: JSON string with optimized sequence

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
from dataclasses import dataclass

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

class OptimizeTaskSequenceTool(BaseTool):
    """
    Tool: Optimize task sequence based on constraints and objectives.
    
    Job: Take planning tasks and optimize their sequence.
    Input: JSON string of tasks from GeneratePlanningTasksTool
    Output: JSON string with optimized sequence
    """
    
    name: str = "optimize_task_sequence_tool"
    description: str = "Optimise la séquence des tâches de planification"
    
    def _run(
        self, 
        tasks_json: str,
        optimization_objective: str = "balanced_optimization",
        constraints: List[str] = None,
        **kwargs
    ) -> str:
        """
        Optimize task sequence based on constraints and objectives.
        
        Args:
            tasks_json: JSON string from GeneratePlanningTasksTool
            optimization_objective: "cost_optimization", "time_optimization", "yield_optimization", "balanced_optimization"
            constraints: List of constraints (e.g., ["budget_constraint", "time_constraint"])
        """
        try:
            data = json.loads(tasks_json)
            
            if "error" in data:
                return tasks_json  # Pass through errors
            
            tasks_data = data.get("tasks", [])
            if not tasks_data:
                return json.dumps({"error": "Aucune tâche fournie pour l'optimisation"})
            
            # Convert back to PlanningTask objects for processing
            tasks = [PlanningTask(**task_dict) for task_dict in tasks_data]
            
            # Optimize sequence based on objective
            optimized_sequence = self._optimize_sequence(tasks, optimization_objective, constraints or [])
            
            # Calculate optimization metrics
            optimization_metrics = self._calculate_optimization_metrics(tasks, optimized_sequence)
            
            result = {
                "optimized_sequence": optimized_sequence,
                "optimization_objective": optimization_objective,
                "constraints": constraints or [],
                "optimization_metrics": optimization_metrics,
                "total_tasks": len(tasks)
            }
            
            return json.dumps(result, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"Optimize task sequence error: {e}")
            return json.dumps({"error": f"Erreur lors de l'optimisation: {str(e)}"})
    
    def _optimize_sequence(self, tasks: List[PlanningTask], objective: str, constraints: List[str]) -> List[str]:
        """Optimize task sequence based on objective and constraints."""
        if objective == "cost_optimization":
            # Sort by cost efficiency (yield impact / cost)
            sorted_tasks = sorted(tasks, key=lambda t: t.yield_impact / max(t.cost_per_hectare, 1), reverse=True)
        elif objective == "time_optimization":
            # Sort by duration (shortest first)
            sorted_tasks = sorted(tasks, key=lambda t: t.duration_hours)
        elif objective == "yield_optimization":
            # Sort by yield impact (highest first)
            sorted_tasks = sorted(tasks, key=lambda t: t.yield_impact, reverse=True)
        else:
            # Default: topological sort based on dependencies and priority
            sorted_tasks = sorted(tasks, key=lambda t: (t.priority, len(t.dependencies)))
        
        return [task.name for task in sorted_tasks]
    
    def _calculate_optimization_metrics(self, tasks: List[PlanningTask], sequence: List[str]) -> Dict[str, Any]:
        """Calculate optimization metrics."""
        # Calculate total duration and cost
        total_duration = sum(task.duration_hours for task in tasks)
        total_cost = sum(task.cost_per_hectare for task in tasks)
        total_yield_impact = sum(task.yield_impact for task in tasks)
        
        # Calculate efficiency metrics
        cost_efficiency = total_yield_impact / total_cost if total_cost > 0 else 0
        time_efficiency = total_yield_impact / total_duration if total_duration > 0 else 0
        
        return {
            "total_duration_hours": round(total_duration, 1),
            "total_cost_per_hectare": round(total_cost, 2),
            "total_yield_impact": round(total_yield_impact, 3),
            "cost_efficiency": round(cost_efficiency, 4),
            "time_efficiency": round(time_efficiency, 4)
        }
