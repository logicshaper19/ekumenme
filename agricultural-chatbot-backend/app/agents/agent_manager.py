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
