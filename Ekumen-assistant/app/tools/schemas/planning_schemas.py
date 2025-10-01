"""
Pydantic schemas for planning agent tools.

Provides type-safe input/output schemas for:
- Crop feasibility checking
- Planning task generation
- Task sequence optimization
- Cost calculation
- Resource requirements analysis
- Planning report generation
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


# ============================================================================
# CHECK CROP FEASIBILITY TOOL SCHEMAS
# ============================================================================

class CropFeasibilityInput(BaseModel):
    """Input schema for check crop feasibility tool"""
    
    crop: str = Field(
        min_length=1,
        max_length=100,
        description="Crop name (e.g., 'blé', 'maïs', 'café')"
    )
    location: str = Field(
        min_length=1,
        max_length=100,
        description="Location name (e.g., 'Dourdan', 'Paris', 'Marseille')"
    )
    include_alternatives: bool = Field(
        default=True,
        description="Whether to include alternative crop suggestions"
    )


class ClimateData(BaseModel):
    """Climate data for a location"""
    
    location_details: Dict[str, Any] = Field(default_factory=dict)
    temp_min_annual: float = Field(description="Minimum annual temperature in °C")
    temp_max_annual: float = Field(description="Maximum annual temperature in °C")
    frost_days: int = Field(ge=0, description="Number of frost days per year")
    growing_season_length: int = Field(ge=0, description="Growing season length in days")
    hardiness_zone: str = Field(description="USDA hardiness zone")


class CropRequirements(BaseModel):
    """Crop climate requirements"""
    
    temp_min: float = Field(description="Minimum temperature tolerance in °C")
    temp_max: float = Field(description="Maximum temperature tolerance in °C")
    frost_tolerance: bool = Field(description="Whether crop tolerates frost")
    climate_type: str = Field(description="Required climate type")
    hardiness_zone: str = Field(description="Required USDA hardiness zone")


class AlternativeCrop(BaseModel):
    """Alternative crop suggestion"""
    
    name: str = Field(description="Crop name")
    hardiness_zone: str = Field(description="USDA hardiness zone")
    description: str = Field(description="Description of the alternative")


class Source(BaseModel):
    """Data source reference"""
    
    title: str = Field(description="Source title")
    url: str = Field(description="Source URL")
    snippet: str = Field(description="Relevant snippet from source")
    relevance: float = Field(ge=0.0, le=1.0, description="Relevance score")
    type: str = Field(description="Source type (database, api, etc.)")


class CropFeasibilityOutput(BaseModel):
    """Output schema for check crop feasibility tool"""
    
    success: bool = Field(default=True)
    crop: str = Field(description="Crop analyzed")
    location: str = Field(description="Location analyzed")
    is_feasible: Optional[bool] = Field(default=None, description="Whether crop is feasible")
    feasibility_score: Optional[float] = Field(default=None, ge=0.0, le=10.0, description="Feasibility score (0-10)")
    limiting_factors: List[str] = Field(default_factory=list, description="Factors limiting feasibility")
    climate_data: Optional[ClimateData] = None
    crop_requirements: Optional[CropRequirements] = None
    alternatives: List[AlternativeCrop] = Field(default_factory=list, description="Alternative crop suggestions")
    indoor_cultivation: Optional[bool] = Field(default=None, description="Whether indoor cultivation is possible")
    recommendations: List[str] = Field(default_factory=list, description="Cultivation recommendations")
    sources: List[Source] = Field(default_factory=list, description="Data sources used")
    warnings: List[str] = Field(default_factory=list, description="Data quality and analysis warnings")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    error: Optional[str] = None
    error_type: Optional[str] = None


# ============================================================================
# GENERATE PLANNING TASKS TOOL SCHEMAS
# ============================================================================

class TaskPriority(str, Enum):
    """Task priority levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskStatus(str, Enum):
    """Task status"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PlanningTasksInput(BaseModel):
    """Input schema for generate planning tasks tool"""
    
    crop: str = Field(
        min_length=1,
        max_length=100,
        description="Crop name"
    )
    surface_ha: float = Field(
        gt=0,
        le=10000,
        description="Surface area in hectares"
    )
    start_date: Optional[str] = Field(
        default=None,
        description="Start date (ISO format)"
    )
    organic: bool = Field(
        default=False,
        description="Whether organic farming"
    )


class PlanningTask(BaseModel):
    """Individual planning task"""
    
    task_id: str = Field(description="Unique task identifier")
    task_name: str = Field(description="Task name")
    description: str = Field(description="Task description")
    priority: TaskPriority = Field(description="Task priority")
    estimated_duration_days: int = Field(ge=1, description="Estimated duration in days")
    dependencies: List[str] = Field(default_factory=list, description="Task IDs this task depends on")
    resources_required: List[str] = Field(default_factory=list, description="Required resources")
    optimal_period: Optional[str] = Field(default=None, description="Optimal time period for task")
    status: TaskStatus = Field(default=TaskStatus.PENDING)


class PlanningTasksOutput(BaseModel):
    """Output schema for generate planning tasks tool"""
    
    success: bool = Field(default=True)
    crop: str
    surface_ha: float
    tasks: List[PlanningTask] = Field(default_factory=list)
    total_tasks: int = Field(ge=0)
    estimated_total_duration_days: int = Field(ge=0)
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    error: Optional[str] = None
    error_type: Optional[str] = None


# ============================================================================
# OPTIMIZE TASK SEQUENCE TOOL SCHEMAS
# ============================================================================

class OptimizationConstraint(str, Enum):
    """Optimization constraints"""
    TIME = "time"
    COST = "cost"
    RESOURCES = "resources"
    WEATHER = "weather"


class TaskSequenceInput(BaseModel):
    """Input schema for optimize task sequence tool"""
    
    tasks: List[Dict[str, Any]] = Field(
        min_items=1,
        description="List of tasks to optimize"
    )
    optimization_goal: OptimizationConstraint = Field(
        default=OptimizationConstraint.TIME,
        description="Primary optimization goal"
    )
    constraints: List[str] = Field(
        default_factory=list,
        description="Additional constraints"
    )


class OptimizedTask(BaseModel):
    """Optimized task with sequence information"""
    
    task_id: str
    task_name: str
    sequence_order: int = Field(ge=1, description="Order in optimized sequence")
    start_day: int = Field(ge=0, description="Start day in sequence")
    end_day: int = Field(ge=0, description="End day in sequence")
    parallel_tasks: List[str] = Field(default_factory=list, description="Tasks that can run in parallel")


class TaskSequenceOutput(BaseModel):
    """Output schema for optimize task sequence tool"""
    
    success: bool = Field(default=True)
    optimized_tasks: List[OptimizedTask] = Field(default_factory=list)
    total_duration_days: int = Field(ge=0)
    optimization_goal: str
    efficiency_gain_percent: Optional[float] = Field(default=None, description="Efficiency gain vs sequential")
    warnings: List[str] = Field(default_factory=list)
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    error: Optional[str] = None
    error_type: Optional[str] = None


# ============================================================================
# CALCULATE PLANNING COSTS TOOL SCHEMAS
# ============================================================================

class CostCategory(str, Enum):
    """Cost categories"""
    SEEDS = "seeds"
    FERTILIZER = "fertilizer"
    PESTICIDES = "pesticides"
    LABOR = "labor"
    EQUIPMENT = "equipment"
    OTHER = "other"


class PlanningCostsInput(BaseModel):
    """Input schema for calculate planning costs tool"""
    
    crop: str = Field(min_length=1, max_length=100)
    surface_ha: float = Field(gt=0, le=10000)
    tasks: List[Dict[str, Any]] = Field(min_items=1)
    include_labor: bool = Field(default=True)


class CostBreakdown(BaseModel):
    """Cost breakdown by category"""
    
    category: CostCategory
    amount_eur: float = Field(ge=0)
    description: str


class PlanningCostsOutput(BaseModel):
    """Output schema for calculate planning costs tool"""

    success: bool = Field(default=True)
    crop: str
    surface_ha: float
    total_cost_eur: float = Field(ge=0)
    cost_per_ha_eur: float = Field(ge=0)
    cost_breakdown: List[CostBreakdown] = Field(default_factory=list)
    estimated_revenue_eur: Optional[float] = Field(default=None, ge=0)
    estimated_profit_eur: Optional[float] = None
    roi_percent: Optional[float] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    error: Optional[str] = None
    error_type: Optional[str] = None


# ============================================================================
# ANALYZE RESOURCE REQUIREMENTS TOOL SCHEMAS
# ============================================================================

class ResourceType(str, Enum):
    """Resource types"""
    EQUIPMENT = "equipment"
    LABOR = "labor"
    MATERIALS = "materials"
    WATER = "water"
    ENERGY = "energy"


class ResourceRequirement(BaseModel):
    """Individual resource requirement"""

    resource_type: ResourceType
    resource_name: str
    quantity: float = Field(ge=0)
    unit: str
    timing: Optional[str] = Field(default=None, description="When resource is needed")
    critical: bool = Field(default=False, description="Whether resource is critical")


class ResourceRequirementsInput(BaseModel):
    """Input schema for analyze resource requirements tool"""

    crop: str = Field(min_length=1, max_length=100)
    surface_ha: float = Field(gt=0, le=10000)
    tasks: List[Dict[str, Any]] = Field(min_items=1)


class ResourceRequirementsOutput(BaseModel):
    """Output schema for analyze resource requirements tool"""

    success: bool = Field(default=True)
    crop: str
    surface_ha: float
    resource_requirements: List[ResourceRequirement] = Field(default_factory=list)
    total_resources: int = Field(ge=0)
    critical_resources: List[str] = Field(default_factory=list)
    resource_availability_warnings: List[str] = Field(default_factory=list)
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    error: Optional[str] = None
    error_type: Optional[str] = None


# ============================================================================
# GENERATE PLANNING REPORT TOOL SCHEMAS
# ============================================================================

class PlanningReportInput(BaseModel):
    """Input schema for generate planning report tool"""

    crop: str = Field(min_length=1, max_length=100)
    surface_ha: float = Field(gt=0, le=10000)
    location: Optional[str] = Field(default=None, max_length=100)
    include_costs: bool = Field(default=True)
    include_resources: bool = Field(default=True)
    include_feasibility: bool = Field(default=False)


class PlanningReportSummary(BaseModel):
    """Planning report executive summary"""

    crop: str
    surface_ha: float
    total_tasks: int = Field(ge=0)
    total_duration_days: int = Field(ge=0)
    total_cost_eur: Optional[float] = Field(default=None, ge=0)
    feasibility_score: Optional[float] = Field(default=None, ge=0.0, le=10.0)
    is_feasible: Optional[bool] = None


class PlanningReportOutput(BaseModel):
    """Output schema for generate planning report tool"""

    success: bool = Field(default=True)
    crop: str
    surface_ha: float
    location: Optional[str] = None
    generated_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    summary: Optional[PlanningReportSummary] = None
    tasks_analysis: Optional[Dict[str, Any]] = None
    cost_analysis: Optional[Dict[str, Any]] = None
    resource_analysis: Optional[Dict[str, Any]] = None
    feasibility_analysis: Optional[Dict[str, Any]] = None
    recommendations: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    error: Optional[str] = None
    error_type: Optional[str] = None

