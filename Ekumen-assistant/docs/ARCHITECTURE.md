# Ekumen Assistant Architecture

**Version:** 1.0.0  
**Last Updated:** 2025-10-01  
**Status:** Production Ready

---

## Overview

Ekumen Assistant is an agricultural AI assistant built on a clean ReAct-based architecture using LangChain and OpenAI GPT-4. The system provides intelligent agricultural advice through specialized agents and tools.

---

## System Architecture

```
┌─────────────────────────────────────────────────────┐
│              FastAPI Application                     │
│                  (app/main.py)                       │
└────────────────────┬────────────────────────────────┘
                     │
         ┌───────────┴───────────┐
         │                       │
         ▼                       ▼
┌─────────────────┐    ┌──────────────────┐
│   API Routes    │    │  WebSocket Chat  │
│   /api/v1/*     │    │   Real-time      │
└────────┬────────┘    └────────┬─────────┘
         │                      │
         └──────────┬───────────┘
                    │
                    ▼
         ┌─────────────────────┐
         │   Chat Service      │
         │  (Orchestration)    │
         └──────────┬──────────┘
                    │
         ┌──────────┴──────────┐
         │                     │
         ▼                     ▼
┌─────────────────┐   ┌─────────────────┐
│  Orchestrator   │   │  Agent Manager  │
│  Agent (ReAct)  │   │   (Registry)    │
└────────┬────────┘   └─────────────────┘
         │
         ├─────────────────────────────────┐
         │                                 │
         ▼                                 ▼
┌──────────────────┐           ┌──────────────────┐
│  ReAct Agents    │           │ Service Agents   │
│   (6 agents)     │           │   (2 agents)     │
└────────┬─────────┘           └────────┬─────────┘
         │                              │
         └──────────┬───────────────────┘
                    │
                    ▼
         ┌─────────────────────┐
         │   Tool Registry     │
         │    (25 tools)       │
         └──────────┬──────────┘
                    │
         ┌──────────┴──────────┐
         │                     │
         ▼                     ▼
┌─────────────────┐   ┌─────────────────┐
│   PostgreSQL    │   │  External APIs  │
│   Database      │   │  (Weather, etc) │
└─────────────────┘   └─────────────────┘
```

---

## Core Components

### 1. Orchestrator Agent
- **Type:** ReAct agent (LangChain)
- **Role:** Routes user queries to appropriate specialized agents
- **Tools:** Has access to all 25 tools
- **Pattern:** Reasoning + Action loop
- **Location:** `app/agents/agent_manager.py`

### 2. Specialized Agents (9 Total)

#### ReAct Agents (6)
1. **Farm Data Agent** - Data analysis, performance metrics, trends
2. **Weather Agent** - Weather analysis, forecasts, climate data
3. **Crop Health Agent** - Disease detection, pest management, treatments
4. **Planning Agent** - Task planning, resource allocation, scheduling
5. **Regulatory Agent** - Compliance, AMM codes, safety guidelines
6. **Sustainability Agent** - Carbon footprint, biodiversity, water management

#### Service Agents (2)
7. **Supplier Agent** - Product search via Tavily API
8. **Internet Agent** - General web search via Tavily API

### 3. Tool Registry (25 Tools)

**Farm Data Tools (5):**
- `get_farm_data` - Retrieve farm information
- `get_performance_metrics` - Calculate performance KPIs
- `analyze_trends` - Analyze historical trends
- `generate_farm_report` - Create comprehensive reports
- `benchmark_performance` - Compare against benchmarks

**Weather Tools (3):**
- `get_weather_analysis` - Current weather analysis
- `get_weather_forecast` - Weather predictions
- `analyze_weather_risks` - Risk assessment

**Crop Health Tools (4):**
- `diagnose_disease` - Disease identification
- `identify_pest` - Pest identification
- `recommend_treatment` - Treatment recommendations
- `assess_soil_health` - Soil analysis

**Planning Tools (4):**
- `generate_planning_report` - Planning recommendations
- `calculate_planning_costs` - Cost estimation
- `optimize_tasks` - Task optimization
- `calculate_resource_requirements` - Resource planning

**Regulatory Tools (3):**
- `check_regulatory_compliance` - Compliance checking
- `get_amm_product_info` - AMM product lookup
- `get_safety_guidelines` - Safety information

**Sustainability Tools (3):**
- `calculate_carbon_footprint` - Carbon calculations
- `assess_biodiversity` - Biodiversity assessment
- `analyze_water_management` - Water usage analysis

**Advanced Tools (3):**
- `calculate_evapotranspiration` - ET₀ calculations (FAO-56)
- `calculate_intervention_windows` - Optimal timing
- `analyze_nutrient_balance` - Nutrient analysis

### 4. Supporting Services

