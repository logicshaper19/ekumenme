"""
Crop Health Intelligence Agent - Production-ready with sophisticated prompts.

This agent:
1. Uses 4 production-ready crop health tools
2. Leverages LangChain's create_react_agent with ChatPromptTemplate
3. Integrates sophisticated prompts from centralized prompt system
4. Supports dynamic few-shot examples and PromptManager
5. Dependencies injected for testability
6. Production-grade error handling with French localization
"""

import logging
import requests
from typing import Dict, List, Any, Optional
from collections import defaultdict
from langchain.agents import create_react_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI

from ..tools.crop_health_agent import (
    diagnose_disease_tool,
    identify_pest_tool,
    analyze_nutrient_deficiency_tool,
    generate_treatment_plan_tool
)
from ..prompts.crop_health_prompts import get_crop_health_react_prompt
from ..prompts.prompt_manager import PromptManager

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
        config: Optional[Dict[str, Any]] = None,
        prompt_manager: Optional[PromptManager] = None,
        enable_dynamic_examples: bool = False,  # Default to False for token optimization
        max_iterations: int = 10,  # Increased for complex multi-step diagnosis
        enable_metrics: bool = True
    ):
        """
        Initialize Crop Health Intelligence Agent with sophisticated prompts.

        Args:
            llm: Language model to use (if None, creates default ChatOpenAI)
            tools: List of tools to use (if None, uses 4 production crop health tools)
            config: Additional configuration (optional)
            prompt_manager: PromptManager for advanced prompt features (optional)
            enable_dynamic_examples: Whether to include few-shot examples (default False for token optimization)
            max_iterations: Maximum ReAct iterations (default 10 for complex crop health diagnosis)
            enable_metrics: Whether to track performance metrics
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
        self.prompt_manager = prompt_manager or PromptManager()
        self.enable_dynamic_examples = enable_dynamic_examples
        self.max_iterations = max_iterations
        self.enable_metrics = enable_metrics

        # Initialize metrics tracking
        if self.enable_metrics:
            self.metrics = {
                "total_calls": 0,
                "successful_calls": 0,
                "failed_calls": 0,
                "avg_iterations": 0.0,
                "tool_usage": defaultdict(int),
                "error_types": defaultdict(int)
            }

        # Create LangChain ReAct agent with sophisticated prompt
        self.agent = self._create_agent()
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=self.max_iterations,
            max_execution_time=30.0  # 30 seconds timeout to prevent hanging
        )

        logger.info(
            f"✅ Crop Health Intelligence Agent initialized: "
            f"{len(self.tools)} tools, "
            f"max_iterations={self.max_iterations}, "
            f"examples={'enabled' if self.enable_dynamic_examples else 'disabled'}, "
            f"metrics={'enabled' if self.enable_metrics else 'disabled'}"
        )

    def _create_agent(self):
        """Create LangChain ReAct agent with sophisticated crop health prompt."""
        prompt = self._get_prompt_template()
        return create_react_agent(self.llm, self.tools, prompt)

    def _get_prompt_template(self) -> ChatPromptTemplate:
        """
        Get sophisticated crop health-specific prompt template for ReAct agent.

        Uses the centralized prompt system from app/prompts/CropHealth_prompts.py
        which includes:
        - Comprehensive crop health expertise
        - ReAct format instructions
        - Few-shot examples
        - Safety reminders

        Returns:
            ChatPromptTemplate configured for crop health intelligence
        """
        # Get sophisticated prompt from centralized prompt system
        return get_crop_health_react_prompt(include_examples=self.enable_dynamic_examples)
    
    def _update_metrics(
        self,
        success: bool,
        error_type: Optional[str] = None,
        iterations: int = 0,
        tools_used: Optional[List[str]] = None
    ):
        """
        Update performance metrics.

        Args:
            success: Whether the call was successful
            error_type: Type of error if failed (validation, api, unexpected)
            iterations: Number of ReAct iterations used
            tools_used: List of tool names that were used
        """
        if not self.enable_metrics:
            return

        self.metrics["total_calls"] += 1
        if success:
            self.metrics["successful_calls"] += 1
            # Update rolling average of iterations
            total = self.metrics["total_calls"]
            current_avg = self.metrics["avg_iterations"]
            self.metrics["avg_iterations"] = ((current_avg * (total - 1)) + iterations) / total

            # Track tool usage
            if tools_used:
                for tool in tools_used:
                    self.metrics["tool_usage"][tool] += 1
        else:
            self.metrics["failed_calls"] += 1
            if error_type:
                self.metrics["error_types"][error_type] += 1

    def _format_context(self, context: Dict[str, Any]) -> str:
        """
        Format context for prompt injection - robust dynamic handling.

        Handles all context keys dynamically instead of hardcoding specific keys.
        This prevents brittleness when new context keys are added.

        Args:
            context: Dictionary of context information

        Returns:
            Formatted context string for prompt injection
        """
        if not context:
            return ""

        # Define key mappings for French labels (extensible)
        key_labels = {
            "siret": "SIRET",
            "farm_id": "Exploitation",
            "millesime": "Campagne",
            "parcelle_id": "Parcelle",
            "parcel_id": "Parcelle",
            "location": "Localisation",
            "crop_type": "Culture",
            "crop": "Culture",
            "year": "Année",
            "season": "Saison",
            "region": "Région",
            "intervention_type": "Type d'intervention",
            "product_amm": "Code AMM"
        }

        context_parts = []
        for key, value in context.items():
            # Skip None values and empty strings
            if value is None or value == "":
                continue

            # Use mapped label or capitalize key as fallback
            label = key_labels.get(key, key.replace("_", " ").capitalize())
            context_parts.append(f"{label}: {value}")

        if context_parts:
            return "CONTEXTE:\n" + "\n".join(f"- {part}" for part in context_parts) + "\n"
        return ""

    def _format_result(self, result: Dict[str, Any], context: Optional[Dict[str, Any]] = None, iterations: int = 0) -> Dict[str, Any]:
        """
        Format agent result into standardized response.

        Args:
            result: Raw result from agent executor
            context: Context used in the query
            iterations: Number of iterations used

        Returns:
            Standardized response dictionary with:
            - response (str): Agent's response
            - agent_type (str): Type of agent
            - tools_available (List[str]): Available tools
            - tools_used (List[str]): Tools actually used
            - context_used (Dict): Context provided
            - iterations_used (int): Number of ReAct iterations
            - success (bool): Whether call succeeded
        """
        # Extract tools used from intermediate steps
        tools_used = []
        intermediate_steps = result.get("intermediate_steps", [])
        for step in intermediate_steps:
            if len(step) >= 1 and hasattr(step[0], 'tool'):
                tools_used.append(step[0].tool)

        # Update metrics with tool usage
        self._update_metrics(success=True, iterations=iterations, tools_used=tools_used)

        return {
            "response": result.get("output", ""),
            "agent_type": "CropHealth_intelligence",
            "tools_available": [tool.name for tool in self.tools],
            "tools_used": tools_used,
            "context_used": context or {},
            "iterations_used": iterations,
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
            logger.info(f"Crop Health Agent processing: {message[:100]}...")

            # Prepare input with context separated from user message
            agent_input = {
                "input": message,
                "context": self._format_context(context)
            }

            # Execute agent
            result = await self.agent_executor.ainvoke(agent_input)

            # Extract iterations count if available
            iterations = len(result.get("intermediate_steps", []))

            return self._format_result(result, context, iterations)

        except ValueError as e:
            # Validation errors (missing data, invalid input)
            logger.warning(f"Validation error in Crop Health Agent: {e}")
            self._update_metrics(success=False, error_type="validation")
            return {
                "response": (
                    f"Données manquantes ou invalides: {str(e)}. "
                    "Veuillez fournir au moins le SIRET ou l'identifiant de l'exploitation."
                ),
                "error": str(e),
                "error_type": "validation",
                "agent_type": "CropHealth_intelligence",
                "success": False
            }
        except requests.exceptions.RequestException as e:
            # API errors (database unavailable)
            logger.error(f"Database/API error: {e}")
            self._update_metrics(success=False, error_type="api")
            return {
                "response": (
                    "Base de données temporairement indisponible. "
                    "Veuillez réessayer dans quelques instants ou vérifier votre connexion."
                ),
                "error": str(e),
                "error_type": "api",
                "agent_type": "CropHealth_intelligence",
                "success": False
            }
        except Exception as e:
            # Unexpected errors
            logger.error(f"Unexpected error in Crop Health Agent: {e}", exc_info=True)
            self._update_metrics(success=False, error_type="unexpected")
            return {
                "response": (
                    "Erreur technique inattendue. "
                    "Veuillez reformuler votre question ou contacter le support si le problème persiste."
                ),
                "error": str(e),
                "error_type": "unexpected",
                "agent_type": "CropHealth_intelligence",
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

            # Extract iterations count if available
            iterations = len(result.get("intermediate_steps", []))

            return self._format_result(result, context, iterations)

        except ValueError as e:
            logger.warning(f"Validation error in Crop Health Agent: {e}")
            self._update_metrics(success=False, error_type="validation")
            return {
                "response": (
                    f"Données manquantes ou invalides: {str(e)}. "
                    "Veuillez fournir au moins le SIRET ou l'identifiant de l'exploitation."
                ),
                "error": str(e),
                "error_type": "validation",
                "agent_type": "CropHealth_intelligence",
                "success": False
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Database/API error: {e}")
            self._update_metrics(success=False, error_type="api")
            return {
                "response": (
                    "Base de données temporairement indisponible. "
                    "Veuillez réessayer dans quelques instants ou vérifier votre connexion."
                ),
                "error": str(e),
                "error_type": "api",
                "agent_type": "CropHealth_intelligence",
                "success": False
            }
        except Exception as e:
            logger.error(f"Unexpected error in Crop Health Agent: {e}", exc_info=True)
            self._update_metrics(success=False, error_type="unexpected")
            return {
                "response": (
                    "Erreur technique inattendue. "
                    "Veuillez reformuler votre question ou contacter le support si le problème persiste."
                ),
                "error": str(e),
                "error_type": "unexpected",
                "agent_type": "CropHealth_intelligence",
                "success": False
            }
    
    def get_capabilities(self) -> Dict[str, Any]:
        """
        Get agent capabilities and metadata.

        Returns:
            Dict containing:
            - agent_type: Type of agent
            - tools: List of available tools
            - capabilities: List of capabilities
            - data_sources: Data sources used
            - language: Response language
            - configuration: Current configuration settings
        """
        return {
            "agent_type": "CropHealth_intelligence",
            "tools": [tool.name for tool in self.tools],
            "capabilities": [
                "CropHealth_retrieval",
                "disease_identification",
                "pest_identification",
                "treatment_planning",
                "nutrient_analysis"
            ],
            "data_sources": ["diagnostic_tools", "phytosanitary_db"],
            "language": "french",
            "configuration": {
                "max_iterations": self.max_iterations,
                "dynamic_examples": self.enable_dynamic_examples,
                "metrics_enabled": self.enable_metrics,
                "timeout": "30s"
            }
        }

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get performance metrics for the agent.

        Returns:
            Dict containing:
            - metrics_enabled (bool): Whether metrics tracking is enabled
            - total_calls (int): Total number of calls
            - successful_calls (int): Number of successful calls
            - failed_calls (int): Number of failed calls
            - success_rate (float): Success rate percentage
            - avg_iterations (float): Average number of ReAct iterations
            - tool_usage (Dict[str, int]): Count of each tool used
            - error_types (Dict[str, int]): Count of each error type

        Example:
            >>> agent.get_metrics()
            {
                'metrics_enabled': True,
                'total_calls': 10,
                'successful_calls': 8,
                'failed_calls': 2,
                'success_rate': 80.0,
                'avg_iterations': 3.5,
                'tool_usage': {'get_CropHealth': 8, 'calculate_disease_identification': 5},
                'error_types': {'validation': 1, 'api': 1}
            }
        """
        if not self.enable_metrics:
            return {"metrics_enabled": False}

        total = self.metrics["total_calls"]
        success_rate = (self.metrics["successful_calls"] / total * 100) if total > 0 else 0.0

        return {
            "metrics_enabled": True,
            "total_calls": total,
            "successful_calls": self.metrics["successful_calls"],
            "failed_calls": self.metrics["failed_calls"],
            "success_rate": round(success_rate, 2),
            "avg_iterations": round(self.metrics["avg_iterations"], 2),
            "tool_usage": dict(self.metrics["tool_usage"]),
            "error_types": dict(self.metrics["error_types"])
        }

    def reset_metrics(self):
        """Reset all performance metrics to zero."""
        if self.enable_metrics:
            self.metrics = {
                "total_calls": 0,
                "successful_calls": 0,
                "failed_calls": 0,
                "avg_iterations": 0.0,
                "tool_usage": defaultdict(int),
                "error_types": defaultdict(int)
            }
            logger.info("Crop Health Agent metrics reset")

