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


# ============================================================================
# INPUT SCHEMAS
# ============================================================================

class EnvironmentalImpactData(BaseModel):
    """Environmental impact assessment data"""
    impact_level: EnvironmentalImpactLevel = Field(
        default=EnvironmentalImpactLevel.MODERATE,
        description="Overall environmental impact level"
    )
    water_proximity_m: Optional[float] = Field(
        default=None,
        description="Distance to nearest water body in meters"
    )
    sensitive_area: bool = Field(
        default=False,
        description="Whether the area is environmentally sensitive (Natura 2000, etc.)"
    )
    flowering_period: bool = Field(
        default=False,
        description="Whether crops/plants are in flowering period"
    )
    wind_speed_kmh: Optional[float] = Field(
        default=None,
        description="Wind speed in km/h"
    )
    temperature_c: Optional[float] = Field(
        default=None,
        description="Temperature in Celsius"
    )
    soil_type: Optional[str] = Field(
        default=None,
        description="Soil type (sandy, clay, loam, etc.)"
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


class ZNTCompliance(BaseModel):
    """ZNT compliance details"""
    required_znt_m: float = Field(description="Required ZNT distance in meters")
    actual_distance_m: Optional[float] = Field(
        default=None,
        description="Actual distance to water body"
    )
    is_compliant: bool = Field(description="Whether ZNT is respected")
    znt_type: str = Field(description="Type of ZNT (aquatic, arthropods, plants)")
    reduction_possible: bool = Field(
        default=False,
        description="Whether ZNT reduction is possible with equipment"
    )
    reduction_conditions: Optional[List[str]] = Field(
        default=None,
        description="Conditions for ZNT reduction"
    )


class EnvironmentalRegulationsOutput(BaseModel):
    """Output schema for environmental regulations check"""
    
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
    
    # ZNT compliance (from database)
    znt_compliance: Optional[List[ZNTCompliance]] = Field(
        default=None,
        description="ZNT compliance details from EPHY database"
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

