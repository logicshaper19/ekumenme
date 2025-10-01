# 🚀 Tool Enhancement Implementation Guide

**Goal:** Upgrade tools to use LangChain best practices with Pydantic schemas, async support, and caching

---

## 📋 Step-by-Step Implementation

### **Step 1: Create Pydantic Schemas (Example: Weather Tool)**

Create `app/tools/schemas/weather_schemas.py`:

```python
"""
Pydantic schemas for weather tools
Provides type safety and validation
"""

from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict
from datetime import datetime
from enum import Enum


class WindDirection(str, Enum):
    """Wind direction enum"""
    N = "N"
    NE = "NE"
    E = "E"
    SE = "SE"
    S = "S"
    SW = "SW"
    W = "W"
    NW = "NW"


class WeatherCondition(BaseModel):
    """Single day weather condition"""
    date: str = Field(description="Date in YYYY-MM-DD format")
    temperature_min: float = Field(ge=-50, le=60, description="Minimum temperature in °C")
    temperature_max: float = Field(ge=-50, le=60, description="Maximum temperature in °C")
    humidity: float = Field(ge=0, le=100, description="Humidity percentage")
    wind_speed: float = Field(ge=0, description="Wind speed in km/h")
    wind_direction: WindDirection = Field(description="Wind direction")
    precipitation: float = Field(ge=0, description="Precipitation in mm")
    cloud_cover: float = Field(ge=0, le=100, description="Cloud cover percentage")
    uv_index: float = Field(ge=0, le=15, description="UV index")
    
    @validator('date')
    def validate_date(cls, v):
        """Validate date format"""
        try:
            datetime.strptime(v, '%Y-%m-%d')
            return v
        except ValueError:
            raise ValueError('Date must be in YYYY-MM-DD format')


class WeatherRisk(BaseModel):
    """Agricultural weather risk"""
    risk_type: str = Field(description="Type of risk (frost, heat, wind, etc.)")
    severity: str = Field(description="Severity level (low, moderate, high, critical)")
    probability: float = Field(ge=0, le=1, description="Probability of occurrence")
    impact: str = Field(description="Impact description")
    recommendations: List[str] = Field(description="Recommended actions")


class InterventionWindow(BaseModel):
    """Optimal intervention window"""
    start_date: str = Field(description="Window start date")
    end_date: str = Field(description="Window end date")
    suitability_score: float = Field(ge=0, le=1, description="Suitability score")
    conditions: str = Field(description="Expected conditions")
    recommendations: str = Field(description="Recommendations")


class WeatherInput(BaseModel):
    """Input schema for weather data tool"""
    location: str = Field(
        description="Location name (e.g., 'Normandie', 'Calvados')",
        min_length=2,
        max_length=100
    )
    days: int = Field(
        default=7,
        ge=1,
        le=14,
        description="Number of forecast days (1-14)"
    )
    coordinates: Optional[Dict[str, float]] = Field(
        default=None,
        description="Optional lat/lon coordinates {'lat': 49.18, 'lon': 0.37}"
    )
    
    @validator('coordinates')
    def validate_coordinates(cls, v):
        """Validate coordinates if provided"""
        if v is not None:
            if 'lat' not in v or 'lon' not in v:
                raise ValueError('Coordinates must have lat and lon keys')
            if not (-90 <= v['lat'] <= 90):
                raise ValueError('Latitude must be between -90 and 90')
            if not (-180 <= v['lon'] <= 180):
                raise ValueError('Longitude must be between -180 and 180')
        return v


class WeatherOutput(BaseModel):
    """Output schema for weather data tool"""
    location: str = Field(description="Location name")
    forecast: List[WeatherCondition] = Field(description="Weather forecast")
    risks: List[WeatherRisk] = Field(description="Agricultural risks")
    intervention_windows: List[InterventionWindow] = Field(description="Optimal intervention windows")
    generated_at: str = Field(description="Generation timestamp")
    
    class Config:
        json_schema_extra = {
            "example": {
                "location": "Normandie",
                "forecast": [
                    {
                        "date": "2024-03-22",
                        "temperature_min": 8.5,
                        "temperature_max": 18.2,
                        "humidity": 72,
                        "wind_speed": 12,
                        "wind_direction": "SW",
                        "precipitation": 0,
                        "cloud_cover": 30,
                        "uv_index": 4
                    }
                ],
                "risks": [],
                "intervention_windows": [],
                "generated_at": "2024-03-22T10:00:00Z"
            }
        }
```

### **Step 2: Create Enhanced Tool with Schemas**

Create `app/tools/weather_agent/get_weather_data_tool_enhanced.py`:

