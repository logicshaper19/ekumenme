"""
Product schemas for agricultural chatbot
Pydantic models for French agricultural product database
"""

from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Any
from datetime import datetime
from decimal import Decimal
from app.models.product import ProductType, AuthorizationStatus, UsageStatus


class ProductSearchRequest(BaseModel):
    """Schema for product search request"""
    search_term: Optional[str] = Field(None, max_length=200)
    product_type: Optional[ProductType] = None
    crop_filter: Optional[str] = Field(None, max_length=100)
    limit: int = Field(default=50, ge=1, le=1000)
    offset: int = Field(default=0, ge=0)


class SubstanceResponse(BaseModel):
    """Schema for active substance response"""
    id: int
    nom_substance: str
    numero_cas: Optional[str]
    etat_autorisation: AuthorizationStatus
    variants: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ProductSubstanceResponse(BaseModel):
    """Schema for product-substance relationship response"""
    id: int
    concentration_value: Optional[Decimal]
    concentration_unit: Optional[str]
    fonction: Optional[str]
    substance: SubstanceResponse
    
    class Config:
        from_attributes = True


class UsageResponse(BaseModel):
    """Schema for product usage response"""
    id: int
    identifiant_usage: Optional[str]
    identifiant_usage_lib_court: Optional[str]
    type_culture_libelle: Optional[str]
    culture_commentaire: Optional[str]
    stade_cultural_min_bbch: Optional[int]
    stade_cultural_max_bbch: Optional[int]
    dose_min_par_apport: Optional[Decimal]
    dose_max_par_apport: Optional[Decimal]
    dose_retenue: Optional[Decimal]
    dose_unite: Optional[str]
    nombre_max_application: Optional[int]
    delai_avant_recolte_jour: Optional[int]
    delai_avant_recolte_bbch: Optional[int]
    intervalle_minimum_applications_jour: Optional[int]
    etat_usage: UsageStatus
    date_decision: Optional[datetime]
    date_fin_distribution: Optional[datetime]
    date_fin_utilisation: Optional[datetime]
    saison_application_min: Optional[str]
    saison_application_max: Optional[str]
    saison_application_min_commentaire: Optional[str]
    saison_application_max_commentaire: Optional[str]
    condition_emploi: Optional[str]
    mentions_autorisees: Optional[str]
    restrictions_usage: Optional[str]
    restrictions_usage_libelle: Optional[str]
    znt_aquatique_m: Optional[int]
    znt_arthropodes_non_cibles_m: Optional[int]
    znt_plantes_non_cibles_m: Optional[int]
    
    class Config:
        from_attributes = True


class ConditionEmploiResponse(BaseModel):
    """Schema for employment condition response"""
    id: int
    categorie_condition: Optional[str]
    condition_emploi_libelle: str
    
    class Config:
        from_attributes = True


class ClassificationDangerResponse(BaseModel):
    """Schema for danger classification response"""
    id: int
    libelle_court: str
    libelle_long: str
    type_classification: Optional[str]
    
    class Config:
        from_attributes = True


class PhraseRisqueResponse(BaseModel):
    """Schema for risk phrase response"""
    id: int
    code_phrase: str
    libelle_court_phrase: Optional[str]
    libelle_long_phrase: Optional[str]
    type_phrase: Optional[str]
    
    class Config:
        from_attributes = True


class ProductResponse(BaseModel):
    """Schema for product response"""
    id: int
    type_produit: ProductType
    numero_amm: str
    nom_produit: str
    seconds_noms_commerciaux: Optional[str]
    titulaire: Optional[str]
    type_commercial: Optional[str]
    gamme_usage: Optional[str]
    etat_autorisation: AuthorizationStatus
    date_retrait_produit: Optional[datetime]
    date_premiere_autorisation: Optional[datetime]
    num_amm_reference: Optional[str]
    nom_produit_reference: Optional[str]
    composition: Optional[str]
    revendication: Optional[str]
    denomination_classe: Optional[str]
    formulations: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    # Related data
    substances: Optional[List[ProductSubstanceResponse]] = None
    usages: Optional[List[UsageResponse]] = None
    conditions_emploi: Optional[List[ConditionEmploiResponse]] = None
    classifications_danger: Optional[List[ClassificationDangerResponse]] = None
    phrases_risque: Optional[List[PhraseRisqueResponse]] = None
    
    class Config:
        from_attributes = True


class ProductUsageResponse(BaseModel):
    """Schema for product usage validation response"""
    valid: bool
    error: Optional[str] = None
    usage: Optional[Dict[str, Any]] = None


class ProductCompatibilityResponse(BaseModel):
    """Schema for product compatibility response"""
    compatible: bool
    conflict_reason: str
    common_substances: Optional[str] = None


class ProductStatisticsResponse(BaseModel):
    """Schema for product statistics response"""
    total_products: int
    authorized_products: int
    mfsc_products: int
    ppp_products: int
    total_substances: int
    total_usages: int
    authorization_rate: float


class CropStatisticsResponse(BaseModel):
    """Schema for crop statistics response"""
    crop: str
    nb_products: int
    nb_usages: int
    products: str


class SubstanceStatisticsResponse(BaseModel):
    """Schema for substance statistics response"""
    fonction: str
    nom_substance: str
    numero_cas: Optional[str]
    nb_products: int
    products: str


