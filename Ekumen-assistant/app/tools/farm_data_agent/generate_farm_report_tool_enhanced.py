"""
Enhanced Generate Farm Report Tool.

Improvements:
- Type-safe Pydantic schemas
- Redis caching (30min TTL for reports)
- Structured error handling
- Comprehensive report generation
- Integration with all farm data tools
"""

import logging
from typing import Optional, Dict, List, Any
from datetime import datetime
from langchain.tools import StructuredTool

from app.tools.schemas.farm_data_schemas import (
    FarmReportInput,
    FarmReportOutput,
    ExecutiveSummary,
    TimePeriod,
    PerformanceRank,
    TrendDirection
)
from app.core.cache import redis_cache
from app.tools.farm_data_agent.get_farm_data_tool_enhanced import EnhancedFarmDataService
from app.tools.farm_data_agent.calculate_performance_metrics_tool_enhanced import EnhancedPerformanceMetricsService
from app.tools.farm_data_agent.benchmark_crop_performance_tool_enhanced import EnhancedBenchmarkService
from app.tools.farm_data_agent.analyze_trends_tool_enhanced import EnhancedTrendsService

logger = logging.getLogger(__name__)


class EnhancedFarmReportService:
    """Service for generating farm reports with caching"""

    @redis_cache(ttl=1800, model_class=FarmReportOutput, category="farm_data")
    async def generate_report(self, input_data: FarmReportInput) -> FarmReportOutput:
        """
        Generate comprehensive farm report
        
        Args:
            input_data: Validated input
            
        Returns:
            FarmReportOutput with comprehensive report
            
        Raises:
            ValueError: If report generation fails
        """
        try:
            # Get farm data
            from app.tools.schemas.farm_data_schemas import FarmDataInput
            farm_data_service = EnhancedFarmDataService()
            farm_data_input = FarmDataInput(
                time_period=input_data.time_period,
                farm_id=input_data.farm_id,
                use_mesparcelles=True
            )
            farm_data = await farm_data_service.get_farm_data(farm_data_input)
            
            if not farm_data.success or not farm_data.database_records:
                return FarmReportOutput(
                    success=False,
                    farm_id=input_data.farm_id,
                    report_period=input_data.time_period.value,
                    error="Aucune donnée disponible pour générer le rapport",
                    error_type="no_data"
                )
            
            # Calculate performance metrics
            from app.tools.schemas.farm_data_schemas import PerformanceMetricsInput
            metrics_service = EnhancedPerformanceMetricsService()
            metrics_input = PerformanceMetricsInput(
                farm_id=input_data.farm_id,
                time_period=input_data.time_period
            )
            metrics_output = await metrics_service.calculate_metrics(metrics_input)
            
            # Get benchmark analysis if requested
            benchmark_analysis = None
            if input_data.include_benchmarks and metrics_output.success:
                benchmark_analysis = await self._get_benchmark_analysis(
                    input_data.farm_id,
                    input_data.time_period,
                    metrics_output
                )
            
            # Get trend analysis if requested
            trend_analysis = None
            if input_data.include_trends:
                trend_analysis = await self._get_trend_analysis(
                    input_data.farm_id
                )
            
            # Generate executive summary
            executive_summary = self._generate_executive_summary(
                farm_data,
                metrics_output,
                benchmark_analysis,
                trend_analysis
            )
            
            # Generate data overview
            data_overview = self._generate_data_overview(farm_data)
            
            # Generate recommendations
            recommendations = self._generate_recommendations(
                metrics_output,
                benchmark_analysis,
                trend_analysis
            )
            
            logger.info(f"✅ Generated farm report for {input_data.farm_id}")
            
            return FarmReportOutput(
                success=True,
                farm_id=input_data.farm_id,
                report_period=input_data.time_period.value,
                executive_summary=executive_summary,
                data_overview=data_overview,
                performance_analysis=metrics_output.model_dump() if metrics_output.success else None,
                benchmark_analysis=benchmark_analysis,
                trend_analysis=trend_analysis,
                recommendations=recommendations
            )
            
        except Exception as e:
            logger.error(f"Farm report generation error: {e}", exc_info=True)
            raise ValueError(f"Erreur lors de la génération du rapport: {str(e)}")

    async def _get_benchmark_analysis(
        self,
        farm_id: str,
        time_period: TimePeriod,
        metrics_output: Any
    ) -> Optional[Dict[str, Any]]:
        """Get benchmark analysis for main crops"""
        try:
            benchmark_service = EnhancedBenchmarkService()
            benchmark_results = {}
            
            # Get benchmarks for each crop
            for crop in metrics_output.crop_metrics.keys():
                from app.tools.schemas.farm_data_schemas import BenchmarkInput
                benchmark_input = BenchmarkInput(
                    crop=crop,
                    farm_id=farm_id,
                    time_period=time_period
                )
                benchmark_output = await benchmark_service.benchmark_performance(benchmark_input)
                if benchmark_output.success:
                    benchmark_results[crop] = benchmark_output.model_dump()
            
            return benchmark_results if benchmark_results else None
            
        except Exception as e:
            logger.warning(f"Benchmark analysis failed: {e}")
            return None

    async def _get_trend_analysis(self, farm_id: str) -> Optional[Dict[str, Any]]:
        """Get trend analysis"""
        try:
            from app.tools.schemas.farm_data_schemas import TrendsInput
            trends_service = EnhancedTrendsService()
            trends_input = TrendsInput(farm_id=farm_id)
            trends_output = await trends_service.analyze_trends(trends_input)
            
            if trends_output.success:
                return trends_output.model_dump()
            return None
            
        except Exception as e:
            logger.warning(f"Trend analysis failed: {e}")
            return None

    def _generate_executive_summary(
        self,
        farm_data: Any,
        metrics_output: Any,
        benchmark_analysis: Optional[Dict],
        trend_analysis: Optional[Dict]
    ) -> ExecutiveSummary:
        """Generate executive summary"""
        total_surface = sum(r.surface_ha for r in farm_data.database_records)
        
        summary = ExecutiveSummary(
            total_records=farm_data.total_records,
            total_surface_ha=round(total_surface, 2)
        )
        
        if metrics_output and metrics_output.success and metrics_output.overall_metrics:
            summary.average_yield_q_ha = metrics_output.overall_metrics.average_yield_q_ha
            summary.average_cost_eur_ha = metrics_output.overall_metrics.average_cost_eur_ha
            summary.average_quality_score = metrics_output.overall_metrics.average_quality_score
        
        if benchmark_analysis:
            # Get first crop's benchmark for summary
            first_crop_benchmark = next(iter(benchmark_analysis.values()), None)
            if first_crop_benchmark:
                summary.performance_rank = first_crop_benchmark.get("performance_rank")
                summary.overall_performance_percent = first_crop_benchmark.get("performance_metrics", {}).get("overall_performance_percent")
        
        if trend_analysis:
            summary.yield_trend = trend_analysis.get("yield_trend", {}).get("trend_direction")
            summary.cost_trend = trend_analysis.get("cost_trend", {}).get("trend_direction")
        
        return summary

    def _generate_data_overview(self, farm_data: Any) -> Dict[str, Any]:
        """Generate data overview"""
        crops = set()
        parcels = []
        
        for record in farm_data.database_records:
            crops.update(record.cultures)
            parcels.append(record.parcel)
        
        return {
            "crops_analyzed": list(crops),
            "parcels_analyzed": parcels,
            "total_parcels": len(parcels),
            "total_crops": len(crops),
            "data_sources": farm_data.data_sources
        }

    def _generate_recommendations(
        self,
        metrics_output: Any,
        benchmark_analysis: Optional[Dict],
        trend_analysis: Optional[Dict]
    ) -> List[str]:
        """Generate recommendations"""
        recommendations = []
        
        # Data quality recommendations
        if metrics_output and metrics_output.success:
            total_records = metrics_output.total_records
            if total_records < 5:
                recommendations.append("📊 Améliorer la collecte de données pour une analyse plus précise")
            elif total_records > 20:
                recommendations.append("✅ Excellent volume de données - Continuer la collecte systématique")
        
        # Performance recommendations
        if metrics_output and metrics_output.success and metrics_output.overall_metrics:
            avg_yield = metrics_output.overall_metrics.average_yield_q_ha
            avg_cost = metrics_output.overall_metrics.average_cost_eur_ha
            
            if avg_yield < 60:
                recommendations.append("🌾 Optimiser les pratiques culturales pour améliorer le rendement")
            if avg_cost > 500:
                recommendations.append("💰 Analyser les coûts pour identifier les économies possibles")
        
        # Benchmark recommendations
        if benchmark_analysis:
            for crop, benchmark in benchmark_analysis.items():
                rank = benchmark.get("performance_rank")
                if rank == "below_average":
                    recommendations.append(f"⚠️ {crop}: Mettre en place un plan d'amélioration des performances")
                elif rank == "top_10_percent":
                    recommendations.append(f"🏆 {crop}: Maintenir l'excellence et partager les bonnes pratiques")
        
        # Trend recommendations
        if trend_analysis:
            yield_trend = trend_analysis.get("yield_trend", {}).get("trend_direction")
            cost_trend = trend_analysis.get("cost_trend", {}).get("trend_direction")
            
            if yield_trend == "decreasing":
                recommendations.append("📉 Investiguer les causes de la baisse de rendement")
            if cost_trend == "increasing":
                recommendations.append("📈 Contrôler l'évolution des coûts de production")
        
        return recommendations


