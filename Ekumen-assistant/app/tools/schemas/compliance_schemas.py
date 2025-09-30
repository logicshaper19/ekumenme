"""
Pydantic schemas for regulatory compliance checking.

These schemas provide type-safe input/output for compliance verification tools.
"""

from pydantic import BaseModel, Field, field_validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class PracticeType(str, Enum):
    """Types of agricultural practices"""
    SPRAYING = "spraying"
    FERTILIZATION = "fertilization"
    IRRIGATION = "irrigation"
    HARVESTING = "harvesting"
    TILLAGE = "tillage"
    SEEDING = "seeding"


class ComplianceStatus(str, Enum):
    """Compliance status levels"""
    COMPLIANT = "compliant"
    PARTIALLY_COMPLIANT = "partially_compliant"
    NON_COMPLIANT = "non_compliant"
    WARNING = "warning"
    UNKNOWN = "unknown"


class RegulationType(str, Enum):
    """Types of regulatory checks"""
    PRODUCT_COMPLIANCE = "product_compliance"
    TIMING_COMPLIANCE = "timing_compliance"
    EQUIPMENT_COMPLIANCE = "equipment_compliance"
    ENVIRONMENTAL_COMPLIANCE = "environmental_compliance"
    ZNT_COMPLIANCE = "znt_compliance"
    DOSE_COMPLIANCE = "dose_compliance"


class ComplianceInput(BaseModel):
    """Input for compliance checking"""
    practice_type: PracticeType = Field(
        ...,
        description="Type of agricultural practice to check"
    )
    products_used: Optional[List[str]] = Field(
        default=None,
        description="List of products used (names or AMM codes)"
    )
    location: Optional[str] = Field(
        default=None,
        description="Location of the practice (region, department, or coordinates)"
    )
    timing: Optional[str] = Field(
        default=None,
        description="Timing of the practice (date, time, season)"
    )
    weather_conditions: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Current weather conditions (wind, temp, humidity)"
    )
    equipment_available: Optional[List[str]] = Field(
        default=None,
        description="List of available equipment"
    )
    crop_type: Optional[str] = Field(
        default=None,
        description="Type of crop being treated"
    )
    field_size_ha: Optional[float] = Field(
        default=None,
        ge=0,
        description="Field size in hectares"
    )
    
    @field_validator('products_used', 'equipment_available')
    @classmethod
    def validate_lists(cls, v):
        """Ensure lists are not empty if provided"""
        if v is not None and len(v) == 0:
            return None
        return v


class ComplianceCheckDetail(BaseModel):
    """Detailed compliance check result"""
    regulation_type: RegulationType
    compliance_status: ComplianceStatus
    compliance_score: float = Field(ge=0.0, le=1.0)
    violations: List[str] = Field(default_factory=list)
    recommendations: List[str] = Field(default_factory=list)
    penalties: List[str] = Field(default_factory=list)
    legal_references: Optional[List[str]] = Field(
        default=None,
        description="Legal references for this regulation"
    )


class OverallCompliance(BaseModel):
    """Overall compliance summary"""
    score: float = Field(ge=0.0, le=1.0)
    status: ComplianceStatus
    total_checks: int = Field(ge=0)
    passed_checks: int = Field(ge=0)
    failed_checks: int = Field(ge=0)
    warning_checks: int = Field(ge=0)


class ComplianceOutput(BaseModel):
    """Output from compliance checking"""
    success: bool
    practice_type: str
    products_used: List[str] = Field(default_factory=list)
    location: Optional[str] = None
    timing: Optional[str] = None
    
    # Compliance results
    compliance_checks: List[ComplianceCheckDetail] = Field(default_factory=list)
    overall_compliance: Optional[OverallCompliance] = None
    compliance_recommendations: List[str] = Field(default_factory=list)
    
    # Priority actions
    critical_violations: List[str] = Field(
        default_factory=list,
        description="Critical violations requiring immediate action"
    )
    warnings: List[str] = Field(
        default_factory=list,
        description="Warnings that should be addressed"
    )
    
    # Additional context
    total_checks: int = Field(ge=0)
    total_penalties_eur: Optional[float] = Field(
        default=None,
        ge=0,
        description="Total potential penalties in euros"
    )
    
    # Error handling
    error: Optional[str] = None
    error_type: Optional[str] = None
    
    # Metadata
    legal_disclaimer: str = Field(
        default="Cette analyse est fournie à titre informatif. "
                "Consultez toujours les textes réglementaires officiels et votre conseiller agricole."
    )
    timestamp: datetime = Field(default_factory=datetime.now)
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "practice_type": "spraying",
                "products_used": ["glyphosate"],
                "location": "Normandie",
                "timing": "2025-06-15 14:00",
                "compliance_checks": [
                    {
                        "regulation_type": "product_compliance",
                        "compliance_status": "non_compliant",
                        "compliance_score": 0.0,
                        "violations": ["Produit restreint utilisé: glyphosate"],
                        "recommendations": ["Remplacer glyphosate par un produit autorisé"],
                        "penalties": ["Amende: 1500€"]
                    }
                ],
                "overall_compliance": {
                    "score": 0.65,
                    "status": "partially_compliant",
                    "total_checks": 4,
                    "passed_checks": 2,
                    "failed_checks": 1,
                    "warning_checks": 1
                },
                "compliance_recommendations": [
                    "Remplacer glyphosate par un produit autorisé",
                    "Reporter l'application à des conditions favorables"
                ],
                "critical_violations": ["Produit restreint utilisé: glyphosate"],
                "warnings": ["Vitesse du vent proche de la limite"],
                "total_checks": 4,
                "total_penalties_eur": 2500.0,
                "timestamp": "2025-09-30T10:00:00"
            }
        }


class ComplianceRule(BaseModel):
    """Configuration for a compliance rule"""
    rule_id: str
    regulation_type: RegulationType
    description: str
    threshold: Optional[float] = None
    unit: Optional[str] = None
    penalty_eur: Optional[float] = None
    legal_reference: Optional[str] = None
    severity: str = Field(default="medium")  # low, medium, high, critical

