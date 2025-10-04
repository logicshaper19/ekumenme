"""
Farm Dashboard API endpoints
Provides aggregated data and analytics for farm dashboards
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func, text
from datetime import date, datetime, timedelta

from app.core.database import get_async_db
from app.models.user import User
from app.models.mesparcelles import Exploitation, Parcelle, Intervention
from app.models.organization import OrganizationFarmAccess, OrganizationMembership
from app.services.shared import AuthService
from pydantic import BaseModel

router = APIRouter(prefix="/dashboard", tags=["Farm Dashboard"])

# Initialize auth service
auth_service = AuthService()


class FarmOverviewResponse(BaseModel):
    """Response model for farm overview data"""
    total_farms: int
    total_parcelles: int
    total_surface_ha: float
    total_interventions: int
    recent_interventions: int  # Last 30 days
    bio_farms: int
    avg_parcelles_per_farm: float


class CultureDistributionResponse(BaseModel):
    """Response model for culture distribution"""
    culture_code: str
    culture_name: Optional[str] = None
    parcelle_count: int
    total_surface_ha: float
    percentage: float


class InterventionTimelineResponse(BaseModel):
    """Response model for intervention timeline"""
    date: date
    intervention_count: int
    total_surface_ha: float
    intervention_types: Dict[str, int]


class FarmDashboardResponse(BaseModel):
    """Complete farm dashboard response"""
    overview: FarmOverviewResponse
    culture_distribution: List[CultureDistributionResponse]
    recent_interventions: List[InterventionTimelineResponse]
    farms: List[Dict[str, Any]]


@router.get("/overview", response_model=FarmOverviewResponse)
async def get_farm_overview(
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get farm overview statistics for the current user's accessible farms
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        FarmOverviewResponse: Farm overview statistics
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
            return FarmOverviewResponse(
                total_farms=0,
                total_parcelles=0,
                total_surface_ha=0.0,
                total_interventions=0,
                recent_interventions=0,
                bio_farms=0,
                avg_parcelles_per_farm=0.0
            )
        
        # Get total farms
        farms_query = select(func.count()).select_from(
            select(Exploitation).where(Exploitation.siret.in_(accessible_farm_sirets)).subquery()
        )
        farms_result = await db.execute(farms_query)
        total_farms = farms_result.scalar()
        
        # Get total parcelles
        parcelles_query = select(func.count()).select_from(
            select(Parcelle).where(Parcelle.siret.in_(accessible_farm_sirets)).subquery()
        )
        parcelles_result = await db.execute(parcelles_query)
        total_parcelles = parcelles_result.scalar()
        
        # Get total surface
        surface_query = select(func.coalesce(func.sum(Parcelle.surface_ha), 0)).where(
            Parcelle.siret.in_(accessible_farm_sirets)
        )
        surface_result = await db.execute(surface_query)
        total_surface_ha = float(surface_result.scalar())
        
        # Get total interventions
        interventions_query = select(func.count()).select_from(
            select(Intervention).where(Intervention.siret.in_(accessible_farm_sirets)).subquery()
        )
        interventions_result = await db.execute(interventions_query)
        total_interventions = interventions_result.scalar()
        
        # Get recent interventions (last 30 days)
        thirty_days_ago = date.today() - timedelta(days=30)
        recent_interventions_query = select(func.count()).select_from(
            select(Intervention).where(
                and_(
                    Intervention.siret.in_(accessible_farm_sirets),
                    Intervention.date_intervention >= thirty_days_ago
                )
            ).subquery()
        )
        recent_interventions_result = await db.execute(recent_interventions_query)
        recent_interventions = recent_interventions_result.scalar()
        
        # Get bio farms
        bio_farms_query = select(func.count()).select_from(
            select(Exploitation).where(
                and_(
                    Exploitation.siret.in_(accessible_farm_sirets),
                    Exploitation.bio == True
                )
            ).subquery()
        )
        bio_farms_result = await db.execute(bio_farms_query)
        bio_farms = bio_farms_result.scalar()
        
        # Calculate average parcelles per farm
        avg_parcelles_per_farm = total_parcelles / total_farms if total_farms > 0 else 0.0
        
        return FarmOverviewResponse(
            total_farms=total_farms,
            total_parcelles=total_parcelles,
            total_surface_ha=total_surface_ha,
            total_interventions=total_interventions,
            recent_interventions=recent_interventions,
            bio_farms=bio_farms,
            avg_parcelles_per_farm=avg_parcelles_per_farm
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve farm overview: {str(e)}"
        )


@router.get("/culture-distribution", response_model=List[CultureDistributionResponse])
async def get_culture_distribution(
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get culture distribution across all accessible farms
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List[CultureDistributionResponse]: Culture distribution data
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
            return []
        
        # Get culture distribution
        culture_query = select(
            Parcelle.culture_code,
            func.count().label('parcelle_count'),
            func.sum(Parcelle.surface_ha).label('total_surface_ha')
        ).where(
            and_(
                Parcelle.siret.in_(accessible_farm_sirets),
                Parcelle.culture_code.isnot(None)
            )
        ).group_by(Parcelle.culture_code).order_by(func.count().desc())
        
        culture_result = await db.execute(culture_query)
        culture_data = culture_result.fetchall()
        
        # Calculate total surface for percentage calculation
        total_surface_query = select(func.coalesce(func.sum(Parcelle.surface_ha), 0)).where(
            Parcelle.siret.in_(accessible_farm_sirets)
        )
        total_surface_result = await db.execute(total_surface_query)
        total_surface = float(total_surface_result.scalar())
        
        return [
            CultureDistributionResponse(
                culture_code=row.culture_code,
                culture_name=None,  # Could be enhanced with culture name lookup
                parcelle_count=row.parcelle_count,
                total_surface_ha=float(row.total_surface_ha),
                percentage=(float(row.total_surface_ha) / total_surface * 100) if total_surface > 0 else 0.0
            )
            for row in culture_data
        ]
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve culture distribution: {str(e)}"
        )


@router.get("/intervention-timeline", response_model=List[InterventionTimelineResponse])
async def get_intervention_timeline(
    days: int = Query(30, ge=1, le=365, description="Number of days to look back"),
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get intervention timeline for the specified number of days
    
    Args:
        days: Number of days to look back
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List[InterventionTimelineResponse]: Intervention timeline data
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
            return []
        
        # Calculate date range
        end_date = date.today()
        start_date = end_date - timedelta(days=days)
        
        # Get intervention timeline
        timeline_query = select(
            Intervention.date_intervention,
            func.count().label('intervention_count'),
            func.sum(Intervention.surface_travaillee_ha).label('total_surface_ha'),
            func.array_agg(Intervention.type_intervention).label('intervention_types')
        ).where(
            and_(
                Intervention.siret.in_(accessible_farm_sirets),
                Intervention.date_intervention >= start_date,
                Intervention.date_intervention <= end_date
            )
        ).group_by(Intervention.date_intervention).order_by(Intervention.date_intervention)
        
        timeline_result = await db.execute(timeline_query)
        timeline_data = timeline_result.fetchall()
        
        # Process intervention types
        processed_timeline = []
        for row in timeline_data:
            # Count intervention types
            type_counts = {}
            for intervention_type in row.intervention_types:
                type_counts[intervention_type] = type_counts.get(intervention_type, 0) + 1
            
            processed_timeline.append(
                InterventionTimelineResponse(
                    date=row.date_intervention,
                    intervention_count=row.intervention_count,
                    total_surface_ha=float(row.total_surface_ha),
                    intervention_types=type_counts
                )
            )
        
        return processed_timeline
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve intervention timeline: {str(e)}"
        )


@router.get("/complete", response_model=FarmDashboardResponse)
async def get_complete_dashboard(
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get complete farm dashboard data
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        FarmDashboardResponse: Complete dashboard data
    """
    try:
        # Get all dashboard components
        overview = await get_farm_overview(current_user, db)
        culture_distribution = await get_culture_distribution(current_user, db)
        recent_interventions = await get_intervention_timeline(30, current_user, db)
        
        # Get farms list
        exploitations_query = select(Exploitation).where(
            Exploitation.siret.in_(
                select(OrganizationFarmAccess.farm_siret).where(
                    OrganizationFarmAccess.organization_id.in_(
                        select(OrganizationMembership.organization_id)
                        .where(OrganizationMembership.user_id == current_user.id)
                    )
                )
            )
        ).order_by(Exploitation.nom)
        
        exploitations_result = await db.execute(exploitations_query)
        exploitations = exploitations_result.scalars().all()
        
        farms = [
            {
                "siret": exploitation.siret,
                "nom": exploitation.nom,
                "surface_totale_ha": float(exploitation.surface_totale_ha),
                "bio": exploitation.bio,
                "type_exploitation": exploitation.type_exploitation
            }
            for exploitation in exploitations
        ]
        
        return FarmDashboardResponse(
            overview=overview,
            culture_distribution=culture_distribution,
            recent_interventions=recent_interventions,
            farms=farms
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve complete dashboard: {str(e)}"
        )
