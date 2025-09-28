"""
Get Weather Data Tool - Single Purpose Tool

Job: Retrieve weather forecast data for a location.
Input: location, days
Output: JSON string of WeatherCondition objects

This tool does ONLY:
- Execute specific, well-defined function
- Take structured inputs, return structured outputs
- Contain domain-specific business logic
- Be stateless and reusable

No prompting logic, no orchestration, no agent responsibilities.
"""

from typing import Dict, List, Any, Optional
from langchain.tools import BaseTool
import logging
import json
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class WeatherCondition:
    """Structured weather condition."""
    date: str
    temperature_min: float
    temperature_max: float
    humidity: float
    wind_speed: float
    wind_direction: str
    precipitation: float
    cloud_cover: float
    uv_index: float

class GetWeatherDataTool(BaseTool):
    """
    Tool: Retrieve weather forecast data for a location.
    
    Job: Get weather forecast data from API or mock data.
    Input: location, days
    Output: JSON string of WeatherCondition objects
    """
    
    name: str = "get_weather_data_tool"
    description: str = "Récupère les données de prévision météorologique"
    
    def _run(
        self, 
        location: str,
        days: int = 7,
        **kwargs
    ) -> str:
        """
        Retrieve weather forecast data for a location.
        
        Args:
            location: Location for weather forecast
            days: Number of days to forecast
        """
        try:
            # Get weather forecast data
            forecast_data = self._get_weather_forecast(location, days)
            
            # Convert to JSON-serializable format
            forecast_as_dicts = [asdict(condition) for condition in forecast_data]
            
            return json.dumps({
                "location": location,
                "forecast_period_days": days,
                "weather_conditions": forecast_as_dicts,
                "total_days": len(forecast_data),
                "retrieved_at": datetime.now().isoformat()
            }, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"Get weather data error: {e}")
            return json.dumps({"error": f"Erreur lors de la récupération des données météo: {str(e)}"})
    
    def _get_weather_forecast(self, location: str, days: int) -> List[WeatherCondition]:
        """Get weather forecast data."""
        # Mock weather data - in production would call real weather API
        mock_forecast_data = {
            "2024-03-22": {
                "temperature_min": 8.5,
                "temperature_max": 18.2,
                "humidity": 72,
                "wind_speed": 12,
                "wind_direction": "SO",
                "precipitation": 0,
                "cloud_cover": 30,
                "uv_index": 4
            },
            "2024-03-23": {
                "temperature_min": 6.8,
                "temperature_max": 16.5,
                "humidity": 85,
                "wind_speed": 8,
                "wind_direction": "O",
                "precipitation": 5.2,
                "cloud_cover": 80,
                "uv_index": 2
            },
            "2024-03-24": {
                "temperature_min": 4.2,
                "temperature_max": 14.8,
                "humidity": 90,
                "wind_speed": 15,
                "wind_direction": "N",
                "precipitation": 8.5,
                "cloud_cover": 95,
                "uv_index": 1
            },
            "2024-03-25": {
                "temperature_min": 7.1,
                "temperature_max": 19.5,
                "humidity": 65,
                "wind_speed": 6,
                "wind_direction": "SE",
                "precipitation": 0,
                "cloud_cover": 20,
                "uv_index": 5
            }
        }
        
        forecast = []
        current_date = datetime.now()
        
        for i in range(days):
            date_str = (current_date + timedelta(days=i)).strftime("%Y-%m-%d")
            if date_str in mock_forecast_data:
                day_data = mock_forecast_data[date_str].copy()
                day_data["date"] = date_str
                forecast.append(WeatherCondition(**day_data))
            else:
                # Generate default data
                forecast.append(WeatherCondition(
                    date=date_str,
                    temperature_min=10.0,
                    temperature_max=20.0,
                    humidity=70,
                    wind_speed=10,
                    wind_direction="N",
                    precipitation=0,
                    cloud_cover=50,
                    uv_index=3
                ))
        
        return forecast
