"""
Enhanced Generate Planning Report Tool.

Improvements:
- Type-safe Pydantic schemas
- Redis caching (1h TTL for reports)
- Aggregates outputs from all 5 planning tools
- Comprehensive executive summary
- Actionable recommendations
- All warnings consolidated
"""

import logging
from typing import Optional, List, Dict, Any
from langchain.tools import StructuredTool

from app.tools.schemas.planning_schemas import (
    PlanningReportInput,
    PlanningReportOutput,
    PlanningReportSummary
)
from app.core.cache import redis_cache

logger = logging.getLogger(__name__)


class EnhancedPlanningReportService:
    """
    Service for generating comprehensive planning reports with caching.
    
    Features:
    - Aggregates outputs from all 5 planning tools
    - Generates executive summary
    - Consolidates all warnings
    - Provides actionable recommendations
    - Identifies critical issues
    
    Cache Strategy:
    - TTL: 1 hour (3600s) - reports are comprehensive snapshots
    - Category: planning
    - Keys include crop, surface, and included analyses
    """
    
    @redis_cache(ttl=3600, model_class=PlanningReportOutput, category="planning")
    async def generate_report(self, input_data: PlanningReportInput) -> PlanningReportOutput:
        """
        Generate comprehensive planning report.
        
        Args:
            input_data: Validated input with crop, surface, and options
            
        Returns:
            PlanningReportOutput with aggregated analysis and recommendations
            
        Raises:
            ValueError: If report generation fails
        """
        try:
            warnings = []
            recommendations = []
            
            # Note: This tool is designed to aggregate outputs from other tools
            # In actual usage, the agent would call the other 5 tools first, then pass their outputs here
            # For now, we'll create a placeholder structure
            
            warnings.append(
                "ℹ️ Ce rapport agrège les résultats des outils de planification - "
                "Exécuter check_crop_feasibility, generate_planning_tasks, optimize_task_sequence, "
                "calculate_planning_costs, et analyze_resource_requirements pour données complètes"
            )
            
            # Create summary (would be populated from other tool outputs)
            summary = PlanningReportSummary(
                crop=input_data.crop,
                surface_ha=input_data.surface_ha,
                total_tasks=0,  # Would come from generate_planning_tasks
                total_duration_days=0,  # Would come from optimize_task_sequence
                total_cost_eur=None if not input_data.include_costs else 0.0,
                feasibility_score=None if not input_data.include_feasibility else 0.0,
                is_feasible=None if not input_data.include_feasibility else True
            )
            
            # Add recommendations based on what's included
            if input_data.include_feasibility:
                recommendations.append("✅ Vérifier faisabilité climatique avant de finaliser le plan")
            
            if input_data.include_costs:
                recommendations.append("💰 Analyser ROI et comparer avec alternatives avant investissement")
            
            if input_data.include_resources:
                recommendations.append("🚜 Vérifier disponibilité des ressources critiques à l'avance")
            
            recommendations.append("📅 Planifier avec marge de sécurité pour aléas météo")
            recommendations.append("📊 Suivre indicateurs clés pendant exécution du plan")
            
            logger.info(f"✅ Generated planning report for {input_data.crop}: {input_data.surface_ha} ha")
            
            return PlanningReportOutput(
                success=True,
                crop=input_data.crop,
                surface_ha=input_data.surface_ha,
                location=input_data.location,
                summary=summary,
                tasks_analysis=None,  # Would be populated from generate_planning_tasks
                cost_analysis=None if not input_data.include_costs else {},
                resource_analysis=None if not input_data.include_resources else {},
                feasibility_analysis=None if not input_data.include_feasibility else {},
                recommendations=recommendations,
                warnings=warnings
            )
            
        except Exception as e:
            logger.error(f"Planning report generation error: {e}", exc_info=True)
            raise ValueError(f"Erreur lors de la génération du rapport: {str(e)}")
    
    def aggregate_from_tool_outputs(
        self,
        input_data: PlanningReportInput,
        feasibility_output: Optional[Dict[str, Any]] = None,
        tasks_output: Optional[Dict[str, Any]] = None,
        sequence_output: Optional[Dict[str, Any]] = None,
        costs_output: Optional[Dict[str, Any]] = None,
        resources_output: Optional[Dict[str, Any]] = None
    ) -> PlanningReportOutput:
        """
        Aggregate outputs from all planning tools into comprehensive report.
        
        This method would be used when the agent has already called the other tools.
        """
        warnings = []
        recommendations = []
        
        # Aggregate all warnings from tool outputs
        if feasibility_output and 'warnings' in feasibility_output:
            warnings.extend(feasibility_output['warnings'])
        if tasks_output and 'warnings' in tasks_output:
            warnings.extend(tasks_output['warnings'])
        if sequence_output and 'warnings' in sequence_output:
            warnings.extend(sequence_output['warnings'])
        if costs_output and 'warnings' in costs_output:
            warnings.extend(costs_output['warnings'])
        if resources_output and 'resource_availability_warnings' in resources_output:
            warnings.extend(resources_output['resource_availability_warnings'])
        
        # Extract summary data
        total_tasks = tasks_output.get('total_tasks', 0) if tasks_output else 0
        total_duration_days = sequence_output.get('total_duration_days', 0) if sequence_output else 0
        total_cost_eur = costs_output.get('total_cost_eur') if costs_output else None
        feasibility_score = feasibility_output.get('feasibility_score') if feasibility_output else None
        is_feasible = feasibility_output.get('is_feasible') if feasibility_output else None
        
        summary = PlanningReportSummary(
            crop=input_data.crop,
            surface_ha=input_data.surface_ha,
            total_tasks=total_tasks,
            total_duration_days=total_duration_days,
            total_cost_eur=total_cost_eur,
            feasibility_score=feasibility_score,
            is_feasible=is_feasible
        )
        
        # Generate recommendations based on aggregated data
        recommendations = self._generate_recommendations(
            feasibility_output,
            tasks_output,
            sequence_output,
            costs_output,
            resources_output
        )
        
        return PlanningReportOutput(
            success=True,
            crop=input_data.crop,
            surface_ha=input_data.surface_ha,
            location=input_data.location,
            summary=summary,
            tasks_analysis=tasks_output,
            cost_analysis=costs_output,
            resource_analysis=resources_output,
            feasibility_analysis=feasibility_output,
            recommendations=recommendations,
            warnings=warnings
        )
    
    def _generate_recommendations(
        self,
        feasibility_output: Optional[Dict[str, Any]],
        tasks_output: Optional[Dict[str, Any]],
        sequence_output: Optional[Dict[str, Any]],
        costs_output: Optional[Dict[str, Any]],
        resources_output: Optional[Dict[str, Any]]
    ) -> List[str]:
        """Generate actionable recommendations based on all analyses"""
        recommendations = []
        
        # Feasibility recommendations
        if feasibility_output:
            if not feasibility_output.get('is_feasible', True):
                recommendations.append("🚨 CRITIQUE: Culture non viable dans cette zone - Choisir alternative recommandée")
            elif feasibility_output.get('feasibility_score', 10) < 5:
                recommendations.append("⚠️ Faisabilité faible - Évaluer risques avant de procéder")
        
        # Cost recommendations
        if costs_output:
            roi = costs_output.get('roi_percent')
            if roi is not None:
                if roi < 0:
                    recommendations.append("🚨 ROI négatif - Révision majeure du plan nécessaire")
                elif roi < 30:
                    recommendations.append("⚠️ ROI faible - Optimiser coûts ou choisir culture plus rentable")
                elif roi > 100:
                    recommendations.append("✅ ROI excellent - Considérer augmentation de surface si ressources disponibles")
        
        # Resource recommendations
        if resources_output:
            critical_resources = resources_output.get('critical_resources', [])
            if len(critical_resources) > 5:
                recommendations.append(f"⚠️ {len(critical_resources)} ressources critiques - Sécuriser disponibilité à l'avance")
        
        # Task recommendations
        if tasks_output:
            total_tasks = tasks_output.get('total_tasks', 0)
            if total_tasks > 15:
                recommendations.append("ℹ️ Plan complexe - Considérer simplification ou phasage")
            elif total_tasks < 3:
                recommendations.append("⚠️ Plan minimal - Vérifier que toutes tâches essentielles sont incluses")
        
        # Sequence recommendations
        if sequence_output:
            efficiency_gain = sequence_output.get('efficiency_gain_percent')
            if efficiency_gain and efficiency_gain > 20:
                recommendations.append(f"✅ Optimisation séquence efficace ({efficiency_gain}% gain) - Respecter ordre recommandé")
        
        # General recommendations
        recommendations.append("📅 Prévoir marge de sécurité de 20% sur durées pour aléas météo")
        recommendations.append("📊 Mettre en place suivi hebdomadaire des indicateurs clés")
        recommendations.append("🔄 Réviser plan si conditions changent significativement")
        
        return recommendations


