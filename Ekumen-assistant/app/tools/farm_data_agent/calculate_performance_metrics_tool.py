"""
Enhanced Calculate Performance Metrics Tool.

Improvements:
- Type-safe Pydantic schemas
- Redis caching (30min TTL for metrics)
- Structured error handling
- Direct database integration
- Comprehensive metrics calculation
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from langchain.tools import StructuredTool

from app.tools.schemas.farm_data_schemas import (
    PerformanceMetricsInput,
    PerformanceMetricsOutput,
    OverallMetrics,
    CropMetrics,
    TimePeriod,
    TrendDirection
)
from app.core.cache import redis_cache
from app.tools.farm_data_agent.get_farm_data_tool import FarmDataService

logger = logging.getLogger(__name__)


class PerformanceMetricsService:
    """Service for calculating performance metrics with caching"""

    @redis_cache(ttl=1800, model_class=PerformanceMetricsOutput, category="farm_data")
    async def calculate_metrics(self, input_data: PerformanceMetricsInput) -> PerformanceMetricsOutput:
        """
        Calculate performance metrics from farm data
        
        Args:
            input_data: Validated input
            
        Returns:
            PerformanceMetricsOutput with calculated metrics
            
        Raises:
            ValueError: If calculation fails
        """
        try:
            # Get farm data first
            from app.tools.schemas.farm_data_schemas import FarmDataInput
            farm_data_service = FarmDataService()
            farm_data_input = FarmDataInput(
                time_period=input_data.time_period,
                crops=input_data.crops,
                parcels=input_data.parcels,
                farm_id=input_data.farm_id,
                use_mesparcelles=False  # Don't need API data for metrics
            )
            farm_data = await farm_data_service.get_farm_data(farm_data_input)
            
            if not farm_data.success or not farm_data.database_records:
                return PerformanceMetricsOutput(
                    success=False,
                    total_records=0,
                    error="Aucune donnée disponible pour le calcul des métriques",
                    error_type="no_data"
                )
            
            records = farm_data.database_records
            
            # Calculate overall metrics
            overall_metrics = self._calculate_overall_metrics(records)
            
            # Calculate crop-specific metrics
            crop_metrics = self._calculate_crop_metrics(records)
            
            # Calculate parcel metrics
            parcel_metrics = self._calculate_parcel_metrics(records)
            
            logger.info(f"✅ Calculated metrics for {len(records)} records")
            
            return PerformanceMetricsOutput(
                success=True,
                overall_metrics=overall_metrics,
                crop_metrics=crop_metrics,
                parcel_metrics=parcel_metrics,
                total_records=len(records)
            )
            
        except Exception as e:
            logger.error(f"Performance metrics calculation error: {e}", exc_info=True)
            raise ValueError(f"Erreur lors du calcul des métriques: {str(e)}")

    def _calculate_overall_metrics(self, records: List[Any]) -> OverallMetrics:
        """
        Calculate overall performance metrics from REAL intervention data.

        Uses intervention_summary from each record to extract:
        - Real yield data from harvest interventions
        - Real cost data from input costs (when available)
        - Returns None for missing data instead of mock values
        """
        if not records:
            raise ValueError("No records provided")

        total_surface = sum(r.surface_ha for r in records)
        if total_surface == 0:
            raise ValueError("Total surface is zero")

        # Extract real data from intervention summaries
        total_yield_q = 0.0
        total_cost_eur = 0.0
        records_with_yield = 0
        records_with_cost = 0

        for record in records:
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
        average_yield_q_ha = None
        if records_with_yield > 0:
            average_yield_q_ha = round(total_yield_q / total_surface, 2)

        average_cost_eur_ha = None
        if records_with_cost > 0:
            average_cost_eur_ha = round(total_cost_eur / total_surface, 2)

        # Quality score not available from current data
        # TODO: Add quality tracking to interventions
        average_quality_score = None

        # Yield trend not calculable without historical data
        yield_trend = TrendDirection.INSUFFICIENT_DATA

        return OverallMetrics(
            total_surface_ha=round(total_surface, 2),
            average_yield_q_ha=average_yield_q_ha,
            total_cost_eur=round(total_cost_eur, 2) if records_with_cost > 0 else None,
            average_cost_eur_ha=average_cost_eur_ha,
            average_quality_score=average_quality_score,
            yield_trend=yield_trend,
            record_count=len(records)
        )

    def _calculate_crop_metrics(self, records: List[Any]) -> Dict[str, CropMetrics]:
        """
        Calculate metrics by crop using REAL intervention data.

        Returns None for metrics where no real data is available.
        """
        crop_data: Dict[str, List[Any]] = {}

        for record in records:
            for culture in record.cultures:
                if culture not in crop_data:
                    crop_data[culture] = []
                crop_data[culture].append(record)

        crop_metrics = {}
        for crop, crop_records in crop_data.items():
            total_surface = sum(r.surface_ha for r in crop_records)

            # Extract real data from intervention summaries
            total_yield_q = 0.0
            total_cost_eur = 0.0
            records_with_yield = 0
            records_with_cost = 0

            for record in crop_records:
                if record.intervention_summary:
                    summary = record.intervention_summary

                    if summary.average_yield_q_ha is not None:
                        total_yield_q += summary.average_yield_q_ha * record.surface_ha
                        records_with_yield += 1

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

            # Quality not available
            average_quality = None

            crop_metrics[crop] = CropMetrics(
                total_surface=round(total_surface, 2),
                average_yield=average_yield,
                average_cost=average_cost,
                average_quality=average_quality,
                record_count=len(crop_records)
            )
        
        return crop_metrics

    def _calculate_parcel_metrics(self, records: List[Any]) -> Dict[str, CropMetrics]:
        """
        Calculate metrics by parcel using REAL intervention data.

        Returns None for metrics where no real data is available.
        """
        parcel_metrics = {}

        for record in records:
            parcel = record.parcel

            # Extract real data from intervention summary
            average_yield = None
            average_cost = None
            average_quality = None

            if record.intervention_summary:
                summary = record.intervention_summary
                average_yield = summary.average_yield_q_ha
                average_cost = summary.average_cost_eur_ha
                # Quality not available

            parcel_metrics[parcel] = CropMetrics(
                total_surface=round(record.surface_ha, 2),
                average_yield=average_yield,
                average_cost=average_cost,
                average_quality=average_quality,
                record_count=1
            )

        return parcel_metrics


async def calculate_performance_metrics_enhanced(
    farm_id: Optional[str] = None,
    time_period: Optional[str] = None,
    crops: Optional[List[str]] = None,
    parcels: Optional[List[str]] = None
) -> str:
    """
    Async wrapper for calculate performance metrics tool
    
    Args:
        farm_id: Farm ID (SIRET) to calculate metrics for
        time_period: Time period for metrics calculation
        crops: Specific crops to analyze
        parcels: Specific parcels to analyze
        
    Returns:
        JSON string with performance metrics
    """
    try:
        # Validate inputs
        input_data = PerformanceMetricsInput(
            farm_id=farm_id,
            time_period=TimePeriod(time_period) if time_period else None,
            crops=crops,
            parcels=parcels
        )
        
        # Execute service
        service = PerformanceMetricsService()
        result = await service.calculate_metrics(input_data)
        
        # Return as JSON
        return result.model_dump_json(indent=2, exclude_none=True)
        
    except ValueError as e:
        logger.error(f"Performance metrics validation error: {e}")
        error_result = PerformanceMetricsOutput(
            success=False,
            total_records=0,
            error=str(e),
            error_type="validation"
        )
        return error_result.model_dump_json(indent=2)
        
    except Exception as e:
        logger.error(f"Unexpected performance metrics error: {e}", exc_info=True)
        error_result = PerformanceMetricsOutput(
            success=False,
            total_records=0,
            error="Erreur inattendue lors du calcul des métriques. Veuillez réessayer.",
            error_type="unknown"
        )
        return error_result.model_dump_json(indent=2)


# Create the StructuredTool
calculate_performance_metrics_tool = StructuredTool.from_function(
    func=calculate_performance_metrics_enhanced,
    name="calculate_performance_metrics",
    description="""Calcule les métriques de performance à partir des données d'exploitation.

Retourne des métriques détaillées avec:
- Métriques globales (rendement, coûts, qualité)
- Métriques par culture
- Métriques par parcelle
- Tendances de performance

Utilisez cet outil quand les agriculteurs demandent leurs performances, rendements, ou coûts.""",
    args_schema=PerformanceMetricsInput,
    return_direct=False,
    coroutine=calculate_performance_metrics_enhanced,
    handle_validation_error=True
)

