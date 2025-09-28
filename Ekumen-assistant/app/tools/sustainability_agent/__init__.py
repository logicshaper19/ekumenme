"""
Sustainability Agent Tools Package.

This package contains all sustainability-related tools following the "One Tool, One Job" principle.
Each tool does ONE specific thing and does it well.

Tools:
- CalculateCarbonFootprintTool: Calculate carbon footprint for agricultural practices
- AssessBiodiversityTool: Assess biodiversity impact and conservation potential
- AnalyzeSoilHealthTool: Analyze soil health indicators and sustainability
- AssessWaterManagementTool: Assess water management efficiency and sustainability
- GenerateSustainabilityReportTool: Generate comprehensive sustainability reports
"""

from .calculate_carbon_footprint_tool import CalculateCarbonFootprintTool
from .assess_biodiversity_tool import AssessBiodiversityTool
from .analyze_soil_health_tool import AnalyzeSoilHealthTool
from .assess_water_management_tool import AssessWaterManagementTool
from .generate_sustainability_report_tool import GenerateSustainabilityReportTool

__all__ = [
    "CalculateCarbonFootprintTool",
    "AssessBiodiversityTool",
    "AnalyzeSoilHealthTool",
    "AssessWaterManagementTool",
    "GenerateSustainabilityReportTool"
]
