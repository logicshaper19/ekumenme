# Development Guide

**Last Updated:** 2025-10-01

---

## Quick Start

```bash
# Clone and setup
git clone https://github.com/logicshaper19/ekumenme.git
cd ekumenme/Ekumen-assistant
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your API keys

# Run
python -m uvicorn app.main:app --reload
```

---

## Project Structure

```
Ekumen-assistant/
├── app/
│   ├── agents/          # 9 AI agents
│   ├── api/             # FastAPI routes
│   ├── models/          # Database models
│   ├── prompts/         # Agent prompts
│   ├── services/        # Business logic
│   ├── tools/           # 25 agricultural tools
│   ├── schemas/         # Pydantic schemas
│   └── main.py          # Application entry point
├── tests/               # Test suite
├── docs/                # Documentation
├── alembic/             # Database migrations
└── requirements.txt     # Dependencies
```

---

## Code Style

### Python Style Guide
- **PEP 8** compliance
- **Type hints** for all functions
- **Docstrings** for all public functions
- **Async/await** for I/O operations

### Example

```python
async def get_farm_data(
    siret: str,
    exploitation_id: int,
    db: AsyncSession
) -> dict:
    """
    Retrieve farm data for given SIRET and exploitation.
    
    Args:
        siret: French business identifier
        exploitation_id: Farm ID
        db: Database session
        
    Returns:
        dict: Farm data with parcelles and cultures
        
    Raises:
        ValueError: If SIRET is invalid
        NotFoundError: If farm doesn't exist
    """
    # Implementation
    pass
```

---

## Adding New Features

### 1. Adding a New Tool

```python
# 1. Create tool file: app/tools/my_tool.py
from langchain.tools import tool
from pydantic import BaseModel, Field

class MyToolInput(BaseModel):
    param: str = Field(description="Parameter description")

@tool(args_schema=MyToolInput)
async def my_tool(param: str) -> dict:
    """Tool description for LLM"""
    return {"result": "..."}

# 2. Export: app/tools/__init__.py
from .my_tool import my_tool

# 3. Register: app/services/tool_registry_service.py
from app.tools import my_tool
TOOLS.append(my_tool)

# 4. Test: tests/tools/test_my_tool.py
async def test_my_tool():
    result = await my_tool.ainvoke({"param": "test"})
    assert result["success"] is True
```

### 2. Adding a New Agent

```python
# 1. Create agent: app/agents/my_agent.py
from langchain.agents import create_react_agent, AgentExecutor
from app.prompts.prompt_registry import get_agent_prompt
from app.tools import tool1, tool2

class MyAgent:
    def __init__(self):
        self.tools = [tool1, tool2]
        self.prompt = get_agent_prompt("my_agent")
        self.agent = create_react_agent(...)
        
# 2. Create prompt: app/prompts/my_agent_prompts.py
def get_my_agent_prompt() -> ChatPromptTemplate:
    return ChatPromptTemplate.from_messages([...])

# 3. Register in AgentManager
# 4. Add tests
```

### 3. Adding a New API Endpoint

```python
# app/api/v1/my_endpoint.py
from fastapi import APIRouter, Depends
from app.schemas.my_schema import MyRequest, MyResponse

router = APIRouter()

@router.post("/my-endpoint", response_model=MyResponse)
async def my_endpoint(
    request: MyRequest,
    db: AsyncSession = Depends(get_db)
) -> MyResponse:
    """Endpoint description"""
    # Implementation
    return MyResponse(...)

# Include in app/main.py
from app.api.v1 import my_endpoint
app.include_router(my_endpoint.router, prefix="/api/v1")
```

---

## Database

### Creating Models

```python
# app/models/my_model.py
from sqlalchemy import Column, String, Integer
from app.models.base import Base

class MyModel(Base):
    __tablename__ = "my_table"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    siret = Column(String(14), nullable=False, index=True)
```

### Creating Migrations

```bash
# Auto-generate migration
alembic revision --autogenerate -m "Add my_table"

# Review migration file in alembic/versions/

# Apply migration
alembic upgrade head
```

---

## Testing

### Running Tests

```bash
# All tests
pytest

# Specific test file
pytest tests/tools/test_my_tool.py

# With coverage
pytest --cov=app tests/

# Critical imports
python tests/test_critical_imports.py
```

