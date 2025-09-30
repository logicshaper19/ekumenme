"""
Caching utilities with Pydantic support and fallback

Provides Redis caching with in-memory fallback for tool results.
Handles Pydantic model serialization/deserialization properly.
"""

import functools
import hashlib
import json
import logging
from typing import Any, Callable, Optional, Type
from pydantic import BaseModel
from cachetools import TTLCache
import redis

from app.core.config import settings

logger = logging.getLogger(__name__)


# ============================================================================
# Dynamic TTL Strategies
# ============================================================================

def smart_weather_ttl(days: int) -> int:
    """
    Dynamic TTL based on weather forecast range

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

# Separate caches per tool category to prevent thrashing
_caches: dict = {
    "weather": TTLCache(maxsize=500, ttl=3600),      # 500 items, 1 hour
    "regulatory": TTLCache(maxsize=300, ttl=7200),   # 300 items, 2 hours (stable data)
    "farm_data": TTLCache(maxsize=200, ttl=1800),    # 200 items, 30 min (changing data)
    "crop_health": TTLCache(maxsize=200, ttl=3600),  # 200 items, 1 hour
    "planning": TTLCache(maxsize=150, ttl=3600),     # 150 items, 1 hour
    "sustainability": TTLCache(maxsize=150, ttl=7200), # 150 items, 2 hours
    "default": TTLCache(maxsize=100, ttl=1800),      # 100 items, 30 min
}


def get_memory_cache(category: str = "default") -> TTLCache:
    """
    Get memory cache for specific tool category

    Args:
        category: Tool category (weather, regulatory, farm_data, etc.)

    Returns:
        TTLCache for the category
    """
    return _caches.get(category, _caches["default"])

# Try to initialize Redis
redis_client: Optional[redis.Redis] = None
try:
    # Parse Redis URL
    redis_url = settings.REDIS_URL
    redis_client = redis.from_url(
        redis_url,
        decode_responses=True,
        socket_connect_timeout=2,
        socket_timeout=2
    )
    # Test connection
    redis_client.ping()
    logger.info("✅ Redis cache available")
except Exception as e:
    logger.warning(f"⚠️ Redis not available, using in-memory cache only: {e}")
    redis_client = None


def _generate_cache_key(func: Callable, args: tuple, kwargs: dict) -> str:
    """
    Generate cache key from function and arguments
    
    Args:
        func: Function being cached
        args: Positional arguments
        kwargs: Keyword arguments
        
    Returns:
        Cache key string
    """
    key_data = {
        "func": f"{func.__module__}.{func.__name__}",
        "args": str(args),
        "kwargs": str(sorted(kwargs.items()))
    }
    key_str = json.dumps(key_data, sort_keys=True)
    hash_key = hashlib.md5(key_str.encode()).hexdigest()
    return f"{settings.CACHE_PREFIX}tool:{hash_key}"


def _serialize_pydantic(obj: Any) -> str:
    """
    Serialize Pydantic model or regular object to JSON
    
    Args:
        obj: Object to serialize (Pydantic model or regular object)
        
    Returns:
        JSON string
    """
    if isinstance(obj, BaseModel):
        # Use Pydantic's JSON serializer
        return obj.model_dump_json()
    return json.dumps(obj, default=str)


def _deserialize_pydantic(data: str, model_class: Optional[Type[BaseModel]] = None) -> Any:
    """
    Deserialize JSON to Pydantic model or regular object
    
    Args:
        data: JSON string
        model_class: Optional Pydantic model class for deserialization
        
    Returns:
        Deserialized object
    """
    if model_class and issubclass(model_class, BaseModel):
        # Reconstruct Pydantic model
        return model_class.model_validate_json(data)
    return json.loads(data)


def redis_cache(
    ttl: int = 300,
    model_class: Optional[Type[BaseModel]] = None,
    category: str = "default"
):
    """
    Decorator for caching with Pydantic support and category-specific fallback

    Caches function results in Redis (if available) and category-specific in-memory cache.
    Properly handles Pydantic model serialization/deserialization.

    Args:
        ttl: Time to live in seconds (default: 5 minutes)
        model_class: Optional Pydantic model class for deserialization
        category: Tool category for memory cache (weather, regulatory, farm_data, etc.)

    Example:
        ```python
        @redis_cache(ttl=3600, model_class=WeatherOutput, category="weather")
        async def get_weather(...) -> WeatherOutput:
            return WeatherOutput(...)
        ```

    Returns:
        Decorated function with caching
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

                # Store in Redis
                if redis_client:
                    try:
                        redis_client.setex(cache_key, ttl, serialized)
                        logger.debug(f"💾 Cached in Redis: {func.__name__} (TTL: {ttl}s)")
                    except Exception as e:
                        logger.warning(f"Redis write error: {e}")

                # Store in category-specific memory cache
                memory_cache[cache_key] = result
                logger.debug(f"💾 Cached in memory ({category}): {func.__name__}")

            except Exception as e:
                logger.warning(f"Cache write error: {e}")

            return result

        return wrapper
    return decorator


