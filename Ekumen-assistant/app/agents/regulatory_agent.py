"""
Simple Regulatory Intelligence Agent - Uses LangChain directly without broken base classes.

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

from ..tools.regulatory_agent import (
    database_integrated_amm_tool,
    check_regulatory_compliance_tool,
    get_safety_guidelines_tool,
    check_environmental_regulations_tool
)

logger = logging.getLogger(__name__)


class RegulatoryIntelligenceAgent:
    """
    Regulatory Intelligence Agent using 4 production-ready tools.
    
    Simple wrapper around LangChain's ReAct agent that:
    - Holds reference to production tools
    - Provides regulatory-specific prompt
    - Delegates to LangChain agent executor
    
    Tools:
    - lookup_amm_database_enhanced: Look up AMM codes using real EPHY database
    - check_regulatory_compliance: Check compliance with French agricultural regulations
    - get_safety_guidelines: Get safety guidelines with PPE recommendations
    - check_environmental_regulations_enhanced: Check environmental compliance with ZNT zones
    """
    
    def __init__(
        self,
        llm: Optional[ChatOpenAI] = None,
        tools: Optional[List] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize Regulatory Intelligence Agent.
        
        Args:
            llm: Language model to use (if None, creates default ChatOpenAI)
            tools: List of tools to use (if None, uses 4 production regulatory tools)
            config: Additional configuration (optional)
        """
        # Use provided LLM or create default
        self.llm = llm or ChatOpenAI(
            model="gpt-4",
            temperature=0.1
        )
        
        # Use provided tools or default production tools
        self.tools = tools or [
            database_integrated_amm_tool,
            check_regulatory_compliance_tool,
            get_safety_guidelines_tool,
            check_environmental_regulations_tool
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
        
        logger.info(f"Initialized Regulatory Intelligence Agent with {len(self.tools)} production tools")
    
    def _create_agent(self):
        """Create LangChain ReAct agent with regulatory-specific prompt."""
        prompt = self._get_prompt_template()
        return create_react_agent(self.llm, self.tools, prompt)
    
    def _get_prompt_template(self) -> PromptTemplate:
        """Get regulatory-specific prompt template for ReAct agent."""
        template = """Tu es un expert en réglementation agricole française et conformité phytosanitaire.

{context}

Tu as accès à ces outils pour aider les agriculteurs:
{tools}

Noms des outils disponibles: {tool_names}

EXPERTISE:
- Recherche de codes AMM (Autorisation de Mise sur le Marché) dans la base EPHY
- Vérification de conformité réglementaire (délais de rentrée, ZNT, doses homologuées)
- Recommandations de sécurité (EPI, stockage, manipulation)
- Conformité environnementale (zones non traitées, protection des eaux)

INSTRUCTIONS:
1. Identifie le produit phytosanitaire ou la réglementation concernée
2. Utilise les outils appropriés pour vérifier la conformité
3. Fournis des recommandations claires et conformes à la réglementation française
4. Alerte sur les non-conformités et les risques réglementaires
5. Réponds toujours en français avec un ton professionnel et précis

IMPORTANT:
- Vérifie toujours les codes AMM dans la base EPHY officielle
- Respecte strictement les doses homologuées et les délais de rentrée
- Alerte sur les ZNT (Zones Non Traitées) obligatoires
- Recommande les EPI (Équipements de Protection Individuelle) appropriés
- Mentionne les restrictions d'usage et les conditions d'application

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
        if "product_name" in context:
            context_parts.append(f"Produit: {context['product_name']}")
        if "amm_code" in context:
            context_parts.append(f"Code AMM: {context['amm_code']}")
        if "crop_type" in context:
            context_parts.append(f"Culture: {context['crop_type']}")
        if "region" in context:
            context_parts.append(f"Région: {context['region']}")
        
        if context_parts:
            return "CONTEXTE:\n" + "\n".join(f"- {part}" for part in context_parts) + "\n"
        return ""
    
    def _format_result(self, result: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Format agent result into standardized response."""
        return {
            "response": result.get("output", ""),
            "agent_type": "regulatory_intelligence",
            "tools_available": [tool.name for tool in self.tools],
            "context_used": context or {},
            "success": True
        }
    
    async def aprocess(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process user message using production tools (async).
        
        Args:
            message: User message/question
            context: Additional context (product_name, amm_code, crop_type, etc.)
            
        Returns:
            Dict with response and metadata
        """
        try:
            logger.info(f"Regulatory Agent processing: {message[:100]}...")
            
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
            logger.warning(f"Validation error in Regulatory Agent: {e}")
            return {
                "response": f"Données manquantes ou invalides: {str(e)}",
                "error": str(e),
                "error_type": "validation",
                "agent_type": "regulatory_intelligence",
                "success": False
            }
        except requests.exceptions.RequestException as e:
            # API errors (database unavailable)
            logger.error(f"Database/API error: {e}")
            return {
                "response": "Base de données EPHY temporairement indisponible. Veuillez réessayer dans quelques instants.",
                "error": str(e),
                "error_type": "api",
                "agent_type": "regulatory_intelligence",
                "success": False
            }
        except Exception as e:
            # Unexpected errors
            logger.error(f"Unexpected error in Regulatory Agent: {e}", exc_info=True)
            return {
                "response": "Erreur technique inattendue. Veuillez reformuler votre question ou contacter le support.",
                "error": str(e),
                "error_type": "unexpected",
                "agent_type": "regulatory_intelligence",
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
            logger.info(f"Regulatory Agent processing (sync): {message[:100]}...")
            
            # Prepare input with context separated from user message
            agent_input = {
                "input": message,
                "context": self._format_context(context)
            }
            
            # Execute agent synchronously
            result = self.agent_executor.invoke(agent_input)
            
            return self._format_result(result, context)
            
        except ValueError as e:
            logger.warning(f"Validation error in Regulatory Agent: {e}")
            return {
                "response": f"Données manquantes ou invalides: {str(e)}",
                "error": str(e),
                "error_type": "validation",
                "agent_type": "regulatory_intelligence",
                "success": False
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Database/API error: {e}")
            return {
                "response": "Base de données EPHY temporairement indisponible. Veuillez réessayer dans quelques instants.",
                "error": str(e),
                "error_type": "api",
                "agent_type": "regulatory_intelligence",
                "success": False
            }
        except Exception as e:
            logger.error(f"Unexpected error in Regulatory Agent: {e}", exc_info=True)
            return {
                "response": "Erreur technique inattendue. Veuillez reformuler votre question ou contacter le support.",
                "error": str(e),
                "error_type": "unexpected",
                "agent_type": "regulatory_intelligence",
                "success": False
            }
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities and metadata."""
        return {
            "agent_type": "regulatory_intelligence",
            "tools": [tool.name for tool in self.tools],
            "capabilities": [
                "amm_lookup",
                "regulatory_compliance",
                "safety_guidelines",
                "environmental_regulations"
            ],
            "data_sources": ["EPHY", "French regulations"],
            "language": "french"
        }

