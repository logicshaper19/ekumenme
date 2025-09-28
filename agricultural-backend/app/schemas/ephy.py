"""
Pydantic schemas for EPHY data models.
"""

from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime, date
from decimal import Decimal
from enum import Enum


# Enums
class ProductType(str, Enum):
    PPP = "PPP"
    MFSC = "MFSC"


class CommercialType(str, Enum):
    PRODUIT_REFERENCE = "Produit de référence"
    PRODUIT_REVENTE = "Produit de revente"
    DEUXIEME_GAMME = "Deuxième gamme"


class GammeUsage(str, Enum):
    PROFESSIONNEL = "Professionnel"
    AMATEUR = "Amateur / emploi autorisé dans les jardins"


class EtatAutorisation(str, Enum):
    AUTORISE = "AUTORISE"
    RETIRE = "RETIRE"
    AUTORISE_FR = "Autorisé"
    RETRAIT_FR = "Retrait"


# Base schemas
class ProduitBase(BaseModel):
    nom_produit: str = Field(..., description="Product name")
    type_produit: Optional[ProductType] = Field(None, description="Product type")
    seconds_noms_commerciaux: Optional[str] = Field(None, description="Alternative commercial names")
    type_commercial: Optional[CommercialType] = Field(None, description="Commercial type")
    gamme_usage: Optional[GammeUsage] = Field(None, description="Usage range")
    mentions_autorisees: Optional[str] = Field(None, description="Authorized mentions")
    restrictions_usage: Optional[str] = Field(None, description="Usage restrictions")
    restrictions_usage_libelle: Optional[str] = Field(None, description="Usage restrictions label")
    etat_autorisation: Optional[EtatAutorisation] = Field(None, description="Authorization status")
    date_retrait_produit: Optional[date] = Field(None, description="Product withdrawal date")
    date_premiere_autorisation: Optional[date] = Field(None, description="First authorization date")


class ProduitResponse(ProduitBase):
    numero_amm: str = Field(..., description="AMM number")
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class SubstanceActiveBase(BaseModel):
    nom_substance: str = Field(..., description="Substance name")
    numero_cas: Optional[str] = Field(None, description="CAS number")
    etat_autorisation: Optional[str] = Field(None, description="Authorization status")
    variants: Optional[str] = Field(None, description="Variant names")


class SubstanceActiveResponse(SubstanceActiveBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


class UsageProduitBase(BaseModel):
    identifiant_usage: Optional[str] = Field(None, description="Usage identifier")
    identifiant_usage_lib_court: Optional[str] = Field(None, description="Short usage label")
    culture_commentaire: Optional[str] = Field(None, description="Culture comment")
    dose_min_par_apport: Optional[Decimal] = Field(None, description="Minimum dose per application")
    dose_min_unite: Optional[str] = Field(None, description="Minimum dose unit")
    dose_max_par_apport: Optional[Decimal] = Field(None, description="Maximum dose per application")
    dose_max_unite: Optional[str] = Field(None, description="Maximum dose unit")
    dose_retenue: Optional[Decimal] = Field(None, description="Retained dose")
    dose_retenue_unite: Optional[str] = Field(None, description="Retained dose unit")
    stade_cultural_min_bbch: Optional[int] = Field(None, description="Minimum cultural stage BBCH")
    stade_cultural_max_bbch: Optional[int] = Field(None, description="Maximum cultural stage BBCH")
    etat_usage: Optional[EtatAutorisation] = Field(None, description="Usage status")
    date_decision: Optional[date] = Field(None, description="Decision date")
    delai_avant_recolte_jour: Optional[int] = Field(None, description="Days before harvest")
    nombre_max_application: Optional[int] = Field(None, description="Maximum number of applications")
    condition_emploi: Optional[str] = Field(None, description="Usage conditions")
    znt_aquatique_m: Optional[Decimal] = Field(None, description="Aquatic ZNT in meters")
    znt_arthropodes_non_cibles_m: Optional[Decimal] = Field(None, description="Non-target arthropods ZNT in meters")
    znt_plantes_non_cibles_m: Optional[Decimal] = Field(None, description="Non-target plants ZNT in meters")
    mentions_autorisees_usage: Optional[str] = Field(None, description="Authorized usage mentions")
    intervalle_minimum_entre_applications_jour: Optional[int] = Field(None, description="Minimum interval between applications in days")


class UsageProduitResponse(UsageProduitBase):
    id: int
    numero_amm: str = Field(..., description="AMM number")
    created_at: datetime
    
    class Config:
        from_attributes = True
