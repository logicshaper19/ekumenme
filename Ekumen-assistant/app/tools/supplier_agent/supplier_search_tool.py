"""
Simplified Supplier Search Tool
Focused LangChain tool for agricultural supplier discovery
"""

import asyncio
import logging
from typing import Dict, Any, List
from langchain.tools import BaseTool

from app.services.tavily_service import get_tavily_service

logger = logging.getLogger(__name__)


class SupplierSearchTool(BaseTool):
    """
    Simplified LangChain tool for finding agricultural suppliers
    Focus: Discovery and research only (Phase 1)
    """
    
    name: str = "find_agricultural_suppliers"
    description: str = """Find agricultural suppliers for products and services.
    
    Use for: seeds, fertilizers, equipment, pesticides, machinery
    Input: Product or service description
    Example: "fournisseur engrais azoté", "distributeur tracteur"
    """
    
    tavily: Any = None
    _last_sources: List[Dict[str, Any]] = []
    
    def __init__(self):
        super().__init__()
        self.tavily = get_tavily_service()
        self._last_sources = []  # Thread-safe source storage for current request
    
    def _run(self, query: str) -> str:
        """Execute supplier search - simplified approach"""
        try:
            logger.info(f"SupplierSearchTool: {query}")
            
            # Enhanced query for agricultural context
            enhanced_query = self._enhance_query(query)
            
            # Use synchronous approach to avoid event loop issues
            result = self._search_suppliers_sync(enhanced_query)
            
            if result.get("success"):
                suppliers = result.get("suppliers", [])
                self._last_sources = suppliers  # Store for source extraction
                
                if suppliers:
                    response = f"## 🔍 Fournisseurs trouvés pour: {query}\n\n"
                    
                    for i, supplier in enumerate(suppliers[:5], 1):
                        name = supplier.get('name', 'N/A')
                        description = supplier.get('description', '')
                        url = supplier.get('url', 'N/A')
                        
                        # Clean up the description
                        if description:
                            # Remove excessive whitespace and truncate intelligently
                            description = ' '.join(description.split())
                            if len(description) > 180:
                                description = description[:180] + "..."
                        
                        response += f"### {i}. {name}\n\n"
                        if description:
                            response += f"📝 **Description:** {description}\n\n"
                        if url != 'N/A':
                            response += f"🔗 **Site web:** [Visiter le site]({url})\n\n"
                        response += "---\n\n"
                    
                    response += "### 💡 Conseils d'achat\n\n"
                    response += "• Contactez plusieurs fournisseurs pour comparer les prix\n"
                    response += "• Vérifiez les garanties et services après-vente\n"
                    response += "• Demandez des devis détaillés avant de décider\n"
                    response += "• Considérez la proximité géographique pour l'entretien"
                    
                    return response
                else:
                    return f"Aucun fournisseur trouvé pour '{query}'. Essayez des termes plus généraux ou ajoutez une localisation."
            else:
                return f"Erreur de recherche: {result.get('error', 'Erreur inconnue')}"
                
        except Exception as e:
            logger.error(f"SupplierSearchTool error: {str(e)}")
            return f"Erreur lors de la recherche: {str(e)}"
    
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
    
    def _search_suppliers_sync(self, query: str) -> Dict[str, Any]:
        """Search suppliers using Tavily - synchronous version"""
        try:
            # Use asyncio.run in a new thread to avoid event loop conflicts
            import concurrent.futures
            import threading
            
            def run_async_search():
                return asyncio.run(self.tavily.search_suppliers(query, max_results=6))
            
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(run_async_search)
                return future.result(timeout=30)  # 30 second timeout
                
        except Exception as e:
            logger.error(f"Tavily search error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    async def _search_suppliers(self, query: str) -> Dict[str, Any]:
        """Search suppliers using Tavily - async version (kept for compatibility)"""
        try:
            return await self.tavily.search_suppliers(query, max_results=6)
        except Exception as e:
            logger.error(f"Tavily search error: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_last_sources(self) -> List[Dict[str, Any]]:
        """
        Get sources from last search - for integration with LCEL
        Note: This is request-scoped and thread-safe for current implementation
        Phase 2: Will integrate with database for persistent source tracking
        """
        return self._last_sources