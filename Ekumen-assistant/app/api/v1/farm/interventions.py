"""
Interventions API endpoints
Provides access to farm intervention data from MesParcelles
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func

from app.core.database import get_async_db
from app.models.user import User
from app.models.mesparcelles import Intervention, Parcelle
from app.models.organization import OrganizationFarmAccess, OrganizationMembership
from app.services.shared import AuthService
from app.api.v1.knowledge_base.schemas import PaginatedResponse, create_paginated_response_from_skip
from pydantic import BaseModel
from decimal import Decimal
from datetime import date
import uuid

router = APIRouter(prefix="/interventions", tags=["Interventions"])

# Initialize auth service
auth_service = AuthService()


class InterventionResponse(BaseModel):
    """Response model for intervention data"""
    id: str
    uuid_intervention: str
    type_intervention: str
    id_type_intervention: Optional[int] = None
    date_intervention: date
    date_debut: date
    date_fin: date
    surface_travaillee_ha: float
    id_culture: Optional[int] = None
    materiel_utilise: Optional[str] = None
    intrants: Optional[dict] = None
    parcelle_id: str
    siret: str
    
    class Config:
        from_attributes = True


@router.get("/", response_model=PaginatedResponse)
async def get_interventions(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=1000, description="Number of records to return"),
    farm_siret: Optional[str] = Query(None, description="Filter by farm SIRET"),
    parcelle_id: Optional[str] = Query(None, description="Filter by parcelle ID"),
    intervention_type: Optional[str] = Query(None, description="Filter by intervention type"),
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get interventions for the current user's accessible farms
    
    Args:
        skip: Number of records to skip for pagination
        limit: Maximum number of records to return
        farm_siret: Optional filter by specific farm SIRET
        parcelle_id: Optional filter by parcelle ID
        intervention_type: Optional filter by intervention type
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        PaginatedResponse: List of interventions with pagination metadata
    """
    try:
        # Get user's accessible farm SIRETs
        accessible_farms_query = select(OrganizationFarmAccess.farm_siret).where(
            OrganizationFarmAccess.organization_id.in_(
                select(OrganizationMembership.organization_id)
                .where(OrganizationMembership.user_id == current_user.id)
            )
        )
        
        accessible_farms_result = await db.execute(accessible_farms_query)
        accessible_farm_sirets = [row[0] for row in accessible_farms_result.fetchall()]
        
        if not accessible_farm_sirets:
            return create_paginated_response_from_skip([], 0, skip, limit)
        
        # Build base query for interventions
        base_query = select(Intervention).where(
            Intervention.siret.in_(accessible_farm_sirets)
        )
        
        # Apply farm filter if specified
        if farm_siret:
            if farm_siret not in accessible_farm_sirets:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to specified farm"
                )
            base_query = base_query.where(Intervention.siret == farm_siret)
        
        # Apply parcelle filter if specified
        if parcelle_id:
            try:
                parcelle_uuid = uuid.UUID(parcelle_id)
                base_query = base_query.where(Intervention.parcelle_id == parcelle_uuid)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid parcelle ID format"
                )
        
        # Apply intervention type filter if specified
        if intervention_type:
            base_query = base_query.where(Intervention.type_intervention.ilike(f"%{intervention_type}%"))
        
        # Get total count
        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Get paginated results
        interventions_query = base_query.offset(skip).limit(limit).order_by(Intervention.date_intervention.desc())
        interventions_result = await db.execute(interventions_query)
        interventions = interventions_result.scalars().all()
        
        # Convert to response format
        intervention_items = [
            InterventionResponse(
                id=str(intervention.id),
                uuid_intervention=str(intervention.uuid_intervention),
                type_intervention=intervention.type_intervention,
                id_type_intervention=intervention.id_type_intervention,
                date_intervention=intervention.date_intervention,
                date_debut=intervention.date_debut,
                date_fin=intervention.date_fin,
                surface_travaillee_ha=float(intervention.surface_travaillee_ha),
                id_culture=intervention.id_culture,
                materiel_utilise=intervention.materiel_utilise,
                intrants=intervention.intrants,
                parcelle_id=str(intervention.parcelle_id),
                siret=intervention.siret
            )
            for intervention in interventions
        ]
        
        return create_paginated_response_from_skip(intervention_items, total, skip, limit)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve interventions: {str(e)}"
        )


