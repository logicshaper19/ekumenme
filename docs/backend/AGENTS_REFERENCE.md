# Agents Reference

**Total Agents:** 9 (6 ReAct + 2 Service + 1 Orchestrator)  
**Last Updated:** 2025-10-01

---

## Overview

All agents are built using LangChain's `create_react_agent` pattern with specialized prompts and tool subsets. The orchestrator coordinates all agents and has access to all 25 tools.

---

## Agent Architecture

```
User Query
    ↓
Orchestrator Agent (ReAct)
    ↓
┌───────────────────────────────┐
│  Routes to Specialized Agent  │
└───────────────────────────────┘
    ↓
┌─────────────┬─────────────┐
│ ReAct Agent │Service Agent│
└─────────────┴─────────────┘
    ↓
Uses Specialized Tools
    ↓
Returns Result
```

---

## 1. Orchestrator Agent

**Type:** ReAct Agent  
**Role:** Main entry point, routes queries to specialized agents  
**Tools:** All 25 tools  
**Location:** Managed by `AgentManager`

### Capabilities
- Query understanding and routing
- Multi-agent coordination
- Context management
- Response synthesis

### Prompt Pattern
```python
system_prompt = """
You are an agricultural AI assistant orchestrator.
You coordinate specialized agents to answer farmer questions.

Available agents:
- Farm Data Agent: Data analysis, metrics, trends
- Weather Agent: Weather forecasts, climate analysis
- Crop Health Agent: Disease/pest diagnosis, treatments
- Planning Agent: Task planning, resource allocation
- Regulatory Agent: Compliance, AMM codes, safety
- Sustainability Agent: Carbon, biodiversity, water
- Supplier Agent: Product search
- Internet Agent: General web search

Route queries to the most appropriate agent.
"""
```

---

## 2. Farm Data Intelligence Agent

**Type:** ReAct Agent  
**Specialization:** Farm data analysis and performance metrics  
**Location:** `app/agents/farm_data_agent.py`

### Tools (5)
- `get_farm_data`
- `get_performance_metrics`
- `analyze_trends`
- `generate_farm_report`
- `benchmark_performance`

### Capabilities
- Retrieve farm and field information
- Calculate performance KPIs (yield, efficiency, profitability)
- Analyze historical trends and patterns
- Generate comprehensive farm reports
- Benchmark against regional averages

### Example Queries
- "Show me my farm data"
- "What's my yield performance this year?"
- "Analyze trends for wheat production"
- "How do I compare to other farms in my region?"

### Prompt Focus
- Data accuracy and precision
- Clear metric explanations
- Actionable insights
- Comparative analysis

---

## 3. Weather Intelligence Agent

**Type:** ReAct Agent  
**Specialization:** Weather analysis and forecasting  
**Location:** `app/agents/weather_agent.py`

### Tools (3)
- `get_weather_analysis`
- `get_weather_forecast`
- `analyze_weather_risks`

### Capabilities
- Current weather conditions analysis
- 7-14 day weather forecasts
- Agricultural weather risk assessment
- Climate pattern analysis
- Intervention timing recommendations

### Example Queries
- "What's the weather forecast for next week?"
- "Is it safe to spray tomorrow?"
- "What are the weather risks for my wheat?"
- "When should I irrigate based on weather?"

### Prompt Focus
- Agricultural context (not general weather)
- Risk assessment for farming activities
- Timing recommendations
- **Safety:** Never uses mock data

---

## 4. Crop Health Intelligence Agent

**Type:** ReAct Agent  
**Specialization:** Disease and pest management  
**Location:** `app/agents/crop_health_agent.py`

### Tools (4)
- `diagnose_disease`
- `identify_pest`
- `recommend_treatment`
- `assess_soil_health`

### Capabilities
- Disease diagnosis from symptoms
- Pest identification
- Treatment recommendations (with AMM products)
- Soil health assessment
- Preventive measures

### Example Queries
- "My wheat has yellow spots on leaves"
- "What pest is eating my corn?"
- "How do I treat powdery mildew?"
- "Is my soil healthy for tomatoes?"

