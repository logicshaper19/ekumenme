"""
Agent Manager - Agent Registry and Request Router

Job: Manage agent registry and route requests to appropriate agents.
Input: Agent requests and configurations
Output: Agent responses with standardized format

Agent Types:
- Production agents: Internet, Supplier, Market Prices (Tavily-powered), Weather, Crop Health, Farm Data, Planning, Regulatory, Sustainability (LangChain ReAct)
- Demo agents: None (all agents are production-ready!)

To upgrade demo agents to production:
1. Implement agent class in app/agents/
2. Add to _create_agent_instance() method
3. Remove from DEMO_AGENTS set
"""

from typing import Dict, List, Any, Optional
import logging
import asyncio
from enum import Enum
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Demo agents that return canned responses (not yet implemented)
# ALL AGENTS ARE NOW PRODUCTION-READY! 🎉
DEMO_AGENTS = set()

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
    Agent registry and request router.

    Manages agent lifecycle and routes requests to appropriate agents.

    Production agents (ALL AGENTS ARE PRODUCTION-READY! 🎉):
    - Internet, Supplier, Market Prices (Tavily-powered)
    - Weather (LangChain ReAct with 4 production tools)
    - Crop Health (LangChain ReAct with 4 production tools)
    - Farm Data (LangChain ReAct with 4 production tools)
    - Planning (LangChain ReAct with 5 production tools)
    - Regulatory (LangChain ReAct with 4 production tools)
    - Sustainability (LangChain ReAct with 4 production tools)

    Demo agents: None - all agents use production tools!
    """

    def __init__(self):
        self.agents = {}
        self.agent_profiles = self._initialize_agent_profiles()
        self._agent_instances: Dict[str, Any] = {}  # Cache for agent instances
        logger.info("AgentManager initialized with agent instance caching")
    
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

    def _is_demo_agent(self, agent_type: str) -> bool:
        """
        Check if agent is demo-only (returns canned responses).

        Args:
            agent_type: Agent type string (e.g., "farm_data", "internet")

        Returns:
            True if agent is demo-only, False if production agent
        """
        return agent_type.lower() in DEMO_AGENTS

    async def _get_or_create_agent(self, agent_type: str) -> Any:
        """
        Get cached agent instance or create new one.

        Args:
            agent_type: Agent type string

        Returns:
            Agent instance
        """
        if agent_type not in self._agent_instances:
            logger.info(f"Creating new agent instance for {agent_type}")
            self._agent_instances[agent_type] = await self._create_agent_instance(agent_type)
        return self._agent_instances[agent_type]

    async def _create_agent_instance(self, agent_type: str) -> Any:
        """
        Create a new agent instance.

        Args:
            agent_type: Agent type string

        Returns:
            New agent instance

        Raises:
            ValueError: If agent type is not supported
        """
        # Import agents lazily to avoid circular imports and missing dependencies
        agent_type_lower = agent_type.lower()

        if agent_type_lower == "weather":
            from app.agents.weather_agent import WeatherIntelligenceAgent
            return WeatherIntelligenceAgent()

        elif agent_type_lower == "crop_health":
            from app.agents.crop_health_agent import CropHealthIntelligenceAgent
            return CropHealthIntelligenceAgent()

        elif agent_type_lower == "farm_data":
            from app.agents.farm_data_agent import FarmDataIntelligenceAgent
            return FarmDataIntelligenceAgent()

        elif agent_type_lower == "planning":
            from app.agents.planning_agent import PlanningIntelligenceAgent
            return PlanningIntelligenceAgent()

        elif agent_type_lower == "regulatory":
            from app.agents.regulatory_agent import RegulatoryIntelligenceAgent
            return RegulatoryIntelligenceAgent()

        elif agent_type_lower == "sustainability":
            from app.agents.sustainability_agent import SustainabilityIntelligenceAgent
            return SustainabilityIntelligenceAgent()

        elif agent_type_lower in ["internet", "market_prices"]:
            from app.agents.internet_agent import InternetAgent
            return InternetAgent()

        elif agent_type_lower == "supplier":
            from app.agents.supplier_agent import SupplierAgent
            return SupplierAgent()

        else:
            raise ValueError(f"Unknown production agent type: {agent_type}")
    
    def get_agent_capabilities(self, agent_type: AgentType) -> List[str]:
        """Get capabilities for a specific agent."""
        profile = self.get_agent_profile(agent_type)
        return profile.capabilities if profile else []
    
    def estimate_cost(self, agent_type: AgentType, request_count: int = 1) -> float:
        """Estimate cost for agent requests."""
        profile = self.get_agent_profile(agent_type)
        return profile.cost_per_request * request_count if profile else 0.0

    async def execute_agent(self, agent_type: str, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute an agent with a message (async to support all agent types).

        Args:
            agent_type: Type of agent to execute (string like "farm_data", "internet")
            message: Message to process
            context: Additional context for processing

        Returns:
            Dict containing the agent response with standardized format:
            {
                "response": str,
                "agent_type": str,
                "agent_name": str,
                "capabilities": List[str],
                "metadata": {...},
                "sources": [...] (optional, for Tavily agents)
            }
        """
        try:
            # Normalize agent type to lowercase
            agent_type_str = agent_type.lower() if isinstance(agent_type, str) else agent_type.value.lower()

            # Convert string agent_type to AgentType enum
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

            agent_enum = agent_type_map.get(agent_type_str)
            if not agent_enum:
                return {
                    "response": f"Type d'agent '{agent_type}' non reconnu",
                    "error": "Unknown agent type"
                }

            # Get agent profile
            profile = self.get_agent_profile(agent_enum)
            if not profile:
                return {
                    "response": f"Agent {agent_type} non disponible",
                    "error": "Agent not found"
                }

            # Check if this is a demo agent or production agent
            if self._is_demo_agent(agent_type_str):
                # Demo agent - return canned response
                logger.info(f"Executing demo agent: {agent_type_str}")
                response = self._generate_demo_response(profile, message)
                return {
                    "response": response,
                    "agent_type": profile.agent_type.value,
                    "agent_name": profile.name,
                    "capabilities": profile.capabilities,
                    "metadata": {
                        "cost": profile.cost_per_request,
                        "message_length": len(message),
                        "context_provided": bool(context),
                        "is_demo": True
                    }
                }
            else:
                # Production agent - execute actual agent
                logger.info(f"Executing production agent: {agent_type_str}")
                agent = await self._get_or_create_agent(agent_type_str)
                result = await agent.process(message, context or {})

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
                        "is_demo": False,
                        **(result.get("metadata", {}))  # Include agent metadata
                    }
                }

        except ValueError as e:
            # Configuration or validation errors
            logger.error(f"Agent configuration error: {e}")
            return {
                "response": f"Erreur de configuration de l'agent: {str(e)}",
                "error": str(e),
                "error_type": "configuration"
            }
        except Exception as e:
            # Unexpected errors
            logger.error(f"Agent execution error: {e}", exc_info=True)
            return {
                "response": f"Désolé, une erreur s'est produite lors du traitement de votre demande: {str(e)}",
                "error": str(e),
                "error_type": "execution"
            }

    def _generate_demo_response(self, profile: AgentProfile, message: str) -> str:
        """
        Generate a canned demo response for agents not yet implemented.

        Args:
            profile: Agent profile
            message: User message (not used, but kept for consistency)

        Returns:
            Canned response explaining agent capabilities
        """
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

    def execute_agent_sync(self, agent_type: str, message: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Synchronous wrapper for execute_agent (for backward compatibility).

        This method handles event loop creation/management for calling async execute_agent
        from synchronous code.

        Args:
            agent_type: Type of agent to execute
            message: Message to process
            context: Additional context for processing

        Returns:
            Dict containing the agent response
        """
        try:
            # Try to get existing event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If loop is already running, we can't use run_until_complete
                # This happens when called from async context
                logger.warning("Event loop already running, use execute_agent() instead of execute_agent_sync()")
                # Create a new loop in a thread (not ideal, but works)
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, self.execute_agent(agent_type, message, context))
                    return future.result()
            else:
                # Loop exists but not running, use it
                return loop.run_until_complete(self.execute_agent(agent_type, message, context))
        except RuntimeError:
            # No event loop exists, create one
            return asyncio.run(self.execute_agent(agent_type, message, context))

    def cleanup(self):
        """
        Cleanup agent instances and resources.

        Call this when shutting down the application to properly cleanup agent resources.
        """
        logger.info("Cleaning up agent instances")
        self._agent_instances.clear()
