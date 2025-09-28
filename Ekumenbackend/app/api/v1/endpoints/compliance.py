"""
Compliance checking endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.mesparcelles import ValidationIntervention, ConformiteReglementaire
from app.schemas.mesparcelles import (
    ValidationInterventionCreate, ValidationInterventionResponse,
    ConformiteReglementaireCreate, ConformiteReglementaireResponse
)
import structlog

logger = structlog.get_logger()
router = APIRouter()


@router.get("/intervention/{uuid_intervention}", response_model=ValidationInterventionResponse)
async def get_intervention_validation(
    uuid_intervention: str,
    db: Session = Depends(get_db)
):
    """Get validation status for a specific intervention."""
    validation = db.query(ValidationIntervention).filter(
        ValidationIntervention.uuid_intervention == uuid_intervention
    ).first()
    
    if not validation:
        raise HTTPException(status_code=404, detail="Validation not found")
    
    return validation


@router.post("/intervention/{uuid_intervention}", response_model=ValidationInterventionResponse)
async def validate_intervention(
    uuid_intervention: str,
    validation: ValidationInterventionCreate,
    db: Session = Depends(get_db)
):
    """Create or update intervention validation."""
    existing = db.query(ValidationIntervention).filter(
        ValidationIntervention.uuid_intervention == uuid_intervention
    ).first()
    
    if existing:
        # Update existing validation
        for field, value in validation.dict(exclude_unset=True).items():
            setattr(existing, field, value)
        db.commit()
        db.refresh(existing)
        logger.info("Intervention validation updated", uuid_intervention=uuid_intervention)
        return existing
    else:
        # Create new validation
        db_validation = ValidationIntervention(
            uuid_intervention=uuid_intervention,
            **validation.dict()
        )
        db.add(db_validation)
        db.commit()
        db.refresh(db_validation)
        logger.info("Intervention validation created", uuid_intervention=uuid_intervention)
        return db_validation


@router.get("/exploitation/{siret}", response_model=ConformiteReglementaireResponse)
async def get_exploitation_compliance(
    siret: str,
    year: int = Query(..., description="Year to check compliance"),
    db: Session = Depends(get_db)
):
    """Get compliance status for an exploitation."""
    compliance = db.query(ConformiteReglementaire).filter(
        ConformiteReglementaire.siret_exploitation == siret,
        ConformiteReglementaire.annee == year
    ).first()
    
    if not compliance:
        raise HTTPException(status_code=404, detail="Compliance record not found")
    
    return compliance


@router.post("/exploitation/{siret}", response_model=ConformiteReglementaireResponse)
async def create_exploitation_compliance(
    siret: str,
    compliance: ConformiteReglementaireCreate,
    db: Session = Depends(get_db)
):
    """Create or update exploitation compliance record."""
    existing = db.query(ConformiteReglementaire).filter(
        ConformiteReglementaire.siret_exploitation == siret,
        ConformiteReglementaire.annee == compliance.annee
    ).first()
    
    if existing:
        # Update existing compliance
        for field, value in compliance.dict(exclude_unset=True).items():
            setattr(existing, field, value)
        db.commit()
        db.refresh(existing)
        logger.info("Exploitation compliance updated", siret=siret, year=compliance.annee)
        return existing
    else:
        # Create new compliance
        db_compliance = ConformiteReglementaire(
            siret_exploitation=siret,
            **compliance.dict()
        )
        db.add(db_compliance)
        db.commit()
        db.refresh(db_compliance)
        logger.info("Exploitation compliance created", siret=siret, year=compliance.annee)
        return db_compliance
