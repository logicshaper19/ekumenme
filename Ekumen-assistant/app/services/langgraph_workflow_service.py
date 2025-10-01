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

    # Response templates
    SIMPLE_TEMPLATE = """Tu es un conseiller agricole expert. Réponds de manière CONCISE et DIRECTE.

QUESTION: {query}
DONNÉES: {data_summary}

INSTRUCTIONS:
- Réponds DIRECTEMENT (3-5 phrases maximum)
- Utilise les données réelles fournies
- Pas d'emoji, ton professionnel
- **Gras** pour les points clés
- Chiffres précis avec unités

Réponds maintenant:"""

    MEDIUM_TEMPLATE = """Tu es un conseiller agricole expert. Réponds de manière STRUCTURÉE mais CONCISE.

QUESTION: {query}
DONNÉES: {data_summary}

INSTRUCTIONS:
- 1-2 paragraphes (8-10 phrases max)
- **Titre en Gras:** pour le titre principal
- Listes à puces pour recommandations
- Chiffres précis, pas d'emoji
- Termine par une recommandation claire

Réponds maintenant:"""

    COMPLEX_TEMPLATE = """Tu es un conseiller agricole expert français avec 20 ans d'expérience.

QUESTION: {query}
DONNÉES: {data_summary}
LOCALISATION: {location}

INSTRUCTIONS - Structure complète:
1. **Analyse de la Situation:** Contexte et données clés
2. **Recommandations Principales:** Actions prioritaires avec listes à puces
3. **Considérations Techniques:** Détails pratiques (doses, timing, conditions)
4. **Points de Vigilance:** Risques et précautions
5. **Prochaines Étapes:** Actions concrètes à court terme

STYLE:
- Professionnel et précis
- Chiffres avec unités (°C, mm, jours, €, kg/ha)
- Pas d'emoji
- Actionnable et pratique

Réponds maintenant:"""

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
        workflow.add_node("crop_feasibility", self._crop_feasibility_node)
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
                "crop_feasibility": "crop_feasibility",
                "regulatory": "regulatory_check",
                "farm_data": "farm_data_analysis",
                "synthesis": "synthesis",
                "error": "error_handler"
            }
        )

        workflow.add_conditional_edges(
            "crop_feasibility",
            self._route_after_feasibility,
            {
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

            # Extract location from context OR query
            location = state["context"].get("location")
            if not location:
                location = self._extract_location_from_query(state["query"])

            logger.info(f"Weather analysis for location: {location}")
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

    async def _crop_feasibility_node(self, state: AgriculturalWorkflowState) -> AgriculturalWorkflowState:
        """Check crop feasibility for location"""
        try:
            processing_steps = state["processing_steps"] + ["crop_feasibility"]

            # Import the crop feasibility tool
            from app.tools.planning_agent.check_crop_feasibility_tool import CheckCropFeasibilityTool
            feasibility_tool = CheckCropFeasibilityTool()

            # Extract crop and location from query or context
            crop = state["context"].get("crop", self._extract_crop_from_query(state["query"]))
            location = state["context"].get("location", self._extract_location_from_query(state["query"]))

            if not crop:
                logger.warning("No crop detected in query, skipping feasibility check")
                state["processing_steps"] = processing_steps
                return state

            # Run feasibility check
            feasibility_result = feasibility_tool._run(
                crop=crop,
                location=location,
                include_alternatives=True
            )

            # Parse result
            try:
                feasibility_data = json.loads(feasibility_result)
            except:
                feasibility_data = {"raw_result": feasibility_result}

            state["feasibility_data"] = feasibility_data
            state["processing_steps"] = processing_steps

            logger.info(f"Crop feasibility check completed for {crop} at {location}")

            return state

        except Exception as e:
            logger.error(f"Crop feasibility check failed: {e}")
            state["errors"].append(f"Crop feasibility check failed: {str(e)}")
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
            location = state["context"].get("location", self._extract_location_from_query(state["query"]))

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

                # Get regional crop data if location is specified
                if location and location.lower() != "france":
                    try:
                        # Query regional crops (simplified - would need proper commune/department mapping)
                        regional_result = await session.execute(text("""
                            SELECT DISTINCT p.nom_culture, COUNT(*) as frequency
                            FROM farm_operations.parcelles p
                            WHERE p.commune ILIKE :location OR p.code_postal LIKE :postal_prefix
                            GROUP BY p.nom_culture
                            ORDER BY frequency DESC
                            LIMIT 10
                        """), {"location": f"%{location}%", "postal_prefix": f"{location[:2]}%"})

                        regional_crops = []
                        for row in regional_result.fetchall():
                            if row[0]:  # Only if crop name exists
                                regional_crops.append({
                                    "crop": row[0],
                                    "frequency": row[1]
                                })

                        if regional_crops:
                            farm_data["regional_crops"] = regional_crops
                            logger.info(f"Found {len(regional_crops)} regional crops for {location}")
                    except Exception as e:
                        logger.warning(f"Could not fetch regional crops: {e}")
            
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

            # STEP 1: Classify query complexity using LangChain
            from app.services.query_classifier import get_classifier

            classifier = get_classifier(use_llm=True)  # Use LangChain LLM for classification
            classification = classifier.classify(state["query"])

            logger.info(f"Query classified as: {classification['complexity']} "
                       f"(confidence: {classification['confidence']:.2f}, "
                       f"method: {classification['method']})")

            # Format collected data for better readability
            weather_summary = self._format_weather_data(state.get("weather_data"))
            regulatory_summary = self._format_regulatory_data(state.get("regulatory_status"))
            farm_summary = self._format_farm_data(state.get("farm_data"))
            feasibility_summary = self._format_feasibility_data(state.get("feasibility_data"))

            # Extract location and crop from query
            location = state["context"].get("location", self._extract_location_from_query(state["query"]))
            crop = state["context"].get("crop", self._extract_crop_from_query(state["query"]))

            # STEP 2: Create data summary for prompt
            data_summary = self._create_data_summary(
                weather_summary,
                regulatory_summary,
                farm_summary,
                feasibility_summary
            )

            # STEP 3: Select appropriate response template based on complexity
            complexity = classification["complexity"]

            if complexity == "simple":
                template = self.SIMPLE_TEMPLATE
            elif complexity == "medium":
                template = self.MEDIUM_TEMPLATE
            else:
                template = self.COMPLEX_TEMPLATE

            synthesis_prompt = template.format(
                query=state["query"],
                data_summary=data_summary,
                location=location
            )

            logger.info(f"Using {complexity} response template")

            # Generate response using LLM
            response = await self.llm.ainvoke([HumanMessage(content=synthesis_prompt)])

            # Extract recommendations
            recommendations = self._extract_recommendations(response.content)

            # Update state
            state["messages"].append(response)
            state["recommendations"] = recommendations
            state["processing_steps"] = processing_steps

            logger.info("Synthesis completed with enhanced structure")

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

        query_lower = state["query"].lower()

        # Check if this is a crop feasibility question
        if any(word in query_lower for word in ["planter", "cultiver", "culture de", "peut-on", "possible"]):
            return "crop_feasibility"

        # Check if we need regulatory analysis
        if any(word in query_lower for word in ["produit", "traitement", "conformité"]):
            return "regulatory"

        # Check if we need farm data
        if any(word in query_lower for word in ["parcelle", "exploitation"]):
            return "farm_data"

        return "synthesis"

    def _route_after_feasibility(self, state: AgriculturalWorkflowState) -> str:
        """Route after crop feasibility check"""
        if state["errors"]:
            return "error"

        query_lower = state["query"].lower()

        # Check if we need farm data for regional alternatives
        if any(word in query_lower for word in ["région", "local", "alternative"]):
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

    def _create_data_summary(
        self,
        weather_summary: str,
        regulatory_summary: str,
        farm_summary: str,
        feasibility_summary: str
    ) -> str:
        """Create concise data summary for prompt"""
        sections = []

        if weather_summary and weather_summary != "Aucune donnée météo disponible.":
            sections.append(weather_summary)

        if feasibility_summary and feasibility_summary != "Aucune analyse de faisabilité disponible.":
            sections.append(feasibility_summary)

        if regulatory_summary and regulatory_summary != "Aucune donnée réglementaire disponible.":
            sections.append(regulatory_summary)

        if farm_summary and farm_summary != "Aucune donnée d'exploitation disponible.":
            sections.append(farm_summary)

        if not sections:
            return "Aucune donnée spécifique disponible pour cette requête."

        return "\n\n".join(sections)

    def _format_weather_data(self, weather_data: Optional[Dict[str, Any]]) -> str:
        """Format weather data for synthesis prompt"""
        if not weather_data:
            return "**Données météo**: Non disponibles"

        try:
            formatted = "**DONNÉES MÉTÉOROLOGIQUES:**\n"
            if isinstance(weather_data, dict):
                # Location
                if "location" in weather_data:
                    formatted += f"- Localisation: {weather_data['location']}\n"

                # Handle new weather_conditions structure
                if "weather_conditions" in weather_data and isinstance(weather_data["weather_conditions"], list):
                    conditions = weather_data["weather_conditions"]
                    if conditions:
                        # Current/first day
                        today = conditions[0]
                        formatted += f"- Température aujourd'hui: {today.get('temperature_min', 'N/A')}°C - {today.get('temperature_max', 'N/A')}°C\n"
                        formatted += f"- Humidité: {today.get('humidity', 'N/A')}%\n"
                        formatted += f"- Vent: {today.get('wind_speed', 'N/A')} km/h ({today.get('wind_direction', 'N/A')})\n"
                        formatted += f"- Précipitations: {today.get('precipitation', 0)} mm\n"

                        # 7-day forecast summary
                        if len(conditions) > 1:
                            temps_min = [c.get('temperature_min', 0) for c in conditions]
                            temps_max = [c.get('temperature_max', 0) for c in conditions]
                            precip_total = sum(c.get('precipitation', 0) for c in conditions)
                            formatted += f"- Prévisions 7 jours: {min(temps_min)}°C à {max(temps_max)}°C\n"
                            formatted += f"- Précipitations totales prévues: {precip_total} mm\n"

                # Fallback for old structure
                elif "temperature" in weather_data:
                    formatted += f"- Température actuelle: {weather_data['temperature']}°C\n"
                    if "forecast" in weather_data and isinstance(weather_data["forecast"], list):
                        temps = [f["temperature"] for f in weather_data["forecast"] if "temperature" in f]
                        if temps:
                            formatted += f"- Température min/max prévue: {min(temps)}°C / {max(temps)}°C\n"

                # Data source
                if "data_source" in weather_data:
                    source = "API réelle" if weather_data["data_source"] != "mock_data" else "données simulées"
                    formatted += f"- Source: {source}\n"

            return formatted
        except Exception as e:
            logger.error(f"Weather data formatting error: {e}")
            return f"**Données météo**: Disponibles mais erreur de formatage ({str(e)})"

    def _format_regulatory_data(self, regulatory_status: Optional[Dict[str, Any]]) -> str:
        """Format regulatory data for synthesis prompt"""
        if not regulatory_status:
            return "**Statut réglementaire**: Non vérifié"

        try:
            formatted = "**STATUT RÉGLEMENTAIRE:**\n"
            if isinstance(regulatory_status, dict):
                if "products_checked" in regulatory_status:
                    formatted += f"- Produits vérifiés: {', '.join(regulatory_status['products_checked'])}\n"
                if "compliant" in regulatory_status:
                    status = "✅ Conforme" if regulatory_status["compliant"] else "❌ Non conforme"
                    formatted += f"- Conformité: {status}\n"
            return formatted
        except Exception as e:
            return f"**Statut réglementaire**: Erreur de formatage ({str(e)})"

    def _format_farm_data(self, farm_data: Optional[Dict[str, Any]]) -> str:
        """Format farm data for synthesis prompt"""
        if not farm_data:
            return "**Données d'exploitation**: Non disponibles"

        try:
            formatted = "**DONNÉES D'EXPLOITATION:**\n"
            if isinstance(farm_data, dict):
                if "exploitation_name" in farm_data:
                    formatted += f"- Exploitation: {farm_data['exploitation_name']}\n"
                if "parcelles_count" in farm_data:
                    formatted += f"- Nombre de parcelles: {farm_data['parcelles_count']}\n"
                if "interventions_count" in farm_data:
                    formatted += f"- Interventions enregistrées: {farm_data['interventions_count']}\n"
                if "regional_crops" in farm_data:
                    crops = [c["crop"] for c in farm_data["regional_crops"][:5]]
                    formatted += f"- Cultures régionales courantes: {', '.join(crops)}\n"
            return formatted
        except Exception as e:
            return f"**Données d'exploitation**: Erreur de formatage ({str(e)})"

    def _format_feasibility_data(self, feasibility_data: Optional[Dict[str, Any]]) -> str:
        """Format crop feasibility data for synthesis prompt"""
        if not feasibility_data:
            return "**Analyse de faisabilité**: Non effectuée"

        try:
            formatted = "**ANALYSE DE FAISABILITÉ:**\n"
            if isinstance(feasibility_data, dict):
                if "crop" in feasibility_data:
                    formatted += f"- Culture: {feasibility_data['crop']}\n"
                if "location" in feasibility_data:
                    formatted += f"- Localisation: {feasibility_data['location']}\n"
                if "is_feasible" in feasibility_data:
                    status = "✅ Faisable" if feasibility_data["is_feasible"] else "❌ Difficile/Impossible en pleine terre"
                    formatted += f"- Faisabilité: {status}\n"
                if "feasibility_score" in feasibility_data:
                    formatted += f"- Score de faisabilité: {feasibility_data['feasibility_score']}/10\n"
                if "limiting_factors" in feasibility_data and feasibility_data["limiting_factors"]:
                    formatted += f"- Facteurs limitants: {', '.join(feasibility_data['limiting_factors'])}\n"
                if "climate_data" in feasibility_data:
                    climate = feasibility_data["climate_data"]
                    if "temp_min_annual" in climate:
                        formatted += f"- Température minimale annuelle: {climate['temp_min_annual']}°C\n"
                    if "frost_days" in climate:
                        formatted += f"- Jours de gel par an: {climate['frost_days']}\n"
                if "alternatives" in feasibility_data and feasibility_data["alternatives"]:
                    alt_names = [a.get("name", a) if isinstance(a, dict) else a for a in feasibility_data["alternatives"][:3]]
                    formatted += f"- Alternatives recommandées: {', '.join(alt_names)}\n"
            return formatted
        except Exception as e:
            return f"**Analyse de faisabilité**: Erreur de formatage ({str(e)})"

    def _extract_location_from_query(self, query: str) -> str:
        """Extract location from query text"""
        import re
        # Look for "à [location]" or "en [location]" patterns
        patterns = [
            r'à\s+([A-Z][a-zéèêàâôûù]+(?:\s+[A-Z][a-zéèêàâôûù]+)?)',
            r'en\s+([A-Z][a-zéèêàâôûù]+)',
            r'dans\s+(?:le|la|les)\s+([A-Z][a-zéèêàâôûù]+)'
        ]
        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                return match.group(1)
        return "France"

    def _extract_crop_from_query(self, query: str) -> str:
        """Extract crop name from query text"""
        import re
        # Look for "planter/cultiver [crop]" patterns
        patterns = [
            r'(?:planter|cultiver|culture\s+de|culture\s+du)\s+([a-zéèêàâôûù]+)',
            r'(?:du|de\s+la|des)\s+([a-zéèêàâôûù]+)'
        ]
        for pattern in patterns:
            match = re.search(pattern, query.lower())
            if match:
                return match.group(1)
        return ""
