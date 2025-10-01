# 📚 Ekumen Agricultural Assistant - Documentation

**Last Updated:** 2025-10-01  
**Version:** 2.0 (Post-Refactoring)

---

## 📖 Table of Contents

1. [Quick Start](#quick-start)
2. [Architecture Overview](#architecture-overview)
3. [Documentation Structure](#documentation-structure)
4. [Key Concepts](#key-concepts)
5. [Development Guide](#development-guide)

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- PostgreSQL 14+
- Redis 7+
- OpenAI API Key
- Tavily API Key (for Internet/Supplier agents)

### Installation
```bash
# Clone repository
git clone https://github.com/logicshaper19/ekumenme.git
cd ekumenme/Ekumen-assistant

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp env.local .env
# Edit .env with your API keys

# Run database migrations
alembic upgrade head

# Start the application
uvicorn app.main:app --reload
```

### First API Call
```bash
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "Quelles sont les prévisions météo pour ma parcelle?"}'
```

---

## 🏗️ Architecture Overview

### System Components

```
Ekumen Agricultural Assistant
├── 🤖 Agents (9 specialized agents)
│   ├── Weather Intelligence Agent
│   ├── Crop Health Monitor Agent
│   ├── Farm Data Agent
│   ├── Planning Agent
│   ├── Regulatory Compliance Agent
│   ├── Sustainability Analytics Agent
│   ├── Internet Agent (Tavily-powered)
│   ├── Supplier Agent (Tavily-powered)
│   └── Semantic Crop Health Agent
│
├── 🛠️ Tools (25 production-ready tools)
│   ├── Weather Tools (4)
│   ├── Crop Health Tools (4)
│   ├── Farm Data Tools (4)
│   ├── Planning Tools (5)
│   ├── Regulatory Tools (4)
│   └── Sustainability Tools (4)
│
├── 🗄️ Database (PostgreSQL)
│   ├── MesParcelles Schema (regions, exploitations, parcelles, interventions)
│   ├── EPHY Database (AMM products, substances, regulations)
│   ├── Agricultural Knowledge Base (diseases, pests, crops)
│   └── User Data (conversations, feedback, journal)
│
├── ⚡ Services
│   ├── LangChain LCEL Service (primary)
│   ├── Multi-Agent Service (complex queries)
│   ├── Chat Service (orchestration)
│   ├── Tavily Service (web search)
│   └── Memory Service (conversation history)
│
└── 🌐 API (FastAPI)
    ├── Authentication (/api/v1/auth)
    ├── Chat (/api/v1/chat)
    ├── Journal (/api/v1/journal)
    ├── Products (/api/v1/products)
    └── Feedback (/api/v1/feedback)
```

### Key Technologies
- **LangChain**: Agent orchestration and tool management
- **FastAPI**: High-performance async API framework
- **PostgreSQL**: Primary database with agricultural schemas
- **Redis**: Caching layer for tool results
- **Pydantic**: Type-safe schemas and validation
- **Tavily**: Web search and supplier discovery
- **OpenAI**: LLM for natural language understanding

---

## 📁 Documentation Structure

### `/architecture/`
Core system architecture and design documents
- Database schemas and relationships
- Agent architecture patterns
- LangChain integration guides
- System integration documentation

### `/tools/`
Tool-specific documentation
- Tool enhancement guides
- PoC (Proof of Concept) patterns
- Individual tool documentation
- Tool migration guides

### `/agents/`
Agent-specific documentation
- Agent capabilities and responsibilities
- Agent orchestration patterns
- Multi-agent workflows
- Semantic agent documentation

### `/deployment/`
Deployment and migration guides
- Database migration scripts
- Phase-by-phase deployment plans
- Production readiness checklists
- API security setup

### `/testing/`
Testing documentation and strategies
- Test patterns and examples
- Integration test guides
- Performance testing
- Edge case documentation

### `/archive/`
Historical documentation and summaries
- Implementation summaries
- Refactoring logs
- Completion reports
- Status updates

---

## 🎯 Key Concepts

### 1. **"One Tool, One Job" Principle**
Each tool performs a single, well-defined function:
- ✅ `get_weather_data_tool` - Retrieves weather forecasts
- ✅ `diagnose_disease_tool` - Diagnoses crop diseases
- ❌ `generate_farm_report_tool` - Meta-orchestration (removed)

### 2. **PoC Pattern (Proof of Concept)**
All production tools follow this pattern:
```python
# 1. Service class with caching
class WeatherService:
    @redis_cache(ttl=3600, model_class=WeatherOutput)
    async def get_weather(self, input: WeatherInput) -> WeatherOutput:
        # Business logic here
        pass

# 2. Async wrapper function
async def get_weather_data_async(
    location: str,
    days: int = 7
) -> WeatherOutput:
    service = WeatherService()
    return await service.get_weather(WeatherInput(location=location, days=days))

# 3. StructuredTool creation
get_weather_data_tool = StructuredTool.from_function(
    coroutine=get_weather_data_async,
    name="get_weather_data",
    description="Get weather forecast for agricultural planning",
    args_schema=WeatherInput,
    handle_validation_error=True
)
```

### 3. **Pydantic Schemas**
All tools use type-safe Pydantic schemas:
- Input validation
- Output structure
- Error handling
- Automatic documentation

### 4. **Redis Caching Strategy**
Dynamic TTL based on data volatility:
- Weather data: 1-6 hours (dynamic based on forecast horizon)
- Regulatory data: 24 hours
- Farm data: 1 hour
- Sustainability calculations: 12 hours

### 5. **French Agricultural Context**
- SIRET-based multi-tenancy
- Millesime (vintage year) tracking
- AMM code integration (EPHY database)
- BBCH crop growth stages
- EPPO crop codes
- French regulatory compliance

---

## 🛠️ Development Guide

### Adding a New Tool

1. **Create Pydantic schemas** (`app/tools/schemas/`)
```python
from pydantic import BaseModel, Field

class MyToolInput(BaseModel):
    param1: str = Field(..., description="Parameter description")
    param2: int = Field(default=10, description="Optional parameter")

class MyToolOutput(BaseModel):
    result: str
    confidence: float
    timestamp: str
```

2. **Create service class** (`app/tools/my_agent/my_tool.py`)
```python
from app.core.cache import redis_cache

class MyService:
    @redis_cache(ttl=3600, model_class=MyToolOutput)
    async def process(self, input: MyToolInput) -> MyToolOutput:
        # Business logic
        return MyToolOutput(...)
```

3. **Create tool wrapper**
```python
async def my_tool_async(param1: str, param2: int = 10) -> MyToolOutput:
    service = MyService()
    return await service.process(MyToolInput(param1=param1, param2=param2))

my_tool = StructuredTool.from_function(
    coroutine=my_tool_async,
    name="my_tool",
    description="Tool description",
    args_schema=MyToolInput,
    handle_validation_error=True
)
```

4. **Export in `__init__.py`**
```python
from .my_tool import my_tool

__all__ = ["my_tool"]
```

5. **Write tests** (`tests/test_my_tool.py`)
```python
import pytest
from app.tools.my_agent import my_tool

@pytest.mark.asyncio
async def test_my_tool():
    result = await my_tool.arun(param1="test", param2=5)
    assert result.confidence > 0.5
```

### Running Tests
```bash
# All tests
pytest

# Specific test file
pytest tests/test_my_tool.py

# With coverage
pytest --cov=app tests/
```

### Code Quality
```bash
# Format code
black app/ tests/

# Sort imports
isort app/ tests/

# Lint
flake8 app/ tests/

# Type checking
mypy app/
```

---

## 📞 Support

- **Issues**: https://github.com/logicshaper19/ekumenme/issues
- **Documentation**: `/docs/`
- **API Docs**: http://localhost:8000/docs (when running locally)

---

## 📄 License

Proprietary - All rights reserved

