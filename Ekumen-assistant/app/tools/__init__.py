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
    get_weather_data_tool,
    analyze_weather_risks_tool,
    identify_intervention_windows_tool,
    calculate_evapotranspiration_tool
)
from .planning_agent import (
    generate_planning_tasks_tool,
    optimize_task_sequence_tool,
    calculate_planning_costs_tool,
    analyze_resource_requirements_tool,
    check_crop_feasibility_tool
)
from .farm_data_agent import (
    get_farm_data_tool,
    calculate_performance_metrics_tool,
    benchmark_crop_performance_tool,
    analyze_trends_tool
)
from .crop_health_agent import (
    diagnose_disease_tool,
    identify_pest_tool,
    analyze_nutrient_deficiency_tool,
    generate_treatment_plan_tool
)
from .regulatory_agent import (
    database_integrated_amm_tool,
    LookupAMMTool,  # Legacy tool (keep for backward compatibility)
    check_regulatory_compliance_tool,
    get_safety_guidelines_tool,
    check_environmental_regulations_tool
)
from .sustainability_agent import (
    calculate_carbon_footprint_tool,
    assess_biodiversity_tool,
    analyze_soil_health_tool,
    assess_water_management_tool
)

__all__ = [
    # Weather Agent Tools (Production-Ready with Dynamic TTL Caching)
    "get_weather_data_tool",
    "analyze_weather_risks_tool",
    "identify_intervention_windows_tool",
    "calculate_evapotranspiration_tool",

    # Planning Tools (Production-Ready with BBCH Integration)
    "generate_planning_tasks_tool",
    "optimize_task_sequence_tool",
    "calculate_planning_costs_tool",
    "analyze_resource_requirements_tool",
    "check_crop_feasibility_tool",

    # Farm Data Tools (Production-Ready with SIRET Multi-Tenancy)
    "get_farm_data_tool",
    "calculate_performance_metrics_tool",
    "benchmark_crop_performance_tool",
    "analyze_trends_tool",

    # Crop Health Agent Tools (Production-Ready with EPPO Codes)
    "diagnose_disease_tool",
    "identify_pest_tool",
    "analyze_nutrient_deficiency_tool",
    "generate_treatment_plan_tool",

    # Regulatory Agent Tools (Production-Ready with Real EPHY Database)
    "database_integrated_amm_tool",  # Primary tool with real EPHY data
    "LookupAMMTool",  # Legacy tool (keep for backward compatibility)
    "check_regulatory_compliance_tool",
    "get_safety_guidelines_tool",
    "check_environmental_regulations_tool",

    # Sustainability Agent Tools (Production-Ready with Uncertainty Quantification & Economic ROI)
    "calculate_carbon_footprint_tool",
    "assess_biodiversity_tool",
    "analyze_soil_health_tool",
    "assess_water_management_tool"
]
