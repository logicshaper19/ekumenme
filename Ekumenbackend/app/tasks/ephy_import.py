"""
EPHY data import tasks.
"""

from celery import current_task
from app.core.celery import celery_app
from app.services.ephy_import import EPHYImporter
import structlog
import os

logger = structlog.get_logger()


@celery_app.task(bind=True)
def import_zip_file(self, zip_path: str):
    """Import EPHY data from ZIP file."""
    try:
        # Update task status
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Starting EPHY import...'}
        )
        
        logger.info("Starting EPHY ZIP import", zip_path=zip_path)
        
        # Check if file exists
        if not os.path.exists(zip_path):
            raise FileNotFoundError(f"ZIP file not found: {zip_path}")
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'current': 10, 'total': 100, 'status': 'Initializing importer...'}
        )
        
        # Initialize importer
        importer = EPHYImporter()
        
        try:
            # Update progress
            self.update_state(
                state='PROGRESS',
                meta={'current': 20, 'total': 100, 'status': 'Extracting and importing data...'}
            )
            
            # Import data
            result = importer.import_zip_file(zip_path)
            
            # Update progress
            self.update_state(
                state='PROGRESS',
                meta={'current': 100, 'total': 100, 'status': 'Import completed'}
            )
            
            logger.info("EPHY ZIP import completed", result=result)
            
            return {
                "status": "completed",
                "zip_path": zip_path,
                "import_stats": result,
                "message": "EPHY import completed successfully"
            }
            
        finally:
            importer.close()
        
    except Exception as e:
        logger.error("EPHY ZIP import failed", zip_path=zip_path, error=str(e))
        self.update_state(
            state='FAILURE',
            meta={'error': str(e)}
        )
        raise


@celery_app.task(bind=True)
def import_csv(self, file_path: str, csv_type: str):
    """Import EPHY data from individual CSV file."""
    try:
        # Update task status
        self.update_state(
            state='PROGRESS',
            meta={'current': 0, 'total': 100, 'status': 'Starting CSV import...'}
        )
        
        logger.info("Starting CSV import", file_path=file_path, csv_type=csv_type)
        
        # Check if file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"CSV file not found: {file_path}")
        
        # Update progress
        self.update_state(
            state='PROGRESS',
            meta={'current': 10, 'total': 100, 'status': 'Initializing importer...'}
        )
        
        # Initialize importer
        importer = EPHYImporter()
        
        try:
            # Update progress
            self.update_state(
                state='PROGRESS',
                meta={'current': 20, 'total': 100, 'status': 'Importing CSV data...'}
            )
            
            # Import single CSV file
            importer._import_csv_file(file_path)
            
            # Update progress
            self.update_state(
                state='PROGRESS',
                meta={'current': 100, 'total': 100, 'status': 'Import completed'}
            )
            
            logger.info("CSV import completed", file_path=file_path, csv_type=csv_type)
            
            return {
                "status": "completed",
                "file_path": file_path,
                "csv_type": csv_type,
                "import_stats": importer.import_stats,
                "message": "CSV import completed successfully"
            }
            
        finally:
            importer.close()
        
    except Exception as e:
        logger.error("CSV import failed", file_path=file_path, csv_type=csv_type, error=str(e))
        self.update_state(
            state='FAILURE',
            meta={'error': str(e)}
        )
        raise
