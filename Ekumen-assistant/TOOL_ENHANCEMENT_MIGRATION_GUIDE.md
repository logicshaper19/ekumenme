# Tool Enhancement Migration Guide

**Version:** 1.0  
**Date:** 2025-09-30  
**Status:** Production-Ready Pattern  

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Proof of Concept Results](#proof-of-concept-results)
3. [Enhancement Pattern](#enhancement-pattern)
4. [Step-by-Step Migration Guide](#step-by-step-migration-guide)
5. [Code Templates](#code-templates)
6. [Testing Requirements](#testing-requirements)
7. [Common Pitfalls](#common-pitfalls)
8. [Rollout Strategy](#rollout-strategy)

---

## 📊 Overview

This guide documents the proven pattern for enhancing agricultural tools with:
- **Pydantic schemas** for type safety
- **Redis + memory caching** for performance
- **Structured error handling** for reliability
- **Async support** for scalability

### What We've Proven

✅ **3 tools enhanced and tested (100% success rate)**  
✅ **13/13 tests passing with real API**  
✅ **17ms end-to-end workflow** (weather → risks → windows)  
✅ **Category-specific caching** prevents thrashing  
✅ **Dynamic TTL** optimizes cache hit rates  

---

## 🎯 Proof of Concept Results

### Enhanced Tools

| Tool | Tests | Performance | Key Features |
|------|-------|-------------|--------------|
| `get_weather_data` | 5/5 ✅ | 68.8% speedup (3.2x) | Real API, dynamic TTL (30min-4h) |
| `analyze_weather_risks` | 4/4 ✅ | 15.3% speedup (1.2x) | Crop-specific, structured errors |
| `identify_intervention_windows` | 4/4 ✅ | 8.3% speedup (1.1x) | Custom types, quality levels |

### Integration Test

✅ **Complete workflow:** 17ms (10ms weather + 4ms risks + 3ms windows)  
✅ **All 3 tools working together seamlessly**  
✅ **Caching working across entire workflow**  

### Production Projections

**Week 1 (Cold Start):**
- Cache hit rate: 25-35%
- Average speedup: 20-30%
- Cost savings: $60/year per tool

**Steady State (Weeks 4+):**
- Cache hit rate: 65-75%
- Average speedup: 50-70%
- Cost savings: $200/year per tool

**For 25 tools:** $5,000/year savings + 3.3x capacity increase

---

## 🔧 Enhancement Pattern

### Core Components

1. **Pydantic Schemas** (`app/tools/schemas/`)
   - Input schema with validation
   - Output schema with error fields
   - Enums for constants
   - Example data

2. **Enhanced Tool** (`app/tools/{category}/{tool}_enhanced.py`)
   - Service class with caching
   - Async function wrapper
   - StructuredTool creation
   - Error handling

3. **Comprehensive Tests** (`test_enhanced_{tool}.py`)
   - Real API testing
   - Caching performance
   - Error handling
   - Integration tests

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     LangChain Agent                         │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   StructuredTool                            │
│  - Pydantic input validation                                │
│  - Async wrapper function                                   │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Service Class                             │
│  - @redis_cache decorator                                   │
│  - Business logic                                           │
│  - Error handling                                           │
└─────────────────────────────────────────────────────────────┘
                            │
                    ┌───────┴───────┐
                    ▼               ▼
            ┌──────────────┐  ┌──────────────┐
            │ Redis Cache  │  │ Memory Cache │
            │ (persistent) │  │ (fallback)   │
            └──────────────┘  └──────────────┘
                    │               │
                    └───────┬───────┘
                            ▼
                    ┌──────────────┐
                    │  External    │
                    │     API      │
                    └──────────────┘
```

---

## 📝 Step-by-Step Migration Guide

### Phase 1: Create Pydantic Schemas (30 minutes)

**File:** `app/tools/schemas/{tool_name}_schemas.py`

```python
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from enum import Enum

# 1. Create input schema
class ToolInput(BaseModel):
    """Input schema for {tool_name}"""
    param1: str = Field(description="Description")
    param2: Optional[int] = Field(default=None, ge=1, le=100)
    
    @field_validator('param1')
    @classmethod
    def validate_param1(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("param1 cannot be empty")
        return v

# 2. Create output schema with error handling
class ToolOutput(BaseModel):
    """Output schema for {tool_name}"""
    result_field: str = Field(description="Main result")
    metadata: dict = Field(default_factory=dict)
    
    # Error handling fields (REQUIRED)
    success: bool = Field(default=True)
    error: Optional[str] = Field(default=None)
    error_type: Optional[str] = Field(default=None)
    
    class Config:
        json_schema_extra = {"example": {...}}
```

**Checklist:**
- [ ] Input schema with all parameters
- [ ] Field validators for critical fields
- [ ] Output schema with all result fields
- [ ] Error handling fields (success, error, error_type)
- [ ] Example data in Config
- [ ] Export in `app/tools/schemas/__init__.py`

### Phase 2: Create Enhanced Tool (45 minutes)

**File:** `app/tools/{category}/{tool_name}_enhanced.py`

```python
from typing import Optional
from langchain.tools import StructuredTool
import logging
from datetime import datetime
from pydantic import ValidationError

from app.tools.schemas.{tool_name}_schemas import (
    ToolInput,
    ToolOutput
)
from app.tools.exceptions import (
    # Import relevant exceptions
)
from app.core.cache import redis_cache

logger = logging.getLogger(__name__)

class Enhanced{ToolName}Service:
    """Service for {tool_name} with caching"""
    
    @redis_cache(
        ttl=3600,  # Choose appropriate TTL
        model_class=ToolOutput,
        category="{category}"  # weather, regulatory, farm_data, etc.
    )
    async def execute(self, param1: str, param2: Optional[int] = None) -> ToolOutput:
        """
        Execute {tool_name} with caching
        
        Args:
            param1: Description
            param2: Description
            
        Returns:
            ToolOutput with results
            
        Raises:
            ValidationError: If input invalid
            DataError: If data missing
        """
        try:
            # Business logic here
            result = self._do_work(param1, param2)
            
            return ToolOutput(
                result_field=result,
                metadata={},
                success=True
            )
            
        except Exception as e:
            raise  # Let wrapper handle errors
    
    def _do_work(self, param1: str, param2: Optional[int]) -> str:
        """Internal business logic"""
        # Implementation
        pass

# Global service instance
service = Enhanced{ToolName}Service()

async def {tool_name}_enhanced(
    param1: str,
    param2: Optional[int] = None
) -> str:
    """
    {Tool description}
    
    Args:
        param1: Description
        param2: Description
        
    Returns:
        JSON string with results
    """
    try:
        # Validate input
        input_data = ToolInput(param1=param1, param2=param2)
        
        # Execute
        result = await service.execute(
            param1=input_data.param1,
            param2=input_data.param2
        )
        
        return result.model_dump_json(indent=2, exclude_none=True)
        
    except ValidationError as e:
        logger.error(f"{tool_name} validation error: {e}")
        error_result = ToolOutput(
            result_field="",
            success=False,
            error=f"Paramètres invalides: {str(e)}",
            error_type="validation"
        )
        return error_result.model_dump_json(indent=2)
        
    except Exception as e:
        logger.error(f"{tool_name} error: {e}", exc_info=True)
        error_result = ToolOutput(
            result_field="",
            success=False,
            error="Erreur inattendue. Veuillez réessayer.",
            error_type="unknown"
        )
        return error_result.model_dump_json(indent=2)

# Create the enhanced tool
{tool_name}_tool_enhanced = StructuredTool.from_function(
    func={tool_name}_enhanced,
    name="{tool_name}",
    description="""Tool description in French.
    
    Detailed description of what it does.
    
    Entrée: Input description
    Sortie: Output description""",
    args_schema=ToolInput,
    return_direct=False,
    coroutine={tool_name}_enhanced,
    handle_validation_error=False  # We handle errors ourselves
)
```

**Checklist:**
- [ ] Service class with @redis_cache decorator
- [ ] Correct TTL for data type
- [ ] Correct category for cache
- [ ] Async wrapper function
- [ ] All error types handled (ValidationError, custom exceptions, Exception)
- [ ] Error results with success=False
- [ ] StructuredTool with handle_validation_error=False
- [ ] French description

### Phase 3: Create Comprehensive Tests (30 minutes)

**File:** `test_enhanced_{tool_name}.py`

```python
import asyncio
import json
import time
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from app.tools.{category}.{tool_name}_enhanced import {tool_name}_tool_enhanced
from app.core.cache import get_cache_stats, clear_cache

async def test_1_basic_functionality():
    """Test 1: Basic functionality"""
    print("\n" + "="*80)
    print("TEST 1: Basic Functionality")
    print("="*80)
    
    try:
        result = await {tool_name}_tool_enhanced.ainvoke({
            "param1": "test_value",
            "param2": 10
        })
        
        data = json.loads(result)
        assert data.get('success') == True
        assert data.get('result_field') is not None
        
        print("✅ TEST 1 PASSED")
        return True
    except Exception as e:
        print(f"❌ TEST 1 FAILED: {e}")
        return False

async def test_2_caching():
    """Test 2: Caching performance"""
    print("\n" + "="*80)
    print("TEST 2: Caching Performance")
    print("="*80)
    
    try:
        clear_cache(category="{category}")
        
        # First call (cache miss)
        start = time.time()
        result1 = await {tool_name}_tool_enhanced.ainvoke({"param1": "test"})
        time1 = time.time() - start
        
        # Second call (cache hit)
        start = time.time()
        result2 = await {tool_name}_tool_enhanced.ainvoke({"param1": "test"})
        time2 = time.time() - start
        
        assert result1 == result2
        speedup = (time1 - time2) / time1 * 100 if time1 > 0 else 0
        
        print(f"Speedup: {speedup:.1f}%")
        print("✅ TEST 2 PASSED")
        return True
    except Exception as e:
        print(f"❌ TEST 2 FAILED: {e}")
        return False

async def test_3_error_handling():
    """Test 3: Error handling"""
    print("\n" + "="*80)
    print("TEST 3: Error Handling")
    print("="*80)
    
    try:
        # Test with invalid input
        result = await {tool_name}_tool_enhanced.ainvoke({"param1": ""})
        data = json.loads(result)
        
        assert data.get('success') == False
        assert data.get('error_type') is not None
        
        print("✅ TEST 3 PASSED")
        return True
    except Exception as e:
        print(f"❌ TEST 3 FAILED: {e}")
        return False

async def main():
    tests = [
        ("Basic Functionality", test_1_basic_functionality),
        ("Caching Performance", test_2_caching),
        ("Error Handling", test_3_error_handling),
    ]
    
    results = []
    for name, test_func in tests:
        result = await test_func()
        results.append((name, result))
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    print(f"\n📊 Overall: {passed}/{total} tests passed")
    return passed == total

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
```

**Checklist:**
- [ ] Test 1: Basic functionality
- [ ] Test 2: Caching performance
- [ ] Test 3: Error handling
- [ ] Test 4: Edge cases (optional)
- [ ] All tests passing (100%)

---

## 🎨 Code Templates

### Cache TTL Guidelines

```python
# Choose TTL based on data stability:

# Real-time data (changes frequently)
ttl=300  # 5 minutes - market prices, live sensors

# Short-term data (changes hourly)
ttl=1800  # 30 minutes - weather current conditions

# Medium-term data (changes daily)
ttl=3600  # 1 hour - weather forecasts, derived analytics

# Long-term data (changes weekly)
ttl=7200  # 2 hours - regulatory data, crop calendars

# Static data (rarely changes)
ttl=14400  # 4 hours - reference data, historical averages
```

### Cache Categories

```python
# Use appropriate category for your tool:

category="weather"         # Weather-related tools (500 items)
category="regulatory"      # Regulatory/compliance tools (300 items)
category="farm_data"       # Farm/field data tools (200 items)
category="crop_health"     # Crop health/monitoring (200 items)
category="planning"        # Planning/scheduling (150 items)
category="sustainability"  # Sustainability metrics (150 items)
category="default"         # Other tools (100 items)
```

### Error Types

```python
# Standard error types to use:

error_type="validation"      # Input validation failed
error_type="data_missing"    # Required data not found
error_type="api_error"       # External API failed
error_type="timeout"         # Operation timed out
error_type="permission"      # Access denied
error_type="unknown"         # Unexpected error
```

---

## ✅ Testing Requirements

### Minimum Test Coverage

Every enhanced tool MUST have:

1. **Basic Functionality Test**
   - Valid input → successful output
   - Verify all output fields present
   - Check success=True

2. **Caching Performance Test**
   - Clear cache
   - First call (measure time)
   - Second call (measure time)
   - Verify speedup > 0%
   - Verify results identical

3. **Error Handling Test**
   - Invalid input → error response
   - Verify success=False
   - Verify error_type present
   - Verify error message helpful

4. **Integration Test** (for related tools)
   - Test tool in realistic workflow
   - Verify works with other tools
   - Measure end-to-end performance

### Test Success Criteria

✅ All tests passing (100%)  
✅ Caching providing measurable speedup  
✅ Error messages user-friendly (French)  
✅ No exceptions raised to user  

---

## ⚠️ Common Pitfalls

### 1. Pydantic Validation in Output Schema

**Problem:** Output schema too strict, fails on error cases

```python
# ❌ BAD - Will fail when creating error response
class ToolOutput(BaseModel):
    result: str = Field(min_length=1)  # Can't be empty!
    count: int = Field(ge=1)  # Can't be 0!
```

**Solution:** Allow flexible values for error cases

```python
# ✅ GOOD - Works for both success and error
class ToolOutput(BaseModel):
    result: str = Field(default="")  # Can be empty
    count: int = Field(ge=0)  # Can be 0
```

### 2. Wrong Cache Category

**Problem:** Tool uses wrong category, causes cache thrashing

```python
# ❌ BAD - Weather tool using default category
@redis_cache(ttl=3600, category="default")  # Only 100 items!
```

**Solution:** Use appropriate category

```python
# ✅ GOOD - Weather tool using weather category
@redis_cache(ttl=3600, category="weather")  # 500 items
```

### 3. TTL Too Short or Too Long

**Problem:** Cache hit rate too low or stale data

```python
# ❌ BAD - Weather forecast cached for 1 day
@redis_cache(ttl=86400)  # Data will be stale!

# ❌ BAD - Regulatory data cached for 1 minute
@redis_cache(ttl=60)  # Cache thrashing!
```

**Solution:** Match TTL to data stability

```python
# ✅ GOOD - Weather forecast cached for 1-2 hours
@redis_cache(ttl=3600)

# ✅ GOOD - Regulatory data cached for 2 hours
@redis_cache(ttl=7200)
```

### 4. Not Handling ValidationError

**Problem:** Pydantic errors not caught, tool crashes

```python
# ❌ BAD - ValidationError not handled
async def tool_function(param: str) -> str:
    input_data = ToolInput(param=param)  # Can raise ValidationError!
    # ... rest of code
```

**Solution:** Catch ValidationError explicitly

```python
# ✅ GOOD - ValidationError handled
async def tool_function(param: str) -> str:
    try:
        input_data = ToolInput(param=param)
        # ... rest of code
    except ValidationError as e:
        # Return error response
        return error_result.model_dump_json()
```

### 5. handle_validation_error=True

**Problem:** LangChain catches errors before our handler

```python
# ❌ BAD - Our error handler never runs
StructuredTool.from_function(
    ...,
    handle_validation_error=True  # LangChain handles it!
)
```

**Solution:** Set to False and handle ourselves

```python
# ✅ GOOD - We handle errors
StructuredTool.from_function(
    ...,
    handle_validation_error=False  # We handle it!
)
```

---

## 🚀 Rollout Strategy

### Phase 1: Enhance Next 3 Tools (Week 1)

**Priority:** High-usage tools with external APIs

Recommended:
1. `get_regulatory_info` (regulatory category)
2. `get_farm_data` (farm_data category)
3. `analyze_crop_health` (crop_health category)

**Goal:** Validate pattern across different categories

### Phase 2: Enhance 6 More Tools (Week 2)

**Priority:** Tools with slow response times

**Goal:** Maximize performance impact

### Phase 3: Enhance Remaining 13 Tools (Weeks 3-4)

**Priority:** Complete coverage

**Goal:** All 25 tools enhanced

### Phase 4: Production Rollout (Weeks 5-6)

1. **10% rollout** with feature flags
2. **Monitor metrics** (hit rate, errors, latency)
3. **100% rollout** if metrics good
4. **Document lessons learned**

---

## 📊 Success Metrics

Track these metrics for each enhanced tool:

### Performance Metrics
- Cache hit rate (target: 60-70% steady state)
- Average speedup (target: 40-50%)
- p95 latency (target: <500ms)

### Quality Metrics
- Test pass rate (target: 100%)
- Error rate (target: <1%)
- User-reported issues (target: 0)

### Business Metrics
- API cost savings (target: $200/year per tool)
- Capacity increase (target: 3x more users)
- User satisfaction (target: maintain or improve)

---

## 📚 Additional Resources

- **Proof of Concept Results:** `REAL_API_PRODUCTION_PROJECTIONS.md`
- **Production Fixes:** `PRODUCTION_FIXES_COMPLETE.md`
- **Example Tests:** `test_enhanced_weather_tool.py`, `test_enhanced_risk_tool.py`, `test_enhanced_intervention_tool.py`
- **Integration Test:** `test_integrated_weather_workflow.py`

---

## 🎯 Quick Start Checklist

For each tool you enhance:

- [ ] Create Pydantic schemas (30 min)
- [ ] Create enhanced tool (45 min)
- [ ] Create comprehensive tests (30 min)
- [ ] Run tests - all passing (100%)
- [ ] Measure caching performance
- [ ] Document any deviations from pattern
- [ ] Update this guide with lessons learned

**Total time per tool:** ~2 hours

**For 22 remaining tools:** ~44 hours (~1 week for 1 developer, or ~2 days for 2 developers)

---

**Last Updated:** 2025-09-30  
**Maintained By:** Development Team  
**Questions?** See examples in `app/tools/weather_agent/*_enhanced.py`

