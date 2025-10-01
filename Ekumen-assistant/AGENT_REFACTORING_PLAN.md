# Agent Refactoring Plan - Using Production Tools

**Date:** 2025-10-01  
**Status:** Planning Phase

---

## Problem Statement

We have **26 production-ready tools** but most agents don't use them!

### Current State

**Production Tools Available (26):**
- Weather Tools (4): get_weather_data, analyze_weather_risks, identify_intervention_windows, calculate_evapotranspiration
- Crop Health Tools (4): diagnose_disease, identify_pest, analyze_nutrient_deficiency, generate_treatment_plan
- Farm Data Tools (4): get_farm_data, get_performance_metrics, get_benchmark_data, analyze_trends
- Planning Tools (5): generate_tasks, optimize_task_sequence, calculate_costs, analyze_resource_requirements, assess_crop_feasibility
- Regulatory Tools (5): database_integrated_amm, check_regulatory_compliance, get_safety_guidelines, check_environmental_regulations
- Sustainability Tools (4): calculate_carbon_footprint, assess_biodiversity, analyze_soil_health, assess_water_management

**Agents Using Production Tools (3/9):**
1. ✅ **Sustainability Agent** - Uses 4 sustainability tools
2. ✅ **Regulatory Agent** - Uses regulatory tools
3. ✅ **Semantic Crop Health Agent** - Uses crop health tools

**Agents NOT Using Production Tools (6/9):**
1. ❌ **Weather Agent** - Has 4 production tools available, not using them
2. ❌ **Crop Health Agent** - Has 4 production tools available, not using them
3. ❌ **Farm Data Agent** - Has 4 production tools available, not using them
4. ❌ **Planning Agent** - Has 5 production tools available, not using them
5. ✅ **Internet Agent** - Uses Tavily (external service, OK)
6. ✅ **Supplier Agent** - Uses Tavily (external service, OK)

---

## Root Cause

**AgentManager has "demo mode"** that returns canned responses instead of executing real agents with real tools.

```python
# Current (WRONG):
def _generate_demo_response(...):
    return """🌾 **Farm Data Agent** - Analyse de vos données...
    Je suis spécialisé dans... Pour une analyse complète..."""  # Fake!
```

**Should be:**
```python
# Correct:
async def execute_agent(agent_type, message, context):
    agent = await self._get_or_create_agent(agent_type)  # Real agent
    return await agent.process(message, context)  # Uses real tools
```

---

## Refactoring Strategy

### Phase 1: Remove Demo Mode from AgentManager ✅ (Partially Done)

**Changes:**
- ✅ Added async execute_agent()
- ✅ Added agent instance caching
- ✅ Added _get_or_create_agent()
- ❌ Still has DEMO_AGENTS set and _generate_demo_response()

**Next:**
- Remove DEMO_AGENTS set
- Remove _is_demo_agent() method
- Remove _generate_demo_response() method
- Only list agents that are actually implemented

### Phase 2: Refactor Agents to Use Production Tools

**Priority Order:**

#### 1. Weather Agent (HIGH PRIORITY)
**Status:** Has 4 production tools, not using them  
**Tools Available:**
- get_weather_data_tool
- analyze_weather_risks_tool
- identify_intervention_windows_tool
- calculate_evapotranspiration_tool

**Refactoring:**
```python
class WeatherAgent(IntegratedAgriculturalAgent):
    def __init__(self):
        tools = [
            get_weather_data_tool,
            analyze_weather_risks_tool,
            identify_intervention_windows_tool,
            calculate_evapotranspiration_tool
        ]
        super().__init__(
            name="weather",
            description="Agent météo agricole",
            system_prompt=FrenchAgriculturalPrompts.get_weather_prompt(),
            tools=tools
        )
```

#### 2. Crop Health Agent (HIGH PRIORITY)
**Status:** Has 4 production tools, not using them  
**Tools Available:**
- diagnose_disease_tool
- identify_pest_tool
- analyze_nutrient_deficiency_tool
- generate_treatment_plan_tool

**Refactoring:**
```python
class CropHealthAgent(IntegratedAgriculturalAgent):
    def __init__(self):
        tools = [
            diagnose_disease_tool,
            identify_pest_tool,
            analyze_nutrient_deficiency_tool,
            generate_treatment_plan_tool
        ]
        super().__init__(
            name="crop_health",
            description="Agent santé des cultures",
            system_prompt=FrenchAgriculturalPrompts.get_crop_health_prompt(),
            tools=tools
        )
```

