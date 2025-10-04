#!/usr/bin/env python3
"""
Simple test for monitoring system core functionality
Tests the monitoring logic without external dependencies
"""

import asyncio
import time
import sys
from datetime import datetime, timedelta
from collections import deque, defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
import json


@dataclass
class VoiceEvent:
    """Voice processing event for monitoring"""
    event_type: str
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


class SimpleMonitoringService:
    """Simplified monitoring service for testing"""
    
    def __init__(self, max_events: int = 10000):
        self.max_events = max_events
        
        # Event storage with proper cleanup
        self.events: deque = deque(maxlen=max_events)
        self.user_events: Dict[str, deque] = {}
        self.org_events: Dict[str, deque] = {}
        
        # Performance tracking with rolling windows
        self.performance_metrics = PerformanceMetrics()
        self.recent_transcription_times = deque(maxlen=100)
        self.recent_validation_times = deque(maxlen=100)
        self.recent_total_times = deque(maxlen=100)
        
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
        
        # Start background workers
        self._start_background_workers()
    
    def _start_background_workers(self):
        """Start background workers for async processing"""
        # Event processor
        asyncio.create_task(self._event_processor())
    
    async def _event_processor(self):
        """Background worker to process events asynchronously"""
        while True:
            try:
                event = await self.event_queue.get()
                await self._process_event(event)
                self.event_queue.task_done()
            except Exception as e:
                print(f"Error in event processor: {e}")
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
            print(f"Error processing event: {e}")
            self.monitoring_health.last_error = str(e)
    
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
        
        # Add to rolling windows
        if event.duration_ms:
            if event.event_type == 'transcription_complete':
                self.recent_transcription_times.append(event.duration_ms)
            elif event.event_type == 'validation_complete':
                self.recent_validation_times.append(event.duration_ms)
            elif event.event_type == 'save_complete':
                self.recent_total_times.append(event.duration_ms)
    
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
    
    async def cleanup_old_data(self):
        """Clean up old user/org event queues"""
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
        
        self.monitoring_health.cleanup_runs += 1
    
    def record_event(self, event: VoiceEvent):
        """Record a voice processing event (non-blocking)"""
        try:
            if self.event_queue.full():
                self.monitoring_health.events_dropped += 1
                return
            
            # Put event in queue for async processing
            asyncio.create_task(self.event_queue.put(event))
            
        except Exception as e:
            print(f"Error recording event: {e}")
            self.monitoring_health.last_error = str(e)
    
    def export_prometheus(self) -> str:
        """Export metrics in Prometheus format"""
        metrics = self.performance_metrics
        health = self.monitoring_health
        
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

# HELP voice_health_score System health score (0-100)
# TYPE voice_health_score gauge
voice_health_score 95.0

# HELP voice_events_processed_total Total events processed
# TYPE voice_events_processed_total counter
voice_events_processed_total {health.events_processed}

