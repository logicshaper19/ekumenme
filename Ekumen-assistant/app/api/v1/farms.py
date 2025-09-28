"""
Farm Management API endpoints
Handles farm data, parcels, and agricultural information
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import logging

from app.core.database import get_async_db
from app.models.user import User
from app.schemas.farm import FarmCreate, FarmResponse, ParcelCreate, ParcelResponse, FarmUpdate
from app.services.auth_service import AuthService
from app.services.farm_service import FarmService

logger = logging.getLogger(__name__)

router = APIRouter()
auth_service = AuthService()
farm_service = FarmService()

@router.post("/", response_model=FarmResponse, status_code=status.HTTP_201_CREATED)
async def create_farm(
    farm_data: FarmCreate,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Create a new farm
    
    Args:
        farm_data: Farm creation data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        FarmResponse: Created farm information
    """
    try:
        # Check if user can create farms (must be farmer or admin)
        if current_user.role not in ["farmer", "admin"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only farmers and admins can create farms"
            )
        
        # Check if SIRET already exists
        existing_farm = await farm_service.get_farm_by_siret(db, farm_data.siret)
        if existing_farm:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Farm with this SIRET already exists"
            )
        
        # Create farm
        farm = await farm_service.create_farm(
            db=db,
            farm_data=farm_data,
            owner_id=current_user.id
        )
        
        logger.info(f"New farm created: {farm.siret} by user {current_user.email}")
        
        return FarmResponse(
            siret=farm.siret,
            farm_name=farm.farm_name,
            legal_name=farm.legal_name,
            legal_form=farm.legal_form,
            region_code=farm.region_code,
            department_code=farm.department_code,
            commune_insee=farm.commune_insee,
            address=farm.address,
            postal_code=farm.postal_code,
            total_area_ha=farm.total_area_ha,
            utilized_agricultural_area_ha=farm.utilized_agricultural_area_ha,
            organic_certified=farm.organic_certified,
            organic_certification_date=farm.organic_certification_date,
            activity_codes=farm.activity_codes,
            primary_productions=farm.primary_productions,
            created_at=farm.created_at,
            updated_at=farm.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Farm creation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create farm"
        )

@router.get("/", response_model=List[FarmResponse])
async def get_user_farms(
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get farms accessible to the current user
    
    Args:
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List[FarmResponse]: User's accessible farms
    """
    try:
        farms = await farm_service.get_user_farms(db, current_user.id)
        
        return [
            FarmResponse(
                siret=farm.siret,
                farm_name=farm.farm_name,
                legal_name=farm.legal_name,
                legal_form=farm.legal_form,
                region_code=farm.region_code,
                department_code=farm.department_code,
                commune_insee=farm.commune_insee,
                address=farm.address,
                postal_code=farm.postal_code,
                total_area_ha=farm.total_area_ha,
                utilized_agricultural_area_ha=farm.utilized_agricultural_area_ha,
                organic_certified=farm.organic_certified,
                organic_certification_date=farm.organic_certification_date,
                activity_codes=farm.activity_codes,
                primary_productions=farm.primary_productions,
                created_at=farm.created_at,
                updated_at=farm.updated_at
            )
            for farm in farms
        ]
        
    except Exception as e:
        logger.error(f"Get farms error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve farms"
        )

@router.get("/{farm_siret}", response_model=FarmResponse)
async def get_farm(
    farm_siret: str,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get a specific farm by SIRET
    
    Args:
        farm_siret: Farm SIRET identifier
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        FarmResponse: Farm information
    """
    try:
        farm = await farm_service.get_farm_by_siret(db, farm_siret)
        
        if not farm:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Farm not found"
            )
        
        # Check if user has access to this farm
        has_access = await farm_service.user_has_farm_access(db, current_user.id, farm_siret)
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this farm"
            )
        
        return FarmResponse(
            siret=farm.siret,
            farm_name=farm.farm_name,
            legal_name=farm.legal_name,
            legal_form=farm.legal_form,
            region_code=farm.region_code,
            department_code=farm.department_code,
            commune_insee=farm.commune_insee,
            address=farm.address,
            postal_code=farm.postal_code,
            total_area_ha=farm.total_area_ha,
            utilized_agricultural_area_ha=farm.utilized_agricultural_area_ha,
            organic_certified=farm.organic_certified,
            organic_certification_date=farm.organic_certification_date,
            activity_codes=farm.activity_codes,
            primary_productions=farm.primary_productions,
            created_at=farm.created_at,
            updated_at=farm.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get farm error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve farm"
        )

