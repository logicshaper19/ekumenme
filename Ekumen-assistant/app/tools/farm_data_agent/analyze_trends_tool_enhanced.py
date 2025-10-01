"""
Enhanced Analyze Trends Tool.

Improvements:
- Type-safe Pydantic schemas
- Redis caching (1h TTL for trends)
- Structured error handling
- Multi-year trend analysis
- Crop-specific trend tracking
"""

import logging
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from langchain.tools import StructuredTool

from app.tools.schemas.farm_data_schemas import (
    TrendsInput,
    TrendsOutput,
    TrendMetrics,
    YearlyMetrics,
    TrendDirection
)
from app.core.cache import redis_cache
from app.tools.farm_data_agent.get_farm_data_tool_enhanced import EnhancedFarmDataService

logger = logging.getLogger(__name__)


class EnhancedTrendsService:
    """Service for analyzing trends with caching"""

    @redis_cache(ttl=3600, model_class=TrendsOutput, category="farm_data")
    async def analyze_trends(self, input_data: TrendsInput) -> TrendsOutput:
        """
        Analyze year-over-year trends from farm data
        
        Args:
            input_data: Validated input
            
        Returns:
            TrendsOutput with trend analysis
            
        Raises:
            ValueError: If trend analysis fails
        """
        try:
            # Get farm data for multiple years
            from app.tools.schemas.farm_data_schemas import FarmDataInput, TimePeriod
            farm_data_service = EnhancedFarmDataService()
            farm_data_input = FarmDataInput(
                time_period=TimePeriod.LAST_3_YEARS,  # Get 3 years of data
                crops=input_data.crops,
                farm_id=input_data.farm_id,
                use_mesparcelles=False
            )
            farm_data = await farm_data_service.get_farm_data(farm_data_input)
            
            if not farm_data.success or not farm_data.database_records:
                return TrendsOutput(
                    success=False,
                    years_analyzed=0,
                    error="Aucune donnée disponible pour l'analyse des tendances",
                    error_type="no_data"
                )
            
            records = farm_data.database_records
            
            # Group records by year
            yearly_data = self._group_by_year(records)
            
            if len(yearly_data) < input_data.min_years:
                return TrendsOutput(
                    success=False,
                    years_analyzed=len(yearly_data),
                    error=f"Données insuffisantes pour l'analyse des tendances (minimum {input_data.min_years} années requises)",
                    error_type="insufficient_years"
                )
            
            # Calculate yearly metrics
            yearly_metrics = self._calculate_yearly_metrics(yearly_data)

            # Calculate overall trends
            yield_trend, cost_trend, quality_trend = self._calculate_overall_trends(yearly_metrics)

            # Calculate crop-specific trends
            crop_trends = self._calculate_crop_trends(records)

            # Generate warnings for missing data
            warnings = []
            if yield_trend is None:
                warnings.append("⚠️ Aucune donnée de rendement réelle - Tendance de rendement non disponible")
            if cost_trend is None:
                warnings.append("⚠️ Aucune donnée de coût disponible - Tendance de coût non disponible")
            if quality_trend is None:
                warnings.append("ℹ️ Aucune donnée de qualité disponible - Tendance de qualité non disponible")
            if len(crop_trends) == 0:
                warnings.append("⚠️ Données insuffisantes pour les tendances par culture")

            # Generate trend insights
            trend_insights = self._generate_trend_insights(
                yield_trend, cost_trend, quality_trend, crop_trends
            )

            logger.info(f"✅ Analyzed trends for {len(yearly_data)} years")

            return TrendsOutput(
                success=True,
                yearly_metrics=yearly_metrics,
                yield_trend=yield_trend,
                cost_trend=cost_trend,
                quality_trend=quality_trend,
                crop_trends=crop_trends,
                trend_insights=trend_insights,
                warnings=warnings,
                years_analyzed=len(yearly_data)
            )
            
        except Exception as e:
            logger.error(f"Trends analysis error: {e}", exc_info=True)
            raise ValueError(f"Erreur lors de l'analyse des tendances: {str(e)}")

    def _group_by_year(self, records: List[Any]) -> Dict[int, List[Any]]:
        """Group records by year (millesime)"""
        yearly_data: Dict[int, List[Any]] = {}
        for record in records:
            year = record.millesime
            if year not in yearly_data:
                yearly_data[year] = []
            yearly_data[year].append(record)
        return yearly_data

    def _calculate_yearly_metrics(self, yearly_data: Dict[int, List[Any]]) -> Dict[str, YearlyMetrics]:
        """
        Calculate metrics for each year using REAL intervention data.

        Extracts yield, cost, and quality from intervention_summary.
        Returns None for missing data instead of mock values.
        """
        yearly_metrics = {}

        for year, year_records in yearly_data.items():
            total_surface = sum(r.surface_ha for r in year_records)

            # Extract REAL data from intervention summaries
            total_yield_q = 0.0
            total_cost_eur = 0.0
            records_with_yield = 0
            records_with_cost = 0

            for record in year_records:
                if record.intervention_summary:
                    summary = record.intervention_summary

                    # Use real yield data if available
                    if summary.average_yield_q_ha is not None:
                        total_yield_q += summary.average_yield_q_ha * record.surface_ha
                        records_with_yield += 1

                    # Use real cost data if available
                    if summary.total_cost_eur is not None:
                        total_cost_eur += summary.total_cost_eur
                        records_with_cost += 1

            # Calculate averages only if we have real data
            average_yield = None
            if records_with_yield > 0 and total_surface > 0:
                average_yield = round(total_yield_q / total_surface, 2)

            average_cost = None
            if records_with_cost > 0 and total_surface > 0:
                average_cost = round(total_cost_eur / total_surface, 2)

            # Quality data not tracked yet - honestly return None
            average_quality = None

            yearly_metrics[str(year)] = YearlyMetrics(
                average_yield=average_yield,
                average_cost=average_cost,
                average_quality=average_quality,
                total_surface=round(total_surface, 2),
                record_count=len(year_records)
            )

        return yearly_metrics

    def _calculate_overall_trends(
        self,
        yearly_metrics: Dict[str, YearlyMetrics]
    ) -> Tuple[Optional[TrendMetrics], Optional[TrendMetrics], Optional[TrendMetrics]]:
        """
        Calculate overall trends from yearly metrics.

        Returns None for trends when insufficient real data available.
        Requires non-None values in both first and last year.
        """
        years = sorted(yearly_metrics.keys())
        if len(years) < 2:
            raise ValueError("Insufficient years for trend calculation")

        first_year = years[0]
        last_year = years[-1]

        first_metrics = yearly_metrics[first_year]
        last_metrics = yearly_metrics[last_year]

        # Calculate yield trend (only if real data available)
        yield_trend = None
        if first_metrics.average_yield is not None and last_metrics.average_yield is not None:
            yield_change = self._calculate_percentage_change(
                first_metrics.average_yield,
                last_metrics.average_yield
            )
            yield_trend = TrendMetrics(
                change_percent=yield_change,
                trend_direction=self._get_trend_direction(yield_change),
                first_year_value=first_metrics.average_yield,
                last_year_value=last_metrics.average_yield
            )

        # Calculate cost trend (only if real data available)
        cost_trend = None
        if first_metrics.average_cost is not None and last_metrics.average_cost is not None:
            cost_change = self._calculate_percentage_change(
                first_metrics.average_cost,
                last_metrics.average_cost
            )
            cost_trend = TrendMetrics(
                change_percent=cost_change,
                trend_direction=self._get_trend_direction(cost_change),
                first_year_value=first_metrics.average_cost,
                last_year_value=last_metrics.average_cost
            )

        # Calculate quality trend (only if real data available)
        quality_trend = None
        if first_metrics.average_quality is not None and last_metrics.average_quality is not None:
            quality_change = self._calculate_percentage_change(
                first_metrics.average_quality,
                last_metrics.average_quality
            )
            quality_trend = TrendMetrics(
                change_percent=quality_change,
                trend_direction=self._get_trend_direction(quality_change),
                first_year_value=first_metrics.average_quality,
                last_year_value=last_metrics.average_quality
            )

        return yield_trend, cost_trend, quality_trend

    def _calculate_crop_trends(self, records: List[Any]) -> Dict[str, Dict[str, TrendMetrics]]:
        """
        Calculate trends by crop using REAL intervention data.

        Requires at least 2 years of data per crop.
        Returns None for metrics when insufficient real data.
        """
        crop_yearly_data: Dict[str, Dict[int, List[Any]]] = {}

        for record in records:
            for culture in record.cultures:
                if culture not in crop_yearly_data:
                    crop_yearly_data[culture] = {}
                year = record.millesime
                if year not in crop_yearly_data[culture]:
                    crop_yearly_data[culture][year] = []
                crop_yearly_data[culture][year].append(record)

        crop_trends = {}
        for crop, yearly_data in crop_yearly_data.items():
            if len(yearly_data) < 2:
                continue

            years = sorted(yearly_data.keys())

            # Calculate average yield for first and last year using REAL data
            first_year_yield = self._calculate_year_average_yield(yearly_data[years[0]])
            last_year_yield = self._calculate_year_average_yield(yearly_data[years[-1]])

            # Only calculate trend if we have real data for both years
            if first_year_yield is not None and last_year_yield is not None:
                yield_change = self._calculate_percentage_change(first_year_yield, last_year_yield)

                crop_trends[crop] = {
                    "yield_trend": TrendMetrics(
                        change_percent=yield_change,
                        trend_direction=self._get_trend_direction(yield_change),
                        first_year_value=round(first_year_yield, 2),
                        last_year_value=round(last_year_yield, 2)
                    )
                }

        return crop_trends

    def _calculate_year_average_yield(self, year_records: List[Any]) -> Optional[float]:
        """
        Calculate average yield for a year from REAL intervention data.

        Returns None if no real yield data available.
        """
        total_yield_q = 0.0
        total_surface = 0.0
        has_yield_data = False

        for record in year_records:
            if record.intervention_summary and record.intervention_summary.average_yield_q_ha is not None:
                total_yield_q += record.intervention_summary.average_yield_q_ha * record.surface_ha
                total_surface += record.surface_ha
                has_yield_data = True

        if has_yield_data and total_surface > 0:
            return total_yield_q / total_surface

        return None

    def _calculate_percentage_change(self, old_value: float, new_value: float) -> float:
        """Calculate percentage change between two values"""
        if old_value == 0:
            return 0.0
        return round(((new_value - old_value) / old_value) * 100, 1)

    def _get_trend_direction(self, change_percent: float) -> TrendDirection:
        """Get trend direction from percentage change"""
        if change_percent > 5:
            return TrendDirection.INCREASING
        elif change_percent < -5:
            return TrendDirection.DECREASING
        else:
            return TrendDirection.STABLE

    def _generate_trend_insights(
        self,
        yield_trend: Optional[TrendMetrics],
        cost_trend: Optional[TrendMetrics],
        quality_trend: Optional[TrendMetrics],
        crop_trends: Dict[str, Dict[str, TrendMetrics]]
    ) -> List[str]:
        """
        Generate trend insights with proper None handling.

        Only generates insights for trends with real data available.
        """
        insights = []

        # Yield trend insights (only if real data available)
        if yield_trend is not None:
            if yield_trend.trend_direction == TrendDirection.INCREASING:
                insights.append(f"📈 Rendement en hausse: +{yield_trend.change_percent}%")
            elif yield_trend.trend_direction == TrendDirection.DECREASING:
                insights.append(f"📉 Rendement en baisse: {yield_trend.change_percent}%")
            else:
                insights.append("📊 Rendement stable")
        else:
            insights.append("ℹ️ Tendance de rendement non disponible (données manquantes)")

        # Cost trend insights (only if real data available)
        if cost_trend is not None:
            if cost_trend.trend_direction == TrendDirection.INCREASING:
                insights.append(f"💰 Coûts en hausse: +{cost_trend.change_percent}%")
            elif cost_trend.trend_direction == TrendDirection.DECREASING:
                insights.append(f"💰 Coûts en baisse: {cost_trend.change_percent}%")
            else:
                insights.append("💰 Coûts stables")
        else:
            insights.append("ℹ️ Tendance de coût non disponible (données manquantes)")

        # Quality trend insights (only if real data available)
        if quality_trend is not None:
            if quality_trend.trend_direction == TrendDirection.INCREASING:
                insights.append(f"⭐ Qualité en amélioration: +{quality_trend.change_percent}%")
            elif quality_trend.trend_direction == TrendDirection.DECREASING:
                insights.append(f"⭐ Qualité en baisse: {quality_trend.change_percent}%")
            else:
                insights.append("⭐ Qualité stable")
        else:
            insights.append("ℹ️ Tendance de qualité non disponible (données manquantes)")

        # Crop-specific insights
        if len(crop_trends) > 0:
            for crop, trends in crop_trends.items():
                yield_trend_crop = trends.get("yield_trend")
                if yield_trend_crop and yield_trend_crop.trend_direction == TrendDirection.INCREASING:
                    insights.append(f"🌾 {crop}: Rendement en hausse (+{yield_trend_crop.change_percent}%)")
                elif yield_trend_crop and yield_trend_crop.trend_direction == TrendDirection.DECREASING:
                    insights.append(f"🌾 {crop}: Rendement en baisse ({yield_trend_crop.change_percent}%)")

        return insights


async def analyze_trends_enhanced(
    farm_id: Optional[str] = None,
    crops: Optional[List[str]] = None,
    min_years: int = 2
) -> str:
    """
    Async wrapper for analyze trends tool
    
    Args:
        farm_id: Farm ID to analyze trends for
        crops: Specific crops to analyze trends for
        min_years: Minimum number of years required for trend analysis
        
    Returns:
        JSON string with trend analysis
    """
    try:
        # Validate inputs
        input_data = TrendsInput(
            farm_id=farm_id,
            crops=crops,
            min_years=min_years
        )
        
        # Execute service
        service = EnhancedTrendsService()
        result = await service.analyze_trends(input_data)
        
        # Return as JSON
        return result.model_dump_json(indent=2, exclude_none=True)
        
    except ValueError as e:
        logger.error(f"Trends validation error: {e}")
        error_result = TrendsOutput(
            success=False,
            years_analyzed=0,
            error=str(e),
            error_type="validation"
        )
        return error_result.model_dump_json(indent=2)
        
    except Exception as e:
        logger.error(f"Unexpected trends error: {e}", exc_info=True)
        error_result = TrendsOutput(
            success=False,
            years_analyzed=0,
            error="Erreur inattendue lors de l'analyse des tendances. Veuillez réessayer.",
            error_type="unknown"
        )
        return error_result.model_dump_json(indent=2)


# Create the StructuredTool
analyze_trends_tool_enhanced = StructuredTool.from_function(
    func=analyze_trends_enhanced,
    name="analyze_trends",
    description="""Analyse les tendances année par année des données d'exploitation.

Retourne une analyse détaillée avec:
- Métriques annuelles (rendement, coûts, qualité)
- Tendances globales (hausse, baisse, stable)
- Tendances par culture
- Insights et recommandations

Utilisez cet outil quand les agriculteurs veulent voir l'évolution de leurs performances dans le temps.""",
    args_schema=TrendsInput,
    return_direct=False,
    coroutine=analyze_trends_enhanced,
    handle_validation_error=True
)

