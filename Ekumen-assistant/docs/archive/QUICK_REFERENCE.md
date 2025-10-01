# Quick Reference: Using Ekumenbackend Models

**Last Updated:** 2025-09-30  
**Status:** Post-Consolidation

---

## 🚀 Quick Start

### **Import Models:**
```python
from Ekumenbackend.app.models.mesparcelles import (
    Exploitation,       # Farm
    Parcelle,          # Parcel/Field
    SuccessionCulture, # Crop rotation
    Intervention,      # Farm operations
    Culture,           # Crop reference data
    Region,            # Administrative regions
)
```

### **Get Database Session:**
```python
from app.core.database import get_async_db
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

# In async function
async def my_function(db: AsyncSession = Depends(get_async_db)):
    # Your queries here
    pass
```

---

## 📊 Model Reference

### **Exploitation (Farm)**

**Primary Key:** `siret` (String, 14 digits)

**Key Fields:**
- `siret` - French business identifier
- `raison_sociale` - Legal name
- `millesime` - Vintage year
- `code_region` - Region code
- `code_departement` - Department code

**Example Query:**
```python
# Get farm by SIRET
query = select(Exploitation).where(Exploitation.siret == "12345678901234")
result = await db.execute(query)
farm = result.scalar_one_or_none()
```

---

### **Parcelle (Parcel/Field)**

**Primary Key:** `uuid_parcelle` (UUID)

**Key Fields:**
- `uuid_parcelle` - Unique identifier
- `siret_exploitation` - Foreign key to Exploitation
- `numero_parcelle` - Parcel number
- `surface_ha` - Area in hectares
- `millesime` - Vintage year
- `geometry` - PostGIS geometry

**Example Query:**
```python
# Get parcels for a farm
query = select(Parcelle).where(
    Parcelle.siret_exploitation == "12345678901234"
)
result = await db.execute(query)
parcels = result.scalars().all()

# Get specific parcel
query = select(Parcelle).where(
    Parcelle.uuid_parcelle == "550e8400-e29b-41d4-a716-446655440000"
)
result = await db.execute(query)
parcel = result.scalar_one_or_none()
```

---

### **SuccessionCulture (Crop Rotation)**

**Primary Key:** `id` (Integer)

**Key Fields:**
- `uuid_parcelle` - Foreign key to Parcelle
- `code_culture` - Foreign key to Culture
- `date_debut_culture` - Planting date
- `date_fin_culture` - Harvest date
- `millesime` - Vintage year

**Example Query:**
```python
# Get crops for a parcel
query = (
    select(SuccessionCulture)
    .join(Culture)
    .where(SuccessionCulture.uuid_parcelle == parcel_uuid)
)
result = await db.execute(query)
crops = result.scalars().all()

# Get crop with details
for crop in crops:
    print(f"Crop: {crop.culture.libelle_culture}")
    print(f"Start: {crop.date_debut_culture}")
    print(f"End: {crop.date_fin_culture}")
```

---

### **Intervention (Farm Operation)**

**Primary Key:** `id` (Integer)

**Key Fields:**
- `uuid_parcelle` - Foreign key to Parcelle
- `type_intervention` - Type of operation
- `date_intervention` - Date of operation
- `code_amm` - AMM code (regulatory)
- `dose` - Application dose
- `unite_dose` - Dose unit

**Example Query:**
```python
# Get interventions for a parcel
query = select(Intervention).where(
    Intervention.uuid_parcelle == parcel_uuid
)
result = await db.execute(query)
interventions = result.scalars().all()

# Filter by type
query = select(Intervention).where(
    Intervention.uuid_parcelle == parcel_uuid,
    Intervention.type_intervention == "traitement"
)
```

---

### **Culture (Crop Reference)**

**Primary Key:** `code_culture` (String)

**Key Fields:**
- `code_culture` - Crop code
- `libelle_culture` - Crop name
- `famille_culture` - Crop family

**Example Query:**
```python
# Get crop by code
query = select(Culture).where(Culture.code_culture == "BLE")
result = await db.execute(query)
crop = result.scalar_one_or_none()

# Get all crops
query = select(Culture)
result = await db.execute(query)
all_crops = result.scalars().all()
```

---

## 🔍 Common Query Patterns

### **1. Get Farm with Parcels:**
```python
from sqlalchemy.orm import selectinload

query = (
    select(Exploitation)
    .options(selectinload(Exploitation.parcelles))
    .where(Exploitation.siret == siret)
)
result = await db.execute(query)
farm = result.scalar_one_or_none()

# Access parcels
for parcel in farm.parcelles:
    print(f"Parcel: {parcel.numero_parcelle}, Area: {parcel.surface_ha} ha")
```

