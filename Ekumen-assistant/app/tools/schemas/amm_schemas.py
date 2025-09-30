"""
Pydantic schemas for AMM (Autorisation de Mise sur le Marché) lookup tool
Type-safe input/output for regulatory product searches
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


class ProductType(str, Enum):
    """Type de produit phytosanitaire"""
    PPP = "PPP"  # Produit de Protection des Plantes
    MFSC = "MFSC"  # Matière Fertilisante et Support de Culture
    ALL = "ALL"  # Tous types


class ComplianceStatus(str, Enum):
    """Statut de conformité du produit"""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    WARNING = "warning"
    UNKNOWN = "unknown"


class AMMInput(BaseModel):
    """Input schema for AMM lookup"""
    
    product_name: Optional[str] = Field(
        default=None,
        description="Nom du produit à rechercher (ex: 'Roundup', 'Glyphosate 360')"
    )
    
    active_ingredient: Optional[str] = Field(
        default=None,
        description="Substance active à rechercher (ex: 'glyphosate', 'métribuzine')"
    )
    
    product_type: Optional[ProductType] = Field(
        default=None,
        description="Type de produit: PPP (phyto), MFSC (fertilisant), ou ALL"
    )
    
    crop_type: Optional[str] = Field(
        default=None,
        description="Type de culture cible (ex: 'blé', 'maïs', 'colza')"
    )
    
    farm_context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Contexte exploitation: region, distance_to_water_m, organic_certified, etc."
    )
    
    @field_validator('product_name', 'active_ingredient', 'crop_type')
    @classmethod
    def validate_strings(cls, v: Optional[str]) -> Optional[str]:
        """Validate and clean string inputs"""
        if v is None:
            return None
        v = v.strip()
        return v if v else None
    
    @field_validator('farm_context')
    @classmethod
    def validate_farm_context(cls, v: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Validate farm context structure"""
        if v is None:
            return None
        
        # Validate known fields
        if 'distance_to_water_m' in v:
            if not isinstance(v['distance_to_water_m'], (int, float)) or v['distance_to_water_m'] < 0:
                raise ValueError("distance_to_water_m must be a non-negative number")
        
        if 'organic_certified' in v:
            if not isinstance(v['organic_certified'], bool):
                raise ValueError("organic_certified must be a boolean")
        
        return v
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "product_name": "Roundup",
                    "crop_type": "blé",
                    "farm_context": {
                        "region": "Hauts-de-France",
                        "distance_to_water_m": 25,
                        "organic_certified": False
                    }
                },
                {
                    "active_ingredient": "glyphosate",
                    "product_type": "PPP",
                    "crop_type": "maïs"
                }
            ]
        }


class SubstanceInfo(BaseModel):
    """Information sur une substance active"""
    nom: str = Field(description="Nom de la substance active")
    concentration: str = Field(description="Concentration (ex: '360 g/L')")


class ProductInfo(BaseModel):
    """Information détaillée sur un produit"""
    numero_amm: str = Field(description="Numéro AMM unique")
    nom_produit: str = Field(description="Nom commercial du produit")
    type_produit: str = Field(description="Type: PPP ou MFSC")
    titulaire: str = Field(description="Titulaire de l'AMM")
    etat_autorisation: str = Field(description="État: AUTORISE, RETIRE, etc.")
    substances_actives: List[SubstanceInfo] = Field(description="Substances actives")
    compliance_score: float = Field(description="Score de conformité (0-100)")
    status: ComplianceStatus = Field(description="Statut de conformité")
    
    # Compliant products only
    usage_recommendations: Optional[List[str]] = Field(
        default=None,
        description="Recommandations d'usage"
    )
    safety_intervals: Optional[Dict[str, int]] = Field(
        default=None,
        description="Délais de sécurité (jours)"
    )
    znt_requirements: Optional[Dict[str, float]] = Field(
        default=None,
        description="Zones Non Traitées requises (mètres)"
    )
    environmental_considerations: Optional[List[str]] = Field(
        default=None,
        description="Considérations environnementales"
    )
    
    # Non-compliant products only
    violations: Optional[List[str]] = Field(
        default=None,
        description="Violations réglementaires"
    )
    warnings: Optional[List[str]] = Field(
        default=None,
        description="Avertissements"
    )
    non_compliance_reasons: Optional[List[str]] = Field(
        default=None,
        description="Raisons de non-conformité"
    )


