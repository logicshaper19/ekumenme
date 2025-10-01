# Tools Reference

**Total Tools:** 25  
**Last Updated:** 2025-10-01

---

## Overview

All tools are implemented as LangChain `StructuredTool` instances with Pydantic validation. They are registered in the Tool Registry and available to agents through the orchestrator.

---

## Farm Data Tools (5)

| Tool | Description | Key Parameters | Returns |
|------|-------------|----------------|---------|
| `get_farm_data` | Retrieve farm information and field data | `siret`, `exploitation_id` | Farm details, parcelles, cultures |
| `get_performance_metrics` | Calculate farm performance KPIs | `siret`, `exploitation_id`, `date_range` | Yield, efficiency, profitability metrics |
| `analyze_trends` | Analyze historical trends | `siret`, `metric_type`, `time_period` | Trend analysis, predictions |
| `generate_farm_report` | Create comprehensive farm report | `siret`, `exploitation_id`, `report_type` | PDF/JSON report |
| `benchmark_performance` | Compare against regional benchmarks | `siret`, `exploitation_id`, `metrics` | Comparative analysis |

**Location:** `app/tools/farm_data_tools.py`

---

## Weather Tools (3)

| Tool | Description | Key Parameters | Returns |
|------|-------------|----------------|---------|
| `get_weather_analysis` | Current weather analysis for location | `latitude`, `longitude` | Temperature, precipitation, wind, conditions |
| `get_weather_forecast` | Weather predictions (7-14 days) | `latitude`, `longitude`, `days` | Daily forecasts, alerts |
| `analyze_weather_risks` | Agricultural weather risk assessment | `latitude`, `longitude`, `crop_type` | Risk scores, recommendations |

**Location:** `app/tools/weather_tools.py`  
**API:** OpenWeatherMap (configurable)  
**Safety:** Never falls back to mock data

---

## Crop Health Tools (4)

| Tool | Description | Key Parameters | Returns |
|------|-------------|----------------|---------|
| `diagnose_disease` | Identify crop diseases from symptoms | `crop_type`, `symptoms`, `growth_stage` | Disease matches, confidence scores |
| `identify_pest` | Identify pests from description | `crop_type`, `pest_description`, `damage_type` | Pest matches, severity |
| `recommend_treatment` | Treatment recommendations | `disease_or_pest`, `crop_type`, `severity` | Treatment options, AMM products |
| `assess_soil_health` | Soil health analysis | `soil_data`, `crop_type` | pH, nutrients, recommendations |

**Location:** `app/tools/crop_health_tools.py`  
**Knowledge Base:** 50+ diseases, 30+ pests  
**Confidence Threshold:** ≥0.5 (not 0.3)

---

## Planning Tools (4)

| Tool | Description | Key Parameters | Returns |
|------|-------------|----------------|---------|
| `generate_planning_report` | Create planning recommendations | `siret`, `exploitation_id`, `season` | Task schedule, priorities |
| `calculate_planning_costs` | Estimate costs for planned activities | `tasks`, `resources`, `duration` | Cost breakdown, ROI estimates |
| `optimize_tasks` | Optimize task scheduling | `tasks`, `constraints`, `objectives` | Optimized schedule |
| `calculate_resource_requirements` | Calculate resource needs | `tasks`, `field_size`, `crop_type` | Labor, equipment, materials |

**Location:** `app/tools/planning_tools.py`  
**ROI Threshold:** 30-40% minimum on variable costs  
**Disclaimer:** Preliminary planning only, not financial advice

---

## Regulatory Tools (3)

| Tool | Description | Key Parameters | Returns |
|------|-------------|----------------|---------|
| `check_regulatory_compliance` | Check compliance with regulations | `activity_type`, `products`, `location` | Compliance status, requirements |
| `get_amm_product_info` | Lookup AMM-approved products | `amm_code` or `product_name` | Product details, usage restrictions |
| `get_safety_guidelines` | Safety guidelines for products/activities | `product_type`, `activity` | Safety protocols, PPE requirements |

**Location:** `app/tools/regulatory_tools.py`  
**Database:** French AMM codes, EU regulations  
**Updates:** Quarterly regulatory updates

---

## Sustainability Tools (3)

| Tool | Description | Key Parameters | Returns |
|------|-------------|----------------|---------|
| `calculate_carbon_footprint` | Calculate carbon emissions | `activities`, `inputs`, `field_size` | CO₂ equivalent, breakdown |
| `assess_biodiversity` | Assess biodiversity impact | `practices`, `field_data`, `region` | Biodiversity score, recommendations |
| `analyze_water_management` | Water usage analysis | `irrigation_data`, `crop_type`, `weather` | Water efficiency, optimization |

**Location:** `app/tools/sustainability_tools.py`  
**Standards:** GHG Protocol, EU biodiversity metrics

---

## Advanced Tools (3)

