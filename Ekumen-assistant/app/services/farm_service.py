"""
Farm service for agricultural chatbot
Handles farm and parcel management
"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_

from app.models.farm import Farm, Parcel
from app.schemas.farm import FarmCreate, FarmUpdate, ParcelCreate


class FarmService:
    """Service for managing farms and parcels"""
    
    async def create_farm(
        self,
        db: AsyncSession,
        farm_data: FarmCreate,
        owner_id: str
    ) -> Farm:
        """Create a new farm"""
        farm = Farm(
            siret=farm_data.siret,
            farm_name=farm_data.farm_name,
            legal_name=farm_data.legal_name,
            legal_form=farm_data.legal_form,
            farm_type=farm_data.farm_type,
            region_code=farm_data.region_code,
            department_code=farm_data.department_code,
            commune_insee=farm_data.commune_insee,
            address=farm_data.address,
            postal_code=farm_data.postal_code,
            total_area_ha=farm_data.total_area_ha,
            utilized_agricultural_area_ha=farm_data.utilized_agricultural_area_ha,
            organic_certified=farm_data.organic_certified,
            organic_certification_date=farm_data.organic_certification_date,
            organic_certification_body=farm_data.organic_certification_body,
            activity_codes=farm_data.activity_codes,
            primary_productions=farm_data.primary_productions,
            secondary_productions=farm_data.secondary_productions,
            annual_revenue=farm_data.annual_revenue,
            employee_count=farm_data.employee_count,
            description=farm_data.description,
            website=farm_data.website,
            owner_user_id=owner_id
        )
        
        db.add(farm)
        await db.commit()
        await db.refresh(farm)
        
        return farm
    
    async def get_farm_by_siret(self, db: AsyncSession, siret: str) -> Optional[Farm]:
        """Get farm by SIRET"""
        result = await db.execute(select(Farm).where(Farm.siret == siret))
        return result.scalar_one_or_none()
    
    async def get_user_farms(self, db: AsyncSession, user_id: str) -> List[Farm]:
        """Get farms accessible to a user"""
        # TODO: Implement proper access control based on user roles and permissions
        result = await db.execute(
            select(Farm).where(Farm.owner_user_id == user_id)
        )
        return result.scalars().all()
    
    async def user_has_farm_access(
        self,
        db: AsyncSession,
        user_id: str,
        farm_siret: str
    ) -> bool:
        """Check if user has access to a farm"""
        # TODO: Implement proper access control
        # For now, check if user is the owner
        farm = await self.get_farm_by_siret(db, farm_siret)
        if farm and farm.owner_user_id == user_id:
            return True
        
        # TODO: Check organization memberships and other access types
        return False
    
    async def update_farm(
        self,
        db: AsyncSession,
        farm: Farm,
        farm_data: FarmUpdate
    ) -> Farm:
        """Update farm information"""
        update_data = farm_data.dict(exclude_unset=True)
        
        for field, value in update_data.items():
            if hasattr(farm, field):
                setattr(farm, field, value)
        
        await db.commit()
        await db.refresh(farm)
        
        return farm
    
    async def create_parcel(
        self,
        db: AsyncSession,
        farm_siret: str,
        parcel_data: ParcelCreate
    ) -> Parcel:
        """Create a new parcel"""
        parcel = Parcel(
            farm_siret=farm_siret,
            parcel_number=parcel_data.parcel_number,
            cadastral_reference=parcel_data.cadastral_reference,
            pac_parcel_id=parcel_data.pac_parcel_id,
            area_ha=parcel_data.area_ha,
            current_crop=parcel_data.current_crop,
            crop_variety=parcel_data.crop_variety,
            planting_date=parcel_data.planting_date,
            expected_harvest_date=parcel_data.expected_harvest_date,
            soil_type=parcel_data.soil_type,
            ph_level=parcel_data.ph_level,
            organic_matter_percent=parcel_data.organic_matter_percent,
            irrigation_available=parcel_data.irrigation_available,
            drainage_system=parcel_data.drainage_system,
            slope_percent=parcel_data.slope_percent,
            exposure=parcel_data.exposure,
            notes=parcel_data.notes
        )
        
        db.add(parcel)
        await db.commit()
        await db.refresh(parcel)
        
        return parcel
    
    async def get_farm_parcels(self, db: AsyncSession, farm_siret: str) -> List[Parcel]:
        """Get all parcels for a farm"""
        result = await db.execute(
            select(Parcel).where(Parcel.farm_siret == farm_siret)
        )
        return result.scalars().all()
    
    async def get_parcel_by_id(self, db: AsyncSession, parcel_id: str) -> Optional[Parcel]:
        """Get parcel by ID"""
        result = await db.execute(select(Parcel).where(Parcel.id == parcel_id))
        return result.scalar_one_or_none()
    
    async def update_parcel(
        self,
        db: AsyncSession,
        parcel: Parcel,
        update_data: dict
    ) -> Parcel:
        """Update parcel information"""
        for field, value in update_data.items():
            if hasattr(parcel, field):
                setattr(parcel, field, value)
        
        await db.commit()
        await db.refresh(parcel)
        
        return parcel
    
    async def delete_parcel(
        self,
        db: AsyncSession,
        parcel_id: str
    ) -> bool:
        """Delete a parcel"""
        parcel = await self.get_parcel_by_id(db, parcel_id)
        if parcel:
            await db.delete(parcel)
            await db.commit()
            return True
        return False
    
    async def get_farm_statistics(self, db: AsyncSession, farm_siret: str) -> dict:
        """Get farm statistics"""
        farm = await self.get_farm_by_siret(db, farm_siret)
        if not farm:
            return {}
        
        parcels = await self.get_farm_parcels(db, farm_siret)
        
        total_parcel_area = sum(parcel.area_ha for parcel in parcels)
        crop_types = list(set(parcel.current_crop for parcel in parcels if parcel.current_crop))
        
        return {
            "farm_name": farm.farm_name,
            "total_area_ha": farm.total_area_ha,
            "utilized_agricultural_area_ha": farm.utilized_agricultural_area_ha,
            "parcel_count": len(parcels),
            "total_parcel_area_ha": total_parcel_area,
            "crop_types": crop_types,
            "organic_certified": farm.organic_certified,
            "region_code": farm.region_code
        }
