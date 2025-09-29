"""
Multi-Agent Conversation Service
Advanced orchestration of specialized agricultural agents
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from enum import Enum
import uuid

from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.agents.openai_functions_agent.base import OpenAIFunctionsAgent
from langchain_openai import ChatOpenAI
from langchain.schema import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langgraph.graph import StateGraph, END
from langgraph.graph import add_messages

from app.services.enhanced_tool_service import EnhancedToolService
from app.services.memory_service import MemoryService
from app.core.config import settings

logger = logging.getLogger(__name__)


class AgentRole(Enum):
    """Specialized agent roles"""
    COORDINATOR = "coordinator"
    WEATHER_SPECIALIST = "weather_specialist"
    REGULATORY_SPECIALIST = "regulatory_specialist"
    FARM_OPERATIONS_SPECIALIST = "farm_operations_specialist"
    COMPLIANCE_AUDITOR = "compliance_auditor"


class AgentState(dict):
    """State for multi-agent conversation"""
    messages: List[BaseMessage]
    current_agent: str
    query: str
    context: Dict[str, Any]
    agent_responses: Dict[str, Any]
    final_response: str
    confidence_scores: Dict[str, float]
    processing_steps: List[str]
    errors: List[str]


class SpecializedAgent:
    """Base class for specialized agricultural agents"""
    
    def __init__(self, role: AgentRole, tools: List[str] = None):
        self.role = role
        self.tools = tools or []
        self.llm = ChatOpenAI(
            model_name="gpt-4",
            temperature=0.1,
            openai_api_key=settings.OPENAI_API_KEY
        )
        self.tool_service = EnhancedToolService()
        self.execution_count = 0
        self.specialization_prompt = self._get_specialization_prompt()
    
    def _get_specialization_prompt(self) -> str:
        """Get role-specific system prompt"""
        prompts = {
            AgentRole.COORDINATOR: """
            Vous êtes l'agent coordinateur agricole. Votre rôle est de:
            1. Analyser les demandes complexes et les décomposer
            2. Coordonner les agents spécialisés
            3. Synthétiser les réponses en une recommandation cohérente
            4. Assurer la cohérence entre les différents aspects (météo, réglementation, opérations)
            """,
            
            AgentRole.WEATHER_SPECIALIST: """
            Vous êtes l'expert météorologique agricole. Votre expertise couvre:
            1. Analyse des conditions météorologiques pour l'agriculture
            2. Fenêtres d'intervention optimales
            3. Risques climatiques pour les cultures
            4. Recommandations de timing pour les traitements
            """,
            
            AgentRole.REGULATORY_SPECIALIST: """
            Vous êtes l'expert en réglementation agricole française. Votre expertise couvre:
            1. Conformité EPHY et AMM
            2. Zones Non Traitées (ZNT)
            3. Délais avant récolte (DAR)
            4. Autorisations et restrictions d'usage
            """,
            
            AgentRole.FARM_OPERATIONS_SPECIALIST: """
            Vous êtes l'expert en opérations agricoles. Votre expertise couvre:
            1. Planification des interventions
            2. Optimisation des pratiques culturales
            3. Gestion des parcelles et rotations
            4. Efficacité opérationnelle
            """,
            
            AgentRole.COMPLIANCE_AUDITOR: """
            Vous êtes l'auditeur de conformité agricole. Votre rôle est de:
            1. Vérifier la conformité réglementaire des recommandations
            2. Identifier les risques de non-conformité
            3. Proposer des alternatives conformes
            4. Assurer la traçabilité des décisions
            """
        }
        
        return prompts.get(self.role, "Vous êtes un expert agricole.")
    
    async def process_query(
        self,
        query: str,
        context: Dict[str, Any],
        previous_responses: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Process query with specialized expertise"""
        self.execution_count += 1
        start_time = datetime.now()
        
        try:
            # Create specialized prompt
            messages = [
                SystemMessage(content=self.specialization_prompt),
                HumanMessage(content=f"""
                Demande: {query}
                
                Contexte: {json.dumps(context, ensure_ascii=False, indent=2)}
                
                Réponses précédentes des autres agents:
                {json.dumps(previous_responses or {}, ensure_ascii=False, indent=2)}
                
                Analysez cette demande selon votre expertise et fournissez:
                1. Votre analyse spécialisée
                2. Vos recommandations
                3. Les points d'attention
                4. Votre niveau de confiance (0-1)
                """)
            ]
            
            # Get specialized response
            response = await self.llm.ainvoke(messages)
            
            # Execute relevant tools if needed
            tool_results = await self._execute_relevant_tools(query, context)
            
            # Calculate execution time and confidence
            execution_time = (datetime.now() - start_time).total_seconds()
            confidence = self._calculate_confidence(query, context, tool_results)
            
            return {
                "agent_role": self.role.value,
                "response": response.content,
                "tool_results": tool_results,
                "confidence": confidence,
                "execution_time": execution_time,
                "execution_count": self.execution_count,
                "timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Agent {self.role.value} failed: {e}")
            return {
                "agent_role": self.role.value,
                "response": f"Erreur lors de l'analyse: {str(e)}",
                "tool_results": {},
                "confidence": 0.0,
                "execution_time": (datetime.now() - start_time).total_seconds(),
                "error": str(e)
            }
    
    async def _execute_relevant_tools(
        self,
        query: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute tools relevant to this agent's specialization"""
        tool_results = {}
        query_lower = query.lower()
        
        # Weather specialist tools
        if self.role == AgentRole.WEATHER_SPECIALIST:
            if any(word in query_lower for word in ["météo", "temps", "pluie", "vent"]):
                result = self.tool_service.execute_tool(
                    "weather_analysis",
                    location=context.get("location", "France"),
                    days=7
                )
                tool_results["weather_analysis"] = result.dict()
        
        # Regulatory specialist tools
        elif self.role == AgentRole.REGULATORY_SPECIALIST:
            if any(word in query_lower for word in ["produit", "traitement", "conformité"]):
                # Extract product names from query
                products = self._extract_products_from_query(query)
                for product in products:
                    result = self.tool_service.execute_tool(
                        "regulatory_compliance",
                        product_name=product,
                        crop_type=context.get("crop_type")
                    )
                    tool_results[f"regulatory_{product}"] = result.dict()
        
        # Farm operations specialist tools
        elif self.role == AgentRole.FARM_OPERATIONS_SPECIALIST:
            if context.get("farm_siret"):
                result = self.tool_service.execute_tool(
                    "farm_data_analysis",
                    siret=context["farm_siret"],
                    analysis_type="operations"
                )
                tool_results["farm_analysis"] = result.dict()
        
        return tool_results
    
    def _extract_products_from_query(self, query: str) -> List[str]:
        """Extract product names from query"""
        products = []
        query_lower = query.lower()
        
        # Common agricultural products
        known_products = [
            "glyphosate", "cuivre", "soufre", "azote", "phosphore", "potasse",
            "roundup", "bouillie bordelaise", "mancozèbe", "chlorothalonil"
        ]
        
        for product in known_products:
            if product in query_lower:
                products.append(product)
        
        return products
    
    def _calculate_confidence(
        self,
        query: str,
        context: Dict[str, Any],
        tool_results: Dict[str, Any]
    ) -> float:
        """Calculate confidence score for the response"""
        base_confidence = 0.7
        
        # Increase confidence if tools were successfully executed
        if tool_results:
            successful_tools = sum(1 for result in tool_results.values() 
                                 if result.get("success", False))
            total_tools = len(tool_results)
            if total_tools > 0:
                tool_success_rate = successful_tools / total_tools
                base_confidence += 0.2 * tool_success_rate
        
        # Adjust based on query complexity
        query_words = len(query.split())
        if query_words > 20:  # Complex query
            base_confidence -= 0.1
        elif query_words < 5:  # Simple query
            base_confidence += 0.1
        
        # Adjust based on available context
        if context.get("farm_siret"):
            base_confidence += 0.1
        if context.get("crop_type"):
            base_confidence += 0.05
        
        return min(1.0, max(0.0, base_confidence))


class MultiAgentService:
    """Service for orchestrating multiple specialized agents"""
    
    def __init__(self):
        self.agents = {
            AgentRole.COORDINATOR: SpecializedAgent(AgentRole.COORDINATOR),
            AgentRole.WEATHER_SPECIALIST: SpecializedAgent(AgentRole.WEATHER_SPECIALIST),
            AgentRole.REGULATORY_SPECIALIST: SpecializedAgent(AgentRole.REGULATORY_SPECIALIST),
            AgentRole.FARM_OPERATIONS_SPECIALIST: SpecializedAgent(AgentRole.FARM_OPERATIONS_SPECIALIST),
            AgentRole.COMPLIANCE_AUDITOR: SpecializedAgent(AgentRole.COMPLIANCE_AUDITOR)
        }
        self.memory_service = MemoryService()
        self.conversation_workflows = {}
    
    async def process_multi_agent_query(
        self,
        query: str,
        context: Dict[str, Any],
        conversation_id: str = None
    ) -> Dict[str, Any]:
        """Process query using multiple specialized agents"""
        
        conversation_id = conversation_id or str(uuid.uuid4())
        start_time = datetime.now()
        
        try:
            # Determine which agents are needed
            required_agents = self._determine_required_agents(query, context)
            
            # Get conversation memory
            memory_context = {}
            if conversation_id:
                memory_context = await self.memory_service.get_conversation_context(
                    conversation_id=conversation_id,
                    user_id=context.get("user_id", "unknown"),
                    farm_siret=context.get("farm_siret")
                )
            
            # Merge context with memory
            enhanced_context = {**context, **memory_context}
            
            # Execute agents in parallel for independent analysis
            agent_tasks = []
            for agent_role in required_agents:
                if agent_role != AgentRole.COORDINATOR:  # Coordinator runs last
                    agent = self.agents[agent_role]
                    task = agent.process_query(query, enhanced_context)
                    agent_tasks.append((agent_role, task))
            
            # Wait for all specialist agents to complete
            agent_responses = {}
            for agent_role, task in agent_tasks:
                try:
                    response = await task
                    agent_responses[agent_role.value] = response
                except Exception as e:
                    logger.error(f"Agent {agent_role.value} failed: {e}")
                    agent_responses[agent_role.value] = {
                        "error": str(e),
                        "confidence": 0.0
                    }
            
            # Run coordinator to synthesize responses
            coordinator = self.agents[AgentRole.COORDINATOR]
            coordinator_response = await coordinator.process_query(
                query, enhanced_context, agent_responses
            )
            
            # Calculate overall confidence
            overall_confidence = self._calculate_overall_confidence(agent_responses)
            
            # Run compliance auditor if needed
            compliance_check = None
            if any("traitement" in query.lower() or "produit" in query.lower() 
                   for word in query.lower().split()):
                auditor = self.agents[AgentRole.COMPLIANCE_AUDITOR]
                compliance_check = await auditor.process_query(
                    query, enhanced_context, agent_responses
                )
            
            # Create final response
            final_response = self._create_final_response(
                coordinator_response,
                agent_responses,
                compliance_check,
                overall_confidence
            )
            
            # Save to memory
            if conversation_id:
                self.memory_service.save_conversation_turn(
                    conversation_id=conversation_id,
                    user_id=context.get("user_id", "unknown"),
                    user_message=query,
                    ai_response=final_response["response"],
                    farm_siret=context.get("farm_siret")
                )
            
            execution_time = (datetime.now() - start_time).total_seconds()
            
            return {
                "response": final_response["response"],
                "agent_responses": agent_responses,
                "coordinator_response": coordinator_response,
                "compliance_check": compliance_check,
                "overall_confidence": overall_confidence,
                "required_agents": [role.value for role in required_agents],
                "execution_time": execution_time,
                "conversation_id": conversation_id,
                "metadata": {
                    "multi_agent": True,
                    "agents_used": len(required_agents),
                    "memory_enhanced": bool(memory_context),
                    "compliance_checked": compliance_check is not None
                }
            }
            
        except Exception as e:
            logger.error(f"Multi-agent processing failed: {e}")
            return {
                "response": f"Erreur lors du traitement multi-agent: {str(e)}",
                "error": str(e),
                "overall_confidence": 0.0,
                "execution_time": (datetime.now() - start_time).total_seconds()
            }
    
    def _determine_required_agents(
        self,
        query: str,
        context: Dict[str, Any]
    ) -> List[AgentRole]:
        """Determine which agents are needed for the query"""
        required = [AgentRole.COORDINATOR]  # Always include coordinator
        query_lower = query.lower()
        
        # Weather specialist
        if any(word in query_lower for word in [
            "météo", "temps", "pluie", "vent", "température", "humidité",
            "fenêtre", "conditions", "traitement"
        ]):
            required.append(AgentRole.WEATHER_SPECIALIST)
        
        # Regulatory specialist
        if any(word in query_lower for word in [
            "réglementation", "amm", "znt", "conformité", "autorisé",
            "interdit", "délai", "produit", "traitement"
        ]):
            required.append(AgentRole.REGULATORY_SPECIALIST)
        
        # Farm operations specialist
        if any(word in query_lower for word in [
            "parcelle", "exploitation", "intervention", "planification",
            "rotation", "culture", "semis", "récolte"
        ]) or context.get("farm_siret"):
            required.append(AgentRole.FARM_OPERATIONS_SPECIALIST)
        
        return required
    
    def _calculate_overall_confidence(
        self,
        agent_responses: Dict[str, Any]
    ) -> float:
        """Calculate overall confidence from agent responses"""
        confidences = []
        for response in agent_responses.values():
            if isinstance(response, dict) and "confidence" in response:
                confidences.append(response["confidence"])
        
        if not confidences:
            return 0.5
        
        # Weighted average with higher weight for higher confidences
        weights = [conf ** 2 for conf in confidences]
        weighted_sum = sum(conf * weight for conf, weight in zip(confidences, weights))
        weight_sum = sum(weights)
        
        return weighted_sum / weight_sum if weight_sum > 0 else 0.5
    
    def _create_final_response(
        self,
        coordinator_response: Dict[str, Any],
        agent_responses: Dict[str, Any],
        compliance_check: Optional[Dict[str, Any]],
        overall_confidence: float
    ) -> Dict[str, Any]:
        """Create final synthesized response"""
        
        response_parts = [coordinator_response.get("response", "")]
        
        # Add compliance warning if needed
        if compliance_check and compliance_check.get("confidence", 0) > 0.7:
            compliance_content = compliance_check.get("response", "")
            if "non conforme" in compliance_content.lower() or "attention" in compliance_content.lower():
                response_parts.append(f"\n⚠️ **Vérification de conformité:**\n{compliance_content}")
        
        # Add confidence indicator
        if overall_confidence > 0.8:
            confidence_indicator = "✅ Recommandation fiable"
        elif overall_confidence > 0.6:
            confidence_indicator = "⚡ Recommandation modérément fiable"
        else:
            confidence_indicator = "⚠️ Recommandation à vérifier"
        
        response_parts.append(f"\n*{confidence_indicator} (confiance: {overall_confidence:.1%})*")
        
        return {
            "response": "\n".join(response_parts),
            "confidence_indicator": confidence_indicator
        }
    
    def get_agent_statistics(self) -> Dict[str, Any]:
        """Get execution statistics for all agents"""
        stats = {}
        for role, agent in self.agents.items():
            stats[role.value] = {
                "execution_count": agent.execution_count,
                "specialization": agent.specialization_prompt[:100] + "..."
            }
        return stats
