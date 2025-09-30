-- Migration: Add crop EPPO code column to diseases table
-- Date: 2025-09-30
-- Purpose: Store EPPO codes for crops to enable international standardization
--
-- This migration adds a new column to store the EPPO code for the primary crop
-- associated with each disease, enabling:
-- - International crop identification
-- - Integration with EPPO databases
-- - Multilingual crop name support
-- - Standardized crop references

-- ============================================================================
-- STEP 1: Add primary_crop_eppo column
-- ============================================================================

ALTER TABLE diseases 
ADD COLUMN IF NOT EXISTS primary_crop_eppo VARCHAR(6);

COMMENT ON COLUMN diseases.primary_crop_eppo IS 
'EPPO code for primary crop (e.g., TRZAX for wheat, ZEAMX for maize)';


-- ============================================================================
-- STEP 2: Create index for fast lookups
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_diseases_primary_crop_eppo 
ON diseases(primary_crop_eppo);


-- ============================================================================
-- STEP 3: Populate primary_crop_eppo from primary_crop
-- ============================================================================

-- Mapping of French crop names to EPPO codes
-- Based on official EPPO Global Database (https://gd.eppo.int/)

UPDATE diseases SET primary_crop_eppo = 'TRZAX' WHERE primary_crop = 'blé';           -- Wheat
UPDATE diseases SET primary_crop_eppo = 'ZEAMX' WHERE primary_crop = 'maïs';          -- Maize/Corn
UPDATE diseases SET primary_crop_eppo = 'BRSNN' WHERE primary_crop = 'colza';         -- Rapeseed
UPDATE diseases SET primary_crop_eppo = 'HORVX' WHERE primary_crop = 'orge';          -- Barley
UPDATE diseases SET primary_crop_eppo = 'HELAN' WHERE primary_crop = 'tournesol';     -- Sunflower
UPDATE diseases SET primary_crop_eppo = 'SOLTU' WHERE primary_crop = 'pomme de terre'; -- Potato
UPDATE diseases SET primary_crop_eppo = 'BEAVA' WHERE primary_crop = 'betterave';     -- Sugar beet
UPDATE diseases SET primary_crop_eppo = 'VITVI' WHERE primary_crop = 'vigne';         -- Grapevine
UPDATE diseases SET primary_crop_eppo = 'SECCE' WHERE primary_crop = 'seigle';        -- Rye
UPDATE diseases SET primary_crop_eppo = 'AVESA' WHERE primary_crop = 'avoine';        -- Oat
UPDATE diseases SET primary_crop_eppo = 'TTLSP' WHERE primary_crop = 'triticale';     -- Triticale
UPDATE diseases SET primary_crop_eppo = 'GLXMA' WHERE primary_crop = 'soja';          -- Soybean
UPDATE diseases SET primary_crop_eppo = 'LIUUT' WHERE primary_crop = 'lin';           -- Flax
UPDATE diseases SET primary_crop_eppo = 'PIBSX' WHERE primary_crop = 'pois';          -- Pea
UPDATE diseases SET primary_crop_eppo = 'VICFX' WHERE primary_crop = 'féverole';      -- Faba bean
UPDATE diseases SET primary_crop_eppo = 'MEDSA' WHERE primary_crop = 'luzerne';       -- Alfalfa
UPDATE diseases SET primary_crop_eppo = 'MABSD' WHERE primary_crop = 'pommier';       -- Apple
UPDATE diseases SET primary_crop_eppo = 'POAPR' WHERE primary_crop = 'prairie';       -- Meadow grass


-- ============================================================================
-- STEP 4: Verification queries
-- ============================================================================

-- Check migration results
SELECT 
    primary_crop,
    primary_crop_eppo,
    COUNT(*) as disease_count
FROM diseases
GROUP BY primary_crop, primary_crop_eppo
ORDER BY primary_crop;

-- Check for diseases without EPPO codes
SELECT 
    COUNT(*) as total_diseases,
    COUNT(primary_crop_eppo) as with_crop_eppo,
    COUNT(*) - COUNT(primary_crop_eppo) as missing_crop_eppo
FROM diseases;

-- Show sample diseases with both crop identifiers
SELECT 
    name,
    scientific_name,
    primary_crop,
    primary_crop_eppo,
    eppo_code as disease_eppo_code
FROM diseases
ORDER BY primary_crop, name
LIMIT 20;


-- ============================================================================
-- STEP 5: Add constraint (optional - uncomment if you want strict validation)
-- ============================================================================

-- This ensures all new diseases must have a crop EPPO code
-- Uncomment only after verifying all existing diseases have been migrated

-- ALTER TABLE diseases 
-- ALTER COLUMN primary_crop_eppo SET NOT NULL;

-- Add check constraint to ensure EPPO code format (uppercase letters, 5-6 chars)
-- ALTER TABLE diseases
-- ADD CONSTRAINT ck_primary_crop_eppo_format 
-- CHECK (primary_crop_eppo ~ '^[A-Z]{5,6}$');


-- ============================================================================
-- ROLLBACK (if needed)
-- ============================================================================

-- To rollback this migration, run:
-- DROP INDEX IF EXISTS idx_diseases_primary_crop_eppo;
-- ALTER TABLE diseases DROP COLUMN IF EXISTS primary_crop_eppo;


-- ============================================================================
-- NOTES
-- ============================================================================

-- 1. This migration is backward compatible - existing queries still work
-- 2. The primary_crop column is kept for backward compatibility
-- 3. Both primary_crop (French name) and primary_crop_eppo (EPPO code) are maintained
-- 4. Future queries can use either identifier
-- 5. EPPO codes enable international integration and multilingual support

-- Example queries after migration:
-- 
-- Find all wheat diseases:
--   SELECT * FROM diseases WHERE primary_crop_eppo = 'TRZAX';
--
-- Find diseases by French name (still works):
--   SELECT * FROM diseases WHERE primary_crop = 'blé';
--
-- Join with BBCH stages:
--   SELECT d.*, b.* 
--   FROM diseases d
--   JOIN bbch_stages b ON d.primary_crop_eppo = b.crop_eppo_code
--   WHERE d.primary_crop_eppo = 'TRZAX';

