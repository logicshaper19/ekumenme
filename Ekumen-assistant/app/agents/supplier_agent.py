"""
Simplified Supplier Agent - Phase 1: Discovery Only
Focused on supplier discovery and research using Tavily
"""

import logging
from typing import Dict, Any, Optional
from app.services.tavily_service import get_tavily_service

logger = logging.getLogger(__name__)


class SupplierAgent:
    """
    Simplified Agent for supplier discovery (Phase 1)
    Focus: Find suppliers using Tavily search
    Future: Will integrate with database in Phase 2
    
    Phase 2 Integration Points:
    - self.db: Database session for supplier data
    - self._get_verified_suppliers(): Query verified suppliers from database
    - self._get_pricing_data(): Get real-time pricing from supplier APIs
    - self._get_inventory_levels(): Check product availability
    """
    
    def __init__(self, db_session=None):
        self.tavily = get_tavily_service()
        self.db = db_session  # Phase 2: Database integration
        self.agent_type = "supplier"
        self.name = "Agent Fournisseurs"
        logger.info("Simplified Supplier Agent initialized")
    
    # Phase 2 Integration Hooks
    async def _get_verified_suppliers(self, product_category: str, region: str = None) -> list:
        """
        Phase 2: Get verified suppliers from database
        This method will be implemented when suppliers onboard
        """
        # TODO: Implement database query for verified suppliers
        # Example: SELECT * FROM suppliers WHERE category = ? AND region = ?
        return []
    
    async def _get_pricing_data(self, supplier_id: str, product_id: str) -> dict:
        """
        Phase 2: Get real-time pricing from supplier APIs
        This method will integrate with supplier pricing APIs
        """
        # TODO: Implement API calls to supplier pricing systems
        return {"price": None, "currency": "EUR", "available": False}
    
    async def _get_inventory_levels(self, supplier_id: str, product_id: str) -> dict:
        """
        Phase 2: Check product availability and lead times
        This method will integrate with supplier inventory systems
        """
        # TODO: Implement API calls to supplier inventory systems
        return {"available": False, "quantity": 0, "lead_time_days": None}
    
    async def find_suppliers(self, query: str, context: dict = None) -> Dict[str, Any]:
        """
        Find suppliers using Tavily search
        
        Args:
            query: User's supplier search query
            context: Additional context (not used in Phase 1)
            
        Returns:
            Dict with supplier results or error information
        """
        logger.info(f"Supplier Agent processing: {query}")

        if not self.tavily.is_available():
            return {
                "success": False,
                "response": "Le service de recherche de fournisseurs n'est pas disponible actuellement.",
                "agent": self.agent_type,
                "sources": []
            }
        
        try:
            # Enhance query for agricultural context
            enhanced_query = self._enhance_query(query)
            
            # Search suppliers
            result = await self.tavily.search_suppliers(enhanced_query, max_results=6)
            
            if result.get("success"):
                suppliers = result.get("suppliers", [])
                return {
                    "success": True,
                    "response": self._format_response(suppliers, query),
                    "agent": self.agent_type,
                    "sources": self._format_sources(suppliers),
                    "metadata": {
                        "query": query,
                        "supplier_count": len(suppliers),
                        "enhanced_query": enhanced_query
                    }
                }
            else:
                return {
                    "success": False,
                    "response": f"Erreur de recherche: {result.get('error', 'Erreur inconnue')}",
                    "agent": self.agent_type,
                    "sources": []
                }
                
        except Exception as e:
            logger.error(f"Supplier Agent error: {str(e)}")
            return {
                "success": False,
                "response": f"Erreur lors de la recherche: {str(e)}",
                "agent": self.agent_type,
                "sources": []
            }
    
    def _enhance_query(self, query: str) -> str:
        """Add agricultural context to improve search results"""
        enhanced = query.lower()
        
        # Add product-specific context
        if any(word in enhanced for word in ['fertilizer', 'engrais', 'azote', 'potasse']):
            enhanced += " distributeur agricole"
        elif any(word in enhanced for word in ['seed', 'semence', 'graine']):
            enhanced += " semencier agréé"
        elif any(word in enhanced for word in ['tracteur', 'equipment', 'matériel']):
            enhanced += " concessionnaire agricole"
        elif any(word in enhanced for word in ['pesticide', 'herbicide', 'phyto']):
            enhanced += " distributeur agréé"
        
        # Add regional context
        enhanced += " France professionnel"
        
        return enhanced
    
    def _format_response(self, suppliers: list, original_query: str) -> str:
        """Format supplier response for chat"""
        if not suppliers:
            return f"Aucun fournisseur trouvé pour '{original_query}'. Essayez des termes plus généraux ou ajoutez une localisation."
        
        response = f"**🔍 Fournisseurs trouvés pour: {original_query}**\n\n"
        
        for i, supplier in enumerate(suppliers[:5], 1):
            response += f"**{i}. {supplier.get('name', 'N/A')}**\n"
            response += f"   📝 {supplier.get('description', '')[:150]}...\n"
            response += f"   🔗 {supplier.get('url', 'N/A')}\n\n"
        
        response += "**💡 Conseil:** Contactez plusieurs fournisseurs pour comparer les prix et conditions."
        return response
    
    def _format_sources(self, suppliers: list) -> list:
        """Format sources for frontend display"""
        sources = []
        for supplier in suppliers:
            sources.append({
                "title": supplier.get("name", "Source web"),
                "url": supplier.get("url", ""),
                "snippet": supplier.get("description", "")[:200] if supplier.get("description") else "",
                "relevance": supplier.get("relevance_score", 0.0),
                "type": "web"
            })
        return sources
    
    # Legacy methods for backward compatibility
    async def process(self, query: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Legacy method - redirects to find_suppliers"""
        return await self.find_suppliers(query, context)
    
    async def search_product_availability(self, product_name: str, location: Optional[str] = None) -> Dict[str, Any]:
        """Search for product availability at suppliers"""
        query = f"disponibilité {product_name} agricole"
        if location:
            query += f" {location}"
        return await self.find_suppliers(query)
    
    async def compare_suppliers(self, product_name: str, location: Optional[str] = None) -> Dict[str, Any]:
        """Compare suppliers for a specific product"""
        query = f"comparaison prix {product_name} fournisseurs agricoles"
        if location:
            query += f" {location}"
        return await self.find_suppliers(query)