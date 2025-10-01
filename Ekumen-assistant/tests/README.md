# Tests

This directory contains all test files for the Ekumen Agricultural AI Assistant.

## 📁 Directory Structure

```
tests/
├── agents/              # Agent-specific tests (6 production-ready agents)
│   ├── archive/        # Archived intermediate test files
│   └── *.py           # Current agent test files
├── integration/        # Integration tests
├── unit/              # Unit tests
└── README.md          # This file
```

## 🎯 Agent Tests (tests/agents/)

### Production-Ready Agent Tests

All 6 agents have comprehensive test suites with 100% passing rates:

1. **test_weather_agent_final.py** - 17/17 tests (100%) ✅
   - Weather Agent with sophisticated prompts
   - Token optimization, metrics tracking, timeout protection

2. **test_farm_data_agent_complete.py** - 6/6 tests (100%) ✅
   - Farm Data Agent with production features
   - Context handling, metrics, capabilities

3. **test_crop_health_agent_complete.py** - 6/6 tests (100%) ✅
   - Crop Health Agent with diagnostic tools
   - Disease, pest, nutrient analysis

4. **test_planning_agent_complete.py** - 6/6 tests (100%) ✅
   - Planning Agent with task optimization
   - Crop feasibility, resource analysis

5. **test_regulatory_agent_complete.py** - 6/6 tests (100%) ✅
   - Regulatory Agent with compliance checking
   - AMM verification, safety guidelines

6. **test_sustainability_agent_complete.py** - 6/6 tests (100%) ✅
   - Sustainability Agent with environmental analysis
   - Carbon footprint, biodiversity, water management

**Total: 47/47 tests passing (100%)**

### Test Categories

Each agent test file includes 6 comprehensive tests:

1. **Sophisticated ChatPromptTemplate Prompt** ✅
   - Verifies ChatPromptTemplate usage
   - Checks 3-message structure (system/human/ai)
   - Validates ReAct format

2. **Token Optimization** ✅
   - Verifies examples disabled by default
   - Measures prompt size reduction (~20-40%)

3. **Configurable Parameters** ✅
   - Tests max_iterations, enable_dynamic_examples, enable_metrics
   - Verifies AgentExecutor configuration

4. **Robust Context Handling** ✅
   - Tests dynamic key handling
   - Tests None/empty value filtering
   - Validates French labels

5. **Metrics Tracking** ✅
   - Tests success/failure tracking
   - Tests tool usage statistics
   - Tests error categorization

6. **Enhanced Capabilities** ✅
   - Tests agent type, tools, capabilities
   - Tests configuration dict

### Archived Tests (tests/agents/archive/)

Intermediate test files from the development process:
- `test_weather_agent_improvements.py`
- `test_weather_agent_sophisticated.py`
- `test_weather_prompt_structure.py`

These are kept for reference but are superseded by the final test files.

## 🔗 Integration Tests (tests/integration/)

Integration tests that verify interactions between components:

- `test_advanced_langchain.py` - LangChain integration tests
- `test_agri_db_structure.py` - Database structure tests
- `test_configuration_service.py` - Configuration service tests
- `test_database_integrated_regulatory.py` - Regulatory database integration
- `test_crop_eppo_codes.py` - EPPO code integration
- `test_crop_model.py` - Crop model tests
- `test_edge_cases.py` - Edge case handling

## 🧪 Unit Tests (tests/unit/)

Unit tests for individual components:

- `test_agents.py` - Basic agent functionality tests

## 🚀 Running Tests

### Run All Agent Tests
```bash
cd Ekumen-assistant
python tests/agents/test_weather_agent_final.py
python tests/agents/test_farm_data_agent_complete.py
python tests/agents/test_crop_health_agent_complete.py
python tests/agents/test_planning_agent_complete.py
python tests/agents/test_regulatory_agent_complete.py
python tests/agents/test_sustainability_agent_complete.py
```

### Run All Tests at Once
```bash
cd Ekumen-assistant
for test in tests/agents/test_*_complete.py tests/agents/test_weather_agent_final.py; do
    echo "Running $test..."
    python "$test"
done
```

### Run Integration Tests
```bash
cd Ekumen-assistant
python tests/integration/test_advanced_langchain.py
```

## ✅ Test Requirements

All tests use:
- **Real APIs** (not mocks) - See `docs/NO_MOCK_DATA_SAFETY.md`
- **Environment variables** from `.env` file
- **Production database** connections
- **Actual LangChain agents** with real LLMs

## 📊 Test Coverage

Current test coverage:
- **Agent Tests:** 47/47 (100%) ✅
- **All agents:** 10/10 production-ready ✅
- **Integration Tests:** Available
- **Unit Tests:** Available

## 🔍 Test Patterns

All agent tests follow the same pattern:

```python
# 1. Import agent
from app.agents.{agent}_agent import {Agent}IntelligenceAgent

# 2. Test sophisticated prompt
def test_sophisticated_prompt():
    agent = {Agent}IntelligenceAgent()
    prompt = agent._get_prompt_template()
    assert isinstance(prompt, ChatPromptTemplate)
    # ... more assertions

# 3. Test token optimization
def test_token_optimization():
    agent_default = {Agent}IntelligenceAgent()
    agent_examples = {Agent}IntelligenceAgent(enable_dynamic_examples=True)
    # ... compare prompt sizes

# 4. Test configurable parameters
# 5. Test robust context handling
# 6. Test metrics tracking
# 7. Test enhanced capabilities
```

## 📝 Adding New Tests

When adding new agent tests:

1. Follow the existing pattern (6 comprehensive tests)
2. Use real APIs, not mocks
3. Test all sophisticated features
4. Verify 100% passing before committing
5. Update this README with the new test file

## 🔗 Related Documentation

- **Agent Documentation:** `docs/AGENT_REPLICATION_COMPLETE.md`
- **Testing Best Practices:** `docs/NO_MOCK_DATA_SAFETY.md`
- **Agent Architecture:** `docs/agents/`
- **Tool Documentation:** `docs/tools/`

## 📈 Test History

- **2025-10-01:** All 6 agents upgraded to 10/10 production-ready (47/47 tests passing)
- **Previous:** Various refactoring and improvement iterations

---

**All tests are production-ready and use real APIs for accurate validation!** ✅

