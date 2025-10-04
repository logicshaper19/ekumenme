"""
Enhanced AMM lookup tool with Pydantic schemas, caching, and structured error handling
Uses real EPHY database with configuration-driven compliance checking
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from langchain_core.tools import StructuredTool
from pydantic import ValidationError

from app.core.database import AsyncSessionLocal
from app.core.cache import redis_cache
from app.services.unified_regulatory_service import UnifiedRegulatoryService
from app.services.configuration_service import get_configuration_service
from app.tools.schemas.amm_schemas import (
    AMMInput, AMMOutput, ProductInfo, SubstanceInfo,
    SearchSummary, RegulatoryContext, ComplianceStatus
)
from app.tools.exceptions import (
    AMMValidationError, AMMDataError, AMMLookupError
)

logger = logging.getLogger(__name__)


class AMMService:
    """
    Enhanced AMM lookup service with caching and structured responses
    
    Features:
    - Real EPHY database product lookup
    - Configuration-based compliance checking
    - Redis + memory caching (2h TTL for regulatory data)
    - Structured Pydantic output
    - Comprehensive error handling
    """
    
    def __init__(self):
        self.regulatory_service = UnifiedRegulatoryService()
        self.config_service = get_configuration_service()
        logger.info("Initialized AMMService")
    
    @redis_cache(ttl=7200, model_class=AMMOutput, category="regulatory")  # 2 hour TTL
    async def lookup_amm(
        self,
        product_name: Optional[str] = None,
        active_ingredient: Optional[str] = None,
        product_type: Optional[str] = None,
        crop_type: Optional[str] = None,
        farm_context: Optional[Dict[str, Any]] = None
    ) -> AMMOutput:
        """
        Look up AMM products with compliance checking
        
        Args:
            product_name: Nom du produit à rechercher
            active_ingredient: Substance active (optionnel)
            product_type: Type de produit (PPP, MFSC)
            crop_type: Type de culture cible
            farm_context: Contexte exploitation
            
        Returns:
            AMMOutput with products and compliance information
        """
        try:
            # Validate at least one search criterion
            if not any([product_name, active_ingredient]):
                raise AMMValidationError(
                    "Au moins un critère de recherche requis (product_name ou active_ingredient)"
                )
            
            async with AsyncSessionLocal() as db:
                # Search compliant products
                compliance_results = await self.regulatory_service.search_compliant_products(
                    db=db,
                    product_name=product_name,
                    active_ingredient=active_ingredient,
                    product_type=product_type,
                    crop_type=crop_type,
                    farm_context=farm_context
                )
                
                if not compliance_results:
                    return self._format_no_results_response(
                        product_name, active_ingredient, product_type, crop_type
                    )
                
                # Format comprehensive response
                return self._format_compliance_response(
                    compliance_results, farm_context, crop_type
                )
                
        except AMMValidationError as e:
            logger.warning(f"AMM validation error: {e}")
            return AMMOutput(
                success=False,
                status="error",
                error=str(e),
                error_type="validation",
                legal_disclaimer=self._get_legal_disclaimer(),
                timestamp=datetime.now()
            )
        
        except AMMDataError as e:
            logger.error(f"AMM data error: {e}")
            return AMMOutput(
                success=False,
                status="error",
                error=f"Erreur d'accès aux données: {str(e)}",
                error_type="database",
                legal_disclaimer=self._get_legal_disclaimer(),
                timestamp=datetime.now()
            )
        
        except Exception as e:
            logger.error(f"Unexpected error in AMM lookup: {e}")
            return AMMOutput(
                success=False,
                status="error",
                error=f"Erreur inattendue: {str(e)}",
                error_type="unknown",
                legal_disclaimer=self._get_legal_disclaimer(),
                timestamp=datetime.now()
            )
    
    def _format_no_results_response(
        self,
        product_name: Optional[str],
        active_ingredient: Optional[str],
        product_type: Optional[str],
        crop_type: Optional[str]
    ) -> AMMOutput:
        """Format response when no products found"""
        return AMMOutput(
            success=True,
            status="no_results",
            search_criteria={
                "product_name": product_name,
                "active_ingredient": active_ingredient,
                "product_type": product_type,
                "crop_type": crop_type
            },
            recommendations=[
                "🔍 Vérifiez l'orthographe du nom du produit",
                "🔍 Essayez avec la substance active uniquement",
                "🔍 Consultez directement E-phy: https://ephy.anses.fr/",
                "⚠️ Contactez votre conseiller agricole"
            ],
            legal_disclaimer=self._get_legal_disclaimer(),
            timestamp=datetime.now()
        )
    
    def _format_compliance_response(
        self,
        compliance_results: List,
        farm_context: Optional[Dict[str, Any]],
        crop_type: Optional[str]
    ) -> AMMOutput:
        """Format comprehensive compliance response"""
        
        # Separate compliant and non-compliant products
        compliant = [r for r in compliance_results if r.compliance_result.compliant]
        non_compliant = [r for r in compliance_results if not r.compliance_result.compliant]
        
        # Get configuration
        config = self.config_service.get_regulatory_config()
        
        return AMMOutput(
            success=True,
            status="success",
            summary=SearchSummary(
                total_products_found=len(compliance_results),
                compliant_products=len(compliant),
                non_compliant_products=len(non_compliant),
                search_context={
                    "crop_type": crop_type,
                    "farm_context_provided": bool(farm_context)
                }
            ),
            compliant_products=[
                self._format_product_info(result, ComplianceStatus.COMPLIANT)
                for result in compliant[:5]  # Limit to top 5
            ],
            non_compliant_products=[
                self._format_product_info(result, ComplianceStatus.NON_COMPLIANT)
                for result in non_compliant[:3]  # Limit to 3
            ],
            general_recommendations=self._get_general_recommendations(farm_context, crop_type),
            regulatory_context=RegulatoryContext(
                znt_requirements=config.get('znt_requirements', {}),
                seasonal_considerations=self._get_seasonal_considerations(),
                regional_factors=self._get_regional_factors(farm_context)
            ),
            legal_disclaimer=self._get_legal_disclaimer(),
            configuration_version=config.get('metadata', {}).get('version', '1.0.0'),
            timestamp=datetime.now()
        )
    
    def _format_product_info(self, compliance_result, status: ComplianceStatus) -> ProductInfo:
        """Format individual product information"""
        product = compliance_result.product
        compliance = compliance_result.compliance_result
        
        # Get main active substances
        substances = []
        for substance_rel in product.substances[:3]:  # Limit to first 3
            substances.append(SubstanceInfo(
                nom=substance_rel.substance.nom_substance,
                concentration=f"{substance_rel.concentration_value} {substance_rel.concentration_unit}" 
                    if substance_rel.concentration_value else "N/A"
            ))
        
        # Base product info
        product_info_dict = {
            "numero_amm": product.numero_amm,
            "nom_produit": product.nom_produit,
            "type_produit": product.type_produit.value if product.type_produit else "N/A",
            "titulaire": product.titulaire or "N/A",
            "etat_autorisation": product.etat_autorisation.value if product.etat_autorisation else "N/A",
            "substances_actives": substances,
            "compliance_score": round(compliance.score * 100, 1),
            "status": status
        }
        
        # Add compliance-specific details
        if status == ComplianceStatus.COMPLIANT:
            product_info_dict.update({
                "usage_recommendations": compliance.recommendations[:3],
                "safety_intervals": compliance_result.safety_intervals,
                "znt_requirements": compliance_result.znt_requirements,
                "environmental_considerations": compliance_result.environmental_considerations[:3]
            })
        else:
            product_info_dict.update({
                "violations": compliance.violations,
                "warnings": compliance.warnings,
                "non_compliance_reasons": compliance.violations[:3]
            })
        
        return ProductInfo(**product_info_dict)
    
    def _get_general_recommendations(
        self, 
        farm_context: Optional[Dict[str, Any]], 
        crop_type: Optional[str]
    ) -> List[str]:
        """Get general recommendations based on context"""
        recommendations = [
            "📋 Vérifiez toujours l'étiquette du produit avant utilisation",
            "🌤️ Consultez les conditions météorologiques avant traitement",
            "🐝 Respectez les périodes de butinage des abeilles",
            "💧 Respectez les Zones Non Traitées (ZNT) près des points d'eau"
        ]
        
        # Add crop-specific recommendations
        if crop_type:
            try:
                safety_intervals = self.config_service.get_safety_intervals(crop_type)
                recommendations.append(
                    f"⏰ Délai avant récolte pour {crop_type}: {safety_intervals.get('pre_harvest_days', 14)} jours minimum"
                )
            except Exception:
                pass
        
        # Add farm-specific recommendations
        if farm_context:
            if farm_context.get('organic_certified'):
                recommendations.append("🌱 Exploitation bio: vérifiez la compatibilité avec le cahier des charges")
            
            if farm_context.get('distance_to_water_m', float('inf')) < 50:
                recommendations.append("💧 Proximité cours d'eau: attention renforcée aux ZNT")
        
        return recommendations
    
    def _get_seasonal_considerations(self) -> Dict[str, Any]:
        """Get current seasonal considerations"""
        current_month = datetime.now().month
        
        # Determine season
        if current_month in [3, 4, 5]:
            season = "printemps"
        elif current_month in [6, 7, 8]:
            season = "ete"
        elif current_month in [9, 10, 11]:
            season = "automne"
        else:
            season = "hiver"
        
        try:
            adjustments = self.config_service.get_seasonal_adjustments(season)
        except Exception:
            adjustments = {}
        
        return {
            "current_season": season,
            "adjustments": adjustments,
            "recommendations": self._get_seasonal_recommendations(season)
        }
    
    def _get_seasonal_recommendations(self, season: str) -> List[str]:
        """Get season-specific recommendations"""
        seasonal_recs = {
            "printemps": [
                "🌸 Période de floraison: protection renforcée des pollinisateurs",
                "🌧️ Risque de pluie élevé: vérifiez les prévisions"
            ],
            "ete": [
                "☀️ Températures élevées: évitez les heures chaudes",
                "🐝 Activité maximale des abeilles: respectez les horaires"
            ],
            "automne": [
                "🍂 Conditions variables: adaptez selon la météo",
                "⏰ Préparation hivernale: derniers traitements"
            ],
            "hiver": [
                "❄️ Conditions difficiles: traitements limités",
                "🌡️ Températures basses: efficacité réduite"
            ]
        }
        
        return seasonal_recs.get(season, [])
    
    def _get_regional_factors(self, farm_context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Get regional adjustment factors"""
        if not farm_context or 'region' not in farm_context:
            return {}
        
        region = farm_context['region'].lower()
        
        try:
            factors = self.config_service.get_regional_factors(region)
        except Exception:
            factors = {}
        
        return {
            "region": region,
            "factors": factors,
            "special_considerations": factors.get('special_restrictions', [])
        }
    
    def _get_legal_disclaimer(self) -> str:
        """Get legal disclaimer"""
        return ("⚠️ IMPORTANT: Cette analyse est basée sur les données EPHY officielles "
                "mais ne remplace pas l'expertise d'un conseiller agricole. "
                "Vérifiez toujours les conditions d'autorisation avant application.")


