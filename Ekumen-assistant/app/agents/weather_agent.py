"""
Simple Weather Intelligence Agent - Uses LangChain directly without broken base classes.

This agent:
1. Uses 4 production-ready tools
2. Delegates orchestration to LangChain's create_react_agent
3. No fake object creation
4. No overcomplicated abstractions
5. Dependencies injected, not created
"""

import logging
import requests
from typing import Dict, List, Any, Optional
from langchain.agents import create_react_agent, AgentExecutor
from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI

from ..tools.weather_agent import (
    get_weather_data_tool,
    analyze_weather_risks_tool,
    identify_intervention_windows_tool,
    calculate_evapotranspiration_tool
)

logger = logging.getLogger(__name__)


class WeatherIntelligenceAgent:
    """
    Weather Intelligence Agent using 4 production-ready tools.
    
    Simple wrapper around LangChain's ReAct agent that:
    - Holds reference to production tools
    - Provides weather-specific prompt
    - Delegates to LangChain agent executor
    
    Tools:
    - get_weather_data: Retrieve weather forecasts with dynamic TTL caching
    - analyze_weather_risks: Analyze agricultural risks with severity scoring
    - identify_intervention_windows: Find optimal work windows with confidence scores
    - calculate_evapotranspiration: Calculate FAO-56 evapotranspiration
    """
    
    def __init__(
        self,
        llm: Optional[ChatOpenAI] = None,
        tools: Optional[List] = None,
        weather_api_config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize Weather Intelligence Agent.
        
        Args:
            llm: Language model to use (if None, creates default ChatOpenAI)
            tools: List of tools to use (if None, uses 4 production weather tools)
            weather_api_config: Weather API configuration (optional)
        """
        # Use provided LLM or create default
        self.llm = llm or ChatOpenAI(
            model="gpt-4",
            temperature=0.1
        )
        
        # Use provided tools or default production tools
        self.tools = tools or [
            get_weather_data_tool,
            analyze_weather_risks_tool,
            identify_intervention_windows_tool,
            calculate_evapotranspiration_tool
        ]
        
        self.weather_api_config = weather_api_config
        
        # Create LangChain ReAct agent
        self.agent = self._create_agent()
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5
        )
        
        logger.info(f"Initialized Weather Intelligence Agent with {len(self.tools)} production tools")
    
    def _create_agent(self):
        """Create LangChain ReAct agent with weather-specific prompt."""
        prompt = self._get_prompt_template()
        return create_react_agent(self.llm, self.tools, prompt)
    
    def _get_prompt_template(self) -> PromptTemplate:
        """Get weather-specific prompt template for ReAct agent."""
        template = """Tu es un expert météorologique agricole français.

{context}

Tu as accès à ces outils pour aider les agriculteurs:
{tools}

Noms des outils disponibles: {tool_names}

EXPERTISE:
- Prévisions météorologiques agricoles
- Analyse des risques climatiques (gel, sécheresse, pluie excessive, vent)
- Identification des fenêtres d'intervention optimales
- Calcul de l'évapotranspiration (FAO-56) pour l'irrigation

INSTRUCTIONS:
1. Analyse la question de l'agriculteur
2. Utilise les outils appropriés pour obtenir des données précises
3. Fournis des recommandations concrètes et actionnables
4. Réponds toujours en français avec un ton professionnel mais accessible

Utilise ce format:

Question: la question de l'utilisateur
Thought: réfléchis à ce que tu dois faire
Action: le nom de l'outil à utiliser
Action Input: l'entrée pour l'outil
Observation: le résultat de l'outil
... (répète Thought/Action/Action Input/Observation autant de fois que nécessaire)
Thought: je connais maintenant la réponse finale
Final Answer: la réponse finale en français

Question: {input}

{agent_scratchpad}"""

        return PromptTemplate(
            template=template,
            input_variables=["input", "context", "tools", "tool_names", "agent_scratchpad"]
        )
    
    def _format_context(self, context: Dict[str, Any]) -> str:
        """Format context for prompt injection."""
        if not context:
            return ""

        context_parts = []
        if "farm_id" in context:
            context_parts.append(f"Exploitation: {context['farm_id']}")
        if "location" in context:
            context_parts.append(f"Localisation: {context['location']}")
        if "crop_type" in context:
            context_parts.append(f"Culture: {context['crop_type']}")

        if context_parts:
            return "CONTEXTE:\n" + "\n".join(f"- {part}" for part in context_parts) + "\n"
        return ""

    def _format_result(self, result: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Format agent result into standardized response."""
        return {
            "response": result.get("output", ""),
            "agent_type": "weather_intelligence",
            "tools_available": [tool.name for tool in self.tools],
            "context_used": context or {},
            "success": True
        }

    async def aprocess(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process user message using production tools (async).

        Args:
            message: User message/question
            context: Additional context (farm_id, location, etc.)

        Returns:
            Dict with response and metadata
        """
        try:
            logger.info(f"Weather Agent processing: {message[:100]}...")

            # Prepare input with context separated from user message
            agent_input = {
                "input": message,
                "context": self._format_context(context)
            }

            # Execute agent
            result = await self.agent_executor.ainvoke(agent_input)

            return self._format_result(result, context)

        except ValueError as e:
            # Validation errors (missing data, invalid input)
            logger.warning(f"Validation error in Weather Agent: {e}")
            return {
                "response": f"Données manquantes ou invalides: {str(e)}",
                "error": str(e),
                "error_type": "validation",
                "agent_type": "weather_intelligence",
                "success": False
            }
        except requests.exceptions.RequestException as e:
            # API errors (weather service unavailable)
            logger.error(f"Weather API error: {e}")
            return {
                "response": "Service météo temporairement indisponible. Veuillez réessayer dans quelques instants.",
                "error": str(e),
                "error_type": "api",
                "agent_type": "weather_intelligence",
                "success": False
            }
        except Exception as e:
            # Unexpected errors
            logger.error(f"Unexpected error in Weather Agent: {e}", exc_info=True)
            return {
                "response": "Erreur technique inattendue. Veuillez reformuler votre question ou contacter le support.",
                "error": str(e),
                "error_type": "unexpected",
                "agent_type": "weather_intelligence",
                "success": False
            }
    
    def process(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process user message using production tools (sync).

        Args:
            message: User message/question
            context: Additional context

        Returns:
            Dict with response and metadata
        """
        try:
            logger.info(f"Weather Agent processing (sync): {message[:100]}...")

            # Prepare input with context separated from user message
            agent_input = {
                "input": message,
                "context": self._format_context(context)
            }

            # Execute agent synchronously
            result = self.agent_executor.invoke(agent_input)

            return self._format_result(result, context)

        except ValueError as e:
            logger.warning(f"Validation error in Weather Agent: {e}")
            return {
                "response": f"Données manquantes ou invalides: {str(e)}",
                "error": str(e),
                "error_type": "validation",
                "agent_type": "weather_intelligence",
                "success": False
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Weather API error: {e}")
            return {
                "response": "Service météo temporairement indisponible. Veuillez réessayer dans quelques instants.",
                "error": str(e),
                "error_type": "api",
                "agent_type": "weather_intelligence",
                "success": False
            }
        except Exception as e:
            logger.error(f"Unexpected error in Weather Agent: {e}", exc_info=True)
            return {
                "response": "Erreur technique inattendue. Veuillez reformuler votre question ou contacter le support.",
                "error": str(e),
                "error_type": "unexpected",
                "agent_type": "weather_intelligence",
                "success": False
            }
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities and metadata."""
        return {
            "agent_type": "weather_intelligence",
            "description": "Expert météorologique agricole français",
            "tools": [
                {
                    "name": tool.name,
                    "description": tool.description
                }
                for tool in self.tools
            ],
            "model": self.llm.model_name if hasattr(self.llm, 'model_name') else "unknown",
            "capabilities": [
                "Prévisions météorologiques agricoles",
                "Analyse des risques climatiques",
                "Fenêtres d'intervention optimales",
                "Calcul d'évapotranspiration FAO-56"
            ]
        }


# Alias for backward compatibility
WeatherAgent = WeatherIntelligenceAgent

