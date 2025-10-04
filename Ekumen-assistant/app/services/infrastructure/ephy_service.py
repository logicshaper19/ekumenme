"""
EPHY Service - Real-time Product Validation
Integrates with EPHY database for approved product validation
"""

from typing import Dict, List, Optional, Any, Tuple
import logging
from datetime import date, datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import selectinload

from app.models.ephy import (
    Produit, SubstanceActive, ProduitSubstance, UsageProduit,
    EtatAutorisation, ProductType, Titulaire, ProduitFonction,
    Fonction, ProduitFormulation, Formulation, ConditionEmploi
)
from app.core.database import get_async_db

logger = logging.getLogger(__name__)


class EphyService:
    """Service for EPHY database integration and product validation"""
    
    def __init__(self):
        self.cache = {}  # Simple in-memory cache for frequently accessed products
        self.cache_ttl = 3600  # 1 hour cache TTL
    
    async def get_product_by_amm(self, amm_code: str, db: AsyncSession = None) -> Optional[Dict[str, Any]]:
        """Get product information by AMM code"""
        try:
            # Check cache first
            cache_key = f"product_{amm_code}"
            if cache_key in self.cache:
                cached_data, timestamp = self.cache[cache_key]
                if (datetime.now() - timestamp).seconds < self.cache_ttl:
                    return cached_data
            
            if not db:
                async for db_session in get_async_db():
                    db = db_session
                    break
            
            # Query product with all related data
            query = select(Produit).options(
                selectinload(Produit.titulaire),
                selectinload(Produit.produit_substances).selectinload(ProduitSubstance.substance),
                selectinload(Produit.produit_fonctions).selectinload(ProduitFonction.fonction),
                selectinload(Produit.produit_formulations).selectinload(ProduitFormulation.formulation),
                selectinload(Produit.usages),
                selectinload(Produit.conditions_emploi)
            ).where(Produit.numero_amm == amm_code)
            
            result = await db.execute(query)
            product = result.scalar_one_or_none()
            
            if not product:
                return None
            
            # Build comprehensive product info
            product_info = await self._build_product_info(product)
            
            # Cache the result
            self.cache[cache_key] = (product_info, datetime.now())
            
            return product_info
            
        except Exception as e:
            logger.error(f"Error getting product by AMM {amm_code}: {e}")
            return None
    
    async def search_products(
        self, 
        product_name: str = None,
        active_ingredient: str = None,
        product_type: str = None,
        crop_type: str = None,
        limit: int = 20,
        db: AsyncSession = None
    ) -> List[Dict[str, Any]]:
        """Search products with multiple criteria"""
        try:
            if not db:
                async for db_session in get_async_db():
                    db = db_session
                    break
            
            # Build query
            query = select(Produit).options(
                selectinload(Produit.titulaire),
                selectinload(Produit.produit_substances).selectinload(ProduitSubstance.substance),
                selectinload(Produit.usages)
            ).where(Produit.etat_autorisation == EtatAutorisation.AUTORISE)
            
            # Add filters
            if product_name:
                query = query.where(
                    or_(
                        Produit.nom_produit.ilike(f"%{product_name}%"),
                        Produit.seconds_noms_commerciaux.ilike(f"%{product_name}%")
                    )
                )
            
            if product_type:
                try:
                    prod_type = ProductType(product_type.upper())
                    query = query.where(Produit.type_produit == prod_type)
                except ValueError:
                    logger.warning(f"Invalid product type: {product_type}")
            
            if active_ingredient:
                query = query.join(ProduitSubstance).join(SubstanceActive).where(
                    SubstanceActive.nom_substance.ilike(f"%{active_ingredient}%")
                )
            
            if crop_type:
                query = query.join(UsageProduit).where(
                    UsageProduit.type_culture_libelle.ilike(f"%{crop_type}%")
                )
            
            query = query.limit(limit)
            
            result = await db.execute(query)
            products = result.scalars().all()
            
            # Build product info for each result
            product_infos = []
            for product in products:
                product_info = await self._build_product_info(product)
                product_infos.append(product_info)
            
            return product_infos
            
        except Exception as e:
            logger.error(f"Error searching products: {e}")
            return []
    
    async def validate_product_usage(
        self, 
        amm_code: str, 
        crop_type: str, 
        application_date: date,
        dose_per_ha: float,
        db: AsyncSession = None
    ) -> Dict[str, Any]:
        """Validate product usage for specific crop and conditions"""
        try:
            product_info = await self.get_product_by_amm(amm_code, db)
            if not product_info:
                return {
                    "is_valid": False,
                    "errors": [f"Produit avec AMM {amm_code} non trouvé"],
                    "warnings": []
                }
            
            # Check if product is authorized
            if product_info["etat_autorisation"] != "AUTORISE":
                return {
                    "is_valid": False,
                    "errors": [f"Produit {product_info['nom_produit']} n'est plus autorisé"],
                    "warnings": []
                }
            
            # Find relevant usage conditions
            relevant_usages = []
            for usage in product_info.get("usages", []):
                if crop_type.lower() in usage.get("type_culture_libelle", "").lower():
                    relevant_usages.append(usage)
            
            if not relevant_usages:
                return {
                    "is_valid": False,
                    "errors": [f"Produit {product_info['nom_produit']} non autorisé pour {crop_type}"],
                    "warnings": []
                }
            
            # Validate against usage conditions
            errors = []
            warnings = []
            
            for usage in relevant_usages:
                # Check dose limits
                dose_min = usage.get("dose_min_par_apport")
                dose_max = usage.get("dose_max_par_apport")
                
                if dose_min and dose_per_ha < dose_min:
                    errors.append(f"Dose trop faible: {dose_per_ha} < {dose_min} {usage.get('dose_min_par_apport_unite', '')}")
                
                if dose_max and dose_per_ha > dose_max:
                    errors.append(f"Dose trop élevée: {dose_per_ha} > {dose_max} {usage.get('dose_max_par_apport_unite', '')}")
                
                # Check application season
                season_min = usage.get("saison_application_min")
                season_max = usage.get("saison_application_max")
                
                if season_min and season_max:
                    # This would need more sophisticated season checking
                    pass
                
                # Check pre-harvest interval
                dar = usage.get("delai_avant_recolte_jour")
                if dar:
                    warnings.append(f"Délai avant récolte: {dar} jours")
                
                # Check ZNT (buffer zones)
                znt_aquatique = usage.get("znt_aquatique_m")
                if znt_aquatique:
                    warnings.append(f"ZNT aquatique: {znt_aquatique}m")
            
            return {
                "is_valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
                "product_info": product_info,
                "relevant_usages": relevant_usages
            }
            
        except Exception as e:
            logger.error(f"Error validating product usage: {e}")
            return {
                "is_valid": False,
                "errors": [f"Erreur de validation: {str(e)}"],
                "warnings": []
            }
    
    async def get_approved_products_for_crop(
        self, 
        crop_type: str, 
        product_type: str = None,
        limit: int = 50,
        db: AsyncSession = None
    ) -> List[Dict[str, Any]]:
        """Get all approved products for a specific crop"""
        try:
            if not db:
                async for db_session in get_async_db():
                    db = db_session
                    break
            
            query = select(Produit).options(
                selectinload(Produit.titulaire),
                selectinload(Produit.usages)
            ).join(UsageProduit).where(
                and_(
                    Produit.etat_autorisation == EtatAutorisation.AUTORISE,
                    UsageProduit.type_culture_libelle.ilike(f"%{crop_type}%"),
                    UsageProduit.etat_usage == "Autorisé"
                )
            )
            
            if product_type:
                try:
                    prod_type = ProductType(product_type.upper())
                    query = query.where(Produit.type_produit == prod_type)
                except ValueError:
                    pass
            
            query = query.limit(limit)
            
            result = await db.execute(query)
            products = result.scalars().all()
            
            # Build simplified product info
            product_list = []
            for product in products:
                product_list.append({
                    "numero_amm": product.numero_amm,
                    "nom_produit": product.nom_produit,
                    "type_produit": product.type_produit.value if product.type_produit else None,
                    "titulaire": product.titulaire.nom if product.titulaire else None,
                    "usages_count": len(product.usages)
                })
            
            return product_list
            
        except Exception as e:
            logger.error(f"Error getting approved products for crop {crop_type}: {e}")
            return []
    
    async def _build_product_info(self, product: Produit) -> Dict[str, Any]:
        """Build comprehensive product information"""
        try:
            # Basic product info
            product_info = {
                "numero_amm": product.numero_amm,
                "nom_produit": product.nom_produit,
                "type_produit": product.type_produit.value if product.type_produit else None,
                "etat_autorisation": product.etat_autorisation.value if product.etat_autorisation else None,
                "date_premiere_autorisation": product.date_premiere_autorisation.isoformat() if product.date_premiere_autorisation else None,
                "date_retrait_produit": product.date_retrait_produit.isoformat() if product.date_retrait_produit else None,
                "is_active": product.etat_autorisation == EtatAutorisation.AUTORISE,
                "titulaire": {
                    "nom": product.titulaire.nom if product.titulaire else None
                },
                "substances_actives": [],
                "fonctions": [],
                "formulations": [],
                "usages": [],
                "conditions_emploi": []
            }
            
            # Active substances
            for ps in product.produit_substances:
                substance_info = {
                    "nom_substance": ps.substance.nom_substance,
                    "concentration": float(ps.concentration) if ps.concentration else None,
                    "unite_concentration": ps.unite_concentration
                }
                product_info["substances_actives"].append(substance_info)
            
            # Functions
            for pf in product.produit_fonctions:
                product_info["fonctions"].append(pf.fonction.libelle)
            
            # Formulations
            for pform in product.produit_formulations:
                product_info["formulations"].append(pform.formulation.libelle)
            
            # Usage conditions
            for usage in product.usages:
                usage_info = {
                    "type_culture_libelle": usage.type_culture_libelle,
                    "dose_min_par_apport": float(usage.dose_min_par_apport) if usage.dose_min_par_apport else None,
                    "dose_max_par_apport": float(usage.dose_max_par_apport) if usage.dose_max_par_apport else None,
                    "dose_min_par_apport_unite": usage.dose_min_par_apport_unite,
                    "dose_max_par_apport_unite": usage.dose_max_par_apport_unite,
                    "delai_avant_recolte_jour": usage.delai_avant_recolte_jour,
                    "nombre_max_application": usage.nombre_max_application,
                    "znt_aquatique_m": float(usage.znt_aquatique_m) if usage.znt_aquatique_m else None,
                    "etat_usage": usage.etat_usage,
                    "condition_emploi": usage.condition_emploi
                }
                product_info["usages"].append(usage_info)
            
            # Employment conditions
            for condition in product.conditions_emploi:
                condition_info = {
                    "categorie_condition_emploi": condition.categorie_condition_emploi,
                    "condition_emploi_libelle": condition.condition_emploi_libelle
                }
                product_info["conditions_emploi"].append(condition_info)
            
            return product_info
            
        except Exception as e:
            logger.error(f"Error building product info: {e}")
            return {
                "numero_amm": product.numero_amm,
                "nom_produit": product.nom_produit,
                "error": str(e)
            }
    
    async def get_product_safety_info(self, amm_code: str, db: AsyncSession = None) -> Dict[str, Any]:
        """Get safety information for a product"""
        try:
            product_info = await self.get_product_by_amm(amm_code, db)
            if not product_info:
                return {"error": "Product not found"}
            
            safety_info = {
                "numero_amm": amm_code,
                "nom_produit": product_info.get("nom_produit"),
                "substances_actives": product_info.get("substances_actives", []),
                "fonctions": product_info.get("fonctions", []),
                "conditions_emploi": product_info.get("conditions_emploi", []),
                "znt_requirements": [],
                "pre_harvest_intervals": []
            }
            
            # Extract ZNT requirements
            for usage in product_info.get("usages", []):
                if usage.get("znt_aquatique_m"):
                    safety_info["znt_requirements"].append({
                        "type": "aquatique",
                        "distance_m": usage["znt_aquatique_m"],
                        "culture": usage.get("type_culture_libelle")
                    })
                
                if usage.get("delai_avant_recolte_jour"):
                    safety_info["pre_harvest_intervals"].append({
                        "days": usage["delai_avant_recolte_jour"],
                        "culture": usage.get("type_culture_libelle")
                    })
            
            return safety_info
            
        except Exception as e:
            logger.error(f"Error getting product safety info: {e}")
            return {"error": str(e)}
    
    def clear_cache(self):
        """Clear the product cache"""
        self.cache.clear()
        logger.info("EPHY product cache cleared")
