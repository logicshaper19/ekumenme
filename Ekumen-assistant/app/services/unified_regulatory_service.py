"""
Unified regulatory service combining configuration and database access
Provides comprehensive regulatory compliance checking for agricultural products
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, date
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_
from dataclasses import dataclass

from app.models.ephy import (
    Produit as Product, SubstanceActive, ProduitSubstance as ProductSubstance,
    UsageProduit as Usage, ProductType, EtatAutorisation as AuthorizationStatus
)
from app.services.configuration_service import get_configuration_service
from app.services.product_service import ProductService

logger = logging.getLogger(__name__)


@dataclass
class ComplianceResult:
    """Result of compliance checking"""
    compliant: bool
    score: float
    violations: List[str]
    warnings: List[str]
    recommendations: List[str]
    details: Dict[str, Any]


@dataclass
class ProductComplianceInfo:
    """Comprehensive product compliance information"""
    product: Product
    compliance_result: ComplianceResult
    usage_restrictions: List[str]
    safety_intervals: Dict[str, int]
    znt_requirements: Dict[str, float]
    application_limits: Dict[str, Any]
    environmental_considerations: List[str]


class UnifiedRegulatoryService:
    """
    Unified service for regulatory compliance checking
    
    Combines:
    - Configuration-based business rules
    - Real EPHY database product data
    - Contextual farm information
    - Seasonal and regional adjustments
    """
    
    def __init__(self):
        self.config_service = get_configuration_service()
        self.product_service = ProductService()
        logger.info("Initialized UnifiedRegulatoryService")
    
    async def search_compliant_products(
        self,
        db: AsyncSession,
        product_name: str = None,
        active_ingredient: str = None,
        product_type: str = None,
        crop_type: str = None,
        farm_context: Dict[str, Any] = None
    ) -> List[ProductComplianceInfo]:
        """
        Search for compliant products with comprehensive compliance checking
        
        Args:
            db: Database session
            product_name: Name of product to search
            active_ingredient: Active ingredient to search
            product_type: Type of product (PPP, MFSC)
            crop_type: Target crop type
            farm_context: Farm-specific context (location, parcels, etc.)
            
        Returns:
            List of products with compliance information
        """
        try:
            # Search products in EPHY database
            products = await self._search_ephy_products(
                db, product_name, active_ingredient, product_type
            )
            
            if not products:
                logger.info(f"No products found for search criteria")
                return []
            
            # Check compliance for each product
            compliance_results = []
            for product in products:
                compliance_info = await self._check_product_compliance(
                    db, product, crop_type, farm_context
                )
                compliance_results.append(compliance_info)
            
            # Sort by compliance score (highest first)
            compliance_results.sort(
                key=lambda x: x.compliance_result.score, 
                reverse=True
            )
            
            logger.info(f"Found {len(compliance_results)} products with compliance info")
            return compliance_results
            
        except Exception as e:
            logger.error(f"Error in search_compliant_products: {e}")
            raise
    
    async def _search_ephy_products(
        self,
        db: AsyncSession,
        product_name: str = None,
        active_ingredient: str = None,
        product_type: str = None
    ) -> List[Product]:
        """Search products in EPHY database"""
        query = select(Product).where(
            Product.etat_autorisation == AuthorizationStatus.AUTORISE
        )

        # Add search filters
        if product_name:
            query = query.where(
                Product.nom_produit.ilike(f"%{product_name}%")
            )

        if product_type:
            try:
                prod_type = ProductType(product_type.upper())
                query = query.where(Product.type_produit == prod_type)
            except ValueError:
                logger.warning(f"Invalid product type: {product_type}")

        # If searching by active ingredient, join with substances
        if active_ingredient:
            query = query.join(ProductSubstance, Product.numero_amm == ProductSubstance.numero_amm)\
                         .join(SubstanceActive, ProductSubstance.substance_id == SubstanceActive.id)\
                         .where(SubstanceActive.nom_substance.ilike(f"%{active_ingredient}%"))
        
        # Limit results for performance
        query = query.limit(50)
        
        result = await db.execute(query)
        products = result.scalars().all()
        
        return list(products)
    
    async def _check_product_compliance(
        self,
        db: AsyncSession,
        product: Product,
        crop_type: str = None,
        farm_context: Dict[str, Any] = None
    ) -> ProductComplianceInfo:
        """Check comprehensive compliance for a product"""
        
        # Get configuration
        config = self.config_service.get_regulatory_config()
        
        # Initialize compliance checking
        violations = []
        warnings = []
        recommendations = []
        score_components = {}
        
        # 1. Check authorization status
        auth_score = self._check_authorization_status(product, violations, warnings)
        score_components['authorization'] = auth_score
        
        # 2. Check usage restrictions for crop
        usage_score = await self._check_usage_restrictions(
            db, product, crop_type, violations, warnings
        )
        score_components['usage'] = usage_score
        
        # 3. Check ZNT requirements
        znt_score, znt_requirements = self._check_znt_requirements(
            product, farm_context, violations, warnings
        )
        score_components['znt'] = znt_score
        
        # 4. Check application limits
        limits_score, application_limits = self._check_application_limits(
            product, farm_context, violations, warnings
        )
        score_components['limits'] = limits_score
        
        # 5. Check safety intervals
        safety_score, safety_intervals = self._check_safety_intervals(
            product, crop_type, violations, warnings
        )
        score_components['safety'] = safety_score
        
        # 6. Environmental considerations
        env_considerations = self._get_environmental_considerations(
            product, farm_context, warnings, recommendations
        )
        
        # Calculate overall compliance score
        weights = config.get('compliance_scoring', {}).get('weights', {})
        overall_score = self._calculate_compliance_score(score_components, weights)
        
        # Determine compliance status
        thresholds = config.get('compliance_scoring', {}).get('thresholds', {})
        is_compliant = overall_score >= thresholds.get('compliant', 0.8)
        
        # Create compliance result
        compliance_result = ComplianceResult(
            compliant=is_compliant,
            score=overall_score,
            violations=violations,
            warnings=warnings,
            recommendations=recommendations,
            details=score_components
        )
        
        # Get usage restrictions
        usage_restrictions = await self._get_usage_restrictions(db, product, crop_type)
        
        return ProductComplianceInfo(
            product=product,
            compliance_result=compliance_result,
            usage_restrictions=usage_restrictions,
            safety_intervals=safety_intervals,
            znt_requirements=znt_requirements,
            application_limits=application_limits,
            environmental_considerations=env_considerations
        )
    
    def _check_authorization_status(
        self, 
        product: Product, 
        violations: List[str], 
        warnings: List[str]
    ) -> float:
        """Check product authorization status"""
        if product.etat_autorisation != AuthorizationStatus.AUTORISE:
            violations.append(f"Produit non autorisé: {product.etat_autorisation}")
            return 0.0
        
        # Check if product is close to withdrawal
        if product.date_retrait_produit:
            days_until_withdrawal = (product.date_retrait_produit - date.today()).days
            if days_until_withdrawal < 30:
                warnings.append(f"Produit retiré dans {days_until_withdrawal} jours")
                return 0.7
        
        return 1.0
    
    async def _check_usage_restrictions(
        self,
        db: AsyncSession,
        product: Product,
        crop_type: str,
        violations: List[str],
        warnings: List[str]
    ) -> float:
        """Check usage restrictions for specific crop"""
        if not crop_type:
            return 1.0  # No specific crop to check
        
        # Get authorized usages from database
        query = select(Usage).where(
            and_(
                Usage.product_id == product.id,
                Usage.etat_usage == AuthorizationStatus.AUTORISE
            )
        )
        
        result = await db.execute(query)
        usages = result.scalars().all()
        
        # Check if crop is authorized
        authorized_crops = []
        for usage in usages:
            if usage.type_culture_libelle:
                authorized_crops.append(usage.type_culture_libelle.lower())
        
        if crop_type.lower() not in authorized_crops:
            violations.append(f"Culture {crop_type} non autorisée pour ce produit")
            return 0.0
        
        return 1.0
    
    def _check_znt_requirements(
        self,
        product: Product,
        farm_context: Dict[str, Any],
        violations: List[str],
        warnings: List[str]
    ) -> Tuple[float, Dict[str, float]]:
        """Check ZNT (Zone Non Traitée) requirements"""
        znt_config = self.config_service.get_znt_requirements()
        znt_requirements = {}
        
        if not farm_context:
            return 1.0, znt_requirements
        
        # Check distance to water bodies
        distance_to_water = farm_context.get('distance_to_water_m', float('inf'))
        required_znt = znt_config.get('minimum_meters', 5)
        
        # Adjust for product risk level
        if hasattr(product, 'environmental_risk'):
            if product.environmental_risk == 'high':
                required_znt = znt_config.get('high_risk_meters', 20)
            elif product.environmental_risk == 'very_high':
                required_znt = znt_config.get('very_high_risk_meters', 50)
        
        znt_requirements['cours_eau'] = required_znt
        
        if distance_to_water < required_znt:
            violations.append(f"ZNT non respectée: {distance_to_water}m < {required_znt}m requis")
            return 0.0
        
        return 1.0
    
    def _check_application_limits(
        self,
        product: Product,
        farm_context: Dict[str, Any],
        violations: List[str],
        warnings: List[str]
    ) -> Tuple[float, Dict[str, Any]]:
        """Check application limits and restrictions"""
        application_limits = {}
        
        # Check substance-specific limits
        for substance_rel in product.substances:
            substance_name = substance_rel.substance.nom_substance.lower()
            limits = self.config_service.get_application_limits(substance_name)
            
            if limits:
                application_limits[substance_name] = limits
                
                # Check if substance is banned
                if limits.get('status') == 'interdiction_generale':
                    violations.append(f"Substance interdite: {substance_name}")
                    return 0.0
                
                # Check crop-specific bans
                banned_crops = limits.get('banned_crops', [])
                if farm_context and farm_context.get('crop_type') in banned_crops:
                    violations.append(f"Substance interdite sur {farm_context['crop_type']}")
                    return 0.0
        
        return 1.0, application_limits
    
    def _check_safety_intervals(
        self,
        product: Product,
        crop_type: str,
        violations: List[str],
        warnings: List[str]
    ) -> Tuple[float, Dict[str, int]]:
        """Check safety intervals"""
        safety_intervals = {}
        
        # Get safety intervals from configuration
        intervals_config = self.config_service.get_safety_intervals(crop_type)
        safety_intervals['pre_harvest_days'] = intervals_config['pre_harvest_days']
        
        # Add re-entry intervals
        config = self.config_service.get_regulatory_config()
        re_entry = config.get('safety_intervals', {}).get('re_entry_intervals', {})
        safety_intervals['re_entry_hours'] = re_entry.get('default_hours', 6)
        
        return 1.0, safety_intervals
    
    def _get_environmental_considerations(
        self,
        product: Product,
        farm_context: Dict[str, Any],
        warnings: List[str],
        recommendations: List[str]
    ) -> List[str]:
        """Get environmental considerations"""
        considerations = []
        
        # Add bee protection warnings
        considerations.append("🐝 Respecter les heures de butinage des abeilles")
        
        # Add weather-related recommendations
        considerations.append("🌤️ Éviter l'application par vent fort (>20 km/h)")
        considerations.append("🌧️ Vérifier les prévisions météo (pas de pluie 6h après)")
        
        return considerations
    
    async def _get_usage_restrictions(
        self,
        db: AsyncSession,
        product: Product,
        crop_type: str
    ) -> List[str]:
        """Get detailed usage restrictions"""
        restrictions = []
        
        # Add general restrictions from product
        if product.restrictions_usage:
            restrictions.append(product.restrictions_usage)
        
        return restrictions
    
    def _calculate_compliance_score(
        self,
        score_components: Dict[str, float],
        weights: Dict[str, float]
    ) -> float:
        """Calculate weighted compliance score"""
        total_score = 0.0
        total_weight = 0.0
        
        default_weights = {
            'authorization': 0.3,
            'usage': 0.25,
            'znt': 0.2,
            'limits': 0.15,
            'safety': 0.1
        }
        
        for component, score in score_components.items():
            weight = weights.get(component, default_weights.get(component, 0.1))
            total_score += score * weight
            total_weight += weight
        
        return total_score / total_weight if total_weight > 0 else 0.0
