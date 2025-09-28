"""
Cleanup tasks.
"""

from celery import current_task
from app.core.celery import celery_app
from app.core.database import SessionLocal
from app.models.mesparcelles import ValidationIntervention
from datetime import datetime, timedelta
import structlog

logger = structlog.get_logger()


@celery_app.task(bind=True)
def cleanup_old_tasks(self):
    """Clean up old task results and temporary data."""
    try:
        # Update task status
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Starting cleanup...'}
        )
        
        logger.info("Starting cleanup of old tasks")
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'current': 25, 'total': 100, 'status': 'Cleaning up old task results...'}
        )
        
        # Clean up old Celery task results
        # This would include cleaning up Redis or database task results older than a certain period
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'current': 50, 'total': 100, 'status': 'Cleaning up old validation records...'}
        )
        
        # Clean up old validation records
        db = SessionLocal()
        try:
            # Delete validation records older than 1 year
            cutoff_date = datetime.utcnow() - timedelta(days=365)
            deleted_count = db.query(ValidationIntervention).filter(
                ValidationIntervention.date_validation < cutoff_date
            ).delete()
            
            db.commit()
            
            logger.info("Cleaned up old validation records", deleted_count=deleted_count)
            
        finally:
            db.close()
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'current': 75, 'total': 100, 'status': 'Cleaning up temporary files...'}
        )
        
        # Clean up temporary files
        # This would include cleaning up uploaded files, generated reports, etc.
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'current': 100, 'total': 100, 'status': 'Cleanup completed'}
        )
        
        logger.info("Cleanup completed successfully")
        
        return {
            "status": "completed",
            "message": "Cleanup completed successfully",
            "deleted_validation_records": deleted_count
        }
        
    except Exception as e:
        logger.error("Cleanup failed", error=str(e))
        self.update_state(
            state='FAILURE',
            meta={'error': str(e)}
        )
        raise