#### 3. Farm Data Agent (MEDIUM PRIORITY)
**Status:** Has 4 production tools, not using them  
**Tools Available:**
- get_farm_data_tool
- get_performance_metrics_tool
- get_benchmark_data_tool
- analyze_trends_tool

**Refactoring:**
```python
class FarmDataAgent(IntegratedAgriculturalAgent):
    def __init__(self):
        tools = [
            get_farm_data_tool,
            get_performance_metrics_tool,
            get_benchmark_data_tool,
            analyze_trends_tool
        ]
        super().__init__(
            name="farm_data",
            description="Agent données d'exploitation",
            system_prompt=FrenchAgriculturalPrompts.get_farm_data_prompt(),
            tools=tools
        )
```

#### 4. Planning Agent (MEDIUM PRIORITY)
**Status:** Has 5 production tools, not using them  
**Tools Available:**
- generate_tasks_tool
- optimize_task_sequence_tool
- calculate_costs_tool
- analyze_resource_requirements_tool
- assess_crop_feasibility_tool

**Refactoring:**
```python
class PlanningAgent(IntegratedAgriculturalAgent):
    def __init__(self):
        tools = [
            generate_tasks_tool,
            optimize_task_sequence_tool,
            calculate_costs_tool,
            analyze_resource_requirements_tool,
            assess_crop_feasibility_tool
        ]
        super().__init__(
            name="planning",
            description="Agent planification agricole",
            system_prompt=FrenchAgriculturalPrompts.get_planning_prompt(),
            tools=tools
        )
```

### Phase 3: Update AgentManager to Only List Production Agents

**Before:**
```python
def list_available_agents(self):
    return list(self.agent_profiles.values())  # Returns all 9, including fake ones
```

**After:**
```python
PRODUCTION_AGENTS = {
    "internet",
    "supplier", 
    "sustainability",
    "regulatory",
    "semantic_crop_health",
    "weather",  # After refactoring
    "crop_health",  # After refactoring
    "farm_data",  # After refactoring
    "planning"  # After refactoring
}

def list_available_agents(self):
    """List only production-ready agents."""
    return [
        profile for profile in self.agent_profiles.values()
        if profile.agent_type.value.lower() in PRODUCTION_AGENTS
    ]
```

### Phase 4: Update _create_agent_instance()

**Current:**
```python
async def _create_agent_instance(self, agent_type: str):
    agent_map = {
        "internet": InternetAgent,
        "supplier": SupplierAgent,
        "market_prices": InternetAgent
    }
    # Only 3 agents!
```

**After Refactoring:**
```python
async def _create_agent_instance(self, agent_type: str):
    from app.agents.internet_agent import InternetAgent
    from app.agents.supplier_agent import SupplierAgent
    from app.agents.sustainability_agent import SustainabilityAnalyticsAgent
    from app.agents.regulatory_agent import RegulatoryAgent
    from app.agents.semantic_crop_health_agent import SemanticCropHealthAgent
    from app.agents.weather_agent import WeatherAgent
    from app.agents.crop_health_agent import CropHealthAgent
    from app.agents.farm_data_agent import FarmDataAgent
    from app.agents.planning_agent import PlanningAgent
    
    agent_map = {
        "internet": InternetAgent,
        "supplier": SupplierAgent,
        "market_prices": InternetAgent,
        "sustainability": SustainabilityAnalyticsAgent,
        "regulatory": RegulatoryAgent,
        "semantic_crop_health": SemanticCropHealthAgent,
        "weather": WeatherAgent,
        "crop_health": CropHealthAgent,
        "farm_data": FarmDataAgent,
        "planning": PlanningAgent
    }
    
    agent_class = agent_map.get(agent_type.lower())
    if not agent_class:
        raise ValueError(f"Agent {agent_type} not implemented")
    
    return agent_class()
```

---

## Implementation Order

1. **Weather Agent** - Refactor to use 4 weather tools
2. **Crop Health Agent** - Refactor to use 4 crop health tools
3. **Farm Data Agent** - Refactor to use 4 farm data tools
4. **Planning Agent** - Refactor to use 5 planning tools
5. **AgentManager** - Remove demo mode, update agent map
6. **Tests** - Update all tests to verify real tool usage

---

## Success Criteria

- ✅ All agents use production tools (no canned responses)
- ✅ AgentManager only lists implemented agents
- ✅ All 26 production tools are used by agents
- ✅ Tests verify real tool execution
- ✅ No "demo mode" or fake responses

---

## Next Steps

**Immediate:**
1. Refactor Weather Agent to use production tools
2. Test Weather Agent with real tools
3. Repeat for other agents

**User Decision Needed:**
- Which agent should we refactor first?
- Should we do them one at a time or all at once?

