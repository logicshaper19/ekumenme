"""
Simple Farm Data Intelligence Agent - Uses LangChain directly without broken base classes.

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

from ..tools.farm_data_agent import (
    get_farm_data_tool,
    calculate_performance_metrics_tool,
    analyze_trends_tool,
    benchmark_crop_performance_tool
)

logger = logging.getLogger(__name__)


class FarmDataIntelligenceAgent:
    """
    Farm Data Intelligence Agent using 4 production-ready tools.
    
    Simple wrapper around LangChain's ReAct agent that:
    - Holds reference to production tools
    - Provides farm data-specific prompt
    - Delegates to LangChain agent executor
    
    Tools:
    - get_farm_data: Retrieve raw farm data with SIRET-based multi-tenancy
    - calculate_performance_metrics: Calculate metrics with statistical analysis
    - analyze_trends: Year-over-year trends with regression analysis
    - benchmark_crop_performance: Compare against industry benchmarks
    """
    
    def __init__(
        self,
        llm: Optional[ChatOpenAI] = None,
        tools: Optional[List] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize Farm Data Intelligence Agent.
        
        Args:
            llm: Language model to use (if None, creates default ChatOpenAI)
            tools: List of tools to use (if None, uses 4 production farm data tools)
            config: Additional configuration (optional)
        """
        # Use provided LLM or create default
        self.llm = llm or ChatOpenAI(
            model="gpt-4",
            temperature=0.1
        )
        
        # Use provided tools or default production tools
        self.tools = tools or [
            get_farm_data_tool,
            calculate_performance_metrics_tool,
            analyze_trends_tool,
            benchmark_crop_performance_tool
        ]
        
        self.config = config or {}
        
        # Create LangChain ReAct agent
        self.agent = self._create_agent()
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=5
        )
        
        logger.info(f"Initialized Farm Data Intelligence Agent with {len(self.tools)} production tools")
    
    def _create_agent(self):
        """Create LangChain ReAct agent with farm data-specific prompt."""
        prompt = self._get_prompt_template()
        return create_react_agent(self.llm, self.tools, prompt)
    
    def _get_prompt_template(self) -> PromptTemplate:
        """Get farm data-specific prompt template for ReAct agent."""
        template = """Tu es un expert en analyse de données agricoles et gestion d'exploitation français.

{context}

Tu as accès à ces outils pour aider les agriculteurs:
{tools}

Noms des outils disponibles: {tool_names}

EXPERTISE:
- Récupération et analyse de données d'exploitation (parcelles, interventions, rendements)
- Calcul de métriques de performance (rendement, coûts, marges)
- Analyse de tendances pluriannuelles (évolution des rendements, des coûts)
- Benchmarking par rapport aux moyennes régionales et nationales

INSTRUCTIONS:
1. Identifie les données nécessaires pour répondre à la question
2. Utilise les outils appropriés pour récupérer et analyser les données
3. Fournis des insights actionnables basés sur les données réelles
4. Compare avec les benchmarks quand pertinent
5. Réponds toujours en français avec un ton professionnel mais accessible

IMPORTANT:
- Demande toujours le SIRET ou l'identifiant d'exploitation
- Vérifie la disponibilité des données avant de faire des analyses
- Utilise les millesimes (années de campagne) pour les analyses temporelles
- Respecte la confidentialité des données d'exploitation

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
        if "siret" in context:
            context_parts.append(f"SIRET: {context['siret']}")
        if "farm_id" in context:
            context_parts.append(f"Exploitation: {context['farm_id']}")
        if "millesime" in context:
            context_parts.append(f"Campagne: {context['millesime']}")
        if "parcelle_id" in context:
            context_parts.append(f"Parcelle: {context['parcelle_id']}")
        
        if context_parts:
            return "CONTEXTE:\n" + "\n".join(f"- {part}" for part in context_parts) + "\n"
        return ""
    
    def _format_result(self, result: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Format agent result into standardized response."""
        return {
            "response": result.get("output", ""),
            "agent_type": "farm_data_intelligence",
            "tools_available": [tool.name for tool in self.tools],
            "context_used": context or {},
            "success": True
        }
    
    async def aprocess(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process user message using production tools (async).
        
        Args:
            message: User message/question
            context: Additional context (siret, farm_id, millesime, etc.)
            
        Returns:
            Dict with response and metadata
        """
        try:
            logger.info(f"Farm Data Agent processing: {message[:100]}...")
            
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
            logger.warning(f"Validation error in Farm Data Agent: {e}")
            return {
                "response": f"Données manquantes ou invalides: {str(e)}",
                "error": str(e),
                "error_type": "validation",
                "agent_type": "farm_data_intelligence",
                "success": False
            }
        except requests.exceptions.RequestException as e:
            # API errors (database unavailable)
            logger.error(f"Database/API error: {e}")
            return {
                "response": "Base de données temporairement indisponible. Veuillez réessayer dans quelques instants.",
                "error": str(e),
                "error_type": "api",
                "agent_type": "farm_data_intelligence",
                "success": False
            }
        except Exception as e:
            # Unexpected errors
            logger.error(f"Unexpected error in Farm Data Agent: {e}", exc_info=True)
            return {
                "response": "Erreur technique inattendue. Veuillez reformuler votre question ou contacter le support.",
                "error": str(e),
                "error_type": "unexpected",
                "agent_type": "farm_data_intelligence",
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
            logger.info(f"Farm Data Agent processing (sync): {message[:100]}...")
            
            # Prepare input with context separated from user message
            agent_input = {
                "input": message,
                "context": self._format_context(context)
            }
            
            # Execute agent synchronously
            result = self.agent_executor.invoke(agent_input)
            
            return self._format_result(result, context)
            
        except ValueError as e:
            logger.warning(f"Validation error in Farm Data Agent: {e}")
            return {
                "response": f"Données manquantes ou invalides: {str(e)}",
                "error": str(e),
                "error_type": "validation",
                "agent_type": "farm_data_intelligence",
                "success": False
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Database/API error: {e}")
            return {
                "response": "Base de données temporairement indisponible. Veuillez réessayer dans quelques instants.",
                "error": str(e),
                "error_type": "api",
                "agent_type": "farm_data_intelligence",
                "success": False
            }
        except Exception as e:
            logger.error(f"Unexpected error in Farm Data Agent: {e}", exc_info=True)
            return {
                "response": "Erreur technique inattendue. Veuillez reformuler votre question ou contacter le support.",
                "error": str(e),
                "error_type": "unexpected",
                "agent_type": "farm_data_intelligence",
                "success": False
            }
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities and metadata."""
        return {
            "agent_type": "farm_data_intelligence",
            "tools": [tool.name for tool in self.tools],
            "capabilities": [
                "farm_data_retrieval",
                "performance_metrics",
                "trend_analysis",
                "benchmarking"
            ],
            "data_sources": ["MesParcelles", "database"],
            "language": "french"
        }