async def generate_farm_report_enhanced(
    farm_id: str,
    time_period: Optional[str] = "current_year",
    include_benchmarks: bool = True,
    include_trends: bool = True
) -> str:
    """
    Async wrapper for generate farm report tool
    
    Args:
        farm_id: Farm ID (SIRET) to generate report for
        time_period: Time period for report
        include_benchmarks: Whether to include benchmark analysis
        include_trends: Whether to include trend analysis
        
    Returns:
        JSON string with comprehensive farm report
    """
    try:
        # Validate inputs
        input_data = FarmReportInput(
            farm_id=farm_id,
            time_period=TimePeriod(time_period) if time_period else TimePeriod.CURRENT_YEAR,
            include_benchmarks=include_benchmarks,
            include_trends=include_trends
        )
        
        # Execute service
        service = EnhancedFarmReportService()
        result = await service.generate_report(input_data)
        
        # Return as JSON
        return result.model_dump_json(indent=2, exclude_none=True)
        
    except ValueError as e:
        logger.error(f"Farm report validation error: {e}")
        error_result = FarmReportOutput(
            success=False,
            farm_id=farm_id,
            report_period=time_period or "current_year",
            error=str(e),
            error_type="validation"
        )
        return error_result.model_dump_json(indent=2)
        
    except Exception as e:
        logger.error(f"Unexpected farm report error: {e}", exc_info=True)
        error_result = FarmReportOutput(
            success=False,
            farm_id=farm_id,
            report_period=time_period or "current_year",
            error="Erreur inattendue lors de la génération du rapport. Veuillez réessayer.",
            error_type="unknown"
        )
        return error_result.model_dump_json(indent=2)


# Create the StructuredTool
generate_farm_report_tool_enhanced = StructuredTool.from_function(
    func=generate_farm_report_enhanced,
    name="generate_farm_report",
    description="""Génère un rapport d'exploitation structuré et complet.

Retourne un rapport détaillé avec:
- Résumé exécutif (surfaces, rendements, coûts)
- Vue d'ensemble des données
- Analyse de performance
- Comparaison aux standards (optionnel)
- Analyse des tendances (optionnel)
- Recommandations personnalisées

Utilisez cet outil quand les agriculteurs demandent un rapport complet de leur exploitation.""",
    args_schema=FarmReportInput,
    return_direct=False,
    coroutine=generate_farm_report_enhanced,
    handle_validation_error=True
)

