"""
Integrated base agent that works with the complete system architecture.
Leverages cost optimization, semantic enhancement, and LangGraph orchestration.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Protocol
from pydantic import BaseModel, Field
from langchain.schema import BaseMessage
import logging

# Import from integrated system components
try:
    from .cost_optimized_agents import CostOptimizedLLMManager, TaskComplexity, TaskComplexityAnalyzer
except ImportError:
    # Fallback if cost_optimized_agents not available
    class TaskComplexity:
        SIMPLE = "simple"
        MODERATE = "moderate"
        COMPLEX = "complex"
        CRITICAL = "critical"
    
    class TaskComplexityAnalyzer:
        @staticmethod
        def analyze_complexity(query: str, domain: str = "") -> str:
            query_lower = query.lower()
            if any(word in query_lower for word in ["complex", "multiple", "integrate", "combine"]):
                return TaskComplexity.COMPLEX
            elif any(word in query_lower for word in ["critical", "urgent", "safety", "regulatory"]):
                return TaskComplexity.CRITICAL
            elif any(word in query_lower for word in ["analyze", "assess", "evaluate"]):
                return TaskComplexity.MODERATE
            else:
                return TaskComplexity.SIMPLE
    
    class CostOptimizedLLMManager:
        def __init__(self, *args, **kwargs):
            self.complexity_mapping = {
                TaskComplexity.SIMPLE: type('obj', (object,), {'value': 'gpt-3.5-turbo'}),
                TaskComplexity.MODERATE: type('obj', (object,), {'value': 'gpt-3.5-turbo'}),
                TaskComplexity.COMPLEX: type('obj', (object,), {'value': 'gpt-4'}),
                TaskComplexity.CRITICAL: type('obj', (object,), {'value': 'gpt-4'})
            }
        
        def get_llm(self, complexity, temperature=0.1):
            return type('obj', (object,), {'invoke': lambda x: type('obj', (object,), {'content': 'Mock response'})()})()
        
        def get_cost_report(self):
            return {"total_savings": 0.0}

# Removed circular import - these classes are now defined in orchestration.py
# Define minimal fallback classes to avoid import errors
class AgentType:
    FARM_DATA = "farm_data"
    REGULATORY = "regulatory"
    WEATHER = "weather"
    CROP_HEALTH = "crop_health"
    PLANNING = "planning"
    SUSTAINABILITY = "sustainability"

class SemanticKnowledgeRetriever:
    def retrieve_relevant_knowledge(self, query: str, top_k: int = 3) -> List[str]:
        return ["Connaissance agricole générale disponible"]

logger = logging.getLogger(__name__)

# =============================================================================
# SYSTEM-AWARE AGENT PROTOCOL
# =============================================================================

class SystemIntegratedAgent(Protocol):
    """Protocol defining the interface for system-integrated agents."""
    
    agent_type: AgentType
    complexity_default: TaskComplexity
    
    def process_message(self, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Process message with full system integration."""
        ...
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities and metadata."""
        ...

# =============================================================================
# INTEGRATED BASE AGENT
# =============================================================================

class IntegratedAgriculturalAgent(ABC):
    """
    Base agent that integrates with the complete system architecture.
    Provides cost optimization, semantic enhancement, and reasoning capabilities.
    """
    
    def __init__(
        self,
        agent_type: AgentType,
        description: str,
        llm_manager: CostOptimizedLLMManager,
        knowledge_retriever: SemanticKnowledgeRetriever,
        complexity_default: TaskComplexity = TaskComplexity.MODERATE,
        specialized_tools: List[Any] = None
    ):
        self.agent_type = agent_type
        self.description = description
        self.complexity_default = complexity_default
        
        # Core system components
        self.llm_manager = llm_manager
        self.knowledge_retriever = knowledge_retriever
        self.specialized_tools = specialized_tools or []
        
        # Performance tracking
        self.performance_metrics = {
            "messages_processed": 0,
            "avg_response_time": 0.0,
            "cost_savings_achieved": 0.0,
            "knowledge_retrievals": 0
        }
        
        logger.info(f"Initialized {agent_type.value} with system integration")
    
    @abstractmethod
    def _get_agent_prompt_template(self) -> str:
        """Get the base prompt template for this agent type."""
        pass
    
    @abstractmethod
    def _analyze_message_complexity(self, message: str, context: Dict[str, Any]) -> TaskComplexity:
        """Analyze message complexity for this specific agent type."""
        pass
    
    @abstractmethod
    def _retrieve_domain_knowledge(self, message: str) -> List[str]:
        """Retrieve domain-specific knowledge for this agent."""
        pass
    
    def process_message(self, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process message with full system integration."""
        import time
        start_time = time.time()
        
        try:
            context = context or {}
            
            # Step 1: Analyze complexity for cost optimization
            complexity = self._analyze_message_complexity(message, context)
            
            # Step 2: Get cost-optimized LLM
            llm = self.llm_manager.get_llm(complexity, temperature=self._get_temperature(complexity))
            
            # Step 3: Retrieve relevant knowledge
            knowledge = self._retrieve_domain_knowledge(message)
            context["retrieved_knowledge"] = knowledge
            
            # Step 4: Execute specialized tools if needed
            tool_results = self._execute_tools_if_needed(message, context)
            
            # Step 5: Generate response with enhanced context
            response = self._generate_response(message, context, knowledge, tool_results, llm)
            
            # Step 6: Update performance metrics
            response_time = time.time() - start_time
            self._update_metrics(complexity, response_time, len(knowledge))
            
            return {
                "response": response,
                "agent_type": self.agent_type.value,
                "complexity_used": complexity.value,
                "llm_tier": self.llm_manager.complexity_mapping[complexity].value,
                "knowledge_retrieved": len(knowledge),
                "tools_used": len(tool_results),
                "response_time_ms": round(response_time * 1000, 2),
                "system_integrated": True
            }
            
        except Exception as e:
            logger.error(f"Error in {self.agent_type.value} agent: {e}")
            return self._handle_error(e)
    
    def _get_temperature(self, complexity: TaskComplexity) -> float:
        """Get appropriate temperature based on complexity."""
        temperature_map = {
            TaskComplexity.SIMPLE: 0.1,
            TaskComplexity.MODERATE: 0.2,
            TaskComplexity.COMPLEX: 0.3,
            TaskComplexity.CRITICAL: 0.0  # No creativity for critical decisions
        }
        return temperature_map.get(complexity, 0.1)
    
    def _execute_tools_if_needed(self, message: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Execute specialized tools if needed."""
        tool_results = []
        
        for tool in self.specialized_tools:
            if self._should_use_tool(tool, message, context):
                try:
                    result = tool.execute(message, context)
                    tool_results.append({
                        "tool": tool.name,
                        "result": result
                    })
                except Exception as e:
                    logger.error(f"Tool {tool.name} failed: {e}")
        
        return tool_results
    
    def _should_use_tool(self, tool: Any, message: str, context: Dict[str, Any]) -> bool:
        """Determine if a tool should be used for this message."""
        # Default implementation - override in specialized agents
        return hasattr(tool, 'should_execute') and tool.should_execute(message, context)
    
    def _generate_response(self, message: str, context: Dict[str, Any], 
                          knowledge: List[str], tool_results: List[Dict[str, Any]], llm) -> str:
        """Generate response with enhanced context."""
        
        # Build enhanced prompt
        prompt = self._build_enhanced_prompt(message, context, knowledge, tool_results)
        
        # Generate response
        response = llm.invoke([{"role": "user", "content": prompt}])
        
        return response.content if hasattr(response, 'content') else str(response)
    
    def _build_enhanced_prompt(self, message: str, context: Dict[str, Any], 
                              knowledge: List[str], tool_results: List[Dict[str, Any]]) -> str:
        """Build enhanced prompt with all available context."""
        
        base_prompt = self._get_agent_prompt_template()
        
        # Add knowledge context
        knowledge_section = ""
        if knowledge:
            knowledge_section = "\n\nCONNAISSANCES PERTINENTES:\n"
            knowledge_section += "\n".join(f"- {k}" for k in knowledge[:3])
        
        # Add tool results
        tools_section = ""
        if tool_results:
            tools_section = "\n\nRÉSULTATS D'OUTILS:\n"
            for result in tool_results:
                tools_section += f"\n{result['tool']}: {result['result']}\n"
        
        # Add context information
        context_section = ""
        if context:
            relevant_context = {k: v for k, v in context.items() 
                              if k not in ['retrieved_knowledge'] and v}
            if relevant_context:
                context_section = f"\n\nCONTEXTE: {relevant_context}"
        
        return f"""
{base_prompt}

{knowledge_section}
{tools_section}
{context_section}

QUESTION: {message}

Répondez en français avec expertise agricole:
        """
    
    def _update_metrics(self, complexity: TaskComplexity, response_time: float, knowledge_count: int):
        """Update performance metrics."""
        self.performance_metrics["messages_processed"] += 1
        
        # Update average response time
        current_avg = self.performance_metrics["avg_response_time"]
        count = self.performance_metrics["messages_processed"]
        self.performance_metrics["avg_response_time"] = (current_avg * (count - 1) + response_time) / count
        
        # Estimate cost savings
        if complexity != TaskComplexity.CRITICAL:
            # Rough estimate of savings vs always using GPT-4
            savings_percentage = {
                TaskComplexity.SIMPLE: 0.95,
                TaskComplexity.MODERATE: 0.75,
                TaskComplexity.COMPLEX: 0.33
            }.get(complexity, 0)
            self.performance_metrics["cost_savings_achieved"] += savings_percentage
        
        if knowledge_count > 0:
            self.performance_metrics["knowledge_retrievals"] += 1
    
    def _handle_error(self, error: Exception) -> Dict[str, Any]:
        """Handle errors gracefully."""
        return {
            "response": "Je rencontre une difficulté technique. Pouvez-vous reformuler votre question ?",
            "agent_type": self.agent_type.value,
            "error": str(error),
            "system_integrated": True
        }
    
    def get_capabilities(self) -> Dict[str, Any]:
        """Get agent capabilities and performance metrics."""
        return {
            "agent_type": self.agent_type.value,
            "description": self.description,
            "complexity_default": self.complexity_default.value,
            "specialized_tools": len(self.specialized_tools),
            "performance_metrics": self.performance_metrics,
            "cost_optimized": True,
            "semantic_enhanced": True,
            "knowledge_integrated": True
        }

# =============================================================================
# SPECIALIZED AGENT IMPLEMENTATIONS
# =============================================================================

class SystemIntegratedFarmDataAgent(IntegratedAgriculturalAgent):
    """Farm data agent integrated with the complete system."""
    
    def __init__(self, llm_manager: CostOptimizedLLMManager, 
                 knowledge_retriever: SemanticKnowledgeRetriever):
        super().__init__(
            agent_type=AgentType.FARM_DATA,
            description="Expert en analyse de données d'exploitation",
            llm_manager=llm_manager,
            knowledge_retriever=knowledge_retriever,
            complexity_default=TaskComplexity.MODERATE
        )
    
    def _get_agent_prompt_template(self) -> str:
        return """Vous êtes un expert en analyse de données d'exploitation agricole française.

VOTRE EXPERTISE:
- Analyse des rendements et performances des parcelles
- Optimisation des pratiques culturales
- Évaluation de la rentabilité des cultures
- Conseils basés sur les données historiques

Fournissez des analyses précises et des recommandations pratiques."""
    
    def _analyze_message_complexity(self, message: str, context: Dict[str, Any]) -> TaskComplexity:
        """Analyze complexity for farm data queries."""
        message_lower = message.lower()
        
        # Simple data retrieval
        if any(word in message_lower for word in ["combien", "quelle", "superficie", "rendement de"]):
            return TaskComplexity.SIMPLE
        
        # Complex analysis
        elif any(word in message_lower for word in ["analyse", "compare", "optimise", "tendance"]):
            return TaskComplexity.COMPLEX
        
        return TaskComplexity.MODERATE
    
    def _retrieve_domain_knowledge(self, message: str) -> List[str]:
        """Retrieve farm data specific knowledge."""
        return self.knowledge_retriever.retrieve_relevant_knowledge(
            f"données exploitation rendement {message}", top_k=3
        )

class SystemIntegratedRegulatoryAgent(IntegratedAgriculturalAgent):
    """Regulatory agent integrated with the complete system."""
    
    def __init__(self, llm_manager: CostOptimizedLLMManager, 
                 knowledge_retriever: SemanticKnowledgeRetriever):
        super().__init__(
            agent_type=AgentType.REGULATORY,
            description="Expert en conformité réglementaire",
            llm_manager=llm_manager,
            knowledge_retriever=knowledge_retriever,
            complexity_default=TaskComplexity.CRITICAL  # Always critical for safety
        )
    
    def _get_agent_prompt_template(self) -> str:
        return """Vous êtes un expert en réglementation agricole française et conformité phytosanitaire.

VOTRE EXPERTISE:
- Vérification des autorisations AMM
- Conformité des produits phytopharmaceutiques
- Respect des zones non traitées (ZNT)
- Sécurité et réglementations phytosanitaires

⚠️ IMPORTANT: Toujours vérifier sur E-phy en cas de doute."""
    
    def _analyze_message_complexity(self, message: str, context: Dict[str, Any]) -> TaskComplexity:
        """Regulatory queries are always critical for safety."""
        return TaskComplexity.CRITICAL
    
    def _retrieve_domain_knowledge(self, message: str) -> List[str]:
        """Retrieve regulatory specific knowledge."""
        return self.knowledge_retriever.retrieve_relevant_knowledge(
            f"réglementation AMM conformité {message}", top_k=5
        )

# =============================================================================
# SYSTEM-INTEGRATED AGENT MANAGER
# =============================================================================

class SystemIntegratedAgentManager:
    """Manages agents within the complete system architecture."""
    
    def __init__(self, llm_manager: CostOptimizedLLMManager, 
                 knowledge_retriever: SemanticKnowledgeRetriever):
        self.llm_manager = llm_manager
        self.knowledge_retriever = knowledge_retriever
        self.agents: Dict[AgentType, IntegratedAgriculturalAgent] = {}
        
        # Initialize core agents
        self._initialize_core_agents()
    
    def _initialize_core_agents(self):
        """Initialize core system-integrated agents."""
        self.agents[AgentType.FARM_DATA] = SystemIntegratedFarmDataAgent(
            self.llm_manager, self.knowledge_retriever
        )
        self.agents[AgentType.REGULATORY] = SystemIntegratedRegulatoryAgent(
            self.llm_manager, self.knowledge_retriever
        )
        # Add other agents as implemented...
    
    def get_agent(self, agent_type: AgentType) -> Optional[IntegratedAgriculturalAgent]:
        """Get agent by type."""
        return self.agents.get(agent_type)
    
    def process_with_agent(self, agent_type: AgentType, message: str, 
                          context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process message with specific agent."""
        agent = self.get_agent(agent_type)
        if not agent:
            return {
                "response": f"Agent {agent_type.value} non disponible",
                "error": "Agent not found"
            }
        
        return agent.process_message(message, context)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status."""
        return {
            "available_agents": list(self.agents.keys()),
            "total_cost_savings": self.llm_manager.get_cost_report(),
            "agent_performance": {
                agent_type.value: agent.get_capabilities() 
                for agent_type, agent in self.agents.items()
            }
        }