"""
Performance Optimization Service
Advanced caching, query optimization, and performance monitoring
"""

import asyncio
import json
import logging
import hashlib
import time
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime, timedelta
from functools import wraps
import pickle
import os
from collections import defaultdict, deque
import statistics

import redis
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.core.config import settings
from app.services.error_recovery_service import ErrorRecoveryService, ErrorContext, ErrorSeverity

logger = logging.getLogger(__name__)


class QueryCache:
    """Advanced query caching system"""
    
    def __init__(self):
        self.redis_client = None
        self.local_cache = {}
        self.cache_stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0
        }
        self._initialize_redis()
    
    def _initialize_redis(self):
        """Initialize Redis connection"""
        try:
            if hasattr(settings, 'REDIS_URL') and settings.REDIS_URL:
                self.redis_client = redis.from_url(settings.REDIS_URL)
                self.redis_client.ping()
                logger.info("Redis cache initialized")
            else:
                logger.warning("Redis not configured, using local cache only")
        except Exception as e:
            logger.warning(f"Redis connection failed, using local cache: {e}")
    
    def _generate_cache_key(self, query: str, context: Dict[str, Any]) -> str:
        """Generate cache key from query and context"""
        # Create deterministic hash
        cache_data = {
            "query": query.lower().strip(),
            "context": {k: v for k, v in context.items() 
                       if k in ["farm_siret", "crop_type", "location"]}
        }
        cache_string = json.dumps(cache_data, sort_keys=True)
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    async def get(self, query: str, context: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Get cached result"""
        cache_key = self._generate_cache_key(query, context)
        
        try:
            # Try Redis first
            if self.redis_client:
                cached_data = self.redis_client.get(f"agri_cache:{cache_key}")
                if cached_data:
                    result = json.loads(cached_data)
                    # Check if not expired
                    if datetime.fromisoformat(result["expires_at"]) > datetime.now():
                        self.cache_stats["hits"] += 1
                        logger.debug(f"Cache hit (Redis): {cache_key}")
                        return result["data"]
                    else:
                        # Remove expired entry
                        self.redis_client.delete(f"agri_cache:{cache_key}")
            
            # Try local cache
            if cache_key in self.local_cache:
                cached_entry = self.local_cache[cache_key]
                if cached_entry["expires_at"] > datetime.now():
                    self.cache_stats["hits"] += 1
                    logger.debug(f"Cache hit (local): {cache_key}")
                    return cached_entry["data"]
                else:
                    # Remove expired entry
                    del self.local_cache[cache_key]
            
            self.cache_stats["misses"] += 1
            return None
            
        except Exception as e:
            logger.error(f"Cache get error: {e}")
            self.cache_stats["misses"] += 1
            return None
    
    async def set(
        self,
        query: str,
        context: Dict[str, Any],
        data: Dict[str, Any],
        ttl_minutes: int = 60
    ):
        """Set cached result"""
        cache_key = self._generate_cache_key(query, context)
        expires_at = datetime.now() + timedelta(minutes=ttl_minutes)
        
        cache_entry = {
            "data": data,
            "expires_at": expires_at.isoformat(),
            "created_at": datetime.now().isoformat()
        }
        
        try:
            # Store in Redis
            if self.redis_client:
                self.redis_client.setex(
                    f"agri_cache:{cache_key}",
                    ttl_minutes * 60,
                    json.dumps(cache_entry)
                )
            
            # Store in local cache (with size limit)
            if len(self.local_cache) > 1000:  # Limit local cache size
                # Remove oldest entries
                oldest_keys = sorted(
                    self.local_cache.keys(),
                    key=lambda k: self.local_cache[k]["created_at"]
                )[:100]
                for key in oldest_keys:
                    del self.local_cache[key]
                self.cache_stats["evictions"] += len(oldest_keys)
            
            self.local_cache[cache_key] = {
                "data": data,
                "expires_at": expires_at,
                "created_at": datetime.now()
            }
            
            logger.debug(f"Cache set: {cache_key}")
            
        except Exception as e:
            logger.error(f"Cache set error: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.cache_stats["hits"] + self.cache_stats["misses"]
        hit_rate = (self.cache_stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        return {
            **self.cache_stats,
            "hit_rate_percent": round(hit_rate, 2),
            "local_cache_size": len(self.local_cache),
            "redis_available": self.redis_client is not None
        }


class PerformanceMonitor:
    """Performance monitoring and metrics collection"""
    
    def __init__(self):
        self.metrics = defaultdict(list)
        self.response_times = deque(maxlen=1000)  # Keep last 1000 response times
        self.error_counts = defaultdict(int)
        self.start_time = datetime.now()
    
    def record_response_time(self, operation: str, duration: float):
        """Record response time for an operation"""
        self.metrics[f"{operation}_response_time"].append(duration)
        self.response_times.append(duration)
        
        # Log slow operations
        if duration > 5.0:  # 5 seconds threshold
            logger.warning(f"Slow operation detected: {operation} took {duration:.2f}s")
    
    def record_error(self, operation: str, error: str):
        """Record error for an operation"""
        self.error_counts[f"{operation}_error"] += 1
        logger.error(f"Operation error: {operation} - {error}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        stats = {
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
            "total_requests": len(self.response_times),
            "error_counts": dict(self.error_counts)
        }
        
        if self.response_times:
            stats["response_times"] = {
                "avg": statistics.mean(self.response_times),
                "median": statistics.median(self.response_times),
                "p95": self._percentile(self.response_times, 95),
                "p99": self._percentile(self.response_times, 99),
                "min": min(self.response_times),
                "max": max(self.response_times)
            }
        
        # Operation-specific stats
        operation_stats = {}
        for operation, times in self.metrics.items():
            if times and operation.endswith("_response_time"):
                op_name = operation.replace("_response_time", "")
                operation_stats[op_name] = {
                    "count": len(times),
                    "avg_time": statistics.mean(times),
                    "total_time": sum(times)
                }
        
        stats["operations"] = operation_stats
        return stats
    
    def _percentile(self, data: List[float], percentile: int) -> float:
        """Calculate percentile"""
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]


class DatabaseOptimizer:
    """Database query optimization"""
    
    def __init__(self):
        self.query_stats = defaultdict(list)
        self.slow_queries = []
    
    async def execute_optimized_query(
        self,
        session: AsyncSession,
        query: str,
        params: Dict[str, Any] = None,
        cache_key: str = None
    ) -> Any:
        """Execute database query with optimization"""
        start_time = time.time()
        
        try:
            # Execute query
            result = await session.execute(text(query), params or {})
            execution_time = time.time() - start_time
            
            # Record performance
            self.query_stats[cache_key or "unknown"].append(execution_time)
            
            # Log slow queries
            if execution_time > 1.0:  # 1 second threshold
                self.slow_queries.append({
                    "query": query[:200] + "..." if len(query) > 200 else query,
                    "execution_time": execution_time,
                    "timestamp": datetime.now().isoformat(),
                    "params": params
                })
                logger.warning(f"Slow query detected: {execution_time:.2f}s")
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"Query failed after {execution_time:.2f}s: {e}")
            raise
    
    def get_query_stats(self) -> Dict[str, Any]:
        """Get database query statistics"""
        stats = {
            "total_queries": sum(len(times) for times in self.query_stats.values()),
            "slow_queries_count": len(self.slow_queries),
            "recent_slow_queries": self.slow_queries[-10:] if self.slow_queries else []
        }
        
        # Query type statistics
        query_type_stats = {}
        for query_type, times in self.query_stats.items():
            if times:
                query_type_stats[query_type] = {
                    "count": len(times),
                    "avg_time": statistics.mean(times),
                    "max_time": max(times),
                    "total_time": sum(times)
                }
        
        stats["query_types"] = query_type_stats
        return stats


def performance_monitor(operation_name: str):
    """Decorator for monitoring function performance"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Get monitor from service if available
                if hasattr(args[0], 'performance_monitor'):
                    args[0].performance_monitor.record_response_time(operation_name, duration)
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                
                # Record error
                if hasattr(args[0], 'performance_monitor'):
                    args[0].performance_monitor.record_error(operation_name, str(e))
                
                raise
        
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                
                # Get monitor from service if available
                if hasattr(args[0], 'performance_monitor'):
                    args[0].performance_monitor.record_response_time(operation_name, duration)
                
                return result
            except Exception as e:
                duration = time.time() - start_time
                
                # Record error
                if hasattr(args[0], 'performance_monitor'):
                    args[0].performance_monitor.record_error(operation_name, str(e))
                
                raise
        
        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    
    return decorator


class PerformanceOptimizationService:
    """Main service for performance optimization"""
    
    def __init__(self):
        self.cache = QueryCache()
        self.performance_monitor = PerformanceMonitor()
        self.db_optimizer = DatabaseOptimizer()
        self.optimization_rules = self._load_optimization_rules()
    
    def _load_optimization_rules(self) -> Dict[str, Any]:
        """Load performance optimization rules"""
        return {
            "cache_ttl": {
                "weather_data": 30,  # 30 minutes
                "regulatory_data": 1440,  # 24 hours
                "farm_data": 60,  # 1 hour
                "general_query": 15  # 15 minutes
            },
            "query_timeout": {
                "default": 30,  # 30 seconds
                "complex_analysis": 60,  # 1 minute
                "data_export": 300  # 5 minutes
            },
            "batch_sizes": {
                "database_operations": 100,
                "api_calls": 10,
                "file_processing": 50
            }
        }
    
    async def optimize_query_execution(
        self,
        query_func: Callable,
        query: str,
        context: Dict[str, Any],
        cache_category: str = "general_query"
    ) -> Dict[str, Any]:
        """Optimize query execution with caching and monitoring"""
        
        # Check cache first
        cached_result = await self.cache.get(query, context)
        if cached_result:
            return {
                **cached_result,
                "from_cache": True,
                "cache_hit": True
            }
        
        # Execute query with monitoring
        start_time = time.time()
        try:
            result = await query_func(query, context)
            execution_time = time.time() - start_time
            
            # Record performance
            self.performance_monitor.record_response_time("query_execution", execution_time)
            
            # Cache result
            ttl = self.optimization_rules["cache_ttl"].get(cache_category, 15)
            await self.cache.set(query, context, result, ttl)
            
            return {
                **result,
                "from_cache": False,
                "cache_hit": False,
                "execution_time": execution_time
            }
            
        except Exception as e:
            execution_time = time.time() - start_time
            self.performance_monitor.record_error("query_execution", str(e))
            raise
    
    async def batch_process_operations(
        self,
        operations: List[Callable],
        batch_size: int = None
    ) -> List[Any]:
        """Process operations in optimized batches"""
        
        if batch_size is None:
            batch_size = self.optimization_rules["batch_sizes"]["database_operations"]
        
        results = []
        
        for i in range(0, len(operations), batch_size):
            batch = operations[i:i + batch_size]
            
            # Execute batch concurrently
            batch_tasks = [op() for op in batch]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            results.extend(batch_results)
        
        return results
    
    def get_comprehensive_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        return {
            "cache_stats": self.cache.get_stats(),
            "performance_stats": self.performance_monitor.get_performance_stats(),
            "database_stats": self.db_optimizer.get_query_stats(),
            "optimization_rules": self.optimization_rules,
            "timestamp": datetime.now().isoformat()
        }
    
    async def cleanup_resources(self):
        """Cleanup resources and optimize memory usage"""
        try:
            # Clear old cache entries
            if hasattr(self.cache, 'local_cache'):
                old_entries = []
                now = datetime.now()
                
                for key, entry in self.cache.local_cache.items():
                    if entry["expires_at"] < now:
                        old_entries.append(key)
                
                for key in old_entries:
                    del self.cache.local_cache[key]
                
                logger.info(f"Cleaned up {len(old_entries)} expired cache entries")
            
            # Clear old performance metrics
            cutoff_time = datetime.now() - timedelta(hours=24)
            
            # Keep only recent slow queries
            self.db_optimizer.slow_queries = [
                q for q in self.db_optimizer.slow_queries
                if datetime.fromisoformat(q["timestamp"]) > cutoff_time
            ]
            
            logger.info("Resource cleanup completed")
            
        except Exception as e:
            logger.error(f"Resource cleanup failed: {e}")
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform system health check"""
        health = {
            "status": "healthy",
            "checks": {},
            "timestamp": datetime.now().isoformat()
        }
        
        # Cache health
        try:
            cache_stats = self.cache.get_stats()
            health["checks"]["cache"] = {
                "status": "healthy",
                "hit_rate": cache_stats["hit_rate_percent"],
                "redis_available": cache_stats["redis_available"]
            }
        except Exception as e:
            health["checks"]["cache"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health["status"] = "degraded"
        
        # Performance health
        try:
            perf_stats = self.performance_monitor.get_performance_stats()
            avg_response_time = perf_stats.get("response_times", {}).get("avg", 0)
            
            health["checks"]["performance"] = {
                "status": "healthy" if avg_response_time < 2.0 else "degraded",
                "avg_response_time": avg_response_time,
                "total_requests": perf_stats["total_requests"]
            }
            
            if avg_response_time >= 2.0:
                health["status"] = "degraded"
                
        except Exception as e:
            health["checks"]["performance"] = {
                "status": "unhealthy",
                "error": str(e)
            }
            health["status"] = "degraded"
        
        return health
