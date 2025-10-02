# Testing Guide

**Last Updated:** 2025-10-01
**Scope:** Phase 1 (Existing System - 9 Agents, 25 Tools)

> **Note:** For Phase 2 testing (Multi-Tenancy, Knowledge Base, Voice Journal), see **[QUICK_START.md](QUICK_START.md)** section "Testing Strategy"

---

## Quick Start

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app tests/

# Run critical import tests
python tests/test_critical_imports.py

# Run specific test file
pytest tests/tools/test_weather_tools.py

# Run specific test
pytest tests/tools/test_weather_tools.py::test_get_weather_analysis
```

---

## Test Structure

```
tests/
├── test_critical_imports.py    # CI/CD import tests
├── agents/                     # Agent tests
├── tools/                      # Tool tests
├── api/                        # API endpoint tests
├── services/                   # Service tests
└── conftest.py                 # Pytest fixtures
```

---

## Critical Import Tests

**File:** `tests/test_critical_imports.py`

### Purpose
Catch broken imports before deployment

### Tests
1. ✅ AgentManager import
2. ✅ Prompt registry import
3. ✅ Main app import
4. ✅ ChatService import
5. ✅ StreamingService import
6. ✅ All agents import
7. ✅ No deleted imports
8. ✅ get_available_agents format

### Usage

```bash
# Run directly
python tests/test_critical_imports.py

# Expected output:
# ✅ ALL CRITICAL IMPORT TESTS PASSED

# Add to CI/CD
# .github/workflows/test.yml
- name: Critical Import Tests
  run: python tests/test_critical_imports.py
```

---

## Unit Tests

### Tool Tests

```python
# tests/tools/test_my_tool.py
import pytest
from app.tools import my_tool

@pytest.mark.asyncio
async def test_my_tool_success():
    """Test successful tool execution"""
    result = await my_tool.ainvoke({
        "param": "test_value"
    })
    
    assert result["success"] is True
    assert "data" in result
    assert result["data"] is not None

@pytest.mark.asyncio
async def test_my_tool_validation_error():
    """Test input validation"""
    from pydantic import ValidationError
    
    with pytest.raises(ValidationError):
        await my_tool.ainvoke({"param": ""})

@pytest.mark.asyncio
async def test_my_tool_error_handling():
    """Test error handling"""
    result = await my_tool.ainvoke({
        "param": "invalid_value"
    })
    
    assert result["success"] is False
    assert "error" in result
```

### Agent Tests

```python
# tests/agents/test_my_agent.py
import pytest
from app.agents.my_agent import MyAgent

@pytest.mark.asyncio
async def test_agent_initialization():
    """Test agent initializes correctly"""
    agent = MyAgent()
    
    assert agent.tools is not None
    assert len(agent.tools) > 0
    assert agent.prompt is not None

@pytest.mark.asyncio
async def test_agent_query_processing():
    """Test agent processes queries"""
    agent = MyAgent()
    
    result = await agent.process_query(
        "Test query",
        siret="12345678901234"
    )
    
    assert result is not None
    assert "response" in result
```

### Service Tests

```python
# tests/services/test_my_service.py
import pytest
from app.services.my_service import MyService

@pytest.fixture
async def service(db_session):
    """Create service instance"""
    return MyService(db=db_session)

@pytest.mark.asyncio
async def test_service_method(service):
    """Test service method"""
    result = await service.my_method("param")
    
    assert result is not None