class SearchSummary(BaseModel):
    """Résumé de la recherche"""
    total_products_found: int = Field(description="Nombre total de produits trouvés")
    compliant_products: int = Field(description="Nombre de produits conformes")
    non_compliant_products: int = Field(description="Nombre de produits non conformes")
    search_context: Dict[str, Any] = Field(description="Contexte de recherche")


class RegulatoryContext(BaseModel):
    """Contexte réglementaire"""
    znt_requirements: Dict[str, Any] = Field(description="Exigences ZNT")
    seasonal_considerations: Dict[str, Any] = Field(description="Considérations saisonnières")
    regional_factors: Dict[str, Any] = Field(description="Facteurs régionaux")


class AMMOutput(BaseModel):
    """Output schema for AMM lookup"""
    
    success: bool = Field(description="Recherche réussie")
    status: str = Field(description="success, no_results, ou error")
    
    # Success fields
    summary: Optional[SearchSummary] = Field(
        default=None,
        description="Résumé de la recherche"
    )
    compliant_products: Optional[List[ProductInfo]] = Field(
        default=None,
        description="Produits conformes (max 5)"
    )
    non_compliant_products: Optional[List[ProductInfo]] = Field(
        default=None,
        description="Produits non conformes (max 3)"
    )
    general_recommendations: Optional[List[str]] = Field(
        default=None,
        description="Recommandations générales"
    )
    regulatory_context: Optional[RegulatoryContext] = Field(
        default=None,
        description="Contexte réglementaire"
    )
    
    # No results fields
    search_criteria: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Critères de recherche utilisés"
    )
    recommendations: Optional[List[str]] = Field(
        default=None,
        description="Recommandations pour améliorer la recherche"
    )
    
    # Error fields
    error: Optional[str] = Field(
        default=None,
        description="Message d'erreur si échec"
    )
    error_type: Optional[str] = Field(
        default=None,
        description="Type d'erreur: validation, database, api_error, timeout, unknown"
    )
    
    # Common fields
    legal_disclaimer: str = Field(
        description="Avertissement légal obligatoire"
    )
    data_source: str = Field(
        default="EPHY_DATABASE_OFFICIAL",
        description="Source des données"
    )
    configuration_version: Optional[str] = Field(
        default=None,
        description="Version de la configuration réglementaire"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="Horodatage de la recherche"
    )
    
    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "success": True,
                    "status": "success",
                    "summary": {
                        "total_products_found": 8,
                        "compliant_products": 5,
                        "non_compliant_products": 3,
                        "search_context": {
                            "crop_type": "blé",
                            "farm_context_provided": True
                        }
                    },
                    "compliant_products": [
                        {
                            "numero_amm": "2020001",
                            "nom_produit": "Roundup Flex",
                            "type_produit": "PPP",
                            "titulaire": "Bayer",
                            "etat_autorisation": "AUTORISE",
                            "substances_actives": [
                                {"nom": "glyphosate", "concentration": "360 g/L"}
                            ],
                            "compliance_score": 95.5,
                            "status": "compliant",
                            "usage_recommendations": [
                                "Respecter les doses homologuées",
                                "Éviter les périodes de vent"
                            ],
                            "safety_intervals": {"pre_harvest_days": 14},
                            "znt_requirements": {"cours_eau": 5.0},
                            "environmental_considerations": [
                                "Protéger les abeilles",
                                "Respecter les ZNT"
                            ]
                        }
                    ],
                    "general_recommendations": [
                        "Vérifiez toujours l'étiquette",
                        "Consultez les conditions météo"
                    ],
                    "legal_disclaimer": "Consultez toujours un conseiller agricole",
                    "data_source": "EPHY_DATABASE_OFFICIAL",
                    "timestamp": "2025-09-30T18:00:00"
                }
            ]
        }

