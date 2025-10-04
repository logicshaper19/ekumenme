# Environmental Regulations Tool Refactoring Plan

## Current Issues Analysis

### 1. **Tool/Service Hybrid Anti-Pattern**
- **Problem**: 1,281 lines of business logic embedded in a LangChain tool
- **Impact**: Violates Single Responsibility Principle, hard to test, maintain, and reuse
- **Solution**: Extract service logic to dedicated service classes

### 2. **N+1 Database Query Pattern**
```python
# CURRENT (BAD) - Lines 346-349
for amm_code in amm_codes:
    product_query = select(Produit).where(Produit.numero_amm == amm_code)
    product_result = await db.execute(product_query)
```
- **Problem**: Separate query per AMM code
- **Impact**: Performance degradation with multiple products
- **Solution**: Batch query all products at once

### 3. **Massive Configuration Dictionary**
- **Problem**: Large configuration dictionaries embedded in code
- **Impact**: Hard to maintain, test, and update
- **Solution**: Extract to configuration files or database

### 4. **Multiple Responsibilities in Single Class**
- **Problem**: One class handles water protection, biodiversity, air quality, ZNT calculations, etc.
- **Impact**: Violates Single Responsibility Principle
- **Solution**: Split into domain-specific services

## Refactoring Strategy

### Phase 1: Extract Service Layer (Priority: HIGH)

#### Current Structure:
```
app/tools/regulatory_agent/
└── check_environmental_regulations_tool.py (1,281 lines)
    └── EnvironmentalRegulationsService (1,200+ lines of business logic)
```

#### Target Structure:
```
app/
├── tools/regulatory_agent/
│   └── check_environmental_regulations_tool.py (~100 lines - tool wrapper only)
└── services/environmental/
    ├── __init__.py
    ├── base_environmental_service.py
    ├── znt_calculator_service.py
    ├── water_protection_service.py
    ├── biodiversity_service.py
    ├── air_quality_service.py
    ├── nitrate_directive_service.py
    └── product_environmental_service.py
```

### Phase 2: Fix N+1 Query Pattern

#### Current (Bad):
```python
for amm_code in amm_codes:
    product_query = select(Produit).where(Produit.numero_amm == amm_code)
    product_result = await db.execute(product_query)
```

#### Target (Good):
```python
# Batch query all products at once
products_query = select(Produit).where(Produit.numero_amm.in_(amm_codes))
products_result = await db.execute(products_query)
products = products_result.scalars().all()
```

### Phase 3: Extract Configuration

#### Current (Bad):
```python
# Large configuration dictionaries embedded in code
WATER_PROTECTION_RULES = {
    # 200+ lines of configuration
}
```

#### Target (Good):
```python
# app/config/environmental_config.py
from app.config.environmental_config import get_water_protection_rules
```

## Detailed Implementation Plan

### 1. Create Service Layer Structure

#### `app/services/environmental/base_environmental_service.py`
```python
"""Base environmental service with common functionality"""

class BaseEnvironmentalService:
    def __init__(self):
        self.config_service = ConfigurationService()
        self.regulatory_service = UnifiedRegulatoryService()
    
    async def batch_query_products(self, db: AsyncSession, amm_codes: List[str]) -> List[Produit]:
        """Batch query products to avoid N+1 pattern"""
        if not amm_codes:
            return []
        
        query = select(Produit).where(Produit.numero_amm.in_(amm_codes))
        result = await db.execute(query)
        return result.scalars().all()
```

#### `app/services/environmental/znt_calculator_service.py`
```python
"""ZNT (Zone de Non-Traitement) calculation service"""

class ZNTCalculatorService(BaseEnvironmentalService):
    async def calculate_znt_compliance(
        self, 
        db: AsyncSession, 
        amm_codes: List[str], 
        impact_data: EnvironmentalImpactData
    ) -> List[ZNTCompliance]:
        """Calculate ZNT compliance with batch queries"""
        # Extract ZNT calculation logic from current _get_znt_compliance_from_db
        pass
    
    def calculate_znt_reduction(self, ...) -> float:
        """Extract _calculate_znt_reduction logic"""
        pass
```

