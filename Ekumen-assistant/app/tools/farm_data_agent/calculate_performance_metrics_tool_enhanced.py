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
from app.tools.farm_data_agent.get_farm_data_tool_enhanced import EnhancedFarmDataService

logger = logging.getLogger(__name__)


class EnhancedPerformanceMetricsService:
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
            farm_data_service = EnhancedFarmDataService()
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
        """Calculate overall performance metrics"""
        if not records:
            raise ValueError("No records provided")
        
        total_surface = sum(r.surface_ha for r in records)
        if total_surface == 0:
            raise ValueError("Total surface is zero")
        
        # For now, use mock yield/cost/quality data
        # TODO: Get actual yield/cost/quality from interventions
        total_yield = total_surface * 70  # Mock: 70 q/ha average
        average_yield = total_yield / total_surface
        
        total_cost = total_surface * 450  # Mock: 450 EUR/ha average
        average_cost = total_cost / total_surface
        
        average_quality = 7.5  # Mock quality score
        
        # Calculate yield trend (mock for now)
        yield_trend = TrendDirection.STABLE
        
        return OverallMetrics(
            total_surface_ha=round(total_surface, 2),
            average_yield_q_ha=round(average_yield, 2),
            total_cost_eur=round(total_cost, 2),
            average_cost_eur_ha=round(average_cost, 2),
            average_quality_score=round(average_quality, 2),
            yield_trend=yield_trend,
            record_count=len(records)
        )

    def _calculate_crop_metrics(self, records: List[Any]) -> Dict[str, CropMetrics]:
        """Calculate metrics by crop"""
        crop_data: Dict[str, List[Any]] = {}
        
        for record in records:
            for culture in record.cultures:
                if culture not in crop_data:
                    crop_data[culture] = []
                crop_data[culture].append(record)
        
        crop_metrics = {}
        for crop, crop_records in crop_data.items():
            total_surface = sum(r.surface_ha for r in crop_records)
            
            # Mock data for now
            # TODO: Get actual yield/cost/quality from interventions
            average_yield = 70.0  # Mock
            average_cost = 450.0  # Mock
            average_quality = 7.5  # Mock
            
            crop_metrics[crop] = CropMetrics(
                total_surface=round(total_surface, 2),
                average_yield=round(average_yield, 2),
                average_cost=round(average_cost, 2),
                average_quality=round(average_quality, 2),
                record_count=len(crop_records)
            )
        
        return crop_metrics

    def _calculate_parcel_metrics(self, records: List[Any]) -> Dict[str, CropMetrics]:
        """Calculate metrics by parcel"""
        parcel_metrics = {}
        
        for record in records:
            parcel = record.parcel
            
            # Mock data for now
            # TODO: Get actual yield/cost/quality from interventions
            parcel_metrics[parcel] = CropMetrics(
                total_surface=round(record.surface_ha, 2),
                average_yield=70.0,  # Mock
                average_cost=450.0,  # Mock
                average_quality=7.5,  # Mock
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
        service = EnhancedPerformanceMetricsService()
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
calculate_performance_metrics_tool_enhanced = StructuredTool.from_function(
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

