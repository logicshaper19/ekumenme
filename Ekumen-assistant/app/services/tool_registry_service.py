"""
Tool Registry Service - Central registry for all agricultural tools.

Connects the parallel executor to actual tool implementations.
"""

import logging
from typing import Dict, Any, Optional
from langchain.tools import BaseTool

# Import all tools
from app.tools import (
    # Weather tools
    GetWeatherDataTool,
    AnalyzeWeatherRisksTool,
    IdentifyInterventionWindowsTool,
    CalculateEvapotranspirationTool,
    
    # Planning tools
    GeneratePlanningTasksTool,
    OptimizeTaskSequenceTool,
    CalculatePlanningCostsTool,
    AnalyzeResourceRequirementsTool,
    GeneratePlanningReportTool,
    
    # Farm data tools
    GetFarmDataTool,
    CalculatePerformanceMetricsTool,
    BenchmarkCropPerformanceTool,
    AnalyzeTrendsTool,
    GenerateFarmReportTool,
    
    # Crop health tools
    DiagnoseDiseaseTool,
    IdentifyPestTool,
    AnalyzeNutrientDeficiencyTool,
    GenerateTreatmentPlanTool,
    
    # Regulatory tools
    DatabaseIntegratedAMMLookupTool,
    CheckRegulatoryComplianceTool,
    GetSafetyGuidelinesTool,
    CheckEnvironmentalRegulationsTool,
    
    # Sustainability tools
    CalculateCarbonFootprintTool,
    AssessBiodiversityTool,
    AnalyzeSoilHealthTool,
    AssessWaterManagementTool,
    GenerateSustainabilityReportTool
)

logger = logging.getLogger(__name__)


