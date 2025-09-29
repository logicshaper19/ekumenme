"""
LangGraph Workflow Service for Agricultural AI
Implements advanced workflow orchestration with conditional routing
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, TypedDict, Annotated
from datetime import datetime
import json

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, END
from langgraph.graph import add_messages
from langgraph.prebuilt import ToolNode
from langchain.tools import tool

from app.core.config import settings
from app.services.unified_regulatory_service import UnifiedRegulatoryService

logger = logging.getLogger(__name__)


class AgriculturalWorkflowState(TypedDict):
    """State for agricultural workflow"""
    messages: Annotated[List[BaseMessage], add_messages]
    query: str
    context: Dict[str, Any]
    weather_data: Optional[Dict[str, Any]]
    regulatory_status: Optional[Dict[str, Any]]
    farm_data: Optional[Dict[str, Any]]
    recommendations: List[str]
    confidence: float
    agent_type: str
    processing_steps: List[str]
    errors: List[str]


class LangGraphWorkflowService:
    """Advanced workflow orchestration using LangGraph"""
    
    def __init__(self):
        self.llm = None
        self.regulatory_service = UnifiedRegulatoryService()
        self.workflow = None
        self.app = None
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize LangGraph components"""
        try:
            # Initialize LLM
            self.llm = ChatOpenAI(
                model_name="gpt-4",
                temperature=0.1,
                openai_api_key=settings.OPENAI_API_KEY
            )
            
            # Create workflow
            self._create_workflow()
            
            logger.info("LangGraph workflow service initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize LangGraph components: {e}")
            raise
    
    def _create_workflow(self):
        """Create the agricultural workflow graph"""
        
        # Create the state graph
        workflow = StateGraph(AgriculturalWorkflowState)
        
        # Add nodes
        workflow.add_node("analyze_query", self._analyze_query_node)
        workflow.add_node("weather_analysis", self._weather_analysis_node)
        workflow.add_node("regulatory_check", self._regulatory_check_node)
        workflow.add_node("farm_data_analysis", self._farm_data_analysis_node)
        workflow.add_node("synthesis", self._synthesis_node)
        workflow.add_node("error_handler", self._error_handler_node)
        
        # Set entry point
        workflow.set_entry_point("analyze_query")
        
        # Add conditional edges
        workflow.add_conditional_edges(
            "analyze_query",
            self._route_after_analysis,
            {
                "weather": "weather_analysis",
                "regulatory": "regulatory_check",
                "farm_data": "farm_data_analysis",
                "synthesis": "synthesis",
                "error": "error_handler"
            }
        )
        
        workflow.add_conditional_edges(
            "weather_analysis",
            self._route_after_weather,
            {
                "regulatory": "regulatory_check",
                "farm_data": "farm_data_analysis",
                "synthesis": "synthesis",
                "error": "error_handler"
            }
        )
        
        workflow.add_conditional_edges(
            "regulatory_check",
            self._route_after_regulatory,
            {
                "farm_data": "farm_data_analysis",
                "synthesis": "synthesis",
                "error": "error_handler"
            }
        )
        
        workflow.add_conditional_edges(
            "farm_data_analysis",
            self._route_after_farm_data,
            {
                "synthesis": "synthesis",
                "error": "error_handler"
            }
        )
        
        # End nodes
        workflow.add_edge("synthesis", END)
        workflow.add_edge("error_handler", END)
        
        # Compile the workflow
        self.app = workflow.compile()
        
        logger.info("LangGraph workflow created and compiled")
    
    async def process_agricultural_query(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process agricultural query through LangGraph workflow"""
        try:
            # Initialize state
            initial_state = AgriculturalWorkflowState(
                messages=[HumanMessage(content=query)],
                query=query,
                context=context or {},
                weather_data=None,
                regulatory_status=None,
                farm_data=None,
                recommendations=[],
                confidence=0.0,
                agent_type="unknown",
                processing_steps=[],
                errors=[]
            )
            
            # Execute workflow
            final_state = await self.app.ainvoke(initial_state)
            
            # Extract response from final message
            response_content = ""
            if final_state["messages"]:
                last_message = final_state["messages"][-1]
                if isinstance(last_message, AIMessage):
                    response_content = last_message.content
            
            return {
                "response": response_content,
                "agent_type": final_state["agent_type"],
                "confidence": final_state["confidence"],
                "recommendations": final_state["recommendations"],
                "weather_data": final_state["weather_data"],
                "regulatory_status": final_state["regulatory_status"],
                "farm_data": final_state["farm_data"],
                "processing_steps": final_state["processing_steps"],
                "metadata": {
                    "workflow_executed": True,
                    "steps_completed": len(final_state["processing_steps"]),
                    "errors": final_state["errors"]
                }
            }
            
        except Exception as e:
            logger.error(f"LangGraph workflow execution failed: {e}")
            return {
                "response": f"Erreur lors du traitement de votre demande: {str(e)}",
                "agent_type": "error",
                "confidence": 0.0,
                "recommendations": [],
                "metadata": {"error": str(e)}
            }
    
    async def _analyze_query_node(self, state: AgriculturalWorkflowState) -> AgriculturalWorkflowState:
        """Analyze the query to determine routing"""
        try:
            query = state["query"].lower()
            processing_steps = state["processing_steps"] + ["query_analysis"]
            
            # Determine agent type and confidence
            if any(word in query for word in ["météo", "temps", "pluie", "vent"]):
                agent_type = "weather"
                confidence = 0.9
            elif any(word in query for word in ["réglementation", "amm", "znt", "conformité"]):
                agent_type = "regulatory"
                confidence = 0.9
            elif any(word in query for word in ["parcelle", "exploitation", "intervention"]):
                agent_type = "farm_data"
                confidence = 0.8
            else:
                agent_type = "general"
                confidence = 0.6
            
            # Update state
            state["agent_type"] = agent_type
            state["confidence"] = confidence
            state["processing_steps"] = processing_steps
            
            logger.info(f"Query analyzed: type={agent_type}, confidence={confidence}")
            
            return state
            
        except Exception as e:
            logger.error(f"Query analysis failed: {e}")
            state["errors"].append(f"Query analysis failed: {str(e)}")
            return state
    
    async def _weather_analysis_node(self, state: AgriculturalWorkflowState) -> AgriculturalWorkflowState:
        """Perform weather analysis"""
        try:
            processing_steps = state["processing_steps"] + ["weather_analysis"]
            
            # Get weather data using tool
            from app.tools.weather_agent.get_weather_data_tool import GetWeatherDataTool
            weather_tool = GetWeatherDataTool()
            
            # Extract location from context or use default
            location = state["context"].get("location", "France")
            weather_result = weather_tool._run(location=location, days=7)
            
            # Parse weather data
            try:
                weather_data = json.loads(weather_result)
            except:
                weather_data = {"raw_result": weather_result}
            
            state["weather_data"] = weather_data
            state["processing_steps"] = processing_steps
            
            logger.info("Weather analysis completed")
            
            return state
            
        except Exception as e:
            logger.error(f"Weather analysis failed: {e}")
            state["errors"].append(f"Weather analysis failed: {str(e)}")
            return state
    
    async def _regulatory_check_node(self, state: AgriculturalWorkflowState) -> AgriculturalWorkflowState:
        """Perform regulatory compliance check"""
        try:
            processing_steps = state["processing_steps"] + ["regulatory_check"]
            
            # Extract product information from query
            query_lower = state["query"].lower()
            products = []
            
            if "glyphosate" in query_lower:
                products.append("glyphosate")
            if "cuivre" in query_lower:
                products.append("cuivre")
            
            regulatory_results = []
            if products:
                for product in products:
                    result = self.regulatory_service.validate_product_usage(
                        product_name=product,
                        crop_type=state["context"].get("crop_type")
                    )
                    regulatory_results.append(result)
            
            state["regulatory_status"] = {
                "products_checked": products,
                "results": regulatory_results,
                "compliant": all(r.get("is_compliant", False) for r in regulatory_results)
            }
            state["processing_steps"] = processing_steps
            
            logger.info(f"Regulatory check completed for {len(products)} products")
            
            return state
            
        except Exception as e:
            logger.error(f"Regulatory check failed: {e}")
            state["errors"].append(f"Regulatory check failed: {str(e)}")
            return state
    
    async def _farm_data_analysis_node(self, state: AgriculturalWorkflowState) -> AgriculturalWorkflowState:
        """Perform farm data analysis"""
        try:
            processing_steps = state["processing_steps"] + ["farm_data_analysis"]
            
            # Get farm data from integrated database
            from sqlalchemy import text
            from app.core.database import AsyncSessionLocal
            
            farm_data = {}
            siret = state["context"].get("farm_siret")
            
            async with AsyncSessionLocal() as session:
                if siret:
                    # Get specific farm data
                    result = await session.execute(text("""
                        SELECT e.nom, COUNT(DISTINCT p.id) as parcelles,
                               COUNT(DISTINCT i.uuid_intervention) as interventions
                        FROM farm_operations.exploitations e
                        LEFT JOIN farm_operations.parcelles p ON e.siret = p.siret_exploitation
                        LEFT JOIN farm_operations.interventions i ON p.id = i.id_parcelle
                        WHERE e.siret = :siret
                        GROUP BY e.siret, e.nom
                    """), {"siret": siret})
                    
                    data = result.fetchone()
                    if data:
                        farm_data = {
                            "exploitation_name": data[0],
                            "parcelles_count": data[1],
                            "interventions_count": data[2]
                        }
                else:
                    # Get general statistics
                    result = await session.execute(text("""
                        SELECT COUNT(DISTINCT e.siret) as exploitations,
                               COUNT(DISTINCT p.id) as parcelles,
                               COUNT(DISTINCT i.uuid_intervention) as interventions
                        FROM farm_operations.exploitations e
                        LEFT JOIN farm_operations.parcelles p ON e.siret = p.siret_exploitation
                        LEFT JOIN farm_operations.interventions i ON p.id = i.id_parcelle
                    """))
                    
                    data = result.fetchone()
                    farm_data = {
                        "total_exploitations": data[0],
                        "total_parcelles": data[1],
                        "total_interventions": data[2]
                    }
            
            state["farm_data"] = farm_data
            state["processing_steps"] = processing_steps
            
            logger.info("Farm data analysis completed")

            return state

        except Exception as e:
            logger.error(f"Farm data analysis failed: {e}")
            state["errors"].append(f"Farm data analysis failed: {str(e)}")
            return state

    async def _synthesis_node(self, state: AgriculturalWorkflowState) -> AgriculturalWorkflowState:
        """Synthesize final response from all collected data"""
        try:
            processing_steps = state["processing_steps"] + ["synthesis"]

            # Create synthesis prompt
            synthesis_prompt = f"""
            En tant qu'expert agricole français, synthétise une réponse complète basée sur:

            Demande: {state["query"]}

            Données collectées:
            - Type d'agent: {state["agent_type"]}
            - Données météo: {json.dumps(state["weather_data"], ensure_ascii=False) if state["weather_data"] else "Non disponibles"}
            - Statut réglementaire: {json.dumps(state["regulatory_status"], ensure_ascii=False) if state["regulatory_status"] else "Non vérifié"}
            - Données d'exploitation: {json.dumps(state["farm_data"], ensure_ascii=False) if state["farm_data"] else "Non disponibles"}

            Fournis une réponse structurée avec:
            1. Réponse directe à la question
            2. Recommandations pratiques
            3. Points de vigilance réglementaire
            4. Considérations météorologiques (si applicable)
            """

            # Generate response using LLM
            response = await self.llm.ainvoke([HumanMessage(content=synthesis_prompt)])

            # Extract recommendations
            recommendations = self._extract_recommendations(response.content)

            # Update state
            state["messages"].append(response)
            state["recommendations"] = recommendations
            state["processing_steps"] = processing_steps

            logger.info("Synthesis completed")

            return state

        except Exception as e:
            logger.error(f"Synthesis failed: {e}")
            state["errors"].append(f"Synthesis failed: {str(e)}")
            # Create fallback response
            fallback_response = AIMessage(content=f"Désolé, je n'ai pas pu traiter complètement votre demande: {str(e)}")
            state["messages"].append(fallback_response)
            return state

    async def _error_handler_node(self, state: AgriculturalWorkflowState) -> AgriculturalWorkflowState:
        """Handle errors and provide fallback response"""
        try:
            error_summary = "; ".join(state["errors"])
            fallback_response = AIMessage(
                content=f"Une erreur s'est produite lors du traitement de votre demande. "
                       f"Erreurs: {error_summary}. "
                       f"Veuillez reformuler votre question ou contacter le support."
            )

            state["messages"].append(fallback_response)
            state["processing_steps"].append("error_handling")

            logger.warning(f"Error handler activated: {error_summary}")

            return state

        except Exception as e:
            logger.error(f"Error handler failed: {e}")
            return state

    def _route_after_analysis(self, state: AgriculturalWorkflowState) -> str:
        """Route after query analysis"""
        if state["errors"]:
            return "error"

        agent_type = state["agent_type"]

        # Route based on agent type
        if agent_type == "weather":
            return "weather"
        elif agent_type == "regulatory":
            return "regulatory"
        elif agent_type == "farm_data":
            return "farm_data"
        else:
            return "synthesis"

    def _route_after_weather(self, state: AgriculturalWorkflowState) -> str:
        """Route after weather analysis"""
        if state["errors"]:
            return "error"

        # Check if we need regulatory analysis
        query_lower = state["query"].lower()
        if any(word in query_lower for word in ["produit", "traitement", "conformité"]):
            return "regulatory"

        # Check if we need farm data
        if any(word in query_lower for word in ["parcelle", "exploitation"]):
            return "farm_data"

        return "synthesis"

    def _route_after_regulatory(self, state: AgriculturalWorkflowState) -> str:
        """Route after regulatory check"""
        if state["errors"]:
            return "error"

        # Check if we need farm data
        query_lower = state["query"].lower()
        if any(word in query_lower for word in ["parcelle", "exploitation", "intervention"]):
            return "farm_data"

        return "synthesis"

    def _route_after_farm_data(self, state: AgriculturalWorkflowState) -> str:
        """Route after farm data analysis"""
        if state["errors"]:
            return "error"

        return "synthesis"

    def _extract_recommendations(self, response: str) -> List[str]:
        """Extract recommendations from response"""
        recommendations = []
        lines = response.split('\n')

        for line in lines:
            line = line.strip()
            if any(indicator in line.lower() for indicator in [
                "recommande", "conseille", "suggère", "préconise",
                "il faut", "vous devez", "pensez à"
            ]):
                recommendations.append(line)

        return recommendations[:5]

    # Routing functions for conditional edges
    def _route_after_analysis(self, state: AgriculturalWorkflowState) -> str:
        """Route after query analysis"""
        agent_type = state.get("agent_type", "general")

        if agent_type == "weather":
            return "weather"
        elif agent_type == "regulatory":
            return "regulatory"
        elif agent_type == "farm_data":
            return "farm_data"
        elif state.get("errors"):
            return "error"
        else:
            return "synthesis"

    def _route_after_weather(self, state: AgriculturalWorkflowState) -> str:
        """Route after weather analysis"""
        if state.get("errors"):
            return "error"
        elif state["agent_type"] in ["regulatory", "farm_data"]:
            return "regulatory" if state["agent_type"] == "regulatory" else "farm_data"
        else:
            return "synthesis"

    def _route_after_regulatory(self, state: AgriculturalWorkflowState) -> str:
        """Route after regulatory check"""
        if state.get("errors"):
            return "error"
        elif state["agent_type"] == "farm_data" and not state.get("farm_data"):
            return "farm_data"
        else:
            return "synthesis"

    def _route_after_farm_data(self, state: AgriculturalWorkflowState) -> str:
        """Route after farm data analysis"""
        if state.get("errors"):
            return "error"
        else:
            return "synthesis"

    async def get_workflow_status(self) -> Dict[str, Any]:
        """Get workflow service status"""
        return {
            "service_name": "LangGraph Workflow Service",
            "initialized": self.app is not None,
            "llm_available": self.llm is not None,
            "regulatory_service_available": self.regulatory_service is not None,
            "workflow_nodes": [
                "analyze_query", "weather_analysis", "regulatory_check",
                "farm_data_analysis", "synthesis", "error_handler"
            ],
            "supported_agent_types": ["weather", "regulatory", "farm_data", "general"]
        }
