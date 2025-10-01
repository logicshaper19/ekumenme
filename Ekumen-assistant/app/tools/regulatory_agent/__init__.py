"""
Regulatory Agent Tools Package.

This package contains all regulatory-related tools following the "One Tool, One Job" principle.
Each tool does ONE specific thing and does it well.

Tools:
- database_integrated_amm_tool: Look up AMM information using real EPHY database with caching
- lookup_amm_tool: Legacy AMM lookup tool (deprecated, use database_integrated_amm_tool)
- check_regulatory_compliance_tool: Check regulatory compliance with French agricultural regulations
- get_safety_guidelines_tool: Get safety guidelines for products with PPE recommendations
- check_environmental_regulations_tool: Check environmental regulation compliance with ZNT zones
"""

from .database_integrated_amm_tool import database_integrated_amm_tool
from .lookup_amm_tool import LookupAMMTool  # Legacy tool (keep for backward compatibility)
from .check_regulatory_compliance_tool import check_regulatory_compliance_tool
from .get_safety_guidelines_tool import get_safety_guidelines_tool
from .check_environmental_regulations_tool import check_environmental_regulations_tool

__all__ = [
    "database_integrated_amm_tool",  # Primary tool
    "LookupAMMTool",  # Legacy tool
    "check_regulatory_compliance_tool",
    "get_safety_guidelines_tool",
    "check_environmental_regulations_tool"
]