| Tool | Description | Key Parameters | Returns |
|------|-------------|----------------|---------|
| `calculate_evapotranspiration` | Calculate ET₀ (FAO-56 method) | `weather_data`, `crop_type`, `growth_stage` | ET₀, crop coefficient, water needs |
| `calculate_intervention_windows` | Optimal timing for interventions | `activity_type`, `weather_forecast`, `crop_stage` | Recommended time windows |
| `analyze_nutrient_balance` | Nutrient balance analysis | `soil_data`, `crop_requirements`, `inputs` | NPK balance, recommendations |

**Location:** `app/tools/advanced_tools.py`  
**Methods:** FAO-56 (ET₀), Penman-Monteith equation  
**Precision:** Research-grade calculations

---

## Tool Architecture

### Common Pattern

All tools follow this structure:

```python
from langchain.tools import tool
from pydantic import BaseModel, Field

class ToolInput(BaseModel):
    """Input schema with validation"""
    param1: str = Field(description="Parameter description")
    param2: int = Field(ge=0, description="Positive integer")

@tool(args_schema=ToolInput)
async def tool_name(param1: str, param2: int) -> dict:
    """
    Tool description for LLM.
    
    This description helps the LLM understand when to use the tool.
    """
    # 1. Validate input
    if not param1:
        return {"error": "param1 is required"}
    
    # 2. Execute logic
    result = await execute_logic(param1, param2)
    
    # 3. Return structured result
    return {
        "success": True,
        "data": result,
        "metadata": {"timestamp": "..."}
    }
```

### Key Principles

1. **Pydantic Validation** - All inputs validated
2. **Async/Await** - All tools are async
3. **Structured Output** - Consistent return format
4. **Error Handling** - Graceful error messages
5. **Caching** - Results cached when appropriate
6. **Documentation** - Clear docstrings for LLM

---

## Tool Registry

**Location:** `app/services/tool_registry_service.py`

**Registration:**
```python
from app.tools import (
    get_farm_data,
    get_weather_analysis,
    diagnose_disease,
    # ... all 25 tools
)

TOOLS = [
    get_farm_data,
    get_weather_analysis,
    diagnose_disease,
    # ... all 25 tools
]
```

**Usage by Agents:**
```python
from app.services.tool_registry_service import TOOLS

agent = create_react_agent(
    llm=llm,
    tools=TOOLS,  # All 25 tools available
    prompt=prompt
)
```

---

## Tool Invocation

### By Orchestrator
```python
# Orchestrator has access to all 25 tools
result = await agent_executor.ainvoke({
    "input": "What's the weather forecast?",
    "chat_history": []
})
```

### By Specialized Agents
```python
# Specialized agents have subset of tools
weather_tools = [
    get_weather_analysis,
    get_weather_forecast,
    analyze_weather_risks
]

weather_agent = create_react_agent(
    llm=llm,
    tools=weather_tools,
    prompt=weather_prompt
)
```

---

## Performance

### Caching Strategy

| Tool Category | Cache TTL | Cache Key |
|---------------|-----------|-----------|
| Weather | 1 hour | `weather:{lat}:{lon}:{type}` |
| Farm Data | 5 minutes | `farm:{siret}:{exploitation_id}` |
| Regulatory | 24 hours | `amm:{code}` |
| Calculations | No cache | N/A |

### Optimization

- **Parallel Execution** - Independent tools run in parallel
- **Connection Pooling** - Database connections reused
- **Query Optimization** - Efficient SQL queries
- **API Rate Limiting** - Respects external API limits

---

## Error Handling

### Common Errors

1. **Invalid Input** - Pydantic validation error
2. **Database Error** - Connection or query failure
3. **API Error** - External API failure
4. **Not Found** - Resource doesn't exist
5. **Permission Denied** - SIRET mismatch

### Error Response Format

```python
{
    "success": False,
    "error": "Error message",
    "error_type": "ValidationError",
    "details": {...}
}
```

---

## Testing

### Unit Tests
- Input validation
- Business logic
- Error handling

### Integration Tests
- Database interactions
- API calls
- Caching behavior

### Test Location
`tests/tools/test_*.py`

---

## Adding New Tools

### Steps

1. **Create Tool File**
   ```python
   # app/tools/new_tool.py
   from langchain.tools import tool
   
   @tool
   async def new_tool(param: str) -> dict:
       """Tool description"""
       return {"result": "..."}
   ```

2. **Export from `__init__.py`**
   ```python
   # app/tools/__init__.py
   from .new_tool import new_tool
   ```

3. **Register in Tool Registry**
   ```python
   # app/services/tool_registry_service.py
   from app.tools import new_tool
   TOOLS.append(new_tool)
   ```

4. **Add Tests**
   ```python
   # tests/tools/test_new_tool.py
   async def test_new_tool():
       result = await new_tool.ainvoke({"param": "test"})
       assert result["success"] is True
   ```

5. **Update Documentation**
   - Add to this file
   - Update tool count

---

## References

- [Architecture](ARCHITECTURE.md)
- [Agents Reference](AGENTS_REFERENCE.md)
- [Development Guide](DEVELOPMENT.md)
- Tool implementations: `app/tools/`

