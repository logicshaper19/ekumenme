"""
Enhanced Supplier Search Tool
Modern LangChain tool for agricultural supplier discovery with structured output
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from langchain_core.tools import StructuredTool

from app.services.tavily_service import get_tavily_service
from app.tools.schemas.supplier_schemas import (
    SupplierSearchInput, SupplierSearchOutput, SupplierInfo
)

logger = logging.getLogger(__name__)


class SupplierSearchService:
    """
    Service for finding agricultural suppliers with structured output
    """
    
    def __init__(self):
        self.tavily = get_tavily_service()
        self._last_sources: List[Dict[str, Any]] = []
    
    async def search_suppliers(
        self,
        query: str
    ) -> SupplierSearchOutput:
        """
        Search for agricultural suppliers with structured output
        
        Args:
            query: Search query for suppliers
            
        Returns:
            SupplierSearchOutput with structured results
        """
        try:
            logger.info(f"SupplierSearchService: {query}")
            
            # Enhanced query for agricultural context
            enhanced_query = self._enhance_query(query)
            
            # Search suppliers using Tavily
            result = await self.tavily.search_suppliers(enhanced_query, max_results=6)
            
            if result.get("success"):
                suppliers_data = result.get("suppliers", [])
                self._last_sources = suppliers_data
                
                # Convert to structured format
                suppliers = []
                for supplier_data in suppliers_data:
                    supplier = SupplierInfo(
                        name=supplier_data.get('name', 'N/A'),
                        description=supplier_data.get('description', ''),
                        url=supplier_data.get('url', 'N/A'),
                        location=supplier_data.get('location'),
                        contact_info=supplier_data.get('contact_info'),
                        specialties=supplier_data.get('specialties')
                    )
                    suppliers.append(supplier)
                
                return SupplierSearchOutput(
                    success=True,
                    query=query,
                    suppliers=suppliers,
                    total_found=len(suppliers),
                    search_tips=[
                        "Contactez plusieurs fournisseurs pour comparer les prix",
                        "Vérifiez les garanties et services après-vente",
                        "Demandez des devis détaillés avant de décider",
                        "Considérez la proximité géographique pour l'entretien"
                    ]
                )
            else:
                return SupplierSearchOutput(
                    success=False,
                    query=query,
                    suppliers=[],
                    total_found=0,
                    search_tips=[],
                    error=result.get('error', 'Erreur inconnue')
                )
                
        except Exception as e:
            logger.error(f"SupplierSearchService error: {str(e)}")
            return SupplierSearchOutput(
                success=False,
                query=query,
                suppliers=[],
                total_found=0,
                search_tips=[],
                error=f"Erreur lors de la recherche: {str(e)}"
            )
    
    def get_last_sources(self) -> List[Dict[str, Any]]:
        """
        Get sources from last search - for integration with LCEL
        """
        return self._last_sources
    
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


# Create service instance
_supplier_service = SupplierSearchService()


# Async wrapper function
async def search_suppliers_async(query: str) -> SupplierSearchOutput:
    """Async wrapper for supplier search"""
    return await _supplier_service.search_suppliers(query)


# Create StructuredTool
supplier_search_tool = StructuredTool.from_function(
    coroutine=search_suppliers_async,
    name="find_agricultural_suppliers",
    description="""
    Find agricultural suppliers for products and services.
    
    Use for: seeds, fertilizers, equipment, pesticides, machinery
    Input: Product or service description
    Example: "fournisseur engrais azoté", "distributeur tracteur"
    
    Returns structured data with supplier information, contact details, and search tips.
    """,
    args_schema=SupplierSearchInput,
    return_direct=False,
    handle_validation_error=True
)