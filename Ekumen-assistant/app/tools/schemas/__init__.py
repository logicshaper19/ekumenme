"""
Pydantic schemas for agricultural tools

Provides type-safe input/output schemas for all tools.
"""

from app.tools.schemas.weather_schemas import (
    WeatherInput,
    WeatherOutput,
    WeatherCondition,
    WeatherRisk,
    InterventionWindow,
    WindDirection,
)

from app.tools.schemas.risk_schemas import (
    RiskAnalysisInput,
    RiskAnalysisOutput,
    WeatherRiskDetail,
    RiskSummary,
    CropRiskProfile,
    CROP_RISK_PROFILES
)

from app.tools.schemas.intervention_schemas import (
    InterventionWindowsInput,
    InterventionWindowsOutput,
    InterventionWindowDetail,
    WindowStatistics,
    DEFAULT_INTERVENTION_TYPES,
    INTERVENTION_CRITERIA
)

from app.tools.schemas.evapotranspiration_schemas import (
    EvapotranspirationInput,
    EvapotranspirationOutput,
    DailyEvapotranspiration,
    WaterBalance,
    IrrigationRecommendation,
    CropType,
    IrrigationMethod,
    CROP_COEFFICIENTS,
)

from app.tools.schemas.amm_schemas import (
    AMMInput,
    AMMOutput,
    ProductInfo,
    SubstanceInfo,
    SearchSummary,
    RegulatoryContext,
    ProductType,
    ComplianceStatus as AMMComplianceStatus
)

from app.tools.schemas.compliance_schemas import (
    ComplianceInput,
    ComplianceOutput,
    ComplianceCheckDetail,
    OverallCompliance,
    ComplianceStatus,
    RegulationType,
    PracticeType,
    ComplianceRule
)

__all__ = [
    # Weather schemas
    "WeatherInput",
    "WeatherOutput",
    "WeatherCondition",
    "WeatherRisk",
    "InterventionWindow",
    "WindDirection",
    # Risk analysis schemas
    "RiskAnalysisInput",
    "RiskAnalysisOutput",
    "WeatherRiskDetail",
    "RiskSummary",
    "CropRiskProfile",
    "CROP_RISK_PROFILES",
    # Intervention windows schemas
    "InterventionWindowsInput",
    "InterventionWindowsOutput",
    "InterventionWindowDetail",
    "WindowStatistics",
    "DEFAULT_INTERVENTION_TYPES",
    "INTERVENTION_CRITERIA",
    # Evapotranspiration schemas
    "EvapotranspirationInput",
    "EvapotranspirationOutput",
    "DailyEvapotranspiration",
    "WaterBalance",
    "IrrigationRecommendation",
    "CropType",
    "IrrigationMethod",
    "CROP_COEFFICIENTS",
    # AMM schemas
    "AMMInput",
    "AMMOutput",
    "ProductInfo",
    "SubstanceInfo",
    "SearchSummary",
    "RegulatoryContext",
    "ProductType",
    "AMMComplianceStatus",
    # Compliance schemas
    "ComplianceInput",
    "ComplianceOutput",
    "ComplianceCheckDetail",
    "OverallCompliance",
    "ComplianceStatus",
    "RegulationType",
    "PracticeType",
    "ComplianceRule",
]

