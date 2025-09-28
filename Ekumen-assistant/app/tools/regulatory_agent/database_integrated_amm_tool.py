"""
Database-integrated AMM lookup tool with configuration-driven compliance checking
Uses real EPHY database data with configurable business rules
"""

import json
import logging
from typing import Dict, List, Any
from datetime import datetime
from langchain.tools import BaseTool

from app.core.database import AsyncSessionLocal
from app.services.unified_regulatory_service import UnifiedRegulatoryService
from app.services.configuration_service import get_configuration_service

logger = logging.getLogger(__name__)


class DatabaseIntegratedAMMLookupTool(BaseTool):
    """
    AMM lookup tool using real EPHY database with configuration-driven compliance
    
    Features:
    - Real EPHY database product lookup
    - Configuration-based compliance checking
    - Contextual farm-specific recommendations
    - Seasonal and regional adjustments
    - Hot-reload of business rules
    """
    
    name: str = "lookup_amm_database"
    description: str = """
    Recherche de produits AMM dans la base EPHY officielle avec vérification de conformité.
    
    Utilise:
    - Base de données EPHY officielle (30 000+ produits)
    - Règles de conformité configurables
    - Contexte exploitation spécifique
    - Ajustements saisonniers et régionaux
    
    Paramètres:
    - product_name: Nom du produit recherché
    - active_ingredient: Substance active (optionnel)
    - product_type: Type de produit (PPP, MFSC)
    - crop_type: Type de culture cible
    - farm_context: Contexte exploitation (JSON string)
    """

    def __init__(self):
        super().__init__()
        logger.info("Initialized DatabaseIntegratedAMMLookupTool")

    @property
    def regulatory_service(self):
        """Get regulatory service instance"""
        if not hasattr(self, '_regulatory_service'):
            self._regulatory_service = UnifiedRegulatoryService()
        return self._regulatory_service

    @property
    def config_service(self):
        """Get configuration service instance"""
        if not hasattr(self, '_config_service'):
            self._config_service = get_configuration_service()
        return self._config_service
    
    def _run(
        self,
        product_name: str,
        active_ingredient: str = None,
        product_type: str = None,
        crop_type: str = None,
        farm_context: str = None
    ) -> str:
        """
        Synchronous wrapper for async AMM lookup
        
        Args:
            product_name: Nom du produit à rechercher
            active_ingredient: Substance active (optionnel)
            product_type: Type de produit (PPP, MFSC)
            crop_type: Type de culture cible
            farm_context: Contexte exploitation (JSON string)
        """
        import asyncio
        
        try:
            # Parse farm context if provided
            parsed_farm_context = None
            if farm_context:
                try:
                    parsed_farm_context = json.loads(farm_context)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid farm_context JSON: {farm_context}")
            
            # Run async lookup
            result = asyncio.run(self._async_lookup(
                product_name=product_name,
                active_ingredient=active_ingredient,
                product_type=product_type,
                crop_type=crop_type,
                farm_context=parsed_farm_context
            ))
            
            return result
            
        except Exception as e:
            logger.error(f"Error in AMM lookup: {e}")
            return json.dumps({
                "status": "error",
                "message": f"Erreur lors de la recherche AMM: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }, ensure_ascii=False, indent=2)
    
    async def _async_lookup(
        self,
        product_name: str,
        active_ingredient: str = None,
        product_type: str = None,
        crop_type: str = None,
        farm_context: Dict[str, Any] = None
    ) -> str:
        """
        Async AMM lookup with comprehensive compliance checking
        """
        try:
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
                
        except Exception as e:
            logger.error(f"Error in async AMM lookup: {e}")
            raise
    
    def _format_no_results_response(
        self,
        product_name: str,
        active_ingredient: str,
        product_type: str,
        crop_type: str
    ) -> str:
        """Format response when no products found"""
        response = {
            "status": "no_results",
            "message": "Aucun produit autorisé trouvé",
            "search_criteria": {
                "product_name": product_name,
                "active_ingredient": active_ingredient,
                "product_type": product_type,
                "crop_type": crop_type
            },
            "recommendations": [
                "🔍 Vérifiez l'orthographe du nom du produit",
                "🔍 Essayez avec la substance active uniquement",
                "🔍 Consultez directement E-phy: https://ephy.anses.fr/",
                "⚠️ Contactez votre conseiller agricole"
            ],
            "legal_disclaimer": "⚠️ IMPORTANT: Consultez toujours un conseiller agricole qualifié avant tout traitement. Cette recherche est indicative et ne remplace pas l'expertise professionnelle.",
            "data_source": "EPHY_DATABASE_OFFICIAL",
            "timestamp": datetime.now().isoformat()
        }
        
        return json.dumps(response, ensure_ascii=False, indent=2)
    
    def _format_compliance_response(
        self,
        compliance_results: List,
        farm_context: Dict[str, Any],
        crop_type: str
    ) -> str:
        """Format comprehensive compliance response"""
        
        # Separate compliant and non-compliant products
        compliant_products = [r for r in compliance_results if r.compliance_result.compliant]
        non_compliant_products = [r for r in compliance_results if not r.compliance_result.compliant]
        
        # Get configuration for additional context
        config = self.config_service.get_regulatory_config()
        
        response = {
            "status": "success",
            "summary": {
                "total_products_found": len(compliance_results),
                "compliant_products": len(compliant_products),
                "non_compliant_products": len(non_compliant_products),
                "search_context": {
                    "crop_type": crop_type,
                    "farm_context_provided": bool(farm_context)
                }
            },
            "compliant_products": [
                self._format_product_info(result, "compliant")
                for result in compliant_products[:5]  # Limit to top 5
            ],
            "non_compliant_products": [
                self._format_product_info(result, "non_compliant")
                for result in non_compliant_products[:3]  # Limit to 3 for reference
            ],
            "general_recommendations": self._get_general_recommendations(farm_context, crop_type),
            "regulatory_context": {
                "znt_requirements": config.get('znt_requirements', {}),
                "seasonal_considerations": self._get_seasonal_considerations(),
                "regional_factors": self._get_regional_factors(farm_context)
            },
            "legal_disclaimer": "⚠️ IMPORTANT: Cette analyse est basée sur les données EPHY officielles mais ne remplace pas l'expertise d'un conseiller agricole. Vérifiez toujours les conditions d'autorisation avant application.",
            "data_source": "EPHY_DATABASE_OFFICIAL",
            "configuration_version": config.get('metadata', {}).get('version', '1.0.0'),
            "timestamp": datetime.now().isoformat()
        }
        
        return json.dumps(response, ensure_ascii=False, indent=2)
    
    def _format_product_info(self, compliance_result, status: str) -> Dict[str, Any]:
        """Format individual product information"""
        product = compliance_result.product
        compliance = compliance_result.compliance_result
        
        # Get main active substances
        substances = []
        for substance_rel in product.substances[:3]:  # Limit to first 3
            substances.append({
                "nom": substance_rel.substance.nom_substance,
                "concentration": f"{substance_rel.concentration_value} {substance_rel.concentration_unit}" if substance_rel.concentration_value else "N/A"
            })
        
        product_info = {
            "numero_amm": product.numero_amm,
            "nom_produit": product.nom_produit,
            "type_produit": product.type_produit.value if product.type_produit else "N/A",
            "titulaire": product.titulaire or "N/A",
            "etat_autorisation": product.etat_autorisation.value if product.etat_autorisation else "N/A",
            "substances_actives": substances,
            "compliance_score": round(compliance.score * 100, 1),
            "status": status
        }
        
        # Add compliance details
        if status == "compliant":
            product_info.update({
                "usage_recommendations": compliance.recommendations[:3],
                "safety_intervals": compliance_result.safety_intervals,
                "znt_requirements": compliance_result.znt_requirements,
                "environmental_considerations": compliance_result.environmental_considerations[:3]
            })
        else:
            product_info.update({
                "violations": compliance.violations,
                "warnings": compliance.warnings,
                "non_compliance_reasons": compliance.violations[:3]
            })
        
        return product_info
    
    def _get_general_recommendations(
        self, 
        farm_context: Dict[str, Any], 
        crop_type: str
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
            safety_intervals = self.config_service.get_safety_intervals(crop_type)
            recommendations.append(
                f"⏰ Délai avant récolte pour {crop_type}: {safety_intervals['pre_harvest_days']} jours minimum"
            )
        
        # Add farm-specific recommendations
        if farm_context:
            if farm_context.get('organic_certified'):
                recommendations.append("🌱 Exploitation bio: vérifiez la compatibilité avec le cahier des charges")
            
            if farm_context.get('distance_to_water_m', 0) < 50:
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
        
        adjustments = self.config_service.get_seasonal_adjustments(season)
        
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
    
    def _get_regional_factors(self, farm_context: Dict[str, Any]) -> Dict[str, Any]:
        """Get regional adjustment factors"""
        if not farm_context or 'region' not in farm_context:
            return {}
        
        region = farm_context['region'].lower()
        factors = self.config_service.get_regional_factors(region)
        
        return {
            "region": region,
            "factors": factors,
            "special_considerations": factors.get('special_restrictions', [])
        }
