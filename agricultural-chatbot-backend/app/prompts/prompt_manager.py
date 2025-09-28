"""
Prompt Manager - Versioning and A/B Testing

This module manages prompt versions, A/B testing, and performance tracking.
Provides centralized prompt management for the agricultural chatbot system.
"""

from typing import Dict, List, Any, Optional, Union
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

# Import semantic routing components
from .semantic_routing import SemanticIntentClassifier, classify_intent, IntentClassification
from .embedding_system import EmbeddingPromptMatcher, find_best_prompt, PromptMatch
from .dynamic_examples import DynamicFewShotManager, get_dynamic_examples

logger = logging.getLogger(__name__)

class PromptVersion(Enum):
    """Prompt version types."""
    PRODUCTION = "production"
    STAGING = "staging"
    DEVELOPMENT = "development"
    EXPERIMENTAL = "experimental"

@dataclass
class PromptMetrics:
    """Prompt performance metrics."""
    agent_type: str
    prompt_version: str
    user_satisfaction: float
    execution_time_ms: int
    confidence_score: float
    success_rate: float
    timestamp: datetime

@dataclass
class PromptConfig:
    """Prompt configuration."""
    agent_type: str
    version: str
    prompt_template: Any
    is_active: bool
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]

class PromptManager:
    """
    Manager for prompt versions, A/B testing, and semantic routing.
    
    Job: Manage prompt versions, A/B testing, performance tracking, and semantic routing.
    Input: Prompt configurations, performance data, and user queries
    Output: Active prompts, performance analytics, and semantic prompt selection
    """
    
    def __init__(self):
        self.prompt_versions: Dict[str, Dict[str, PromptConfig]] = {}
        self.active_versions: Dict[str, str] = {}
        self.performance_metrics: List[PromptMetrics] = []
        
        # Semantic routing components
        self.semantic_classifier = SemanticIntentClassifier()
        self.embedding_matcher = EmbeddingPromptMatcher()
        self.dynamic_examples_manager = DynamicFewShotManager()
        self.routing_method = "semantic"  # "semantic", "embedding", "llm", "fallback"
        self.enable_dynamic_examples = True
        
        self._initialize_default_prompts()
    
    def _initialize_default_prompts(self):
        """Initialize default prompt versions."""
        # Import prompts here to avoid circular imports
        try:
            from .farm_data_prompts import FARM_DATA_CHAT_PROMPT
            from .regulatory_prompts import REGULATORY_CHAT_PROMPT
            from .weather_prompts import WEATHER_CHAT_PROMPT
            from .crop_health_prompts import CROP_HEALTH_CHAT_PROMPT
            from .planning_prompts import PLANNING_CHAT_PROMPT
            from .sustainability_prompts import SUSTAINABILITY_CHAT_PROMPT
            from .orchestrator_prompts import ORCHESTRATOR_ROUTING_PROMPT
            
            # Initialize default versions
            self._register_prompt("farm_data_agent", "v1.0", FARM_DATA_CHAT_PROMPT, True)
            self._register_prompt("regulatory_agent", "v1.0", REGULATORY_CHAT_PROMPT, True)
            self._register_prompt("weather_agent", "v1.0", WEATHER_CHAT_PROMPT, True)
            self._register_prompt("crop_health_agent", "v1.0", CROP_HEALTH_CHAT_PROMPT, True)
            self._register_prompt("planning_agent", "v1.0", PLANNING_CHAT_PROMPT, True)
            self._register_prompt("sustainability_agent", "v1.0", SUSTAINABILITY_CHAT_PROMPT, True)
            self._register_prompt("orchestrator", "v1.0", ORCHESTRATOR_ROUTING_PROMPT, True)
            
        except ImportError as e:
            logger.warning(f"Could not import default prompts: {e}")
    
    def _register_prompt(self, agent_type: str, version: str, prompt_template: Any, is_active: bool = False):
        """Register a new prompt version."""
        if agent_type not in self.prompt_versions:
            self.prompt_versions[agent_type] = {}
        
        config = PromptConfig(
            agent_type=agent_type,
            version=version,
            prompt_template=prompt_template,
            is_active=is_active,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            metadata={}
        )
        
        self.prompt_versions[agent_type][version] = config
        
        if is_active:
            self.active_versions[agent_type] = version
    
    def get_prompt(self, agent_type: str, version: str = None) -> Optional[Any]:
        """
        Get prompt for agent with optional version.
        
        Args:
            agent_type: Type of agent
            version: Specific version (defaults to active version)
            
        Returns:
            Prompt template or None if not found
        """
        if version is None:
            version = self.active_versions.get(agent_type)
        
        if not version:
            logger.error(f"No active version found for agent type: {agent_type}")
            return None
        
        agent_prompts = self.prompt_versions.get(agent_type, {})
        config = agent_prompts.get(version)
        
        if config:
            return config.prompt_template
        else:
            logger.error(f"Prompt version {version} not found for agent type: {agent_type}")
            return None
    
    def update_prompt_version(self, agent_type: str, version: str) -> bool:
        """
        Update active prompt version for agent.
        
        Args:
            agent_type: Type of agent
            version: New version to activate
            
        Returns:
            True if successful, False otherwise
        """
        if agent_type not in self.prompt_versions:
            logger.error(f"Agent type {agent_type} not found")
            return False
        
        if version not in self.prompt_versions[agent_type]:
            logger.error(f"Version {version} not found for agent type {agent_type}")
            return False
        
        # Deactivate current version
        current_version = self.active_versions.get(agent_type)
        if current_version:
            self.prompt_versions[agent_type][current_version].is_active = False
        
        # Activate new version
        self.prompt_versions[agent_type][version].is_active = True
        self.prompt_versions[agent_type][version].updated_at = datetime.now()
        self.active_versions[agent_type] = version
        
        logger.info(f"Updated active version for {agent_type} to {version}")
        return True
    
    def register_new_prompt(self, agent_type: str, version: str, prompt_template: Any, 
                          metadata: Dict[str, Any] = None) -> bool:
        """
        Register a new prompt version.
        
        Args:
            agent_type: Type of agent
            version: Version identifier
            prompt_template: Prompt template
            metadata: Additional metadata
            
        Returns:
            True if successful, False otherwise
        """
        if metadata is None:
            metadata = {}
        
        self._register_prompt(agent_type, version, prompt_template, False)
        self.prompt_versions[agent_type][version].metadata = metadata
        
        logger.info(f"Registered new prompt version {version} for {agent_type}")
        return True
    
    def list_prompt_versions(self, agent_type: str = None) -> Dict[str, List[str]]:
        """
        List available prompt versions.
        
        Args:
            agent_type: Specific agent type (optional)
            
        Returns:
            Dictionary of agent types and their versions
        """
        if agent_type:
            if agent_type in self.prompt_versions:
                return {agent_type: list(self.prompt_versions[agent_type].keys())}
            else:
                return {}
        else:
            return {
                agent: list(versions.keys()) 
                for agent, versions in self.prompt_versions.items()
            }
    
    def get_active_versions(self) -> Dict[str, str]:
        """Get all active prompt versions."""
        return self.active_versions.copy()
    
    def log_prompt_performance(self, metrics: PromptMetrics) -> bool:
        """
        Log prompt performance metrics.
        
        Args:
            metrics: Performance metrics to log
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.performance_metrics.append(metrics)
            logger.info(f"Logged performance metrics for {metrics.agent_type} v{metrics.prompt_version}")
            return True
        except Exception as e:
            logger.error(f"Failed to log performance metrics: {e}")
            return False
    
    def get_performance_analytics(self, agent_type: str = None, 
                                version: str = None, 
                                days: int = 30) -> Dict[str, Any]:
        """
        Get performance analytics for prompts.
        
        Args:
            agent_type: Specific agent type (optional)
            version: Specific version (optional)
            days: Number of days to analyze
            
        Returns:
            Performance analytics
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Filter metrics
        filtered_metrics = [
            m for m in self.performance_metrics 
            if m.timestamp >= cutoff_date
        ]
        
        if agent_type:
            filtered_metrics = [m for m in filtered_metrics if m.agent_type == agent_type]
        
        if version:
            filtered_metrics = [m for m in filtered_metrics if m.prompt_version == version]
        
        if not filtered_metrics:
            return {"error": "No metrics found for the specified criteria"}
        
        # Calculate analytics
        total_requests = len(filtered_metrics)
        avg_satisfaction = sum(m.user_satisfaction for m in filtered_metrics) / total_requests
        avg_execution_time = sum(m.execution_time_ms for m in filtered_metrics) / total_requests
        avg_confidence = sum(m.confidence_score for m in filtered_metrics) / total_requests
        avg_success_rate = sum(m.success_rate for m in filtered_metrics) / total_requests
        
        return {
            "total_requests": total_requests,
            "average_satisfaction": round(avg_satisfaction, 2),
            "average_execution_time_ms": round(avg_execution_time, 2),
            "average_confidence": round(avg_confidence, 2),
            "average_success_rate": round(avg_success_rate, 2),
            "period_days": days,
            "agent_type": agent_type,
            "version": version
        }
    
    def compare_prompt_versions(self, agent_type: str, version1: str, version2: str, 
                              days: int = 30) -> Dict[str, Any]:
        """
        Compare performance between two prompt versions.
        
        Args:
            agent_type: Type of agent
            version1: First version to compare
            version2: Second version to compare
            days: Number of days to analyze
            
        Returns:
            Comparison results
        """
        metrics1 = self.get_performance_analytics(agent_type, version1, days)
        metrics2 = self.get_performance_analytics(agent_type, version2, days)
        
        if "error" in metrics1 or "error" in metrics2:
            return {"error": "Could not retrieve metrics for one or both versions"}
        
        return {
            "version1": metrics1,
            "version2": metrics2,
            "comparison": {
                "satisfaction_difference": metrics1["average_satisfaction"] - metrics2["average_satisfaction"],
                "execution_time_difference": metrics1["average_execution_time_ms"] - metrics2["average_execution_time_ms"],
                "confidence_difference": metrics1["average_confidence"] - metrics2["average_confidence"],
                "success_rate_difference": metrics1["average_success_rate"] - metrics2["average_success_rate"]
            }
        }
    
    def export_prompt_config(self, agent_type: str, version: str) -> Dict[str, Any]:
        """
        Export prompt configuration.
        
        Args:
            agent_type: Type of agent
            version: Version to export
            
        Returns:
            Prompt configuration
        """
        if agent_type not in self.prompt_versions:
            return {"error": f"Agent type {agent_type} not found"}
        
        if version not in self.prompt_versions[agent_type]:
            return {"error": f"Version {version} not found for agent type {agent_type}"}
        
        config = self.prompt_versions[agent_type][version]
        
        return {
            "agent_type": config.agent_type,
            "version": config.version,
            "is_active": config.is_active,
            "created_at": config.created_at.isoformat(),
            "updated_at": config.updated_at.isoformat(),
            "metadata": config.metadata
        }
    
    # Semantic Routing Methods
    
    def select_prompt_semantic(self, query: str, context: str = "", 
                              method: str = None) -> Dict[str, Any]:
        """
        Select prompt using semantic routing.
        
        Args:
            query: User query
            context: Additional context
            method: Routing method ("semantic", "embedding", "llm", "fallback")
            
        Returns:
            Prompt selection result
        """
        if method is None:
            method = self.routing_method
        
        try:
            if method == "semantic":
                # Use semantic intent classification
                classification = self.semantic_classifier.classify_intent_semantic(query, context)
                selected_prompt = classification.selected_prompt
                confidence = classification.confidence
                reasoning = classification.reasoning
                
            elif method == "embedding":
                # Use embedding-based matching
                match = find_best_prompt(query, context)
                if match:
                    selected_prompt = match.prompt_name
                    confidence = match.similarity_score
                    reasoning = match.reasoning
                else:
                    selected_prompt = "FARM_DATA_CHAT_PROMPT"
                    confidence = 0.5
                    reasoning = "Fallback to default prompt"
                    
            elif method == "llm":
                # Use LLM-based classification
                classification = self.semantic_classifier.classify_intent_llm(query, context)
                selected_prompt = classification.selected_prompt
                confidence = classification.confidence
                reasoning = classification.reasoning
                
            else:
                # Fallback method
                selected_prompt = "FARM_DATA_CHAT_PROMPT"
                confidence = 0.5
                reasoning = "Fallback method used"
            
            return {
                "selected_prompt": selected_prompt,
                "confidence": confidence,
                "reasoning": reasoning,
                "method": method,
                "query": query,
                "context": context,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in semantic prompt selection: {e}")
            return {
                "selected_prompt": "FARM_DATA_CHAT_PROMPT",
                "confidence": 0.0,
                "reasoning": f"Error in semantic routing: {str(e)}",
                "method": "error_fallback",
                "query": query,
                "context": context,
                "timestamp": datetime.now().isoformat()
            }
    
    def get_prompt_semantic(self, query: str, context: str = "", 
                           method: str = None) -> Optional[Any]:
        """
        Get prompt using semantic routing.
        
        Args:
            query: User query
            context: Additional context
            method: Routing method
            
        Returns:
            Prompt template or None
        """
        selection = self.select_prompt_semantic(query, context, method)
        prompt_name = selection["selected_prompt"]
        
        # Try to get the prompt from the prompt registry
        try:
            # Import the specific prompt modules
            if "FARM_DATA" in prompt_name:
                from . import farm_data_prompts
                return getattr(farm_data_prompts, prompt_name, None)
            elif "REGULATORY" in prompt_name:
                from . import regulatory_prompts
                return getattr(regulatory_prompts, prompt_name, None)
            elif "WEATHER" in prompt_name:
                from . import weather_prompts
                return getattr(weather_prompts, prompt_name, None)
            elif "CROP_HEALTH" in prompt_name:
                from . import crop_health_prompts
                return getattr(crop_health_prompts, prompt_name, None)
            elif "PLANNING" in prompt_name:
                from . import planning_prompts
                return getattr(planning_prompts, prompt_name, None)
            elif "SUSTAINABILITY" in prompt_name:
                from . import sustainability_prompts
                return getattr(sustainability_prompts, prompt_name, None)
            elif "ORCHESTRATOR" in prompt_name:
                from . import orchestrator_prompts
                return getattr(orchestrator_prompts, prompt_name, None)
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting prompt {prompt_name}: {e}")
            return None
    
    def set_routing_method(self, method: str) -> bool:
        """
        Set the routing method for prompt selection.
        
        Args:
            method: Routing method ("semantic", "embedding", "llm", "fallback")
            
        Returns:
            True if successful, False otherwise
        """
        valid_methods = ["semantic", "embedding", "llm", "fallback"]
        if method in valid_methods:
            self.routing_method = method
            logger.info(f"Set routing method to: {method}")
            return True
        else:
            logger.error(f"Invalid routing method: {method}")
            return False
    
    def get_routing_method(self) -> str:
        """Get the current routing method."""
        return self.routing_method
    
    def add_intent_example(self, intent: str, query: str, context: str, 
                          expected_prompt: str) -> bool:
        """
        Add a new intent example for training.
        
        Args:
            intent: Intent identifier
            query: Example query
            context: Example context
            expected_prompt: Expected prompt name
            
        Returns:
            True if successful, False otherwise
        """
        try:
            from .semantic_routing import IntentExample, IntentType
            
            # Convert string to IntentType
            intent_type = IntentType(intent) if hasattr(IntentType, intent) else None
            if not intent_type:
                logger.error(f"Invalid intent type: {intent}")
                return False
            
            example = IntentExample(
                intent=intent_type,
                query=query,
                context=context,
                expected_prompt=expected_prompt
            )
            
            return self.semantic_classifier.add_intent_example(example)
            
        except Exception as e:
            logger.error(f"Error adding intent example: {e}")
            return False
    
    def get_semantic_analytics(self, days: int = 30) -> Dict[str, Any]:
        """
        Get analytics for semantic routing performance.
        
        Args:
            days: Number of days to analyze
            
        Returns:
            Semantic routing analytics
        """
        cutoff_date = datetime.now() - timedelta(days=days)
        
        # Filter metrics for semantic routing
        semantic_metrics = [
            m for m in self.performance_metrics 
            if m.timestamp >= cutoff_date and "semantic" in str(m.agent_type).lower()
        ]
        
        if not semantic_metrics:
            return {"error": "No semantic routing metrics found"}
        
        # Calculate analytics
        total_requests = len(semantic_metrics)
        avg_confidence = sum(m.confidence_score for m in semantic_metrics) / total_requests
        avg_satisfaction = sum(m.user_satisfaction for m in semantic_metrics) / total_requests
        avg_execution_time = sum(m.execution_time_ms for m in semantic_metrics) / total_requests
        
        return {
            "total_semantic_requests": total_requests,
            "average_confidence": round(avg_confidence, 3),
            "average_satisfaction": round(avg_satisfaction, 2),
            "average_execution_time_ms": round(avg_execution_time, 2),
            "routing_method": self.routing_method,
            "period_days": days
        }
    
    # Dynamic Examples Methods
    
    def get_prompt_with_examples(self, prompt_type: str, query: str = "", 
                               context: str = "") -> str:
        """
        Get a prompt with dynamically injected examples.
        
        Args:
            prompt_type: Type of prompt
            query: User query for relevance matching
            context: Additional context
            
        Returns:
            Prompt with injected examples
        """
        # Get the base prompt
        base_prompt = self.get_prompt(prompt_type)
        if not base_prompt:
            return ""
        
        # Get dynamic examples if enabled
        if self.enable_dynamic_examples:
            examples = get_dynamic_examples(prompt_type, context, query)
            if examples:
                # Inject examples into the prompt
                examples_section = f"\n\n**Exemples pertinents:**\n{examples}\n"
                return str(base_prompt) + examples_section
        
        return str(base_prompt)
    
    def enable_dynamic_examples_injection(self, enabled: bool = True) -> bool:
        """
        Enable or disable dynamic examples injection.
        
        Args:
            enabled: Whether to enable dynamic examples
            
        Returns:
            True if successful
        """
        self.enable_dynamic_examples = enabled
        logger.info(f"Dynamic examples injection {'enabled' if enabled else 'disabled'}")
        return True
    
    def add_dynamic_example(self, prompt_type: str, example_type: str, 
                          user_query: str, context: str, expected_response: str,
                          reasoning: str, confidence: float, tags: List[str]) -> bool:
        """
        Add a new dynamic example.
        
        Args:
            prompt_type: Type of prompt
            example_type: Type of example
            user_query: Example user query
            context: Example context
            expected_response: Expected response
            reasoning: Reasoning for the example
            confidence: Confidence score
            tags: Tags for the example
            
        Returns:
            True if successful
        """
        try:
            from .dynamic_examples import ExampleType, add_few_shot_example
            
            # Convert string to ExampleType
            example_type_enum = ExampleType(example_type) if hasattr(ExampleType, example_type) else ExampleType.BASIC
            
            return add_few_shot_example(
                prompt_type=prompt_type,
                example_type=example_type_enum,
                user_query=user_query,
                context=context,
                expected_response=expected_response,
                reasoning=reasoning,
                confidence=confidence,
                tags=tags
            )
            
        except Exception as e:
            logger.error(f"Error adding dynamic example: {e}")
            return False
    
    def get_dynamic_examples_stats(self) -> Dict[str, Any]:
        """Get statistics about dynamic examples."""
        try:
            from .dynamic_examples import get_example_stats
            return get_example_stats()
        except Exception as e:
            logger.error(f"Error getting dynamic examples stats: {e}")
            return {"error": str(e)}
    
    def get_prompt_with_semantic_examples(self, query: str, context: str = "", 
                                        method: str = None) -> Dict[str, Any]:
        """
        Get prompt with semantic routing and dynamic examples.
        
        Args:
            query: User query
            context: Additional context
            method: Routing method
            
        Returns:
            Complete prompt configuration with examples
        """
        # Get semantic prompt selection
        selection = self.select_prompt_semantic(query, context, method)
        prompt_type = selection["selected_prompt"]
        
        # Get prompt with examples
        prompt_with_examples = self.get_prompt_with_examples(prompt_type, query, context)
        
        return {
            "prompt_type": prompt_type,
            "prompt_content": prompt_with_examples,
            "selection_info": selection,
            "examples_injected": self.enable_dynamic_examples,
            "timestamp": datetime.now().isoformat()
        }

# Global prompt manager instance
prompt_manager = PromptManager()

# Convenience functions
def get_prompt(agent_type: str, version: str = None) -> Optional[Any]:
    """Get prompt for agent with optional version."""
    return prompt_manager.get_prompt(agent_type, version)

def update_prompt_version(agent_type: str, version: str) -> bool:
    """Update active prompt version for agent."""
    return prompt_manager.update_prompt_version(agent_type, version)

def log_prompt_performance(agent_type: str, prompt_version: str, 
                          user_satisfaction: float, execution_time_ms: int,
                          confidence_score: float, success_rate: float) -> bool:
    """Log prompt performance metrics."""
    metrics = PromptMetrics(
        agent_type=agent_type,
        prompt_version=prompt_version,
        user_satisfaction=user_satisfaction,
        execution_time_ms=execution_time_ms,
        confidence_score=confidence_score,
        success_rate=success_rate,
        timestamp=datetime.now()
    )
    return prompt_manager.log_prompt_performance(metrics)

# Semantic routing convenience functions
def select_prompt_semantic(query: str, context: str = "", method: str = None) -> Dict[str, Any]:
    """Select prompt using semantic routing."""
    return prompt_manager.select_prompt_semantic(query, context, method)

def get_prompt_semantic(query: str, context: str = "", method: str = None) -> Optional[Any]:
    """Get prompt using semantic routing."""
    return prompt_manager.get_prompt_semantic(query, context, method)

def set_routing_method(method: str) -> bool:
    """Set the routing method for prompt selection."""
    return prompt_manager.set_routing_method(method)

def get_routing_method() -> str:
    """Get the current routing method."""
    return prompt_manager.get_routing_method()

def add_intent_example(intent: str, query: str, context: str, expected_prompt: str) -> bool:
    """Add a new intent example for training."""
    return prompt_manager.add_intent_example(intent, query, context, expected_prompt)

def get_semantic_analytics(days: int = 30) -> Dict[str, Any]:
    """Get analytics for semantic routing performance."""
    return prompt_manager.get_semantic_analytics(days)

# Dynamic examples convenience functions
def get_prompt_with_examples(prompt_type: str, query: str = "", context: str = "") -> str:
    """Get a prompt with dynamically injected examples."""
    return prompt_manager.get_prompt_with_examples(prompt_type, query, context)

def enable_dynamic_examples_injection(enabled: bool = True) -> bool:
    """Enable or disable dynamic examples injection."""
    return prompt_manager.enable_dynamic_examples_injection(enabled)

def add_dynamic_example(prompt_type: str, example_type: str, user_query: str, 
                       context: str, expected_response: str, reasoning: str,
                       confidence: float, tags: List[str]) -> bool:
    """Add a new dynamic example."""
    return prompt_manager.add_dynamic_example(
        prompt_type, example_type, user_query, context, 
        expected_response, reasoning, confidence, tags
    )

def get_dynamic_examples_stats() -> Dict[str, Any]:
    """Get statistics about dynamic examples."""
    return prompt_manager.get_dynamic_examples_stats()

def get_prompt_with_semantic_examples(query: str, context: str = "", method: str = None) -> Dict[str, Any]:
    """Get prompt with semantic routing and dynamic examples."""
    return prompt_manager.get_prompt_with_semantic_examples(query, context, method)

# Export all classes and functions
__all__ = [
    "PromptManager",
    "PromptVersion",
    "PromptMetrics",
    "PromptConfig",
    "prompt_manager",
    "get_prompt",
    "update_prompt_version",
    "log_prompt_performance",
    "select_prompt_semantic",
    "get_prompt_semantic",
    "set_routing_method",
    "get_routing_method",
    "add_intent_example",
    "get_semantic_analytics",
    "get_prompt_with_examples",
    "enable_dynamic_examples_injection",
    "add_dynamic_example",
    "get_dynamic_examples_stats",
    "get_prompt_with_semantic_examples"
]
