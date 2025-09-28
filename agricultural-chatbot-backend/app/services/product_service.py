"""
Product service for agricultural chatbot
Handles French agricultural product database operations
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, text
from sqlalchemy.orm import selectinload

from app.models.product import (
    Product, SubstanceActive, ProductSubstance, Usage, 
    ConditionEmploi, ClassificationDanger, PhraseRisque,
    ProductType, AuthorizationStatus, UsageStatus
)
from app.schemas.product import (
    ProductSearchRequest, ProductResponse, ProductUsageResponse,
    SubstanceResponse, ProductCompatibilityResponse
)


class ProductService:
    """Service for managing French agricultural product database"""
    
    async def search_products(
        self,
        db: AsyncSession,
        search_term: Optional[str] = None,
        product_type: Optional[ProductType] = None,
        crop_filter: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Product]:
        """Search products using the database function"""
        query = text("""
            SELECT * FROM search_products(:search_term, :product_type_filter, :crop_filter)
            LIMIT :limit OFFSET :offset
        """)
        
        result = await db.execute(query, {
            "search_term": search_term,
            "product_type_filter": product_type.value if product_type else None,
            "crop_filter": crop_filter,
            "limit": limit,
            "offset": offset
        })
        
        # Convert result to Product objects
        products = []
        for row in result:
            product = await self.get_product_by_amm(db, row.numero_amm)
            if product:
                products.append(product)
        
        return products
    
    async def get_product_by_amm(self, db: AsyncSession, numero_amm: str) -> Optional[Product]:
        """Get product by AMM number"""
        result = await db.execute(
            select(Product)
            .where(Product.numero_amm == numero_amm)
            .options(
                selectinload(Product.substances).selectinload(ProductSubstance.substance),
                selectinload(Product.usages),
                selectinload(Product.conditions_emploi),
                selectinload(Product.classifications_danger),
                selectinload(Product.phrases_risque)
            )
        )
        return result.scalar_one_or_none()
    
    async def get_product_by_name(self, db: AsyncSession, nom_produit: str) -> Optional[Product]:
        """Get product by name"""
        result = await db.execute(
            select(Product)
            .where(Product.nom_produit.ilike(f"%{nom_produit}%"))
            .options(
                selectinload(Product.substances).selectinload(ProductSubstance.substance),
                selectinload(Product.usages),
                selectinload(Product.conditions_emploi),
                selectinload(Product.classifications_danger),
                selectinload(Product.phrases_risque)
            )
        )
        return result.scalar_one_or_none()
    
    async def get_products_by_substance(
        self,
        db: AsyncSession,
        substance_name: str,
        limit: int = 50
    ) -> List[Product]:
        """Get products containing a specific active substance"""
        result = await db.execute(
            select(Product)
            .join(ProductSubstance)
            .join(SubstanceActive)
            .where(
                and_(
                    SubstanceActive.nom_substance.ilike(f"%{substance_name}%"),
                    Product.etat_autorisation == AuthorizationStatus.AUTORISE
                )
            )
            .options(
                selectinload(Product.substances).selectinload(ProductSubstance.substance),
                selectinload(Product.usages)
            )
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_products_for_crop(
        self,
        db: AsyncSession,
        crop_name: str,
        limit: int = 50
    ) -> List[Product]:
        """Get products authorized for a specific crop"""
        result = await db.execute(
            select(Product)
            .join(Usage)
            .where(
                and_(
                    Usage.type_culture_libelle.ilike(f"%{crop_name}%"),
                    Product.etat_autorisation == AuthorizationStatus.AUTORISE,
                    Usage.etat_usage == UsageStatus.AUTORISE
                )
            )
            .options(
                selectinload(Product.substances).selectinload(ProductSubstance.substance),
                selectinload(Product.usages)
            )
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_product_usage_for_crop(
        self,
        db: AsyncSession,
        numero_amm: str,
        crop_name: str
    ) -> List[Usage]:
        """Get usage details for a product on a specific crop"""
        result = await db.execute(
            select(Usage)
            .join(Product)
            .where(
                and_(
                    Product.numero_amm == numero_amm,
                    Usage.type_culture_libelle.ilike(f"%{crop_name}%"),
                    Product.etat_autorisation == AuthorizationStatus.AUTORISE,
                    Usage.etat_usage == UsageStatus.AUTORISE
                )
            )
        )
        return result.scalars().all()
    
    async def get_substance_by_name(self, db: AsyncSession, nom_substance: str) -> Optional[SubstanceActive]:
        """Get active substance by name"""
        result = await db.execute(
            select(SubstanceActive)
            .where(SubstanceActive.nom_substance.ilike(f"%{nom_substance}%"))
        )
        return result.scalar_one_or_none()
    
    async def get_substances_by_function(
        self,
        db: AsyncSession,
        fonction: str,
        limit: int = 50
    ) -> List[SubstanceActive]:
        """Get active substances by function (insecticide, fongicide, etc.)"""
        result = await db.execute(
            select(SubstanceActive)
            .join(ProductSubstance)
            .where(
                and_(
                    ProductSubstance.fonction.ilike(f"%{fonction}%"),
                    SubstanceActive.etat_autorisation == AuthorizationStatus.AUTORISE
                )
            )
            .options(selectinload(SubstanceActive.products))
            .limit(limit)
        )
        return result.scalars().all()
    
    async def check_product_compatibility(
        self,
        db: AsyncSession,
        product1_amm: str,
        product2_amm: str
    ) -> Dict[str, Any]:
        """Check compatibility between two products"""
        query = text("""
            SELECT * FROM check_product_compatibility(:product1_amm, :product2_amm)
        """)
        
        result = await db.execute(query, {
            "product1_amm": product1_amm,
            "product2_amm": product2_amm
        })
        
        row = result.fetchone()
        if row:
            return {
                "compatible": row.compatible,
                "conflict_reason": row.conflict_reason,
                "common_substances": row.substances_common
            }
        
        return {
            "compatible": True,
            "conflict_reason": "No compatibility data available",
            "common_substances": None
        }
    
    async def get_products_with_buffer_zones(
        self,
        db: AsyncSession,
        limit: int = 50
    ) -> List[Product]:
        """Get products that require buffer zones (ZNT)"""
        result = await db.execute(
            select(Product)
            .join(Usage)
            .where(
                and_(
                    Product.etat_autorisation == AuthorizationStatus.AUTORISE,
                    Usage.etat_usage == UsageStatus.AUTORISE,
                    or_(
                        Usage.znt_aquatique_m.isnot(None),
                        Usage.znt_arthropodes_non_cibles_m.isnot(None),
                        Usage.znt_plantes_non_cibles_m.isnot(None)
                    )
                )
            )
            .options(
                selectinload(Product.substances).selectinload(ProductSubstance.substance),
                selectinload(Product.usages)
            )
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_products_by_holder(
        self,
        db: AsyncSession,
        titulaire: str,
        limit: int = 50
    ) -> List[Product]:
        """Get products by holder company"""
        result = await db.execute(
            select(Product)
            .where(
                and_(
                    Product.titulaire.ilike(f"%{titulaire}%"),
                    Product.etat_autorisation == AuthorizationStatus.AUTORISE
                )
            )
            .options(
                selectinload(Product.substances).selectinload(ProductSubstance.substance),
                selectinload(Product.usages)
            )
            .limit(limit)
        )
        return result.scalars().all()
    
    async def get_product_statistics(self, db: AsyncSession) -> Dict[str, Any]:
        """Get product database statistics"""
        # Total products
        total_products_result = await db.execute(
            select(func.count(Product.id))
        )
        total_products = total_products_result.scalar()
        
        # Authorized products
        authorized_products_result = await db.execute(
            select(func.count(Product.id))
            .where(Product.etat_autorisation == AuthorizationStatus.AUTORISE)
        )
        authorized_products = authorized_products_result.scalar()
        
        # Products by type
        mfsc_products_result = await db.execute(
            select(func.count(Product.id))
            .where(
                and_(
                    Product.type_produit == ProductType.MFSC,
                    Product.etat_autorisation == AuthorizationStatus.AUTORISE
                )
            )
        )
        mfsc_products = mfsc_products_result.scalar()
        
        ppp_products_result = await db.execute(
            select(func.count(Product.id))
            .where(
                and_(
                    Product.type_produit == ProductType.PPP,
                    Product.etat_autorisation == AuthorizationStatus.AUTORISE
                )
            )
        )
        ppp_products = ppp_products_result.scalar()
        
        # Total active substances
        total_substances_result = await db.execute(
            select(func.count(SubstanceActive.id))
            .where(SubstanceActive.etat_autorisation == AuthorizationStatus.AUTORISE)
        )
        total_substances = total_substances_result.scalar()
        
        # Total usages
        total_usages_result = await db.execute(
            select(func.count(Usage.id))
            .where(Usage.etat_usage == UsageStatus.AUTORISE)
        )
        total_usages = total_usages_result.scalar()
        
        return {
            "total_products": total_products,
            "authorized_products": authorized_products,
            "mfsc_products": mfsc_products,
            "ppp_products": ppp_products,
            "total_substances": total_substances,
            "total_usages": total_usages,
            "authorization_rate": (authorized_products / total_products * 100) if total_products > 0 else 0
        }
    
    async def get_crop_statistics(self, db: AsyncSession) -> List[Dict[str, Any]]:
        """Get statistics by crop type"""
        query = text("""
            SELECT 
                u.type_culture_libelle as crop,
                COUNT(DISTINCT p.id) as nb_products,
                COUNT(DISTINCT u.id) as nb_usages,
                STRING_AGG(DISTINCT p.nom_produit, ', ') as products
            FROM products p
            JOIN usages u ON p.id = u.product_id
            WHERE p.etat_autorisation = 'AUTORISE' 
            AND u.etat_usage = 'Autorise'
            AND u.type_culture_libelle IS NOT NULL
            GROUP BY u.type_culture_libelle
            ORDER BY nb_products DESC
            LIMIT 20
        """)
        
        result = await db.execute(query)
        return [
            {
                "crop": row.crop,
                "nb_products": row.nb_products,
                "nb_usages": row.nb_usages,
                "products": row.products
            }
            for row in result
        ]
    
    async def get_substance_statistics(self, db: AsyncSession) -> List[Dict[str, Any]]:
        """Get statistics by active substance"""
        query = text("""
            SELECT 
                ps.fonction,
                sa.nom_substance,
                sa.numero_cas,
                COUNT(DISTINCT p.id) as nb_products,
                STRING_AGG(DISTINCT p.nom_produit, ', ') as products
            FROM substances_actives sa
            JOIN product_substances ps ON sa.id = ps.substance_id
            JOIN products p ON ps.product_id = p.id
            WHERE p.etat_autorisation = 'AUTORISE'
            AND sa.etat_autorisation = 'AUTORISE'
            AND ps.fonction IS NOT NULL
            GROUP BY ps.fonction, sa.nom_substance, sa.numero_cas
            ORDER BY ps.fonction, nb_products DESC
            LIMIT 50
        """)
        
        result = await db.execute(query)
        return [
            {
                "fonction": row.fonction,
                "nom_substance": row.nom_substance,
                "numero_cas": row.numero_cas,
                "nb_products": row.nb_products,
                "products": row.products
            }
            for row in result
        ]
    
    async def validate_product_usage(
        self,
        db: AsyncSession,
        numero_amm: str,
        crop_name: str,
        dose: float,
        unit: str
    ) -> Dict[str, Any]:
        """Validate product usage for a specific crop and dose"""
        usages = await self.get_product_usage_for_crop(db, numero_amm, crop_name)
        
        if not usages:
            return {
                "valid": False,
                "error": f"Aucun usage autorisé trouvé pour le produit {numero_amm} sur la culture {crop_name}"
            }
        
        # Check dose against authorized ranges
        for usage in usages:
            if usage.dose_unite == unit:
                if usage.dose_min_par_apport and dose < usage.dose_min_par_apport:
                    return {
                        "valid": False,
                        "error": f"Dose trop faible. Dose minimale autorisée: {usage.dose_min_par_apport} {unit}"
                    }
                
                if usage.dose_max_par_apport and dose > usage.dose_max_par_apport:
                    return {
                        "valid": False,
                        "error": f"Dose trop élevée. Dose maximale autorisée: {usage.dose_max_par_apport} {unit}"
                    }
                
                return {
                    "valid": True,
                    "usage": {
                        "dose_retenue": usage.dose_retenue,
                        "dose_unite": usage.dose_unite,
                        "nombre_max_application": usage.nombre_max_application,
                        "delai_avant_recolte_jour": usage.delai_avant_recolte_jour,
                        "intervalle_minimum_applications_jour": usage.intervalle_minimum_applications_jour,
                        "znt_aquatique_m": usage.znt_aquatique_m,
                        "znt_arthropodes_non_cibles_m": usage.znt_arthropodes_non_cibles_m,
                        "znt_plantes_non_cibles_m": usage.znt_plantes_non_cibles_m,
                        "condition_emploi": usage.condition_emploi,
                        "restrictions_usage_libelle": usage.restrictions_usage_libelle
                    }
                }
        
        return {
            "valid": False,
            "error": f"Unité de dose non autorisée. Unités autorisées: {', '.join(set(u.dose_unite for u in usages if u.dose_unite))}"
        }
