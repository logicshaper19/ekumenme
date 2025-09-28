"""
Pydantic schemas for MesParcelles data models.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, date
from decimal import Decimal
import uuid


# Base schemas
class ExploitationBase(BaseModel):
    siret: str = Field(..., description="SIRET number of the exploitation")


class ExploitationCreate(ExploitationBase):
    pass


class ExploitationResponse(ExploitationBase):
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ServiceActivationBase(BaseModel):
    millesime_active: List[int] = Field(..., description="Active years")
    millesime_deja_actif: List[int] = Field(..., description="Previously active years")


class ServiceActivationResponse(ServiceActivationBase):
    id: int
    siret: str
    last_updated: datetime
    
    class Config:
        from_attributes = True


# Parcelle schemas
class ParcelleBase(BaseModel):
    siret_exploitation: str = Field(..., description="SIRET of the exploitation")
    millesime: int = Field(..., description="Year")
    nom: Optional[str] = Field(None, description="Parcel name")
    surface_mesuree_ha: Optional[Decimal] = Field(None, description="Measured surface in hectares")
    insee_commune: Optional[str] = Field(None, description="INSEE commune code")
    geometrie_vide: bool = Field(False, description="Empty geometry flag")
    uuid_parcelle_millesime_precedent: Optional[uuid.UUID] = Field(None, description="Previous year parcel UUID")


class ParcelleCreate(ParcelleBase):
    pass


class ParcelleResponse(ParcelleBase):
    uuid_parcelle: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Culture schemas
class CultureBase(BaseModel):
    libelle: str = Field(..., description="Culture label")


class CultureResponse(CultureBase):
    id_culture: int
    
    class Config:
        from_attributes = True


# Intervention schemas
class InterventionBase(BaseModel):
    numero_lot: Optional[int] = Field(None, description="Lot number")
    siret_exploitation: str = Field(..., description="SIRET of the exploitation")
    uuid_parcelle: uuid.UUID = Field(..., description="Parcel UUID")
    id_culture: int = Field(..., description="Culture ID")
    surface_travaillee_ha: Optional[Decimal] = Field(None, description="Worked surface in hectares")
    date_debut: date = Field(..., description="Start date")
    date_fin: date = Field(..., description="End date")
    id_type_intervention: int = Field(..., description="Intervention type ID")


class InterventionCreate(InterventionBase):
    pass


class InterventionResponse(InterventionBase):
    uuid_intervention: uuid.UUID
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Intrant schemas
class IntrantBase(BaseModel):
    libelle: str = Field(..., description="Intrant label")
    type_intrant_id: int = Field(..., description="Intrant type ID")
    numero_amm_ephy: Optional[str] = Field(None, description="EPHY AMM number")


class IntrantCreate(IntrantBase):
    pass


class IntrantResponse(IntrantBase):
    id_intrant: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


# Intervention Intrant schemas
class InterventionIntrantBase(BaseModel):
    uuid_intervention: uuid.UUID = Field(..., description="Intervention UUID")
    id_intrant: int = Field(..., description="Intrant ID")
    quantite_totale: Decimal = Field(..., description="Total quantity")
    unite_intrant_intervention: str = Field(..., description="Unit of measurement")


class InterventionIntrantCreate(InterventionIntrantBase):
    pass


class InterventionIntrantResponse(InterventionIntrantBase):
    id: int
    
    class Config:
        from_attributes = True


# Compliance schemas
class ValidationInterventionBase(BaseModel):
    uuid_intervention: uuid.UUID = Field(..., description="Intervention UUID")
    numero_amm_ephy: Optional[str] = Field(None, description="EPHY AMM number")
    usage_autorise: Optional[bool] = Field(None, description="Authorized usage")
    dose_conforme: Optional[bool] = Field(None, description="Dose compliance")
    delai_avant_recolte_respecte: Optional[bool] = Field(None, description="Harvest delay compliance")
    znt_respectees: Optional[bool] = Field(None, description="ZNT compliance")
    commentaires: Optional[str] = Field(None, description="Comments")


class ValidationInterventionCreate(ValidationInterventionBase):
    pass


class ValidationInterventionResponse(ValidationInterventionBase):
    id: int
    date_validation: datetime
    
    class Config:
        from_attributes = True


# Conformity schemas
class ConformiteReglementaireBase(BaseModel):
    siret_exploitation: str = Field(..., description="SIRET of the exploitation")
    annee: int = Field(..., description="Year")
    interventions_controlees: int = Field(0, description="Number of controlled interventions")
    interventions_conformes: int = Field(0, description="Number of compliant interventions")
    commentaires: Optional[str] = Field(None, description="Comments")


class ConformiteReglementaireCreate(ConformiteReglementaireBase):
    pass


class ConformiteReglementaireResponse(ConformiteReglementaireBase):
    id: int
    taux_conformite: Optional[Decimal] = Field(None, description="Compliance rate")
    derniere_verification: datetime
    
    class Config:
        from_attributes = True
