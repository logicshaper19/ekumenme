"""
Pydantic schemas for Safety Guidelines Tool

Provides type-safe input/output schemas for agricultural safety guidelines
with database integration for EPHY product safety data.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime


class SafetyLevel(str, Enum):
    """Safety level classification"""
    BASIC = "basic"
    STANDARD = "standard"
    HIGH = "high"
    CRITICAL = "critical"


class ProductType(str, Enum):
    """Product type classification"""
    HERBICIDE = "herbicide"
    INSECTICIDE = "insecticide"
    FONGICIDE = "fongicide"
    FERTILIZER = "fertilizer"
    GROWTH_REGULATOR = "growth_regulator"
    OTHER = "other"


class PracticeType(str, Enum):
    """Practice type classification"""
    SPRAYING = "spraying"
    FERTILIZATION = "fertilization"
    IRRIGATION = "irrigation"
    HARVESTING = "harvesting"
    SOIL_PREPARATION = "soil_preparation"
    OTHER = "other"


class SafetyPriority(str, Enum):
    """Safety priority level"""
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


# ============================================================================
# INPUT SCHEMAS
# ============================================================================

class SafetyGuidelinesInput(BaseModel):
    """Input schema for safety guidelines request"""
    
    product_type: Optional[ProductType] = Field(
        default=None,
        description="Type of agricultural product"
    )
    practice_type: Optional[PracticeType] = Field(
        default=None,
        description="Type of agricultural practice"
    )
    safety_level: SafetyLevel = Field(
        default=SafetyLevel.STANDARD,
        description="Required safety level"
    )
    amm_code: Optional[str] = Field(
        default=None,
        description="AMM code for specific product safety data from EPHY database"
    )
    product_name: Optional[str] = Field(
        default=None,
        description="Product name for database lookup"
    )
    include_risk_phrases: bool = Field(
        default=True,
        description="Include risk phrases from EPHY database"
    )
    include_emergency_procedures: bool = Field(
        default=True,
        description="Include emergency procedures"
    )
    
    @field_validator('amm_code')
    @classmethod
    def validate_amm_code(cls, v):
        """Validate AMM code format"""
        if v is not None and len(v) == 0:
            return None
        return v
    
    class Config:
        use_enum_values = True


# ============================================================================
# OUTPUT SCHEMAS
# ============================================================================

class RiskPhrase(BaseModel):
    """Risk phrase from EPHY database"""
    code: str = Field(description="Risk phrase code (e.g., H301, P102)")
    description: str = Field(description="Risk phrase description in French")
    category: str = Field(description="Category: hazard (H) or precautionary (P)")


class SafetyEquipment(BaseModel):
    """Required safety equipment"""
    equipment_type: str = Field(description="Type of equipment")
    is_mandatory: bool = Field(description="Whether equipment is mandatory")
    specification: Optional[str] = Field(
        default=None,
        description="Specific requirements or standards"
    )


class EmergencyProcedure(BaseModel):
    """Emergency procedure"""
    situation: str = Field(description="Emergency situation")
    procedure: str = Field(description="Procedure to follow")
    priority: SafetyPriority = Field(description="Priority level")
    contact_info: Optional[str] = Field(
        default=None,
        description="Emergency contact information"
    )


class SafetyGuideline(BaseModel):
    """Individual safety guideline"""
    guideline_type: str = Field(description="Type of guideline")
    description: str = Field(description="Guideline description")
    safety_level: SafetyLevel = Field(description="Safety level")
    required_equipment: List[SafetyEquipment] = Field(
        default_factory=list,
        description="Required safety equipment"
    )
    safety_measures: List[str] = Field(
        default_factory=list,
        description="Safety measures to follow"
    )
    emergency_procedures: List[EmergencyProcedure] = Field(
        default_factory=list,
        description="Emergency procedures"
    )
    risk_phrases: Optional[List[RiskPhrase]] = Field(
        default=None,
        description="Risk phrases from EPHY database"
    )
    legal_references: Optional[List[str]] = Field(
        default=None,
        description="Legal references for safety requirements"
    )
    source: str = Field(
        default="configuration",
        description="Source of guideline: 'configuration' or 'ephy_database'"
    )


class ProductSafetyInfo(BaseModel):
    """Product-specific safety information from EPHY database"""
    amm_code: str = Field(description="AMM code")
    product_name: str = Field(description="Product name")
    risk_phrases: List[RiskPhrase] = Field(
        default_factory=list,
        description="Risk phrases"
    )
    safety_interval_days: Optional[int] = Field(
        default=None,
        description="Safety interval before harvest (DAR)"
    )
    reentry_interval_hours: Optional[int] = Field(
        default=None,
        description="Re-entry interval after application"
    )
    znt_requirements: Optional[Dict[str, float]] = Field(
        default=None,
        description="ZNT requirements (aquatic, arthropods, plants)"
    )
    authorized_mentions: Optional[str] = Field(
        default=None,
        description="Authorized mentions from label"
    )
    usage_restrictions: Optional[str] = Field(
        default=None,
        description="Usage restrictions"
    )


class SafetyGuidelinesOutput(BaseModel):
    """Output schema for safety guidelines"""
    
    success: bool = Field(description="Whether the request was successful")
    product_type: Optional[str] = Field(
        default=None,
        description="Product type queried"
    )
    practice_type: Optional[str] = Field(
        default=None,
        description="Practice type queried"
    )
    safety_level: str = Field(description="Safety level applied")
    
    # Guidelines
    safety_guidelines: List[SafetyGuideline] = Field(
        default_factory=list,
        description="Safety guidelines"
    )
    
    # Product-specific data from EPHY
    product_safety_info: Optional[ProductSafetyInfo] = Field(
        default=None,
        description="Product-specific safety information from EPHY database"
    )
    
    # Summary
    safety_priority: SafetyPriority = Field(description="Overall safety priority")
    total_guidelines: int = Field(description="Total number of guidelines")
    total_risk_phrases: int = Field(
        default=0,
        description="Total number of risk phrases"
    )
    
    # Recommendations
    safety_recommendations: List[str] = Field(
        default_factory=list,
        description="Safety recommendations"
    )
    critical_warnings: List[str] = Field(
        default_factory=list,
        description="Critical safety warnings"
    )
    
    # Emergency contacts
    emergency_contacts: Dict[str, str] = Field(
        default_factory=dict,
        description="Emergency contact information"
    )
    
    # Error handling
    error: Optional[str] = Field(default=None, description="Error message if failed")
    error_type: Optional[str] = Field(default=None, description="Error type")
    
    # Metadata
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Timestamp of the response"
    )
    data_source: str = Field(
        default="configuration",
        description="Primary data source: 'configuration', 'ephy_database', or 'hybrid'"
    )

