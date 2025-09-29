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
import requests
import os
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
        use_real_api: bool = True,
        coordinates: Optional[Dict[str, float]] = None,
        **kwargs
    ) -> str:
        """
        Retrieve weather forecast data from real weather APIs or mock data.

        Args:
            location: Location name (e.g., "Normandie", "Calvados")
            days: Number of forecast days (1-14)
            use_real_api: Whether to use real weather APIs
            coordinates: Optional lat/lon coordinates {"lat": 49.18, "lon": 0.37}
        """
        try:
            # Get weather forecast from real API or mock data
            weather_data = self._get_weather_forecast_enhanced(
                location, days, use_real_api, coordinates
            )

            return json.dumps(weather_data, ensure_ascii=False, indent=2)

        except Exception as e:
            logger.error(f"Get weather data error: {e}")
            return json.dumps({"error": f"Erreur lors de la récupération des données météo: {str(e)}"})
    
    def _get_weather_forecast_enhanced(
        self,
        location: str,
        days: int,
        use_real_api: bool = True,
        coordinates: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """Get weather forecast from real APIs or mock data."""

        if use_real_api:
            # Try to get real weather data
            try:
                real_weather = self._get_real_weather_data(location, days, coordinates)
                if real_weather:
                    return real_weather
            except Exception as e:
                logger.warning(f"Real weather API failed, falling back to mock data: {e}")

        # Fallback to enhanced mock data
        return self._get_mock_weather_data(location, days)

    def _get_real_weather_data(
        self,
        location: str,
        days: int,
        coordinates: Optional[Dict[str, float]] = None
    ) -> Optional[Dict[str, Any]]:
        """Get weather data from real weather APIs."""

        # Try WeatherAPI.com first (primary API)
        api_key = os.getenv("WEATHER_API_KEY")
        if api_key:
            try:
                return self._get_weatherapi_data(location, days, api_key)
            except Exception as e:
                logger.warning(f"WeatherAPI.com failed: {e}")

        # Try OpenWeatherMap API (free tier)
        api_key = os.getenv("OPENWEATHER_API_KEY")
        if api_key:
            try:
                return self._get_openweather_data(location, days, api_key, coordinates)
            except Exception as e:
                logger.warning(f"OpenWeatherMap API failed: {e}")

        # Try Météo-France API (if available)
        try:
            return self._get_meteofrance_data(location, days, coordinates)
        except Exception as e:
            logger.warning(f"Météo-France API failed: {e}")

        return None

    def _get_weatherapi_data(
        self,
        location: str,
        days: int,
        api_key: str
    ) -> Dict[str, Any]:
        """Get weather data from WeatherAPI.com."""

        # Call WeatherAPI.com API
        url = f"http://api.weatherapi.com/v1/forecast.json"
        params = {
            "key": api_key,
            "q": location,
            "days": min(days, 14),  # WeatherAPI.com supports up to 14 days
            "lang": "fr"
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        # Process WeatherAPI.com response
        forecast_conditions = []

        for day in data["forecast"]["forecastday"]:
            condition = {
                "date": day["date"],
                "temperature_min": day["day"]["mintemp_c"],
                "temperature_max": day["day"]["maxtemp_c"],
                "humidity": day["day"]["avghumidity"],
                "wind_speed": day["day"]["maxwind_kph"],
                "wind_direction": self._degrees_to_direction(day["hour"][12].get("wind_degree", 0)),
                "precipitation": day["day"]["totalprecip_mm"],
                "cloud_cover": day["day"]["avgvis_km"],
                "uv_index": day["day"]["uv"]
            }
            forecast_conditions.append(condition)

        return {
            "location": data["location"]["name"],
            "coordinates": {
                "lat": data["location"]["lat"],
                "lon": data["location"]["lon"]
            },
            "forecast_period_days": days,
            "weather_conditions": forecast_conditions,
            "total_days": len(forecast_conditions),
            "data_source": "weatherapi.com",
            "retrieved_at": datetime.now().isoformat()
        }

    def _get_openweather_data(
        self,
        location: str,
        days: int,
        api_key: str,
        coordinates: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """Get weather data from OpenWeatherMap API."""

        # Use coordinates if provided, otherwise geocode location
        if coordinates:
            lat, lon = coordinates["lat"], coordinates["lon"]
        else:
            # Simple geocoding for French locations
            location_coords = {
                "normandie": {"lat": 49.18, "lon": 0.37},
                "calvados": {"lat": 49.18, "lon": 0.37},
                "paris": {"lat": 48.85, "lon": 2.35},
                "lyon": {"lat": 45.75, "lon": 4.85}
            }
            coords = location_coords.get(location.lower(), {"lat": 49.18, "lon": 0.37})
            lat, lon = coords["lat"], coords["lon"]

        # Call OpenWeatherMap API
        url = f"https://api.openweathermap.org/data/2.5/forecast"
        params = {
            "lat": lat,
            "lon": lon,
            "appid": api_key,
            "units": "metric",
            "lang": "fr"
        }

        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        data = response.json()

        # Process OpenWeatherMap response
        forecast_conditions = []
        processed_dates = set()

        for item in data["list"][:days*8]:  # 8 forecasts per day (3-hour intervals)
            date_str = datetime.fromtimestamp(item["dt"]).strftime("%Y-%m-%d")

            if date_str not in processed_dates:
                processed_dates.add(date_str)

                condition = {
                    "date": date_str,
                    "temperature_min": item["main"]["temp_min"],
                    "temperature_max": item["main"]["temp_max"],
                    "humidity": item["main"]["humidity"],
                    "wind_speed": item["wind"]["speed"] * 3.6,  # Convert m/s to km/h
                    "wind_direction": self._degrees_to_direction(item["wind"].get("deg", 0)),
                    "precipitation": item.get("rain", {}).get("3h", 0) + item.get("snow", {}).get("3h", 0),
                    "cloud_cover": item["clouds"]["all"],
                    "uv_index": 3  # OpenWeatherMap doesn't provide UV in free tier
                }
                forecast_conditions.append(condition)

        return {
            "location": location,
            "coordinates": {"lat": lat, "lon": lon},
            "forecast_period_days": days,
            "weather_conditions": forecast_conditions,
            "total_days": len(forecast_conditions),
            "data_source": "openweathermap",
            "retrieved_at": datetime.now().isoformat()
        }

    def _get_meteofrance_data(
        self,
        location: str,
        days: int,
        coordinates: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """Get weather data from Météo-France API (placeholder for future implementation)."""

        # TODO: Implement Météo-France API integration
        # For now, return None to indicate unavailable
        logger.info("Météo-France API integration not yet implemented")
        return None

    def _degrees_to_direction(self, degrees: float) -> str:
        """Convert wind degrees to direction."""
        directions = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"]
        index = round(degrees / 45) % 8
        return directions[index]

    def _get_mock_weather_data(self, location: str, days: int) -> Dict[str, Any]:
        """Get enhanced mock weather data."""

        # Enhanced mock weather data with more realistic patterns
        base_conditions = {
            "normandie": {"temp_min": 8, "temp_max": 18, "humidity": 75, "precipitation_chance": 0.3},
            "calvados": {"temp_min": 8, "temp_max": 18, "humidity": 75, "precipitation_chance": 0.3},
            "paris": {"temp_min": 10, "temp_max": 20, "humidity": 65, "precipitation_chance": 0.2},
            "lyon": {"temp_min": 12, "temp_max": 22, "humidity": 60, "precipitation_chance": 0.15}
        }

        base = base_conditions.get(location.lower(), base_conditions["normandie"])

        forecast_conditions = []
        current_date = datetime.now()

        for i in range(days):
            date_str = (current_date + timedelta(days=i)).strftime("%Y-%m-%d")

            # Add some realistic variation
            temp_variation = (i % 3 - 1) * 2  # ±2°C variation
            humidity_variation = (i % 4 - 1.5) * 10  # ±15% variation

            condition = {
                "date": date_str,
                "temperature_min": base["temp_min"] + temp_variation,
                "temperature_max": base["temp_max"] + temp_variation,
                "humidity": max(30, min(95, base["humidity"] + humidity_variation)),
                "wind_speed": 8 + (i % 5) * 2,  # 8-16 km/h
                "wind_direction": ["N", "NE", "E", "SE", "S", "SO", "O", "NO"][i % 8],
                "precipitation": 0 if (i % 3) != 0 else (2 + i % 8),  # Some days with rain
                "cloud_cover": 30 + (i % 7) * 10,  # 30-90% cloud cover
                "uv_index": max(1, min(8, 4 + (i % 3) - 1))  # 1-8 UV index
            }
            forecast_conditions.append(condition)

        return {
            "location": location,
            "coordinates": {"lat": 49.18, "lon": 0.37},  # Default to Normandie
            "forecast_period_days": days,
            "weather_conditions": forecast_conditions,
            "total_days": len(forecast_conditions),
            "data_source": "mock_data",
            "retrieved_at": datetime.now().isoformat()
        }
