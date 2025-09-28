"""
Lookup AMM Tool - Single Purpose Tool

Job: Look up AMM (Autorisation de Mise sur le Marché) information for agricultural products.
Input: product_name, active_ingredient, product_type
Output: JSON string with AMM information

This tool does ONLY:
- Execute specific, well-defined function
- Take structured inputs, return structured outputs
- Contain domain-specific business logic
- Be stateless and reusable

No prompting logic, no orchestration, no agent responsibilities.
"""

from typing import Dict, List, Any, Optional
from langchain.tools import BaseTool
import logging
import json
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class AMMInfo:
    """Structured AMM information."""
    product_name: str
    amm_number: str
    active_ingredient: str
    product_type: str
    authorized_uses: List[str]
    restrictions: List[str]
    safety_measures: List[str]
    validity_period: str

class LookupAMMTool(BaseTool):
    """
    Tool: Look up AMM information for agricultural products.
    
    Job: Take product information and return AMM details.
    Input: product_name, active_ingredient, product_type
    Output: JSON string with AMM information
    """
    
    name: str = "lookup_amm_tool"
    description: str = "Consulte les informations AMM pour les produits agricoles"
    
    def _run(
        self,
        product_name: str = None,
        active_ingredient: str = None,
        product_type: str = None,
        **kwargs
    ) -> str:
        """
        Look up AMM information for agricultural products.
        
        Args:
            product_name: Name of the agricultural product
            active_ingredient: Active ingredient of the product
            product_type: Type of product (herbicide, insecticide, fungicide, etc.)
        """
        try:
            # Get AMM database
            amm_database = self._get_amm_database()
            
            # Search for AMM information
            amm_results = self._search_amm_info(product_name, active_ingredient, product_type, amm_database)
            
            # Calculate search confidence
            search_confidence = self._calculate_search_confidence(amm_results)
            
            result = {
                "search_criteria": {
                    "product_name": product_name,
                    "active_ingredient": active_ingredient,
                    "product_type": product_type
                },
                "amm_results": [asdict(amm_info) for amm_info in amm_results],
                "search_confidence": search_confidence,
                "total_results": len(amm_results)
            }
            
            return json.dumps(result, ensure_ascii=False)
            
        except Exception as e:
            logger.error(f"Lookup AMM error: {e}")
            return json.dumps({"error": f"Erreur lors de la consultation AMM: {str(e)}"})
    
    def _get_amm_database(self) -> Dict[str, Any]:
        """Get AMM database with product information."""
        amm_database = {
            "Roundup": {
                "amm_number": "AMM-2024-001",
                "active_ingredient": "glyphosate",
                "product_type": "herbicide",
                "authorized_uses": ["désherbage_total", "désherbage_sélectif"],
                "restrictions": ["interdiction_usage_public", "dose_maximale_3L_ha"],
                "safety_measures": ["port_EPI", "respect_ZNT", "vent_inférieur_20kmh"],
                "validity_period": "2024-2029"
            },
            "Decis": {
                "amm_number": "AMM-2024-002",
                "active_ingredient": "deltaméthrine",
                "product_type": "insecticide",
                "authorized_uses": ["lutte_insectes", "protection_cultures"],
                "restrictions": ["interdiction_usage_abeilles", "dose_maximale_0.5L_ha"],
                "safety_measures": ["port_EPI", "respect_ZNT", "vent_inférieur_15kmh"],
                "validity_period": "2024-2028"
            },
            "Tilt": {
                "amm_number": "AMM-2024-003",
                "active_ingredient": "propiconazole",
                "product_type": "fongicide",
                "authorized_uses": ["lutte_maladies_fongiques", "protection_céréales"],
                "restrictions": ["dose_maximale_1L_ha", "interdiction_usage_maïs"],
                "safety_measures": ["port_EPI", "respect_ZNT", "vent_inférieur_25kmh"],
                "validity_period": "2024-2027"
            },
            "Azote 46": {
                "amm_number": "AMM-2024-004",
                "active_ingredient": "urée",
                "product_type": "engrais",
                "authorized_uses": ["fertilisation_azotée", "amélioration_rendement"],
                "restrictions": ["dose_maximale_200kg_ha", "interdiction_usage_eau"],
                "safety_measures": ["port_EPI", "stockage_sécurisé", "épandage_contrôlé"],
                "validity_period": "2024-2030"
            },
            "Phosphate 18": {
                "amm_number": "AMM-2024-005",
                "active_ingredient": "phosphate_diammonique",
                "product_type": "engrais",
                "authorized_uses": ["fertilisation_phosphorée", "développement_racinaire"],
                "restrictions": ["dose_maximale_150kg_ha", "interdiction_usage_eau"],
                "safety_measures": ["port_EPI", "stockage_sécurisé", "épandage_contrôlé"],
                "validity_period": "2024-2030"
            }
        }
        
        return amm_database
    
    def _search_amm_info(self, product_name: str = None, active_ingredient: str = None, product_type: str = None, amm_database: Dict[str, Any] = None) -> List[AMMInfo]:
        """Search for AMM information based on criteria."""
        results = []
        
        for product, amm_data in amm_database.items():
            # Check if product matches search criteria
            if self._matches_search_criteria(product, amm_data, product_name, active_ingredient, product_type):
                amm_info = AMMInfo(
                    product_name=product,
                    amm_number=amm_data["amm_number"],
                    active_ingredient=amm_data["active_ingredient"],
                    product_type=amm_data["product_type"],
                    authorized_uses=amm_data["authorized_uses"],
                    restrictions=amm_data["restrictions"],
                    safety_measures=amm_data["safety_measures"],
                    validity_period=amm_data["validity_period"]
                )
                results.append(amm_info)
        
        return results
    
    def _matches_search_criteria(self, product: str, amm_data: Dict[str, Any], product_name: str = None, active_ingredient: str = None, product_type: str = None) -> bool:
        """Check if product matches search criteria."""
        # If no criteria provided, return all products
        if not any([product_name, active_ingredient, product_type]):
            return True
        
        # Check product name match
        if product_name and product_name.lower() not in product.lower():
            return False
        
        # Check active ingredient match
        if active_ingredient and active_ingredient.lower() not in amm_data["active_ingredient"].lower():
            return False
        
        # Check product type match
        if product_type and product_type.lower() not in amm_data["product_type"].lower():
            return False
        
        return True
    
    def _calculate_search_confidence(self, amm_results: List[AMMInfo]) -> str:
        """Calculate search confidence based on results."""
        if not amm_results:
            return "low"
        elif len(amm_results) == 1:
            return "high"
        elif len(amm_results) <= 3:
            return "moderate"
        else:
            return "low"