class ToolRegistryService:
    """
    Central registry for all agricultural tools.
    
    Provides:
    - Tool lookup by name
    - Tool execution
    - Tool metadata
    """
    
    def __init__(self):
        # Initialize all tools
        self.tools: Dict[str, BaseTool] = {}
        self._register_all_tools()
        
        logger.info(f"Initialized Tool Registry with {len(self.tools)} tools")
    
    def _register_all_tools(self):
        """Register all available tools"""
        
        # Weather tools
        self._register_tool("get_weather_data", GetWeatherDataTool())
        self._register_tool("analyze_weather_risks", AnalyzeWeatherRisksTool())
        self._register_tool("identify_intervention_windows", IdentifyInterventionWindowsTool())
        self._register_tool("calculate_evapotranspiration", CalculateEvapotranspirationTool())
        
        # Planning tools
        self._register_tool("generate_planning_tasks", GeneratePlanningTasksTool())
        self._register_tool("optimize_task_sequence", OptimizeTaskSequenceTool())
        self._register_tool("calculate_planning_costs", CalculatePlanningCostsTool())
        self._register_tool("analyze_resource_requirements", AnalyzeResourceRequirementsTool())
        self._register_tool("generate_planning_report", GeneratePlanningReportTool())
        
        # Farm data tools
        self._register_tool("get_farm_data", GetFarmDataTool())
        self._register_tool("calculate_performance_metrics", CalculatePerformanceMetricsTool())
        self._register_tool("benchmark_crop_performance", BenchmarkCropPerformanceTool())
        self._register_tool("analyze_trends", AnalyzeTrendsTool())
        self._register_tool("generate_farm_report", GenerateFarmReportTool())
        
        # Crop health tools
        self._register_tool("diagnose_disease", DiagnoseDiseaseTool())
        self._register_tool("identify_pest", IdentifyPestTool())
        self._register_tool("analyze_nutrient_deficiency", AnalyzeNutrientDeficiencyTool())
        self._register_tool("generate_treatment_plan", GenerateTreatmentPlanTool())
        
        # Regulatory tools
        self._register_tool("lookup_amm", DatabaseIntegratedAMMLookupTool())
        self._register_tool("check_regulatory_compliance", CheckRegulatoryComplianceTool())
        self._register_tool("get_safety_guidelines", GetSafetyGuidelinesTool())
        self._register_tool("check_environmental_regulations", CheckEnvironmentalRegulationsTool())
        
        # Sustainability tools
        self._register_tool("calculate_carbon_footprint", CalculateCarbonFootprintTool())
        self._register_tool("assess_biodiversity", AssessBiodiversityTool())
        self._register_tool("analyze_soil_health", AnalyzeSoilHealthTool())
        self._register_tool("assess_water_management", AssessWaterManagementTool())
        self._register_tool("generate_sustainability_report", GenerateSustainabilityReportTool())
    
    def _register_tool(self, name: str, tool: BaseTool):
        """Register a single tool"""
        self.tools[name] = tool
        logger.debug(f"Registered tool: {name}")
    
    def get_tool(self, tool_name: str) -> Optional[BaseTool]:
        """Get tool by name"""
        return self.tools.get(tool_name)
    
    async def execute_tool(
        self,
        tool_name: str,
        context: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> Any:
        """
        Execute a tool by name.

        Args:
            tool_name: Name of the tool to execute
            context: Execution context
            **kwargs: Tool-specific arguments

        Returns:
            Tool execution result
        """
        tool = self.get_tool(tool_name)

        if not tool:
            raise ValueError(f"Tool not found: {tool_name}")

        # Execute tool
        try:
            # Check if tool has async run method
            if hasattr(tool, '_arun'):
                result = await tool._arun(**kwargs)
            else:
                # Fallback to sync run
                result = tool._run(**kwargs)

            return result

        except Exception as e:
            logger.error(f"Tool execution failed: {tool_name} - {e}")
            raise

    async def execute_tools(
        self,
        tools: list[str],
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute multiple tools (for compatibility with OptimizedStreamingService).

        Args:
            tools: List of tool names or categories to execute
            query: User query
            context: Execution context

        Returns:
            Dict mapping tool names to results
        """
        # Import agents here to avoid circular imports
        from app.agents.internet_agent import InternetAgent
        from app.agents.supplier_agent import SupplierAgent
        from app.agents.weather_agent import WeatherIntelligenceAgent
        from app.agents.regulatory_agent import IntegratedRegulatoryAgent

        # Category to primary tool mapping (for LangChain tools)
        category_to_tool = {
            "farm_data": "get_farm_data",
            "planning": "generate_planning_tasks",
            "crop_health": "diagnose_disease",
            "sustainability": "calculate_carbon_footprint"
        }

        # Category to agent mapping (for standalone agents)
        category_to_agent = {
            "internet": InternetAgent,
            "supplier": SupplierAgent,
            "market_prices": InternetAgent,  # Market prices uses internet agent
            "weather": WeatherIntelligenceAgent,
            "regulatory": IntegratedRegulatoryAgent
        }

        results = {}

        for tool_name in tools:
            try:
                # Check if this is an agent-based category
                if tool_name in category_to_agent:
                    agent_class = category_to_agent[tool_name]
                    agent = agent_class()
                    result = await agent.process(query, context)
                    results[tool_name] = result
                    logger.info(f"✅ Executed agent: {tool_name}")

                # Otherwise, try to execute as a LangChain tool
                elif tool_name in category_to_tool:
                    actual_tool_name = category_to_tool[tool_name]
                    result = await self.execute_tool(
                        tool_name=actual_tool_name,
                        context=context,
                        query=query
                    )
                    results[tool_name] = result
                    logger.info(f"✅ Executed tool: {actual_tool_name}")

                else:
                    logger.warning(f"⚠️ Unknown tool/agent: {tool_name}")
                    results[tool_name] = {"error": f"Unknown tool: {tool_name}"}

            except Exception as e:
                logger.error(f"❌ Tool {tool_name} failed: {e}")
                results[tool_name] = {"error": str(e)}

        return results
    
    def get_all_tool_names(self) -> list[str]:
        """Get list of all registered tool names"""
        return list(self.tools.keys())
    
    def get_tool_metadata(self, tool_name: str) -> Dict[str, Any]:
        """Get metadata for a tool"""
        tool = self.get_tool(tool_name)
        
        if not tool:
            return {}
        
        return {
            "name": tool_name,
            "description": tool.description if hasattr(tool, 'description') else "",
            "args_schema": str(tool.args) if hasattr(tool, 'args') else None
        }
    
    def get_tools_by_category(self, category: str) -> list[str]:
        """Get tools by category"""
        category_mapping = {
            "weather": [
                "get_weather_data",
                "analyze_weather_risks",
                "identify_intervention_windows",
                "calculate_evapotranspiration"
            ],
            "planning": [
                "generate_planning_tasks",
                "optimize_task_sequence",
                "calculate_planning_costs",
                "analyze_resource_requirements",
                "generate_planning_report"
            ],
            "farm_data": [
                "get_farm_data",
                "calculate_performance_metrics",
                "benchmark_crop_performance",
                "analyze_trends",
                "generate_farm_report"
            ],
            "crop_health": [
                "diagnose_disease",
                "identify_pest",
                "analyze_nutrient_deficiency",
                "generate_treatment_plan"
            ],
            "regulatory": [
                "lookup_amm",
                "check_regulatory_compliance",
                "get_safety_guidelines",
                "check_environmental_regulations"
            ],
            "sustainability": [
                "calculate_carbon_footprint",
                "assess_biodiversity",
                "analyze_soil_health",
                "assess_water_management",
                "generate_sustainability_report"
            ]
        }
        
        return category_mapping.get(category, [])


# Global tool registry instance
_tool_registry = None


def get_tool_registry() -> ToolRegistryService:
    """Get global tool registry instance"""
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistryService()
    return _tool_registry

