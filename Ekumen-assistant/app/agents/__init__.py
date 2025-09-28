"""
Agricultural Chatbot Agents Package.

This package contains all the specialized agricultural agents and orchestration logic.

CLEAN ARCHITECTURE:
- Agents follow LangChain best practices
- Pure orchestration with clear separation of concerns
- Business logic moved to tools
- Prompts centralized (Phase 3)
"""

# Core Agent Infrastructure
from .base_agent import (
    IntegratedAgriculturalAgent, 
    SystemIntegratedFarmDataAgent, 
    SystemIntegratedRegulatoryAgent, 
    SystemIntegratedAgentManager,
    AgentType
)

# Specialized Agricultural Agents
from .farm_data_agent import IntegratedFarmDataAgent
from .regulatory_agent import IntegratedRegulatoryAgent
from .weather_agent import WeatherIntelligenceAgent
from .crop_health_agent import CropHealthMonitorAgent
from .planning_agent import OperationalPlanningCoordinatorAgent
from .sustainability_agent import SustainabilityAnalyticsAgent

# Orchestration Components
from .agent_manager import AgentManager, AgentType
from .agent_selector import AgentSelector, TaskType, TaskRequirements
from .orchestrator import AgriculturalOrchestrator, WorkflowStep, WorkflowResult

__all__ = [
    # Core Agent Infrastructure
    "IntegratedAgriculturalAgent",
    "SystemIntegratedFarmDataAgent", 
    "SystemIntegratedRegulatoryAgent",
    "SystemIntegratedAgentManager",
    "AgentType",
    
    # Specialized Agricultural Agents
    "IntegratedFarmDataAgent",
    "IntegratedRegulatoryAgent", 
    "WeatherIntelligenceAgent",
    "CropHealthMonitorAgent",
    "OperationalPlanningCoordinatorAgent",
    "SustainabilityAnalyticsAgent",
    
    # Orchestration Components
    "AgentManager",
    "AgentType",
    "AgentSelector",
    "TaskType",
    "TaskRequirements",
    "AgriculturalOrchestrator",
    "WorkflowStep",
    "WorkflowResult"
]