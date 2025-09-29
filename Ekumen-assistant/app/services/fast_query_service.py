"""
Fast Query Service for Simple Agricultural Queries
Bypasses complex workflow for simple, direct questions
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
import asyncio

from langchain_openai import ChatOpenAI
from langchain.schema import HumanMessage, SystemMessage

from app.core.config import settings
from app.tools.weather_agent.get_weather_data_tool import GetWeatherDataTool

logger = logging.getLogger(__name__)


class FastQueryService:
    """
    Fast query service that bypasses complex workflows for simple queries
    
    This service provides sub-5-second responses for:
    - Simple weather queries
    - Basic farm data questions
    - Quick regulatory lookups
    """
    
    def __init__(self):
        self.llm = None
        self.weather_tool = GetWeatherDataTool()
        self._initialize()
    
    def _initialize(self):
        """Initialize fast LLM with minimal latency"""
        try:
            # Use GPT-3.5-turbo for speed (10x faster than GPT-4)
            self.llm = ChatOpenAI(
                model_name="gpt-3.5-turbo",
                temperature=0.3,
                max_tokens=500,  # Limit response length for speed
                openai_api_key=settings.OPENAI_API_KEY
            )
            logger.info("Fast query service initialized")
        except Exception as e:
            logger.error(f"Failed to initialize fast query service: {e}")
    
    def should_use_fast_path(self, query: str) -> bool:
        """
        Determine if query can use fast path

        Fast path criteria:
        - Single, simple question
        - No complex reasoning required
        - Direct data lookup
        """
        query_lower = query.lower()

        # Simple weather queries
        weather_keywords = ['météo', 'temps', 'température', 'pluie', 'vent', 'soleil', 'pleuvoir', 'neiger']
        if any(word in query_lower for word in weather_keywords):
            # Check if it's a simple query (not complex analysis)
            complex_keywords = ['analyse', 'comparaison', 'prévision long terme', 'tendance', 'historique', 'dernières années']
            if not any(word in query_lower for word in complex_keywords):
                return True

        # Simple location queries
        if 'où' in query_lower or 'quelle ville' in query_lower:
            return True

        # Simple yes/no questions about weather
        if any(starter in query_lower for starter in ['est-ce que', 'est-ce qu', 'peut-on', 'dois-je', 'faut-il', 'va-t-il']):
            if any(word in query_lower for word in weather_keywords):
                return True

        return False
    
    async def process_fast_query(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process query using fast path
        
        Returns response in < 5 seconds
        """
        try:
            start_time = datetime.now()
            
            # Classify query type
            query_type = self._classify_query(query)
            
            # Route to appropriate fast handler
            if query_type == "weather":
                result = await self._handle_weather_query(query, context)
            elif query_type == "simple":
                result = await self._handle_simple_query(query, context)
            else:
                result = await self._handle_generic_query(query, context)
            
            # Add timing metadata
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            result["metadata"]["fast_path"] = True
            result["metadata"]["duration_seconds"] = duration
            result["metadata"]["query_type"] = query_type
            
            logger.info(f"Fast query processed in {duration:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"Fast query processing failed: {e}")
            return {
                "response": f"Désolé, une erreur s'est produite: {str(e)}",
                "agent_type": "error",
                "confidence": 0.0,
                "metadata": {
                    "fast_path": True,
                    "error": str(e)
                }
            }
    
    def _classify_query(self, query: str) -> str:
        """Classify query type for fast routing"""
        query_lower = query.lower()
        
        # Weather queries
        if any(word in query_lower for word in ['météo', 'temps', 'température', 'pluie', 'vent']):
            return "weather"
        
        # Simple factual queries
        if any(word in query_lower for word in ['où', 'quand', 'combien', 'quel']):
            return "simple"
        
        return "generic"
    
    async def _handle_weather_query(
        self,
        query: str,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Handle weather query with direct tool call"""
        try:
            # Extract location from query or context
            location = self._extract_location(query, context)
            
            # Get weather data directly
            weather_data = await self.weather_tool._arun(location=location)
            
            # Generate concise response
            system_prompt = """Tu es un assistant agricole rapide et concis.
Réponds en 2-3 phrases maximum.
N'utilise AUCUN emoji.
N'utilise JAMAIS de ## ou ### pour les titres.
Utilise **Titre en Gras:** pour les sections si nécessaire.
Utilise des listes à puces (- ) pour les recommandations.
Concentre-toi sur l'essentiel."""
            
            user_prompt = f"""Question: {query}

Données météo pour {location}:
{weather_data}

Réponds de manière concise et pratique."""
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=user_prompt)
            ]
            
            response = await self.llm.ainvoke(messages)
            
            return {
                "response": response.content,
                "agent_type": "weather",
                "confidence": 0.9,
                "weather_data": weather_data,
                "metadata": {
                    "location": location,
                    "tool_used": "weather_data"
                }
            }
            
        except Exception as e:
            logger.error(f"Weather query failed: {e}")
            raise
    
    async def _handle_simple_query(
        self,
        query: str,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Handle simple factual query"""
        try:
            system_prompt = """Tu es un assistant agricole rapide.
Réponds en 1-2 phrases maximum.
N'utilise AUCUN emoji.
N'utilise JAMAIS de ## ou ### pour les titres.
Utilise **gras** pour les points clés.
Sois direct et précis."""
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=query)
            ]
            
            response = await self.llm.ainvoke(messages)
            
            return {
                "response": response.content,
                "agent_type": "general",
                "confidence": 0.7,
                "metadata": {}
            }
            
        except Exception as e:
            logger.error(f"Simple query failed: {e}")
            raise
    
    async def _handle_generic_query(
        self,
        query: str,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Handle generic query with fast LLM"""
        try:
            system_prompt = """Tu es un assistant agricole expert.
Réponds de manière concise mais complète.
Maximum 4-5 phrases.
N'utilise AUCUN emoji.
N'utilise JAMAIS de ## ou ### pour les titres.
Utilise **Titre en Gras:** pour les sections si nécessaire.
Utilise des listes à puces (- ) pour les recommandations."""
            
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=query)
            ]
            
            response = await self.llm.ainvoke(messages)
            
            return {
                "response": response.content,
                "agent_type": "general",
                "confidence": 0.6,
                "metadata": {}
            }
            
        except Exception as e:
            logger.error(f"Generic query failed: {e}")
            raise
    
    def _extract_location(
        self,
        query: str,
        context: Optional[Dict[str, Any]]
    ) -> str:
        """Extract location from query or context"""
        # Check context first
        if context:
            if "location" in context:
                return context["location"]
            if "farm_location" in context:
                return context["farm_location"]
        
        # Try to extract from query
        query_lower = query.lower()
        
        # Common French cities
        cities = [
            'paris', 'lyon', 'marseille', 'toulouse', 'nice', 'nantes',
            'strasbourg', 'montpellier', 'bordeaux', 'lille', 'rennes',
            'reims', 'le havre', 'saint-étienne', 'toulon', 'grenoble',
            'dijon', 'angers', 'nîmes', 'villeurbanne', 'clermont-ferrand',
            'dourdan', 'étampes', 'arpajon', 'corbeil-essonnes'
        ]
        
        for city in cities:
            if city in query_lower:
                return city.title()
        
        # Default location
        return "Paris"
    
    async def stream_fast_response(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ):
        """Stream fast response token by token"""
        try:
            # Get full response first (fast)
            result = await self.process_fast_query(query, context)
            
            # Stream the response word by word for UX
            response_text = result["response"]
            words = response_text.split()
            
            # Send start message
            yield {
                "type": "fast_start",
                "message": "⚡ Réponse rapide...",
                "timestamp": datetime.now().isoformat()
            }
            
            # Stream words
            partial = ""
            for word in words:
                partial += word + " "
                yield {
                    "type": "token",
                    "token": word + " ",
                    "partial_response": partial.strip(),
                    "timestamp": datetime.now().isoformat()
                }
                await asyncio.sleep(0.02)  # Small delay for streaming effect
            
            # Send final result
            yield {
                "type": "workflow_result",
                "response": response_text,
                "agent_type": result["agent_type"],
                "confidence": result["confidence"],
                "metadata": result["metadata"],
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Fast streaming failed: {e}")
            yield {
                "type": "error",
                "message": f"Erreur: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }

