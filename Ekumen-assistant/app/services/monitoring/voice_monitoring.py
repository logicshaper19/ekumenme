"""
Voice Journal Monitoring and Observability
Tracks performance, errors, and usage metrics for the voice journal system
"""

from typing import Dict, List, Optional, Any
import logging
import time
import asyncio
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import json

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


class VoiceMonitoringService:
    """Service for monitoring voice journal system performance and health"""
    
    def __init__(self, max_events: int = 10000, metrics_window_minutes: int = 60):
        self.max_events = max_events
        self.metrics_window_minutes = metrics_window_minutes
        
        # Event storage
        self.events: deque = deque(maxlen=max_events)
        self.user_events: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self.org_events: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        
        # Performance tracking
        self.performance_metrics = PerformanceMetrics()
        self.daily_metrics: Dict[str, PerformanceMetrics] = {}
        
        # Error tracking
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.recent_errors: deque = deque(maxlen=100)
        
        # Real-time metrics
        self.active_connections = 0
        self.processing_queue_size = 0
        self.last_activity = datetime.now()
        
        logger.info("Voice monitoring service initialized")
    
    def record_event(self, event: VoiceEvent):
        """Record a voice processing event"""
        try:
            # Add to main event queue
            self.events.append(event)
            
            # Add to user-specific queue
            if event.user_id:
                self.user_events[event.user_id].append(event)
            
            # Add to org-specific queue
            if event.org_id:
                self.org_events[event.org_id].append(event)
            
            # Update performance metrics
            self._update_performance_metrics(event)
            
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
            
        except Exception as e:
            logger.error(f"Error recording voice event: {e}")
    
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
            metadata={'amm_code': amm_code}
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
            metadata={'location': location, 'date': date}
        )
        
        self.record_event(event)
    
    def update_connection_count(self, count: int):
        """Update active WebSocket connection count"""
        self.active_connections = count
    
    def update_queue_size(self, size: int):
        """Update validation queue size"""
        self.processing_queue_size = size
    
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
        
        # Update average times
        if event.duration_ms:
            if event.event_type == 'transcription_complete':
                self._update_average_time('transcription', event.duration_ms)
            elif event.event_type == 'validation_complete':
                self._update_average_time('validation', event.duration_ms)
            elif event.event_type == 'save_complete':
                self._update_average_time('total', event.duration_ms)
    
    def _update_average_time(self, metric_type: str, duration_ms: float):
        """Update rolling average for time metrics"""
        if metric_type == 'transcription':
            current_avg = self.performance_metrics.average_transcription_time_ms
            count = self.performance_metrics.total_requests
            self.performance_metrics.average_transcription_time_ms = (
                (current_avg * (count - 1) + duration_ms) / count
            )
        elif metric_type == 'validation':
            current_avg = self.performance_metrics.average_validation_time_ms
            count = self.performance_metrics.total_requests
            self.performance_metrics.average_validation_time_ms = (
                (current_avg * (count - 1) + duration_ms) / count
            )
        elif metric_type == 'total':
            current_avg = self.performance_metrics.average_total_time_ms
            count = self.performance_metrics.total_requests
            self.performance_metrics.average_total_time_ms = (
                (current_avg * (count - 1) + duration_ms) / count
            )
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return {
            'performance': asdict(self.performance_metrics),
            'active_connections': self.active_connections,
            'processing_queue_size': self.processing_queue_size,
            'last_activity': self.last_activity.isoformat(),
            'total_events': len(self.events),
            'error_counts': dict(self.error_counts),
            'recent_errors_count': len(self.recent_errors)
        }
    
    def get_user_metrics(self, user_id: str, hours: int = 24) -> Dict[str, Any]:
        """Get metrics for a specific user"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
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
            )
        }
    
    def export_metrics(self, format: str = 'json') -> str:
        """Export metrics in specified format"""
        data = {
            'timestamp': datetime.now().isoformat(),
            'performance': asdict(self.performance_metrics),
            'health': self.get_health_status(),
            'recent_errors': self.get_recent_errors(50),
            'error_counts': dict(self.error_counts)
        }
        
        if format == 'json':
            return json.dumps(data, indent=2)
        else:
            # Could add other formats like CSV, Prometheus, etc.
            return str(data)


# Global monitoring instance
voice_monitor = VoiceMonitoringService()


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
                    error_message=error_message
                )
                
                voice_monitor.record_event(event)
        
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
                    error_message=error_message
                )
                
                voice_monitor.record_event(event)
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator
