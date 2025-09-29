"""
Unified Router Service - Single routing system replacing 5 overlapping routers.

This service consolidates:
- streaming_service.py routing logic
- semantic_routing_service.py
- conditional_routing_service.py
- fast_query_service.py routing
- langgraph_workflow_service.py routing

Goal: Reduce routing overhead from 8-13s to 1-2s
"""

import logging
import time
from typing import Dict, Any, Optional, List
from enum import Enum
from dataclasses import dataclass
from functools import lru_cache

from langchain_openai import ChatOpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)


class QueryComplexity(Enum):
    """Query complexity levels"""
    SIMPLE = "simple"           # < 5s - Direct answer, no tools
    FAST = "fast"               # < 10s - Single tool, GPT-3.5
    MEDIUM = "medium"           # < 20s - Multiple tools, GPT-3.5
    COMPLEX = "complex"         # < 40s - Multi-agent, GPT-4


class ExecutionPath(Enum):
    """Execution paths for queries"""
    DIRECT_ANSWER = "direct_answer"      # No tools, just LLM
    FAST_PATH = "fast_path"              # Single tool, GPT-3.5
    STANDARD_PATH = "standard_path"      # Multiple tools, parallel
    WORKFLOW_PATH = "workflow_path"      # Full workflow, GPT-4


@dataclass
class RoutingDecision:
    """Routing decision with all necessary information"""
    complexity: QueryComplexity
    execution_path: ExecutionPath
    required_tools: List[str]
    required_agents: List[str]
    use_gpt4: bool
    estimated_time: float
    confidence: float
    reasoning: str
    cache_key: Optional[str] = None


