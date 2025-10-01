"""
Crop Health Agent Tools Package.

This package contains all crop health-related tools following the "One Tool, One Job" principle.
Each tool does ONE specific thing and does it well.

Tools:
- diagnose_disease_tool: Disease diagnosis with Crop table + EPPO codes, severity scoring
- identify_pest_tool: Pest identification with crop categories + EPPO codes, damage assessment
- analyze_nutrient_deficiency_tool: Nutrient analysis with Crop integration, visual symptom matching
- generate_treatment_plan_tool: Comprehensive treatment planning with multi-issue prioritization
"""

from .diagnose_disease_tool import diagnose_disease_tool
from .identify_pest_tool import identify_pest_tool
from .analyze_nutrient_deficiency_tool import analyze_nutrient_deficiency_tool
from .generate_treatment_plan_tool import generate_treatment_plan_tool

__all__ = [
    "diagnose_disease_tool",
    "identify_pest_tool",
    "analyze_nutrient_deficiency_tool",
    "generate_treatment_plan_tool",
]