#### `app/services/environmental/water_protection_service.py`
```python
"""Water protection regulations service"""

class WaterProtectionService(BaseEnvironmentalService):
    def classify_water_body(self, ...) -> WaterBodyClassification:
        """Extract _classify_water_body logic"""
        pass
    
    def get_water_protection_regulations(self, ...) -> List[EnvironmentalRegulation]:
        """Extract water protection logic"""
        pass
```

#### `app/services/environmental/product_environmental_service.py`
```python
"""Product environmental data service"""

class ProductEnvironmentalService(BaseEnvironmentalService):
    async def get_product_environmental_data(
        self, 
        db: AsyncSession, 
        amm_codes: List[str]
    ) -> ProductEnvironmentalData:
        """Get product environmental data with batch queries"""
        # Fix N+1 query pattern here
        products = await self.batch_query_products(db, amm_codes)
        # Process products in batch
        pass
```

### 2. Refactor Tool to Use Services

#### `app/tools/regulatory_agent/check_environmental_regulations_tool.py` (New - ~100 lines)
```python
"""Environmental regulations LangChain tool - lightweight wrapper"""

from langchain.tools import StructuredTool
from app.services.environmental import EnvironmentalRegulationsService

class EnvironmentalRegulationsService:
    """Orchestrates environmental regulation checks using specialized services"""
    
    def __init__(self):
        self.znt_service = ZNTCalculatorService()
        self.water_service = WaterProtectionService()
        self.biodiversity_service = BiodiversityService()
        self.air_quality_service = AirQualityService()
        self.product_service = ProductEnvironmentalService()
    
    @redis_cache(ttl=7200, model_class=EnvironmentalRegulationsOutput, category="regulatory")
    async def check_environmental_regulations(self, ...) -> EnvironmentalRegulationsOutput:
        """Orchestrate environmental regulation checks"""
        # Delegate to specialized services
        znt_compliance = await self.znt_service.calculate_znt_compliance(...)
        water_regulations = self.water_service.get_water_protection_regulations(...)
        # etc.
        
        return EnvironmentalRegulationsOutput(...)

# LangChain tool wrapper
check_environmental_regulations_tool = StructuredTool.from_function(
    func=EnvironmentalRegulationsService().check_environmental_regulations,
    name="check_environmental_regulations",
    description="Check environmental regulations for agricultural practices"
)
```

### 3. Fix N+1 Query Pattern

#### Current Problem Areas:
1. **Lines 346-349**: Product queries in loop
2. **Lines 335-416**: `_get_product_environmental_data` method
3. **Lines 234-334**: `_get_znt_compliance_from_db` method

#### Solution:
```python
async def batch_query_products_with_usage(self, db: AsyncSession, amm_codes: List[str]) -> Dict[str, Any]:
    """Batch query products and their usage data"""
    if not amm_codes:
        return {}
    
    # Single query for all products
    products_query = (
        select(Produit, UsageProduit, SubstanceActive)
        .join(UsageProduit, Produit.id == UsageProduit.produit_id)
        .join(ProduitSubstance, Produit.id == ProduitSubstance.produit_id)
        .join(SubstanceActive, ProduitSubstance.substance_active_id == SubstanceActive.id)
        .where(Produit.numero_amm.in_(amm_codes))
    )
    
    result = await db.execute(products_query)
    rows = result.fetchall()
    
    # Group by AMM code
    products_data = {}
    for row in rows:
        product, usage, substance = row
        if product.numero_amm not in products_data:
            products_data[product.numero_amm] = {
                'product': product,
                'usages': [],
                'substances': []
            }
        products_data[product.numero_amm]['usages'].append(usage)
        products_data[product.numero_amm]['substances'].append(substance)
    
    return products_data
```

