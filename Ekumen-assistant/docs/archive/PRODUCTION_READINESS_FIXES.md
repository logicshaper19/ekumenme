# 🔧 Production Readiness Fixes

**Based on Critical Review Feedback**

---

## 🚨 Issues Identified

Your critical review identified 5 real production issues:

1. ❌ **Optimistic cache hit rate** - 65-79% won't hold in production
2. ❌ **TTL too short** - Weather doesn't change every 5 minutes
3. ❌ **Memory cache will overflow** - 1000 items shared across 25 tools
4. ❌ **Error handling misleading** - Errors swallowed, not propagated
5. ❌ **No rate limiting** - Cache miss storm will get us banned

**All valid. Let's fix them before scaling.**

---

## ✅ Fixes to Implement

### **Fix 1: Dynamic TTL Strategy**

**Problem:** 5-minute TTL is too short for weather forecasts.

**Solution:**

```python
# app/core/cache.py

def smart_weather_ttl(days: int) -> int:
    """
    Dynamic TTL based on forecast range
    
    Logic:
    - Today's forecast: 30 min (changes frequently)
    - 3-day forecast: 1 hour (moderate changes)
    - 7-day forecast: 2 hours (stable)
    - 14-day forecast: 4 hours (very stable)
    
    Args:
        days: Number of forecast days
        
    Returns:
        TTL in seconds
    """
    if days <= 1:
        return 1800  # 30 min for today
    elif days <= 3:
        return 3600  # 1 hour for 3-day
    elif days <= 7:
        return 7200  # 2 hours for week
    else:
        return 14400  # 4 hours for 14-day


# In get_weather_data_tool_enhanced.py
@redis_cache(
    ttl=lambda location, days, **kwargs: smart_weather_ttl(days),
    model_class=WeatherOutput
)
async def get_weather_forecast(...):
    ...
```

**Impact:**
- 20-30% increase in cache hit rate
- Fewer API calls
- Better cost savings

---

### **Fix 2: Separate Caches per Tool Category**

**Problem:** 1000 items shared across 25 tools = 40 items per tool (thrashing).

**Solution:**

```python
# app/core/cache.py

from cachetools import TTLCache
from typing import Dict

# Separate caches per tool category
_caches: Dict[str, TTLCache] = {
    "weather": TTLCache(maxsize=500, ttl=3600),      # 500 items, 1 hour
    "regulatory": TTLCache(maxsize=300, ttl=7200),   # 300 items, 2 hours (stable data)
    "farm_data": TTLCache(maxsize=200, ttl=1800),    # 200 items, 30 min (changing data)
    "crop_health": TTLCache(maxsize=200, ttl=3600),  # 200 items, 1 hour
    "planning": TTLCache(maxsize=150, ttl=3600),     # 150 items, 1 hour
    "sustainability": TTLCache(maxsize=150, ttl=7200), # 150 items, 2 hours
    "default": TTLCache(maxsize=100, ttl=1800),      # 100 items, 30 min
}


def get_memory_cache(category: str = "default") -> TTLCache:
    """Get memory cache for specific tool category"""
    return _caches.get(category, _caches["default"])


def redis_cache(
    ttl: int = 300,
    model_class: Optional[Type[BaseModel]] = None,
    category: str = "default"  # NEW: category parameter
):
    """
    Decorator for caching with category-specific memory cache
    
    Args:
        ttl: Time to live in seconds
        model_class: Pydantic model class
        category: Tool category (weather, regulatory, farm_data, etc.)
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            cache_key = _generate_cache_key(func, args, kwargs)
            
            # Try Redis first
            if redis_client:
                try:
                    cached = redis_client.get(cache_key)
                    if cached:
                        logger.debug(f"🎯 Redis cache hit: {func.__name__}")
                        return _deserialize_pydantic(cached, model_class)
                except Exception as e:
                    logger.warning(f"Redis read error: {e}")
            
            # Try category-specific memory cache
            memory_cache = get_memory_cache(category)
            if cache_key in memory_cache:
                logger.debug(f"🎯 Memory cache hit ({category}): {func.__name__}")
                return memory_cache[cache_key]
            
            # Cache miss - execute function
            logger.debug(f"❌ Cache miss: {func.__name__}")
            result = await func(*args, **kwargs)
            
            # Store in both caches
            try:
                serialized = _serialize_pydantic(result)
                
                if redis_client:
                    try:
                        redis_client.setex(cache_key, ttl, serialized)
                        logger.debug(f"💾 Cached in Redis: {func.__name__}")
                    except Exception as e:
                        logger.warning(f"Redis write error: {e}")
                
                memory_cache[cache_key] = result
                logger.debug(f"💾 Cached in memory ({category}): {func.__name__}")
                
            except Exception as e:
                logger.warning(f"Cache write error: {e}")
            
            return result
        
        return wrapper
    return decorator


# Usage in weather tool:
@redis_cache(
    ttl=smart_weather_ttl(days),
    model_class=WeatherOutput,
    category="weather"  # NEW
)
async def get_weather_forecast(...):
    ...
```

**Impact:**
- No cache thrashing
- Better hit rates per tool
- Predictable memory usage

---

### **Fix 3: Structured Error Handling**

**Problem:** Errors returned as strings, not structured data.

**Solution:**

