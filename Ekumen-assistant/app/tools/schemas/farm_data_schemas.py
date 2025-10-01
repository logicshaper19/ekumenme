"""
Pydantic schemas for Farm Data Agent tools.

All schemas follow the pattern:
- Input schemas with Field validation
- Output schemas with success/error fields
- Nested models for complex data structures
"""

from pydantic import BaseModel, Field, validator
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class TimePeriod(str, Enum):
    """Time period filter options"""
    CURRENT_YEAR = "current_year"
    PREVIOUS_YEAR = "previous_year"
    LAST_SEASON = "last_season"
    LAST_3_YEARS = "last_3_years"
    ALL_TIME = "all_time"


class TrendDirection(str, Enum):
    """Trend direction"""
    INCREASING = "increasing"
    DECREASING = "decreasing"
    STABLE = "stable"
    INSUFFICIENT_DATA = "insufficient_data"


class PerformanceRank(str, Enum):
    """
    Performance ranking based on % of national average.

    WARNING: These are NOT percentile ranks!
    Being 110% of average ≠ top 10% of farms.
    Actual percentile depends on distribution variance.
    """
    EXCEPTIONAL = "exceptional"          # >110% of average
    EXCELLENT = "excellent"              # >100% of average
    ABOVE_AVERAGE = "above_average"      # >90% of average
    AVERAGE = "average"                  # 80-90% of average
    BELOW_AVERAGE = "below_average"      # <80% of average


# ============================================================================
# GET FARM DATA TOOL SCHEMAS
# ============================================================================

class FarmDataInput(BaseModel):
    """Input schema for get farm data tool"""
    
    time_period: Optional[TimePeriod] = Field(
        default=None,
        description="Time period filter (e.g., 'current_year', 'last_season')"
    )
    crops: Optional[List[str]] = Field(
        default=None,
        description="List of crop types to filter by",
        max_items=20
    )
    parcels: Optional[List[str]] = Field(
        default=None,
        description="List of parcel IDs to filter by",
        max_items=50
    )
    farm_id: Optional[str] = Field(
        default=None,
        description="Specific farm ID (SIRET) for targeted data retrieval",
        min_length=14,
        max_length=14
    )
    use_mesparcelles: bool = Field(
        default=True,
        description="Whether to include MesParcelles API data"
    )


class InterventionSummary(BaseModel):
    """Summary of interventions for a parcel"""
    total_interventions: int = Field(ge=0)
    harvest_interventions: int = Field(ge=0)
    fertilization_interventions: int = Field(ge=0)
    pest_control_interventions: int = Field(ge=0)
    total_harvest_quantity: Optional[float] = Field(default=None, description="Total harvest in kg")
    average_yield_q_ha: Optional[float] = Field(default=None, description="Average yield in quintals/ha")
    total_cost_eur: Optional[float] = Field(default=None, description="Total cost in EUR")
    average_cost_eur_ha: Optional[float] = Field(default=None, description="Average cost per hectare")
    has_real_data: bool = Field(default=False, description="Whether data is from real interventions or estimated")


class ParcelRecord(BaseModel):
    """Individual parcel record"""
    id: str
    farm_id: Optional[str] = None
    parcel: str
    millesime: int
    surface_ha: float = Field(ge=0, le=10000)
    commune: Optional[str] = None
    cultures: List[str] = Field(default_factory=list)
    nb_interventions: int = Field(ge=0)
    intervention_summary: Optional[InterventionSummary] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class FarmDataOutput(BaseModel):
    """Output schema for get farm data tool"""

    success: bool = Field(default=True)
    database_records: List[ParcelRecord] = Field(default_factory=list)
    total_records: int = Field(ge=0)
    total_available: Optional[int] = Field(default=None, description="Total parcels available before pagination")
    filters: Dict[str, Any] = Field(default_factory=dict)
    data_sources: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list, description="Data quality and pagination warnings")
    mesparcelles_data: Optional[Dict[str, Any]] = None
    mesparcelles_error: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    error: Optional[str] = None
    error_type: Optional[str] = None


