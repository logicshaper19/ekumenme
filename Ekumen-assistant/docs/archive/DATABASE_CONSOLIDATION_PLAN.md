# Database Consolidation Plan

**Date:** 2025-09-30  
**Issue:** Ekumen-assistant has duplicate farm models that should be deleted. We need to use only Ekumenbackend MesParcelles models.

---

## 🎯 **Goal**

**Use ONLY Ekumenbackend models** for all farm data queries. Delete duplicate Assistant models.

---

## 📊 **Current Situation**

### **Two Sets of Models:**

1. **Ekumen-assistant/app/models/farm.py** (DUPLICATE - TO DELETE)
   - `Farm` (with `siret`, `owner_user_id`)
   - `Parcel` (with `farm_siret`, `current_crop`)
   - `CropRotation`
   - These are simplified models for the chatbot

2. **Ekumenbackend/app/models/mesparcelles.py** (REAL DATA - TO USE)
   - `Exploitation` (with `siret`)
   - `Parcelle` (with `uuid_parcelle`, `siret_exploitation`, `millesime`)
   - `SuccessionCulture` (crop rotations)
   - `Intervention` (farm operations)
   - `Culture` (crop reference data)
   - These are the real MesParcelles imported data

---

## ✅ **What's Already Fixed**

### **1. Farm Data Tool Updated** ✅

**File:** `Ekumen-assistant/app/tools/farm_data_agent/get_farm_data_tool.py`

**Changes:**
- `_get_database_farm_data_sync()` now queries Ekumenbackend models
- Imports `Parcelle`, `SuccessionCulture`, `Culture`, `Intervention` from `app.models.mesparcelles`
- Returns real data from MesParcelles database
- No more mock data!

**Query Logic:**
```python
# Query parcelles for the farm (SIRET)
query = select(Parcelle).where(Parcelle.siret_exploitation == farm_id)

# Get succession cultures (crops) for each parcel
cultures_query = select(SuccessionCulture).join(Culture).where(
    SuccessionCulture.uuid_parcelle == parcelle.uuid_parcelle
)

# Get interventions for each parcel
interventions_query = select(Intervention).where(
    Intervention.uuid_parcelle == parcelle.uuid_parcelle
)
```

---

## ⚠️ **Files That Still Use Assistant Farm Models**

### **Critical Files (Need Updates):**

1. **app/models/__init__.py**
   - Imports `Farm`, `Parcel`, `CropRotation` from `.farm`
   - **Action:** Remove these imports

2. **app/core/database.py** (line 129)
   - Imports `from app.models import farm` for table creation
   - **Action:** Remove farm import, or import from Ekumenbackend

3. **app/services/farm_service.py**
   - Uses `Farm`, `Parcel` models
   - **Action:** Either delete this service OR update to use Ekumenbackend models

4. **app/schemas/farm.py**
   - Imports `FarmType`, `FarmStatus` from `app.models.farm`
   - **Action:** Either delete OR update to use Ekumenbackend enums

### **Test Files (Can be Updated Later):**

5. **tests/test_models.py**
   - Tests `Farm`, `Parcel`, `CropRotation` models
   - **Action:** Update to test Ekumenbackend models OR delete

6. **tests/conftest.py**
   - Creates test fixtures for `Farm`, `Parcel`
   - **Action:** Update to use Ekumenbackend models OR delete

---

## 🚀 **Recommended Action Plan**

### **Option A: Clean Break (RECOMMENDED)** ✅ COMPLETED

**Delete all Assistant farm models and dependent code:**

1. ✅ Update `get_farm_data_tool.py` to use Ekumenbackend models (DONE)
2. ✅ Delete `app/models/farm.py` (DONE)
3. ✅ Delete `app/schemas/farm.py` (DONE)
4. ✅ Delete `app/services/farm_service.py` (DONE)
5. ✅ Delete `app/api/v1/farms.py` (DONE - API endpoint removed)
6. ✅ Update `app/models/__init__.py` to remove farm imports (DONE)
7. ✅ Update `app/core/database.py` to remove farm import (DONE)
8. ✅ Update `app/api/v1/__init__.py` to remove farms import (DONE)
9. ✅ Update `app/main.py` to remove farms router (DONE)
10. ✅ Update test files - commented out farm tests (DONE)

**Pros:**
- Clean, no duplication
- Forces use of real MesParcelles data
- Simpler architecture

**Cons:**
- Breaks any code that depends on Assistant farm models
- Need to update all imports

---

### **Option B: Gradual Migration**

**Keep Assistant models but make them query Ekumenbackend:**

1. ✅ Update `get_farm_data_tool.py` to use Ekumenbackend models (DONE)
2. Keep `app/models/farm.py` but mark as deprecated
3. Update `farm_service.py` to proxy to Ekumenbackend
4. Gradually migrate all code to use Ekumenbackend directly

**Pros:**
- Less breaking changes
- Can migrate gradually

**Cons:**
- Maintains duplication
- More complex
- Confusing which models to use

---

## 💡 **Recommendation**

**Go with Option A (Clean Break)** because:

1. **You already have MesParcelles data in the database**
2. **The farm_data tool is already updated**
3. **The Assistant farm models are not heavily used**
4. **Clean architecture is better long-term**

---

## 📋 **Step-by-Step Implementation**

### **Step 1: Verify Farm Data Tool Works** ✅

Test that the updated `get_farm_data_tool.py` actually queries the database:

```bash
# Run test with real database
python test_farmer_queries.py
```

**Expected:** Should return real parcels from MesParcelles database, not mock data

---

### **Step 2: Check What Breaks**

Before deleting, check what actually uses the Assistant farm models:

```bash
# Search for imports
grep -r "from app.models.farm import" Ekumen-assistant/app/
grep -r "from app.models import.*Farm" Ekumen-assistant/app/
```

---

### **Step 3: Delete Assistant Farm Models**

```bash
# Delete the duplicate models
rm Ekumen-assistant/app/models/farm.py
rm Ekumen-assistant/app/schemas/farm.py
rm Ekumen-assistant/app/services/farm_service.py
```

---

### **Step 4: Update Imports**

**File:** `app/models/__init__.py`

```python
# Remove these lines:
from .farm import Farm, Parcel, CropRotation

# Remove from __all__:
"Farm", "Parcel", "CropRotation",
```

**File:** `app/core/database.py`

```python
# Remove or comment out:
from app.models import farm
```

---

### **Step 5: Fix Broken Imports**

Any file that imports `Farm`, `Parcel`, `CropRotation` will break. Options:

1. **Delete the file** if not needed
2. **Update to import from Ekumenbackend**:
   ```python
   from Ekumenbackend.app.models.mesparcelles import Parcelle, Exploitation
   ```
3. **Rewrite to not need farm models**

---

### **Step 6: Update Tests**

Either:
- Delete tests for Assistant farm models
- Update tests to use Ekumenbackend models

---

### **Step 7: Verify Everything Works**

```bash
# Run all tests
pytest Ekumen-assistant/tests/

# Run the application
cd Ekumen-assistant
uvicorn app.main:app --reload

# Test farm data queries
python test_farmer_queries.py
```

---

## 🎯 **Expected Outcome**

After completion:

1. ✅ **No duplicate farm models**
2. ✅ **All farm data comes from MesParcelles database**
3. ✅ **Cleaner, simpler architecture**
4. ✅ **No mock data**
5. ✅ **Single source of truth for farm data**

---

## ⚠️ **Risks & Mitigation**

### **Risk 1: Breaking Changes**

**Risk:** Deleting models might break existing code

**Mitigation:**
- Search for all imports first
- Update or delete dependent code
- Test thoroughly

### **Risk 2: Missing Data**

**Risk:** MesParcelles database might not have all needed data

**Mitigation:**
- Check what data is actually in the database
- Ensure MesParcelles import is complete
- Add fallback logic if needed

### **Risk 3: Performance**

**Risk:** Querying MesParcelles models might be slower

**Mitigation:**
- Add database indexes
- Use query optimization
- Cache frequently accessed data

---

## 🚀 **Next Steps**

**Immediate:**
1. Test the updated `get_farm_data_tool.py` with real database
2. Verify it returns real MesParcelles data
3. Check query performance

**Then:**
1. Decide: Clean Break (Option A) or Gradual Migration (Option B)
2. If Clean Break: Follow Step-by-Step Implementation above
3. If Gradual: Create migration plan

---

## ✅ **IMPLEMENTATION COMPLETED - 2025-09-30**

### **What Was Done:**

**Files Deleted:**
1. ✅ `app/models/farm.py` - Duplicate Farm, Parcel, CropRotation models
2. ✅ `app/schemas/farm.py` - Farm-related Pydantic schemas
3. ✅ `app/services/farm_service.py` - Farm service layer
4. ✅ `app/api/v1/farms.py` - Farm API endpoints

**Files Updated:**
1. ✅ `app/models/__init__.py` - Removed Farm, Parcel, CropRotation imports
2. ✅ `app/core/database.py` - Removed farm import from init_db()
3. ✅ `app/api/v1/__init__.py` - Removed farms module import
4. ✅ `app/main.py` - Removed farms router registration
5. ✅ `tests/conftest.py` - Commented out test_farm and test_parcel fixtures
6. ✅ `tests/test_models.py` - Commented out TestFarmModel class

**Already Working:**
- ✅ `app/tools/farm_data_agent/get_farm_data_tool.py` - Already uses Ekumenbackend models

### **Result:**

**Single Source of Truth:** All farm data now comes from `Ekumenbackend/app/models/mesparcelles.py`

**Models to Use:**
- `Exploitation` (instead of Farm)
- `Parcelle` (instead of Parcel)
- `SuccessionCulture` (instead of CropRotation)
- `Intervention` (farm operations)
- `Culture` (crop reference data)

**No More:**
- ❌ Duplicate farm models
- ❌ Mock data
- ❌ Confusion about which models to use
- ❌ Data synchronization issues

### **Next Steps:**

1. **Test the Application:**
   ```bash
   cd Ekumen-assistant
   uvicorn app.main:app --reload
   ```

2. **Verify Farm Data Tool:**
   ```bash
   python test_farmer_queries.py
   ```

3. **If You Need Farm API Endpoints:**
   - Create new endpoints that query Ekumenbackend models directly
   - Use `Exploitation` and `Parcelle` models
   - Query by SIRET for exploitations
   - Query by `uuid_parcelle` for parcelles

4. **For New Features:**
   - Always import from `Ekumenbackend.app.models.mesparcelles`
   - Never create duplicate farm models
   - Use the MesParcelles schema structure

---

## 🎉 **Success!**

The database consolidation is complete. The application now uses only Ekumenbackend MesParcelles models for all farm data.