### Writing Tests

```python
# tests/tools/test_my_tool.py
import pytest
from app.tools import my_tool

@pytest.mark.asyncio
async def test_my_tool_success():
    result = await my_tool.ainvoke({"param": "test"})
    assert result["success"] is True
    assert "data" in result

@pytest.mark.asyncio
async def test_my_tool_validation_error():
    with pytest.raises(ValidationError):
        await my_tool.ainvoke({"param": ""})
```

---

## Debugging

### Enable Debug Logging

```python
# .env
DEBUG=True
LOG_LEVEL=DEBUG

# Or in code
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Debug Agent Execution

```python
# Enable verbose mode
agent_executor = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True  # Shows reasoning steps
)
```

### Debug Database Queries

```python
# Enable SQL logging
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
```

---

## Git Workflow

### Branch Strategy

```bash
# Create feature branch
git checkout -b feature/my-feature

# Make changes and commit
git add .
git commit -m "feat: Add my feature"

# Push and create PR
git push origin feature/my-feature
```

### Commit Message Format

```
<type>: <description>

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance

**Examples:**
```
feat: Add carbon footprint calculation tool
fix: Correct weather API error handling
docs: Update deployment guide
refactor: Simplify agent manager
test: Add tests for crop health agent
```

---

## Performance Optimization

### Caching

```python
# Use Redis cache
from app.services.performance_optimization_service import cache_result

@cache_result(ttl=3600, key_prefix="weather")
async def get_weather(lat: float, lon: float):
    # Expensive operation
    pass
```

### Database Optimization

```python
# Use eager loading
from sqlalchemy.orm import selectinload

query = select(Exploitation).options(
    selectinload(Exploitation.parcelles)
)

# Use indexes
class MyModel(Base):
    siret = Column(String(14), index=True)
```

### Async Operations

```python
# Run operations in parallel
import asyncio

results = await asyncio.gather(
    get_weather(lat, lon),
    get_farm_data(siret),
    get_soil_data(parcelle_id)
)
```

---

## Common Patterns

### Error Handling

```python
from app.exceptions import NotFoundError, ValidationError

try:
    result = await some_operation()
except NotFoundError as e:
    logger.error(f"Resource not found: {e}")
    raise HTTPException(status_code=404, detail=str(e))
except ValidationError as e:
    logger.error(f"Validation error: {e}")
    raise HTTPException(status_code=422, detail=str(e))
```

### Dependency Injection

```python
from fastapi import Depends
from app.database import get_db

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    # Validate token and return user
    pass

@router.get("/me")
async def read_users_me(
    current_user: User = Depends(get_current_user)
):
    return current_user
```

---

## Environment Setup

### Required Tools

- Python 3.9+
- PostgreSQL 14+
- Redis 7+ (optional)
- Git
- Code editor (VS Code recommended)

### VS Code Extensions

- Python
- Pylance
- Python Test Explorer
- GitLens
- Docker (if using containers)

### VS Code Settings

```json
{
    "python.linting.enabled": true,
    "python.linting.pylintEnabled": true,
    "python.formatting.provider": "black",
    "editor.formatOnSave": true,
    "python.testing.pytestEnabled": true
}
```

---

## Troubleshooting

### Import Errors

```bash
# Run critical import tests
python tests/test_critical_imports.py

# Check PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

### Database Issues

```bash
# Reset database
alembic downgrade base
alembic upgrade head

# Check connection
psql -U ekumen_user -d ekumen_assistant -c "SELECT 1"
```

### Redis Issues

```bash
# Check Redis
redis-cli ping

# Clear cache
redis-cli FLUSHALL
```

---

## Resources

- [Architecture](ARCHITECTURE.md)
- [API Reference](API_REFERENCE.md)
- [Tools Reference](TOOLS_REFERENCE.md)
- [Agents Reference](AGENTS_REFERENCE.md)
- [Testing Guide](TESTING.md)
- [Deployment Guide](DEPLOYMENT.md)

---

## Getting Help

- **Issues:** GitHub Issues
- **Documentation:** `/docs` directory
- **Tests:** Run `python tests/test_critical_imports.py`