```

---

## Integration Tests

### API Tests

```python
# tests/api/test_chat.py
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_chat_endpoint():
    """Test chat endpoint"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/chat/message",
            json={
                "message": "Test message",
                "conversation_id": "test-123"
            },
            headers={"Authorization": "Bearer test-token"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
```

### Database Tests

```python
# tests/test_database.py
import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from app.models import Exploitation, Parcelle

@pytest.mark.asyncio
async def test_create_exploitation(db_session: AsyncSession):
    """Test creating exploitation"""
    exploitation = Exploitation(
        nom="Test Farm",
        siret="12345678901234"
    )
    
    db_session.add(exploitation)
    await db_session.commit()
    await db_session.refresh(exploitation)
    
    assert exploitation.id is not None
    assert exploitation.nom == "Test Farm"
```

---

## Test Fixtures

### conftest.py

```python
# tests/conftest.py
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.database import Base

@pytest.fixture
async def db_engine():
    """Create test database engine"""
    engine = create_async_engine(
        "postgresql+asyncpg://test:test@localhost/test_db",
        echo=False
    )
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    yield engine
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    await engine.dispose()

@pytest.fixture
async def db_session(db_engine):
    """Create test database session"""
    async_session = sessionmaker(
        db_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session

@pytest.fixture
def mock_openai_response():
    """Mock OpenAI API response"""
    return {
        "choices": [{
            "message": {
                "content": "Test response"
            }
        }]
    }
```

---

## Mocking

### Mock External APIs

```python
# tests/test_weather_api.py
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
@patch('app.tools.weather_tools.httpx.AsyncClient.get')
async def test_weather_api_call(mock_get):
    """Test weather API call with mock"""
    mock_get.return_value = AsyncMock(
        status_code=200,
        json=lambda: {"temp": 20, "conditions": "sunny"}
    )
    
    from app.tools import get_weather_analysis
    
    result = await get_weather_analysis.ainvoke({
        "latitude": 48.8566,
        "longitude": 2.3522
    })
    
    assert result["success"] is True
    mock_get.assert_called_once()
```

### Mock Database

```python
@pytest.mark.asyncio
async def test_with_mock_db():
    """Test with mocked database"""
    mock_db = AsyncMock(spec=AsyncSession)
    mock_db.execute.return_value.scalars.return_value.first.return_value = None
    
    service = MyService(db=mock_db)
    result = await service.get_data("123")
    
    assert result is None
```

---

## Coverage

### Generate Coverage Report

```bash
# Run tests with coverage
pytest --cov=app --cov-report=html tests/

# View report
open htmlcov/index.html

# Coverage threshold
pytest --cov=app --cov-fail-under=80 tests/
```

### Coverage Configuration

```ini
# .coveragerc
[run]
source = app
omit = 
    */tests/*
    */venv/*
    */__init__.py

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
```

---

## Performance Tests

### Benchmark Tests

```python
# tests/test_performance.py
import pytest
import time

@pytest.mark.asyncio
async def test_tool_performance():
    """Test tool response time"""
    from app.tools import get_farm_data
    
    start = time.time()
    result = await get_farm_data.ainvoke({
        "siret": "12345678901234",
        "exploitation_id": 1
    })
    duration = time.time() - start
    
    assert duration < 2.0  # Should complete in <2s
    assert result["success"] is True
```

---

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:14
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Run critical import tests
        run: python tests/test_critical_imports.py
      
      - name: Run pytest
        run: pytest --cov=app tests/
      
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

---

## Test Best Practices

### 1. Test Naming
```python
# Good
def test_get_farm_data_returns_correct_format():
    pass

# Bad
def test1():
    pass
```

### 2. Arrange-Act-Assert Pattern
```python
async def test_my_function():
    # Arrange
    input_data = {"param": "value"}
    
    # Act
    result = await my_function(input_data)
    
    # Assert
    assert result["success"] is True
```

### 3. One Assertion Per Test
```python
# Good
async def test_returns_success():
    result = await my_function()
    assert result["success"] is True

async def test_returns_data():
    result = await my_function()
    assert "data" in result

# Avoid
async def test_everything():
    result = await my_function()
    assert result["success"] is True
    assert "data" in result
    assert result["data"]["field"] == "value"
```

### 4. Use Fixtures
```python
@pytest.fixture
def sample_data():
    return {"field": "value"}

async def test_with_fixture(sample_data):
    result = await my_function(sample_data)
    assert result is not None
```

---

## Debugging Tests

### Run with Verbose Output
```bash
pytest -v tests/

# Show print statements
pytest -s tests/

# Stop on first failure
pytest -x tests/

# Run last failed tests
pytest --lf tests/
```

### Debug with pdb
```python
async def test_my_function():
    import pdb; pdb.set_trace()
    result = await my_function()
    assert result is not None
```

---

## References

- [Development Guide](DEVELOPMENT.md)
- [Architecture](ARCHITECTURE.md)
- [Tools Reference](TOOLS_REFERENCE.md)
- [Agents Reference](AGENTS_REFERENCE.md)

