"""
Sustainability Agent Tools Package.

This package contains all sustainability-related tools following the "One Tool, One Job" principle.
Each tool does ONE specific thing and does it well.

Tools:
- calculate_carbon_footprint_tool: Calculate carbon footprint with uncertainty ranges
- assess_biodiversity_tool: Assess biodiversity with 7 indicators
- analyze_soil_health_tool: Analyze soil health with crop-specific recommendations
- assess_water_management_tool: Assess water management with economic ROI
"""

from .calculate_carbon_footprint_tool import carbon_footprint_tool
from .assess_biodiversity_tool import biodiversity_tool
from .analyze_soil_health_tool import soil_health_tool
from .assess_water_management_tool import water_management_tool

__all__ = [
    "carbon_footprint_tool",
    "biodiversity_tool",
    "soil_health_tool",
    "water_management_tool"
]