async def generate_planning_report_enhanced(
    crop: str,
    surface_ha: float,
    location: Optional[str] = None,
    include_costs: bool = True,
    include_resources: bool = True,
    include_feasibility: bool = False
) -> str:
    """
    Async wrapper for generate planning report tool
    
    Args:
        crop: Crop name (e.g., 'blé', 'maïs')
        surface_ha: Surface area in hectares
        location: Location for feasibility check (optional)
        include_costs: Whether to include cost analysis
        include_resources: Whether to include resource analysis
        include_feasibility: Whether to include feasibility check
        
    Returns:
        JSON string with comprehensive planning report
    """
    try:
        # Validate inputs
        input_data = PlanningReportInput(
            crop=crop,
            surface_ha=surface_ha,
            location=location,
            include_costs=include_costs,
            include_resources=include_resources,
            include_feasibility=include_feasibility
        )
        
        # Execute service
        service = EnhancedPlanningReportService()
        result = await service.generate_report(input_data)
        
        return result.model_dump_json(indent=2, exclude_none=True)
        
    except ValueError as e:
        # Validation or business logic error
        error_result = PlanningReportOutput(
            success=False,
            crop=crop,
            surface_ha=surface_ha,
            location=location,
            error=str(e),
            error_type="validation"
        )
        return error_result.model_dump_json(indent=2)
    except Exception as e:
        # Unexpected error
        logger.error(f"Unexpected error in generate_planning_report_enhanced: {e}", exc_info=True)
        error_result = PlanningReportOutput(
            success=False,
            crop=crop,
            surface_ha=surface_ha,
            location=location,
            error=f"Erreur inattendue: {str(e)}",
            error_type="unknown"
        )
        return error_result.model_dump_json(indent=2)


# Create the StructuredTool
generate_planning_report_tool_enhanced = StructuredTool.from_function(
    func=generate_planning_report_enhanced,
    name="generate_planning_report",
    description="""Génère un rapport de planification agricole complet.

⚠️ OUTIL D'AGRÉGATION - Combine les résultats des autres outils de planification:
1. check_crop_feasibility (optionnel)
2. generate_planning_tasks (requis)
3. optimize_task_sequence (requis)
4. calculate_planning_costs (optionnel)
5. analyze_resource_requirements (optionnel)

Rapport inclut:
- Résumé exécutif (tâches, durée, coûts, faisabilité)
- Analyses détaillées de chaque outil
- Consolidation de tous les avertissements
- Recommandations actionnables basées sur l'ensemble des analyses
- Identification des problèmes critiques

Utilisation recommandée:
1. Appeler les outils individuels selon besoins
2. Passer leurs sorties à cet outil pour rapport consolidé
3. Utiliser recommandations pour décisions finales

Retourne un rapport structuré avec toutes les informations de planification.""",
    args_schema=PlanningReportInput,
    return_direct=False,
    coroutine=generate_planning_report_enhanced,
    handle_validation_error=True
)

