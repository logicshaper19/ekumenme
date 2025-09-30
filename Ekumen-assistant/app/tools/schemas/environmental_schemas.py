"""
Pydantic schemas for Environmental Regulations Tool

Provides type-safe input/output schemas for environmental compliance checking
with database integration for ZNT, water protection, biodiversity, and air quality.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime, date


class PracticeType(str, Enum):
    """Agricultural practice type"""
    SPRAYING = "spraying"
    FERTILIZATION = "fertilization"
    IRRIGATION = "irrigation"
    SOIL_PREPARATION = "soil_preparation"
    HARVESTING = "harvesting"
    OTHER = "other"


class EnvironmentalImpactLevel(str, Enum):
    """Environmental impact level"""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class ComplianceStatus(str, Enum):
    """Compliance status"""
    COMPLIANT = "compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    NON_COMPLIANT = "non_compliant"
    UNKNOWN = "unknown"


class RiskLevel(str, Enum):
    """Environmental risk level"""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class RegulationType(str, Enum):
    """Type of environmental regulation"""
    WATER_PROTECTION = "water_protection"
    BIODIVERSITY_PROTECTION = "biodiversity_protection"
    AIR_QUALITY = "air_quality"
    SOIL_PROTECTION = "soil_protection"
    NITRATE_DIRECTIVE = "nitrate_directive"
    PHOSPHORUS_MANAGEMENT = "phosphorus_management"
    WATER_USAGE = "water_usage"
    GROUNDWATER_PROTECTION = "groundwater_protection"
    ZNT_COMPLIANCE = "znt_compliance"
    NATURA_2000 = "natura_2000"


class WaterBodyType(str, Enum):
    """Type of water body"""
    DRINKING_WATER_SOURCE = "drinking_water_source"
    PERMANENT_STREAM = "permanent_stream"
    INTERMITTENT_STREAM = "intermittent_stream"
    DRAINAGE_DITCH = "drainage_ditch"
    LAKE_POND = "lake_pond"
    WETLAND = "wetland"
    UNKNOWN = "unknown"


class EquipmentDriftClass(str, Enum):
    """Anti-drift equipment classification"""
    NO_EQUIPMENT = "no_equipment"
    ONE_STAR = "1_star"
    THREE_STAR = "3_star"
    FIVE_STAR = "5_star"


class GroundwaterVulnerability(str, Enum):
    """Groundwater vulnerability level"""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    VERY_HIGH = "very_high"


# ============================================================================
# INPUT SCHEMAS
# ============================================================================

class EnvironmentalImpactData(BaseModel):
    """Environmental impact assessment data - ENHANCED"""
    impact_level: EnvironmentalImpactLevel = Field(
        default=EnvironmentalImpactLevel.MODERATE,
        description="Overall environmental impact level"
    )

    # Water proximity - ENHANCED
    water_proximity_m: Optional[float] = Field(
        default=None,
        description="Distance to nearest water body in meters"
    )
    water_body_type: WaterBodyType = Field(
        default=WaterBodyType.UNKNOWN,
        description="Type of water body (permanent stream, drinking water, etc.)"
    )
    water_body_width_m: Optional[float] = Field(
        default=None,
        description="Width of water body in meters"
    )

    # Sensitive areas
    sensitive_area: bool = Field(
        default=False,
        description="Whether the area is environmentally sensitive (Natura 2000, etc.)"
    )
    natura_2000_site_code: Optional[str] = Field(
        default=None,
        description="Natura 2000 site code if applicable"
    )

    # Phenology
    flowering_period: bool = Field(
        default=False,
        description="Whether crops/plants are in flowering period"
    )
    bbch_stage: Optional[int] = Field(
        default=None,
        ge=0,
        le=99,
        description="BBCH growth stage (0-99)"
    )

    # Weather - ENHANCED
    wind_speed_kmh: Optional[float] = Field(
        default=None,
        description="Wind speed in km/h"
    )
    temperature_c: Optional[float] = Field(
        default=None,
        description="Temperature in Celsius"
    )
    humidity_percent: Optional[float] = Field(
        default=None,
        ge=0,
        le=100,
        description="Relative humidity percentage"
    )
    rain_forecast_48h: bool = Field(
        default=False,
        description="Rain forecast within 48 hours"
    )
    temperature_inversion: bool = Field(
        default=False,
        description="Temperature inversion conditions (early morning risk)"
    )

    # Soil - ENHANCED
    soil_type: Optional[str] = Field(
        default=None,
        description="Soil type (sandy, clay, loam, etc.)"
    )
    soil_moisture_level: Optional[str] = Field(
        default=None,
        description="Soil moisture level (dry, moist, saturated)"
    )
    depth_to_groundwater_m: Optional[float] = Field(
        default=None,
        description="Depth to groundwater table in meters"
    )

    # Equipment
    drift_reduction_equipment: EquipmentDriftClass = Field(
        default=EquipmentDriftClass.NO_EQUIPMENT,
        description="Anti-drift equipment class (1-star, 3-star, 5-star)"
    )
    has_vegetation_buffer: bool = Field(
        default=False,
        description="Presence of vegetation buffer strip"
    )

    # Neighbors
    organic_farm_nearby: bool = Field(
        default=False,
        description="Organic farm within 50m"
    )
    beehives_nearby: bool = Field(
        default=False,
        description="Beehives within 200m"
    )
    habitation_distance_m: Optional[float] = Field(
        default=None,
        description="Distance to nearest habitation in meters"
    )


class EnvironmentalRegulationsInput(BaseModel):
    """Input schema for environmental regulations check"""
    
    practice_type: PracticeType = Field(description="Type of agricultural practice")
    location: Optional[str] = Field(
        default=None,
        description="Location (department, region, or coordinates)"
    )
    environmental_impact: Optional[EnvironmentalImpactData] = Field(
        default=None,
        description="Environmental impact assessment data"
    )
    amm_codes: Optional[List[str]] = Field(
        default=None,
        description="AMM codes of products to check for environmental restrictions"
    )
    crop_eppo_code: Optional[str] = Field(
        default=None,
        description="EPPO code of the crop"
    )
    field_size_ha: Optional[float] = Field(
        default=None,
        ge=0,
        description="Field size in hectares"
    )
    application_date: Optional[date] = Field(
        default=None,
        description="Planned application date"
    )
    
    class Config:
        use_enum_values = True


# ============================================================================
# OUTPUT SCHEMAS
# ============================================================================

class EnvironmentalRegulation(BaseModel):
    """Individual environmental regulation"""
    regulation_type: RegulationType = Field(description="Type of regulation")
    regulation_name: str = Field(description="Name of the regulation")
    compliance_status: ComplianceStatus = Field(description="Compliance status")
    environmental_impact: EnvironmentalImpactLevel = Field(
        description="Environmental impact level"
    )
    required_measures: List[str] = Field(
        default_factory=list,
        description="Required measures for compliance"
    )
    restrictions: List[str] = Field(
        default_factory=list,
        description="Restrictions and prohibitions"
    )
    penalties: List[str] = Field(
        default_factory=list,
        description="Potential penalties for non-compliance"
    )
    legal_references: Optional[List[str]] = Field(
        default=None,
        description="Legal references"
    )
    znt_requirements: Optional[Dict[str, float]] = Field(
        default=None,
        description="ZNT requirements from database (aquatic, arthropods, plants)"
    )
    source: str = Field(
        default="configuration",
        description="Source: 'configuration', 'ephy_database', or 'hybrid'"
    )


class EnvironmentalRisk(BaseModel):
    """Environmental risk assessment"""
    risk_level: RiskLevel = Field(description="Overall risk level")
    risk_score: float = Field(
        ge=0.0,
        le=1.0,
        description="Risk score (0-1)"
    )
    high_impact_count: int = Field(
        default=0,
        description="Number of high-impact regulations"
    )
    non_compliant_count: int = Field(
        default=0,
        description="Number of non-compliant regulations"
    )
    critical_issues: List[str] = Field(
        default_factory=list,
        description="Critical environmental issues"
    )


class ProductEnvironmentalData(BaseModel):
    """Product environmental fate and ecotoxicology data"""
    amm_code: str = Field(description="AMM code")
    product_name: str = Field(description="Product name")

    # Active substances
    active_substances: List[str] = Field(
        default_factory=list,
        description="List of active substance names"
    )

    # Persistence (not in current EPHY but should be)
    soil_half_life_days: Optional[float] = Field(
        default=None,
        description="Soil degradation half-life in days (DT50)"
    )
    water_half_life_days: Optional[float] = Field(
        default=None,
        description="Water degradation half-life in days"
    )

    # Mobility
    koc_value: Optional[float] = Field(
        default=None,
        description="Soil organic carbon partition coefficient (Koc)"
    )
    gus_index: Optional[float] = Field(
        default=None,
        description="Groundwater Ubiquity Score (GUS index)"
    )
    leaching_potential: Optional[str] = Field(
        default=None,
        description="Leaching potential (low, moderate, high)"
    )

    # Toxicity
    aquatic_toxicity_level: Optional[str] = Field(
        default=None,
        description="Aquatic toxicity level (low, moderate, high, very high)"
    )
    bee_toxicity: Optional[str] = Field(
        default=None,
        description="Bee toxicity (not toxic, toxic, highly toxic)"
    )

    # Classification
    is_cmr: bool = Field(
        default=False,
        description="Carcinogenic, Mutagenic, or Reprotoxic"
    )
    is_pbt: bool = Field(
        default=False,
        description="Persistent, Bioaccumulative, and Toxic"
    )
    is_vpvb: bool = Field(
        default=False,
        description="Very Persistent and Very Bioaccumulative"
    )


class ZNTCompliance(BaseModel):
    """ZNT compliance details - ENHANCED"""
    required_znt_m: float = Field(description="Required ZNT distance in meters")
    actual_distance_m: Optional[float] = Field(
        default=None,
        description="Actual distance to water body"
    )
    is_compliant: bool = Field(description="Whether ZNT is respected")
    znt_type: str = Field(description="Type of ZNT (aquatic, arthropods, plants)")

    # Enhanced reduction logic
    reduction_possible: bool = Field(
        default=False,
        description="Whether ZNT reduction is possible with equipment"
    )
    reduction_conditions: Optional[List[str]] = Field(
        default=None,
        description="Conditions for ZNT reduction"
    )
    equipment_class_required: Optional[EquipmentDriftClass] = Field(
        default=None,
        description="Minimum equipment class required for reduction"
    )
    max_reduction_percent: Optional[float] = Field(
        default=None,
        description="Maximum reduction percentage allowed"
    )
    minimum_absolute_znt_m: float = Field(
        default=5.0,
        description="Minimum absolute ZNT (cannot be reduced below this)"
    )
    reduced_znt_m: Optional[float] = Field(
        default=None,
        description="Reduced ZNT with equipment (if applicable)"
    )
    water_body_type: WaterBodyType = Field(
        default=WaterBodyType.UNKNOWN,
        description="Type of water body affecting ZNT requirements"
    )


class CumulativeImpactAssessment(BaseModel):
    """Cumulative environmental impact assessment"""
    total_applications_30days: int = Field(
        default=0,
        description="Number of applications in last 30 days"
    )
    total_active_substance_kg: float = Field(
        default=0.0,
        description="Total active substance applied (kg)"
    )
    soil_residue_risk: RiskLevel = Field(
        description="Risk of soil residue accumulation"
    )
    water_contamination_risk: RiskLevel = Field(
        description="Risk of water contamination"
    )
    cumulative_warnings: List[str] = Field(
        default_factory=list,
        description="Warnings about cumulative impacts"
    )
    recommended_waiting_period_days: Optional[int] = Field(
        default=None,
        description="Recommended waiting period before next application"
    )


class GroundwaterRiskAssessment(BaseModel):
    """Groundwater vulnerability and contamination risk assessment"""
    vulnerability_level: GroundwaterVulnerability = Field(
        description="Groundwater vulnerability level"
    )
    contamination_risk: RiskLevel = Field(
        description="Contamination risk level"
    )
    risk_factors: List[str] = Field(
        default_factory=list,
        description="Factors contributing to groundwater risk"
    )
    is_recharge_zone: bool = Field(
        default=False,
        description="Whether location is in aquifer recharge zone"
    )
    is_karst_area: bool = Field(
        default=False,
        description="Whether location is in karst area (direct infiltration)"
    )
    nearby_wells_springs: bool = Field(
        default=False,
        description="Presence of wells or springs nearby"
    )
    protective_measures: List[str] = Field(
        default_factory=list,
        description="Recommended protective measures"
    )


class WaterBodyClassification(BaseModel):
    """Water body classification and protection requirements"""
    water_body_type: WaterBodyType = Field(description="Type of water body")
    base_znt_m: float = Field(description="Base ZNT requirement in meters")
    reduction_allowed: bool = Field(
        default=True,
        description="Whether ZNT reduction is allowed"
    )
    special_protections: List[str] = Field(
        default_factory=list,
        description="Special protection requirements"
    )
    is_drinking_water_source: bool = Field(
        default=False,
        description="Whether it's a drinking water source"
    )
    is_fish_bearing: bool = Field(
        default=False,
        description="Whether it contains fish populations"
    )


class EnvironmentalRegulationsOutput(BaseModel):
    """Output schema for environmental regulations check - ENHANCED"""

    success: bool = Field(description="Whether the request was successful")
    practice_type: str = Field(description="Practice type checked")
    location: Optional[str] = Field(
        default=None,
        description="Location checked"
    )

    # Regulations
    environmental_regulations: List[EnvironmentalRegulation] = Field(
        default_factory=list,
        description="Environmental regulations applicable"
    )

    # Risk assessment
    environmental_risk: EnvironmentalRisk = Field(
        description="Environmental risk assessment"
    )

    # ZNT compliance (from database) - ENHANCED
    znt_compliance: Optional[List[ZNTCompliance]] = Field(
        default=None,
        description="ZNT compliance details from EPHY database"
    )

    # NEW: Product environmental data
    product_environmental_data: Optional[List[ProductEnvironmentalData]] = Field(
        default=None,
        description="Environmental fate and ecotoxicology data for products"
    )

    # NEW: Cumulative impact
    cumulative_impact: Optional[CumulativeImpactAssessment] = Field(
        default=None,
        description="Cumulative environmental impact assessment"
    )

    # NEW: Groundwater risk
    groundwater_risk: Optional[GroundwaterRiskAssessment] = Field(
        default=None,
        description="Groundwater vulnerability and contamination risk"
    )

    # NEW: Water body classification
    water_body_classification: Optional[WaterBodyClassification] = Field(
        default=None,
        description="Water body classification and protection requirements"
    )

    # Recommendations
    environmental_recommendations: List[str] = Field(
        default_factory=list,
        description="Environmental recommendations"
    )
    critical_warnings: List[str] = Field(
        default_factory=list,
        description="Critical environmental warnings"
    )

    # Summary
    total_regulations: int = Field(description="Total number of regulations checked")
    compliant_count: int = Field(
        default=0,
        description="Number of compliant regulations"
    )
    non_compliant_count: int = Field(
        default=0,
        description="Number of non-compliant regulations"
    )

    # Seasonal restrictions
    seasonal_restrictions: Optional[List[str]] = Field(
        default=None,
        description="Seasonal restrictions based on application date"
    )

    # NEW: Weather-based restrictions
    weather_restrictions: Optional[List[str]] = Field(
        default=None,
        description="Weather-based restrictions (temperature, humidity, rain forecast)"
    )

    # NEW: Neighbor considerations
    neighbor_warnings: Optional[List[str]] = Field(
        default=None,
        description="Warnings about nearby organic farms, beehives, etc."
    )

    # Error handling
    error: Optional[str] = Field(default=None, description="Error message if failed")
    error_type: Optional[str] = Field(default=None, description="Error type")

    # Metadata
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp of the check"
    )
    data_source: str = Field(
        default="configuration",
        description="Primary data source: 'configuration', 'ephy_database', or 'hybrid'"
    )

