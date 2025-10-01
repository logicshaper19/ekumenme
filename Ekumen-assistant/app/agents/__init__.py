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
from .farm_data_agent import FarmDataIntelligenceAgent
from .regulatory_agent import RegulatoryIntelligenceAgent
from .weather_agent import WeatherIntelligenceAgent
from .crop_health_agent import CropHealthIntelligenceAgent
from .planning_agent import PlanningIntelligenceAgent
from .sustainability_agent import SustainabilityIntelligenceAgent

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
    "FarmDataIntelligenceAgent",
    "RegulatoryIntelligenceAgent",
    "WeatherIntelligenceAgent",
    "CropHealthIntelligenceAgent",
    "PlanningIntelligenceAgent",
    "SustainabilityIntelligenceAgent",
    
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