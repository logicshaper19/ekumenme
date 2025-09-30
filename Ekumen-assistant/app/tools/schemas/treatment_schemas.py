"""
Pydantic schemas for treatment plan generation

Provides type-safe input/output schemas for comprehensive treatment planning with:
- Treatment plan input/output
- Integration with disease, pest, and nutrient analyses
- Crop-specific recommendations
- Cost analysis
- Monitoring plans
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any, Union
from enum import Enum
from datetime import datetime
from .disease_schemas import DiseaseDiagnosisOutput
from .pest_schemas import PestIdentificationOutput


class TreatmentPriority(str, Enum):
    """Treatment priority levels"""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class TreatmentType(str, Enum):
    """Treatment types"""
    CHEMICAL = "chemical"
    BIOLOGICAL = "biological"
    CULTURAL = "cultural"
    MECHANICAL = "mechanical"
    INTEGRATED = "integrated"


class TreatmentTiming(str, Enum):
    """Treatment timing"""
    IMMEDIATE = "immediate"
    WITHIN_24H = "within_24h"
    WITHIN_WEEK = "within_week"
    SCHEDULED = "scheduled"
    PREVENTIVE = "preventive"


class TreatmentPlanInput(BaseModel):
    """Input schema for treatment plan generation"""
    
    crop_type: str = Field(
        description="Type of crop (e.g., 'blé', 'maïs', 'colza')"
    )
    eppo_code: Optional[str] = Field(
        default=None,
        description="EPPO code for crop"
    )
    disease_analysis: Optional[Union[DiseaseDiagnosisOutput, Dict[str, Any]]] = Field(
        default=None,
        description="Disease diagnosis output"
    )
    pest_analysis: Optional[Union[PestIdentificationOutput, Dict[str, Any]]] = Field(
        default=None,
        description="Pest identification output"
    )
    nutrient_analysis: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Nutrient deficiency analysis output"
    )
    bbch_stage: Optional[int] = Field(
        default=None,
        ge=0,
        le=99,
        description="Current BBCH growth stage"
    )
    field_size_ha: Optional[float] = Field(
        default=None,
        ge=0,
        description="Field size in hectares"
    )
    budget_constraint: Optional[float] = Field(
        default=None,
        ge=0,
        description="Budget constraint in euros"
    )
    organic_farming: Optional[bool] = Field(
        default=False,
        description="Whether organic farming practices are required"
    )
    
    @validator('crop_type')
    def validate_crop_type(cls, v):
        """Validate crop type"""
        if not v or not v.strip():
            raise ValueError("Crop type is required")
        return v.strip()
    
    class Config:
        use_enum_values = True
        arbitrary_types_allowed = True


class TreatmentStep(BaseModel):
    """Individual treatment step"""
    
    step_number: int = Field(ge=1, description="Step number in sequence")
    step_name: str = Field(description="Treatment step name")
    description: str = Field(description="Detailed description")
    treatment_type: TreatmentType = Field(description="Type of treatment")
    priority: TreatmentPriority = Field(description="Priority level")
    timing: TreatmentTiming = Field(description="When to apply treatment")
    target_issue: str = Field(description="Target disease/pest/deficiency")
    products: Optional[List[str]] = Field(
        default=None,
        description="Recommended products"
    )
    dosage: Optional[str] = Field(
        default=None,
        description="Application dosage"
    )
    application_method: Optional[str] = Field(
        default=None,
        description="Application method"
    )
    cost_estimate_eur: Optional[float] = Field(
        default=None,
        ge=0,
        description="Estimated cost in euros"
    )
    effectiveness_rating: Optional[str] = Field(
        default=None,
        description="Expected effectiveness (low, moderate, high)"
    )
    safety_precautions: Optional[List[str]] = Field(
        default=None,
        description="Safety precautions"
    )
    weather_requirements: Optional[str] = Field(
        default=None,
        description="Weather requirements for application"
    )
    
    class Config:
        use_enum_values = True


class TreatmentSchedule(BaseModel):
    """Treatment schedule entry"""
    
    scheduled_date: Optional[str] = Field(
        default=None,
        description="Scheduled date (ISO format or relative like 'immediate')"
    )
    treatment_steps: List[int] = Field(
        description="Step numbers to execute on this date"
    )
    weather_dependent: bool = Field(
        default=False,
        description="Whether timing depends on weather"
    )
    bbch_stage_dependent: bool = Field(
        default=False,
        description="Whether timing depends on BBCH stage"
    )
    notes: Optional[str] = Field(
        default=None,
        description="Additional notes"
    )
    
    class Config:
        use_enum_values = True


class CostAnalysis(BaseModel):
    """Cost analysis for treatment plan"""
    
    total_estimated_cost_eur: float = Field(
        ge=0,
        description="Total estimated cost in euros"
    )
    cost_per_hectare_eur: Optional[float] = Field(
        default=None,
        ge=0,
        description="Cost per hectare"
    )
    cost_breakdown: Dict[str, float] = Field(
        description="Cost breakdown by category"
    )
    budget_status: Optional[str] = Field(
        default=None,
        description="Budget status (within_budget, over_budget, no_budget_set)"
    )
    cost_optimization_suggestions: Optional[List[str]] = Field(
        default=None,
        description="Suggestions for cost optimization"
    )
    
    class Config:
        use_enum_values = True


class MonitoringPlan(BaseModel):
    """Monitoring plan for treatment effectiveness"""
    
    monitoring_frequency: str = Field(
        description="How often to monitor (daily, weekly, etc.)"
    )
    monitoring_methods: List[str] = Field(
        description="Monitoring methods to use"
    )
    success_indicators: List[str] = Field(
        description="Indicators of treatment success"
    )
    warning_signs: List[str] = Field(
        description="Warning signs to watch for"
    )
    reassessment_date: Optional[str] = Field(
        default=None,
        description="When to reassess treatment plan"
    )
    
    class Config:
        use_enum_values = True


class TreatmentPlanOutput(BaseModel):
    """Output schema for treatment plan generation"""
    
    success: bool = Field(description="Whether plan generation was successful")
    crop_type: str = Field(description="Crop type")
    crop_eppo_code: Optional[str] = Field(
        default=None,
        description="EPPO code for crop"
    )
    plan_metadata: Dict[str, Any] = Field(
        description="Plan metadata (generated_at, version, etc.)"
    )
    executive_summary: Dict[str, Any] = Field(
        description="Executive summary of treatment plan"
    )
    treatment_steps: List[TreatmentStep] = Field(
        description="Detailed treatment steps"
    )
    treatment_schedule: List[TreatmentSchedule] = Field(
        description="Treatment schedule"
    )
    cost_analysis: CostAnalysis = Field(
        description="Cost analysis"
    )
    monitoring_plan: MonitoringPlan = Field(
        description="Monitoring plan"
    )
    prevention_measures: List[str] = Field(
        description="Long-term prevention measures"
    )
    total_steps: int = Field(
        ge=0,
        description="Total number of treatment steps"
    )
    estimated_duration_days: Optional[int] = Field(
        default=None,
        ge=0,
        description="Estimated treatment duration in days"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Plan generation timestamp"
    )
    error: Optional[str] = Field(
        default=None,
        description="Error message if plan generation failed"
    )
    error_type: Optional[str] = Field(
        default=None,
        description="Error type"
    )
    warnings: Optional[List[str]] = Field(
        default=None,
        description="Warning messages"
    )
    
    class Config:
        use_enum_values = True
        arbitrary_types_allowed = True