```python
# app/tools/schemas/weather_schemas.py

class WeatherOutput(BaseModel):
    """Output schema for weather data tool"""
    location: str = Field(description="Location name")
    coordinates: Optional[Coordinates] = Field(default=None, description="Geographic coordinates")
    forecast_period_days: int = Field(description="Number of forecast days")
    weather_conditions: List[WeatherCondition] = Field(
        default_factory=list,
        description="Daily weather forecast"
    )
    risks: List[WeatherRisk] = Field(default_factory=list, description="Agricultural risks")
    intervention_windows: List[InterventionWindow] = Field(
        default_factory=list,
        description="Optimal intervention windows"
    )
    total_days: int = Field(description="Total number of forecast days returned")
    data_source: str = Field(description="Data source")
    retrieved_at: str = Field(description="Timestamp when data was retrieved")
    
    # NEW: Error handling fields
    success: bool = Field(default=True, description="Whether the request was successful")
    error: Optional[str] = Field(default=None, description="Error message if failed")
    error_type: Optional[str] = Field(default=None, description="Error type (validation, api, timeout)")


# In get_weather_data_tool_enhanced.py

async def get_weather_data_enhanced(
    location: str,
    days: int = 7,
    coordinates: Optional[dict] = None,
    use_real_api: bool = True
) -> str:
    """Get weather forecast for agricultural planning"""
    try:
        # Validate input
        coords = Coordinates(**coordinates) if coordinates else None
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
        
        # Return successful result
        return result.model_dump_json(indent=2, exclude_none=True)
        
    except WeatherValidationError as e:
        # Return structured error
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
        
    except Exception as e:
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
```

**Impact:**
- Agent can parse errors properly
- Structured error handling
- Better debugging

---

### **Fix 4: Rate Limiting**

**Problem:** No protection against cache miss storms.

**Solution:**

```python
# requirements.txt
ratelimit==2.2.1

# app/core/rate_limiter.py

import time
import logging
from functools import wraps
from typing import Callable, Dict
from threading import Lock

logger = logging.getLogger(__name__)


class RateLimiter:
    """Simple rate limiter with per-function tracking"""
    
    def __init__(self):
        self._calls: Dict[str, list] = {}
        self._lock = Lock()
    
    def __call__(self, calls: int, period: int):
        """
        Rate limit decorator
        
        Args:
            calls: Number of calls allowed
            period: Time period in seconds
        """
        def decorator(func: Callable) -> Callable:
            func_name = f"{func.__module__}.{func.__name__}"
            
            @wraps(func)
            async def wrapper(*args, **kwargs):
                with self._lock:
                    now = time.time()
                    
                    # Initialize call history
                    if func_name not in self._calls:
                        self._calls[func_name] = []
                    
                    # Remove old calls outside the period
                    self._calls[func_name] = [
                        call_time for call_time in self._calls[func_name]
                        if now - call_time < period
                    ]
                    
                    # Check if we're over the limit
                    if len(self._calls[func_name]) >= calls:
                        wait_time = period - (now - self._calls[func_name][0])
                        logger.warning(
                            f"Rate limit hit for {func_name}. "
                            f"Waiting {wait_time:.1f}s"
                        )
                        time.sleep(wait_time)
                        # Clear old calls after waiting
                        self._calls[func_name] = []
                    
                    # Record this call
                    self._calls[func_name].append(now)
                
                # Execute function
                return await func(*args, **kwargs)
            
            return wrapper
        return decorator


# Global rate limiter
rate_limit = RateLimiter()


# Usage in weather tool:
from app.core.rate_limiter import rate_limit

class EnhancedWeatherService:
    
    @rate_limit(calls=50, period=60)  # 50 calls per minute
    async def _call_weather_api(self, location: str, days: int) -> dict:
        """Rate-limited weather API call"""
        # ... actual API call
```

**Impact:**
- Protection against API bans
- Graceful degradation under load
- Better error messages

---

## 📊 Realistic Production Projections

### **Updated Expectations**

| Metric | Test (Optimistic) | Production Week 1 | Production Steady State |
|--------|-------------------|-------------------|-------------------------|
| **Cache Hit Rate** | 100% (2nd call) | 15-25% | 50-60% |
| **Avg Speedup** | 75% | 10-20% | 35-45% |
| **API Cost Savings** | $219/year | $30/year | $120/year |
| **Error Rate** | 0% | 2-5% (cold cache) | <1% |

**Still good, just realistic.**

---

## ✅ Week 1.5 Checklist

**Before enhancing more tools:**

- [ ] Implement dynamic TTL strategy
- [ ] Implement separate caches per category
- [ ] Fix structured error handling
- [ ] Add rate limiting
- [ ] Add monitoring (cache stats, error rate, latency)
- [ ] Load test (100 concurrent requests)
- [ ] Test cache miss storm scenario
- [ ] Test Redis failure scenario
- [ ] Update documentation with realistic projections

**Estimated time:** 4-6 hours

---

## 🎯 Priority Order

**Critical (Do First):**
1. ✅ Structured error handling (breaks agents)
2. ✅ Separate caches (memory overflow)
3. ✅ Rate limiting (API bans)

**Important (Do Soon):**
4. ✅ Dynamic TTL (better hit rate)
5. ✅ Monitoring (visibility)

**Nice to Have:**
6. ⏳ Load testing (validation)

---

**Next:** Implement these fixes before scaling to more tools.

