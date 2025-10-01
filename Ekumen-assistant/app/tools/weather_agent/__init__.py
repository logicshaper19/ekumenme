"""
Weather Agent Tools Package.

This package contains all weather-related tools following the "One Tool, One Job" principle.
Each tool does ONE specific thing and does it well.

Tools:
- get_weather_data_tool: Retrieve weather forecast data with dynamic TTL caching
- analyze_weather_risks_tool: Analyze agricultural weather risks with severity scoring
- identify_intervention_windows_tool: Identify optimal intervention windows with confidence scores
- calculate_evapotranspiration_tool: Calculate FAO-56 evapotranspiration and water needs
"""

from .get_weather_data_tool import get_weather_data_tool
from .analyze_weather_risks_tool import analyze_weather_risks_tool
from .identify_intervention_windows_tool import identify_intervention_windows_tool
from .calculate_evapotranspiration_tool import calculate_evapotranspiration_tool

__all__ = [
    "get_weather_data_tool",
    "analyze_weather_risks_tool",
    "identify_intervention_windows_tool",
    "calculate_evapotranspiration_tool"
]
