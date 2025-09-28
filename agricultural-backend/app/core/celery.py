"""
Celery configuration for background tasks.
"""

from celery import Celery
from .config import settings

# Create Celery instance
celery_app = Celery(
    "agricultural_backend",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.tasks.mesparcelles_sync",
        "app.tasks.ephy_import",
        "app.tasks.compliance_check",
        "app.tasks.reports",
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Europe/Paris",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    result_expires=3600,  # 1 hour
    beat_schedule={
        "sync-mesparcelles-daily": {
            "task": "app.tasks.mesparcelles_sync.sync_all_exploitations",
            "schedule": 86400.0,  # Daily
            "args": (2024,),  # Current year
        },
        "check-compliance-weekly": {
            "task": "app.tasks.compliance_check.check_all_compliance",
            "schedule": 604800.0,  # Weekly
        },
        "cleanup-old-tasks": {
            "task": "app.tasks.cleanup.cleanup_old_tasks",
            "schedule": 3600.0,  # Hourly
        },
    },
)
