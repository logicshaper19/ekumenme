"""
Generate Planning Report Tool - Single Purpose Tool

Job: Generate structured planning reports from analysis results.
Input: JSON strings from other planning tools
Output: JSON string with comprehensive planning report

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
from datetime import datetime

logger = logging.getLogger(__name__)

class GeneratePlanningReportTool(BaseTool):
    """
    Tool: Generate structured planning reports from analysis results.
    
    Job: Take results from other planning tools and generate comprehensive report.
    Input: JSON strings from other planning tools
    Output: JSON string with comprehensive planning report
    """
    
    name: str = "generate_planning_report_tool"
    description: str = "Génère un rapport de planification structuré"
    
    def _run(
        self, 
        tasks_json: str,
        sequence_json: str = None,
        costs_json: str = None,
        resources_json: str = None,
        **kwargs
    ) -> str:
        """
        Generate structured planning report from analysis results.
        
        Args:
            tasks_json: JSON string from GeneratePlanningTasksTool
            sequence_json: JSON string from OptimizeTaskSequenceTool (optional)
            costs_json: JSON string from CalculatePlanningCostsTool (optional)
            resources_json: JSON string from AnalyzeResourceRequirementsTool (optional)
        """
        try:
            # Parse input data
            tasks_data = json.loads(tasks_json)
            sequence_data = json.loads(sequence_json) if sequence_json else None
            costs_data = json.loads(costs_json) if costs_json else None
            resources_data = json.loads(resources_json) if resources_json else None
            
            # Generate comprehensive report
            report = self._generate_comprehensive_report(tasks_data, sequence_data, costs_data, resources_data)
            
            return json.dumps(report, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"Generate planning report error: {e}")
            return json.dumps({"error": f"Erreur lors de la génération du rapport: {str(e)}"})
    
    def _generate_comprehensive_report(self, tasks_data: Dict, sequence_data: Dict = None, costs_data: Dict = None, resources_data: Dict = None) -> Dict[str, Any]:
        """Generate comprehensive planning report."""
        report = {
            "report_metadata": {
                "generated_at": datetime.now().isoformat(),
                "report_type": "planning_analysis",
                "version": "1.0"
            },
            "executive_summary": self._generate_executive_summary(tasks_data, sequence_data, costs_data, resources_data),
            "task_analysis": self._extract_task_analysis(tasks_data),
            "sequence_analysis": self._extract_sequence_analysis(sequence_data) if sequence_data else None,
            "cost_analysis": self._extract_cost_analysis(costs_data) if costs_data else None,
            "resource_analysis": self._extract_resource_analysis(resources_data) if resources_data else None,
            "recommendations": self._generate_recommendations(tasks_data, sequence_data, costs_data, resources_data)
        }
        
        return report
    
    def _generate_executive_summary(self, tasks_data: Dict, sequence_data: Dict = None, costs_data: Dict = None, resources_data: Dict = None) -> Dict[str, Any]:
        """Generate executive summary."""
        summary = {
            "total_tasks": tasks_data.get("total_tasks", 0),
            "crops_planned": tasks_data.get("crops_planned", []),
            "surface_ha": tasks_data.get("surface_ha", 0)
        }
        
        if costs_data:
            summary["total_cost_per_hectare"] = costs_data.get("cost_analysis", {}).get("total_cost_per_hectare", 0)
            summary["roi_percent"] = costs_data.get("economic_impact", {}).get("roi_percent", 0)
        
        if resources_data:
            summary["total_duration_hours"] = resources_data.get("resource_analysis", {}).get("total_duration_hours", 0)
            summary["estimated_weeks"] = resources_data.get("resource_analysis", {}).get("labor_requirements", {}).get("estimated_weeks", 0)
        
        return summary
    
    def _extract_task_analysis(self, tasks_data: Dict) -> Dict[str, Any]:
        """Extract task analysis from tasks data."""
        tasks = tasks_data.get("tasks", [])
        
        # Analyze tasks by category
        tasks_by_category = {}
        for task in tasks:
            task_name = task.get("name", "").lower()
            if "préparation" in task_name:
                category = "préparation"
            elif "semis" in task_name:
                category = "semis"
            elif "fertilisation" in task_name:
                category = "fertilisation"
            elif "protection" in task_name or "désherbage" in task_name:
                category = "protection"
            elif "récolte" in task_name:
                category = "récolte"
            else:
                category = "autre"
            
            if category not in tasks_by_category:
                tasks_by_category[category] = []
            tasks_by_category[category].append(task)
        
        return {
            "tasks_by_category": tasks_by_category,
            "total_tasks": len(tasks)
        }
    
    def _extract_sequence_analysis(self, sequence_data: Dict) -> Dict[str, Any]:
        """Extract sequence analysis from sequence data."""
        return {
            "optimized_sequence": sequence_data.get("optimized_sequence", []),
            "optimization_objective": sequence_data.get("optimization_objective", ""),
            "optimization_metrics": sequence_data.get("optimization_metrics", {})
        }
    
    def _extract_cost_analysis(self, costs_data: Dict) -> Dict[str, Any]:
        """Extract cost analysis from costs data."""
        return {
            "cost_analysis": costs_data.get("cost_analysis", {}),
            "economic_impact": costs_data.get("economic_impact", {}),
            "cost_insights": costs_data.get("cost_insights", [])
        }
    
    def _extract_resource_analysis(self, resources_data: Dict) -> Dict[str, Any]:
        """Extract resource analysis from resources data."""
        return {
            "resource_analysis": resources_data.get("resource_analysis", {}),
            "resource_utilization": resources_data.get("resource_utilization", {}),
            "resource_insights": resources_data.get("resource_insights", [])
        }
    
    def _generate_recommendations(self, tasks_data: Dict, sequence_data: Dict = None, costs_data: Dict = None, resources_data: Dict = None) -> List[str]:
        """Generate recommendations based on analysis."""
        recommendations = []
        
        # Task recommendations
        total_tasks = tasks_data.get("total_tasks", 0)
        if total_tasks > 10:
            recommendations.append("Considérer la simplification des tâches pour réduire la complexité")
        elif total_tasks < 5:
            recommendations.append("Vérifier que toutes les tâches nécessaires sont incluses")
        
        # Cost recommendations
        if costs_data:
            roi = costs_data.get("economic_impact", {}).get("roi_percent", 0)
            if roi < 10:
                recommendations.append("Optimiser les coûts pour améliorer la rentabilité")
            elif roi > 20:
                recommendations.append("Excellent ROI - Considérer l'augmentation de la surface")
        
        # Resource recommendations
        if resources_data:
            bottlenecks = resources_data.get("resource_utilization", {}).get("bottlenecks", [])
            if bottlenecks:
                recommendations.append(f"Résoudre les goulots d'étranglement: {', '.join(bottlenecks)}")
        
        # Sequence recommendations
        if sequence_data:
            objective = sequence_data.get("optimization_objective", "")
            if objective != "balanced_optimization":
                recommendations.append(f"Considérer l'optimisation équilibrée pour de meilleurs résultats")
        
        return recommendations
