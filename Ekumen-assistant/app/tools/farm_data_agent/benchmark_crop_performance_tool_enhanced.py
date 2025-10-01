"""
Enhanced Benchmark Crop Performance Tool.

Improvements:
- Type-safe Pydantic schemas
- Redis caching (2h TTL for benchmarks)
- Structured error handling
- Industry benchmark database
- Comprehensive performance ranking
"""

import logging
from typing import Optional, Dict, List
from datetime import datetime
from langchain.tools import StructuredTool

from app.tools.schemas.farm_data_schemas import (
    BenchmarkInput,
    BenchmarkOutput,
    IndustryBenchmark,
    PerformanceMetrics,
    PerformanceRank,
    TimePeriod
)
from app.core.cache import redis_cache
from app.tools.farm_data_agent.calculate_performance_metrics_tool_enhanced import EnhancedPerformanceMetricsService

logger = logging.getLogger(__name__)


class EnhancedBenchmarkService:
    """Service for benchmarking crop performance with caching"""

    # Industry benchmarks (from French agricultural statistics)
    INDUSTRY_BENCHMARKS = {
        "blé": {"yield_q_ha": 70.0, "quality_score": 8.0},
        "maïs": {"yield_q_ha": 90.0, "quality_score": 8.5},
        "colza": {"yield_q_ha": 35.0, "quality_score": 7.5},
        "tournesol": {"yield_q_ha": 25.0, "quality_score": 7.0},
        "orge": {"yield_q_ha": 65.0, "quality_score": 7.8},
        "avoine": {"yield_q_ha": 55.0, "quality_score": 7.2},
        "soja": {"yield_q_ha": 30.0, "quality_score": 7.5},
        "pois": {"yield_q_ha": 40.0, "quality_score": 7.3},
        "betterave": {"yield_q_ha": 850.0, "quality_score": 8.2},
        "pomme de terre": {"yield_q_ha": 450.0, "quality_score": 7.8}
    }

    @redis_cache(ttl=7200, model_class=BenchmarkOutput, category="farm_data")
    async def benchmark_performance(self, input_data: BenchmarkInput) -> BenchmarkOutput:
        """
        Benchmark crop performance against industry standards
        
        Args:
            input_data: Validated input
            
        Returns:
            BenchmarkOutput with benchmark comparison
            
        Raises:
            ValueError: If benchmarking fails
        """
        try:
            # Get farm performance metrics
            from app.tools.schemas.farm_data_schemas import PerformanceMetricsInput
            metrics_service = EnhancedPerformanceMetricsService()
            metrics_input = PerformanceMetricsInput(
                farm_id=input_data.farm_id,
                time_period=input_data.time_period,
                crops=[input_data.crop]
            )
            metrics_output = await metrics_service.calculate_metrics(metrics_input)
            
            if not metrics_output.success:
                return BenchmarkOutput(
                    success=False,
                    crop=input_data.crop,
                    error="Impossible de calculer les métriques de performance",
                    error_type="metrics_error"
                )
            
            # Get crop-specific metrics
            crop_metrics = metrics_output.crop_metrics.get(input_data.crop)
            if not crop_metrics:
                return BenchmarkOutput(
                    success=False,
                    crop=input_data.crop,
                    error=f"Aucune donnée disponible pour la culture '{input_data.crop}'",
                    error_type="no_crop_data"
                )

            # Check if we have real data to benchmark
            warnings = []
            if crop_metrics.average_yield is None:
                warnings.append("⚠️ Aucune donnée de rendement réelle - Benchmark impossible")
            if crop_metrics.average_quality is None:
                warnings.append("⚠️ Aucune donnée de qualité disponible")

            # Cannot benchmark without yield data
            if crop_metrics.average_yield is None:
                return BenchmarkOutput(
                    success=False,
                    crop=input_data.crop,
                    error="Impossible de comparer sans données de rendement réelles",
                    error_type="insufficient_data",
                    warnings=warnings
                )

            # Get industry benchmark
            industry_benchmark = self._get_industry_benchmark(input_data.crop)

            # Calculate performance metrics (with None handling)
            performance_metrics = self._calculate_performance_metrics(
                farm_yield=crop_metrics.average_yield,
                farm_quality=crop_metrics.average_quality,
                benchmark=industry_benchmark
            )
            
            # Determine performance rank
            performance_rank = self._calculate_performance_rank(performance_metrics)
            
            # Generate benchmark insights
            benchmark_insights = self._generate_benchmark_insights(
                performance_metrics,
                performance_rank,
                input_data.crop
            )
            
            logger.info(f"✅ Benchmarked {input_data.crop}: {performance_rank.value}")

            return BenchmarkOutput(
                success=True,
                crop=input_data.crop,
                farm_performance={
                    "average_yield": crop_metrics.average_yield,
                    "average_quality": crop_metrics.average_quality
                },
                industry_benchmark=industry_benchmark,
                performance_metrics=performance_metrics,
                performance_rank=performance_rank,
                benchmark_insights=benchmark_insights,
                warnings=warnings
            )
            
        except Exception as e:
            logger.error(f"Benchmark error: {e}", exc_info=True)
            raise ValueError(f"Erreur lors du benchmark: {str(e)}")

    def _get_industry_benchmark(self, crop: str) -> IndustryBenchmark:
        """Get industry benchmark for a specific crop"""
        crop_lower = crop.lower()
        benchmark_data = self.INDUSTRY_BENCHMARKS.get(
            crop_lower,
            {"yield_q_ha": 65.0, "quality_score": 7.5}  # Default
        )
        
        return IndustryBenchmark(
            yield_q_ha=benchmark_data["yield_q_ha"],
            quality_score=benchmark_data["quality_score"]
        )

    def _calculate_performance_metrics(
        self,
        farm_yield: Optional[float],
        farm_quality: Optional[float],
        benchmark: IndustryBenchmark
    ) -> PerformanceMetrics:
        """
        Calculate performance metrics compared to benchmark.

        Handles None values for missing data.
        farm_yield should not be None (checked before calling).
        farm_quality can be None (quality not tracked yet).
        """
        # Calculate yield performance (farm_yield guaranteed not None by caller)
        yield_performance = (farm_yield / benchmark.yield_q_ha) * 100

        # Calculate quality performance (may be None)
        quality_performance = None
        if farm_quality is not None:
            quality_performance = (farm_quality / benchmark.quality_score) * 100

        # Calculate overall performance
        if quality_performance is not None:
            overall_performance = (yield_performance + quality_performance) / 2
        else:
            # If no quality data, overall = yield only
            overall_performance = yield_performance

        return PerformanceMetrics(
            yield_performance_percent=round(yield_performance, 1),
            quality_performance_percent=round(quality_performance, 1) if quality_performance is not None else None,
            overall_performance_percent=round(overall_performance, 1)
        )

    def _calculate_performance_rank(self, metrics: PerformanceMetrics) -> PerformanceRank:
        """
        Calculate performance rank based on overall performance.

        NOTE: These ranks are based on % of national average, NOT percentile ranks.
        Being 110% of average does NOT mean top 10% of farms - it depends on distribution.
        These are simplified categories for quick assessment.
        """
        overall = metrics.overall_performance_percent

        if overall > 110:
            return PerformanceRank.EXCEPTIONAL  # >110% of average
        elif overall > 100:
            return PerformanceRank.EXCELLENT  # >100% of average
        elif overall > 90:
            return PerformanceRank.ABOVE_AVERAGE  # >90% of average
        elif overall > 80:
            return PerformanceRank.AVERAGE  # 80-90% of average
        else:
            return PerformanceRank.BELOW_AVERAGE  # <80% of average

    def _generate_benchmark_insights(
        self,
        metrics: PerformanceMetrics,
        rank: PerformanceRank,
        crop: str
    ) -> List[str]:
        """
        Generate benchmark insights with proper None handling.

        CRITICAL: quality_perf can be None when quality data is unavailable.
        All comparisons must check for None before using operators.
        """
        insights = []

        overall = metrics.overall_performance_percent
        yield_perf = metrics.yield_performance_percent
        quality_perf = metrics.quality_performance_percent  # Can be None!

        # Disclaimer about ranking methodology
        insights.append(
            "ℹ️ Note: Classement basé sur % de la moyenne nationale, "
            "pas sur percentiles réels. Consulter un expert pour comparaison précise."
        )

        # Overall performance insights (updated to match new enum values)
        if overall > 110:
            insights.append(f"🏆 Performance exceptionnelle pour {crop} - >110% de la moyenne nationale")
        elif overall > 100:
            insights.append(f"🥇 Performance excellente pour {crop} - >100% de la moyenne nationale")
        elif overall > 90:
            insights.append(f"✅ Performance au-dessus de la moyenne pour {crop}")
        elif overall > 80:
            insights.append(f"📊 Performance dans la moyenne pour {crop}")
        else:
            insights.append(f"⚠️ Performance en dessous de la moyenne pour {crop} - Amélioration nécessaire")

        # Yield-specific insights
        if yield_perf > 110:
            insights.append("🌾 Rendement exceptionnel - Dépassement des standards de +10%")
        elif yield_perf > 100:
            insights.append("🌾 Rendement excellent - Au-dessus des standards")
        elif yield_perf < 80:
            insights.append("🌾 Rendement faible - Optimisation des pratiques culturales recommandée")

        # Quality-specific insights (ONLY if quality data available)
        if quality_perf is not None:
            if quality_perf > 110:
                insights.append("⭐ Qualité exceptionnelle - Standards dépassés de +10%")
            elif quality_perf > 100:
                insights.append("⭐ Qualité excellente - Au-dessus des standards")
            elif quality_perf < 80:
                insights.append("⭐ Qualité faible - Amélioration de la qualité recommandée")
        else:
            insights.append("ℹ️ Données de qualité non disponibles pour ce benchmark")

        # Balanced performance insights (ONLY if quality data available)
        if quality_perf is not None:
            if abs(yield_perf - quality_perf) > 20:
                if yield_perf > quality_perf:
                    insights.append("⚖️ Déséquilibre: Rendement élevé mais qualité à améliorer")
                else:
                    insights.append("⚖️ Déséquilibre: Qualité élevée mais rendement à améliorer")
            else:
                insights.append("⚖️ Performance équilibrée entre rendement et qualité")
        else:
            insights.append("📊 Benchmark basé uniquement sur le rendement")

        return insights