### **2. Get Parcel with Crops and Interventions:**
```python
query = (
    select(Parcelle)
    .options(
        selectinload(Parcelle.succession_cultures),
        selectinload(Parcelle.interventions)
    )
    .where(Parcelle.uuid_parcelle == parcel_uuid)
)
result = await db.execute(query)
parcel = result.scalar_one_or_none()
```

### **3. Filter by Year (Millesime):**
```python
# Get parcels for current year
current_year = 2024
query = select(Parcelle).where(
    Parcelle.siret_exploitation == siret,
    Parcelle.millesime == current_year
)
```

### **4. Get Recent Interventions:**
```python
from datetime import datetime, timedelta

# Last 30 days
thirty_days_ago = datetime.now() - timedelta(days=30)
query = select(Intervention).where(
    Intervention.uuid_parcelle == parcel_uuid,
    Intervention.date_intervention >= thirty_days_ago
)
```

---

## 🛠️ Helper Functions

### **Convert to Dict:**
```python
def exploitation_to_dict(exploitation: Exploitation) -> dict:
    """Convert Exploitation to dictionary."""
    return {
        "siret": exploitation.siret,
        "raison_sociale": exploitation.raison_sociale,
        "millesime": exploitation.millesime,
        "region": exploitation.code_region,
        "department": exploitation.code_departement,
    }

def parcelle_to_dict(parcelle: Parcelle) -> dict:
    """Convert Parcelle to dictionary."""
    return {
        "uuid": str(parcelle.uuid_parcelle),
        "numero": parcelle.numero_parcelle,
        "surface_ha": float(parcelle.surface_ha) if parcelle.surface_ha else None,
        "siret_exploitation": parcelle.siret_exploitation,
        "millesime": parcelle.millesime,
    }
```

### **Format for API Response:**
```python
async def get_farm_summary(siret: str, db: AsyncSession) -> dict:
    """Get farm summary with parcels."""
    # Get farm
    farm_query = select(Exploitation).where(Exploitation.siret == siret)
    farm_result = await db.execute(farm_query)
    farm = farm_result.scalar_one_or_none()
    
    if not farm:
        return None
    
    # Get parcels
    parcels_query = select(Parcelle).where(Parcelle.siret_exploitation == siret)
    parcels_result = await db.execute(parcels_query)
    parcels = parcels_result.scalars().all()
    
    return {
        "farm": exploitation_to_dict(farm),
        "parcels": [parcelle_to_dict(p) for p in parcels],
        "total_parcels": len(parcels),
        "total_area_ha": sum(p.surface_ha or 0 for p in parcels),
    }
```

---

## ⚠️ Important Notes

### **1. SIRET Format:**
- Always 14 digits
- String type, not integer
- Example: `"12345678901234"`

### **2. UUID Parcelle:**
- UUID type, not string
- Use `str(uuid)` to convert to string
- Example: `"550e8400-e29b-41d4-a716-446655440000"`

### **3. Millesime (Year):**
- Integer representing the vintage year
- Important for temporal queries
- Example: `2024`

### **4. Async/Await:**
- All database operations are async
- Always use `await` with queries
- Use `AsyncSession` not `Session`

### **5. Relationships:**
- Use `selectinload()` to eager load relationships
- Prevents N+1 query problems
- More efficient than lazy loading

---

## 📚 Additional Resources

- **Full Plan:** `DATABASE_CONSOLIDATION_PLAN.md`
- **Detailed Summary:** `CONSOLIDATION_SUMMARY.md`
- **Completion Report:** `CONSOLIDATION_COMPLETE.md`
- **MesParcelles Models:** `Ekumenbackend/app/models/mesparcelles.py`

---

## 🆘 Troubleshooting

### **Import Error:**
```python
# ❌ Wrong
from app.models.farm import Farm

# ✅ Correct
from Ekumenbackend.app.models.mesparcelles import Exploitation
```

### **Query Returns None:**
```python
# Check SIRET format (must be string)
siret = "12345678901234"  # ✅ Correct
siret = 12345678901234    # ❌ Wrong

# Check millesime (year)
query = select(Parcelle).where(
    Parcelle.siret_exploitation == siret,
    Parcelle.millesime == 2024  # Make sure year is correct
)
```

### **Relationship Not Loaded:**
```python
# ❌ Wrong - lazy loading
query = select(Exploitation).where(Exploitation.siret == siret)
farm = await db.execute(query)
# farm.parcelles will trigger additional queries

# ✅ Correct - eager loading
from sqlalchemy.orm import selectinload

query = (
    select(Exploitation)
    .options(selectinload(Exploitation.parcelles))
    .where(Exploitation.siret == siret)
)
farm = await db.execute(query)
# farm.parcelles is already loaded
```

---

**Quick Reference Version:** 1.0  
**Last Updated:** 2025-09-30

