#!/usr/bin/env python3
"""
Test script for the improved monitoring system
Actually tests the functionality instead of just claiming it works
"""

import asyncio
import time
import sys
import os
from datetime import datetime, timedelta
from typing import List, Dict, Any

# Add the app directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.services.monitoring.improved_voice_monitoring import (
    ImprovedVoiceMonitoringService, 
    VoiceEvent
)


class MonitoringTester:
    """Test the monitoring system with real scenarios"""
    
    def __init__(self):
        self.monitor = ImprovedVoiceMonitoringService()
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
        await self.monitor._cleanup_old_data()
        
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
        avg_windowed = windowed_avg < final_avg  # Should decrease as old slow events are pushed out
        correct_calculation = abs(windowed_avg - 300.0) < 10.0  # Should be around 300ms (mix of 500ms and 200ms)
        
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
        prometheus_data = self.monitor.export_metrics('prometheus')
        
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
        initial_memory = self.monitor.monitoring_health.memory_usage_mb
        
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
        await asyncio.sleep(3)
        
        # Check if self-monitoring updated
        final_processed = self.monitor.monitoring_health.events_processed
        final_memory = self.monitor.monitoring_health.memory_usage_mb
        queue_size = self.monitor.monitoring_health.queue_size
        
        # Test results
        events_tracked = final_processed > initial_processed
        memory_tracked = final_memory > 0  # Should have some memory usage
        queue_tracked = queue_size >= 0  # Should track queue size
        
        self.log_test(
            "Self-monitoring",
            events_tracked and memory_tracked and queue_tracked,
            f"Events: {initial_processed} → {final_processed}, "
            f"Memory: {initial_memory:.1f}MB → {final_memory:.1f}MB, "
            f"Queue: {queue_size}"
        )
        
        return events_tracked and memory_tracked and queue_tracked
    
    async def test_tool_metrics(self):
        """Test that tool-specific metrics work"""
        print("\n🧪 Testing tool metrics...")
        
        # Record some tool usage
        tool_names = ['get_product_by_amm', 'check_wind_speed', 'validate_dose']
        
        for tool_name in tool_names:
            for i in range(10):
                event = VoiceEvent(
                    event_type='tool_usage',
                    timestamp=datetime.now(),
                    duration_ms=50.0 + i * 10,  # Varying durations
                    success=i % 3 != 0,  # Some failures
                    metadata={'tool_name': tool_name}
                )
                self.monitor.record_event(event)
        
        # Wait for processing
        await asyncio.sleep(1)
        
        # Check tool metrics
        tool_metrics = self.monitor.tool_metrics
        all_tools_tracked = all(tool_name in tool_metrics for tool_name in tool_names)
        
        # Check specific metrics
        amm_tool = tool_metrics.get('get_product_by_amm')
        amm_usage_correct = amm_tool.usage_count == 10
        amm_errors_correct = amm_tool.error_count > 0  # Should have some errors
        
        self.log_test(
            "Tool metrics",
            all_tools_tracked and amm_usage_correct and amm_errors_correct,
            f"Tools tracked: {len(tool_metrics)}, "
            f"AMM tool usage: {amm_tool.usage_count}, errors: {amm_tool.error_count}"
        )
        
        return all_tools_tracked and amm_usage_correct and amm_errors_correct
    
    async def test_queue_metrics(self):
        """Test that queue metrics work"""
        print("\n🧪 Testing queue metrics...")
        
        # Record queue metrics
        self.monitor.record_queue_metrics(queue_size=50, wait_time_ms=100.0)
        self.monitor.record_queue_metrics(queue_size=30, wait_time_ms=200.0)
        self.monitor.record_queue_metrics(queue_size=10, processed=True)
        self.monitor.record_queue_metrics(queue_size=5, failed=True)
        
        # Check queue metrics
        queue_metrics = self.monitor.queue_metrics
        max_size_correct = queue_metrics.max_size == 50
        processed_correct = queue_metrics.total_processed == 1
        failed_correct = queue_metrics.total_failed == 1
        wait_times_tracked = len(self.monitor.queue_wait_times) == 2
        
        self.log_test(
            "Queue metrics",
            max_size_correct and processed_correct and failed_correct and wait_times_tracked,
            f"Max size: {queue_metrics.max_size}, processed: {queue_metrics.total_processed}, "
            f"failed: {queue_metrics.total_failed}, wait times: {len(self.monitor.queue_wait_times)}"
        )
        
        return max_size_correct and processed_correct and failed_correct and wait_times_tracked
    
    async def run_all_tests(self):
        """Run all tests and report results"""
        print("🚀 Starting monitoring system tests...")
        print("=" * 60)
        
        tests = [
            self.test_async_event_recording,
            self.test_memory_cleanup,
            self.test_rolling_averages,
            self.test_prometheus_export,
            self.test_self_monitoring,
            self.test_tool_metrics,
            self.test_queue_metrics
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