# Create service instance
_amm_service = AMMService()


# Async wrapper function
async def lookup_amm_async(
    product_name: Optional[str] = None,
    active_ingredient: Optional[str] = None,
    product_type: Optional[str] = None,
    crop_type: Optional[str] = None,
    farm_context: Optional[Dict[str, Any]] = None
) -> AMMOutput:
    """Async wrapper for AMM lookup"""
    return await _amm_service.lookup_amm(
        product_name=product_name,
        active_ingredient=active_ingredient,
        product_type=product_type,
        crop_type=crop_type,
        farm_context=farm_context
    )


# Create StructuredTool
lookup_amm_tool = StructuredTool.from_function(
    coroutine=lookup_amm_async,
    name="lookup_amm_tool",
    description="""
Recherche de produits AMM dans la base EPHY officielle avec vérification de conformité.

Utilise:
- Base de données EPHY officielle (30 000+ produits)
- Règles de conformité configurables
- Contexte exploitation spécifique
- Ajustements saisonniers et régionaux
- Cache Redis (2h TTL)

Paramètres:
- product_name: Nom du produit recherché (ex: 'Roundup')
- active_ingredient: Substance active (ex: 'glyphosate')
- product_type: Type de produit (PPP, MFSC)
- crop_type: Type de culture cible (ex: 'blé', 'maïs')
- farm_context: Contexte exploitation (dict avec region, distance_to_water_m, etc.)

Retourne: Produits conformes avec scores de conformité, recommandations, et contexte réglementaire.
""",
    args_schema=AMMInput,
    return_direct=False,
    handle_validation_error=False  # We handle validation ourselves
)

