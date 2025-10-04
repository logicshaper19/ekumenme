"""
Parcelles API endpoints
Provides access to farm parcel data from MesParcelles
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.core.database import get_async_db
from app.models.user import User
from app.models.mesparcelles import Parcelle, Exploitation
from app.models.organization import OrganizationFarmAccess, OrganizationMembership
from app.services.shared import AuthService
from app.api.v1.knowledge_base.schemas import PaginatedResponse, create_paginated_response_from_skip
from pydantic import BaseModel
from decimal import Decimal
from datetime import date
import uuid

router = APIRouter(prefix="/parcelles", tags=["Parcelles"])

# Initialize auth service
auth_service = AuthService()


class ParcelleResponse(BaseModel):
    """Response model for parcelle data"""
    id: str
    nom: str
    surface_ha: float
    surface_mesuree_ha: Optional[float] = None
    culture_code: Optional[str] = None
    variete: Optional[str] = None
    date_semis: Optional[date] = None
    bbch_stage: Optional[int] = None
    commune_insee: Optional[str] = None
    millesime: int
    geometrie_vide: bool
    succession_cultures: Optional[dict] = None
    culture_intermediaire: Optional[dict] = None
    
    class Config:
        from_attributes = True


@router.get("/", response_model=PaginatedResponse)
async def get_parcelles(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(50, ge=1, le=1000, description="Number of records to return"),
    farm_siret: Optional[str] = Query(None, description="Filter by farm SIRET"),
    culture_filter: Optional[str] = Query(None, description="Filter by culture code"),
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get parcelles for the current user's accessible farms
    
    Args:
        skip: Number of records to skip for pagination
        limit: Maximum number of records to return
        farm_siret: Optional filter by specific farm SIRET
        culture_filter: Optional filter by culture code
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        PaginatedResponse: List of parcelles with pagination metadata
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
        
        # Build base query for parcelles
        base_query = select(Parcelle).where(
            Parcelle.siret.in_(accessible_farm_sirets)
        )
        
        # Apply farm filter if specified
        if farm_siret:
            if farm_siret not in accessible_farm_sirets:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to specified farm"
                )
            base_query = base_query.where(Parcelle.siret == farm_siret)
        
        # Apply culture filter if specified
        if culture_filter:
            base_query = base_query.where(Parcelle.culture_code.ilike(f"%{culture_filter}%"))
        
        # Get total count
        count_query = select(func.count()).select_from(base_query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar()
        
        # Get paginated results
        parcelles_query = base_query.offset(skip).limit(limit).order_by(Parcelle.nom)
        parcelles_result = await db.execute(parcelles_query)
        parcelles = parcelles_result.scalars().all()
        
        # Convert to response format
        parcelle_items = [
            ParcelleResponse(
                id=str(parcelle.id),
                nom=parcelle.nom,
                surface_ha=float(parcelle.surface_ha),
                surface_mesuree_ha=float(parcelle.surface_mesuree_ha) if parcelle.surface_mesuree_ha else None,
                culture_code=parcelle.culture_code,
                variete=parcelle.variete,
                date_semis=parcelle.date_semis,
                bbch_stage=parcelle.bbch_stage,
                commune_insee=parcelle.commune_insee,
                millesime=parcelle.millesime,
                geometrie_vide=parcelle.geometrie_vide,
                succession_cultures=parcelle.succession_cultures,
                culture_intermediaire=parcelle.culture_intermediaire
            )
            for parcelle in parcelles
        ]
        
        return create_paginated_response_from_skip(parcelle_items, total, skip, limit)
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve parcelles: {str(e)}"
        )


@router.get("/{parcelle_id}", response_model=ParcelleResponse)
async def get_parcelle(
    parcelle_id: str,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get a specific parcelle by ID
    
    Args:
        parcelle_id: UUID of the parcelle
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        ParcelleResponse: Parcelle details
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
        
        # Get parcelle with access control
        parcelle_query = select(Parcelle).where(
            and_(
                Parcelle.id == parcelle_uuid,
                Parcelle.siret.in_(accessible_farm_sirets)
            )
        )
        
        parcelle_result = await db.execute(parcelle_query)
        parcelle = parcelle_result.scalar_one_or_none()
        
        if not parcelle:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parcelle not found or access denied"
            )
        
        return ParcelleResponse(
            id=str(parcelle.id),
            nom=parcelle.nom,
            surface_ha=float(parcelle.surface_ha),
            surface_mesuree_ha=float(parcelle.surface_mesuree_ha) if parcelle.surface_mesuree_ha else None,
            culture_code=parcelle.culture_code,
            variete=parcelle.variete,
            date_semis=parcelle.date_semis,
            bbch_stage=parcelle.bbch_stage,
            commune_insee=parcelle.commune_insee,
            millesime=parcelle.millesime,
            geometrie_vide=parcelle.geometrie_vide,
            succession_cultures=parcelle.succession_cultures,
            culture_intermediaire=parcelle.culture_intermediaire
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve parcelle: {str(e)}"
        )


@router.get("/farm/{farm_siret}", response_model=List[ParcelleResponse])
async def get_parcelles_by_farm(
    farm_siret: str,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get all parcelles for a specific farm
    
    Args:
        farm_siret: SIRET of the farm
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List[ParcelleResponse]: List of parcelles for the farm
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
        
        # Get parcelles for the farm
        parcelles_query = select(Parcelle).where(
            Parcelle.siret == farm_siret
        ).order_by(Parcelle.nom)
        
        parcelles_result = await db.execute(parcelles_query)
        parcelles = parcelles_result.scalars().all()
        
        return [
            ParcelleResponse(
                id=str(parcelle.id),
                nom=parcelle.nom,
                surface_ha=float(parcelle.surface_ha),
                surface_mesuree_ha=float(parcelle.surface_mesuree_ha) if parcelle.surface_mesuree_ha else None,
                culture_code=parcelle.culture_code,
                variete=parcelle.variete,
                date_semis=parcelle.date_semis,
                bbch_stage=parcelle.bbch_stage,
                commune_insee=parcelle.commune_insee,
                millesime=parcelle.millesime,
                geometrie_vide=parcelle.geometrie_vide,
                succession_cultures=parcelle.succession_cultures,
                culture_intermediaire=parcelle.culture_intermediaire
            )
            for parcelle in parcelles
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve parcelles for farm: {str(e)}"
        )
