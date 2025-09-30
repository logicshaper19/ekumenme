"""
Internet Agent - Powered by Tavily
Handles general web search queries when user activates "Internet" mode
"""

import logging
from typing import Dict, Any, Optional
from app.services.tavily_service import get_tavily_service

logger = logging.getLogger(__name__)


class InternetAgent:
    """
    Agent for handling Internet mode queries
    Uses Tavily to search the web for real-time information
    """
    
    def __init__(self):
        self.tavily = get_tavily_service()
        self.agent_type = "internet"
        self.name = "Agent Internet"
        logger.info("✅ Internet Agent initialized")
    
    async def process(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process an internet search query
        
        Args:
            query: User's search query
            context: Additional context (user info, conversation history, etc.)
            
        Returns:
            Dict with search results formatted for chat response
        """
        logger.info(f"🌐 Internet Agent processing: {query}")
        
        if not self.tavily.is_available():
            return {
                "success": False,
                "response": "❌ Le service de recherche Internet n'est pas disponible actuellement. Veuillez réessayer plus tard.",
                "agent": self.agent_type
            }
        
        try:
            # Detect query type and route accordingly
            query_lower = query.lower()
            
            # Market prices
            if any(word in query_lower for word in ["prix", "cours", "cotation", "marché"]):
                # Extract commodity if possible
                commodity = self._extract_commodity(query_lower)
                if commodity:
                    result = await self.tavily.search_market_prices(
                        commodity=commodity,
                        max_results=5
                    )
                    return self._format_market_response(result)
            
            # News
            if any(word in query_lower for word in ["actualité", "news", "nouveau", "récent"]):
                result = await self.tavily.search_news(
                    topic=query,
                    max_results=5
                )
                return self._format_news_response(result)
            
            # General search
            result = await self.tavily.search_internet(
                query=query,
                max_results=5
            )
            return self._format_general_response(result)
            
        except Exception as e:
            logger.error(f"❌ Internet Agent error: {str(e)}")
            return {
                "success": False,
                "response": f"❌ Erreur lors de la recherche: {str(e)}",
                "agent": self.agent_type
            }
    
    def _extract_commodity(self, query: str) -> Optional[str]:
        """Extract commodity name from query"""
        commodities = {
            "blé": "blé",
            "ble": "blé",
            "wheat": "blé",
            "maïs": "maïs",
            "mais": "maïs",
            "corn": "maïs",
            "colza": "colza",
            "rapeseed": "colza",
            "orge": "orge",
            "barley": "orge",
            "tournesol": "tournesol",
            "sunflower": "tournesol",
            "soja": "soja",
            "soy": "soja"
        }
        
        for key, value in commodities.items():
            if key in query:
                return value
        return None
    
    def _format_general_response(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Format general search results for chat"""
        if not result.get("success"):
            return {
                "success": False,
                "response": f"❌ Erreur: {result.get('error', 'Erreur inconnue')}",
                "agent": self.agent_type
            }
        
        # Build response with AI summary and sources
        response = f"🌐 **Recherche Internet**\n\n"
        
        # Add AI-generated answer if available
        if result.get("answer"):
            response += f"{result['answer']}\n\n"
        
        # Add sources
        if result.get("results"):
            response += "**Sources:**\n"
            for i, item in enumerate(result["results"][:5], 1):
                response += f"{i}. [{item['title']}]({item['url']})\n"
                if item.get("content"):
                    # Truncate content to 150 chars
                    content = item["content"][:150] + "..." if len(item["content"]) > 150 else item["content"]
                    response += f"   {content}\n\n"
        
        return {
            "success": True,
            "response": response,
            "agent": self.agent_type,
            "metadata": {
                "query": result.get("query"),
                "source_count": len(result.get("results", [])),
                "timestamp": result.get("timestamp")
            }
        }
    
    def _format_market_response(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Format market price results for chat"""
        if not result.get("success"):
            return {
                "success": False,
                "response": f"❌ Erreur: {result.get('error', 'Erreur inconnue')}",
                "agent": self.agent_type
            }
        
        response = f"💰 **Prix du marché - {result.get('commodity', 'Produit')}**\n\n"
        
        # Add AI summary
        if result.get("summary"):
            response += f"{result['summary']}\n\n"
        
        # Add price sources
        if result.get("prices"):
            response += "**Sources de prix:**\n"
            for i, item in enumerate(result["prices"][:5], 1):
                response += f"{i}. [{item['source']}]({item['url']})\n"
                if item.get("information"):
                    info = item["information"][:200] + "..." if len(item["information"]) > 200 else item["information"]
                    response += f"   {info}\n\n"
        
        return {
            "success": True,
            "response": response,
            "agent": self.agent_type,
            "metadata": {
                "commodity": result.get("commodity"),
                "source_count": len(result.get("prices", [])),
                "timestamp": result.get("timestamp")
            }
        }
    
    def _format_news_response(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Format news results for chat"""
        if not result.get("success"):
            return {
                "success": False,
                "response": f"❌ Erreur: {result.get('error', 'Erreur inconnue')}",
                "agent": self.agent_type
            }
        
        response = f"📰 **Actualités agricoles**\n\n"
        
        # Add summary
        if result.get("summary"):
            response += f"{result['summary']}\n\n"
        
        # Add news articles
        if result.get("news"):
            response += "**Articles récents:**\n"
            for i, item in enumerate(result["news"][:5], 1):
                response += f"{i}. **{item['title']}**\n"
                response += f"   [{item['url']}]({item['url']})\n"
                if item.get("summary"):
                    summary = item["summary"][:150] + "..." if len(item["summary"]) > 150 else item["summary"]
                    response += f"   {summary}\n\n"
        
        return {
            "success": True,
            "response": response,
            "agent": self.agent_type,
            "metadata": {
                "topic": result.get("topic"),
                "article_count": len(result.get("news", [])),
                "timestamp": result.get("timestamp")
            }
        }

