"""
Simple Planning Intelligence Agent - Uses LangChain directly without broken base classes.

This agent:
1. Uses 5 production-ready tools
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

from ..tools.planning_agent import (
    check_crop_feasibility_tool,
    generate_planning_tasks_tool,
    optimize_task_sequence_tool,
    analyze_resource_requirements_tool,
    calculate_planning_costs_tool
)

logger = logging.getLogger(__name__)


class PlanningIntelligenceAgent:
    """
    Planning Intelligence Agent using 5 production-ready tools.
    
    Simple wrapper around LangChain's ReAct agent that:
    - Holds reference to production tools
    - Provides planning-specific prompt
    - Delegates to LangChain agent executor
    
    Tools:
    - check_crop_feasibility: Verify crop suitability for parcelle/region
    - generate_planning_tasks: Generate task list for crop planning
    - optimize_task_sequence: Optimize task order based on constraints
    - analyze_resource_requirements: Calculate resource needs (labor, equipment, inputs)
    - calculate_planning_costs: Estimate costs for planning scenarios
    """
    
    def __init__(
        self,
        llm: Optional[ChatOpenAI] = None,
        tools: Optional[List] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize Planning Intelligence Agent.
        
        Args:
            llm: Language model to use (if None, creates default ChatOpenAI)
            tools: List of tools to use (if None, uses 5 production planning tools)
            config: Additional configuration (optional)
        """
        # Use provided LLM or create default
        self.llm = llm or ChatOpenAI(
            model="gpt-4",
            temperature=0.1
        )
        
        # Use provided tools or default production tools
        self.tools = tools or [
            check_crop_feasibility_tool,
            generate_planning_tasks_tool,
            optimize_task_sequence_tool,
            analyze_resource_requirements_tool,
            calculate_planning_costs_tool
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
        
        logger.info(f"Initialized Planning Intelligence Agent with {len(self.tools)} production tools")
    
    def _create_agent(self):
        """Create LangChain ReAct agent with planning-specific prompt."""
        prompt = self._get_prompt_template()
        return create_react_agent(self.llm, self.tools, prompt)
    
    def _get_prompt_template(self) -> PromptTemplate:
        """Get planning-specific prompt template for ReAct agent."""
        template = """Tu es un expert en planification agricole et gestion d'exploitation français.

{context}

Tu as accès à ces outils pour aider les agriculteurs:
{tools}

Noms des outils disponibles: {tool_names}

EXPERTISE:
- Vérification de faisabilité des cultures (sol, climat, rotation)
- Génération de plans de travail détaillés (semis, traitements, récolte)
- Optimisation de séquences de tâches (contraintes météo, main d'œuvre, équipement)
- Analyse des besoins en ressources (heures de travail, matériel, intrants)
- Estimation des coûts de production (semences, phytos, mécanisation)

INSTRUCTIONS:
1. Comprends l'objectif de planification de l'agriculteur
2. Utilise les outils appropriés pour analyser la faisabilité
3. Génère un plan d'action réaliste et optimisé
4. Fournis des estimations de coûts et de ressources
5. Réponds toujours en français avec un ton professionnel mais accessible

IMPORTANT:
- Vérifie toujours la faisabilité avant de planifier
- Respecte les rotations culturales et les contraintes agronomiques
- Optimise l'utilisation des ressources (main d'œuvre, équipement)
- Fournis des estimations de coûts réalistes
- Prends en compte les contraintes réglementaires (délais de rentrée, ZNT)

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
        if "millesime" in context:
            context_parts.append(f"Campagne: {context['millesime']}")
        if "surface_ha" in context:
            context_parts.append(f"Surface: {context['surface_ha']} ha")
        
        if context_parts:
            return "CONTEXTE:\n" + "\n".join(f"- {part}" for part in context_parts) + "\n"
        return ""
    
    def _format_result(self, result: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Format agent result into standardized response."""
        return {
            "response": result.get("output", ""),
            "agent_type": "planning_intelligence",
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
            logger.info(f"Planning Agent processing: {message[:100]}...")
            
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
            logger.warning(f"Validation error in Planning Agent: {e}")
            return {
                "response": f"Données manquantes ou invalides: {str(e)}",
                "error": str(e),
                "error_type": "validation",
                "agent_type": "planning_intelligence",
                "success": False
            }
        except requests.exceptions.RequestException as e:
            # API errors (database unavailable)
            logger.error(f"Database/API error: {e}")
            return {
                "response": "Base de données temporairement indisponible. Veuillez réessayer dans quelques instants.",
                "error": str(e),
                "error_type": "api",
                "agent_type": "planning_intelligence",
                "success": False
            }
        except Exception as e:
            # Unexpected errors
            logger.error(f"Unexpected error in Planning Agent: {e}", exc_info=True)
            return {
                "response": "Erreur technique inattendue. Veuillez reformuler votre question ou contacter le support.",
                "error": str(e),
                "error_type": "unexpected",
                "agent_type": "planning_intelligence",
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
            logger.info(f"Planning Agent processing (sync): {message[:100]}...")
            
            # Prepare input with context separated from user message
            agent_input = {
                "input": message,
                "context": self._format_context(context)
            }
            
            # Execute agent synchronously
            result = self.agent_executor.invoke(agent_input)
            
            return self._format_result(result, context)
            
        except ValueError as e:
            logger.warning(f"Validation error in Planning Agent: {e}")
            return {
                "response": f"Données manquantes ou invalides: {str(e)}",
                "error": str(e),
                "error_type": "validation",
                "agent_type": "planning_intelligence",
                "success": False
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Database/API error: {e}")
            return {
                "response": "Base de données temporairement indisponible. Veuillez réessayer dans quelques instants.",
                "error": str(e),
                "error_type": "api",
                "agent_type": "planning_intelligence",
                "success": False
            }
        except Exception as e:
            logger.error(f"Unexpected error in Planning Agent: {e}", exc_info=True)
            return {
                "response": "Erreur technique inattendue. Veuillez reformuler votre question ou contacter le support.",
                "error": str(e),
                "error_type": "unexpected",
                "agent_type": "planning_intelligence",
                "success": False
            }
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities and metadata."""
        return {
            "agent_type": "planning_intelligence",
            "tools": [tool.name for tool in self.tools],
            "capabilities": [
                "crop_feasibility",
                "task_planning",
                "sequence_optimization",
                "resource_analysis",
                "cost_estimation"
            ],
            "planning_types": ["crop_planning", "task_scheduling", "resource_planning"],
            "language": "french"
        }