### 4. Extract Configuration

#### `app/config/environmental_config.py`
```python
"""Environmental regulations configuration"""

WATER_PROTECTION_RULES = {
    "surface_water": {
        "buffer_zones": {
            "standard": 5,  # meters
            "reduced": 3,   # meters with specific conditions
            "increased": 20 # meters for sensitive areas
        },
        "restrictions": {
            "wind_speed_max": 19,  # km/h
            "temperature_min": 3,  # °C
            "humidity_min": 40     # %
        }
    },
    # ... rest of configuration
}

BIODIVERSITY_PROTECTION_RULES = {
    "natura_2000": {
        "restricted_practices": ["spraying", "fertilization"],
        "buffer_zones": 50,  # meters
        "seasonal_restrictions": {
            "breeding_season": {"start": "03-01", "end": "07-31"},
            "migration_season": {"start": "09-01", "end": "11-30"}
        }
    },
    # ... rest of configuration
}
```

## Implementation Steps

### Step 1: Create Service Structure (2-3 hours)
1. Create `app/services/environmental/` directory
2. Create base service class
3. Create specialized service classes (empty initially)

### Step 2: Extract ZNT Calculator Service (3-4 hours)
1. Move `_get_znt_compliance_from_db` logic
2. Move `_calculate_znt_reduction` logic
3. Fix N+1 query pattern
4. Add unit tests

### Step 3: Extract Product Environmental Service (2-3 hours)
1. Move `_get_product_environmental_data` logic
2. Fix N+1 query pattern
3. Add unit tests

### Step 4: Extract Other Services (4-5 hours)
1. Water protection service
2. Biodiversity service
3. Air quality service
4. Nitrate directive service

### Step 5: Refactor Tool (1-2 hours)
1. Update tool to use new services
2. Ensure backward compatibility
3. Update tests

### Step 6: Extract Configuration (1-2 hours)
1. Move configuration dictionaries to config files
2. Update services to use configuration
3. Add configuration validation

## Benefits

### Code Quality
- **Single Responsibility**: Each service has one clear purpose
- **Testability**: Services can be unit tested independently
- **Maintainability**: Changes are isolated to specific services
- **Reusability**: Services can be used by other tools/agents

### Performance
- **Eliminated N+1 Queries**: Batch queries for better performance
- **Better Caching**: Service-specific caching strategies
- **Reduced Memory Usage**: Only load needed services

### Development Experience
- **Faster Development**: Smaller, focused files
- **Easier Debugging**: Clear service boundaries
- **Better Code Reviews**: Focused changes
- **Reduced Merge Conflicts**: Isolated changes

## Risk Mitigation

### 1. Backward Compatibility
- Keep existing tool interface unchanged
- Gradual migration of functionality
- Comprehensive testing

### 2. Testing Strategy
- Unit tests for each service
- Integration tests for service composition
- End-to-end tests for tool functionality

### 3. Performance Monitoring
- Monitor query performance
- Track cache hit rates
- Measure response times

## Estimated Effort

| Phase | Hours | Description |
|-------|-------|-------------|
| Service Structure | 2-3 | Create base services |
| ZNT Calculator | 3-4 | Extract ZNT logic + fix N+1 |
| Product Service | 2-3 | Extract product logic + fix N+1 |
| Other Services | 4-5 | Extract remaining services |
| Tool Refactor | 1-2 | Update tool to use services |
| Configuration | 1-2 | Extract configuration |
| Testing | 3-4 | Add comprehensive tests |
| **Total** | **16-23** | **2-3 days** |

## Next Steps

1. **Start with ZNT Calculator Service** - Highest impact, fixes N+1 pattern
2. **Create service interfaces** - Define clear contracts
3. **Extract one service at a time** - Gradual migration
4. **Add comprehensive tests** - Ensure no regressions
5. **Monitor performance** - Ensure improvements
6. **Update documentation** - Keep docs in sync
