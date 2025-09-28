"""
MesParcelles synchronization tasks.
"""

from celery import current_task
from app.core.celery import celery_app
from app.core.database import SessionLocal
from app.models.mesparcelles import Exploitation
import structlog
import httpx

logger = structlog.get_logger()


@celery_app.task(bind=True)
def sync_exploitation(self, siret: str, millesime: int):
    """Sync data for a specific exploitation from MesParcelles API."""
    try:
        # Update task status
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Starting synchronization...'}
        )
        
        # Create database session
        db = SessionLocal()
        
        try:
            # Check if exploitation exists
            exploitation = db.query(Exploitation).filter(Exploitation.siret == siret).first()
            if not exploitation:
                logger.error("Exploitation not found", siret=siret)
                return {"error": "Exploitation not found"}
            
            # Update progress
            self.update_state(
                state='PROGRESS',
                meta={'current': 25, 'total': 100, 'status': 'Fetching data from MesParcelles API...'}
            )
            
            # Here you would make actual API calls to MesParcelles
            # For now, we'll simulate the process
            logger.info("Syncing exploitation", siret=siret, millesime=millesime)
            
            # Simulate API call
            # response = httpx.get(f"{settings.mesparcelles_api_url}/exploitations/{siret}")
            
            # Update progress
            self.update_state(
                state='PROGRESS',
                meta={'current': 75, 'total': 100, 'status': 'Processing data...'}
            )
            
            # Process and save data
            # This would include parsing the response and updating the database
            
            # Update progress
            self.update_state(
                state='PROGRESS',
                meta={'current': 100, 'total': 100, 'status': 'Synchronization completed'}
            )
            
            logger.info("Exploitation sync completed", siret=siret, millesime=millesime)
            
            return {
                "status": "completed",
                "siret": siret,
                "millesime": millesime,
                "message": "Synchronization completed successfully"
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error("Exploitation sync failed", siret=siret, error=str(e))
        self.update_state(
            state='FAILURE',
            meta={'error': str(e)}
        )
        raise


@celery_app.task(bind=True)
def sync_all_exploitations(self, millesime: int):
    """Sync data for all exploitations from MesParcelles API."""
    try:
        # Create database session
        db = SessionLocal()
        
        try:
            # Get all exploitations
            exploitations = db.query(Exploitation).all()
            total = len(exploitations)
            
            if total == 0:
                return {"message": "No exploitations found"}
            
            # Update task status
            self.update_state(
                state='PROGRESS',
                meta={'current': 0, 'total': total, 'status': f'Starting sync for {total} exploitations...'}
            )
            
            completed = 0
            errors = []
            
            for exploitation in exploitations:
                try:
                    # Sync individual exploitation
                    result = sync_exploitation.delay(exploitation.siret, millesime)
                    
                    # Wait for completion (in production, you might want to handle this differently)
                    result.get(timeout=300)  # 5 minutes timeout
                    
                    completed += 1
                    
                    # Update progress
                    self.update_state(
                        state='PROGRESS',
                        meta={
                            'current': completed,
                            'total': total,
                            'status': f'Completed {completed}/{total} exploitations'
                        }
                    )
                    
                except Exception as e:
                    logger.error("Failed to sync exploitation", siret=exploitation.siret, error=str(e))
                    errors.append({"siret": exploitation.siret, "error": str(e)})
            
            logger.info("All exploitations sync completed", completed=completed, total=total, errors=len(errors))
            
            return {
                "status": "completed",
                "total": total,
                "completed": completed,
                "errors": errors,
                "message": f"Synchronization completed: {completed}/{total} exploitations"
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error("All exploitations sync failed", error=str(e))
        self.update_state(
            state='FAILURE',
            meta={'error': str(e)}
        )
        raise
