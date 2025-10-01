"""
Agricultural Chatbot Agents Package.

This package contains all the specialized agricultural agents.

CLEAN ARCHITECTURE (ReAct-based):
- All agents use LangChain ReAct pattern with create_react_agent
- Prompts centralized in app/prompts/prompt_registry.py
- Tools registered in app/services/tool_registry_service.py
- Orchestrator agent coordinates specialized agents
"""

# Specialized ReAct Agents
from .farm_data_agent import FarmDataIntelligenceAgent
from .regulatory_agent import RegulatoryIntelligenceAgent
from .weather_agent import WeatherIntelligenceAgent
from .crop_health_agent import CropHealthIntelligenceAgent
from .planning_agent import PlanningIntelligenceAgent
from .sustainability_agent import SustainabilityIntelligenceAgent

# Specialized Service Agents (External API wrappers)
from .supplier_agent import SupplierAgent
from .internet_agent import InternetAgent

# Agent Management
from .agent_manager import AgentManager, AgentType

__all__ = [
    # ReAct Agents
    "FarmDataIntelligenceAgent",
    "RegulatoryIntelligenceAgent",
    "WeatherIntelligenceAgent",
    "CropHealthIntelligenceAgent",
    "PlanningIntelligenceAgent",
    "SustainabilityIntelligenceAgent",

    # Service Agents
    "SupplierAgent",
    "InternetAgent",

    # Agent Management
    "AgentManager",
    "AgentType",
]