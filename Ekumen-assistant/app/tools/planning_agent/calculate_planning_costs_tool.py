"""
Calculate Planning Costs Tool - Single Purpose Tool

Job: Calculate costs and economic impact of planning tasks.
Input: JSON string of tasks from GeneratePlanningTasksTool
Output: JSON string with cost analysis

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

class CalculatePlanningCostsTool(BaseTool):
    """
    Tool: Calculate costs and economic impact of planning tasks.
    
    Job: Take planning tasks and calculate detailed cost analysis.
    Input: JSON string of tasks from GeneratePlanningTasksTool
    Output: JSON string with cost analysis
    """
    
    name: str = "calculate_planning_costs_tool"
    description: str = "Calcule les coûts et l'impact économique des tâches de planification"
    
    def _run(
        self, 
        tasks_json: str,
        surface_ha: float,
        **kwargs
    ) -> str:
        """
        Calculate costs and economic impact of planning tasks.
        
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
                return json.dumps({"error": "Aucune tâche fournie pour le calcul des coûts"})
            
            # Convert back to PlanningTask objects for processing
            tasks = [PlanningTask(**task_dict) for task_dict in tasks_data]
            
            # Calculate costs
            cost_analysis = self._calculate_cost_analysis(tasks, surface_ha)
            
            # Calculate economic impact
            economic_impact = self._calculate_economic_impact(tasks, surface_ha)
            
            # Generate cost insights
            cost_insights = self._generate_cost_insights(cost_analysis, economic_impact)
            
            result = {
                "surface_ha": surface_ha,
                "cost_analysis": cost_analysis,
                "economic_impact": economic_impact,
                "cost_insights": cost_insights,
                "total_tasks": len(tasks)
            }
            
            return json.dumps(result, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"Calculate planning costs error: {e}")
            return json.dumps({"error": f"Erreur lors du calcul des coûts: {str(e)}"})
    
    def _calculate_cost_analysis(self, tasks: List[PlanningTask], surface_ha: float) -> Dict[str, Any]:
        """Calculate detailed cost analysis."""
        # Calculate total costs
        total_cost_per_hectare = sum(task.cost_per_hectare for task in tasks)
        total_cost = total_cost_per_hectare * surface_ha
        
        # Calculate costs by category
        costs_by_category = {
            "préparation": 0,
            "semis": 0,
            "fertilisation": 0,
            "protection": 0,
            "récolte": 0
        }
        
        for task in tasks:
            task_name_lower = task.name.lower()
            if "préparation" in task_name_lower:
                costs_by_category["préparation"] += task.cost_per_hectare
            elif "semis" in task_name_lower:
                costs_by_category["semis"] += task.cost_per_hectare
            elif "fertilisation" in task_name_lower:
                costs_by_category["fertilisation"] += task.cost_per_hectare
            elif "protection" in task_name_lower or "désherbage" in task_name_lower:
                costs_by_category["protection"] += task.cost_per_hectare
            elif "récolte" in task_name_lower:
                costs_by_category["récolte"] += task.cost_per_hectare
        
        # Calculate costs by equipment
        costs_by_equipment = {}
        for task in tasks:
            if task.equipment not in costs_by_equipment:
                costs_by_equipment[task.equipment] = 0
            costs_by_equipment[task.equipment] += task.cost_per_hectare
        
        return {
            "total_cost_per_hectare": round(total_cost_per_hectare, 2),
            "total_cost": round(total_cost, 2),
            "costs_by_category": {k: round(v, 2) for k, v in costs_by_category.items()},
            "costs_by_equipment": {k: round(v, 2) for k, v in costs_by_equipment.items()}
        }
    
    def _calculate_economic_impact(self, tasks: List[PlanningTask], surface_ha: float) -> Dict[str, Any]:
        """Calculate economic impact of planning tasks."""
        # Calculate total yield impact
        total_yield_impact = sum(task.yield_impact for task in tasks)
        
        # Estimate yield increase (assuming base yield of 70 q/ha)
        base_yield = 70.0  # q/ha
        estimated_yield_increase = base_yield * total_yield_impact
        
        # Calculate economic value (assuming grain price of 200€/q)
        grain_price = 200.0  # €/q
        economic_value = estimated_yield_increase * grain_price * surface_ha
        
        # Calculate ROI
        total_cost = sum(task.cost_per_hectare for task in tasks) * surface_ha
        roi = (economic_value - total_cost) / total_cost * 100 if total_cost > 0 else 0
        
        return {
            "total_yield_impact": round(total_yield_impact, 3),
            "estimated_yield_increase_q_ha": round(estimated_yield_increase, 1),
            "economic_value_eur": round(economic_value, 2),
            "roi_percent": round(roi, 1)
        }
    
    def _generate_cost_insights(self, cost_analysis: Dict[str, Any], economic_impact: Dict[str, Any]) -> List[str]:
        """Generate cost insights."""
        insights = []
        
        total_cost = cost_analysis["total_cost_per_hectare"]
        roi = economic_impact["roi_percent"]
        
        # Cost level insights
        if total_cost > 800:
            insights.append("💰 Coûts élevés - Optimisation recommandée")
        elif total_cost > 600:
            insights.append("💰 Coûts modérés - Surveillance nécessaire")
        else:
            insights.append("💰 Coûts raisonnables - Bon équilibre")
        
        # ROI insights
        if roi > 20:
            insights.append("📈 Excellent ROI - Investissement rentable")
        elif roi > 10:
            insights.append("📈 Bon ROI - Investissement acceptable")
        elif roi > 0:
            insights.append("📈 ROI positif - Investissement marginal")
        else:
            insights.append("📉 ROI négatif - Révision nécessaire")
        
        # Category insights
        costs_by_category = cost_analysis["costs_by_category"]
        highest_cost_category = max(costs_by_category.items(), key=lambda x: x[1])
        insights.append(f"🔍 Coût principal: {highest_cost_category[0]} ({highest_cost_category[1]}€/ha)")
        
        return insights
