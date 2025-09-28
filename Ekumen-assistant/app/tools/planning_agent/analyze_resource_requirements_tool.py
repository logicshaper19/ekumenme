"""
Analyze Resource Requirements Tool - Single Purpose Tool

Job: Analyze resource requirements for planning tasks.
Input: JSON string of tasks from GeneratePlanningTasksTool
Output: JSON string with resource analysis

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

class AnalyzeResourceRequirementsTool(BaseTool):
    """
    Tool: Analyze resource requirements for planning tasks.
    
    Job: Take planning tasks and analyze resource requirements.
    Input: JSON string of tasks from GeneratePlanningTasksTool
    Output: JSON string with resource analysis
    """
    
    name: str = "analyze_resource_requirements_tool"
    description: str = "Analyse les besoins en ressources pour les tâches de planification"
    
    def _run(
        self, 
        tasks_json: str,
        surface_ha: float,
        **kwargs
    ) -> str:
        """
        Analyze resource requirements for planning tasks.
        
        Args:
            tasks_json: JSON string from GeneratePlanningTasksTool
            surface_ha: Surface area in hectares
        """
        try:
            data = json.loads(tasks_json)
            
            if "error" in data:
                return tasks_json  # Pass through errors
            
            tasks_data = data.get("tasks", [])
            if not tasks_data:
                return json.dumps({"error": "Aucune tâche fournie pour l'analyse des ressources"})
            
            # Convert back to PlanningTask objects for processing
            tasks = [PlanningTask(**task_dict) for task_dict in tasks_data]
            
            # Analyze resource requirements
            resource_analysis = self._analyze_resource_requirements(tasks, surface_ha)
            
            # Calculate resource utilization
            resource_utilization = self._calculate_resource_utilization(tasks)
            
            # Generate resource insights
            resource_insights = self._generate_resource_insights(resource_analysis, resource_utilization)
            
            result = {
                "surface_ha": surface_ha,
                "resource_analysis": resource_analysis,
                "resource_utilization": resource_utilization,
                "resource_insights": resource_insights,
                "total_tasks": len(tasks)
            }
            
            return json.dumps(result, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"Analyze resource requirements error: {e}")
            return json.dumps({"error": f"Erreur lors de l'analyse des ressources: {str(e)}"})
    
    def _analyze_resource_requirements(self, tasks: List[PlanningTask], surface_ha: float) -> Dict[str, Any]:
        """Analyze resource requirements for tasks."""
        # Calculate total time requirements
        total_duration_hours = sum(task.duration_hours for task in tasks)
        total_duration_days = total_duration_hours / 8  # Assuming 8 hours per day
        
        # Analyze equipment requirements
        equipment_usage = {}
        for task in tasks:
            if task.equipment not in equipment_usage:
                equipment_usage[task.equipment] = {
                    "total_hours": 0,
                    "tasks": [],
                    "utilization_percent": 0
                }
            equipment_usage[task.equipment]["total_hours"] += task.duration_hours
            equipment_usage[task.equipment]["tasks"].append(task.name)
        
        # Calculate equipment utilization
        for equipment, usage in equipment_usage.items():
            # Assume equipment is available 8 hours per day, 5 days per week
            max_available_hours = 8 * 5 * 4  # 4 weeks
            usage["utilization_percent"] = (usage["total_hours"] / max_available_hours) * 100
        
        # Analyze labor requirements
        labor_requirements = {
            "total_hours": total_duration_hours,
            "estimated_days": round(total_duration_days, 1),
            "estimated_weeks": round(total_duration_days / 5, 1)
        }
        
        return {
            "labor_requirements": labor_requirements,
            "equipment_usage": equipment_usage,
            "total_duration_hours": round(total_duration_hours, 1)
        }
    
    def _calculate_resource_utilization(self, tasks: List[PlanningTask]) -> Dict[str, Any]:
        """Calculate resource utilization metrics."""
        # Calculate equipment utilization
        equipment_hours = {}
        for task in tasks:
            if task.equipment not in equipment_hours:
                equipment_hours[task.equipment] = 0
            equipment_hours[task.equipment] += task.duration_hours
        
        # Calculate utilization efficiency
        total_hours = sum(equipment_hours.values())
        equipment_count = len(equipment_hours)
        average_utilization = total_hours / equipment_count if equipment_count > 0 else 0
        
        # Identify bottlenecks
        bottlenecks = []
        for equipment, hours in equipment_hours.items():
            if hours > 40:  # More than 5 days of work
                bottlenecks.append(equipment)
        
        return {
            "equipment_hours": equipment_hours,
            "average_utilization_hours": round(average_utilization, 1),
            "bottlenecks": bottlenecks,
            "total_equipment_types": equipment_count
        }
    
    def _generate_resource_insights(self, resource_analysis: Dict[str, Any], resource_utilization: Dict[str, Any]) -> List[str]:
        """Generate resource insights."""
        insights = []
        
        # Labor insights
        labor_req = resource_analysis["labor_requirements"]
        if labor_req["estimated_weeks"] > 4:
            insights.append("⏰ Durée importante - Planification sur plusieurs semaines")
        elif labor_req["estimated_weeks"] > 2:
            insights.append("⏰ Durée modérée - Planification sur 2-4 semaines")
        else:
            insights.append("⏰ Durée courte - Planification sur 1-2 semaines")
        
        # Equipment insights
        equipment_usage = resource_analysis["equipment_usage"]
        for equipment, usage in equipment_usage.items():
            if usage["utilization_percent"] > 80:
                insights.append(f"🚜 {equipment}: Utilisation élevée ({usage['utilization_percent']:.0f}%)")
            elif usage["utilization_percent"] > 50:
                insights.append(f"🚜 {equipment}: Utilisation modérée ({usage['utilization_percent']:.0f}%)")
            else:
                insights.append(f"🚜 {equipment}: Utilisation faible ({usage['utilization_percent']:.0f}%)")
        
        # Bottleneck insights
        bottlenecks = resource_utilization["bottlenecks"]
        if bottlenecks:
            insights.append(f"⚠️ Goulots d'étranglement identifiés: {', '.join(bottlenecks)}")
        else:
            insights.append("✅ Aucun goulot d'étranglement identifié")
        
        return insights