async def benchmark_crop_performance_enhanced(
    crop: str,
    farm_id: Optional[str] = None,
    time_period: Optional[str] = None
) -> str:
    """
    Async wrapper for benchmark crop performance tool
    
    Args:
        crop: Crop type to benchmark
        farm_id: Farm ID to benchmark
        time_period: Time period for benchmark
        
    Returns:
        JSON string with benchmark comparison
    """
    try:
        # Validate inputs
        input_data = BenchmarkInput(
            crop=crop,
            farm_id=farm_id,
            time_period=TimePeriod(time_period) if time_period else None
        )
        
        # Execute service
        service = EnhancedBenchmarkService()
        result = await service.benchmark_performance(input_data)
        
        # Return as JSON
        return result.model_dump_json(indent=2, exclude_none=True)
        
    except ValueError as e:
        logger.error(f"Benchmark validation error: {e}")
        error_result = BenchmarkOutput(
            success=False,
            crop=crop,
            error=str(e),
            error_type="validation"
        )
        return error_result.model_dump_json(indent=2)
        
    except Exception as e:
        logger.error(f"Unexpected benchmark error: {e}", exc_info=True)
        error_result = BenchmarkOutput(
            success=False,
            crop=crop,
            error="Erreur inattendue lors du benchmark. Veuillez réessayer.",
            error_type="unknown"
        )
        return error_result.model_dump_json(indent=2)


# Create the StructuredTool
benchmark_crop_performance_tool_enhanced = StructuredTool.from_function(
    func=benchmark_crop_performance_enhanced,
    name="benchmark_crop_performance",
    description="""Compare les performances des cultures aux standards de l'industrie.

Retourne une analyse comparative avec:
- Performance vs standards industriels
- Classement de performance (Top 10%, Top 25%, etc.)
- Insights détaillés sur rendement et qualité
- Recommandations d'amélioration

Utilisez cet outil quand les agriculteurs veulent comparer leurs performances aux standards.""",
    args_schema=BenchmarkInput,
    return_direct=False,
    coroutine=benchmark_crop_performance_enhanced,
    handle_validation_error=True
)

