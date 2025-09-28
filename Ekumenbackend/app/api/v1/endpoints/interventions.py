"""
Interventions endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.mesparcelles import Intervention
from app.schemas.mesparcelles import InterventionCreate, InterventionResponse
import structlog

logger = structlog.get_logger()
router = APIRouter()


@router.get("/", response_model=List[InterventionResponse])
async def get_interventions(
    siret_exploitation: Optional[str] = Query(None, description="SIRET of the exploitation"),
    uuid_parcelle: Optional[str] = Query(None, description="Parcelle UUID"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get interventions with optional filtering."""
    query = db.query(Intervention)
    
    if siret_exploitation:
        query = query.filter(Intervention.siret_exploitation == siret_exploitation)
    
    if uuid_parcelle:
        query = query.filter(Intervention.uuid_parcelle == uuid_parcelle)
    
    interventions = query.offset(skip).limit(limit).all()
    return interventions


@router.get("/{uuid_intervention}", response_model=InterventionResponse)
async def get_intervention(uuid_intervention: str, db: Session = Depends(get_db)):
    """Get a specific intervention by UUID."""
    intervention = db.query(Intervention).filter(
        Intervention.uuid_intervention == uuid_intervention
    ).first()
    if not intervention:
        raise HTTPException(status_code=404, detail="Intervention not found")
    return intervention


@router.post("/", response_model=InterventionResponse)
async def create_intervention(
    intervention: InterventionCreate,
    db: Session = Depends(get_db)
):
    """Create a new intervention."""
    db_intervention = Intervention(**intervention.dict())
    db.add(db_intervention)
    db.commit()
    db.refresh(db_intervention)
    
    logger.info("Intervention created", uuid_intervention=str(db_intervention.uuid_intervention))
    return db_intervention