# ============================================================================
# CALCULATE PERFORMANCE METRICS TOOL SCHEMAS
# ============================================================================

class PerformanceMetricsInput(BaseModel):
    """Input schema for calculate performance metrics tool"""
    
    farm_id: Optional[str] = Field(
        default=None,
        description="Farm ID (SIRET) to calculate metrics for"
    )
    time_period: Optional[TimePeriod] = Field(
        default=None,
        description="Time period for metrics calculation"
    )
    crops: Optional[List[str]] = Field(
        default=None,
        description="Specific crops to analyze"
    )
    parcels: Optional[List[str]] = Field(
        default=None,
        description="Specific parcels to analyze"
    )


class OverallMetrics(BaseModel):
    """
    Overall performance metrics.

    Fields are Optional to support cases where real data is not available.
    None values indicate missing data rather than zero values.
    """
    total_surface_ha: float = Field(ge=0)
    average_yield_q_ha: Optional[float] = Field(default=None, ge=0, description="None if no harvest data available")
    total_cost_eur: Optional[float] = Field(default=None, ge=0, description="None if no cost data available")
    average_cost_eur_ha: Optional[float] = Field(default=None, ge=0, description="None if no cost data available")
    average_quality_score: Optional[float] = Field(default=None, ge=0, le=10, description="None if no quality data available")
    yield_trend: TrendDirection
    record_count: int = Field(ge=0)


class CropMetrics(BaseModel):
    """
    Metrics for a specific crop.

    Fields are Optional to support cases where real data is not available.
    None values indicate missing data rather than zero values.
    """
    total_surface: float = Field(ge=0)
    average_yield: Optional[float] = Field(default=None, ge=0, description="None if no harvest data available")
    average_cost: Optional[float] = Field(default=None, ge=0, description="None if no cost data available")
    average_quality: Optional[float] = Field(default=None, ge=0, le=10, description="None if no quality data available")
    record_count: int = Field(ge=0)


class PerformanceMetricsOutput(BaseModel):
    """Output schema for calculate performance metrics tool"""
    
    success: bool = Field(default=True)
    overall_metrics: Optional[OverallMetrics] = None
    crop_metrics: Dict[str, CropMetrics] = Field(default_factory=dict)
    parcel_metrics: Dict[str, CropMetrics] = Field(default_factory=dict)
    total_records: int = Field(ge=0)
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    error: Optional[str] = None
    error_type: Optional[str] = None


# ============================================================================
# BENCHMARK CROP PERFORMANCE TOOL SCHEMAS
# ============================================================================

class BenchmarkInput(BaseModel):
    """Input schema for benchmark crop performance tool"""
    
    crop: str = Field(
        description="Crop type to benchmark",
        min_length=1,
        max_length=100
    )
    farm_id: Optional[str] = Field(
        default=None,
        description="Farm ID to benchmark"
    )
    time_period: Optional[TimePeriod] = Field(
        default=None,
        description="Time period for benchmark"
    )


class IndustryBenchmark(BaseModel):
    """Industry benchmark data"""
    yield_q_ha: float = Field(ge=0, description="Industry average yield in quintals/ha")
    quality_score: float = Field(ge=0, le=10, description="Industry average quality score")


class PerformanceMetrics(BaseModel):
    """
    Performance metrics compared to benchmark.

    quality_performance_percent is Optional because quality data may not be available.
    """
    yield_performance_percent: float
    quality_performance_percent: Optional[float] = Field(default=None, description="None if no quality data available")
    overall_performance_percent: float


class BenchmarkOutput(BaseModel):
    """Output schema for benchmark crop performance tool"""

    success: bool = Field(default=True)
    crop: str
    farm_performance: Dict[str, Optional[float]] = Field(default_factory=dict)
    industry_benchmark: Optional[IndustryBenchmark] = None
    performance_metrics: Optional[PerformanceMetrics] = None
    performance_rank: Optional[PerformanceRank] = None
    benchmark_insights: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list, description="Data quality warnings")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    error: Optional[str] = None
    error_type: Optional[str] = None


