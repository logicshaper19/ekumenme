"""
Optimize Task Sequence Tool - Vector Database Ready Tool

Job: Optimize task sequence based on constraints and objectives.
Input: JSON string of tasks from GeneratePlanningTasksTool
Output: JSON string with optimized sequence

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
from ...config.task_optimization_config import get_task_optimization_config

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
class OptimizedTask:
    """Structured optimized task with sequence information."""
    name: str
    duration_hours: float
    equipment: str
    priority: int
    dependencies: List[str]
    cost_per_hectare: float
    yield_impact: float
    sequence_order: int
    start_time: float
    end_time: float
    optimization_score: float

@dataclass
class ValidationError:
    """Validation error information."""
    field: str
    message: str
    severity: str

class OptimizeTaskSequenceTool(BaseTool):
    """
    Vector Database Ready Tool: Optimize task sequence based on constraints and objectives.
    
    Job: Take planning tasks and optimize their sequence.
    Input: JSON string of tasks from GeneratePlanningTasksTool
    Output: JSON string with optimized sequence
    
    Enhanced Features:
    - External knowledge base (JSON file)
    - Configurable analysis parameters
    - Asynchronous support
    - Comprehensive input validation
    - Vector database ready architecture
    """
    
    name: str = "optimize_task_sequence_tool"
    description: str = "Optimise la séquence des tâches avec analyse avancée"
    
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
        return str(current_dir.parent.parent / "data" / "task_optimization_knowledge.json")
    
    def _get_config(self):
        """Get current configuration."""
        if self._config_cache is None:
            self._config_cache = get_task_optimization_config()
        return self._config_cache
    
    def _load_knowledge_base(self) -> Dict[str, Any]:
        """Load knowledge base from JSON file."""
        try:
            with open(self.knowledge_base_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading task optimization knowledge base: {e}")
            return {}
    
    def _validate_inputs(
        self, 
        tasks_json: str, 
        optimization_objective: str
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
        
        # Validate optimization objective
        if config.require_optimization_objective and not optimization_objective:
            errors.append(ValidationError("optimization_objective", "Optimization objective is required", "error"))
        
        return errors
    
    def _optimize_task_sequence(
        self, 
        tasks: List[Dict[str, Any]], 
        optimization_objective: str,
        knowledge_base: Dict[str, Any]
    ) -> List[OptimizedTask]:
        """Optimize task sequence using greedy algorithm."""
        optimization_weights = knowledge_base.get("optimization_weights", {})
        equipment_constraints = knowledge_base.get("equipment_constraints", {})
        
        # Convert to PlanningTask objects
        planning_tasks = [PlanningTask(**task) for task in tasks]
        
        # Sort tasks by priority and dependencies
        optimized_tasks = []
        completed_tasks = set()
        current_time = 0.0
        
        # Create a copy of tasks to work with
        remaining_tasks = planning_tasks.copy()
        
        while remaining_tasks:
            # Find tasks that can be executed (dependencies satisfied)
            available_tasks = []
            for task in remaining_tasks:
                if all(dep in completed_tasks for dep in task.dependencies):
                    available_tasks.append(task)
            
            if not available_tasks:
                # If no tasks can be executed, break to avoid infinite loop
                break
            
            # Select best task based on optimization objective
            best_task = self._select_best_task(available_tasks, optimization_objective, optimization_weights)
            
            # Calculate timing
            equipment = best_task.equipment
            setup_time = equipment_constraints.get(equipment, {}).get("setup_time_hours", 0.0)
            
            optimized_task = OptimizedTask(
                name=best_task.name,
                duration_hours=best_task.duration_hours,
                equipment=best_task.equipment,
                priority=best_task.priority,
                dependencies=best_task.dependencies,
                cost_per_hectare=best_task.cost_per_hectare,
                yield_impact=best_task.yield_impact,
                sequence_order=len(optimized_tasks) + 1,
                start_time=current_time,
                end_time=current_time + best_task.duration_hours + setup_time,
                optimization_score=self._calculate_optimization_score(best_task, optimization_objective, optimization_weights)
            )
            
            optimized_tasks.append(optimized_task)
            completed_tasks.add(best_task.name)
            remaining_tasks.remove(best_task)
            current_time = optimized_task.end_time
        
        return optimized_tasks
    
    def _select_best_task(
        self, 
        available_tasks: List[PlanningTask], 
        optimization_objective: str,
        optimization_weights: Dict[str, float]
    ) -> PlanningTask:
        """Select the best task based on optimization objective."""
        if optimization_objective == "minimize_cost":
            return min(available_tasks, key=lambda t: t.cost_per_hectare)
        elif optimization_objective == "minimize_time":
            return min(available_tasks, key=lambda t: t.duration_hours)
        elif optimization_objective == "maximize_yield":
            return max(available_tasks, key=lambda t: t.yield_impact)
        else:
            # Default: balanced optimization
            return max(available_tasks, key=lambda t: self._calculate_optimization_score(t, optimization_objective, optimization_weights))
    
    def _calculate_optimization_score(
        self, 
        task: PlanningTask, 
        optimization_objective: str,
        optimization_weights: Dict[str, float]
    ) -> float:
        """Calculate optimization score for a task."""
        cost_weight = optimization_weights.get("cost", 0.3)
        time_weight = optimization_weights.get("time", 0.25)
        yield_weight = optimization_weights.get("yield", 0.25)
        equipment_weight = optimization_weights.get("equipment_efficiency", 0.2)
        
        # Normalize scores (lower is better for cost and time)
        cost_score = 1.0 / (1.0 + task.cost_per_hectare / 100.0)
        time_score = 1.0 / (1.0 + task.duration_hours / 10.0)
        yield_score = task.yield_impact
        equipment_score = 1.0 / (1.0 + task.priority / 5.0)  # Lower priority = better equipment efficiency
        
        return (cost_weight * cost_score + 
                time_weight * time_score + 
                yield_weight * yield_score + 
                equipment_weight * equipment_score)
    
    def _run(
        self, 
        tasks_json: str,
        optimization_objective: str = "balanced",
        **kwargs
    ) -> str:
        """
        Optimize task sequence based on constraints and objectives.
        
        Args:
            tasks_json: JSON string of tasks from GeneratePlanningTasksTool
            optimization_objective: Optimization objective (minimize_cost, minimize_time, maximize_yield, balanced)
        """
        try:
            # Validate inputs
            validation_errors = self._validate_inputs(tasks_json, optimization_objective)
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
            
            tasks = data.get("tasks", [])
            if not tasks:
                return json.dumps({"error": "Aucune tâche fournie pour l'optimisation"})
            
            # Optimize task sequence
            optimized_tasks = self._optimize_task_sequence(tasks, optimization_objective, knowledge_base)
            
            # Calculate optimization metrics
            total_duration = sum(task.end_time for task in optimized_tasks)
            total_cost = sum(task.cost_per_hectare for task in optimized_tasks)
            total_yield_impact = sum(task.yield_impact for task in optimized_tasks)
            avg_optimization_score = sum(task.optimization_score for task in optimized_tasks) / len(optimized_tasks)
            
            result = {
                "optimization_objective": optimization_objective,
                "optimized_tasks": [asdict(task) for task in optimized_tasks],
                "optimization_metrics": {
                    "total_duration_hours": round(total_duration, 2),
                    "total_cost_eur": round(total_cost, 2),
                    "total_yield_impact": round(total_yield_impact, 2),
                    "average_optimization_score": round(avg_optimization_score, 2),
                    "tasks_optimized": len(optimized_tasks)
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
            logger.error(f"Optimize task sequence error: {e}")
            return json.dumps({
                "error": f"Erreur lors de l'optimisation de la séquence des tâches: {str(e)}",
                "error_type": type(e).__name__
            })
    
    async def _arun(
        self, 
        tasks_json: str,
        optimization_objective: str = "balanced",
        **kwargs
    ) -> str:
        """
        Asynchronous version of task sequence optimization.
        """
        # For now, just call the sync version
        return self._run(tasks_json, optimization_objective, **kwargs)
    
    def clear_cache(self):
        """Clear internal caches."""
        self._config_cache = None
        logger.info("Cleared tool caches")
