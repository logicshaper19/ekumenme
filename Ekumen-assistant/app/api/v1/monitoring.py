"""
Monitoring API endpoints for voice journal system
Provides metrics, health checks, and observability data
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Dict, List, Optional, Any
import logging
from datetime import datetime, timedelta

from app.services.monitoring.voice_monitoring import voice_monitor
from app.services.shared.auth_service import AuthService

logger = logging.getLogger(__name__)

router = APIRouter()
auth_service = AuthService()


@router.get("/health")
async def health_check():
    """Basic health check endpoint"""
    try:
        health_status = voice_monitor.get_health_status()
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
    current_user: dict = Depends(auth_service.get_current_user)
):
    """Get comprehensive voice system metrics"""
    try:
        # Check if user has admin privileges
        if not current_user.get("is_admin", False):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        metrics = voice_monitor.get_performance_metrics()
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
    current_user: dict = Depends(auth_service.get_current_user)
):
    """Get metrics for a specific user"""
    try:
        # Users can only see their own metrics, admins can see any user
        if not current_user.get("is_admin", False) and current_user.get("user_id") != user_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        user_metrics = voice_monitor.get_user_metrics(user_id, hours)
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
    current_user: dict = Depends(auth_service.get_current_user)
):
    """Get metrics for a specific organization"""
    try:
        # Users can only see their own org metrics, admins can see any org
        if not current_user.get("is_admin", False) and current_user.get("org_id") != org_id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        org_metrics = voice_monitor.get_org_metrics(org_id, hours)
        return {
            "timestamp": datetime.now().isoformat(),
            "org_metrics": org_metrics
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting org metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve org metrics")


@router.get("/errors")
async def get_recent_errors(
    limit: int = Query(20, ge=1, le=100),
    current_user: dict = Depends(auth_service.get_current_user)
):
    """Get recent errors from the voice system"""
    try:
        # Check if user has admin privileges
        if not current_user.get("is_admin", False):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        recent_errors = voice_monitor.get_recent_errors(limit)
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
    current_user: dict = Depends(auth_service.get_current_user)
):
    """Export metrics in various formats"""
    try:
        # Check if user has admin privileges
        if not current_user.get("is_admin", False):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        exported_data = voice_monitor.export_metrics(format)
        
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
        health_status = voice_monitor.get_health_status()
        
        # Return simplified status for public consumption
        return {
            "status": health_status["status"],
            "health_score": health_status["health_score"],
            "active_connections": health_status["active_connections"],
            "last_activity_seconds_ago": health_status["last_activity_seconds_ago"],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve system status")


@router.post("/test")
async def test_monitoring(
    current_user: dict = Depends(auth_service.get_current_user)
):
    """Test monitoring system by generating sample events"""
    try:
        # Check if user has admin privileges
        if not current_user.get("is_admin", False):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Generate test events
        from app.services.monitoring.voice_monitoring import VoiceEvent
        
        test_events = [
            VoiceEvent(
                event_type='transcription_complete',
                timestamp=datetime.now(),
                duration_ms=1500.0,
                user_id=current_user.get("user_id"),
                org_id=current_user.get("org_id"),
                success=True
            ),
            VoiceEvent(
                event_type='validation_complete',
                timestamp=datetime.now(),
                duration_ms=3000.0,
                user_id=current_user.get("user_id"),
                org_id=current_user.get("org_id"),
                entry_id="test_entry_123",
                success=True
            ),
            VoiceEvent(
                event_type='save_complete',
                timestamp=datetime.now(),
                duration_ms=500.0,
                user_id=current_user.get("user_id"),
                org_id=current_user.get("org_id"),
                entry_id="test_entry_123",
                success=True
            )
        ]
        
        for event in test_events:
            voice_monitor.record_event(event)
        
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
    current_user: dict = Depends(auth_service.get_current_user)
):
    """Get dashboard data for monitoring UI"""
    try:
        # Check if user has admin privileges
        if not current_user.get("is_admin", False):
            raise HTTPException(status_code=403, detail="Admin access required")
        
        # Get comprehensive dashboard data
        health_status = voice_monitor.get_health_status()
        performance_metrics = voice_monitor.get_performance_metrics()
        recent_errors = voice_monitor.get_recent_errors(10)
        
        # Calculate additional metrics
        uptime_hours = 24  # This would be calculated from system start time
        success_rate = (
            performance_metrics["performance"]["successful_requests"] / 
            performance_metrics["performance"]["total_requests"] * 100
            if performance_metrics["performance"]["total_requests"] > 0 else 100
        )
        
        dashboard_data = {
            "timestamp": datetime.now().isoformat(),
            "overview": {
                "status": health_status["status"],
                "health_score": health_status["health_score"],
                "uptime_hours": uptime_hours,
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