@router.get("/{intervention_id}", response_model=InterventionResponse)
async def get_intervention(
    intervention_id: str,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get a specific intervention by ID
    
    Args:
        intervention_id: UUID of the intervention
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        InterventionResponse: Intervention details
    """
    try:
        # Validate UUID format
        try:
            intervention_uuid = uuid.UUID(intervention_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid intervention ID format"
            )
        
        # Get user's accessible farm SIRETs
        accessible_farms_query = select(OrganizationFarmAccess.farm_siret).where(
            OrganizationFarmAccess.organization_id.in_(
                select(OrganizationMembership.organization_id)
                .where(OrganizationMembership.user_id == current_user.id)
            )
        )
        
        accessible_farms_result = await db.execute(accessible_farms_query)
        accessible_farm_sirets = [row[0] for row in accessible_farms_result.fetchall()]
        
        # Get intervention with access control
        intervention_query = select(Intervention).where(
            and_(
                Intervention.id == intervention_uuid,
                Intervention.siret.in_(accessible_farm_sirets)
            )
        )
        
        intervention_result = await db.execute(intervention_query)
        intervention = intervention_result.scalar_one_or_none()
        
        if not intervention:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Intervention not found or access denied"
            )
        
        return InterventionResponse(
            id=str(intervention.id),
            uuid_intervention=str(intervention.uuid_intervention),
            type_intervention=intervention.type_intervention,
            id_type_intervention=intervention.id_type_intervention,
            date_intervention=intervention.date_intervention,
            date_debut=intervention.date_debut,
            date_fin=intervention.date_fin,
            surface_travaillee_ha=float(intervention.surface_travaillee_ha),
            id_culture=intervention.id_culture,
            materiel_utilise=intervention.materiel_utilise,
            intrants=intervention.intrants,
            parcelle_id=str(intervention.parcelle_id),
            siret=intervention.siret
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve intervention: {str(e)}"
        )


@router.get("/farm/{farm_siret}", response_model=List[InterventionResponse])
async def get_interventions_by_farm(
    farm_siret: str,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get all interventions for a specific farm
    
    Args:
        farm_siret: SIRET of the farm
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List[InterventionResponse]: List of interventions for the farm
    """
    try:
        # Check if user has access to this farm
        access_query = select(OrganizationFarmAccess).where(
            and_(
                OrganizationFarmAccess.organization_id.in_(
                    select(OrganizationMembership.organization_id)
                    .where(OrganizationMembership.user_id == current_user.id)
                ),
                OrganizationFarmAccess.farm_siret == farm_siret
            )
        )
        
        access_result = await db.execute(access_query)
        access = access_result.scalar_one_or_none()
        
        if not access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to specified farm"
            )
        
        # Get interventions for the farm
        interventions_query = select(Intervention).where(
            Intervention.siret == farm_siret
        ).order_by(Intervention.date_intervention.desc())
        
        interventions_result = await db.execute(interventions_query)
        interventions = interventions_result.scalars().all()
        
        return [
            InterventionResponse(
                id=str(intervention.id),
                uuid_intervention=str(intervention.uuid_intervention),
                type_intervention=intervention.type_intervention,
                id_type_intervention=intervention.id_type_intervention,
                date_intervention=intervention.date_intervention,
                date_debut=intervention.date_debut,
                date_fin=intervention.date_fin,
                surface_travaillee_ha=float(intervention.surface_travaillee_ha),
                id_culture=intervention.id_culture,
                materiel_utilise=intervention.materiel_utilise,
                intrants=intervention.intrants,
                parcelle_id=str(intervention.parcelle_id),
                siret=intervention.siret
            )
            for intervention in interventions
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve interventions for farm: {str(e)}"
        )


@router.get("/parcelle/{parcelle_id}", response_model=List[InterventionResponse])
async def get_interventions_by_parcelle(
    parcelle_id: str,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get all interventions for a specific parcelle
    
    Args:
        parcelle_id: UUID of the parcelle
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List[InterventionResponse]: List of interventions for the parcelle
    """
    try:
        # Validate UUID format
        try:
            parcelle_uuid = uuid.UUID(parcelle_id)
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid parcelle ID format"
            )
        
        # Get user's accessible farm SIRETs
        accessible_farms_query = select(OrganizationFarmAccess.farm_siret).where(
            OrganizationFarmAccess.organization_id.in_(
                select(OrganizationMembership.organization_id)
                .where(OrganizationMembership.user_id == current_user.id)
            )
        )
        
        accessible_farms_result = await db.execute(accessible_farms_query)
        accessible_farm_sirets = [row[0] for row in accessible_farms_result.fetchall()]
        
        # Get interventions for the parcelle with access control
        interventions_query = select(Intervention).where(
            and_(
                Intervention.parcelle_id == parcelle_uuid,
                Intervention.siret.in_(accessible_farm_sirets)
            )
        ).order_by(Intervention.date_intervention.desc())
        
        interventions_result = await db.execute(interventions_query)
        interventions = interventions_result.scalars().all()
        
        return [
            InterventionResponse(
                id=str(intervention.id),
                uuid_intervention=str(intervention.uuid_intervention),
                type_intervention=intervention.type_intervention,
                id_type_intervention=intervention.id_type_intervention,
                date_intervention=intervention.date_intervention,
                date_debut=intervention.date_debut,
                date_fin=intervention.date_fin,
                surface_travaillee_ha=float(intervention.surface_travaillee_ha),
                id_culture=intervention.id_culture,
                materiel_utilise=intervention.materiel_utilise,
                intrants=intervention.intrants,
                parcelle_id=str(intervention.parcelle_id),
                siret=intervention.siret
            )
            for intervention in interventions
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve interventions for parcelle: {str(e)}"
        )
