"""
Improved Voice Journal Monitoring and Observability
Fixed version with proper memory management, async processing, and self-monitoring
"""

from typing import Dict, List, Optional, Any
import logging
import time
import asyncio
import psutil
import gc
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import json
import threading
from concurrent.futures import ThreadPoolExecutor

logger = logging.getLogger(__name__)


@dataclass
class VoiceEvent:
    """Voice processing event for monitoring"""
    event_type: str  # 'transcription', 'validation', 'save', 'error'
    timestamp: datetime
    duration_ms: Optional[float] = None
    user_id: Optional[str] = None
    org_id: Optional[str] = None
    entry_id: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class PerformanceMetrics:
    """Performance metrics for voice processing"""
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_transcription_time_ms: float = 0.0
    average_validation_time_ms: float = 0.0
    average_total_time_ms: float = 0.0
    transcription_errors: int = 0
    validation_errors: int = 0
    save_errors: int = 0
    ephy_lookup_errors: int = 0
    weather_lookup_errors: int = 0


@dataclass
class MonitoringHealth:
    """Health metrics for the monitoring system itself"""
    events_processed: int = 0
    events_dropped: int = 0
    queue_size: int = 0
    memory_usage_mb: float = 0.0
    last_error: Optional[str] = None
    processing_lag_ms: float = 0.0
    cleanup_runs: int = 0


@dataclass
class ToolMetrics:
    """Metrics for individual tools"""
    usage_count: int = 0
    total_duration_ms: float = 0.0
    error_count: int = 0
    last_used: Optional[datetime] = None


@dataclass
class AgentMetrics:
    """Metrics for agent reasoning"""
    total_queries: int = 0
    avg_tools_per_query: float = 0.0
    max_tools_per_query: int = 0
    reasoning_time_ms: float = 0.0
    failed_reasoning: int = 0
    successful_reasoning: int = 0


@dataclass
class QueueMetrics:
    """Metrics for validation queue"""
    current_size: int = 0
    max_size: int = 0
    avg_wait_time_ms: float = 0.0
    total_processed: int = 0
    total_failed: int = 0


