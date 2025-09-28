"""
Crop Health Agent Tools Package.

This package contains all crop health-related tools following the "One Tool, One Job" principle.
Each tool does ONE specific thing and does it well.

Tools:
- DiagnoseDiseaseTool: Diagnose crop diseases from symptoms
- IdentifyPestTool: Identify crop pests from damage patterns
- AnalyzeNutrientDeficiencyTool: Analyze nutrient deficiencies
- GenerateTreatmentPlanTool: Generate comprehensive treatment plans
"""

from .diagnose_disease_tool import DiagnoseDiseaseTool
from .identify_pest_tool import IdentifyPestTool
from .analyze_nutrient_deficiency_tool import AnalyzeNutrientDeficiencyTool
from .generate_treatment_plan_tool import GenerateTreatmentPlanTool

__all__ = [
    "DiagnoseDiseaseTool",
    "IdentifyPestTool",
    "AnalyzeNutrientDeficiencyTool",
    "GenerateTreatmentPlanTool"
]