@router.put("/{farm_siret}", response_model=FarmResponse)
async def update_farm(
    farm_siret: str,
    farm_data: FarmUpdate,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Update farm information
    
    Args:
        farm_siret: Farm SIRET identifier
        farm_data: Farm update data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        FarmResponse: Updated farm information
    """
    try:
        farm = await farm_service.get_farm_by_siret(db, farm_siret)
        
        if not farm:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Farm not found"
            )
        
        # Check if user has write access to this farm
        has_access = await farm_service.user_has_farm_access(db, current_user.id, farm_siret)
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this farm"
            )
        
        # Update farm
        updated_farm = await farm_service.update_farm(
            db=db,
            farm=farm,
            farm_data=farm_data
        )
        
        logger.info(f"Farm {farm_siret} updated by user {current_user.email}")
        
        return FarmResponse(
            siret=updated_farm.siret,
            farm_name=updated_farm.farm_name,
            legal_name=updated_farm.legal_name,
            legal_form=updated_farm.legal_form,
            region_code=updated_farm.region_code,
            department_code=updated_farm.department_code,
            commune_insee=updated_farm.commune_insee,
            address=updated_farm.address,
            postal_code=updated_farm.postal_code,
            total_area_ha=updated_farm.total_area_ha,
            utilized_agricultural_area_ha=updated_farm.utilized_agricultural_area_ha,
            organic_certified=updated_farm.organic_certified,
            organic_certification_date=updated_farm.organic_certification_date,
            activity_codes=updated_farm.activity_codes,
            primary_productions=updated_farm.primary_productions,
            created_at=updated_farm.created_at,
            updated_at=updated_farm.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Farm update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update farm"
        )

@router.post("/{farm_siret}/parcels", response_model=ParcelResponse, status_code=status.HTTP_201_CREATED)
async def create_parcel(
    farm_siret: str,
    parcel_data: ParcelCreate,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Create a new parcel for a farm
    
    Args:
        farm_siret: Farm SIRET identifier
        parcel_data: Parcel creation data
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        ParcelResponse: Created parcel information
    """
    try:
        # Verify farm exists and user has access
        farm = await farm_service.get_farm_by_siret(db, farm_siret)
        if not farm:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Farm not found"
            )
        
        has_access = await farm_service.user_has_farm_access(db, current_user.id, farm_siret)
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this farm"
            )
        
        # Create parcel
        parcel = await farm_service.create_parcel(
            db=db,
            farm_siret=farm_siret,
            parcel_data=parcel_data
        )
        
        logger.info(f"New parcel created: {parcel.id} for farm {farm_siret}")
        
        return ParcelResponse(
            id=parcel.id,
            parcel_number=parcel.parcel_number,
            cadastral_reference=parcel.cadastral_reference,
            pac_parcel_id=parcel.pac_parcel_id,
            area_ha=parcel.area_ha,
            current_crop=parcel.current_crop,
            crop_variety=parcel.crop_variety,
            planting_date=parcel.planting_date,
            expected_harvest_date=parcel.expected_harvest_date,
            soil_type=parcel.soil_type,
            ph_level=parcel.ph_level,
            organic_matter_percent=parcel.organic_matter_percent,
            irrigation_available=parcel.irrigation_available,
            drainage_system=parcel.drainage_system,
            slope_percent=parcel.slope_percent,
            exposure=parcel.exposure,
            notes=parcel.notes,
            created_at=parcel.created_at,
            updated_at=parcel.updated_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Parcel creation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create parcel"
        )

@router.get("/{farm_siret}/parcels", response_model=List[ParcelResponse])
async def get_farm_parcels(
    farm_siret: str,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Get all parcels for a farm
    
    Args:
        farm_siret: Farm SIRET identifier
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        List[ParcelResponse]: Farm parcels
    """
    try:
        # Verify farm exists and user has access
        farm = await farm_service.get_farm_by_siret(db, farm_siret)
        if not farm:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Farm not found"
            )
        
        has_access = await farm_service.user_has_farm_access(db, current_user.id, farm_siret)
        if not has_access:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this farm"
            )
        
        parcels = await farm_service.get_farm_parcels(db, farm_siret)
        
        return [
            ParcelResponse(
                id=parcel.id,
                parcel_number=parcel.parcel_number,
                cadastral_reference=parcel.cadastral_reference,
                pac_parcel_id=parcel.pac_parcel_id,
                area_ha=parcel.area_ha,
                current_crop=parcel.current_crop,
                crop_variety=parcel.crop_variety,
                planting_date=parcel.planting_date,
                expected_harvest_date=parcel.expected_harvest_date,
                soil_type=parcel.soil_type,
                ph_level=parcel.ph_level,
                organic_matter_percent=parcel.organic_matter_percent,
                irrigation_available=parcel.irrigation_available,
                drainage_system=parcel.drainage_system,
                slope_percent=parcel.slope_percent,
                exposure=parcel.exposure,
                notes=parcel.notes,
                created_at=parcel.created_at,
                updated_at=parcel.updated_at
            )
            for parcel in parcels
        ]
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get parcels error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve parcels"
        )