```python
"""
Enhanced Weather Data Tool with Pydantic schemas and async support
"""

import logging
from typing import Dict, Any
from langchain.tools import StructuredTool
from langchain.tools.base import ToolException
from datetime import datetime
import json

from app.tools.schemas.weather_schemas import (
    WeatherInput,
    WeatherOutput,
    WeatherCondition,
    WeatherRisk,
    InterventionWindow
)
from app.core.cache import redis_cache

logger = logging.getLogger(__name__)


class EnhancedWeatherService:
    """Service for fetching and processing weather data"""
    
    @redis_cache(ttl=300)  # Cache for 5 minutes
    async def get_weather_forecast(
        self,
        location: str,
        days: int,
        coordinates: Dict[str, float] = None
    ) -> WeatherOutput:
        """
        Get weather forecast with caching
        
        Args:
            location: Location name
            days: Number of forecast days
            coordinates: Optional lat/lon coordinates
            
        Returns:
            WeatherOutput with forecast, risks, and intervention windows
            
        Raises:
            ToolException: If weather API fails
        """
        try:
            # Fetch weather data from API
            forecast_data = await self._fetch_weather_api(location, days, coordinates)
            
            # Analyze agricultural risks
            risks = await self._analyze_risks(forecast_data)
            
            # Identify intervention windows
            windows = await self._identify_windows(forecast_data)
            
            # Create structured output
            return WeatherOutput(
                location=location,
                forecast=forecast_data,
                risks=risks,
                intervention_windows=windows,
                generated_at=datetime.utcnow().isoformat()
            )
            
        except Exception as e:
            logger.error(f"Weather forecast error: {e}")
            raise ToolException(f"Failed to fetch weather forecast: {str(e)}")
    
    async def _fetch_weather_api(
        self,
        location: str,
        days: int,
        coordinates: Dict[str, float] = None
    ) -> list[WeatherCondition]:
        """Fetch weather data from API"""
        # Implementation here
        # For now, return mock data
        return [
            WeatherCondition(
                date="2024-03-22",
                temperature_min=8.5,
                temperature_max=18.2,
                humidity=72,
                wind_speed=12,
                wind_direction="SW",
                precipitation=0,
                cloud_cover=30,
                uv_index=4
            )
        ]
    
    async def _analyze_risks(self, forecast: list[WeatherCondition]) -> list[WeatherRisk]:
        """Analyze agricultural risks from forecast"""
        risks = []
        
        for condition in forecast:
            # Check for frost risk
            if condition.temperature_min < 2:
                risks.append(WeatherRisk(
                    risk_type="frost",
                    severity="high",
                    probability=0.8,
                    impact="Risque de gel sur cultures sensibles",
                    recommendations=[
                        "Reporter les semis",
                        "Protéger les cultures sensibles",
                        "Surveiller les prévisions"
                    ]
                ))
            
            # Check for wind risk
            if condition.wind_speed > 30:
                risks.append(WeatherRisk(
                    risk_type="wind",
                    severity="moderate",
                    probability=0.7,
                    impact="Vent fort - risque pour traitements",
                    recommendations=[
                        "Reporter les traitements phytosanitaires",
                        "Éviter les épandages"
                    ]
                ))
        
        return risks
    
    async def _identify_windows(
        self,
        forecast: list[WeatherCondition]
    ) -> list[InterventionWindow]:
        """Identify optimal intervention windows"""
        windows = []
        
        # Find suitable days (low wind, no rain, good temperature)
        for i, condition in enumerate(forecast):
            if (condition.wind_speed < 15 and
                condition.precipitation < 1 and
                5 < condition.temperature_min < 25):
                
                windows.append(InterventionWindow(
                    start_date=condition.date,
                    end_date=condition.date,
                    suitability_score=0.9,
                    conditions=f"Vent: {condition.wind_speed} km/h, Pluie: {condition.precipitation} mm",
                    recommendations="Conditions optimales pour interventions"
                ))
        
        return windows


# Create service instance
weather_service = EnhancedWeatherService()


# Async function for the tool
async def get_weather_data_async(
    location: str,
    days: int = 7,
    coordinates: Dict[str, float] = None
) -> str:
    """
    Get weather forecast for agricultural planning
    
    Args:
        location: Location name (e.g., 'Normandie', 'Calvados')
        days: Number of forecast days (1-14)
        coordinates: Optional lat/lon coordinates
        
    Returns:
        JSON string with weather forecast, risks, and intervention windows
    """
    try:
        # Validate input
        input_data = WeatherInput(
            location=location,
            days=days,
            coordinates=coordinates
        )
        
        # Get weather forecast
        result = await weather_service.get_weather_forecast(
            location=input_data.location,
            days=input_data.days,
            coordinates=input_data.coordinates
        )
        
        # Return as JSON
        return result.model_dump_json(indent=2, exclude_none=True)
        
    except Exception as e:
        logger.error(f"Weather tool error: {e}")
        raise ToolException(f"Weather tool failed: {str(e)}")


# Create structured tool
get_weather_data_tool = StructuredTool.from_function(
    func=get_weather_data_async,
    name="get_weather_data",
    description="""Get weather forecast for agricultural planning.
    
Returns detailed forecast with:
- Daily weather conditions (temperature, humidity, wind, precipitation)
- Agricultural risk analysis (frost, wind, heat, etc.)
- Optimal intervention windows for field operations

Use this tool when farmers ask about weather, forecast, or optimal timing for operations.""",
    args_schema=WeatherInput,
    return_direct=False,
    coroutine=get_weather_data_async  # Enable async execution
)
```

