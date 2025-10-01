# 🌾 Crop EPPO Codes Implementation

## Overview

This document describes the implementation of **EPPO (European and Mediterranean Plant Protection Organization) codes** for crop identification in the Ekumen agricultural system.

## What Are EPPO Codes?

EPPO codes are **internationally standardized identifiers** for plants, pests, and diseases:

- **Format**: 5-6 uppercase letters (e.g., `TRZAX` for wheat)
- **Purpose**: Language-independent crop identification
- **Authority**: EPPO Global Database (https://gd.eppo.int/)
- **Benefits**: 
  - ✅ No language barriers
  - ✅ International compatibility
  - ✅ Precise identification
  - ✅ Database integration ready

---

## Implementation Architecture

### 1. **Constants Module** 📋
**File**: `app/constants/crop_eppo_codes.py`

Central source of truth for all crop EPPO codes:

```python
from app.constants.crop_eppo_codes import (
    get_eppo_code,
    validate_crop,
    get_crop_name
)

# Get EPPO code from French name
eppo = get_eppo_code("blé")  # Returns: "TRZAX"

# Validate crop name
is_valid = validate_crop("maïs")  # Returns: True

# Reverse lookup
crop = get_crop_name("TRZAX")  # Returns: "blé"
```

**Features**:
- ✅ 20+ major French crops
- ✅ Bidirectional mapping (name ↔ EPPO)
- ✅ Alias support (e.g., "ble" → "blé", "wheat" → "blé")
- ✅ Crop categories (cereals, oilseeds, etc.)
- ✅ Validation functions

---

### 2. **Database Schema** 🗄️

#### Disease Table Enhancement

**Migration**: `app/migrations/add_crop_eppo_codes.sql`

```sql
ALTER TABLE diseases 
ADD COLUMN primary_crop_eppo VARCHAR(6);

CREATE INDEX idx_diseases_primary_crop_eppo 
ON diseases(primary_crop_eppo);
```

**Disease Model Fields**:
```python
class Disease(Base):
    # Crop identification (dual approach)
    primary_crop = Column(String(100))      # French name: "blé"
    primary_crop_eppo = Column(String(6))   # EPPO code: "TRZAX"
    
    # Disease identification
    eppo_code = Column(String(10))          # Disease EPPO: "SEPTTR"
```

**Why Both Fields?**
- `primary_crop`: Backward compatibility, user-friendly
- `primary_crop_eppo`: International standard, future-proof

---

### 3. **Data Seeding** 🌱

**File**: `app/scripts/seed_all_57_diseases.py`

Enhanced with automatic EPPO code assignment:

```python
from app.constants.crop_eppo_codes import validate_crop_strict, get_eppo_code

# Pre-validate all crops
validated_crop = validate_crop_strict("blé")  # Raises error if invalid
crop_eppo = get_eppo_code(validated_crop)     # "TRZAX"

# Insert with both identifiers
INSERT INTO diseases (
    primary_crop,        # "blé"
    primary_crop_eppo,   # "TRZAX"
    eppo_code,           # "SEPTTR" (disease EPPO)
    ...
)
```

**Validation Features**:
- ✅ Pre-flight validation of all crops
- ✅ Automatic EPPO code lookup
- ✅ Error handling for unknown crops
- ✅ Detailed logging

---

## Supported Crops

### Cereals (Céréales)
| French Name | EPPO Code | Scientific Name |
|-------------|-----------|-----------------|
| blé | `TRZAX` | *Triticum aestivum* |
| maïs | `ZEAMX` | *Zea mays* |
| orge | `HORVX` | *Hordeum vulgare* |
| seigle | `SECCE` | *Secale cereale* |
| avoine | `AVESA` | *Avena sativa* |
| triticale | `TTLSP` | *Triticosecale* |

### Oilseeds (Oléagineux)
| French Name | EPPO Code | Scientific Name |
|-------------|-----------|-----------------|
| colza | `BRSNN` | *Brassica napus* |
| tournesol | `HELAN` | *Helianthus annuus* |
| soja | `GLXMA` | *Glycine max* |
| lin | `LIUUT` | *Linum usitatissimum* |

### Root Crops (Cultures racines)
| French Name | EPPO Code | Scientific Name |
|-------------|-----------|-----------------|
| betterave | `BEAVA` | *Beta vulgaris* |
| pomme de terre | `SOLTU` | *Solanum tuberosum* |

### Other Crops
| French Name | EPPO Code | Scientific Name |
|-------------|-----------|-----------------|
| vigne | `VITVI` | *Vitis vinifera* |
| pois | `PIBSX` | *Pisum sativum* |
| féverole | `VICFX` | *Vicia faba* |
| luzerne | `MEDSA` | *Medicago sativa* |

---

## Usage Examples

### 1. Query Diseases by Crop (French Name)
```sql
SELECT * FROM diseases 
WHERE primary_crop = 'blé';
```

### 2. Query Diseases by Crop (EPPO Code)
```sql
SELECT * FROM diseases 
WHERE primary_crop_eppo = 'TRZAX';
```

### 3. International Integration
```python
# External API expects EPPO codes
def get_diseases_for_external_api(crop_eppo_code: str):
    return db.query(Disease).filter(
        Disease.primary_crop_eppo == crop_eppo_code
    ).all()
```

### 4. Multilingual Support
```python
# User inputs in English
user_input = "wheat"

# Convert to French
crop_fr = normalize_crop_name(user_input)  # "blé"

# Get EPPO code
eppo = get_eppo_code(crop_fr)  # "TRZAX"

# Query database
diseases = db.query(Disease).filter(
    Disease.primary_crop_eppo == eppo
).all()
```

---

## Migration Guide

### Step 1: Run Database Migration
```bash
psql -U your_user -d your_database -f app/migrations/add_crop_eppo_codes.sql
```

This will:
- ✅ Add `primary_crop_eppo` column
- ✅ Create index for fast lookups
- ✅ Populate EPPO codes for existing diseases
- ✅ Verify migration success

### Step 2: Seed New Diseases
```bash
cd Ekumen-assistant
python app/scripts/seed_all_57_diseases.py
```

This will:
- ✅ Validate all crop types
- ✅ Automatically assign EPPO codes
- ✅ Insert 57 diseases with full EPPO compliance

### Step 3: Verify
```sql
-- Check EPPO code coverage
SELECT 
    COUNT(*) as total_diseases,
    COUNT(primary_crop_eppo) as with_eppo,
    COUNT(*) - COUNT(primary_crop_eppo) as missing_eppo
FROM diseases;

-- View sample data
SELECT 
    name,
    primary_crop,
    primary_crop_eppo,
    eppo_code as disease_eppo
FROM diseases
LIMIT 10;
```

---

## API Integration

### Disease Diagnosis Tool
```python
from app.constants.crop_eppo_codes import get_eppo_code

class DiseaseDiagnosisInput(BaseModel):
    crop_type: str  # Can be French name or EPPO code
    
    @field_validator('crop_type')
    def validate_crop(cls, v):
        # Accept both French names and EPPO codes
        if len(v) <= 6 and v.isupper():
            # Looks like EPPO code
            crop_name = get_crop_name(v)
            if not crop_name:
                raise ValueError(f"Unknown EPPO code: {v}")
            return crop_name
        else:
            # French name
            return validate_crop_strict(v)
```

---

## Benefits

### 1. **International Compatibility** 🌍
- Works with EPPO databases worldwide
- Language-independent queries
- Standardized data exchange

### 2. **Future-Proof** 🚀
- Ready for multilingual support
- API integration ready
- Regulatory compliance (EU standards)

### 3. **Backward Compatible** ✅
- Existing queries still work
- French names preserved
- Gradual adoption possible

### 4. **Data Quality** 📊
- Validation at insert time
- Prevents typos and inconsistencies
- Centralized crop definitions

---

## Relationship with BBCH Stages

Both crops and diseases use EPPO codes, creating a clean data model:

```
┌─────────────────────┐
│  Crop               │
│  ─────────────────  │
│  name: "blé"        │
│  eppo: "TRZAX"      │ ←──────┐
└─────────────────────┘        │
                               │
┌─────────────────────┐        │ Links via
│  Disease            │        │ primary_crop_eppo
│  ─────────────────  │        │
│  name: "Septoriose" │        │
│  eppo: "SEPTTR"     │        │
│  primary_crop_eppo: "TRZAX" ─┘
│  susceptible_bbch: [30-61]
└─────────────────────┘
         │
         │ Links to
         ↓
┌─────────────────────┐
│  BBCH Stage         │
│  ─────────────────  │
│  crop_type: "blé"   │
│  bbch_code: 31      │
│  description: "..."  │
└─────────────────────┘
```

---

## Next Steps

### Immediate (Done ✅)
- [x] Create constants module
- [x] Add database migration
- [x] Update Disease model
- [x] Enhance seeding script
- [x] Add validation

### Future Enhancements
- [ ] Create dedicated `Crop` table
- [ ] Add EPPO codes to BBCH stages table
- [ ] Multilingual crop name support
- [ ] EPPO database API integration
- [ ] Crop variety tracking (e.g., wheat cultivars)

---

## References

- **EPPO Global Database**: https://gd.eppo.int/
- **EPPO Standards**: https://www.eppo.int/RESOURCES/eppo_standards
- **FAO Crop Classification**: http://www.fao.org/

---

## Questions?

For questions about EPPO code implementation, contact the development team or refer to:
- `app/constants/crop_eppo_codes.py` - Source code
- `app/migrations/add_crop_eppo_codes.sql` - Database schema
- This document - Implementation guide