class ProductCreate(BaseModel):
    """Schema for creating a new product"""
    type_produit: ProductType
    numero_amm: str = Field(..., min_length=1, max_length=20)
    nom_produit: str = Field(..., min_length=1, max_length=200)
    seconds_noms_commerciaux: Optional[str] = None
    titulaire: Optional[str] = Field(None, max_length=200)
    type_commercial: Optional[str] = Field(None, max_length=50)
    gamme_usage: Optional[str] = Field(None, max_length=50)
    etat_autorisation: AuthorizationStatus = AuthorizationStatus.AUTORISE
    date_retrait_produit: Optional[datetime] = None
    date_premiere_autorisation: Optional[datetime] = None
    num_amm_reference: Optional[str] = Field(None, max_length=20)
    nom_produit_reference: Optional[str] = Field(None, max_length=200)
    composition: Optional[str] = None
    revendication: Optional[str] = None
    denomination_classe: Optional[str] = Field(None, max_length=100)
    formulations: Optional[str] = Field(None, max_length=100)
    
    @validator('numero_amm')
    def validate_numero_amm(cls, v):
        if not v.strip():
            raise ValueError('Numéro AMM ne peut pas être vide')
        return v.strip()
    
    @validator('nom_produit')
    def validate_nom_produit(cls, v):
        if not v.strip():
            raise ValueError('Nom du produit ne peut pas être vide')
        return v.strip()


class SubstanceCreate(BaseModel):
    """Schema for creating a new active substance"""
    nom_substance: str = Field(..., min_length=1, max_length=200)
    numero_cas: Optional[str] = Field(None, max_length=20)
    etat_autorisation: AuthorizationStatus = AuthorizationStatus.AUTORISE
    variants: Optional[str] = None
    
    @validator('nom_substance')
    def validate_nom_substance(cls, v):
        if not v.strip():
            raise ValueError('Nom de la substance ne peut pas être vide')
        return v.strip()


class UsageCreate(BaseModel):
    """Schema for creating a new usage"""
    product_id: int
    identifiant_usage: Optional[str] = Field(None, max_length=50)
    identifiant_usage_lib_court: Optional[str] = Field(None, max_length=200)
    type_culture_libelle: Optional[str] = Field(None, max_length=100)
    culture_commentaire: Optional[str] = None
    stade_cultural_min_bbch: Optional[int] = Field(None, ge=0, le=99)
    stade_cultural_max_bbch: Optional[int] = Field(None, ge=0, le=99)
    dose_min_par_apport: Optional[Decimal] = Field(None, ge=0)
    dose_max_par_apport: Optional[Decimal] = Field(None, ge=0)
    dose_retenue: Optional[Decimal] = Field(None, ge=0)
    dose_unite: Optional[str] = Field(None, max_length=20)
    nombre_max_application: Optional[int] = Field(None, ge=0)
    delai_avant_recolte_jour: Optional[int] = Field(None, ge=0)
    delai_avant_recolte_bbch: Optional[int] = Field(None, ge=0, le=99)
    intervalle_minimum_applications_jour: Optional[int] = Field(None, ge=0)
    etat_usage: UsageStatus = UsageStatus.AUTORISE
    date_decision: Optional[datetime] = None
    date_fin_distribution: Optional[datetime] = None
    date_fin_utilisation: Optional[datetime] = None
    saison_application_min: Optional[str] = Field(None, max_length=50)
    saison_application_max: Optional[str] = Field(None, max_length=50)
    saison_application_min_commentaire: Optional[str] = None
    saison_application_max_commentaire: Optional[str] = None
    condition_emploi: Optional[str] = None
    mentions_autorisees: Optional[str] = None
    restrictions_usage: Optional[str] = None
    restrictions_usage_libelle: Optional[str] = None
    znt_aquatique_m: Optional[int] = Field(None, ge=0)
    znt_arthropodes_non_cibles_m: Optional[int] = Field(None, ge=0)
    znt_plantes_non_cibles_m: Optional[int] = Field(None, ge=0)


class ProductValidationRequest(BaseModel):
    """Schema for product usage validation request"""
    numero_amm: str = Field(..., min_length=1, max_length=20)
    crop_name: str = Field(..., min_length=1, max_length=100)
    dose: float = Field(..., gt=0)
    unit: str = Field(..., min_length=1, max_length=20)
    
    @validator('numero_amm')
    def validate_numero_amm(cls, v):
        if not v.strip():
            raise ValueError('Numéro AMM ne peut pas être vide')
        return v.strip()
    
    @validator('crop_name')
    def validate_crop_name(cls, v):
        if not v.strip():
            raise ValueError('Nom de la culture ne peut pas être vide')
        return v.strip()
    
    @validator('unit')
    def validate_unit(cls, v):
        if not v.strip():
            raise ValueError('Unité ne peut pas être vide')
        return v.strip()


class ProductCompatibilityRequest(BaseModel):
    """Schema for product compatibility check request"""
    product1_amm: str = Field(..., min_length=1, max_length=20)
    product2_amm: str = Field(..., min_length=1, max_length=20)
    
    @validator('product1_amm', 'product2_amm')
    def validate_amm(cls, v):
        if not v.strip():
            raise ValueError('Numéro AMM ne peut pas être vide')
        return v.strip()
    
    @validator('product2_amm')
    def validate_different_products(cls, v, values):
        if 'product1_amm' in values and v == values['product1_amm']:
            raise ValueError('Les deux produits doivent être différents')
        return v
