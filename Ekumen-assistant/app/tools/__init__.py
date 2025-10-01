"""
Agricultural Tools Package - Organized by Agent.

This package contains all the specialized agricultural tools with pure business logic,
organized by agent following the "One Tool, One Job" principle.

Tools should ONLY:
- Execute specific, well-defined functions
- Take structured inputs, return structured outputs
- Contain domain-specific business logic
- Be stateless and reusable

No prompting logic, no orchestration, no agent responsibilities.
"""

# Import tools organized by agent
from .weather_agent import (
    GetWeatherDataTool,
    AnalyzeWeatherRisksTool,
    IdentifyInterventionWindowsTool,
    CalculateEvapotranspirationTool
)
from .planning_agent import (
    GeneratePlanningTasksTool,
    OptimizeTaskSequenceTool,
    CalculatePlanningCostsTool,
    AnalyzeResourceRequirementsTool
)
from .farm_data_agent import (
    GetFarmDataTool,
    CalculatePerformanceMetricsTool,
    BenchmarkCropPerformanceTool,
    AnalyzeTrendsTool,
    GenerateFarmReportTool
)
from .crop_health_agent import (
    DiagnoseDiseaseTool,
    IdentifyPestTool,
    AnalyzeNutrientDeficiencyTool,
    GenerateTreatmentPlanTool
)
from .regulatory_agent import (
    DatabaseIntegratedAMMLookupTool,
    LookupAMMTool,  # Legacy tool
    CheckRegulatoryComplianceTool,
    GetSafetyGuidelinesTool,
    CheckEnvironmentalRegulationsTool
)
from .sustainability_agent import (
    carbon_footprint_tool,
    biodiversity_tool,
    soil_health_tool,
    water_management_tool
)

__all__ = [
    # Weather Agent Tools (Organized - One Tool, One Job)
    "GetWeatherDataTool",
    "AnalyzeWeatherRisksTool",
    "IdentifyInterventionWindowsTool",
    "CalculateEvapotranspirationTool",
    
    # Planning Tools (Clean - One Tool, One Job)
    "GeneratePlanningTasksTool",
    "OptimizeTaskSequenceTool",
    "CalculatePlanningCostsTool",
    "AnalyzeResourceRequirementsTool",
    
    # Farm Data Tools (Clean - One Tool, One Job)
    "GetFarmDataTool",
    "CalculatePerformanceMetricsTool",
    "BenchmarkCropPerformanceTool",
    "AnalyzeTrendsTool",
    "GenerateFarmReportTool",
    
    # Crop Health Agent Tools (Organized - One Tool, One Job)
    "DiagnoseDiseaseTool",
    "IdentifyPestTool",
    "AnalyzeNutrientDeficiencyTool",
    "GenerateTreatmentPlanTool",
    
    # Regulatory Agent Tools (Database-Integrated)
    "DatabaseIntegratedAMMLookupTool",  # Primary tool with real EPHY data
    "LookupAMMTool",  # Legacy tool (deprecated)
    "CheckRegulatoryComplianceTool",
    "GetSafetyGuidelinesTool",
    "CheckEnvironmentalRegulationsTool",
    
    # Sustainability Agent Tools (Production-Ready with Uncertainty Quantification & Economic ROI)
    "carbon_footprint_tool",
    "biodiversity_tool",
    "soil_health_tool",
    "water_management_tool"
]
