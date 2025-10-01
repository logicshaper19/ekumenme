"""
Simple Crop Health Intelligence Agent - Uses LangChain directly without broken base classes.

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

from ..tools.crop_health_agent import (
    diagnose_disease_tool,
    identify_pest_tool,
    analyze_nutrient_deficiency_tool,
    generate_treatment_plan_tool
)

logger = logging.getLogger(__name__)


class CropHealthIntelligenceAgent:
    """
    Crop Health Intelligence Agent using 4 production-ready tools.
    
    Simple wrapper around LangChain's ReAct agent that:
    - Holds reference to production tools
    - Provides crop health-specific prompt
    - Delegates to LangChain agent executor
    
    Tools:
    - diagnose_disease: Disease diagnosis with EPPO codes and severity scoring
    - identify_pest: Pest identification with damage assessment
    - analyze_nutrient_deficiency: Nutrient analysis with visual symptom matching
    - generate_treatment_plan: Comprehensive treatment planning with prioritization
    """
    
    def __init__(
        self,
        llm: Optional[ChatOpenAI] = None,
        tools: Optional[List] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize Crop Health Intelligence Agent.
        
        Args:
            llm: Language model to use (if None, creates default ChatOpenAI)
            tools: List of tools to use (if None, uses 4 production crop health tools)
            config: Additional configuration (optional)
        """
        # Use provided LLM or create default
        self.llm = llm or ChatOpenAI(
            model="gpt-4",
            temperature=0.1
        )
        
        # Use provided tools or default production tools
        self.tools = tools or [
            diagnose_disease_tool,
            identify_pest_tool,
            analyze_nutrient_deficiency_tool,
            generate_treatment_plan_tool
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
        
        logger.info(f"Initialized Crop Health Intelligence Agent with {len(self.tools)} production tools")
    
    def _create_agent(self):
        """Create LangChain ReAct agent with crop health-specific prompt."""
        prompt = self._get_prompt_template()
        return create_react_agent(self.llm, self.tools, prompt)
    
    def _get_prompt_template(self) -> PromptTemplate:
        """Get crop health-specific prompt template for ReAct agent."""
        template = """Tu es un expert en santé des cultures et phytopathologie français.

{context}

Tu as accès à ces outils pour aider les agriculteurs:
{tools}

Noms des outils disponibles: {tool_names}

EXPERTISE:
- Diagnostic des maladies des cultures (champignons, bactéries, virus)
- Identification des ravageurs et évaluation des dégâts
- Analyse des carences nutritionnelles (NPK, oligo-éléments)
- Élaboration de plans de traitement intégrés

INSTRUCTIONS:
1. Analyse les symptômes décrits par l'agriculteur
2. Utilise les outils appropriés pour diagnostiquer le problème
3. Fournis des recommandations de traitement conformes à la réglementation française
4. Priorise les solutions biologiques et préventives quand possible
5. Réponds toujours en français avec un ton professionnel mais accessible

IMPORTANT:
- Demande toujours le type de culture et les symptômes précis
- Vérifie les codes EPPO pour les maladies et ravageurs
- Respecte les restrictions d'usage des produits phytosanitaires
- Recommande des méthodes de prévention pour éviter les récidives

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
        if "parcelle_id" in context:
            context_parts.append(f"Parcelle: {context['parcelle_id']}")
        if "crop_type" in context:
            context_parts.append(f"Culture: {context['crop_type']}")
        if "growth_stage" in context:
            context_parts.append(f"Stade de croissance: {context['growth_stage']}")
        
        if context_parts:
            return "CONTEXTE:\n" + "\n".join(f"- {part}" for part in context_parts) + "\n"
        return ""
    
    def _format_result(self, result: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Format agent result into standardized response."""
        return {
            "response": result.get("output", ""),
            "agent_type": "crop_health_intelligence",
            "tools_available": [tool.name for tool in self.tools],
            "context_used": context or {},
            "success": True
        }
    
    async def aprocess(self, message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process user message using production tools (async).
        
        Args:
            message: User message/question
            context: Additional context (farm_id, parcelle_id, crop_type, etc.)
            
        Returns:
            Dict with response and metadata
        """
        try:
            logger.info(f"Crop Health Agent processing: {message[:100]}...")
            
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
            logger.warning(f"Validation error in Crop Health Agent: {e}")
            return {
                "response": f"Données manquantes ou invalides: {str(e)}",
                "error": str(e),
                "error_type": "validation",
                "agent_type": "crop_health_intelligence",
                "success": False
            }
        except requests.exceptions.RequestException as e:
            # API errors (database unavailable)
            logger.error(f"Database/API error: {e}")
            return {
                "response": "Base de données temporairement indisponible. Veuillez réessayer dans quelques instants.",
                "error": str(e),
                "error_type": "api",
                "agent_type": "crop_health_intelligence",
                "success": False
            }
        except Exception as e:
            # Unexpected errors
            logger.error(f"Unexpected error in Crop Health Agent: {e}", exc_info=True)
            return {
                "response": "Erreur technique inattendue. Veuillez reformuler votre question ou contacter le support.",
                "error": str(e),
                "error_type": "unexpected",
                "agent_type": "crop_health_intelligence",
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
            logger.info(f"Crop Health Agent processing (sync): {message[:100]}...")
            
            # Prepare input with context separated from user message
            agent_input = {
                "input": message,
                "context": self._format_context(context)
            }
            
            # Execute agent synchronously
            result = self.agent_executor.invoke(agent_input)
            
            return self._format_result(result, context)
            
        except ValueError as e:
            logger.warning(f"Validation error in Crop Health Agent: {e}")
            return {
                "response": f"Données manquantes ou invalides: {str(e)}",
                "error": str(e),
                "error_type": "validation",
                "agent_type": "crop_health_intelligence",
                "success": False
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Database/API error: {e}")
            return {
                "response": "Base de données temporairement indisponible. Veuillez réessayer dans quelques instants.",
                "error": str(e),
                "error_type": "api",
                "agent_type": "crop_health_intelligence",
                "success": False
            }
        except Exception as e:
            logger.error(f"Unexpected error in Crop Health Agent: {e}", exc_info=True)
            return {
                "response": "Erreur technique inattendue. Veuillez reformuler votre question ou contacter le support.",
                "error": str(e),
                "error_type": "unexpected",
                "agent_type": "crop_health_intelligence",
                "success": False
            }
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities and metadata."""
        return {
            "agent_type": "crop_health_intelligence",
            "tools": [tool.name for tool in self.tools],
            "capabilities": [
                "disease_diagnosis",
                "pest_identification",
                "nutrient_deficiency_analysis",
                "treatment_planning"
            ],
            "supported_crops": "all",  # Tools support all crops in database
            "language": "french"
        }

