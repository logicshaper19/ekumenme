# BBCH & Zadoks Universal Schema - CORRECT DESIGN

**Date:** 2025-09-30  
**Status:** ✅ Production-Ready  
**Design:** Universal growth stages (not crop-specific)

---

## 🎯 Key Insight

**BBCH codes are like a calendar** - everyone uses the same codes, not crop-specific versions.

❌ **WRONG:** Separate BBCH entries for each crop  
✅ **CORRECT:** Universal BBCH codes (0-99) used by all crops

---

## 📊 Database Schema

### **Table 1: BBCH Stages (Universal)**

```sql
CREATE TABLE bbch_stages (
    bbch_code INTEGER PRIMARY KEY CHECK (0-99),
    principal_stage INTEGER CHECK (0-9),
    description_fr TEXT NOT NULL,
    description_en TEXT,
    notes TEXT
);
```

**Purpose:** Universal growth stage codes used across ALL crops

**Data:**
- ✅ 61 BBCH stages (0-99 range)
- ✅ 10 principal stages (0-9)
- ✅ French + English descriptions
- ✅ Universal for all crops

**Principal Stages:**
- 0: Germination (6 stages)
- 1: Leaf development (10 stages)
- 2: Tillering/side shoots (7 stages)
- 3: Stem elongation (7 stages)
- 4: Harvestable parts (6 stages)
- 5: Inflorescence emergence (5 stages)
- 6: Flowering (6 stages)
- 7: Fruit development (5 stages)
- 8: Ripening (5 stages)
- 9: Senescence (4 stages)

---

### **Table 2: Zadoks Stages (Cereals)**

```sql
CREATE TABLE zadoks_stages (
    zadoks_code INTEGER PRIMARY KEY CHECK (0-99),
    bbch_equivalent INTEGER REFERENCES bbch_stages(bbch_code),
    description_fr TEXT NOT NULL,
    description_en TEXT,
    applies_to TEXT[],  -- ['blé', 'orge', 'seigle']
    notes TEXT
);
```

**Purpose:** Cereal-specific codes that map to BBCH equivalents

**Data:**
- ✅ 48 Zadoks stages (0-99 range)
- ✅ Maps to BBCH equivalents
- ✅ Applies to: blé, orge, seigle
- ✅ French farmer terminology

**French Terms:**
- Tallage (tillering) - Zadoks 20-29
- Montaison (stem elongation) - Zadoks 30-39
- Épiaison (heading) - Zadoks 50-59
- Floraison (flowering) - Zadoks 60-69
- Maturité (ripeness) - Zadoks 80-89

---

## 🌾 Usage Examples

### **Example 1: Universal BBCH (All Crops)**

```sql
-- Farmer: "Mon blé est au stade BBCH 65"
SELECT bbch_code, description_fr, description_en
FROM bbch_stages
WHERE bbch_code = 65;

-- Result:
-- bbch_code | description_fr                            | description_en
-- 65        | Pleine floraison: 50% des fleurs ouvertes | Full flowering: 50% open
```

**Same code works for:**
- Blé (wheat) at BBCH 65
- Maïs (corn) at BBCH 65
- Colza (rapeseed) at BBCH 65
- Tournesol (sunflower) at BBCH 65

---

### **Example 2: Zadoks (Cereals Only)**

```sql
-- Farmer: "Mon blé est au stade Zadoks 65"
SELECT z.zadoks_code, z.description_fr, z.bbch_equivalent, z.applies_to
FROM zadoks_stages z
WHERE z.zadoks_code = 65;

-- Result:
-- zadoks_code | description_fr        | bbch_equivalent | applies_to
-- 65          | Pleine floraison: 50% | 65              | {blé,orge,seigle}
```

**Only applies to cereals:**
- ✅ Blé (wheat)
- ✅ Orge (barley)
- ✅ Seigle (rye)
- ❌ NOT for maïs, colza, tournesol

---

### **Example 3: Crop Observation (Database)**

```sql
-- Store farmer observation
CREATE TABLE crop_observations (
    id SERIAL PRIMARY KEY,
    farm_id VARCHAR(50),
    field_id VARCHAR(50),
    crop_type VARCHAR(50),
    observation_date DATE,
    bbch_code INTEGER REFERENCES bbch_stages(bbch_code),
    zadoks_code INTEGER REFERENCES zadoks_stages(zadoks_code),
    notes TEXT
);

-- Farmer reports wheat at Zadoks 65
INSERT INTO crop_observations VALUES
(DEFAULT, 'FR-12345', 'field-5', 'blé', '2025-06-15', 65, 65, 'Pleine floraison');

-- Query: What stage is my wheat at?
SELECT 
    o.crop_type,
    o.observation_date,
    b.description_fr as bbch_description,
    z.description_fr as zadoks_description
FROM crop_observations o
JOIN bbch_stages b ON o.bbch_code = b.bbch_code
LEFT JOIN zadoks_stages z ON o.zadoks_code = z.zadoks_code
WHERE o.farm_id = 'FR-12345' AND o.field_id = 'field-5'
ORDER BY o.observation_date DESC
LIMIT 1;
```

---

### **Example 4: ET Tool Integration**

