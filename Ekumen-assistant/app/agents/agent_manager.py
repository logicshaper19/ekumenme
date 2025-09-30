"""
Agent Manager - Single Purpose Component

Job: Manage and coordinate agricultural agents.
Input: Agent requests and configurations
Output: Agent responses and coordination

This component does ONLY:
- Execute specific, well-defined function
- Take structured inputs, return structured outputs
- Contain domain-specific business logic
- Be stateless and reusable

No prompting logic, no orchestration, no agent responsibilities.
"""

from typing import Dict, List, Any, Optional
import logging
import asyncio
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)

class AgentType(Enum):
    """Agricultural agent types."""
    FARM_DATA = "farm_data"
    WEATHER = "weather"
    CROP_HEALTH = "crop_health"
    PLANNING = "planning"
    REGULATORY = "regulatory"
    SUSTAINABILITY = "sustainability"
    INTERNET = "internet"
    SUPPLIER = "supplier"
    MARKET_PRICES = "market_prices"

@dataclass
class AgentProfile:
    """Agent profile configuration."""
    agent_type: AgentType
    name: str
    description: str
    capabilities: List[str]
    cost_per_request: float

class AgentManager:
    """
    Manager for agricultural agents.
    
    Job: Manage and coordinate agricultural agents.
    Input: Agent requests and configurations
    Output: Agent responses and coordination
    """
    
    def __init__(self):
        self.agents = {}
        self.agent_profiles = self._initialize_agent_profiles()
    
    def _initialize_agent_profiles(self) -> Dict[AgentType, AgentProfile]:
        """Initialize agent profiles."""
        return {
            AgentType.FARM_DATA: AgentProfile(
                agent_type=AgentType.FARM_DATA,
                name="Farm Data Agent",
                description="Analyzes farm data and performance metrics",
                capabilities=["data_analysis", "performance_metrics", "trends"],
                cost_per_request=0.05
            ),
            AgentType.WEATHER: AgentProfile(
                agent_type=AgentType.WEATHER,
                name="Weather Agent",
                description="Provides weather intelligence and forecasts",
                capabilities=["weather_forecast", "risk_analysis", "intervention_windows"],
                cost_per_request=0.03
            ),
            AgentType.CROP_HEALTH: AgentProfile(
                agent_type=AgentType.CROP_HEALTH,
                name="Crop Health Agent",
                description="Monitors crop health and diagnoses issues",
                capabilities=["disease_diagnosis", "pest_identification", "nutrient_analysis"],
                cost_per_request=0.07
            ),
            AgentType.PLANNING: AgentProfile(
                agent_type=AgentType.PLANNING,
                name="Planning Agent",
                description="Coordinates operational planning and optimization",
                capabilities=["task_planning", "resource_optimization", "cost_analysis"],
                cost_per_request=0.06
            ),
            AgentType.REGULATORY: AgentProfile(
                agent_type=AgentType.REGULATORY,
                name="Regulatory Agent",
                description="Ensures regulatory compliance and safety",
                capabilities=["compliance_check", "amm_lookup", "safety_guidelines"],
                cost_per_request=0.04
            ),
            AgentType.SUSTAINABILITY: AgentProfile(
                agent_type=AgentType.SUSTAINABILITY,
                name="Sustainability Agent",
                description="Analyzes environmental impact and sustainability",
                capabilities=["carbon_footprint", "biodiversity", "soil_health"],
                cost_per_request=0.08
            ),
            AgentType.INTERNET: AgentProfile(
                agent_type=AgentType.INTERNET,
                name="Internet Agent",
                description="Searches the web for real-time information",
                capabilities=["web_search", "news", "market_prices", "general_info"],
                cost_per_request=0.02
            ),
            AgentType.SUPPLIER: AgentProfile(
                agent_type=AgentType.SUPPLIER,
                name="Supplier Agent",
                description="Finds agricultural suppliers and products",
                capabilities=["supplier_search", "product_availability", "price_comparison"],
                cost_per_request=0.02
            ),
            AgentType.MARKET_PRICES: AgentProfile(
                agent_type=AgentType.MARKET_PRICES,
                name="Market Prices Agent",
                description="Provides real-time agricultural commodity prices",
                capabilities=["price_lookup", "market_trends", "price_comparison"],
                cost_per_request=0.02
            )
        }
    
    def get_agent_profile(self, agent_type: AgentType) -> Optional[AgentProfile]:
        """Get agent profile by type."""
        return self.agent_profiles.get(agent_type)
    
    def list_available_agents(self) -> List[AgentProfile]:
        """List all available agents."""
        return list(self.agent_profiles.values())
    
    def get_agent_capabilities(self, agent_type: AgentType) -> List[str]:
        """Get capabilities for a specific agent."""
        profile = self.get_agent_profile(agent_type)
        return profile.capabilities if profile else []
    
    def estimate_cost(self, agent_type: AgentType, request_count: int = 1) -> float:
        """Estimate cost for agent requests."""
        profile = self.get_agent_profile(agent_type)
        return profile.cost_per_request * request_count if profile else 0.0

    def execute_agent(self, agent_type: str, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute an agent with a message.

        Args:
            agent_type: Type of agent to execute
            message: Message to process
            context: Additional context for processing

        Returns:
            Dict containing the agent response
        """
        try:
            # Convert string agent_type to AgentType enum
            if isinstance(agent_type, str):
                agent_type_map = {
                    "farm_data": AgentType.FARM_DATA,
                    "weather": AgentType.WEATHER,
                    "crop_health": AgentType.CROP_HEALTH,
                    "planning": AgentType.PLANNING,
                    "regulatory": AgentType.REGULATORY,
                    "sustainability": AgentType.SUSTAINABILITY,
                    "internet": AgentType.INTERNET,
                    "supplier": AgentType.SUPPLIER,
                    "market_prices": AgentType.MARKET_PRICES
                }
                agent_enum = agent_type_map.get(agent_type)
                if not agent_enum:
                    return {
                        "response": f"Type d'agent '{agent_type}' non reconnu",
                        "error": "Unknown agent type"
                    }
            else:
                agent_enum = agent_type

            # Get agent profile
            profile = self.get_agent_profile(agent_enum)
            if not profile:
                return {
                    "response": f"Agent {agent_type} non disponible",
                    "error": "Agent not found"
                }

            # For new Tavily-powered agents, use actual implementation
            if agent_enum in [AgentType.INTERNET, AgentType.SUPPLIER, AgentType.MARKET_PRICES]:
                result = self._execute_tavily_agent(agent_enum, message, context or {})
                # result is a dict with 'response' and optionally 'sources'
                return {
                    "response": result.get("response", ""),
                    "sources": result.get("sources", []),  # Include sources if available
                    "agent_type": profile.agent_type.value,
                    "agent_name": profile.name,
                    "capabilities": profile.capabilities,
                    "metadata": {
                        "cost": profile.cost_per_request,
                        "message_length": len(message),
                        "context_provided": bool(context),
                        **(result.get("metadata", {}))  # Include agent metadata
                    }
                }
            else:
                # Generate response based on agent type (legacy agents)
                response = self._generate_agent_response(profile, message, context or {})
                return {
                    "response": response,
                    "agent_type": profile.agent_type.value,
                    "agent_name": profile.name,
                    "capabilities": profile.capabilities,
                    "metadata": {
                        "cost": profile.cost_per_request,
                        "message_length": len(message),
                        "context_provided": bool(context)
                    }
                }

        except Exception as e:
            logger.error(f"Agent execution error: {e}")
            return {
                "response": f"Désolé, une erreur s'est produite lors du traitement de votre demande: {str(e)}",
                "error": str(e)
            }

    def _generate_agent_response(self, profile: AgentProfile, message: str, context: Dict[str, Any]) -> str:
        """Generate a response based on agent profile and message."""
        agent_responses = {
            AgentType.FARM_DATA: f"""🌾 **{profile.name}** - Analyse de vos données d'exploitation

Votre demande : "{message}"

Je suis spécialisé dans l'analyse des données agricoles françaises. Je peux vous aider avec :
- Analyse des performances de vos parcelles
- Suivi des interventions et leur efficacité
- Métriques de rendement et optimisation
- Contexte régional et comparaisons

Pour une analyse complète, j'aurais besoin d'accéder à vos données MesParcelles ou de connaître votre SIRET d'exploitation.""",

            AgentType.WEATHER: f"""🌤️ **{profile.name}** - Intelligence météorologique

Votre demande : "{message}"

Je suis votre conseiller météo agricole. Je peux vous fournir :
- Conditions météo actuelles et prévisions
- Alertes météo spécifiques à l'agriculture
- Fenêtres d'intervention optimales
- Analyse des risques climatiques

Pour des prévisions précises, indiquez-moi votre localisation ou vos parcelles.""",

            AgentType.CROP_HEALTH: f"""🌱 **{profile.name}** - Diagnostic phytosanitaire

Votre demande : "{message}"

Je suis expert en santé des cultures. Je peux vous aider avec :
- Diagnostic de maladies et ravageurs
- Identification des carences nutritionnelles
- Recommandations de traitement
- Stratégies de prévention

Pour un diagnostic précis, décrivez les symptômes observés et le type de culture.""",

            AgentType.PLANNING: f"""📅 **{profile.name}** - Optimisation opérationnelle

Votre demande : "{message}"

Je coordonne vos activités agricoles. Mes services incluent :
- Planification des interventions
- Optimisation des ressources
- Coordination des équipes
- Gestion des priorités

Partagez vos objectifs et contraintes pour une planification personnalisée.""",

            AgentType.REGULATORY: f"""⚖️ **{profile.name}** - Conformité réglementaire

Votre demande : "{message}"

Je vous guide dans la réglementation phytosanitaire française :
- Recherche de produits AMM
- Conditions d'usage autorisées
- Classifications de sécurité
- Vérification de conformité

Précisez le produit ou la situation réglementaire qui vous préoccupe.""",

            AgentType.SUSTAINABILITY: f"""🌍 **{profile.name}** - Durabilité agricole

Votre demande : "{message}"

Je vous accompagne vers une agriculture durable :
- Métriques environnementales
- Analyse d'impact carbone
- Optimisation des ressources
- Reporting de durabilité

Décrivez vos pratiques actuelles pour des recommandations personnalisées."""
        }

        return agent_responses.get(profile.agent_type, f"Réponse de {profile.name} pour: {message}")

    def _execute_tavily_agent(self, agent_type: AgentType, message: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute Tavily-powered agents (Internet, Supplier, Market Prices)

        Returns:
            Dict with 'response' and optionally 'sources' keys
        """
        try:
            # Import agents here to avoid circular imports
            from app.agents.internet_agent import InternetAgent
            from app.agents.supplier_agent import SupplierAgent

            # Create event loop if needed
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

            # Execute the appropriate agent
            if agent_type == AgentType.INTERNET:
                agent = InternetAgent()
                result = loop.run_until_complete(agent.process(message, context))
            elif agent_type == AgentType.SUPPLIER:
                agent = SupplierAgent()
                result = loop.run_until_complete(agent.process(message, context))
            elif agent_type == AgentType.MARKET_PRICES:
                # Market prices uses Internet agent with specific query
                agent = InternetAgent()
                result = loop.run_until_complete(agent.process(message, context))
            else:
                return {"response": f"Agent type {agent_type} not implemented"}

            # Return full result dict (includes response and sources)
            if isinstance(result, dict):
                return result
            return {"response": str(result)}

        except Exception as e:
            logger.error(f"Error executing Tavily agent {agent_type}: {e}")
            return {"response": f"❌ Erreur lors de l'exécution de l'agent: {str(e)}"}
