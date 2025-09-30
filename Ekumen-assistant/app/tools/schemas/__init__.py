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

from app.tools.schemas.safety_schemas import (
    SafetyGuidelinesInput,
    SafetyGuidelinesOutput,
    SafetyGuideline,
    SafetyEquipment,
    EmergencyProcedure,
    RiskPhrase,
    ProductSafetyInfo,
    SafetyLevel,
    SafetyPriority
)

from app.tools.schemas.environmental_schemas import (
    EnvironmentalRegulationsInput,
    EnvironmentalRegulationsOutput,
    EnvironmentalRegulation,
    EnvironmentalRisk,
    ZNTCompliance,
    EnvironmentalImpactData,
    EnvironmentalImpactLevel,
    RiskLevel as EnvironmentalRiskLevel,
    ProductEnvironmentalData,
    CumulativeImpactAssessment,
    GroundwaterRiskAssessment,
    WaterBodyClassification,
    WaterBodyType,
    EquipmentDriftClass,
    GroundwaterVulnerability
)

from app.tools.schemas.disease_schemas import (
    DiseaseDiagnosisInput,
    DiseaseDiagnosisOutput,
    DiseaseDiagnosis,
    DiseaseSeverity,
    DiseaseType,
    ConfidenceLevel as DiseaseConfidenceLevel,
    EnvironmentalConditions,
    BBCHStageInfo
)

from app.tools.schemas.pest_schemas import (
    PestIdentificationInput,
    PestIdentificationOutput,
    PestIdentification,
    PestSeverity,
    PestType,
    PestStage,
    CropCategoryRiskProfile
)

from app.tools.schemas.treatment_schemas import (
    TreatmentPlanInput,
    TreatmentPlanOutput,
    TreatmentStep,
    TreatmentSchedule,
    CostAnalysis,
    MonitoringPlan,
    TreatmentPriority,
    TreatmentType,
    TreatmentTiming
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
    # Safety schemas
    "SafetyGuidelinesInput",
    "SafetyGuidelinesOutput",
    "SafetyGuideline",
    "SafetyEquipment",
    "EmergencyProcedure",
    "RiskPhrase",
    "ProductSafetyInfo",
    "SafetyLevel",
    "SafetyPriority",
    # Environmental schemas
    "EnvironmentalRegulationsInput",
    "EnvironmentalRegulationsOutput",
    "EnvironmentalRegulation",
    "EnvironmentalRisk",
    "ZNTCompliance",
    "EnvironmentalImpactData",
    "EnvironmentalImpactLevel",
    "EnvironmentalRiskLevel",
    "ProductEnvironmentalData",
    "CumulativeImpactAssessment",
    "GroundwaterRiskAssessment",
    "WaterBodyClassification",
    "WaterBodyType",
    "EquipmentDriftClass",
    "GroundwaterVulnerability",
    # Disease schemas
    "DiseaseDiagnosisInput",
    "DiseaseDiagnosisOutput",
    "DiseaseDiagnosis",
    "DiseaseSeverity",
    "DiseaseType",
    "DiseaseConfidenceLevel",
    "EnvironmentalConditions",
    "BBCHStageInfo",
    # Pest schemas
    "PestIdentificationInput",
    "PestIdentificationOutput",
    "PestIdentification",
    "PestSeverity",
    "PestType",
    "PestStage",
    "CropCategoryRiskProfile",
    # Treatment schemas
    "TreatmentPlanInput",
    "TreatmentPlanOutput",
    "TreatmentStep",
    "TreatmentSchedule",
    "CostAnalysis",
    "MonitoringPlan",
    "TreatmentPriority",
    "TreatmentType",
    "TreatmentTiming",
]