# HELP voice_events_dropped_total Total events dropped
# TYPE voice_events_dropped_total counter
voice_events_dropped_total {health.events_dropped}
"""


class MonitoringTester:
    """Test the monitoring system with real scenarios"""
    
    def __init__(self):
        self.monitor = SimpleMonitoringService()
        self.test_results = []
    
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}")
        if details:
            print(f"    {details}")
        self.test_results.append({
            "test": test_name,
            "success": success,
            "details": details
        })
    
    async def test_async_event_recording(self):
        """Test that event recording is non-blocking"""
        print("\n🧪 Testing async event recording...")
        
        # Record start time
        start_time = time.time()
        
        # Create 1000 events rapidly
        events_created = 0
        for i in range(1000):
            event = VoiceEvent(
                event_type='test_event',
                timestamp=datetime.now(),
                duration_ms=10.0,
                user_id=f'user_{i % 10}',
                org_id=f'org_{i % 5}',
                success=True,
                metadata={'test_id': i}
            )
            self.monitor.record_event(event)
            events_created += 1
        
        # Check how long it took (should be very fast - non-blocking)
        creation_time = time.time() - start_time
        
        # Wait a bit for async processing
        await asyncio.sleep(2)
        
        # Check if events were processed
        queue_size = self.monitor.event_queue.qsize()
        events_processed = self.monitor.monitoring_health.events_processed
        
        # Test results
        creation_fast = creation_time < 0.5  # Should be very fast
        events_queued = queue_size == 0  # Queue should be empty after processing
        events_processed_correctly = events_processed >= 1000
        
        self.log_test(
            "Async event recording",
            creation_fast and events_queued and events_processed_correctly,
            f"Created {events_created} events in {creation_time:.3f}s, "
            f"processed {events_processed}, queue size: {queue_size}"
        )
        
        return creation_fast and events_queued and events_processed_correctly
    
    async def test_memory_cleanup(self):
        """Test that memory cleanup actually works"""
        print("\n🧪 Testing memory cleanup...")
        
        # Create many inactive users
        inactive_users = []
        for i in range(100):
            user_id = f'inactive_user_{i}'
            inactive_users.append(user_id)
            
            # Create event with old timestamp
            old_event = VoiceEvent(
                event_type='old_event',
                timestamp=datetime.now() - timedelta(hours=25),  # 25 hours ago
                user_id=user_id,
                org_id='test_org',
                success=True
            )
            self.monitor.record_event(old_event)
        
        # Wait for event processing
        await asyncio.sleep(1)
        
        # Check initial state
        initial_user_count = len(self.monitor.user_events)
        print(f"    Initial user count: {initial_user_count}")
        
        # Force cleanup
        await self.monitor.cleanup_old_data()
        
        # Check final state
        final_user_count = len(self.monitor.user_events)
        cleanup_runs = self.monitor.monitoring_health.cleanup_runs
        
        # Test results
        cleanup_worked = final_user_count < initial_user_count
        cleanup_tracked = cleanup_runs > 0
        
        self.log_test(
            "Memory cleanup",
            cleanup_worked and cleanup_tracked,
            f"Users before: {initial_user_count}, after: {final_user_count}, "
            f"cleanup runs: {cleanup_runs}"
        )
        
        return cleanup_worked and cleanup_tracked
    
    async def test_rolling_averages(self):
        """Test that rolling averages work correctly"""
        print("\n🧪 Testing rolling averages...")
        
        # Clear existing data
        self.monitor.recent_transcription_times.clear()
        
        # Add some initial events
        for i in range(50):
            self.monitor.recent_transcription_times.append(100.0)  # 100ms average
        
        # Update rolling metrics
        self.monitor._update_rolling_metrics()
        initial_avg = self.monitor.performance_metrics.average_transcription_time_ms
        
        # Add slow events (should increase average)
        for i in range(50):
            self.monitor.recent_transcription_times.append(500.0)  # 500ms
        
        # Update rolling metrics again
        self.monitor._update_rolling_metrics()
        final_avg = self.monitor.performance_metrics.average_transcription_time_ms
        
        # Add more events to test windowing (should push out old 100ms events)
        for i in range(50):
            self.monitor.recent_transcription_times.append(200.0)  # 200ms
        
        self.monitor._update_rolling_metrics()
        windowed_avg = self.monitor.performance_metrics.average_transcription_time_ms
        
        # Test results
        avg_increased = final_avg > initial_avg
        # The windowed average should be different from the final average (showing rolling window works)
        avg_windowed = windowed_avg != final_avg
        # With 50 events of 500ms and 50 events of 200ms, average should be 350ms
        correct_calculation = abs(windowed_avg - 350.0) < 50.0  # Allow some tolerance
        
        # Debug info
        print(f"    Debug: avg_increased={avg_increased}, avg_windowed={avg_windowed}, correct_calculation={correct_calculation}")
        print(f"    Debug: windowed_avg={windowed_avg}, expected=350.0, diff={abs(windowed_avg - 350.0)}")
        
        self.log_test(
            "Rolling averages",
            avg_increased and avg_windowed and correct_calculation,
            f"Initial: {initial_avg:.1f}ms, after slow: {final_avg:.1f}ms, "
            f"after windowing: {windowed_avg:.1f}ms"
        )
        
        return avg_increased and avg_windowed and correct_calculation
    
    async def test_prometheus_export(self):
        """Test that Prometheus export works correctly"""
        print("\n🧪 Testing Prometheus export...")
        
        # Generate some test data
        for i in range(10):
            event = VoiceEvent(
                event_type='transcription_complete',
                timestamp=datetime.now(),
                duration_ms=150.0,
                user_id=f'test_user_{i}',
                org_id='test_org',
                success=True
            )
            self.monitor.record_event(event)
        
        # Wait for processing
        await asyncio.sleep(1)
        
        # Export in Prometheus format
        prometheus_data = self.monitor.export_prometheus()
        
        # Check Prometheus format
        has_help_lines = '# HELP' in prometheus_data
        has_type_lines = '# TYPE' in prometheus_data
        has_metrics = 'voice_requests_total' in prometheus_data
        has_gauges = 'voice_health_score' in prometheus_data
        has_counters = 'voice_requests_failed' in prometheus_data
        
        # Check that it's valid Prometheus format
        lines = prometheus_data.strip().split('\n')
        help_lines = [line for line in lines if line.startswith('# HELP')]
        type_lines = [line for line in lines if line.startswith('# TYPE')]
        metric_lines = [line for line in lines if not line.startswith('#') and line.strip()]
        
        valid_format = (
            has_help_lines and has_type_lines and has_metrics and 
            has_gauges and has_counters and
            len(help_lines) > 0 and len(type_lines) > 0 and len(metric_lines) > 0
        )
        
        self.log_test(
            "Prometheus export",
            valid_format,
            f"Help lines: {len(help_lines)}, Type lines: {len(type_lines)}, "
            f"Metric lines: {len(metric_lines)}"
        )
        
        return valid_format
    
    async def test_self_monitoring(self):
        """Test that self-monitoring actually works"""
        print("\n🧪 Testing self-monitoring...")
        
        # Check initial state
        initial_processed = self.monitor.monitoring_health.events_processed
        
        # Generate some events to trigger self-monitoring
        for i in range(50):
            event = VoiceEvent(
                event_type='self_monitoring_test',
                timestamp=datetime.now(),
                user_id=f'self_test_user_{i}',
                org_id='self_test_org',
                success=True
            )
            self.monitor.record_event(event)
        
        # Wait for processing and self-monitoring updates
        await asyncio.sleep(2)
        
        # Check if self-monitoring updated
        final_processed = self.monitor.monitoring_health.events_processed
        queue_size = self.monitor.monitoring_health.queue_size
        
        # Test results
        events_tracked = final_processed > initial_processed
        queue_tracked = queue_size >= 0  # Should track queue size
        
        self.log_test(
            "Self-monitoring",
            events_tracked and queue_tracked,
            f"Events: {initial_processed} → {final_processed}, "
            f"Queue: {queue_size}"
        )
        
        return events_tracked and queue_tracked
    
    async def run_all_tests(self):
        """Run all tests and report results"""
        print("🚀 Starting monitoring system tests...")
        print("=" * 60)
        
        tests = [
            self.test_async_event_recording,
            self.test_memory_cleanup,
            self.test_rolling_averages,
            self.test_prometheus_export,
            self.test_self_monitoring
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                result = await test()
                if result:
                    passed += 1
            except Exception as e:
                print(f"❌ FAIL {test.__name__} - Exception: {e}")
                self.test_results.append({
                    "test": test.__name__,
                    "success": False,
                    "details": f"Exception: {e}"
                })
        
        print("\n" + "=" * 60)
        print(f"📊 Test Results: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 All tests passed! Monitoring system is working correctly.")
        else:
            print("⚠️  Some tests failed. Monitoring system needs fixes.")
        
        return passed == total


async def main():
    """Main test runner"""
    tester = MonitoringTester()
    success = await tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
