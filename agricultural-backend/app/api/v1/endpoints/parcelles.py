"""
Parcelles endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.mesparcelles import Parcelle
from app.schemas.mesparcelles import ParcelleCreate, ParcelleResponse
import structlog

logger = structlog.get_logger()
router = APIRouter()


@router.get("/", response_model=List[ParcelleResponse])
async def get_parcelles(
    siret_exploitation: Optional[str] = Query(None, description="SIRET of the exploitation"),
    millesime: Optional[int] = Query(None, description="Year"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get parcelles with optional filtering."""
    query = db.query(Parcelle)
    
    if siret_exploitation:
        query = query.filter(Parcelle.siret_exploitation == siret_exploitation)
    
    if millesime:
        query = query.filter(Parcelle.millesime == millesime)
    
    parcelles = query.offset(skip).limit(limit).all()
    return parcelles


@router.get("/{uuid_parcelle}", response_model=ParcelleResponse)
async def get_parcelle(uuid_parcelle: str, db: Session = Depends(get_db)):
    """Get a specific parcelle by UUID."""
    parcelle = db.query(Parcelle).filter(Parcelle.uuid_parcelle == uuid_parcelle).first()
    if not parcelle:
        raise HTTPException(status_code=404, detail="Parcelle not found")
    return parcelle


@router.post("/", response_model=ParcelleResponse)
async def create_parcelle(
    parcelle: ParcelleCreate,
    db: Session = Depends(get_db)
):
    """Create a new parcelle."""
    db_parcelle = Parcelle(**parcelle.dict())
    db.add(db_parcelle)
    db.commit()
    db.refresh(db_parcelle)
    
    logger.info("Parcelle created", uuid_parcelle=str(db_parcelle.uuid_parcelle))
    return db_parcelle