### **Step 3: Add Caching Service**

Create `app/core/cache.py`:

```python
"""
Caching utilities for tools
"""

import functools
import hashlib
import json
import logging
from typing import Any, Callable
import redis
from app.core.config import settings

logger = logging.getLogger(__name__)

# Initialize Redis client
try:
    redis_client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=0,
        decode_responses=True
    )
except Exception as e:
    logger.warning(f"Redis not available: {e}")
    redis_client = None


def redis_cache(ttl: int = 300):
    """
    Decorator for caching function results in Redis
    
    Args:
        ttl: Time to live in seconds (default: 5 minutes)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            if redis_client is None:
                # No caching if Redis not available
                return await func(*args, **kwargs)
            
            # Create cache key from function name and arguments
            key_data = {
                "func": func.__name__,
                "args": args,
                "kwargs": kwargs
            }
            key_str = json.dumps(key_data, sort_keys=True)
            cache_key = f"tool_cache:{hashlib.md5(key_str.encode()).hexdigest()}"
            
            # Try to get from cache
            try:
                cached = redis_client.get(cache_key)
                if cached:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return json.loads(cached)
            except Exception as e:
                logger.warning(f"Cache read error: {e}")
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Store in cache
            try:
                redis_client.setex(
                    cache_key,
                    ttl,
                    json.dumps(result, default=str)
                )
                logger.debug(f"Cached result for {func.__name__}")
            except Exception as e:
                logger.warning(f"Cache write error: {e}")
            
            return result
        
        return wrapper
    return decorator
```

### **Step 4: Update Tool Registry**

Update `app/services/tool_registry_service.py`:

```python
# Import enhanced tools
from app.tools.weather_agent.get_weather_data_tool_enhanced import get_weather_data_tool

class ToolRegistryService:
    def __init__(self):
        self.tools = {}
        self._register_enhanced_tools()
    
    def _register_enhanced_tools(self):
        """Register enhanced tools with Pydantic schemas"""
        # Weather tools
        self.tools["get_weather_data"] = get_weather_data_tool
        
        # Add more enhanced tools...
```

---

## 🧪 Testing Enhanced Tools

Create `test_enhanced_weather_tool.py`:

```python
import asyncio
from app.tools.weather_agent.get_weather_data_tool_enhanced import get_weather_data_tool

async def test_weather_tool():
    """Test enhanced weather tool"""
    
    # Test with valid input
    result = await get_weather_data_tool.arun(
        location="Normandie",
        days=7
    )
    print("✅ Weather tool result:")
    print(result)
    
    # Test with coordinates
    result2 = await get_weather_data_tool.arun(
        location="Calvados",
        days=5,
        coordinates={"lat": 49.18, "lon": 0.37}
    )
    print("\n✅ Weather tool with coordinates:")
    print(result2)
    
    # Test validation (should fail)
    try:
        result3 = await get_weather_data_tool.arun(
            location="X",  # Too short
            days=20  # Too many days
        )
    except Exception as e:
        print(f"\n✅ Validation working: {e}")

if __name__ == "__main__":
    asyncio.run(test_weather_tool())
```

---

## 📋 Migration Checklist

### **Phase 1: Core Tools (Week 1)**

- [ ] Create `app/tools/schemas/` directory
- [ ] Create weather schemas
- [ ] Create regulatory schemas
- [ ] Create farm data schemas
- [ ] Implement caching service
- [ ] Enhance weather tools (4 tools)
- [ ] Enhance regulatory tools (5 tools)
- [ ] Test enhanced tools

### **Phase 2: Remaining Tools (Week 2)**

- [ ] Enhance crop health tools (4 tools)
- [ ] Enhance planning tools (5 tools)
- [ ] Enhance farm data tools (5 tools)
- [ ] Enhance sustainability tools (5 tools)
- [ ] Update tool registry
- [ ] Update agent configurations

### **Phase 3: Integration (Week 3)**

- [ ] Integrate with LCEL service
- [ ] Add streaming support
- [ ] Add error recovery
- [ ] Performance testing
- [ ] Documentation

---

**Next:** Start with weather tools as proof of concept!

