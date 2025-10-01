# 🚀 Crop EPPO Codes - Deployment Checklist

## Pre-Deployment Verification

### ✅ Code Quality
- [x] All tests pass (8/8 in `test_crop_eppo_codes.py`)
- [x] No linting errors
- [x] Type hints complete
- [x] Documentation complete

### ✅ Files Created
- [x] `app/constants/crop_eppo_codes.py` - Constants module
- [x] `app/migrations/add_crop_eppo_codes.sql` - Database migration
- [x] `test_crop_eppo_codes.py` - Test suite
- [x] `CROP_EPPO_CODES_IMPLEMENTATION.md` - Implementation guide
- [x] `CROP_EPPO_IMPLEMENTATION_SUMMARY.md` - Summary document
- [x] `DEPLOYMENT_CHECKLIST.md` - This file

### ✅ Files Modified
- [x] `app/models/disease.py` - Added `primary_crop_eppo` field
- [x] `app/scripts/seed_all_57_diseases.py` - Added validation and EPPO codes

---

## Deployment Steps

### Step 1: Backup Database ⚠️
```bash
# Create backup before running migration
pg_dump -U your_user -d your_database > backup_before_crop_eppo_$(date +%Y%m%d).sql
```

### Step 2: Run Database Migration
```bash
# Connect to your database
psql -U your_user -d your_database

# Run migration
\i Ekumen-assistant/app/migrations/add_crop_eppo_codes.sql

# Verify migration
SELECT 
    COUNT(*) as total_diseases,
    COUNT(primary_crop_eppo) as with_eppo,
    COUNT(*) - COUNT(primary_crop_eppo) as missing_eppo
FROM diseases;

# Expected: All diseases should have EPPO codes
```

### Step 3: Verify Migration
```bash
# Check sample data
SELECT 
    name,
    primary_crop,
    primary_crop_eppo,
    eppo_code
FROM diseases
LIMIT 10;

# Expected output:
# name          | primary_crop | primary_crop_eppo | eppo_code
# --------------|--------------|-------------------|----------
# Septoriose    | blé          | TRZAX             | SEPTTR
# Rouille jaune | blé          | TRZAX             | PUCCST
# ...
```

### Step 4: Run Tests
```bash
cd Ekumen-assistant
python test_crop_eppo_codes.py

# Expected: All 8 tests pass
```

### Step 5: Test Seeding Script (Optional)
```bash
# Only run if you want to add new diseases
python app/scripts/seed_all_57_diseases.py

# This will:
# - Validate all crops
# - Skip existing diseases
# - Add new diseases with EPPO codes
```

### Step 6: Verify Application
```bash
# Start your application
# Test disease queries with both methods:

# Method 1: French name (backward compatible)
SELECT * FROM diseases WHERE primary_crop = 'blé';

# Method 2: EPPO code (new feature)
SELECT * FROM diseases WHERE primary_crop_eppo = 'TRZAX';

# Both should return the same results
```

---

## Rollback Plan (If Needed)

### If Migration Fails
```bash
# Restore from backup
psql -U your_user -d your_database < backup_before_crop_eppo_YYYYMMDD.sql
```

### If Migration Succeeds But Issues Found
```sql
-- Remove the column
DROP INDEX IF EXISTS idx_diseases_primary_crop_eppo;
ALTER TABLE diseases DROP COLUMN IF EXISTS primary_crop_eppo;

-- Application will continue working (backward compatible)
```

---

## Post-Deployment Verification

### ✅ Database Checks
```sql
-- 1. Check all diseases have crop EPPO codes
SELECT 
    primary_crop,
    COUNT(*) as disease_count,
    COUNT(primary_crop_eppo) as with_eppo
FROM diseases
GROUP BY primary_crop
HAVING COUNT(*) != COUNT(primary_crop_eppo);

-- Expected: No rows (all diseases have EPPO codes)

-- 2. Check EPPO code format
SELECT DISTINCT primary_crop_eppo 
FROM diseases 
WHERE primary_crop_eppo !~ '^[A-Z]{5,6}$';

-- Expected: No rows (all EPPO codes are valid format)

-- 3. Check crop coverage
SELECT DISTINCT primary_crop, primary_crop_eppo 
FROM diseases 
ORDER BY primary_crop;

-- Expected: All crops have valid EPPO codes
```

### ✅ Application Checks
- [ ] Disease diagnosis API works
- [ ] Crop validation works
- [ ] EPPO code lookups work
- [ ] Backward compatibility maintained (French names still work)

---

## Integration Points

### Update These Components (If Applicable)

#### 1. Disease Diagnosis Tool
```python
# File: app/tools/crop_health_agent/disease_diagnosis_tool.py

from app.constants.crop_eppo_codes import validate_crop_strict, get_eppo_code

# Add validation in input schema
@field_validator('crop_type')
def validate_crop(cls, v):
    return validate_crop_strict(v)
```

#### 2. API Endpoints
```python
# File: app/api/endpoints/diseases.py

from app.constants.crop_eppo_codes import get_eppo_code

# Support both French names and EPPO codes
@router.get("/diseases/by-crop/{crop_identifier}")
async def get_diseases_by_crop(crop_identifier: str):
    # Try as EPPO code first
    if len(crop_identifier) <= 6 and crop_identifier.isupper():
        return db.query(Disease).filter(
            Disease.primary_crop_eppo == crop_identifier
        ).all()
    else:
        # French name
        return db.query(Disease).filter(
            Disease.primary_crop == crop_identifier
        ).all()
```

#### 3. BBCH Stages (Future Enhancement)
```python
# File: app/models/bbch_stage.py

# Consider adding crop_eppo_code field in future
# crop_eppo_code = Column(String(6), nullable=True, index=True)
```

---

## Performance Considerations

### Index Performance
```sql
-- Check index usage
EXPLAIN ANALYZE 
SELECT * FROM diseases WHERE primary_crop_eppo = 'TRZAX';

-- Should use: Index Scan using idx_diseases_primary_crop_eppo
```

### Query Optimization
```sql
-- If you frequently join with BBCH stages, consider:
CREATE INDEX idx_bbch_crop_type ON bbch_stages(crop_type);

-- Future: Add crop_eppo_code to bbch_stages for direct joins
```

---

## Monitoring

### Metrics to Track
- [ ] Query performance (before/after migration)
- [ ] API response times
- [ ] Error rates in crop validation
- [ ] Usage of EPPO codes vs French names

### Logging
```python
# Add logging to track EPPO code usage
import logging

logger = logging.getLogger(__name__)

def get_diseases_by_crop(crop_identifier: str):
    logger.info(f"Disease query: crop={crop_identifier}")
    # ... query logic
```

---

## Documentation Updates

### Update These Docs
- [ ] API documentation (add EPPO code support)
- [ ] User guide (explain crop identification options)
- [ ] Developer guide (link to CROP_EPPO_CODES_IMPLEMENTATION.md)

---

## Communication Plan

### Notify Stakeholders
- [ ] Development team: New constants module available
- [ ] QA team: New test suite to include in regression tests
- [ ] Product team: New feature (EPPO code support)
- [ ] Users: Backward compatible, no changes needed

### Release Notes Template
```markdown
## New Feature: EPPO Crop Codes

We've added support for international EPPO codes for crop identification:

**What's New:**
- Crops can now be identified by EPPO codes (e.g., TRZAX for wheat)
- 24 major French crops supported
- Backward compatible - French names still work

**Benefits:**
- International compatibility
- Language-independent queries
- Future-proof for multilingual support

**For Developers:**
- New module: `app.constants.crop_eppo_codes`
- Database field: `diseases.primary_crop_eppo`
- See: CROP_EPPO_CODES_IMPLEMENTATION.md
```

---

## Success Criteria

### ✅ Deployment Successful If:
- [ ] Database migration completes without errors
- [ ] All tests pass (8/8)
- [ ] No performance degradation
- [ ] Backward compatibility maintained
- [ ] No errors in application logs
- [ ] Sample queries return expected results

### ⚠️ Rollback If:
- [ ] Migration fails
- [ ] Tests fail
- [ ] Performance degrades significantly
- [ ] Application errors increase
- [ ] Data integrity issues found

---

## Next Steps (Future Enhancements)

### Phase 2 (Optional)
1. Create dedicated `Crop` table
2. Add EPPO codes to BBCH stages
3. Multilingual crop names
4. Crop variety tracking
5. EPPO database API integration

---

## Support

### If Issues Arise
1. Check logs: `tail -f /var/log/your_app.log`
2. Verify database: Run verification queries above
3. Run tests: `python test_crop_eppo_codes.py`
4. Check documentation: `CROP_EPPO_CODES_IMPLEMENTATION.md`

### Contact
- Development team: [your-team@example.com]
- Documentation: See `CROP_EPPO_CODES_IMPLEMENTATION.md`
- Tests: Run `test_crop_eppo_codes.py`

---

## Final Checklist

Before marking deployment complete:

- [ ] Database backup created
- [ ] Migration executed successfully
- [ ] All tests pass
- [ ] Sample queries verified
- [ ] Application tested
- [ ] Performance acceptable
- [ ] Documentation updated
- [ ] Stakeholders notified
- [ ] Monitoring in place
- [ ] Rollback plan ready

---

## 🎉 Deployment Complete!

Once all items are checked, the EPPO crop codes feature is live and ready for use!

**Date Deployed**: _______________
**Deployed By**: _______________
**Database Version**: _______________
**Application Version**: _______________

