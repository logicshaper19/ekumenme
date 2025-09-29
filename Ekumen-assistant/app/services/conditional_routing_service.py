"""
Conditional Routing Service for Agricultural AI
Advanced query complexity-based routing and decision trees
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple, Callable
from datetime import datetime
import json
import re

from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
from pydantic import BaseModel, Field

from app.core.config import settings

logger = logging.getLogger(__name__)


class RoutingDecision(BaseModel):
    """Structured routing decision"""
    primary_route: str = Field(description="Primary routing destination")
    confidence: float = Field(description="Confidence in routing decision 0-1")
    reasoning: str = Field(description="Explanation of routing logic")
    fallback_routes: List[str] = Field(default=[], description="Alternative routes")
    complexity_score: float = Field(description="Query complexity score 0-1")
    requires_multi_step: bool = Field(description="Whether query needs multi-step processing")
    estimated_processing_time: float = Field(description="Estimated processing time in seconds")


class ConditionalRoutingService:
    """Advanced conditional routing with decision trees"""
    
    def __init__(self):
        self.llm = None
        self.routing_rules = {}
        self.decision_trees = {}
        self.performance_metrics = {}
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize conditional routing components"""
        try:
            # Initialize LLM
            self.llm = ChatOpenAI(
                model_name="gpt-4",
                temperature=0.1,
                openai_api_key=settings.OPENAI_API_KEY
            )
            
            # Setup routing rules
            self._setup_routing_rules()
            
            # Setup decision trees
            self._setup_decision_trees()
            
            logger.info("Conditional routing service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize conditional routing: {e}")
            raise
    
    def _setup_routing_rules(self):
        """Setup conditional routing rules"""
        self.routing_rules = {
            "complexity_thresholds": {
                "simple": {"max_words": 10, "max_concepts": 2, "processing_time": 2.0},
                "moderate": {"max_words": 25, "max_concepts": 4, "processing_time": 5.0},
                "complex": {"max_words": 50, "max_concepts": 8, "processing_time": 10.0},
                "very_complex": {"max_words": float('inf'), "max_concepts": float('inf'), "processing_time": 20.0}
            },
            "domain_priorities": {
                "emergency": {"priority": 1, "max_wait_time": 1.0},
                "regulatory": {"priority": 2, "max_wait_time": 3.0},
                "weather": {"priority": 3, "max_wait_time": 2.0},
                "planning": {"priority": 4, "max_wait_time": 10.0},
                "general": {"priority": 5, "max_wait_time": 15.0}
            },
            "resource_requirements": {
                "weather": {"requires_external_api": True, "cpu_intensive": False},
                "regulatory": {"requires_database": True, "cpu_intensive": False},
                "planning": {"requires_reasoning": True, "cpu_intensive": True},
                "pest_disease": {"requires_image_analysis": True, "cpu_intensive": True}
            }
        }
    
    def _setup_decision_trees(self):
        """Setup decision trees for routing"""
        self.decision_trees = {
            "agricultural_routing": {
                "root": {
                    "condition": "is_emergency",
                    "true_branch": "emergency_handler",
                    "false_branch": "domain_analysis"
                },
                "domain_analysis": {
                    "condition": "primary_domain",
                    "branches": {
                        "weather": "weather_complexity_check",
                        "regulatory": "regulatory_complexity_check",
                        "planning": "planning_complexity_check",
                        "pest_disease": "diagnostic_complexity_check",
                        "general": "general_complexity_check"
                    }
                },
                "weather_complexity_check": {
                    "condition": "complexity_score",
                    "branches": {
                        "low": "simple_weather_agent",
                        "medium": "advanced_weather_agent",
                        "high": "weather_workflow"
                    }
                },
                "regulatory_complexity_check": {
                    "condition": "involves_multiple_products",
                    "true_branch": "regulatory_workflow",
                    "false_branch": "simple_regulatory_agent"
                },
                "planning_complexity_check": {
                    "condition": "planning_horizon",
                    "branches": {
                        "short_term": "tactical_planning_agent",
                        "medium_term": "strategic_planning_agent",
                        "long_term": "comprehensive_planning_workflow"
                    }
                }
            }
        }
    
    async def route_query(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        user_preferences: Optional[Dict[str, Any]] = None
    ) -> RoutingDecision:
        """Perform conditional routing based on query analysis"""
        try:
            # Step 1: Analyze query characteristics
            query_analysis = await self._analyze_query_characteristics(query, context)
            
            # Step 2: Apply decision tree routing
            routing_path = await self._apply_decision_tree(query_analysis, user_preferences)
            
            # Step 3: Validate routing decision
            validated_decision = await self._validate_routing_decision(routing_path, query_analysis)
            
            # Step 4: Generate routing decision
            decision = RoutingDecision(
                primary_route=validated_decision["primary_route"],
                confidence=validated_decision["confidence"],
                reasoning=validated_decision["reasoning"],
                fallback_routes=validated_decision.get("fallback_routes", []),
                complexity_score=query_analysis["complexity_score"],
                requires_multi_step=query_analysis["requires_multi_step"],
                estimated_processing_time=validated_decision["estimated_processing_time"]
            )
            
            # Step 5: Update performance metrics
            self._update_performance_metrics(decision, query_analysis)
            
            return decision
            
        except Exception as e:
            logger.error(f"Conditional routing failed: {e}")
            # Return safe fallback
            return RoutingDecision(
                primary_route="general_agent",
                confidence=0.5,
                reasoning=f"Routing failed, using fallback: {str(e)}",
                complexity_score=0.5,
                requires_multi_step=False,
                estimated_processing_time=5.0
            )
    
    async def _analyze_query_characteristics(
        self,
        query: str,
        context: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze query characteristics for routing"""
        try:
            # Basic metrics
            word_count = len(query.split())
            char_count = len(query)
            
            # Detect complexity indicators
            complexity_indicators = [
                "comment", "pourquoi", "quand", "où", "combien", "quel",
                "compare", "optimise", "planifie", "analyse", "évalue"
            ]
            
            complexity_score = sum(1 for indicator in complexity_indicators if indicator in query.lower()) / len(complexity_indicators)
            
            # Detect domain
            domain_keywords = {
                "weather": ["météo", "temps", "pluie", "vent", "température", "climat"],
                "regulatory": ["réglementation", "amm", "znt", "conformité", "autorisation"],
                "planning": ["planification", "calendrier", "programme", "stratégie"],
                "pest_disease": ["maladie", "ravageur", "diagnostic", "symptôme"],
                "emergency": ["urgent", "immédiat", "critique", "danger", "alerte"]
            }
            
            primary_domain = "general"
            domain_confidence = 0.0
            
            for domain, keywords in domain_keywords.items():
                matches = sum(1 for keyword in keywords if keyword in query.lower())
                confidence = matches / len(keywords)
                if confidence > domain_confidence:
                    domain_confidence = confidence
                    primary_domain = domain
            
            # Detect multi-step requirements
            multi_step_indicators = ["puis", "ensuite", "après", "et", "également", "aussi"]
            requires_multi_step = any(indicator in query.lower() for indicator in multi_step_indicators)
            
            # Detect resource requirements
            requires_external_data = any(keyword in query.lower() for keyword in [
                "météo", "prévision", "cours", "prix", "marché"
            ])
            
            requires_database_lookup = any(keyword in query.lower() for keyword in [
                "produit", "amm", "autorisation", "parcelle", "intervention"
            ])
            
            return {
                "word_count": word_count,
                "char_count": char_count,
                "complexity_score": complexity_score,
                "primary_domain": primary_domain,
                "domain_confidence": domain_confidence,
                "requires_multi_step": requires_multi_step,
                "requires_external_data": requires_external_data,
                "requires_database_lookup": requires_database_lookup,
                "query_type": self._classify_query_type(query),
                "urgency_level": self._assess_urgency(query, context)
            }
            
        except Exception as e:
            logger.error(f"Query analysis failed: {e}")
            return {
                "word_count": len(query.split()),
                "complexity_score": 0.5,
                "primary_domain": "general",
                "requires_multi_step": False
            }
    
    def _classify_query_type(self, query: str) -> str:
        """Classify the type of query"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["?", "comment", "pourquoi", "quand"]):
            return "question"
        elif any(word in query_lower for word in ["recommande", "conseil", "suggère"]):
            return "advice_request"
        elif any(word in query_lower for word in ["planifie", "programme", "organise"]):
            return "planning_request"
        elif any(word in query_lower for word in ["analyse", "évalue", "compare"]):
            return "analysis_request"
        else:
            return "general_inquiry"
    
    def _assess_urgency(self, query: str, context: Optional[Dict[str, Any]]) -> str:
        """Assess urgency level of query"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["urgent", "immédiat", "critique", "danger"]):
            return "high"
        elif any(word in query_lower for word in ["rapidement", "vite", "bientôt"]):
            return "medium"
        else:
            return "low"

    async def _apply_decision_tree(
        self,
        query_analysis: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Apply decision tree logic for routing"""
        try:
            tree = self.decision_trees["agricultural_routing"]
            current_node = "root"
            routing_path = []

            while current_node in tree:
                node = tree[current_node]
                routing_path.append(current_node)

                if "condition" in node:
                    condition_result = self._evaluate_condition(
                        node["condition"],
                        query_analysis,
                        user_preferences
                    )

                    if "branches" in node:
                        # Multi-branch node
                        current_node = node["branches"].get(condition_result, "general_agent")
                    else:
                        # Binary branch node
                        current_node = node["true_branch"] if condition_result else node["false_branch"]
                else:
                    # Leaf node
                    break

            return {
                "final_route": current_node,
                "routing_path": routing_path,
                "decision_points": len(routing_path)
            }

        except Exception as e:
            logger.error(f"Decision tree application failed: {e}")
            return {"final_route": "general_agent", "routing_path": ["error"], "decision_points": 0}

    def _evaluate_condition(
        self,
        condition: str,
        query_analysis: Dict[str, Any],
        user_preferences: Optional[Dict[str, Any]]
    ) -> Any:
        """Evaluate a routing condition"""
        try:
            if condition == "is_emergency":
                return query_analysis.get("urgency_level") == "high"

            elif condition == "primary_domain":
                return query_analysis.get("primary_domain", "general")

            elif condition == "complexity_score":
                score = query_analysis.get("complexity_score", 0.5)
                if score < 0.3:
                    return "low"
                elif score < 0.7:
                    return "medium"
                else:
                    return "high"

            elif condition == "involves_multiple_products":
                query_text = query_analysis.get("original_query", "").lower()
                product_indicators = ["produits", "traitements", "plusieurs", "différents"]
                return any(indicator in query_text for indicator in product_indicators)

            elif condition == "planning_horizon":
                query_text = query_analysis.get("original_query", "").lower()
                if any(word in query_text for word in ["aujourd'hui", "demain", "cette semaine"]):
                    return "short_term"
                elif any(word in query_text for word in ["ce mois", "cette saison", "trimestre"]):
                    return "medium_term"
                else:
                    return "long_term"

            else:
                return False

        except Exception as e:
            logger.error(f"Condition evaluation failed for {condition}: {e}")
            return False

    async def _validate_routing_decision(
        self,
        routing_path: Dict[str, Any],
        query_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate and enhance routing decision"""
        try:
            final_route = routing_path["final_route"]

            # Map routes to actual service endpoints
            route_mapping = {
                "emergency_handler": "emergency_response_service",
                "simple_weather_agent": "weather_agent",
                "advanced_weather_agent": "advanced_weather_service",
                "weather_workflow": "langgraph_weather_workflow",
                "simple_regulatory_agent": "regulatory_agent",
                "regulatory_workflow": "langgraph_regulatory_workflow",
                "tactical_planning_agent": "planning_agent",
                "strategic_planning_agent": "advanced_planning_service",
                "comprehensive_planning_workflow": "langgraph_planning_workflow",
                "general_agent": "general_agricultural_agent"
            }

            primary_route = route_mapping.get(final_route, "general_agricultural_agent")

            # Calculate confidence based on routing path
            confidence = 0.9 - (0.1 * routing_path["decision_points"])  # Decrease confidence with complexity
            confidence = max(0.5, confidence)  # Minimum confidence

            # Estimate processing time
            complexity_score = query_analysis.get("complexity_score", 0.5)
            base_time = 2.0

            if "workflow" in primary_route:
                estimated_time = base_time * (2 + complexity_score * 3)
            elif "advanced" in primary_route:
                estimated_time = base_time * (1.5 + complexity_score * 2)
            else:
                estimated_time = base_time * (1 + complexity_score)

            # Generate reasoning
            reasoning = f"Routed to {primary_route} via {' -> '.join(routing_path['routing_path'])} based on domain: {query_analysis.get('primary_domain')}, complexity: {complexity_score:.2f}"

            # Determine fallback routes
            fallback_routes = self._determine_fallback_routes(primary_route, query_analysis)

            return {
                "primary_route": primary_route,
                "confidence": confidence,
                "reasoning": reasoning,
                "fallback_routes": fallback_routes,
                "estimated_processing_time": estimated_time
            }

        except Exception as e:
            logger.error(f"Routing validation failed: {e}")
            return {
                "primary_route": "general_agricultural_agent",
                "confidence": 0.5,
                "reasoning": f"Validation failed: {str(e)}",
                "fallback_routes": [],
                "estimated_processing_time": 5.0
            }

    def _determine_fallback_routes(
        self,
        primary_route: str,
        query_analysis: Dict[str, Any]
    ) -> List[str]:
        """Determine fallback routes for primary route"""
        fallbacks = []

        # Domain-specific fallbacks
        domain = query_analysis.get("primary_domain", "general")

        if "workflow" in primary_route:
            # Workflow fallback to simpler agent
            fallbacks.append(primary_route.replace("workflow", "agent"))

        if "advanced" in primary_route:
            # Advanced service fallback to basic agent
            fallbacks.append(primary_route.replace("advanced_", ""))

        # Always include general agent as ultimate fallback
        if "general" not in primary_route:
            fallbacks.append("general_agricultural_agent")

        return fallbacks[:3]  # Limit to 3 fallbacks

    def _update_performance_metrics(
        self,
        decision: RoutingDecision,
        query_analysis: Dict[str, Any]
    ):
        """Update performance metrics for routing decisions"""
        try:
            route = decision.primary_route

            if route not in self.performance_metrics:
                self.performance_metrics[route] = {
                    "total_requests": 0,
                    "avg_confidence": 0.0,
                    "avg_complexity": 0.0,
                    "success_rate": 1.0
                }

            metrics = self.performance_metrics[route]
            metrics["total_requests"] += 1

            # Update running averages
            n = metrics["total_requests"]
            metrics["avg_confidence"] = ((n-1) * metrics["avg_confidence"] + decision.confidence) / n
            metrics["avg_complexity"] = ((n-1) * metrics["avg_complexity"] + decision.complexity_score) / n

        except Exception as e:
            logger.error(f"Failed to update performance metrics: {e}")

    async def get_routing_statistics(self) -> Dict[str, Any]:
        """Get routing performance statistics"""
        return {
            "total_routes": len(self.performance_metrics),
            "performance_metrics": self.performance_metrics,
            "decision_tree_nodes": len(self.decision_trees["agricultural_routing"]),
            "routing_rules": len(self.routing_rules)
        }
