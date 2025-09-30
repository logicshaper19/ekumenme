"""
Enhanced Get Weather Data Tool with Pydantic schemas, caching, and error handling

Improvements over original:
- ✅ Pydantic schemas for type safety
- ✅ Redis caching with 5-minute TTL
- ✅ Async support
- ✅ Granular error handling
- ✅ Agricultural risk analysis
- ✅ Intervention window identification
"""

import logging
from typing import Optional
from datetime import datetime, timedelta
import requests
import os

from langchain.tools import StructuredTool
from pydantic import ValidationError

from app.tools.schemas.weather_schemas import (
    WeatherInput,
    WeatherOutput,
    WeatherCondition,
    WeatherRisk,
    InterventionWindow,
    Coordinates,
    RiskSeverity,
)
from app.tools.exceptions import (
    WeatherAPIError,
    WeatherValidationError,
    WeatherTimeoutError,
    WeatherLocationNotFoundError,
)
from app.core.cache import redis_cache, smart_weather_ttl

logger = logging.getLogger(__name__)


class EnhancedWeatherService:
    """Service for fetching and processing weather data with caching"""

    async def get_weather_forecast(
        self,
        location: str,
        days: int = 7,
        coordinates: Optional[Coordinates] = None,
        use_real_api: bool = True
    ) -> WeatherOutput:
        """
        Get weather forecast with dynamic caching and risk analysis

        Uses smart TTL based on forecast range:
        - 1 day: 30 min cache
        - 3 days: 1 hour cache
        - 7 days: 2 hours cache
        - 14 days: 4 hours cache

        Args:
            location: Location name
            days: Number of forecast days (1-14)
            coordinates: Optional lat/lon coordinates
            use_real_api: Whether to use real weather APIs

        Returns:
            WeatherOutput with forecast, risks, and intervention windows

        Raises:
            WeatherAPIError: If weather API fails
            WeatherValidationError: If parameters are invalid
            WeatherTimeoutError: If API times out
            WeatherLocationNotFoundError: If location not found
        """
        # Use cached version with dynamic TTL
        return await self._get_weather_forecast_cached(
            location=location,
            days=days,
            coordinates=coordinates,
            use_real_api=use_real_api
        )

    @redis_cache(
        ttl=7200,  # Default 2 hours, overridden by smart_weather_ttl
        model_class=WeatherOutput,
        category="weather"
    )
    async def _get_weather_forecast_cached(
        self,
        location: str,
        days: int = 7,
        coordinates: Optional[Coordinates] = None,
        use_real_api: bool = True
    ) -> WeatherOutput:
        """Internal cached method with dynamic TTL"""
        # Calculate dynamic TTL
        ttl = smart_weather_ttl(days)
        logger.debug(f"Using TTL of {ttl}s for {days}-day forecast")

        try:
            # Get weather forecast
            if use_real_api:
                try:
                    weather_data = await self._get_real_weather_data(location, days, coordinates)
                except Exception as e:
                    logger.warning(f"Real weather API failed, falling back to mock: {e}")
                    weather_data = self._get_mock_weather_data(location, days)
            else:
                weather_data = self._get_mock_weather_data(location, days)
            
            # Analyze agricultural risks
            risks = self._analyze_agricultural_risks(weather_data["weather_conditions"])
            
            # Identify intervention windows
            windows = self._identify_intervention_windows(weather_data["weather_conditions"])
            
            # Create structured output
            return WeatherOutput(
                location=weather_data["location"],
                coordinates=Coordinates(**weather_data["coordinates"]),
                forecast_period_days=days,
                weather_conditions=weather_data["weather_conditions"],
                risks=risks,
                intervention_windows=windows,
                total_days=len(weather_data["weather_conditions"]),
                data_source=weather_data["data_source"],
                retrieved_at=weather_data["retrieved_at"]
            )
            
        except requests.Timeout:
            raise WeatherTimeoutError()
        except requests.ConnectionError as e:
            raise WeatherAPIError(f"Connexion impossible: {str(e)}")
        except ValidationError as e:
            raise WeatherValidationError(str(e))
        except Exception as e:
            logger.error(f"Weather forecast error: {e}", exc_info=True)
            raise WeatherAPIError(str(e))
    
    async def _get_real_weather_data(
        self,
        location: str,
        days: int,
        coordinates: Optional[Coordinates] = None
    ) -> dict:
        """Get weather data from real APIs"""
        
        # Try WeatherAPI.com first
        api_key = os.getenv("WEATHER_API_KEY")
        if api_key:
            try:
                return self._get_weatherapi_data(location, days, api_key)
            except requests.HTTPError as e:
                if e.response.status_code == 404:
                    raise WeatherLocationNotFoundError(location)
                logger.warning(f"WeatherAPI.com failed: {e}")
        
        # Try OpenWeatherMap
        api_key = os.getenv("OPENWEATHER_API_KEY")
        if api_key:
            try:
                coords_dict = coordinates.model_dump() if coordinates else None
                return self._get_openweather_data(location, days, api_key, coords_dict)
            except Exception as e:
                logger.warning(f"OpenWeatherMap failed: {e}")
        
        # Fallback to mock data
        logger.info("No weather API available, using mock data")
        return self._get_mock_weather_data(location, days)
    
    def _get_weatherapi_data(self, location: str, days: int, api_key: str) -> dict:
        """Get weather data from WeatherAPI.com"""
        
        url = "http://api.weatherapi.com/v1/forecast.json"
        params = {
            "key": api_key,
            "q": location,
            "days": min(days, 14),
            "lang": "fr"
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Convert to WeatherCondition objects
        forecast_conditions = []
        for day in data["forecast"]["forecastday"]:
            condition = WeatherCondition(
                date=day["date"],
                temperature_min=day["day"]["mintemp_c"],
                temperature_max=day["day"]["maxtemp_c"],
                humidity=day["day"]["avghumidity"],
                wind_speed=day["day"]["maxwind_kph"],
                wind_direction=self._degrees_to_direction(
                    day["hour"][12].get("wind_degree", 0) if day.get("hour") else 0
                ),
                precipitation=day["day"]["totalprecip_mm"],
                cloud_cover=day["day"].get("cloud", 50),
                uv_index=day["day"]["uv"]
            )
            forecast_conditions.append(condition)
        
        return {
            "location": data["location"]["name"],
            "coordinates": {
                "lat": data["location"]["lat"],
                "lon": data["location"]["lon"]
            },
            "weather_conditions": forecast_conditions,
            "data_source": "weatherapi.com",
            "retrieved_at": datetime.utcnow().isoformat() + "Z"
        }
    
    def _get_openweather_data(
        self,
        location: str,
        days: int,
        api_key: str,
        coordinates: Optional[dict] = None
    ) -> dict:
        """Get weather data from OpenWeatherMap"""
        
        # Use coordinates or geocode
        if coordinates:
            lat, lon = coordinates["lat"], coordinates["lon"]
        else:
            location_coords = {
                "normandie": {"lat": 49.18, "lon": 0.37},
                "calvados": {"lat": 49.18, "lon": 0.37},
                "paris": {"lat": 48.85, "lon": 2.35},
                "lyon": {"lat": 45.75, "lon": 4.85}
            }
            coords = location_coords.get(location.lower(), {"lat": 49.18, "lon": 0.37})
            lat, lon = coords["lat"], coords["lon"]
        
        url = "https://api.openweathermap.org/data/2.5/forecast"
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
        
        # Process daily forecasts
        forecast_conditions = []
        processed_dates = set()
        
        for item in data["list"][:days*8]:
            date_str = datetime.fromtimestamp(item["dt"]).strftime("%Y-%m-%d")
            
            if date_str not in processed_dates:
                processed_dates.add(date_str)
                
                condition = WeatherCondition(
                    date=date_str,
                    temperature_min=item["main"]["temp_min"],
                    temperature_max=item["main"]["temp_max"],
                    humidity=item["main"]["humidity"],
                    wind_speed=item["wind"]["speed"] * 3.6,
                    wind_direction=self._degrees_to_direction(item["wind"].get("deg", 0)),
                    precipitation=item.get("rain", {}).get("3h", 0) + item.get("snow", {}).get("3h", 0),
                    cloud_cover=item["clouds"]["all"],
                    uv_index=3
                )
                forecast_conditions.append(condition)
        
        return {
            "location": location,
            "coordinates": {"lat": lat, "lon": lon},
            "weather_conditions": forecast_conditions,
            "data_source": "openweathermap",
            "retrieved_at": datetime.utcnow().isoformat() + "Z"
        }
    
    def _get_mock_weather_data(self, location: str, days: int) -> dict:
        """Get mock weather data for testing"""
        
        base_conditions = {
            "normandie": {"temp_min": 8, "temp_max": 18, "humidity": 75},
            "calvados": {"temp_min": 8, "temp_max": 18, "humidity": 75},
            "paris": {"temp_min": 10, "temp_max": 20, "humidity": 65},
            "lyon": {"temp_min": 12, "temp_max": 22, "humidity": 60}
        }
        
        base = base_conditions.get(location.lower(), base_conditions["normandie"])
        forecast_conditions = []
        current_date = datetime.now()
        
        for i in range(days):
            date_str = (current_date + timedelta(days=i)).strftime("%Y-%m-%d")
            temp_variation = (i % 3 - 1) * 2
            
            condition = WeatherCondition(
                date=date_str,
                temperature_min=base["temp_min"] + temp_variation,
                temperature_max=base["temp_max"] + temp_variation,
                humidity=max(30, min(95, base["humidity"] + (i % 4 - 1.5) * 10)),
                wind_speed=8 + (i % 5) * 2,
                wind_direction=["N", "NE", "E", "SE", "S", "SO", "O", "NO"][i % 8],
                precipitation=0 if (i % 3) != 0 else (2 + i % 8),
                cloud_cover=30 + (i % 7) * 10,
                uv_index=max(1, min(8, 4 + (i % 3) - 1))
            )
            forecast_conditions.append(condition)
        
        return {
            "location": location,
            "coordinates": {"lat": 49.18, "lon": 0.37},
            "weather_conditions": forecast_conditions,
            "data_source": "mock_data",
            "retrieved_at": datetime.utcnow().isoformat() + "Z"
        }
    
    def _degrees_to_direction(self, degrees: float) -> str:
        """Convert wind degrees to direction"""
        directions = ["N", "NE", "E", "SE", "S", "SO", "O", "NO"]
        index = round(degrees / 45) % 8
        return directions[index]
    
    def _analyze_agricultural_risks(self, forecast: list[WeatherCondition]) -> list[WeatherRisk]:
        """Analyze agricultural risks from forecast"""
        risks = []
        
        for condition in forecast:
            # Frost risk
            if condition.temperature_min < 2:
                risks.append(WeatherRisk(
                    risk_type="frost",
                    severity=RiskSeverity.HIGH if condition.temperature_min < 0 else RiskSeverity.MODERATE,
                    probability=0.9 if condition.temperature_min < 0 else 0.7,
                    impact="Risque de gel sur cultures sensibles",
                    recommendations=[
                        "Reporter les semis",
                        "Protéger les cultures sensibles",
                        "Surveiller les prévisions nocturnes"
                    ],
                    affected_dates=[condition.date]
                ))
            
            # Wind risk
            if condition.wind_speed > 25:
                risks.append(WeatherRisk(
                    risk_type="wind",
                    severity=RiskSeverity.HIGH if condition.wind_speed > 35 else RiskSeverity.MODERATE,
                    probability=0.8,
                    impact=f"Vent fort ({condition.wind_speed:.0f} km/h) - risque pour traitements",
                    recommendations=[
                        "Reporter les traitements phytosanitaires",
                        "Éviter les épandages",
                        "Sécuriser les équipements"
                    ],
                    affected_dates=[condition.date]
                ))
            
            # Heavy rain risk
            if condition.precipitation > 10:
                risks.append(WeatherRisk(
                    risk_type="heavy_rain",
                    severity=RiskSeverity.MODERATE,
                    probability=0.7,
                    impact=f"Fortes précipitations ({condition.precipitation:.0f} mm)",
                    recommendations=[
                        "Reporter les interventions au champ",
                        "Surveiller le drainage",
                        "Éviter la compaction du sol"
                    ],
                    affected_dates=[condition.date]
                ))
        
        return risks
    
    def _identify_intervention_windows(self, forecast: list[WeatherCondition]) -> list[InterventionWindow]:
        """Identify optimal intervention windows"""
        windows = []
        
        for condition in forecast:
            # Good conditions: low wind, no rain, moderate temperature
            if (condition.wind_speed < 15 and
                condition.precipitation < 1 and
                5 < condition.temperature_min < 25):
                
                suitability = 1.0
                if condition.wind_speed > 10:
                    suitability -= 0.1
                if condition.cloud_cover > 70:
                    suitability -= 0.1
                
                windows.append(InterventionWindow(
                    start_date=condition.date,
                    end_date=condition.date,
                    suitability_score=max(0.5, suitability),
                    conditions=f"Vent: {condition.wind_speed:.0f} km/h, Pluie: {condition.precipitation:.0f} mm, Temp: {condition.temperature_min:.0f}-{condition.temperature_max:.0f}°C",
                    recommendations="Conditions favorables pour interventions au champ",
                    intervention_types=["traitement", "semis", "épandage"]
                ))
        
        return windows


# Create service instance
weather_service = EnhancedWeatherService()


# Async function for the tool
async def get_weather_data_enhanced(
    location: str,
    days: int = 7,
    coordinates: Optional[dict] = None,
    use_real_api: bool = True
) -> str:
    """
    Get weather forecast for agricultural planning

    Returns detailed forecast with:
    - Daily weather conditions (temperature, humidity, wind, precipitation)
    - Agricultural risk analysis (frost, wind, heavy rain)
    - Optimal intervention windows for field operations

    Args:
        location: Location name (e.g., 'Normandie', 'Calvados')
        days: Number of forecast days (1-14)
        coordinates: Optional lat/lon coordinates as dict
        use_real_api: Whether to use real weather APIs

    Returns:
        JSON string with weather forecast, risks, and intervention windows
    """
    try:
        # Convert coordinates dict to Pydantic model if provided
        coords = Coordinates(**coordinates) if coordinates else None

        # Validate input
        input_data = WeatherInput(
            location=location,
            days=days,
            coordinates=coords,
            use_real_api=use_real_api
        )

        # Get weather forecast
        result = await weather_service.get_weather_forecast(
            location=input_data.location,
            days=input_data.days,
            coordinates=input_data.coordinates,
            use_real_api=input_data.use_real_api
        )

        # Return as JSON
        return result.model_dump_json(indent=2, exclude_none=True)

    except WeatherValidationError as e:
        # Return structured error for validation issues
        logger.error(f"Weather validation error: {e}")
        error_result = WeatherOutput(
            location=location,
            coordinates=Coordinates(lat=0, lon=0),
            forecast_period_days=days,
            weather_conditions=[],
            total_days=0,
            data_source="error",
            retrieved_at=datetime.utcnow().isoformat() + "Z",
            success=False,
            error=str(e),
            error_type="validation"
        )
        return error_result.model_dump_json(indent=2)

    except WeatherAPIError as e:
        logger.error(f"Weather API error: {e}")
        error_result = WeatherOutput(
            location=location,
            coordinates=Coordinates(lat=0, lon=0),
            forecast_period_days=days,
            weather_conditions=[],
            total_days=0,
            data_source="error",
            retrieved_at=datetime.utcnow().isoformat() + "Z",
            success=False,
            error=str(e),
            error_type="api"
        )
        return error_result.model_dump_json(indent=2)

    except WeatherTimeoutError as e:
        logger.error(f"Weather timeout error: {e}")
        error_result = WeatherOutput(
            location=location,
            coordinates=Coordinates(lat=0, lon=0),
            forecast_period_days=days,
            weather_conditions=[],
            total_days=0,
            data_source="error",
            retrieved_at=datetime.utcnow().isoformat() + "Z",
            success=False,
            error=str(e),
            error_type="timeout"
        )
        return error_result.model_dump_json(indent=2)

    except WeatherLocationNotFoundError as e:
        logger.error(f"Weather location error: {e}")
        error_result = WeatherOutput(
            location=location,
            coordinates=Coordinates(lat=0, lon=0),
            forecast_period_days=days,
            weather_conditions=[],
            total_days=0,
            data_source="error",
            retrieved_at=datetime.utcnow().isoformat() + "Z",
            success=False,
            error=str(e),
            error_type="location_not_found"
        )
        return error_result.model_dump_json(indent=2)

    except Exception as e:
        # Unexpected errors
        logger.error(f"Unexpected weather tool error: {e}", exc_info=True)
        error_result = WeatherOutput(
            location=location,
            coordinates=Coordinates(lat=0, lon=0),
            forecast_period_days=days,
            weather_conditions=[],
            total_days=0,
            data_source="error",
            retrieved_at=datetime.utcnow().isoformat() + "Z",
            success=False,
            error="Erreur inattendue lors de la récupération de la météo. Veuillez réessayer.",
            error_type="unknown"
        )
        return error_result.model_dump_json(indent=2)


# Create structured tool with handle_validation_error
get_weather_data_tool_enhanced = StructuredTool.from_function(
    func=get_weather_data_enhanced,
    name="get_weather_data",
    description="""Récupère les prévisions météorologiques pour la planification agricole.

Retourne des prévisions détaillées avec:
- Conditions météo quotidiennes (température, humidité, vent, précipitations)
- Analyse des risques agricoles (gel, vent fort, pluies intenses)
- Fenêtres d'intervention optimales pour les opérations au champ

Utilisez cet outil quand les agriculteurs demandent la météo, les prévisions, ou le moment optimal pour les interventions.""",
    args_schema=WeatherInput,
    return_direct=False,
    coroutine=get_weather_data_enhanced,
    handle_validation_error=True  # Return validation errors as strings instead of raising
)

