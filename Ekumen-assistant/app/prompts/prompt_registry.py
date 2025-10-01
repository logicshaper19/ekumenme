"""
Simple Prompt Registry - Clean access to refactored ReAct prompts

Provides a simple, centralized way to access agent prompts.
All prompts follow the gold standard ReAct pattern.
"""

from typing import Optional, Dict, Callable
from langchain.prompts import ChatPromptTemplate
import logging

logger = logging.getLogger(__name__)


class PromptRegistry:
    """
    Simple registry for accessing refactored agent prompts.
    
    All prompts are ReAct-compatible and follow the gold standard pattern:
    - Proper ReAct format (system provides Observation)
    - MessagesPlaceholder for agent_scratchpad
    - Single braces for template variables
    - Concrete multi-step examples
    - Critical rules section
    - Dynamic examples integration
    """
    
    def __init__(self):
        """Initialize the registry with available prompts."""
        self._prompts: Dict[str, Callable] = {}
        self._register_prompts()
    
    def _register_prompts(self):
        """Register all available agent prompts."""
        try:
            from .crop_health_prompts import get_crop_health_react_prompt
            self._prompts["crop_health"] = get_crop_health_react_prompt
        except ImportError as e:
            logger.warning(f"Could not import crop_health prompts: {e}")
        
        try:
            from .weather_prompts import get_weather_react_prompt
            self._prompts["weather"] = get_weather_react_prompt
        except ImportError as e:
            logger.warning(f"Could not import weather prompts: {e}")
        
        try:
            from .farm_data_prompts import get_farm_data_react_prompt
            self._prompts["farm_data"] = get_farm_data_react_prompt
        except ImportError as e:
            logger.warning(f"Could not import farm_data prompts: {e}")
        
        try:
            from .regulatory_prompts import get_regulatory_react_prompt
            self._prompts["regulatory"] = get_regulatory_react_prompt
        except ImportError as e:
            logger.warning(f"Could not import regulatory prompts: {e}")
        
        try:
            from .planning_prompts import get_planning_react_prompt
            self._prompts["planning"] = get_planning_react_prompt
        except ImportError as e:
            logger.warning(f"Could not import planning prompts: {e}")
        
        try:
            from .sustainability_prompts import get_sustainability_react_prompt
            self._prompts["sustainability"] = get_sustainability_react_prompt
        except ImportError as e:
            logger.warning(f"Could not import sustainability prompts: {e}")
        
        try:
            from .orchestrator_prompts import get_orchestrator_react_prompt
            self._prompts["orchestrator"] = get_orchestrator_react_prompt
        except ImportError as e:
            logger.warning(f"Could not import orchestrator prompts: {e}")
    
    def get_prompt(
        self, 
        agent_type: str, 
        include_examples: bool = True
    ) -> Optional[ChatPromptTemplate]:
        """
        Get a ReAct prompt for the specified agent.
        
        Args:
            agent_type: Agent identifier (e.g., "crop_health", "weather")
            include_examples: Whether to include few-shot examples (default True)
            
        Returns:
            ChatPromptTemplate configured for ReAct agent, or None if not found
            
        Example:
            >>> registry = PromptRegistry()
            >>> prompt = registry.get_prompt("crop_health", include_examples=True)
            >>> # Use with create_react_agent
        """
        if agent_type not in self._prompts:
            logger.error(f"Unknown agent type: {agent_type}")
            logger.info(f"Available agents: {list(self._prompts.keys())}")
            return None
        
        try:
            return self._prompts[agent_type](include_examples=include_examples)
        except Exception as e:
            logger.error(f"Error getting prompt for {agent_type}: {e}")
            return None
    
    def list_agents(self) -> list[str]:
        """
        List all available agent types.
        
        Returns:
            List of agent identifiers
        """
        return list(self._prompts.keys())
    
    def is_available(self, agent_type: str) -> bool:
        """
        Check if an agent prompt is available.
        
        Args:
            agent_type: Agent identifier
            
        Returns:
            True if agent is available
        """
        return agent_type in self._prompts


# Global registry instance
_registry = PromptRegistry()


def get_agent_prompt(
    agent_type: str, 
    include_examples: bool = True
) -> Optional[ChatPromptTemplate]:
    """
    Get a ReAct prompt for the specified agent.
    
    Args:
        agent_type: Agent identifier (e.g., "crop_health", "weather", "orchestrator")
        include_examples: Whether to include few-shot examples (default True)
        
    Returns:
        ChatPromptTemplate configured for ReAct agent, or None if not found
        
    Example:
        >>> from prompts.prompt_registry import get_agent_prompt
        >>> prompt = get_agent_prompt("crop_health", include_examples=True)
        >>> 
        >>> # Use with LangChain's create_react_agent
        >>> from langchain.agents import create_react_agent, AgentExecutor
        >>> from langchain_openai import ChatOpenAI
        >>> 
        >>> llm = ChatOpenAI(model="gpt-4", temperature=0)
        >>> agent = create_react_agent(llm, tools, prompt)
        >>> agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)
    """
    return _registry.get_prompt(agent_type, include_examples)


def list_available_agents() -> list[str]:
    """
    List all available agent types.
    
    Returns:
        List of agent identifiers
        
    Example:
        >>> from prompts.prompt_registry import list_available_agents
        >>> agents = list_available_agents()
        >>> print(agents)
        ['crop_health', 'weather', 'farm_data', 'regulatory', 'planning', 'sustainability', 'orchestrator']
    """
    return _registry.list_agents()


def is_agent_available(agent_type: str) -> bool:
    """
    Check if an agent prompt is available.
    
    Args:
        agent_type: Agent identifier
        
    Returns:
        True if agent is available
        
    Example:
        >>> from prompts.prompt_registry import is_agent_available
        >>> if is_agent_available("crop_health"):
        ...     prompt = get_agent_prompt("crop_health")
    """
    return _registry.is_available(agent_type)


__all__ = [
    "PromptRegistry",
    "get_agent_prompt",
    "list_available_agents",
    "is_agent_available",
]