**Chat Service** (`app/services/chat_service.py`)
- Main orchestration service
- Conversation management
- Message routing

**Streaming Service** (`app/services/optimized_streaming_service.py`)
- Real-time response streaming
- WebSocket support
- Token-by-token delivery

**Memory Service** (`app/services/memory_service.py`)
- Conversation history
- Context management
- User preferences

**Performance Service** (`app/services/performance_optimization_service.py`)
- Redis caching
- In-memory caching
- Query optimization

---

## Data Architecture

### Database Schema

**Multi-Tenancy:** SIRET-based (French business identifier)

**Hierarchy:**
```
Region (Région)
  └─ Exploitation (Farm)
      └─ Parcelle (Field)
          └─ Intervention (Activity)
```

**Key Models:**
- `User` - User accounts and authentication
- `Conversation` - Chat conversations
- `Message` - Individual messages
- `Region` - Geographic regions
- `Exploitation` - Farms
- `Parcelle` - Fields/plots
- `Intervention` - Agricultural activities
- `Culture` - Crops (with EPPO codes)
- `Produit` - Products (with AMM codes)

### Caching Strategy

**Two-Layer Cache:**
1. **Redis** - Distributed cache (primary)
2. **In-Memory** - Local cache (fallback)

**Cache Keys:**
- Weather data: 1 hour TTL
- Farm data: 5 minutes TTL
- Tool results: Varies by tool

---

## Technology Stack

### Backend
- **Framework:** FastAPI 0.104+
- **Language:** Python 3.9+
- **AI:** LangChain + OpenAI GPT-4
- **Database:** PostgreSQL 14+ (async SQLAlchemy)
- **Cache:** Redis 7+
- **Search:** Tavily API

### Key Libraries
- `langchain` - AI agent framework
- `openai` - GPT-4 API
- `sqlalchemy` - Database ORM
- `pydantic` - Data validation
- `redis` - Caching
- `httpx` - Async HTTP client

---

## Design Patterns

### 1. ReAct Pattern
All agents use the ReAct (Reasoning + Action) pattern:
```
1. Thought: Agent reasons about the query
2. Action: Agent selects and uses a tool
3. Observation: Agent observes the result
4. Repeat until answer is complete
```

### 2. Tool Pattern
All tools follow a consistent pattern:
```python
@tool
async def tool_name(param: str) -> dict:
    """Tool description for LLM"""
    # 1. Validate input
    # 2. Execute logic
    # 3. Return structured result
```

### 3. Prompt Pattern
All prompts use `ChatPromptTemplate`:
```python
prompt = ChatPromptTemplate.from_messages([
    ("system", system_prompt),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder("agent_scratchpad")
])
```

### 4. Service Pattern
Services are singleton-like with dependency injection:
```python
class Service:
    def __init__(self, db: AsyncSession):
        self.db = db
```

---

## Security

### Authentication
- JWT tokens
- User sessions
- SIRET-based multi-tenancy

### Data Protection
- Row-level security (SIRET filtering)
- Input validation (Pydantic)
- SQL injection prevention (SQLAlchemy)
- API rate limiting

### API Keys
- OpenAI API key (required)
- Tavily API key (optional)
- Weather API key (optional)

---

## Performance

### Optimization Strategies
1. **Caching** - Redis + in-memory
2. **Async I/O** - All database and API calls
3. **Connection pooling** - Database connections
4. **Streaming** - Real-time response delivery
5. **Query optimization** - Efficient SQL queries

### Benchmarks
- Average response time: <2s
- Cache hit rate: >80%
- Concurrent users: 100+
- Database queries: <50ms

---

## Scalability

### Horizontal Scaling
- Stateless application servers
- Shared Redis cache
- PostgreSQL read replicas

### Vertical Scaling
- Async I/O for high concurrency
- Connection pooling
- Efficient caching

---

## Monitoring

### Logging
- Structured logging (JSON)
- Log levels: DEBUG, INFO, WARNING, ERROR
- Request/response logging

### Metrics
- Response times
- Cache hit rates
- Error rates
- API usage

---

## Future Enhancements

### Planned Features
1. Multi-language support (currently French)
2. Mobile app integration
3. Offline mode
4. Advanced analytics dashboard
5. Machine learning models for predictions

### Technical Improvements
1. GraphQL API
2. Event-driven architecture
3. Microservices migration
4. Kubernetes deployment
5. Advanced monitoring (Prometheus/Grafana)

---

## References

- [API Reference](API_REFERENCE.md)
- [Deployment Guide](DEPLOYMENT.md)
- [Development Guide](DEVELOPMENT.md)
- [Tools Reference](TOOLS_REFERENCE.md)
- [Agents Reference](AGENTS_REFERENCE.md)

