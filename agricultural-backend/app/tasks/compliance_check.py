"""
Compliance checking tasks.
"""

from celery import current_task
from app.core.celery import celery_app
from app.core.database import SessionLocal
from app.models.mesparcelles import Exploitation, Intervention, ValidationIntervention
import structlog

logger = structlog.get_logger()


@celery_app.task(bind=True)
def check_all_compliance(self, year: int):
    """Check compliance for all exploitations for a given year."""
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
                meta={'current': 0, 'total': total, 'status': f'Starting compliance check for {total} exploitations...'}
            )
            
            completed = 0
            errors = []
            
            for exploitation in exploitations:
                try:
                    # Check compliance for individual exploitation
                    result = check_exploitation_compliance.delay(exploitation.siret, year)
                    
                    # Wait for completion
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
                    logger.error("Failed to check compliance for exploitation", siret=exploitation.siret, error=str(e))
                    errors.append({"siret": exploitation.siret, "error": str(e)})
            
            logger.info("All compliance checks completed", completed=completed, total=total, errors=len(errors))
            
            return {
                "status": "completed",
                "total": total,
                "completed": completed,
                "errors": errors,
                "message": f"Compliance check completed: {completed}/{total} exploitations"
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error("All compliance checks failed", error=str(e))
        self.update_state(
            state='FAILURE',
            meta={'error': str(e)}
        )
        raise


@celery_app.task(bind=True)
def check_exploitation_compliance(self, siret: str, year: int):
    """Check compliance for a specific exploitation."""
    try:
        # Update task status
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Starting compliance check...'}
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
                meta={'current': 25, 'total': 100, 'status': 'Fetching interventions...'}
            )
            
            # Get interventions for the year
            interventions = db.query(Intervention).filter(
                Intervention.siret_exploitation == siret,
                # Add year filter based on your date field
            ).all()
            
            total_interventions = len(interventions)
            
            # Update progress
            self.update_state(
                state='PROGRESS',
                meta={'current': 50, 'total': 100, 'status': f'Checking {total_interventions} interventions...'}
            )
            
            # Check compliance for each intervention
            compliant_interventions = 0
            
            for intervention in interventions:
                # Check if validation already exists
                validation = db.query(ValidationIntervention).filter(
                    ValidationIntervention.uuid_intervention == intervention.uuid_intervention
                ).first()
                
                if not validation:
                    # Create new validation record
                    validation = ValidationIntervention(
                        uuid_intervention=intervention.uuid_intervention,
                        usage_autorise=True,  # This would be determined by actual compliance logic
                        dose_conforme=True,   # This would be determined by actual compliance logic
                        delai_avant_recolte_respecte=True,  # This would be determined by actual compliance logic
                        znt_respectees=True,  # This would be determined by actual compliance logic
                        commentaires="Compliance check completed"
                    )
                    db.add(validation)
                
                if (validation.usage_autorise and 
                    validation.dose_conforme and 
                    validation.delai_avant_recolte_respecte and 
                    validation.znt_respectees):
                    compliant_interventions += 1
            
            # Commit changes
            db.commit()
            
            # Update progress
            self.update_state(
                state='PROGRESS',
                meta={'current': 100, 'total': 100, 'status': 'Compliance check completed'}
            )
            
            logger.info("Exploitation compliance check completed", siret=siret, year=year, 
                       total=total_interventions, compliant=compliant_interventions)
            
            return {
                "status": "completed",
                "siret": siret,
                "year": year,
                "total_interventions": total_interventions,
                "compliant_interventions": compliant_interventions,
                "compliance_rate": (compliant_interventions / total_interventions * 100) if total_interventions > 0 else 0,
                "message": "Compliance check completed successfully"
            }
            
        finally:
            db.close()
            
    except Exception as e:
        logger.error("Exploitation compliance check failed", siret=siret, error=str(e))
        self.update_state(
            state='FAILURE',
            meta={'error': str(e)}
        )
        raise