def clear_cache(pattern: str = "*", category: Optional[str] = None):
    """
    Clear cache by pattern and/or category

    Args:
        pattern: Pattern to match cache keys (default: "*" for all)
        category: Optional category to clear (weather, regulatory, etc.)

    Example:
        ```python
        # Clear all weather tool caches
        clear_cache("weather*", category="weather")

        # Clear all caches
        clear_cache()

        # Clear specific category
        clear_cache(category="weather")
        ```
    """
    if redis_client:
        try:
            # Find matching keys
            search_pattern = f"{settings.CACHE_PREFIX}tool:{pattern}"
            keys = redis_client.keys(search_pattern)
            if keys:
                redis_client.delete(*keys)
                logger.info(f"✅ Cleared {len(keys)} Redis cache entries matching '{pattern}'")
        except Exception as e:
            logger.error(f"Cache clear error: {e}")

    # Clear memory cache(s)
    if category:
        # Clear specific category
        cache = get_memory_cache(category)
        cache.clear()
        logger.info(f"✅ Cleared memory cache for category '{category}'")
    else:
        # Clear all categories
        for cat, cache in _caches.items():
            cache.clear()
        logger.info("✅ Cleared all memory caches")


def get_cache_stats() -> dict:
    """
    Get cache statistics for all categories

    Returns:
        Dictionary with cache stats including per-category breakdown
    """
    stats = {
        "redis_available": redis_client is not None,
        "memory_caches": {},
        "total_memory_items": 0,
    }

    # Get stats for each category
    for category, cache in _caches.items():
        stats["memory_caches"][category] = {
            "size": len(cache),
            "maxsize": cache.maxsize,
            "utilization": len(cache) / cache.maxsize * 100 if cache.maxsize > 0 else 0
        }
        stats["total_memory_items"] += len(cache)

    # Get Redis stats
    if redis_client:
        try:
            info = redis_client.info("stats")
            stats["redis_keys"] = redis_client.dbsize()
            stats["redis_hits"] = info.get("keyspace_hits", 0)
            stats["redis_misses"] = info.get("keyspace_misses", 0)

            # Calculate hit rate
            total = stats["redis_hits"] + stats["redis_misses"]
            if total > 0:
                stats["redis_hit_rate"] = stats["redis_hits"] / total * 100
            else:
                stats["redis_hit_rate"] = 0
        except Exception as e:
            logger.error(f"Error getting Redis stats: {e}")

    return stats


# Sync version for non-async functions
def redis_cache_sync(ttl: int = 300, model_class: Optional[Type[BaseModel]] = None):
    """
    Synchronous version of redis_cache decorator
    
    Args:
        ttl: Time to live in seconds
        model_class: Optional Pydantic model class
        
    Returns:
        Decorated function with caching
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
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
            
            # Try memory cache
            if cache_key in memory_cache:
                logger.debug(f"🎯 Memory cache hit: {func.__name__}")
                return memory_cache[cache_key]
            
            # Cache miss - execute function
            logger.debug(f"❌ Cache miss: {func.__name__}")
            result = func(*args, **kwargs)
            
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
                logger.debug(f"💾 Cached in memory: {func.__name__}")
                
            except Exception as e:
                logger.warning(f"Cache write error: {e}")
            
            return result
        
        return wrapper
    return decorator

