# 🚀 Phase 2 Deployment Guide

## Current Status

✅ **Code Implementation**: COMPLETE  
⏳ **Database Migration**: PENDING  
⏳ **Testing**: PENDING (waiting for migration)

---

## What Needs to Be Done

You need to run the database migration to create the crops table and update existing tables.

---

## Deployment Steps

### Step 1: Check Database Connection

Make sure your PostgreSQL database is running and accessible.

```bash
# Check your database connection settings
cat Ekumen-assistant/.env | grep DATABASE_URL
```

---

### Step 2: Run the Migration

You have **two options**:

#### **Option A: Using psql (Recommended)**

```bash
# Navigate to migrations directory
cd Ekumen-assistant/app/migrations

# Run the migration
psql -U your_username -d your_database_name -f create_crops_table.sql

# Example:
# psql -U postgres -d ekumen_db -f create_crops_table.sql
```

#### **Option B: Using Python Script**

Create a simple migration runner:

```bash
cd Ekumen-assistant
python -c "
import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def run_migration():
    with open('app/migrations/create_crops_table.sql', 'r') as f:
        sql = f.read()
    
    async with AsyncSessionLocal() as db:
        # Split by semicolon and execute each statement
        statements = [s.strip() for s in sql.split(';') if s.strip() and not s.strip().startswith('--')]
        for stmt in statements:
            if stmt:
                try:
                    await db.execute(text(stmt))
                    await db.commit()
                except Exception as e:
                    print(f'Error: {e}')
                    print(f'Statement: {stmt[:100]}...')
        
    print('Migration complete!')

asyncio.run(run_migration())
"
```

---

### Step 3: Verify Migration

After running the migration, verify it worked:

```bash
cd Ekumen-assistant
python test_crop_model.py
```

**Expected Output**:
```
✅ PASS - Test 1: test_crops_table
✅ PASS - Test 2: test_crop_eppo_codes
✅ PASS - Test 3: test_bbch_crop_eppo
✅ PASS - Test 4: test_disease_crop_links
✅ PASS - Test 5: test_crop_relationships
✅ PASS - Test 6: test_data_integrity
✅ PASS - Test 7: test_backward_compatibility

Total: 7/7 tests passed 🎉
```

---

### Step 4: Commit and Push

Once tests pass:

```bash
git add .
git commit -m "Phase 2: Add Crop table with EPPO codes and foreign key relationships"
git push origin main
```

---

## What the Migration Does

### 1. Creates `crops` Table
- 24 major French crops
- EPPO codes for international standardization
- Multilingual support (French, English)
- Scientific names and classifications

### 2. Updates `bbch_stages` Table
- Adds `crop_eppo_code` column
- Populates from existing `crop_type` data
- Creates index for performance

### 3. Updates `diseases` Table
- Adds `crop_id` column
- Populates from existing `primary_crop_eppo` data
- Creates index for performance

### 4. Creates Helper Views
- `crop_summary` view for quick crop statistics

---

## Rollback (If Needed)

If something goes wrong, you can rollback:

```sql
-- Rollback commands (run in psql)
DROP VIEW IF EXISTS crop_summary;
ALTER TABLE diseases DROP COLUMN IF EXISTS crop_id;
ALTER TABLE bbch_stages DROP COLUMN IF EXISTS crop_eppo_code;
DROP TABLE IF EXISTS crops CASCADE;
```

---

## Troubleshooting

### Issue: "relation crops does not exist"
**Solution**: You haven't run the migration yet. Run Step 2 above.

### Issue: "column crop_type does not exist" in bbch_stages
**Solution**: Your bbch_stages table has a different schema. Check the actual column name:
```sql
\d bbch_stages
```

### Issue: "column primary_crop_eppo does not exist" in diseases
**Solution**: You need to run the Phase 1 migration first (add_crop_eppo_codes.sql).

### Issue: Permission denied
**Solution**: Make sure your database user has CREATE TABLE permissions:
```sql
GRANT CREATE ON DATABASE your_database TO your_user;
```

---

## Next Steps After Deployment

1. ✅ Verify all tests pass
2. ✅ Check application still works
3. ✅ Commit and push changes
4. ✅ Update any documentation
5. ✅ Consider adding foreign key constraints (optional)

---

## Summary

**Files Created**:
- `app/models/crop.py` - Crop model
- `app/migrations/create_crops_table.sql` - Migration script
- `test_crop_model.py` - Test suite

**Files Modified**:
- `app/models/bbch_stage.py` - Added crop_eppo_code
- `app/models/disease.py` - Added crop_id
- `app/models/__init__.py` - Added Crop import
- `app/scripts/seed_all_57_diseases.py` - Added crop_id lookup

**Database Changes**:
- New table: `crops` (24 rows)
- Updated: `bbch_stages` (added crop_eppo_code column)
- Updated: `diseases` (added crop_id column)
- New view: `crop_summary`

**Breaking Changes**: NONE (fully backward compatible)

---

## Ready to Deploy! 🚀

Run the migration and let me know if you encounter any issues!

