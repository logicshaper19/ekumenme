"""
Improved Monitoring API endpoints for voice journal system
Fixed version with proper role-based access and comprehensive metrics
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime, timedelta

from app.services.monitoring.improved_voice_monitoring import improved_voice_monitor
from app.services.shared.auth_service import AuthService

logger = logging.getLogger(__name__)

router = APIRouter()
auth_service = AuthService()


def check_admin_access(current_user: dict):
    """Check if user has admin access"""
    if not current_user.get("is_admin", False):
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user


def check_org_access(current_user: dict, org_id: str):
    """Check if user has access to organization data"""
    user_org_id = current_user.get("org_id")
    is_admin = current_user.get("is_admin", False)
    
    if not is_admin and user_org_id != org_id:
        raise HTTPException(status_code=403, detail="Access denied to organization data")
    return current_user


def check_user_access(current_user: dict, user_id: str):
    """Check if user has access to user data"""
    current_user_id = current_user.get("user_id")
    is_admin = current_user.get("is_admin", False)
    
    if not is_admin and current_user_id != user_id:
        raise HTTPException(status_code=403, detail="Access denied to user data")
    return current_user


@router.get("/health")
async def health_check():
    """Basic health check endpoint"""
    try:
        health_status = improved_voice_monitor.get_health_status()
        return {
            "status": "ok",
            "timestamp": datetime.now().isoformat(),
            "voice_system": health_status
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail="Health check failed")


@router.get("/metrics")
async def get_metrics(
    current_user: dict = Depends(check_admin_access)
):
    """Get comprehensive voice system metrics (admin only)"""
    try:
        metrics = improved_voice_monitor.get_performance_metrics()
        return {
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve metrics")


@router.get("/user-metrics/{user_id}")
async def get_user_metrics(
    user_id: str,
    hours: int = Query(24, ge=1, le=168),  # 1 hour to 1 week
    current_user: dict = Depends(lambda u: check_user_access(u, user_id))
):
    """Get metrics for a specific user"""
    try:
        user_metrics = improved_voice_monitor.get_user_metrics(user_id, hours)
        return {
            "timestamp": datetime.now().isoformat(),
            "user_metrics": user_metrics
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting user metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve user metrics")


@router.get("/org-metrics/{org_id}")
async def get_org_metrics(
    org_id: str,
    hours: int = Query(24, ge=1, le=168),  # 1 hour to 1 week
    current_user: dict = Depends(lambda u: check_org_access(u, org_id))
):
    """Get metrics for a specific organization"""
    try:
        org_metrics = improved_voice_monitor.get_org_metrics(org_id, hours)
        return {
            "timestamp": datetime.now().isoformat(),
            "org_metrics": org_metrics
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting org metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve org metrics")


@router.get("/tool-metrics")
async def get_tool_metrics(
    current_user: dict = Depends(check_admin_access)
):
    """Get metrics for individual tools (admin only)"""
    try:
        metrics = improved_voice_monitor.get_performance_metrics()
        tool_metrics = metrics.get('tool_metrics', {})
        
        # Calculate additional metrics
        tool_analysis = {}
        for tool_name, tool_data in tool_metrics.items():
            usage_count = tool_data.get('usage_count', 0)
            total_duration = tool_data.get('total_duration_ms', 0)
            error_count = tool_data.get('error_count', 0)
            
            avg_duration = total_duration / usage_count if usage_count > 0 else 0
            error_rate = error_count / usage_count if usage_count > 0 else 0
            
            tool_analysis[tool_name] = {
                **tool_data,
                'avg_duration_ms': round(avg_duration, 2),
                'error_rate': round(error_rate, 4),
                'last_used': tool_data.get('last_used')
            }
        
        return {
            "timestamp": datetime.now().isoformat(),
            "tool_metrics": tool_analysis
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting tool metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve tool metrics")


@router.get("/agent-metrics")
async def get_agent_metrics(
    current_user: dict = Depends(check_admin_access)
):
    """Get agent reasoning metrics (admin only)"""
    try:
        metrics = improved_voice_monitor.get_performance_metrics()
        agent_metrics = metrics.get('agent_metrics', {})
        
        return {
            "timestamp": datetime.now().isoformat(),
            "agent_metrics": agent_metrics
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting agent metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve agent metrics")


@router.get("/queue-metrics")
async def get_queue_metrics(
    current_user: dict = Depends(check_admin_access)
):
    """Get validation queue metrics (admin only)"""
    try:
        metrics = improved_voice_monitor.get_performance_metrics()
        queue_metrics = metrics.get('queue_metrics', {})
        
        return {
            "timestamp": datetime.now().isoformat(),
            "queue_metrics": queue_metrics
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting queue metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve queue metrics")


@router.get("/errors")
async def get_recent_errors(
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(check_admin_access)
):
    """Get recent errors from the voice system (admin only)"""
    try:
        recent_errors = improved_voice_monitor.get_recent_errors(limit)
        return {
            "timestamp": datetime.now().isoformat(),
            "recent_errors": recent_errors,
            "count": len(recent_errors)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting recent errors: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve recent errors")


@router.get("/export")
async def export_metrics(
    format: str = Query("json", regex="^(json|prometheus)$"),
    current_user: dict = Depends(check_admin_access)
):
    """Export metrics in various formats (admin only)"""
    try:
        exported_data = improved_voice_monitor.export_metrics(format)
        
        if format == "json":
            return {
                "timestamp": datetime.now().isoformat(),
                "format": format,
                "data": exported_data
            }
        else:
            # For Prometheus format, return as plain text
            from fastapi.responses import PlainTextResponse
            return PlainTextResponse(
                content=exported_data,
                media_type="text/plain"
            )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to export metrics")


@router.get("/status")
async def get_system_status():
    """Get current system status (public endpoint)"""
    try:
        health_status = improved_voice_monitor.get_health_status()
        
        # Return simplified status for public consumption
        return {
            "status": health_status["status"],
            "health_score": health_status["health_score"],
            "active_connections": health_status["active_connections"],
            "last_activity_seconds_ago": health_status["last_activity_seconds_ago"],
            "uptime_hours": improved_voice_monitor.get_uptime_hours(),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve system status")


@router.get("/monitoring-health")
async def get_monitoring_health(
    current_user: dict = Depends(check_admin_access)
):
    """Get monitoring system health (admin only)"""
    try:
        metrics = improved_voice_monitor.get_performance_metrics()
        monitoring_health = metrics.get('monitoring_health', {})
        
        return {
            "timestamp": datetime.now().isoformat(),
            "monitoring_health": monitoring_health
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting monitoring health: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve monitoring health")


@router.post("/test")
async def test_monitoring(
    current_user: dict = Depends(check_admin_access)
):
    """Test monitoring system by generating sample events (admin only)"""
    try:
        # Generate test events
        from app.services.monitoring.improved_voice_monitoring import VoiceEvent
        
        test_events = [
            VoiceEvent(
                event_type='transcription_complete',
                timestamp=datetime.now(),
                duration_ms=1500.0,
                user_id=current_user.get("user_id"),
                org_id=current_user.get("org_id"),
                success=True,
                metadata={'tool_name': 'test_transcription'}
            ),
            VoiceEvent(
                event_type='validation_complete',
                timestamp=datetime.now(),
                duration_ms=3000.0,
                user_id=current_user.get("user_id"),
                org_id=current_user.get("org_id"),
                entry_id="test_entry_123",
                success=True,
                metadata={'tool_name': 'test_validation'}
            ),
            VoiceEvent(
                event_type='save_complete',
                timestamp=datetime.now(),
                duration_ms=500.0,
                user_id=current_user.get("user_id"),
                org_id=current_user.get("org_id"),
                entry_id="test_entry_123",
                success=True,
                metadata={'tool_name': 'test_save'}
            )
        ]
        
        for event in test_events:
            improved_voice_monitor.record_event(event)
        
        return {
            "message": "Test events generated successfully",
            "events_count": len(test_events),
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating test events: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate test events")


@router.get("/dashboard")
async def get_dashboard_data(
    current_user: dict = Depends(check_admin_access)
):
    """Get dashboard data for monitoring UI (admin only)"""
    try:
        # Get comprehensive dashboard data
        health_status = improved_voice_monitor.get_health_status()
        performance_metrics = improved_voice_monitor.get_performance_metrics()
        recent_errors = improved_voice_monitor.get_recent_errors(10)
        
        # Calculate additional metrics
        uptime_hours = improved_voice_monitor.get_uptime_hours()
        success_rate = (
            performance_metrics["performance"]["successful_requests"] / 
            performance_metrics["performance"]["total_requests"] * 100
            if performance_metrics["performance"]["total_requests"] > 0 else 100
        )
        
        # Tool usage analysis
        tool_metrics = performance_metrics.get("tool_metrics", {})
        most_used_tools = sorted(
            tool_metrics.items(),
            key=lambda x: x[1].get("usage_count", 0),
            reverse=True
        )[:5]
        
        # Agent performance
        agent_metrics = performance_metrics.get("agent_metrics", {})
        avg_tools_per_query = agent_metrics.get("avg_tools_per_query", 0)
        
        dashboard_data = {
            "timestamp": datetime.now().isoformat(),
            "overview": {
                "status": health_status["status"],
                "health_score": health_status["health_score"],
                "uptime_hours": round(uptime_hours, 2),
                "success_rate": round(success_rate, 2)
            },
            "performance": {
                "total_requests": performance_metrics["performance"]["total_requests"],
                "active_connections": performance_metrics["active_connections"],
                "queue_size": performance_metrics["processing_queue_size"],
                "avg_transcription_time_ms": round(performance_metrics["performance"]["average_transcription_time_ms"], 2),
                "avg_validation_time_ms": round(performance_metrics["performance"]["average_validation_time_ms"], 2),
                "avg_total_time_ms": round(performance_metrics["performance"]["average_total_time_ms"], 2)
            },
            "errors": {
                "total_errors": performance_metrics["performance"]["failed_requests"],
                "transcription_errors": performance_metrics["performance"]["transcription_errors"],
                "validation_errors": performance_metrics["performance"]["validation_errors"],
                "save_errors": performance_metrics["performance"]["save_errors"],
                "ephy_errors": performance_metrics["performance"]["ephy_lookup_errors"],
                "weather_errors": performance_metrics["performance"]["weather_lookup_errors"],
                "recent_errors": recent_errors
            },
            "tools": {
                "most_used": [
                    {"name": name, "usage_count": data.get("usage_count", 0)}
                    for name, data in most_used_tools
                ],
                "total_tools": len(tool_metrics)
            },
            "agent": {
                "avg_tools_per_query": round(avg_tools_per_query, 2),
                "total_queries": agent_metrics.get("total_queries", 0),
                "successful_reasoning": agent_metrics.get("successful_reasoning", 0),
                "failed_reasoning": agent_metrics.get("failed_reasoning", 0)
            },
            "queue": {
                "current_size": performance_metrics["queue_metrics"]["current_size"],
                "max_size": performance_metrics["queue_metrics"]["max_size"],
                "avg_wait_time_ms": round(performance_metrics["queue_metrics"]["avg_wait_time_ms"], 2),
                "total_processed": performance_metrics["queue_metrics"]["total_processed"],
                "total_failed": performance_metrics["queue_metrics"]["total_failed"]
            },
            "monitoring": {
                "events_processed": performance_metrics["monitoring_health"]["events_processed"],
                "events_dropped": performance_metrics["monitoring_health"]["events_dropped"],
                "memory_usage_mb": round(performance_metrics["monitoring_health"]["memory_usage_mb"], 2),
                "queue_size": performance_metrics["monitoring_health"]["queue_size"],
                "last_error": performance_metrics["monitoring_health"]["last_error"]
            },
            "activity": {
                "last_activity_seconds_ago": health_status["last_activity_seconds_ago"],
                "total_events": performance_metrics["total_events"]
            }
        }
        
        return dashboard_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting dashboard data: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve dashboard data")


@router.get("/alerts")
async def get_alerts(
    current_user: dict = Depends(check_admin_access)
):
    """Get current system alerts (admin only)"""
    try:
        health_status = improved_voice_monitor.get_health_status()
        performance_metrics = improved_voice_monitor.get_performance_metrics()
        
        alerts = []
        
        # Health score alerts
        if health_status["health_score"] < 70:
            alerts.append({
                "level": "critical" if health_status["health_score"] < 50 else "warning",
                "type": "health_score",
                "message": f"System health score is {health_status['health_score']}",
                "timestamp": datetime.now().isoformat()
            })
        
        # Error rate alerts
        error_rate = health_status.get("error_rate", 0)
        if error_rate > 0.1:  # 10% error rate
            alerts.append({
                "level": "critical" if error_rate > 0.2 else "warning",
                "type": "error_rate",
                "message": f"High error rate: {error_rate:.2%}",
                "timestamp": datetime.now().isoformat()
            })
        
        # Memory usage alerts
        memory_usage = performance_metrics["monitoring_health"]["memory_usage_mb"]
        if memory_usage > 500:  # 500MB
            alerts.append({
                "level": "warning" if memory_usage < 1000 else "critical",
                "type": "memory_usage",
                "message": f"High memory usage: {memory_usage:.1f}MB",
                "timestamp": datetime.now().isoformat()
            })
        
        # Queue size alerts
        queue_size = performance_metrics["processing_queue_size"]
        if queue_size > 100:
            alerts.append({
                "level": "warning" if queue_size < 500 else "critical",
                "type": "queue_size",
                "message": f"Large processing queue: {queue_size} items",
                "timestamp": datetime.now().isoformat()
            })
        
        # Events dropped alerts
        events_dropped = performance_metrics["monitoring_health"]["events_dropped"]
        if events_dropped > 0:
            alerts.append({
                "level": "critical",
                "type": "events_dropped",
                "message": f"Events dropped: {events_dropped}",
                "timestamp": datetime.now().isoformat()
            })
        
        return {
            "timestamp": datetime.now().isoformat(),
            "alerts": alerts,
            "count": len(alerts)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve alerts")
