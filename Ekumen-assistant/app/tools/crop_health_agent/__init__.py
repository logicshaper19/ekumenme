"""
Crop Health Agent Tools Package.

This package contains all crop health-related tools following the "One Tool, One Job" principle.
Each tool does ONE specific thing and does it well.

Tools:
- DiagnoseDiseaseTool: Diagnose crop diseases from symptoms
- IdentifyPestTool: Identify crop pests from damage patterns
- AnalyzeNutrientDeficiencyTool: Analyze nutrient deficiencies
- GenerateTreatmentPlanTool: Generate comprehensive treatment plans

Enhanced Tools (Phase 2 - Database Integration):
- diagnose_disease_tool_enhanced: Disease diagnosis with Crop table + EPPO codes
- identify_pest_tool_enhanced: Pest identification with crop categories + EPPO codes
- analyze_nutrient_deficiency_tool_enhanced: Nutrient analysis with Crop integration
- generate_treatment_plan_tool_enhanced: Comprehensive treatment planning with Crop model
"""

# Original tools
from .diagnose_disease_tool import DiagnoseDiseaseTool
from .identify_pest_tool import IdentifyPestTool
from .analyze_nutrient_deficiency_tool import AnalyzeNutrientDeficiencyTool
from .generate_treatment_plan_tool import GenerateTreatmentPlanTool

# Enhanced tools (Phase 2)
from .diagnose_disease_tool_enhanced import diagnose_disease_tool_enhanced
from .identify_pest_tool_enhanced import identify_pest_tool_enhanced
from .analyze_nutrient_deficiency_tool_enhanced import analyze_nutrient_deficiency_tool_enhanced
from .generate_treatment_plan_tool_enhanced import generate_treatment_plan_tool_enhanced

__all__ = [
    # Original tools
    "DiagnoseDiseaseTool",
    "IdentifyPestTool",
    "AnalyzeNutrientDeficiencyTool",
    "GenerateTreatmentPlanTool",
    # Enhanced tools
    "diagnose_disease_tool_enhanced",
    "identify_pest_tool_enhanced",
    "analyze_nutrient_deficiency_tool_enhanced",
    "generate_treatment_plan_tool_enhanced",
]