class ImprovedVoiceMonitoringService:
    """Improved monitoring service with proper memory management and async processing"""
    
    def __init__(self, max_events: int = 10000, metrics_window_minutes: int = 60):
        self.max_events = max_events
        self.metrics_window_minutes = metrics_window_minutes
        
        # Event storage with proper cleanup
        self.events: deque = deque(maxlen=max_events)
        self.user_events: Dict[str, deque] = {}
        self.org_events: Dict[str, deque] = {}
        
        # Performance tracking with rolling windows
        self.performance_metrics = PerformanceMetrics()
        self.recent_transcription_times = deque(maxlen=100)
        self.recent_validation_times = deque(maxlen=100)
        self.recent_total_times = deque(maxlen=100)
        
        # Tool-specific metrics
        self.tool_metrics: Dict[str, ToolMetrics] = defaultdict(ToolMetrics)
        
        # Agent metrics
        self.agent_metrics = AgentMetrics()
        self.agent_tool_counts = deque(maxlen=100)  # Last 100 queries
        
        # Queue metrics
        self.queue_metrics = QueueMetrics()
        self.queue_wait_times = deque(maxlen=100)
        
        # Error tracking
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.recent_errors: deque = deque(maxlen=100)
        
        # Real-time metrics
        self.active_connections = 0
        self.processing_queue_size = 0
        self.last_activity = datetime.now()
        self.start_time = datetime.now()
        
        # Self-monitoring
        self.monitoring_health = MonitoringHealth()
        self.event_queue = asyncio.Queue(maxsize=10000)
        self.cleanup_lock = threading.Lock()
        
        # Start background workers
        self._start_background_workers()
        
        logger.info("Improved voice monitoring service initialized")
    
    def _start_background_workers(self):
        """Start background workers for async processing"""
        # Event processor
        asyncio.create_task(self._event_processor())
        
        # Cleanup worker
        asyncio.create_task(self._cleanup_worker())
        
        # Metrics updater
        asyncio.create_task(self._metrics_updater())
        
        # Self-monitoring
        asyncio.create_task(self._self_monitoring())
    
    async def _event_processor(self):
        """Background worker to process events asynchronously"""
        while True:
            try:
                event = await self.event_queue.get()
                await self._process_event(event)
                self.event_queue.task_done()
            except Exception as e:
                logger.error(f"Error in event processor: {e}")
                self.monitoring_health.last_error = str(e)
                await asyncio.sleep(1)
    
    async def _process_event(self, event: VoiceEvent):
        """Process a single event (non-blocking)"""
        try:
            # Add to main event queue
            self.events.append(event)
            
            # Add to user-specific queue (with cleanup)
            if event.user_id:
                if event.user_id not in self.user_events:
                    self.user_events[event.user_id] = deque(maxlen=1000)
                self.user_events[event.user_id].append(event)
            
            # Add to org-specific queue (with cleanup)
            if event.org_id:
                if event.org_id not in self.org_events:
                    self.org_events[event.org_id] = deque(maxlen=1000)
                self.org_events[event.org_id].append(event)
            
            # Update performance metrics
            self._update_performance_metrics(event)
            
            # Update tool metrics
            if event.metadata and 'tool_name' in event.metadata:
                self._update_tool_metrics(event.metadata['tool_name'], event)
            
            # Track errors
            if not event.success and event.error_message:
                self.error_counts[event.error_message] += 1
                self.recent_errors.append({
                    'timestamp': event.timestamp.isoformat(),
                    'error': event.error_message,
                    'user_id': event.user_id,
                    'entry_id': event.entry_id
                })
            
            # Update last activity
            self.last_activity = datetime.now()
            self.monitoring_health.events_processed += 1
            
        except Exception as e:
            logger.error(f"Error processing event: {e}")
            self.monitoring_health.last_error = str(e)
    
    async def _cleanup_worker(self):
        """Background worker to clean up old data"""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                await self._cleanup_old_data()
                self.monitoring_health.cleanup_runs += 1
            except Exception as e:
                logger.error(f"Error in cleanup worker: {e}")
                self.monitoring_health.last_error = str(e)
    
    async def _cleanup_old_data(self):
        """Clean up old user/org event queues"""
        with self.cleanup_lock:
            cutoff = datetime.now() - timedelta(hours=24)
            
            # Clean up inactive users
            inactive_users = []
            for user_id, events in self.user_events.items():
                if not events or events[-1].timestamp < cutoff:
                    inactive_users.append(user_id)
            
            for user_id in inactive_users:
                del self.user_events[user_id]
            
            # Clean up inactive orgs
            inactive_orgs = []
            for org_id, events in self.org_events.items():
                if not events or events[-1].timestamp < cutoff:
                    inactive_orgs.append(org_id)
            
            for org_id in inactive_orgs:
                del self.org_events[org_id]
            
            # Force garbage collection
            gc.collect()
            
            logger.info(f"Cleanup completed: removed {len(inactive_users)} users, {len(inactive_orgs)} orgs")
    
    async def _metrics_updater(self):
        """Background worker to update rolling metrics"""
        while True:
            try:
                await asyncio.sleep(60)  # Update every minute
                self._update_rolling_metrics()
            except Exception as e:
                logger.error(f"Error in metrics updater: {e}")
                self.monitoring_health.last_error = str(e)
    
    def _update_rolling_metrics(self):
        """Update rolling averages using time windows"""
        # Update transcription time average
        if self.recent_transcription_times:
            self.performance_metrics.average_transcription_time_ms = (
                sum(self.recent_transcription_times) / len(self.recent_transcription_times)
            )
        
        # Update validation time average
        if self.recent_validation_times:
            self.performance_metrics.average_validation_time_ms = (
                sum(self.recent_validation_times) / len(self.recent_validation_times)
            )
        
        # Update total time average
        if self.recent_total_times:
            self.performance_metrics.average_total_time_ms = (
                sum(self.recent_total_times) / len(self.recent_total_times)
            )
        
        # Update agent metrics
        if self.agent_tool_counts:
            self.agent_metrics.avg_tools_per_query = (
                sum(self.agent_tool_counts) / len(self.agent_tool_counts)
            )
            self.agent_metrics.max_tools_per_query = max(self.agent_tool_counts)
        
        # Update queue metrics
        if self.queue_wait_times:
            self.queue_metrics.avg_wait_time_ms = (
                sum(self.queue_wait_times) / len(self.queue_wait_times)
            )
    
    async def _self_monitoring(self):
        """Monitor the monitoring system itself"""
        while True:
            try:
                await asyncio.sleep(30)  # Check every 30 seconds
                
                # Update memory usage
                process = psutil.Process()
                self.monitoring_health.memory_usage_mb = process.memory_info().rss / 1024 / 1024
                
                # Update queue size
                self.monitoring_health.queue_size = self.event_queue.qsize()
                
                # Check for dropped events
                if self.monitoring_health.queue_size > 9000:  # Near capacity
                    self.monitoring_health.events_dropped += 1
                    logger.warning(f"Event queue near capacity: {self.monitoring_health.queue_size}")
                
            except Exception as e:
                logger.error(f"Error in self-monitoring: {e}")
                self.monitoring_health.last_error = str(e)
    
    def record_event(self, event: VoiceEvent):
        """Record a voice processing event (non-blocking)"""
        try:
            # Non-blocking queue put
            if self.event_queue.full():
                self.monitoring_health.events_dropped += 1
                logger.warning("Event queue full, dropping event")
                return
            
            # Put event in queue for async processing
            asyncio.create_task(self.event_queue.put(event))
            
        except Exception as e:
            logger.error(f"Error recording event: {e}")
            self.monitoring_health.last_error = str(e)
    
    def record_transcription_start(self, user_id: str, org_id: str) -> str:
        """Record start of transcription and return tracking ID"""
        tracking_id = f"trans_{int(time.time() * 1000)}"
        
        event = VoiceEvent(
            event_type='transcription_start',
            timestamp=datetime.now(),
            user_id=user_id,
            org_id=org_id,
            metadata={'tracking_id': tracking_id}
        )
        
        self.record_event(event)
        return tracking_id
    
    def record_transcription_complete(
        self, 
        tracking_id: str, 
        duration_ms: float, 
        success: bool = True,
        error_message: Optional[str] = None,
        transcript_length: Optional[int] = None
    ):
        """Record completion of transcription"""
        event = VoiceEvent(
            event_type='transcription_complete',
            timestamp=datetime.now(),
            duration_ms=duration_ms,
            success=success,
            error_message=error_message,
            metadata={
                'tracking_id': tracking_id,
                'transcript_length': transcript_length
            }
        )
        
        self.record_event(event)
    
    def record_validation_start(self, entry_id: str, user_id: str, org_id: str) -> str:
        """Record start of validation and return tracking ID"""
        tracking_id = f"val_{int(time.time() * 1000)}"
        
        event = VoiceEvent(
            event_type='validation_start',
            timestamp=datetime.now(),
            user_id=user_id,
            org_id=org_id,
            entry_id=entry_id,
            metadata={'tracking_id': tracking_id}
        )
        
        self.record_event(event)
        return tracking_id
    
    def record_validation_complete(
        self, 
        tracking_id: str, 
        entry_id: str,
        duration_ms: float, 
        success: bool = True,
        error_message: Optional[str] = None,
        validation_results: Optional[Dict] = None
    ):
        """Record completion of validation"""
        event = VoiceEvent(
            event_type='validation_complete',
            timestamp=datetime.now(),
            duration_ms=duration_ms,
            entry_id=entry_id,
            success=success,
            error_message=error_message,
            metadata={
                'tracking_id': tracking_id,
                'validation_results': validation_results
            }
        )
        
        self.record_event(event)
    
    def record_save_complete(
        self, 
        entry_id: str, 
        user_id: str, 
        org_id: str,
        duration_ms: float,
        success: bool = True,
        error_message: Optional[str] = None
    ):
        """Record completion of entry save"""
        event = VoiceEvent(
            event_type='save_complete',
            timestamp=datetime.now(),
            duration_ms=duration_ms,
            user_id=user_id,
            org_id=org_id,
            entry_id=entry_id,
            success=success,
            error_message=error_message
        )
        
        self.record_event(event)
    
    def record_ephy_lookup(
        self, 
        amm_code: str, 
        duration_ms: float,
        success: bool = True,
        error_message: Optional[str] = None
    ):
        """Record EPHY database lookup"""
        event = VoiceEvent(
            event_type='ephy_lookup',
            timestamp=datetime.now(),
            duration_ms=duration_ms,
            success=success,
            error_message=error_message,
            metadata={'amm_code': amm_code, 'tool_name': 'get_product_by_amm'}
        )
        
        self.record_event(event)
    
    def record_weather_lookup(
        self, 
        location: str, 
        date: str,
        duration_ms: float,
        success: bool = True,
        error_message: Optional[str] = None
    ):
        """Record weather service lookup"""
        event = VoiceEvent(
            event_type='weather_lookup',
            timestamp=datetime.now(),
            duration_ms=duration_ms,
            success=success,
            error_message=error_message,
            metadata={'location': location, 'date': date, 'tool_name': 'get_weather_conditions'}
        )
        
        self.record_event(event)
    
    def record_agent_reasoning(
        self,
        tools_used: int,
        duration_ms: float,
        success: bool = True,
        error_message: Optional[str] = None
    ):
        """Record agent reasoning session"""
        event = VoiceEvent(
            event_type='agent_reasoning',
            timestamp=datetime.now(),
            duration_ms=duration_ms,
            success=success,
            error_message=error_message,
            metadata={'tools_used': tools_used}
        )
        
        self.record_event(event)
        
        # Update agent metrics
        self.agent_metrics.total_queries += 1
        self.agent_tool_counts.append(tools_used)
        
        if success:
            self.agent_metrics.successful_reasoning += 1
        else:
            self.agent_metrics.failed_reasoning += 1
    
    def record_queue_metrics(
        self,
        queue_size: int,
        wait_time_ms: Optional[float] = None,
        processed: bool = False,
        failed: bool = False
    ):
        """Record validation queue metrics"""
        self.queue_metrics.current_size = queue_size
        self.queue_metrics.max_size = max(self.queue_metrics.max_size, queue_size)
        
        if wait_time_ms:
            self.queue_wait_times.append(wait_time_ms)
        
        if processed:
            self.queue_metrics.total_processed += 1
        
        if failed:
            self.queue_metrics.total_failed += 1
    
    def update_connection_count(self, count: int):
        """Update active WebSocket connection count"""
        self.active_connections = count
    
    def update_queue_size(self, size: int):
        """Update validation queue size"""
        self.processing_queue_size = size
        self.record_queue_metrics(size)
    
    def _update_performance_metrics(self, event: VoiceEvent):
        """Update performance metrics based on event"""
        self.performance_metrics.total_requests += 1
        
        if event.success:
            self.performance_metrics.successful_requests += 1
        else:
            self.performance_metrics.failed_requests += 1
            
            # Track specific error types
            if event.event_type == 'transcription_complete':
                self.performance_metrics.transcription_errors += 1
            elif event.event_type == 'validation_complete':
                self.performance_metrics.validation_errors += 1
            elif event.event_type == 'save_complete':
                self.performance_metrics.save_errors += 1
            elif event.event_type == 'ephy_lookup':
                self.performance_metrics.ephy_lookup_errors += 1
            elif event.event_type == 'weather_lookup':
                self.performance_metrics.weather_lookup_errors += 1
        
        # Add to rolling windows
        if event.duration_ms:
            if event.event_type == 'transcription_complete':
                self.recent_transcription_times.append(event.duration_ms)
            elif event.event_type == 'validation_complete':
                self.recent_validation_times.append(event.duration_ms)
            elif event.event_type == 'save_complete':
                self.recent_total_times.append(event.duration_ms)
    
    def _update_tool_metrics(self, tool_name: str, event: VoiceEvent):
        """Update metrics for a specific tool"""
        metrics = self.tool_metrics[tool_name]
        metrics.usage_count += 1
        metrics.last_used = event.timestamp
        
        if event.duration_ms:
            metrics.total_duration_ms += event.duration_ms
        
        if not event.success:
            metrics.error_count += 1
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return {
            'performance': asdict(self.performance_metrics),
            'tool_metrics': {name: asdict(metrics) for name, metrics in self.tool_metrics.items()},
            'agent_metrics': asdict(self.agent_metrics),
            'queue_metrics': asdict(self.queue_metrics),
            'monitoring_health': asdict(self.monitoring_health),
            'active_connections': self.active_connections,
            'processing_queue_size': self.processing_queue_size,
            'last_activity': self.last_activity.isoformat(),
            'uptime_hours': self.get_uptime_hours(),
            'total_events': len(self.events),
            'error_counts': dict(self.error_counts),
            'recent_errors_count': len(self.recent_errors)
        }
    
    def get_uptime_hours(self) -> float:
        """Get system uptime in hours"""
        return (datetime.now() - self.start_time).total_seconds() / 3600
    
    def get_user_metrics(self, user_id: str, hours: int = 24) -> Dict[str, Any]:
        """Get metrics for a specific user"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        if user_id not in self.user_events:
            return {'user_id': user_id, 'events': 0, 'success_rate': 0}
        
        user_events = [e for e in self.user_events[user_id] if e.timestamp >= cutoff_time]
        
        if not user_events:
            return {'user_id': user_id, 'events': 0, 'success_rate': 0}
        
        successful = sum(1 for e in user_events if e.success)
        total = len(user_events)
        
        return {
            'user_id': user_id,
            'events': total,
            'successful_events': successful,
            'success_rate': successful / total if total > 0 else 0,
            'recent_events': [
                {
                    'timestamp': e.timestamp.isoformat(),
                    'type': e.event_type,
                    'success': e.success,
                    'duration_ms': e.duration_ms
                }
                for e in user_events[-10:]  # Last 10 events
            ]
        }
    
    def get_org_metrics(self, org_id: str, hours: int = 24) -> Dict[str, Any]:
        """Get metrics for a specific organization"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        if org_id not in self.org_events:
            return {'org_id': org_id, 'events': 0, 'users': 0}
        
        org_events = [e for e in self.org_events[org_id] if e.timestamp >= cutoff_time]
        
        if not org_events:
            return {'org_id': org_id, 'events': 0, 'users': 0}
        
        unique_users = set(e.user_id for e in org_events if e.user_id)
        successful = sum(1 for e in org_events if e.success)
        total = len(org_events)
        
        return {
            'org_id': org_id,
            'events': total,
            'successful_events': successful,
            'success_rate': successful / total if total > 0 else 0,
            'unique_users': len(unique_users),
            'users': list(unique_users)
        }
    
    def get_recent_errors(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent errors"""
        return list(self.recent_errors)[-limit:]
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get overall system health status"""
        now = datetime.now()
        time_since_activity = (now - self.last_activity).total_seconds()
        
        # Calculate health score (0-100)
        health_score = 100
        
        # Deduct points for errors
        if self.performance_metrics.failed_requests > 0:
            error_rate = self.performance_metrics.failed_requests / self.performance_metrics.total_requests
            health_score -= min(50, error_rate * 100)
        
        # Deduct points for high processing times
        if self.performance_metrics.average_total_time_ms > 10000:  # 10 seconds
            health_score -= 20
        
        # Deduct points for no recent activity (if expected)
        if time_since_activity > 3600:  # 1 hour
            health_score -= 10
        
        # Deduct points for monitoring issues
        if self.monitoring_health.events_dropped > 0:
            health_score -= 15
        
        if self.monitoring_health.memory_usage_mb > 500:  # 500MB
            health_score -= 10
        
        # Determine status
        if health_score >= 90:
            status = 'healthy'
        elif health_score >= 70:
            status = 'warning'
        else:
            status = 'critical'
        
        return {
            'status': status,
            'health_score': max(0, health_score),
            'last_activity_seconds_ago': time_since_activity,
            'active_connections': self.active_connections,
            'processing_queue_size': self.processing_queue_size,
            'total_requests': self.performance_metrics.total_requests,
            'error_rate': (
                self.performance_metrics.failed_requests / self.performance_metrics.total_requests
                if self.performance_metrics.total_requests > 0 else 0
            ),
            'monitoring_health': asdict(self.monitoring_health)
        }
    
    def export_metrics(self, format: str = 'json') -> str:
        """Export metrics in specified format"""
        data = {
            'timestamp': datetime.now().isoformat(),
            'performance': asdict(self.performance_metrics),
            'tool_metrics': {name: asdict(metrics) for name, metrics in self.tool_metrics.items()},
            'agent_metrics': asdict(self.agent_metrics),
            'queue_metrics': asdict(self.queue_metrics),
            'monitoring_health': asdict(self.monitoring_health),
            'health': self.get_health_status(),
            'recent_errors': self.get_recent_errors(50),
            'error_counts': dict(self.error_counts),
            'uptime_hours': self.get_uptime_hours()
        }
        
        if format == 'json':
            return json.dumps(data, indent=2)
        elif format == 'prometheus':
            return self._export_prometheus()
        else:
            return str(data)
    
    def _export_prometheus(self) -> str:
        """Export metrics in Prometheus format"""
        metrics = self.performance_metrics
        health = self.get_health_status()
        
        return f"""# HELP voice_requests_total Total voice requests
# TYPE voice_requests_total counter
voice_requests_total {metrics.total_requests}

# HELP voice_requests_failed Failed voice requests
# TYPE voice_requests_failed counter
voice_requests_failed {metrics.failed_requests}

# HELP voice_transcription_duration_ms Average transcription duration
# TYPE voice_transcription_duration_ms gauge
voice_transcription_duration_ms {metrics.average_transcription_time_ms}

# HELP voice_validation_duration_ms Average validation duration
# TYPE voice_validation_duration_ms gauge
voice_validation_duration_ms {metrics.average_validation_time_ms}

# HELP voice_total_duration_ms Average total processing duration
# TYPE voice_total_duration_ms gauge
voice_total_duration_ms {metrics.average_total_time_ms}

# HELP voice_active_connections Current active connections
# TYPE voice_active_connections gauge
voice_active_connections {self.active_connections}

# HELP voice_queue_size Current processing queue size
# TYPE voice_queue_size gauge
voice_queue_size {self.processing_queue_size}

# HELP voice_health_score System health score (0-100)
# TYPE voice_health_score gauge
voice_health_score {health['health_score']}

# HELP voice_uptime_hours System uptime in hours
# TYPE voice_uptime_hours gauge
voice_uptime_hours {self.get_uptime_hours()}

# HELP voice_memory_usage_mb Memory usage in MB
# TYPE voice_memory_usage_mb gauge
voice_memory_usage_mb {self.monitoring_health.memory_usage_mb}

# HELP voice_events_processed_total Total events processed
# TYPE voice_events_processed_total counter
voice_events_processed_total {self.monitoring_health.events_processed}

# HELP voice_events_dropped_total Total events dropped
# TYPE voice_events_dropped_total counter
voice_events_dropped_total {self.monitoring_health.events_dropped}
"""


# Global improved monitoring instance
improved_voice_monitor = ImprovedVoiceMonitoringService()


# Decorator for monitoring function execution
def monitor_voice_function(func_name: str):
    """Decorator to monitor voice processing functions"""
    def decorator(func):
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            error_message = None
            
            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                error_message = str(e)
                raise
            finally:
                duration_ms = (time.time() - start_time) * 1000
                
                event = VoiceEvent(
                    event_type=f'{func_name}_complete',
                    timestamp=datetime.now(),
                    duration_ms=duration_ms,
                    success=success,
                    error_message=error_message,
                    metadata={'tool_name': func_name}
                )
                
                improved_voice_monitor.record_event(event)
        
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            success = True
            error_message = None
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                error_message = str(e)
                raise
            finally:
                duration_ms = (time.time() - start_time) * 1000
                
                event = VoiceEvent(
                    event_type=f'{func_name}_complete',
                    timestamp=datetime.now(),
                    duration_ms=duration_ms,
                    success=success,
                    error_message=error_message,
                    metadata={'tool_name': func_name}
                )
                
                improved_voice_monitor.record_event(event)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