class UnifiedRouterService:
    """
    Unified router that replaces all overlapping routing systems.
    
    Features:
    - Single routing decision (not 5 separate ones)
    - Pattern-based classification (fast, no LLM)
    - LLM fallback only when needed
    - Aggressive caching
    - Clear execution path selection
    """
    
    def __init__(self):
        self.routing_cache: Dict[str, RoutingDecision] = {}
        self.cache_hits = 0
        self.cache_misses = 0
        
        # Initialize lightweight LLM for routing (only when needed)
        self.routing_llm = ChatOpenAI(
            model_name="gpt-3.5-turbo",
            temperature=0,
            max_tokens=200,  # Short routing decision
            openai_api_key=settings.OPENAI_API_KEY
        )
        
        # Pattern-based routing rules (FAST - no LLM needed)
        self._initialize_routing_patterns()
        
        logger.info("Initialized Unified Router Service")
    
    def _initialize_routing_patterns(self):
        """Initialize fast pattern-based routing rules"""

        # Simple queries - Direct answer, no tools
        self.simple_patterns = [
            "bonjour", "salut", "merci", "au revoir",
            "qui es-tu", "comment ça va", "aide",
            "qu'est-ce que tu peux faire"
        ]

        # Fast path - Single tool queries (simple lookups)
        self.fast_patterns = {
            "weather": ["météo", "temps", "pluie", "température", "prévision"],
            "regulatory": ["amm code", "numéro amm", "autorisation produit"]
        }

        # Medium path - Multiple tools but simple
        self.medium_keywords = [
            "planification", "coût", "prix"
        ]

        # Complex path - Analytical queries requiring deep investigation
        self.complex_keywords = [
            # Explicit complexity markers
            "analyse complète", "plan détaillé", "stratégie",
            "optimisation", "étude de faisabilité",
            "rapport complet", "diagnostic approfondi",

            # Comparison and calculation indicators
            "comparaison", "comparer", "différence", "pourquoi",
            "quelle est la dose", "dose moyenne", "calcul",

            # Multi-intervention analysis
            "interventions", "traitements", "plusieurs",
            "les deux", "ces deux", "lors de ces",

            # Surface/area analysis
            "surface de", "hectares", "n'ont-elles été réalisées que sur",
            "totalité de la parcelle", "une partie de",

            # Investigation keywords
            "sont-ils le même", "est-ce que", "comment se fait-il",
            "quelle est la raison", "pourquoi les"
        ]
    
    async def route_query(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> RoutingDecision:
        """
        Main routing method - single entry point for all queries.
        
        Args:
            query: User query
            context: Optional context (user_id, farm_siret, etc.)
        
        Returns:
            RoutingDecision with execution path and requirements
        """
        start_time = time.time()
        
        # Check cache first (< 1ms)
        cache_key = self._generate_cache_key(query, context)
        if cache_key in self.routing_cache:
            self.cache_hits += 1
            decision = self.routing_cache[cache_key]
            logger.info(f"✅ Cache HIT for query: {query[:50]}... (took {time.time() - start_time:.3f}s)")
            return decision
        
        self.cache_misses += 1
        
        # Step 1: Try pattern-based routing (FAST - no LLM)
        decision = self._pattern_based_routing(query, context)
        
        # Step 2: If uncertain, use LLM routing (FALLBACK)
        if decision.confidence < 0.8:
            logger.info(f"Pattern confidence low ({decision.confidence:.2f}), using LLM routing")
            decision = await self._llm_based_routing(query, context)
        
        # Cache the decision
        self.routing_cache[cache_key] = decision
        
        # Limit cache size
        if len(self.routing_cache) > 1000:
            # Remove oldest 100 entries
            oldest_keys = list(self.routing_cache.keys())[:100]
            for key in oldest_keys:
                del self.routing_cache[key]
        
        elapsed = time.time() - start_time
        logger.info(
            f"🔀 Routed query in {elapsed:.3f}s: "
            f"path={decision.execution_path.value}, "
            f"complexity={decision.complexity.value}, "
            f"tools={len(decision.required_tools)}, "
            f"gpt4={decision.use_gpt4}"
        )
        
        return decision
    
    def _generate_cache_key(self, query: str, context: Optional[Dict[str, Any]]) -> str:
        """Generate cache key for query"""
        # Normalize query
        normalized = query.lower().strip()
        
        # Include relevant context in cache key
        context_key = ""
        if context:
            # Only include stable context (not timestamps, etc.)
            stable_context = {
                k: v for k, v in context.items()
                if k in ["user_id", "farm_siret", "location"]
            }
            context_key = str(sorted(stable_context.items()))
        
        return f"{normalized}_{context_key}"
    
    def _pattern_based_routing(
        self,
        query: str,
        context: Optional[Dict[str, Any]]
    ) -> RoutingDecision:
        """
        Fast pattern-based routing (no LLM needed).

        Returns routing decision with confidence score.

        IMPORTANT: Check complex patterns FIRST to avoid misclassification!
        """
        query_lower = query.lower()

        # Check for simple queries
        if any(pattern in query_lower for pattern in self.simple_patterns):
            return RoutingDecision(
                complexity=QueryComplexity.SIMPLE,
                execution_path=ExecutionPath.DIRECT_ANSWER,
                required_tools=[],
                required_agents=[],
                use_gpt4=False,
                estimated_time=1.0,
                confidence=0.95,
                reasoning="Simple conversational query, no tools needed"
            )

        # Check for COMPLEX queries FIRST (before fast path!)
        # This prevents analytical queries from being misclassified as simple lookups
        complex_matches = [kw for kw in self.complex_keywords if kw in query_lower]
        if complex_matches:
            return RoutingDecision(
                complexity=QueryComplexity.COMPLEX,
                execution_path=ExecutionPath.WORKFLOW_PATH,
                required_tools=["weather", "regulatory", "farm_data", "planning"],
                required_agents=["weather", "regulatory", "farm_data", "planning"],
                use_gpt4=True,
                estimated_time=30.0,
                confidence=0.9,
                reasoning=f"Complex analytical query detected: {complex_matches[:3]}"
            )

        # Check for fast path (single tool) - only simple lookups
        for tool_type, patterns in self.fast_patterns.items():
            if any(pattern in query_lower for pattern in patterns):
                return RoutingDecision(
                    complexity=QueryComplexity.FAST,
                    execution_path=ExecutionPath.FAST_PATH,
                    required_tools=[tool_type],
                    required_agents=[tool_type],
                    use_gpt4=False,
                    estimated_time=3.0,
                    confidence=0.9,
                    reasoning=f"Single tool query: {tool_type}"
                )

        # Check for medium queries
        if any(keyword in query_lower for keyword in self.medium_keywords):
            return RoutingDecision(
                complexity=QueryComplexity.MEDIUM,
                execution_path=ExecutionPath.STANDARD_PATH,
                required_tools=["weather", "crop_health", "regulatory"],
                required_agents=["weather", "crop_health", "regulatory"],
                use_gpt4=False,
                estimated_time=12.0,
                confidence=0.8,
                reasoning="Medium complexity query with multiple tools"
            )

        # Default: medium path with lower confidence
        return RoutingDecision(
            complexity=QueryComplexity.MEDIUM,
            execution_path=ExecutionPath.STANDARD_PATH,
            required_tools=["weather", "farm_data"],
            required_agents=["weather", "farm_data"],
            use_gpt4=False,
            estimated_time=10.0,
            confidence=0.6,
            reasoning="Default routing - uncertain classification"
        )
    
    async def _llm_based_routing(
        self,
        query: str,
        context: Optional[Dict[str, Any]]
    ) -> RoutingDecision:
        """
        LLM-based routing for uncertain cases.
        
        Only called when pattern-based routing has low confidence.
        """
        # TODO: Implement LLM-based routing
        # For now, return medium path
        logger.warning("LLM-based routing not yet implemented, using default")
        return RoutingDecision(
            complexity=QueryComplexity.MEDIUM,
            execution_path=ExecutionPath.STANDARD_PATH,
            required_tools=["weather", "farm_data"],
            required_agents=["weather", "farm_data"],
            use_gpt4=False,
            estimated_time=10.0,
            confidence=0.7,
            reasoning="LLM routing fallback"
        )
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = self.cache_hits / total_requests if total_requests > 0 else 0
        
        return {
            "cache_size": len(self.routing_cache),
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "hit_rate": hit_rate,
            "total_requests": total_requests
        }

