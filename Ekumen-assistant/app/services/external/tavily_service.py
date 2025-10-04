"""
Tavily Search Service
Provides real-time web search for Internet mode, Supplier mode, and Market prices
"""

import os
import logging
from typing import List, Dict, Optional, Any
from datetime import datetime

try:
    from tavily import TavilyClient
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False
    TavilyClient = None

logger = logging.getLogger(__name__)


class TavilyService:
    """
    Service for integrating Tavily search API
    Use cases:
    - Internet mode: General web search
    - Supplier mode: Find agricultural suppliers
    - Market prices: Real-time commodity prices
    """
    
    def __init__(self):
        if not TAVILY_AVAILABLE:
            logger.warning("Tavily package not installed. Web search features will be disabled.")
            self.client = None
            return

        # Use Pydantic settings instead of direct os.getenv
        from app.core.config import settings
        self.api_key = settings.TAVILY_API_KEY
        if not self.api_key:
            logger.warning("TAVILY_API_KEY not found in environment variables")
            self.client = None
        else:
            self.client = TavilyClient(api_key=self.api_key)
            logger.info("✅ Tavily service initialized")
    
    def is_available(self) -> bool:
        """Check if Tavily service is available"""
        return self.client is not None
    
    async def search_internet(
        self,
        query: str,
        max_results: int = 5,
        include_domains: Optional[List[str]] = None,
        exclude_domains: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        General internet search for Internet mode
        
        Args:
            query: Search query
            max_results: Maximum number of results
            include_domains: List of domains to prioritize
            exclude_domains: List of domains to exclude
            
        Returns:
            Dict with search results and metadata
        """
        if not self.is_available():
            return {
                "success": False,
                "error": "Tavily service not available",
                "results": []
            }
        
        try:
            logger.info(f"🌐 Internet search: {query}")
            
            # Perform search
            response = self.client.search(
                query=query,
                max_results=max_results,
                search_depth="advanced",  # More comprehensive results
                include_domains=include_domains,
                exclude_domains=exclude_domains,
                include_answer=True,  # Get AI-generated answer
                include_raw_content=False  # Don't need full HTML
            )
            
            # Format results
            results = []
            for item in response.get("results", []):
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "content": item.get("content", ""),
                    "score": item.get("score", 0.0)
                })
            
            return {
                "success": True,
                "query": query,
                "answer": response.get("answer", ""),  # AI-generated summary
                "results": results,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Tavily search error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "results": []
            }
    
    async def search_suppliers(
        self,
        query: str,
        location: Optional[str] = None,
        max_results: int = 5
    ) -> Dict[str, Any]:
        """
        Search for agricultural suppliers (Mode Fournisseurs)
        
        Args:
            query: Product or supplier type (e.g., "fournisseur glyphosate")
            location: Location filter (e.g., "Bordeaux", "Nouvelle-Aquitaine")
            max_results: Maximum number of results
            
        Returns:
            Dict with supplier information
        """
        if not self.is_available():
            return {
                "success": False,
                "error": "Tavily service not available",
                "suppliers": []
            }
        
        try:
            # Enhance query with location
            search_query = query
            if location:
                search_query = f"{query} {location} France"
            else:
                search_query = f"{query} France"
            
            logger.info(f"🎁 Supplier search: {search_query}")
            
            # Prioritize French agricultural supplier sites
            include_domains = [
                "agriconomie.com",
                "agrizone.net",
                "terralto.com",
                "agriaffaires.com",
                "pages-jaunes.fr"
            ]
            
            response = self.client.search(
                query=search_query,
                max_results=max_results,
                search_depth="advanced",
                include_domains=include_domains,
                include_answer=True
            )
            
            # Format supplier results
            suppliers = []
            for item in response.get("results", []):
                suppliers.append({
                    "name": item.get("title", ""),
                    "url": item.get("url", ""),
                    "description": item.get("content", ""),
                    "relevance_score": item.get("score", 0.0)
                })
            
            return {
                "success": True,
                "query": search_query,
                "summary": response.get("answer", ""),
                "suppliers": suppliers,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Supplier search error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "suppliers": []
            }
    
    async def search_market_prices(
        self,
        commodity: str,
        region: Optional[str] = None,
        max_results: int = 5
    ) -> Dict[str, Any]:
        """
        Search for agricultural commodity market prices
        
        Args:
            commodity: Commodity name (e.g., "blé", "maïs", "colza")
            region: Region filter (optional)
            max_results: Maximum number of results
            
        Returns:
            Dict with market price information
        """
        if not self.is_available():
            return {
                "success": False,
                "error": "Tavily service not available",
                "prices": []
            }
        
        try:
            # Build market price query
            search_query = f"prix {commodity} agricole France {datetime.now().year}"
            if region:
                search_query += f" {region}"
            
            logger.info(f"💰 Market price search: {search_query}")
            
            # Prioritize French agricultural market sites
            include_domains = [
                "terre-net.fr",
                "lafranceagricole.fr",
                "agri-mutuel.com",
                "agritel.com",
                "euronext.com"
            ]
            
            response = self.client.search(
                query=search_query,
                max_results=max_results,
                search_depth="advanced",
                include_domains=include_domains,
                include_answer=True
            )
            
            # Format price results
            prices = []
            for item in response.get("results", []):
                prices.append({
                    "source": item.get("title", ""),
                    "url": item.get("url", ""),
                    "information": item.get("content", ""),
                    "relevance": item.get("score", 0.0)
                })
            
            return {
                "success": True,
                "commodity": commodity,
                "query": search_query,
                "summary": response.get("answer", ""),
                "prices": prices,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ Market price search error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "prices": []
            }
    
    async def search_news(
        self,
        topic: str,
        max_results: int = 5
    ) -> Dict[str, Any]:
        """
        Search for agricultural news
        
        Args:
            topic: News topic
            max_results: Maximum number of results
            
        Returns:
            Dict with news articles
        """
        if not self.is_available():
            return {
                "success": False,
                "error": "Tavily service not available",
                "news": []
            }
        
        try:
            search_query = f"{topic} agriculture France actualité"
            logger.info(f"📰 News search: {search_query}")
            
            # Prioritize French agricultural news sites
            include_domains = [
                "lafranceagricole.fr",
                "terre-net.fr",
                "agri-mutuel.com",
                "pleinchamp.com",
                "web-agri.fr"
            ]
            
            response = self.client.search(
                query=search_query,
                max_results=max_results,
                search_depth="basic",  # News doesn't need deep search
                include_domains=include_domains,
                include_answer=True
            )
            
            # Format news results
            news = []
            for item in response.get("results", []):
                news.append({
                    "title": item.get("title", ""),
                    "url": item.get("url", ""),
                    "summary": item.get("content", ""),
                    "relevance": item.get("score", 0.0)
                })
            
            return {
                "success": True,
                "topic": topic,
                "summary": response.get("answer", ""),
                "news": news,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ News search error: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "news": []
            }


# Singleton instance
_tavily_service = None

def get_tavily_service() -> TavilyService:
    """Get or create Tavily service singleton"""
    global _tavily_service
    if _tavily_service is None:
        _tavily_service = TavilyService()
    return _tavily_service

