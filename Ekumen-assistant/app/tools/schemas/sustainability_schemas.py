"""
Pydantic schemas for Sustainability Agent tools.

All schemas follow v2 patterns with proper validation.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


# ============================================================================
# ANALYZE SOIL HEALTH TOOL SCHEMAS
# ============================================================================

class SoilHealthStatus(str, Enum):
    """Soil health status levels"""
    OPTIMAL = "optimal"
    GOOD = "good"
    MODERATE = "moderate"
    POOR = "poor"
    CRITICAL = "critical"


class SoilIndicator(BaseModel):
    """Individual soil health indicator"""
    indicator_name: str
    current_value: float = Field(ge=0)
    optimal_min: float = Field(ge=0)
    optimal_max: float = Field(ge=0)
    unit: str
    status: SoilHealthStatus
    deviation_percent: Optional[float] = Field(default=None, description="% deviation from optimal range")


class SoilHealthInput(BaseModel):
    """Input schema for analyze soil health tool"""
    
    # Required soil indicators (at least one)
    ph: Optional[float] = Field(default=None, ge=3.0, le=10.0, description="Soil pH")
    organic_matter_percent: Optional[float] = Field(default=None, ge=0.0, le=100.0, description="Organic matter %")
    nitrogen_ppm: Optional[float] = Field(default=None, ge=0.0, description="Nitrogen (ppm)")
    phosphorus_ppm: Optional[float] = Field(default=None, ge=0.0, description="Phosphorus (ppm)")
    potassium_ppm: Optional[float] = Field(default=None, ge=0.0, description="Potassium (ppm)")
    
    # Optional indicators
    calcium_ppm: Optional[float] = Field(default=None, ge=0.0, description="Calcium (ppm)")
    magnesium_ppm: Optional[float] = Field(default=None, ge=0.0, description="Magnesium (ppm)")
    cec_meq: Optional[float] = Field(default=None, ge=0.0, description="Cation exchange capacity (meq/100g)")
    
    # Context
    crop: Optional[str] = Field(default=None, max_length=100, description="Current or planned crop")
    location: Optional[str] = Field(default=None, max_length=100, description="Location for regional recommendations")


class SoilHealthOutput(BaseModel):
    """Output schema for analyze soil health tool"""
    
    success: bool = Field(default=True)
    overall_score: float = Field(ge=0.0, le=10.0, description="Overall soil health score (0-10)")
    overall_status: SoilHealthStatus
    indicators_analyzed: List[SoilIndicator] = Field(default_factory=list)
    total_indicators: int = Field(ge=0)
    critical_issues: List[str] = Field(default_factory=list, description="Critical soil health issues")
    improvement_recommendations: List[str] = Field(default_factory=list)
    estimated_improvement_time_months: Optional[int] = Field(default=None, ge=0, description="Time to reach good status")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    error: Optional[str] = None
    error_type: Optional[str] = None


# ============================================================================
# CALCULATE CARBON FOOTPRINT TOOL SCHEMAS
# ============================================================================

class CarbonSource(str, Enum):
    """Carbon emission sources"""
    FUEL = "fuel"
    FERTILIZER = "fertilizer"
    PESTICIDES = "pesticides"
    MACHINERY = "machinery"
    TRANSPORT = "transport"
    IRRIGATION = "irrigation"
    SEQUESTRATION = "sequestration"  # Negative emissions


class CarbonEmission(BaseModel):
    """Individual carbon emission source"""
    source: CarbonSource
    emissions_kg_co2eq: float = Field(description="Emissions in kg CO2 equivalent")
    percentage_of_total: float = Field(ge=0.0, le=100.0)
    reduction_potential_percent: Optional[float] = Field(default=None, ge=0.0, le=100.0)


class CarbonFootprintInput(BaseModel):
    """Input schema for calculate carbon footprint tool"""
    
    surface_ha: float = Field(gt=0, le=10000, description="Surface area in hectares")
    crop: str = Field(min_length=1, max_length=100, description="Crop type")
    
    # Fuel consumption
    diesel_liters: Optional[float] = Field(default=None, ge=0, description="Diesel consumption (L)")
    gasoline_liters: Optional[float] = Field(default=None, ge=0, description="Gasoline consumption (L)")
    
    # Fertilizer inputs (kg)
    nitrogen_kg: Optional[float] = Field(default=None, ge=0, description="Nitrogen fertilizer (kg)")
    phosphorus_kg: Optional[float] = Field(default=None, ge=0, description="Phosphorus fertilizer (kg)")
    potassium_kg: Optional[float] = Field(default=None, ge=0, description="Potassium fertilizer (kg)")
    organic_fertilizer_kg: Optional[float] = Field(default=None, ge=0, description="Organic fertilizer (kg)")
    
    # Pesticides
    pesticide_kg: Optional[float] = Field(default=None, ge=0, description="Total pesticides (kg active ingredient)")
    
    # Practices (for sequestration estimation)
    cover_crops: bool = Field(default=False, description="Cover crops used")
    reduced_tillage: bool = Field(default=False, description="Reduced/no-till practices")
    organic_amendments: bool = Field(default=False, description="Organic amendments applied")


class CarbonFootprintOutput(BaseModel):
    """Output schema for calculate carbon footprint tool"""

    success: bool = Field(default=True)
    crop: str
    surface_ha: float
    total_emissions_kg_co2eq: float = Field(description="Total emissions in kg CO2eq (mid-range estimate)")
    total_emissions_min_kg_co2eq: Optional[float] = Field(default=None, description="Minimum emissions (low emission factors)")
    total_emissions_max_kg_co2eq: Optional[float] = Field(default=None, description="Maximum emissions (high emission factors)")
    uncertainty_range_percent: Optional[float] = Field(default=None, description="Uncertainty range as % of mid-range")
    emissions_per_ha: float = Field(description="Emissions per hectare (kg CO2eq/ha)")
    emissions_by_source: List[CarbonEmission] = Field(default_factory=list)
    sequestration_potential_kg_co2eq: float = Field(default=0.0, description="Carbon sequestration potential")
    net_emissions_kg_co2eq: float = Field(description="Net emissions after sequestration")
    benchmark_comparison: Optional[str] = Field(default=None, description="Comparison to regional/crop average")
    reduction_recommendations: List[str] = Field(default_factory=list)
    data_quality_note: str = Field(description="Note about data completeness and assumptions")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    error: Optional[str] = None
    error_type: Optional[str] = None


# ============================================================================
# ASSESS BIODIVERSITY TOOL SCHEMAS
# ============================================================================

class BiodiversityIndicator(str, Enum):
    """Biodiversity indicators"""
    CROP_ROTATION = "crop_rotation"
    FIELD_MARGINS = "field_margins"
    HEDGEROWS = "hedgerows"
    WATER_FEATURES = "water_features"
    ORGANIC_PRACTICES = "organic_practices"
    PESTICIDE_USE = "pesticide_use"
    HABITAT_DIVERSITY = "habitat_diversity"


class BiodiversityScore(BaseModel):
    """Individual biodiversity indicator score"""
    indicator: BiodiversityIndicator
    score: float = Field(ge=0.0, le=10.0, description="Score 0-10")
    status: str = Field(description="poor, moderate, good, excellent")
    impact_description: str


class BiodiversityInput(BaseModel):
    """Input schema for assess biodiversity tool"""
    
    surface_ha: float = Field(gt=0, le=10000)
    
    # Crop diversity
    crops_in_rotation: int = Field(ge=1, le=20, description="Number of different crops in rotation")
    rotation_years: int = Field(ge=1, le=10, description="Rotation cycle length in years")
    
    # Landscape features
    field_margin_percent: Optional[float] = Field(default=0.0, ge=0.0, le=100.0, description="% of field with margins")
    hedgerow_length_m: Optional[float] = Field(default=0.0, ge=0.0, description="Total hedgerow length (m)")
    water_features: bool = Field(default=False, description="Presence of ponds, streams, wetlands")
    
    # Practices
    organic_certified: bool = Field(default=False)
    pesticide_applications_per_year: int = Field(ge=0, le=50, description="Number of pesticide applications")
    cover_crops_used: bool = Field(default=False)
    
    # Optional context
    location: Optional[str] = Field(default=None, max_length=100)


class BiodiversityOutput(BaseModel):
    """Output schema for assess biodiversity tool"""
    
    success: bool = Field(default=True)
    surface_ha: float
    overall_biodiversity_score: float = Field(ge=0.0, le=10.0)
    overall_status: str = Field(description="poor, moderate, good, excellent")
    indicator_scores: List[BiodiversityScore] = Field(default_factory=list)
    strengths: List[str] = Field(default_factory=list, description="Positive biodiversity practices")
    weaknesses: List[str] = Field(default_factory=list, description="Areas for improvement")
    improvement_recommendations: List[str] = Field(default_factory=list)
    potential_score_improvement: float = Field(ge=0.0, le=10.0, description="Potential score with recommendations")
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    error: Optional[str] = None
    error_type: Optional[str] = None


# ============================================================================
# ASSESS WATER MANAGEMENT TOOL SCHEMAS
# ============================================================================

class WaterManagementIndicator(str, Enum):
    """Water management indicators"""
    IRRIGATION_EFFICIENCY = "irrigation_efficiency"
    WATER_CONSERVATION = "water_conservation"
    DRAINAGE_MANAGEMENT = "drainage_management"
    RUNOFF_CONTROL = "runoff_control"
    WATER_QUALITY = "water_quality"


class WaterIndicatorScore(BaseModel):
    """Individual water management indicator score"""
    indicator: WaterManagementIndicator
    score: float = Field(ge=0.0, le=10.0)
    status: str
    description: str


class WaterManagementInput(BaseModel):
    """Input schema for assess water management tool"""
    
    surface_ha: float = Field(gt=0, le=10000)
    crop: str = Field(min_length=1, max_length=100)
    
    # Irrigation
    irrigated: bool = Field(default=False)
    irrigation_method: Optional[str] = Field(default=None, description="sprinkler, drip, flood, etc.")
    annual_water_usage_m3: Optional[float] = Field(default=None, ge=0, description="Annual water usage (m³)")
    
    # Conservation practices
    soil_moisture_monitoring: bool = Field(default=False)
    weather_based_irrigation: bool = Field(default=False)
    mulching_used: bool = Field(default=False)
    cover_crops_for_water: bool = Field(default=False)
    
    # Drainage and runoff
    drainage_system: bool = Field(default=False)
    buffer_strips: bool = Field(default=False)
    contour_farming: bool = Field(default=False)
    
    # Optional context
    location: Optional[str] = Field(default=None, max_length=100)
    rainfall_mm_annual: Optional[float] = Field(default=None, ge=0, description="Annual rainfall (mm)")


class WaterManagementOutput(BaseModel):
    """Output schema for assess water management tool"""
    
    success: bool = Field(default=True)
    surface_ha: float
    crop: str
    overall_water_score: float = Field(ge=0.0, le=10.0)
    overall_status: str
    indicator_scores: List[WaterIndicatorScore] = Field(default_factory=list)
    water_use_efficiency: Optional[float] = Field(default=None, description="m³/ha if data available")
    estimated_water_savings_potential_m3: Optional[float] = Field(default=None, ge=0)
    improvement_recommendations: List[str] = Field(default_factory=list)
    critical_issues: List[str] = Field(default_factory=list)
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat() + "Z")
    error: Optional[str] = None
    error_type: Optional[str] = None

