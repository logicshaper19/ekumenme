"""
Multi-Agent Conversation Service for Agricultural AI
Implements agent-to-agent communication with LangGraph
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, TypedDict, Annotated
from datetime import datetime
import json
import uuid

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langgraph import StateGraph, END
from langgraph.graph import add_messages
from langgraph.prebuilt import ToolExecutor
from langchain.tools import tool

from app.core.config import settings
from app.services.unified_regulatory_service import UnifiedRegulatoryService

logger = logging.getLogger(__name__)


class MultiAgentState(TypedDict):
    """State for multi-agent conversations"""
    messages: Annotated[List[BaseMessage], add_messages]
    current_agent: str
    conversation_id: str
    query: str
    context: Dict[str, Any]
    agent_responses: Dict[str, str]
    consensus_reached: bool
    final_recommendation: str
    confidence_scores: Dict[str, float]
    collaboration_history: List[Dict[str, Any]]
    next_agent: Optional[str]


class MultiAgentConversationService:
    """Multi-agent conversation orchestration with LangGraph"""
    
    def __init__(self):
        self.llm = None
        self.regulatory_service = UnifiedRegulatoryService()
        self.agent_graph = None
        self.agent_definitions = {}
        self.collaboration_patterns = {}
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize multi-agent conversation components"""
        try:
            # Initialize LLM
            self.llm = ChatOpenAI(
                model_name="gpt-4",
                temperature=0.1,
                openai_api_key=settings.OPENAI_API_KEY
            )
            
            # Define agent personalities and expertise
            self._define_agent_personalities()
            
            # Setup collaboration patterns
            self._setup_collaboration_patterns()
            
            # Create multi-agent graph
            self._create_multi_agent_graph()
            
            logger.info("Multi-agent conversation service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize multi-agent conversation service: {e}")
            raise
    
    def _define_agent_personalities(self):
        """Define different agent personalities and expertise"""
        self.agent_definitions = {
            "weather_expert": {
                "name": "Dr. Météo",
                "expertise": "Météorologie agricole et conditions d'application",
                "personality": "Précis, analytique, axé sur les données météorologiques",
                "prompt_template": """
                Je suis Dr. Météo, expert en météorologie agricole. Mon rôle est d'analyser les conditions météorologiques 
                et leur impact sur les pratiques agricoles. Je me concentre sur:
                - Conditions actuelles et prévisions
                - Fenêtres d'application optimales
                - Risques météorologiques
                - Impact sur l'efficacité des traitements
                
                Question: {query}
                Contexte: {context}
                
                Mon analyse météorologique:
                """
            },
            "regulatory_expert": {
                "name": "Maître Réglementation",
                "expertise": "Conformité réglementaire et autorisations phytosanitaires",
                "personality": "Rigoureux, précis, axé sur la conformité légale",
                "prompt_template": """
                Je suis Maître Réglementation, expert en conformité phytosanitaire française. Mon rôle est de vérifier 
                la conformité réglementaire et les autorisations. Je me concentre sur:
                - Autorisations AMM et usages autorisés
                - Zones de Non-Traitement (ZNT)
                - Délais Avant Récolte (DAR)
                - Conformité aux arrêtés préfectoraux
                
                Question: {query}
                Contexte: {context}
                
                Mon analyse réglementaire:
                """
            },
            "agronomist": {
                "name": "Prof. Agronome",
                "expertise": "Agronomie et pratiques culturales",
                "personality": "Pragmatique, expérimenté, axé sur les bonnes pratiques",
                "prompt_template": """
                Je suis Prof. Agronome, expert en agronomie et pratiques culturales. Mon rôle est de fournir des conseils 
                agronomiques pratiques et adaptés. Je me concentre sur:
                - Bonnes pratiques culturales
                - Optimisation des rendements
                - Gestion intégrée des cultures
                - Durabilité des pratiques
                
                Question: {query}
                Contexte: {context}
                
                Mon conseil agronomique:
                """
            },
            "economist": {
                "name": "Dr. Économie",
                "expertise": "Économie agricole et optimisation des coûts",
                "personality": "Analytique, orienté ROI, pragmatique",
                "prompt_template": """
                Je suis Dr. Économie, expert en économie agricole. Mon rôle est d'analyser les aspects économiques 
                et l'optimisation des coûts. Je me concentre sur:
                - Analyse coût-bénéfice
                - Optimisation des intrants
                - Rentabilité des pratiques
                - Impact économique des décisions
                
                Question: {query}
                Contexte: {context}
                
                Mon analyse économique:
                """
            },
            "moderator": {
                "name": "Coordinateur",
                "expertise": "Synthèse et coordination des expertises",
                "personality": "Synthétique, diplomate, orienté consensus",
                "prompt_template": """
                Je suis le Coordinateur, responsable de la synthèse des expertises multiples. Mon rôle est de:
                - Analyser les différents points de vue
                - Identifier les convergences et divergences
                - Proposer une synthèse équilibrée
                - Formuler des recommandations consensuelles
                
                Question: {query}
                Avis des experts:
                {expert_opinions}
                
                Ma synthèse coordonnée:
                """
            }
        }
    
    def _setup_collaboration_patterns(self):
        """Setup collaboration patterns between agents"""
        self.collaboration_patterns = {
            "weather_regulatory": {
                "description": "Collaboration météo-réglementation",
                "agents": ["weather_expert", "regulatory_expert"],
                "interaction_type": "sequential",
                "focus": "Conditions d'application conformes"
            },
            "full_consultation": {
                "description": "Consultation complète multi-expertise",
                "agents": ["weather_expert", "regulatory_expert", "agronomist", "economist"],
                "interaction_type": "parallel_then_synthesis",
                "focus": "Recommandation complète et équilibrée"
            },
            "technical_focus": {
                "description": "Focus technique agronomie-météo",
                "agents": ["weather_expert", "agronomist"],
                "interaction_type": "collaborative",
                "focus": "Optimisation technique"
            },
            "compliance_check": {
                "description": "Vérification conformité réglementaire",
                "agents": ["regulatory_expert", "agronomist"],
                "interaction_type": "validation",
                "focus": "Conformité des pratiques"
            }
        }
    
    def _create_multi_agent_graph(self):
        """Create LangGraph for multi-agent conversations"""
        
        # Create the state graph
        workflow = StateGraph(MultiAgentState)
        
        # Add agent nodes
        workflow.add_node("weather_expert", self._weather_expert_node)
        workflow.add_node("regulatory_expert", self._regulatory_expert_node)
        workflow.add_node("agronomist", self._agronomist_node)
        workflow.add_node("economist", self._economist_node)
        workflow.add_node("moderator", self._moderator_node)
        workflow.add_node("consensus_check", self._consensus_check_node)
        
        # Set entry point
        workflow.set_entry_point("weather_expert")
        
        # Add conditional edges for agent routing
        workflow.add_conditional_edges(
            "weather_expert",
            self._route_after_weather,
            {
                "regulatory": "regulatory_expert",
                "agronomist": "agronomist",
                "consensus": "consensus_check"
            }
        )
        
        workflow.add_conditional_edges(
            "regulatory_expert",
            self._route_after_regulatory,
            {
                "agronomist": "agronomist",
                "economist": "economist",
                "consensus": "consensus_check"
            }
        )
        
        workflow.add_conditional_edges(
            "agronomist",
            self._route_after_agronomist,
            {
                "economist": "economist",
                "consensus": "consensus_check"
            }
        )
        
        workflow.add_conditional_edges(
            "economist",
            self._route_after_economist,
            {
                "consensus": "consensus_check"
            }
        )
        
        workflow.add_conditional_edges(
            "consensus_check",
            self._route_after_consensus,
            {
                "moderator": "moderator",
                "continue": "weather_expert",
                "end": END
            }
        )
        
        workflow.add_edge("moderator", END)
        
        # Compile the workflow
        self.agent_graph = workflow.compile()
        
        logger.info("Multi-agent graph created and compiled")
    
    async def start_multi_agent_conversation(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
        collaboration_pattern: str = "full_consultation"
    ) -> Dict[str, Any]:
        """Start a multi-agent conversation"""
        try:
            conversation_id = str(uuid.uuid4())
            
            # Initialize state
            initial_state = MultiAgentState(
                messages=[HumanMessage(content=query)],
                current_agent="weather_expert",
                conversation_id=conversation_id,
                query=query,
                context=context or {},
                agent_responses={},
                consensus_reached=False,
                final_recommendation="",
                confidence_scores={},
                collaboration_history=[],
                next_agent=None
            )
            
            # Execute multi-agent workflow
            final_state = await self.agent_graph.ainvoke(initial_state)
            
            # Extract final response
            final_response = final_state.get("final_recommendation", "")
            if not final_response and final_state["messages"]:
                last_message = final_state["messages"][-1]
                if isinstance(last_message, AIMessage):
                    final_response = last_message.content
            
            return {
                "response": final_response,
                "conversation_id": conversation_id,
                "agent_responses": final_state["agent_responses"],
                "confidence_scores": final_state["confidence_scores"],
                "consensus_reached": final_state["consensus_reached"],
                "collaboration_history": final_state["collaboration_history"],
                "metadata": {
                    "collaboration_pattern": collaboration_pattern,
                    "agents_consulted": list(final_state["agent_responses"].keys()),
                    "total_interactions": len(final_state["collaboration_history"])
                }
            }
            
        except Exception as e:
            logger.error(f"Multi-agent conversation failed: {e}")
            return {
                "response": f"Erreur lors de la consultation multi-expertise: {str(e)}",
                "conversation_id": "",
                "agent_responses": {},
                "confidence_scores": {},
                "consensus_reached": False,
                "metadata": {"error": str(e)}
            }

    async def _weather_expert_node(self, state: MultiAgentState) -> MultiAgentState:
        """Weather expert agent node"""
        try:
            agent_def = self.agent_definitions["weather_expert"]

            # Create weather expert response
            prompt = agent_def["prompt_template"].format(
                query=state["query"],
                context=json.dumps(state["context"], ensure_ascii=False)
            )

            response = self.llm.predict(prompt)

            # Update state
            state["agent_responses"]["weather_expert"] = response
            state["confidence_scores"]["weather_expert"] = 0.85
            state["current_agent"] = "weather_expert"
            state["collaboration_history"].append({
                "agent": "weather_expert",
                "timestamp": datetime.now().isoformat(),
                "response_length": len(response)
            })

            # Add AI message
            state["messages"].append(AIMessage(
                content=f"**{agent_def['name']}**: {response}",
                name="weather_expert"
            ))

            return state

        except Exception as e:
            logger.error(f"Weather expert node failed: {e}")
            return state

    async def _regulatory_expert_node(self, state: MultiAgentState) -> MultiAgentState:
        """Regulatory expert agent node"""
        try:
            agent_def = self.agent_definitions["regulatory_expert"]

            # Create regulatory expert response
            prompt = agent_def["prompt_template"].format(
                query=state["query"],
                context=json.dumps(state["context"], ensure_ascii=False)
            )

            response = self.llm.predict(prompt)

            # Update state
            state["agent_responses"]["regulatory_expert"] = response
            state["confidence_scores"]["regulatory_expert"] = 0.90
            state["current_agent"] = "regulatory_expert"
            state["collaboration_history"].append({
                "agent": "regulatory_expert",
                "timestamp": datetime.now().isoformat(),
                "response_length": len(response)
            })

            # Add AI message
            state["messages"].append(AIMessage(
                content=f"**{agent_def['name']}**: {response}",
                name="regulatory_expert"
            ))

            return state

        except Exception as e:
            logger.error(f"Regulatory expert node failed: {e}")
            return state

    async def _agronomist_node(self, state: MultiAgentState) -> MultiAgentState:
        """Agronomist agent node"""
        try:
            agent_def = self.agent_definitions["agronomist"]

            # Create agronomist response
            prompt = agent_def["prompt_template"].format(
                query=state["query"],
                context=json.dumps(state["context"], ensure_ascii=False)
            )

            response = self.llm.predict(prompt)

            # Update state
            state["agent_responses"]["agronomist"] = response
            state["confidence_scores"]["agronomist"] = 0.88
            state["current_agent"] = "agronomist"
            state["collaboration_history"].append({
                "agent": "agronomist",
                "timestamp": datetime.now().isoformat(),
                "response_length": len(response)
            })

            # Add AI message
            state["messages"].append(AIMessage(
                content=f"**{agent_def['name']}**: {response}",
                name="agronomist"
            ))

            return state

        except Exception as e:
            logger.error(f"Agronomist node failed: {e}")
            return state

    async def _economist_node(self, state: MultiAgentState) -> MultiAgentState:
        """Economist agent node"""
        try:
            agent_def = self.agent_definitions["economist"]

            # Create economist response
            prompt = agent_def["prompt_template"].format(
                query=state["query"],
                context=json.dumps(state["context"], ensure_ascii=False)
            )

            response = self.llm.predict(prompt)

            # Update state
            state["agent_responses"]["economist"] = response
            state["confidence_scores"]["economist"] = 0.82
            state["current_agent"] = "economist"
            state["collaboration_history"].append({
                "agent": "economist",
                "timestamp": datetime.now().isoformat(),
                "response_length": len(response)
            })

            # Add AI message
            state["messages"].append(AIMessage(
                content=f"**{agent_def['name']}**: {response}",
                name="economist"
            ))

            return state

        except Exception as e:
            logger.error(f"Economist node failed: {e}")
            return state

    async def _moderator_node(self, state: MultiAgentState) -> MultiAgentState:
        """Moderator synthesis node"""
        try:
            agent_def = self.agent_definitions["moderator"]

            # Compile expert opinions
            expert_opinions = ""
            for agent, response in state["agent_responses"].items():
                if agent != "moderator":
                    expert_opinions += f"\n\n**{agent.replace('_', ' ').title()}**: {response}"

            # Create moderator synthesis
            prompt = agent_def["prompt_template"].format(
                query=state["query"],
                expert_opinions=expert_opinions
            )

            response = self.llm.predict(prompt)

            # Update state
            state["agent_responses"]["moderator"] = response
            state["confidence_scores"]["moderator"] = 0.92
            state["current_agent"] = "moderator"
            state["final_recommendation"] = response
            state["consensus_reached"] = True
            state["collaboration_history"].append({
                "agent": "moderator",
                "timestamp": datetime.now().isoformat(),
                "response_length": len(response),
                "synthesis": True
            })

            # Add AI message
            state["messages"].append(AIMessage(
                content=f"**{agent_def['name']}**: {response}",
                name="moderator"
            ))

            return state

        except Exception as e:
            logger.error(f"Moderator node failed: {e}")
            return state

    async def _consensus_check_node(self, state: MultiAgentState) -> MultiAgentState:
        """Check if consensus is reached"""
        try:
            # Simple consensus check based on number of agents consulted
            agents_consulted = len(state["agent_responses"])

            if agents_consulted >= 3:
                state["consensus_reached"] = True
            else:
                state["consensus_reached"] = False

            state["collaboration_history"].append({
                "action": "consensus_check",
                "timestamp": datetime.now().isoformat(),
                "agents_consulted": agents_consulted,
                "consensus_reached": state["consensus_reached"]
            })

            return state

        except Exception as e:
            logger.error(f"Consensus check failed: {e}")
            return state

    def _route_after_weather(self, state: MultiAgentState) -> str:
        """Route after weather expert"""
        # Always go to regulatory expert after weather
        return "regulatory"

    def _route_after_regulatory(self, state: MultiAgentState) -> str:
        """Route after regulatory expert"""
        # Go to agronomist for practical advice
        return "agronomist"

    def _route_after_agronomist(self, state: MultiAgentState) -> str:
        """Route after agronomist"""
        # Check if economic analysis is needed
        query_lower = state["query"].lower()
        if any(word in query_lower for word in ["coût", "prix", "rentabilité", "économique"]):
            return "economist"
        else:
            return "consensus"

    def _route_after_economist(self, state: MultiAgentState) -> str:
        """Route after economist"""
        # Always go to consensus after economist
        return "consensus"

    def _route_after_consensus(self, state: MultiAgentState) -> str:
        """Route after consensus check"""
        if state["consensus_reached"]:
            return "moderator"
        else:
            # Need more consultation
            return "continue"

    async def get_conversation_summary(self, conversation_id: str) -> Dict[str, Any]:
        """Get summary of multi-agent conversation"""
        # This would typically query a database for conversation history
        return {
            "conversation_id": conversation_id,
            "status": "completed",
            "agents_involved": ["weather_expert", "regulatory_expert", "agronomist", "moderator"],
            "total_interactions": 4,
            "consensus_reached": True,
            "summary": "Multi-agent consultation completed with consensus"
        }