### Prompt Focus
- Symptom-based diagnosis
- Confidence thresholds (≥0.5)
- Bayesian-inspired confidence calculation
- Fuzzy symptom matching
- Tiered recommendations (>0.7='treat now', 0.5-0.7='monitor', <0.5='insufficient data')

---

## 5. Planning Intelligence Agent

**Type:** ReAct Agent  
**Specialization:** Task planning and resource allocation  
**Location:** `app/agents/planning_agent.py`

### Tools (4)
- `generate_planning_report`
- `calculate_planning_costs`
- `optimize_tasks`
- `calculate_resource_requirements`

### Capabilities
- Seasonal planning recommendations
- Cost estimation and ROI analysis
- Task scheduling optimization
- Resource requirement calculations
- Labor and equipment planning

### Example Queries
- "Help me plan for spring planting"
- "What will it cost to plant 10 hectares of corn?"
- "Optimize my harvest schedule"
- "How much labor do I need for harvest?"

### Prompt Focus
- Practical, actionable plans
- Cost transparency (ROI ≥30-40%)
- Resource optimization
- **Disclaimer:** Preliminary planning only, not financial advice

---

## 6. Regulatory Intelligence Agent

**Type:** ReAct Agent  
**Specialization:** Compliance and safety  
**Location:** `app/agents/regulatory_agent.py`

### Tools (3)
- `check_regulatory_compliance`
- `get_amm_product_info`
- `get_safety_guidelines`

### Capabilities
- Regulatory compliance checking
- AMM product lookup and verification
- Safety guidelines and protocols
- PPE requirements
- Application restrictions

### Example Queries
- "Is this product approved for use on wheat?"
- "What are the safety requirements for this pesticide?"
- "Am I compliant with organic farming regulations?"
- "What's the AMM code for this product?"

### Prompt Focus
- Regulatory accuracy
- Safety emphasis
- Clear compliance requirements
- French AMM codes and EU regulations

---

## 7. Sustainability Intelligence Agent

**Type:** ReAct Agent  
**Specialization:** Environmental impact and sustainability  
**Location:** `app/agents/sustainability_agent.py`

### Tools (3)
- `calculate_carbon_footprint`
- `assess_biodiversity`
- `analyze_water_management`

### Capabilities
- Carbon footprint calculation
- Biodiversity impact assessment
- Water usage optimization
- Sustainable practice recommendations
- Environmental reporting

### Example Queries
- "What's my farm's carbon footprint?"
- "How can I improve biodiversity?"
- "Am I using water efficiently?"
- "What sustainable practices should I adopt?"

### Prompt Focus
- Environmental impact
- Practical sustainability improvements
- GHG Protocol standards
- EU biodiversity metrics

---

## 8. Supplier Agent

**Type:** Service Agent (Tavily API wrapper)  
**Specialization:** Agricultural product search  
**Location:** `app/agents/supplier_agent.py`

### Capabilities
- Search for agricultural products
- Find suppliers and vendors
- Compare product options
- Price information (when available)

### Example Queries
- "Find suppliers for organic fertilizer"
- "Where can I buy wheat seeds?"
- "Compare prices for irrigation systems"

### Implementation
```python
# Wraps Tavily API with agricultural context
result = tavily_client.search(
    query=f"agricultural supplier {product_name}",
    search_depth="advanced"
)
```

---

## 9. Internet Agent

**Type:** Service Agent (Tavily API wrapper)  
**Specialization:** General web search  
**Location:** `app/agents/internet_agent.py`

### Capabilities
- General agricultural information search
- Research latest farming techniques
- Find agricultural news and updates
- Lookup general information

### Example Queries
- "What are the latest organic farming techniques?"
- "Find information about regenerative agriculture"
- "What's new in precision farming?"

### Implementation
```python
# Wraps Tavily API for general search
result = tavily_client.search(
    query=user_query,
    search_depth="basic"
)
```

---

## Agent Manager

**Location:** `app/agents/agent_manager.py`

### Agent Registry