# ============================================================================
# ANALYZE TRENDS TOOL SCHEMAS
# ============================================================================

class TrendsInput(BaseModel):
    """Input schema for analyze trends tool"""
    
    farm_id: Optional[str] = Field(
        default=None,
        description="Farm ID to analyze trends for"
    )
    crops: Optional[List[str]] = Field(
        default=None,
        description="Specific crops to analyze trends for"
    )
    min_years: int = Field(
        default=2,
        ge=2,
        le=10,
        description="Minimum number of years required for trend analysis"
    )


class TrendMetrics(BaseModel):
    """Trend metrics for a specific metric"""
    change_percent: float
    trend_direction: TrendDirection
    first_year_value: float
    last_year_value: float


class YearlyMetrics(BaseModel):
    """
    Metrics for a specific year.

    Fields are Optional to handle missing real data honestly.
    """
    average_yield: Optional[float] = Field(default=None, ge=0, description="None if no harvest data available")
    average_cost: Optional[float] = Field(default=None, ge=0, description="None if no cost data available")
    average_quality: Optional[float] = Field(default=None, ge=0, le=10, description="None if no quality data available")
    total_surface: float = Field(ge=0)
    record_count: int = Field(ge=0)


class TrendsOutput(BaseModel):
    """
    Output schema for analyze trends tool.

    Trend fields are Optional to handle missing real data honestly.
    Warnings field alerts users to data quality issues.
    """

    success: bool = Field(default=True)
    yearly_metrics: Dict[str, YearlyMetrics] = Field(default_factory=dict)
    yield_trend: Optional[TrendMetrics] = Field(default=None, description="None if no yield data available")
    cost_trend: Optional[TrendMetrics] = Field(default=None, description="None if no cost data available")
    quality_trend: Optional[TrendMetrics] = Field(default=None, description="None if no quality data available")
    crop_trends: Dict[str, Dict[str, TrendMetrics]] = Field(default_factory=dict)
    trend_insights: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list, description="Data quality warnings")
    years_analyzed: int = Field(ge=0)
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    error: Optional[str] = None
    error_type: Optional[str] = None


# ============================================================================
# GENERATE FARM REPORT TOOL SCHEMAS
# ============================================================================

class FarmReportInput(BaseModel):
    """Input schema for generate farm report tool"""
    
    farm_id: str = Field(
        description="Farm ID (SIRET) to generate report for",
        min_length=14,
        max_length=14
    )
    time_period: Optional[TimePeriod] = Field(
        default=TimePeriod.CURRENT_YEAR,
        description="Time period for report"
    )
    include_benchmarks: bool = Field(
        default=True,
        description="Whether to include benchmark analysis"
    )
    include_trends: bool = Field(
        default=True,
        description="Whether to include trend analysis"
    )


class ExecutiveSummary(BaseModel):
    """Executive summary for farm report"""
    total_records: int = Field(ge=0)
    total_surface_ha: float = Field(ge=0)
    average_yield_q_ha: Optional[float] = None
    average_cost_eur_ha: Optional[float] = None
    average_quality_score: Optional[float] = None
    performance_rank: Optional[PerformanceRank] = None
    overall_performance_percent: Optional[float] = None
    yield_trend: Optional[TrendDirection] = None
    cost_trend: Optional[TrendDirection] = None


class FarmReportOutput(BaseModel):
    """Output schema for generate farm report tool"""
    
    success: bool = Field(default=True)
    farm_id: str
    report_period: str
    generated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    executive_summary: Optional[ExecutiveSummary] = None
    data_overview: Dict[str, Any] = Field(default_factory=dict)
    performance_analysis: Optional[Dict[str, Any]] = None
    benchmark_analysis: Optional[Dict[str, Any]] = None
    trend_analysis: Optional[Dict[str, Any]] = None
    recommendations: List[str] = Field(default_factory=list)
    error: Optional[str] = None
    error_type: Optional[str] = None

