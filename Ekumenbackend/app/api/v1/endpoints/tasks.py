"""
Background tasks endpoints.
"""

from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks
from app.core.celery import celery_app
import structlog

logger = structlog.get_logger()
router = APIRouter()


@router.post("/sync/exploitation/{siret}")
async def sync_exploitation(
    siret: str,
    millesime: int,
    background_tasks: BackgroundTasks
):
    """Start synchronization task for a specific exploitation."""
    try:
        # Start Celery task
        task = celery_app.send_task(
            'app.tasks.mesparcelles_sync.sync_exploitation',
            args=[siret, millesime]
        )
        
        logger.info("Exploitation sync task started", siret=siret, millesime=millesime, task_id=task.id)
        
        return {
            "message": "Synchronization task started",
            "task_id": task.id,
            "siret": siret,
            "millesime": millesime
        }
    except Exception as e:
        logger.error("Failed to start sync task", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to start sync task: {str(e)}")


@router.post("/sync/all-exploitations")
async def sync_all_exploitations(
    millesime: int,
    background_tasks: BackgroundTasks
):
    """Start synchronization task for all exploitations."""
    try:
        # Start Celery task
        task = celery_app.send_task(
            'app.tasks.mesparcelles_sync.sync_all_exploitations',
            args=[millesime]
        )
        
        logger.info("All exploitations sync task started", millesime=millesime, task_id=task.id)
        
        return {
            "message": "Synchronization task started for all exploitations",
            "task_id": task.id,
            "millesime": millesime
        }
    except Exception as e:
        logger.error("Failed to start sync all task", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to start sync task: {str(e)}")


@router.post("/ephy/import-zip")
async def import_ephy_zip(
    zip_path: str,
    background_tasks: BackgroundTasks
):
    """Start EPHY ZIP import task."""
    try:
        # Start Celery task
        task = celery_app.send_task(
            'app.tasks.ephy_import.import_zip_file',
            args=[zip_path]
        )
        
        logger.info("EPHY ZIP import task started", zip_path=zip_path, task_id=task.id)
        
        return {
            "message": "EPHY ZIP import task started",
            "task_id": task.id,
            "zip_path": zip_path
        }
    except Exception as e:
        logger.error("Failed to start EPHY ZIP import task", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to start import task: {str(e)}")


@router.post("/ephy/import-csv")
async def import_ephy_csv(
    file_path: str,
    csv_type: str,
    background_tasks: BackgroundTasks
):
    """Start EPHY CSV import task."""
    try:
        # Start Celery task
        task = celery_app.send_task(
            'app.tasks.ephy_import.import_csv',
            args=[file_path, csv_type]
        )
        
        logger.info("EPHY import task started", file_path=file_path, csv_type=csv_type, task_id=task.id)
        
        return {
            "message": "EPHY import task started",
            "task_id": task.id,
            "file_path": file_path,
            "csv_type": csv_type
        }
    except Exception as e:
        logger.error("Failed to start EPHY import task", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to start import task: {str(e)}")


@router.get("/status/{task_id}")
async def get_task_status(task_id: str):
    """Get status of a background task."""
    try:
        task = celery_app.AsyncResult(task_id)
        
        if task.state == 'PENDING':
            response = {
                'state': task.state,
                'current': 0,
                'total': 1,
                'status': 'Task is waiting to be processed...'
            }
        elif task.state != 'FAILURE':
            response = {
                'state': task.state,
                'current': task.info.get('current', 0),
                'total': task.info.get('total', 1),
                'status': task.info.get('status', '')
            }
        else:
            # Task failed
            response = {
                'state': task.state,
                'current': 0,
                'total': 1,
                'status': str(task.info)
            }
        
        return response
    except Exception as e:
        logger.error("Failed to get task status", task_id=task_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get task status: {str(e)}")


@router.get("/active")
async def get_active_tasks():
    """Get list of active tasks."""
    try:
        # Get active tasks from Celery
        inspect = celery_app.control.inspect()
        active_tasks = inspect.active()
        
        if not active_tasks:
            return {"active_tasks": []}
        
        # Flatten the results
        all_active_tasks = []
        for worker, tasks in active_tasks.items():
            for task in tasks:
                all_active_tasks.append({
                    "worker": worker,
                    "task_id": task.get("id"),
                    "name": task.get("name"),
                    "args": task.get("args", []),
                    "kwargs": task.get("kwargs", {}),
                    "time_start": task.get("time_start")
                })
        
        return {"active_tasks": all_active_tasks}
    except Exception as e:
        logger.error("Failed to get active tasks", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to get active tasks: {str(e)}")


@router.post("/compliance/check-all")
async def check_all_compliance(
    year: int,
    background_tasks: BackgroundTasks
):
    """Start compliance checking task for all exploitations."""
    try:
        # Start Celery task
        task = celery_app.send_task(
            'app.tasks.compliance_check.check_all_compliance',
            args=[year]
        )
        
        logger.info("Compliance check task started", year=year, task_id=task.id)
        
        return {
            "message": "Compliance checking task started",
            "task_id": task.id,
            "year": year
        }
    except Exception as e:
        logger.error("Failed to start compliance check task", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to start compliance check task: {str(e)}")
