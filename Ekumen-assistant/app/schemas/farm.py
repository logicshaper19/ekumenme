"""
Farm schemas for agricultural chatbot
Pydantic models for farm and parcel management
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from app.models.farm import FarmType, FarmStatus


class FarmCreate(BaseModel):
    """Schema for creating a farm"""
    siret: str = Field(..., min_length=14, max_length=14)
    farm_name: str = Field(..., max_length=255)
    legal_name: Optional[str] = Field(None, max_length=255)
    legal_form: Optional[str] = Field(None, max_length=100)
    farm_type: FarmType = FarmType.INDIVIDUAL
    region_code: str = Field(..., max_length=20)
    department_code: Optional[str] = Field(None, max_length=10)
    commune_insee: Optional[str] = Field(None, max_length=10)
    address: Optional[str] = None
    postal_code: Optional[str] = Field(None, max_length=10)
    total_area_ha: Optional[Decimal] = Field(None, ge=0)
    utilized_agricultural_area_ha: Optional[Decimal] = Field(None, ge=0)
    organic_certified: bool = False
    organic_certification_date: Optional[datetime] = None
    organic_certification_body: Optional[str] = Field(None, max_length=255)
    activity_codes: Optional[List[str]] = None
    primary_productions: Optional[List[str]] = None
    secondary_productions: Optional[List[str]] = None
    annual_revenue: Optional[Decimal] = Field(None, ge=0)
    employee_count: Optional[int] = Field(None, ge=0)
    description: Optional[str] = None
    website: Optional[str] = Field(None, max_length=500)
    
    @validator('siret')
    def validate_siret(cls, v):
        if not v.isdigit():
            raise ValueError('SIRET must contain only digits')
        return v


class FarmUpdate(BaseModel):
    """Schema for updating farm information"""
    farm_name: Optional[str] = Field(None, max_length=255)
    legal_name: Optional[str] = Field(None, max_length=255)
    legal_form: Optional[str] = Field(None, max_length=100)
    farm_type: Optional[FarmType] = None
    region_code: Optional[str] = Field(None, max_length=20)
    department_code: Optional[str] = Field(None, max_length=10)
    commune_insee: Optional[str] = Field(None, max_length=10)
    address: Optional[str] = None
    postal_code: Optional[str] = Field(None, max_length=10)
    total_area_ha: Optional[Decimal] = Field(None, ge=0)
    utilized_agricultural_area_ha: Optional[Decimal] = Field(None, ge=0)
    organic_certified: Optional[bool] = None
    organic_certification_date: Optional[datetime] = None
    organic_certification_body: Optional[str] = Field(None, max_length=255)
    activity_codes: Optional[List[str]] = None
    primary_productions: Optional[List[str]] = None
    secondary_productions: Optional[List[str]] = None
    annual_revenue: Optional[Decimal] = Field(None, ge=0)
    employee_count: Optional[int] = Field(None, ge=0)
    description: Optional[str] = None
    website: Optional[str] = Field(None, max_length=500)


class FarmResponse(BaseModel):
    """Schema for farm response"""
    siret: str
    farm_name: str
    legal_name: Optional[str]
    legal_form: Optional[str]
    region_code: str
    department_code: Optional[str]
    commune_insee: Optional[str]
    address: Optional[str]
    postal_code: Optional[str]
    total_area_ha: Optional[Decimal]
    utilized_agricultural_area_ha: Optional[Decimal]
    organic_certified: bool
    organic_certification_date: Optional[datetime]
    activity_codes: Optional[List[str]]
    primary_productions: Optional[List[str]]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ParcelCreate(BaseModel):
    """Schema for creating a parcel"""
    parcel_number: str = Field(..., max_length=50)
    cadastral_reference: Optional[str] = Field(None, max_length=50)
    pac_parcel_id: Optional[str] = Field(None, max_length=50)
    area_ha: Decimal = Field(..., gt=0)
    current_crop: Optional[str] = Field(None, max_length=100)
    crop_variety: Optional[str] = Field(None, max_length=100)
    planting_date: Optional[datetime] = None
    expected_harvest_date: Optional[datetime] = None
    soil_type: Optional[str] = Field(None, max_length=100)
    ph_level: Optional[Decimal] = Field(None, ge=0, le=14)
    organic_matter_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    irrigation_available: bool = False
    drainage_system: bool = False
    slope_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    exposure: Optional[str] = Field(None, max_length=20)
    notes: Optional[str] = None


class ParcelUpdate(BaseModel):
    """Schema for updating parcel information"""
    parcel_number: Optional[str] = Field(None, max_length=50)
    cadastral_reference: Optional[str] = Field(None, max_length=50)
    pac_parcel_id: Optional[str] = Field(None, max_length=50)
    area_ha: Optional[Decimal] = Field(None, gt=0)
    current_crop: Optional[str] = Field(None, max_length=100)
    crop_variety: Optional[str] = Field(None, max_length=100)
    planting_date: Optional[datetime] = None
    expected_harvest_date: Optional[datetime] = None
    soil_type: Optional[str] = Field(None, max_length=100)
    ph_level: Optional[Decimal] = Field(None, ge=0, le=14)
    organic_matter_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    irrigation_available: Optional[bool] = None
    drainage_system: Optional[bool] = None
    slope_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    exposure: Optional[str] = Field(None, max_length=20)
    notes: Optional[str] = None


class ParcelResponse(BaseModel):
    """Schema for parcel response"""
    id: str
    parcel_number: str
    cadastral_reference: Optional[str]
    pac_parcel_id: Optional[str]
    area_ha: Decimal
    current_crop: Optional[str]
    crop_variety: Optional[str]
    planting_date: Optional[datetime]
    expected_harvest_date: Optional[datetime]
    soil_type: Optional[str]
    ph_level: Optional[Decimal]
    organic_matter_percent: Optional[Decimal]
    irrigation_available: bool
    drainage_system: bool
    slope_percent: Optional[Decimal]
    exposure: Optional[str]
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class CropRotationCreate(BaseModel):
    """Schema for creating crop rotation"""
    crop_name: str = Field(..., max_length=100)
    crop_variety: Optional[str] = Field(None, max_length=100)
    crop_family: Optional[str] = Field(None, max_length=50)
    planting_date: datetime
    harvest_date: Optional[datetime] = None
    season: Optional[str] = Field(None, max_length=20)
    yield_quantity: Optional[Decimal] = Field(None, ge=0)
    yield_unit: Optional[str] = Field(None, max_length=20)
    yield_per_hectare: Optional[Decimal] = Field(None, ge=0)
    quality_grade: Optional[str] = Field(None, max_length=20)
    moisture_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    protein_percent: Optional[Decimal] = Field(None, ge=0, le=100)
    notes: Optional[str] = None
    weather_conditions: Optional[str] = None


class CropRotationResponse(BaseModel):
    """Schema for crop rotation response"""
    id: str
    crop_name: str
    crop_variety: Optional[str]
    crop_family: Optional[str]
    planting_date: datetime
    harvest_date: Optional[datetime]
    season: Optional[str]
    yield_quantity: Optional[Decimal]
    yield_unit: Optional[str]
    yield_per_hectare: Optional[Decimal]
    quality_grade: Optional[str]
    moisture_percent: Optional[Decimal]
    protein_percent: Optional[Decimal]
    notes: Optional[str]
    weather_conditions: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class FarmAccessRequest(BaseModel):
    """Schema for farm access request"""
    farm_siret: str = Field(..., min_length=14, max_length=14)
    access_type: str = Field(..., pattern="^(owner|admin|advisor|viewer|readonly)$")
    expires_at: Optional[datetime] = None
    notes: Optional[str] = None
    
    @validator('farm_siret')
    def validate_siret(cls, v):
        if not v.isdigit():
            raise ValueError('SIRET must contain only digits')
        return v


class FarmAccessResponse(BaseModel):
    """Schema for farm access response"""
    id: str
    farm_siret: str
    access_type: str
    granted_at: datetime
    expires_at: Optional[datetime]
    is_active: bool
    
    class Config:
        from_attributes = True
