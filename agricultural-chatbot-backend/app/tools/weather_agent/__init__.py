"""
Weather Agent Tools Package.

This package contains all weather-related tools following the "One Tool, One Job" principle.
Each tool does ONE specific thing and does it well.

Tools:
- GetWeatherDataTool: Retrieve weather forecast data
- AnalyzeWeatherRisksTool: Analyze agricultural weather risks
- IdentifyInterventionWindowsTool: Identify optimal intervention windows
- CalculateEvapotranspirationTool: Calculate evapotranspiration and water needs
"""

from .get_weather_data_tool import GetWeatherDataTool
from .analyze_weather_risks_tool import AnalyzeWeatherRisksTool
from .identify_intervention_windows_tool import IdentifyInterventionWindowsTool
from .calculate_evapotranspiration_tool import CalculateEvapotranspirationTool

__all__ = [
    "GetWeatherDataTool",
    "AnalyzeWeatherRisksTool", 
    "IdentifyInterventionWindowsTool",
    "CalculateEvapotranspirationTool"
]