```python
class AgentType(Enum):
    FARM_DATA = "farm_data"
    WEATHER = "weather"
    CROP_HEALTH = "crop_health"
    PLANNING = "planning"
    REGULATORY = "regulatory"
    SUSTAINABILITY = "sustainability"
    INTERNET = "internet"
    SUPPLIER = "supplier"
    MARKET_PRICES = "market_prices"  # Future

@dataclass
class AgentProfile:
    agent_type: AgentType
    name: str
    description: str
    capabilities: List[str]
    cost_per_request: float
```

### Usage

```python
from app.agents.agent_manager import AgentManager

manager = AgentManager()

# Get all agent profiles
profiles = manager.agent_profiles

# Get specific agent
farm_agent = manager.get_agent(AgentType.FARM_DATA)
```

---

## Prompt Registry

**Location:** `app/prompts/prompt_registry.py`

### Centralized Prompt Management

```python
def get_agent_prompt(agent_type: str) -> ChatPromptTemplate:
    """Get prompt template for agent"""
    prompts = {
        "orchestrator": get_orchestrator_prompt(),
        "farm_data": get_farm_data_prompt(),
        "weather": get_weather_prompt(),
        # ... all agents
    }
    return prompts.get(agent_type)
```

### Prompt Structure

All prompts follow this pattern:
```python
ChatPromptTemplate.from_messages([
    ("system", system_prompt),  # Agent role and capabilities
    MessagesPlaceholder("chat_history"),  # Conversation history
    ("human", "{input}"),  # User query
    MessagesPlaceholder("agent_scratchpad")  # ReAct scratchpad
])
```

---

## Agent Creation Pattern

### Standard ReAct Agent

```python
from langchain.agents import create_react_agent, AgentExecutor
from langchain_openai import ChatOpenAI

# 1. Get prompt
prompt = get_agent_prompt("farm_data")

# 2. Get tools
tools = [get_farm_data, get_performance_metrics, ...]

# 3. Create LLM
llm = ChatOpenAI(model="gpt-4", temperature=0)

# 4. Create agent
agent = create_react_agent(
    llm=llm,
    tools=tools,
    prompt=prompt
)

# 5. Create executor
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True
)

# 6. Invoke
result = await agent_executor.ainvoke({
    "input": "user query",
    "chat_history": []
})
```

---

## Agent Communication

### Orchestrator → Specialized Agent

```python
# Orchestrator decides which agent to use
if "weather" in query.lower():
    agent = weather_agent
elif "disease" in query.lower():
    agent = crop_health_agent
else:
    agent = farm_data_agent

# Execute with specialized agent
result = await agent.ainvoke({
    "input": query,
    "chat_history": conversation_history
})
```

---

## Performance

### Agent Response Times

| Agent | Avg Response | Tools Used | Complexity |
|-------|--------------|------------|------------|
| Orchestrator | 1-2s | 0-25 | High |
| Farm Data | 1-3s | 1-3 | Medium |
| Weather | 0.5-1.5s | 1-2 | Low |
| Crop Health | 2-4s | 2-4 | High |
| Planning | 2-5s | 2-4 | High |
| Regulatory | 1-2s | 1-2 | Low |
| Sustainability | 2-3s | 1-3 | Medium |
| Supplier | 1-2s | 1 | Low |
| Internet | 1-2s | 1 | Low |

---

## Testing

### Agent Tests

**Location:** `tests/agents/`

**Test Coverage:**
- Agent initialization
- Tool access
- Prompt loading
- Query handling
- Error handling

### Example Test

```python
async def test_farm_data_agent():
    agent = FarmDataIntelligenceAgent()
    result = await agent.process_query(
        "Show me farm data",
        siret="12345678901234"
    )
    assert result["success"] is True
```

---

## Adding New Agents

### Steps

1. **Create Agent File** (`app/agents/new_agent.py`)
2. **Create Prompt** (`app/prompts/new_agent_prompts.py`)
3. **Register in AgentManager**
4. **Add to Agent Registry**
5. **Create Tests**
6. **Update Documentation**

---

## References

- [Architecture](ARCHITECTURE.md)
- [Tools Reference](TOOLS_REFERENCE.md)
- [Development Guide](DEVELOPMENT.md)
- Agent implementations: `app/agents/`
- Prompts: `app/prompts/`

