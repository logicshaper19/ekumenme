"""
Supplier Agent - Powered by Tavily
Handles supplier search queries when user activates "Mode Fournisseurs"
"""

import logging
import re
from typing import Dict, Any, Optional, List
from app.services.tavily_service import get_tavily_service

logger = logging.getLogger(__name__)


class SupplierAgent:
    """
    Agent for handling Supplier mode queries
    Uses Tavily to find agricultural suppliers, products, and services
    """
    
    def __init__(self):
        self.tavily = get_tavily_service()
        self.agent_type = "supplier"
        self.name = "Agent Fournisseurs"
        logger.info("✅ Supplier Agent initialized")
    
    async def process(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a supplier search query
        
        Args:
            query: User's supplier search query
            context: Additional context (user location, farm info, etc.)
            
        Returns:
            Dict with supplier results formatted for chat response
        """
        logger.info(f"🎁 Supplier Agent processing: {query}")
        
        if not self.tavily.is_available():
            return {
                "success": False,
                "response": "❌ Le service de recherche de fournisseurs n'est pas disponible actuellement. Veuillez réessayer plus tard.",
                "agent": self.agent_type
            }
        
        try:
            # Extract location from query or context
            location = self._extract_location(query)
            if not location and context:
                # Try to get location from user context
                location = context.get("user_region") or context.get("user_department")
            
            # Enhance query for supplier search
            enhanced_query = self._enhance_supplier_query(query)
            
            # Search for suppliers
            result = await self.tavily.search_suppliers(
                query=enhanced_query,
                location=location,
                max_results=8  # More results for suppliers
            )
            
            return self._format_supplier_response(result, query)
            
        except Exception as e:
            logger.error(f"❌ Supplier Agent error: {str(e)}")
            return {
                "success": False,
                "response": f"❌ Erreur lors de la recherche de fournisseurs: {str(e)}",
                "agent": self.agent_type
            }
    
    def _extract_location(self, query: str) -> Optional[str]:
        """Extract location from query"""
        # Common French location patterns
        location_patterns = [
            r"(?:à|a|près de|proche de|autour de)\s+([A-Z][a-zéèêàâôûù\-]+(?:\s+[A-Z][a-zéèêàâôûù\-]+)?)",
            r"([A-Z][a-zéèêàâôûù\-]+(?:\s+[A-Z][a-zéèêàâôûù\-]+)?)\s+\d{5}",  # City with postal code
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, query)
            if match:
                return match.group(1)
        
        # Check for department numbers
        dept_match = re.search(r"\b(\d{2})\b", query)
        if dept_match:
            return f"département {dept_match.group(1)}"
        
        return None
    
    def _enhance_supplier_query(self, query: str) -> str:
        """Enhance query for better supplier search results"""
        query_lower = query.lower()
        
        # Add "fournisseur" if not present
        if "fournisseur" not in query_lower and "vendeur" not in query_lower:
            # Check if it's a product query
            products = [
                "semence", "engrais", "phyto", "pesticide", "herbicide",
                "tracteur", "matériel", "équipement", "pièce",
                "glyphosate", "roundup", "azote", "potasse"
            ]
            
            for product in products:
                if product in query_lower:
                    return f"fournisseur {query}"
        
        return query
    
    def _format_supplier_response(
        self,
        result: Dict[str, Any],
        original_query: str
    ) -> Dict[str, Any]:
        """Format supplier search results for chat"""
        if not result.get("success"):
            return {
                "success": False,
                "response": f"❌ Erreur: {result.get('error', 'Erreur inconnue')}",
                "agent": self.agent_type
            }
        
        response = f"🎁 **Recherche de fournisseurs**\n\n"
        
        # Add AI summary if available
        if result.get("summary"):
            response += f"**Résumé:**\n{result['summary']}\n\n"
        
        # Add supplier results
        suppliers = result.get("suppliers", [])
        if suppliers:
            response += f"**{len(suppliers)} fournisseur(s) trouvé(s):**\n\n"
            
            for i, supplier in enumerate(suppliers, 1):
                response += f"**{i}. {supplier['name']}**\n"
                response += f"   🔗 [{supplier['url']}]({supplier['url']})\n"
                
                if supplier.get("description"):
                    # Truncate description
                    desc = supplier["description"]
                    if len(desc) > 200:
                        desc = desc[:200] + "..."
                    response += f"   📝 {desc}\n"
                
                # Add relevance indicator
                score = supplier.get("relevance_score", 0)
                if score > 0.8:
                    response += f"   ⭐ Très pertinent\n"
                elif score > 0.6:
                    response += f"   ✓ Pertinent\n"
                
                response += "\n"
        else:
            response += "❌ Aucun fournisseur trouvé pour cette recherche.\n\n"
            response += "**Suggestions:**\n"
            response += "- Essayez d'élargir votre recherche\n"
            response += "- Vérifiez l'orthographe du produit\n"
            response += "- Ajoutez une localisation (ville, département)\n"
        
        # Add helpful tips
        response += "\n---\n"
        response += "💡 **Conseils:**\n"
        response += "- Contactez plusieurs fournisseurs pour comparer les prix\n"
        response += "- Vérifiez les certifications et autorisations\n"
        response += "- Demandez les délais de livraison\n"
        
        return {
            "success": True,
            "response": response,
            "agent": self.agent_type,
            "metadata": {
                "query": result.get("query"),
                "supplier_count": len(suppliers),
                "timestamp": result.get("timestamp"),
                "original_query": original_query
            }
        }
    
    async def search_product_availability(
        self,
        product_name: str,
        location: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Search for product availability at suppliers
        
        Args:
            product_name: Name of the product
            location: Location to search near
            
        Returns:
            Dict with availability information
        """
        query = f"disponibilité {product_name} agricole"
        if location:
            query += f" {location}"
        
        return await self.process(query)
    
    async def compare_suppliers(
        self,
        product_name: str,
        location: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Compare suppliers for a specific product
        
        Args:
            product_name: Name of the product
            location: Location to search near
            
        Returns:
            Dict with comparison information
        """
        query = f"comparaison prix {product_name} fournisseurs agricoles"
        if location:
            query += f" {location}"
        
        return await self.process(query)