```python
# Farmer provides BBCH code
input = {
    "crop_type": "blé",
    "bbch_code": 65  # From field observation
}

# Schema auto-converts BBCH → simple stage
def bbch_to_simple_stage(bbch: int) -> str:
    if bbch <= 29:
        return "semis"
    elif bbch <= 59:
        return "croissance"
    elif bbch <= 69:
        return "floraison"  # BBCH 65 maps here
    else:
        return "maturation"

# Lookup Kc from simple dict (NOT database)
kc = CROP_COEFFICIENTS["blé"]["floraison"]  # 1.15
```

---

## 🔄 BBCH ↔ Zadoks Mapping

### **Cereals (blé, orge, seigle)**

| Zadoks | BBCH | Description FR | French Term |
|--------|------|----------------|-------------|
| 21 | 21 | Début du tallage | Tallage |
| 30 | 30 | Épi à 1 cm | Début montaison |
| 31 | 31 | 1er nœud | Montaison |
| 51 | 51 | Début épiaison | Épiaison |
| 65 | 65 | Pleine floraison | Floraison |
| 89 | 89 | Maturité physiologique | Maturité |

### **Non-Cereals (maïs, colza, tournesol)**

Use **BBCH only** (no Zadoks equivalent):
- Maïs BBCH 65: Pleine floraison
- Colza BBCH 65: Pleine floraison
- Tournesol BBCH 65: Pleine floraison

---

## 📊 Database Statistics

```sql
-- BBCH stages
SELECT COUNT(*) FROM bbch_stages;
-- Result: 61 universal stages

-- Zadoks stages
SELECT COUNT(*) FROM zadoks_stages;
-- Result: 48 cereal stages

-- Principal stage distribution
SELECT principal_stage, COUNT(*) as stage_count
FROM bbch_stages
GROUP BY principal_stage
ORDER BY principal_stage;

-- Result:
-- 0: Germination (6 stages)
-- 1: Leaf development (10 stages)
-- 2: Tillering (7 stages)
-- 3: Stem elongation (7 stages)
-- 4: Harvestable parts (6 stages)
-- 5: Inflorescence (5 stages)
-- 6: Flowering (6 stages)
-- 7: Fruit development (5 stages)
-- 8: Ripening (5 stages)
-- 9: Senescence (4 stages)
```

---

## ✅ Benefits of Universal Design

### **1. Simplicity**
- ✅ One BBCH 65 for all crops (not 10 different entries)
- ✅ Easy to maintain
- ✅ No duplication

### **2. Flexibility**
- ✅ Add new crops without changing BBCH table
- ✅ Crop-specific Kc values stay in code (simple dict)
- ✅ Zadoks for cereals, BBCH for everything else

### **3. Correctness**
- ✅ Matches how BBCH scale actually works
- ✅ Matches how farmers use it
- ✅ Matches European standards

---

## 🚫 What We DON'T Store in Database

### **Crop Coefficients (Kc)**

**NOT in database:**
```sql
-- ❌ WRONG: Don't create this table
CREATE TABLE crop_coefficients (
    crop_type VARCHAR(50),
    bbch_code INTEGER,
    kc_value DECIMAL(3,2)
);
```

**Keep in code:**
```python
# ✅ CORRECT: Simple dict in code
CROP_COEFFICIENTS = {
    "blé": {
        "semis": 0.30,
        "croissance": 0.75,
        "floraison": 1.15,
        "maturation": 0.50
    }
}
```

**Why?**
- Simple 4-stage model (not 100 BBCH stages)
- Easy to maintain
- Fast lookup (no database query)
- FAO-56 standard

---

## 📝 Migration Summary

### **Before (WRONG):**
```sql
-- Crop-specific BBCH entries
INSERT INTO bbch_stages (crop_type, bbch_code, description_fr, kc_value)
VALUES ('blé', 65, 'Pleine floraison', 1.15);

INSERT INTO bbch_stages (crop_type, bbch_code, description_fr, kc_value)
VALUES ('maïs', 65, 'Pleine floraison', 1.20);
```

### **After (CORRECT):**
```sql
-- Universal BBCH code
INSERT INTO bbch_stages (bbch_code, principal_stage, description_fr)
VALUES (65, 6, 'Pleine floraison: 50% des fleurs ouvertes');

-- Cereal-specific Zadoks
INSERT INTO zadoks_stages (zadoks_code, bbch_equivalent, description_fr, applies_to)
VALUES (65, 65, 'Pleine floraison: 50%', ARRAY['blé', 'orge', 'seigle']);
```

---

## 🎯 Bottom Line

**BBCH = Universal calendar (0-99)**
- Same codes for all crops
- 61 stages in database
- French + English descriptions

**Zadoks = Cereal-specific (0-99)**
- Maps to BBCH equivalents
- 48 stages in database
- Applies to: blé, orge, seigle

**Kc = Simple dict in code**
- 4 stages per crop
- No database table
- Fast lookup

**Result:** Clean, correct, maintainable architecture.

---

**Last Updated:** 2025-09-30  
**Status:** ✅ Production-Ready  
**Migration:** `fix_bbch_universal_schema`

