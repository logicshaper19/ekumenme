-- Migration: Fix Schema Alignment Between Models and Database
-- Date: 2025-09-30
-- Purpose: Add missing columns to bbch_stages and diseases tables
--
-- This migration fixes the schema mismatch between Ekumen-assistant models
-- and the actual database schema, enabling Phase 2 features to work correctly.

-- ============================================================================
-- STEP 1: Fix BBCH Stages Table
-- ============================================================================

-- Add id column as primary key (if it doesn't exist)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'bbch_stages' AND column_name = 'id'
    ) THEN
        -- Add id column
        ALTER TABLE bbch_stages ADD COLUMN id SERIAL;
        
        -- Make it primary key
        ALTER TABLE bbch_stages ADD PRIMARY KEY (id);
        
        RAISE NOTICE 'Added id column to bbch_stages';
    ELSE
        RAISE NOTICE 'id column already exists in bbch_stages';
    END IF;
END $$;

-- Add crop_type column (if it doesn't exist)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'bbch_stages' AND column_name = 'crop_type'
    ) THEN
        ALTER TABLE bbch_stages ADD COLUMN crop_type VARCHAR(50);
        RAISE NOTICE 'Added crop_type column to bbch_stages';
    ELSE
        RAISE NOTICE 'crop_type column already exists in bbch_stages';
    END IF;
END $$;

-- Populate crop_type from crop_eppo_code
UPDATE bbch_stages SET crop_type = 'blé' WHERE crop_eppo_code = 'TRZAX' AND crop_type IS NULL;
UPDATE bbch_stages SET crop_type = 'maïs' WHERE crop_eppo_code = 'ZEAMX' AND crop_type IS NULL;
UPDATE bbch_stages SET crop_type = 'colza' WHERE crop_eppo_code = 'BRSNN' AND crop_type IS NULL;
UPDATE bbch_stages SET crop_type = 'orge' WHERE crop_eppo_code = 'HORVX' AND crop_type IS NULL;
UPDATE bbch_stages SET crop_type = 'tournesol' WHERE crop_eppo_code = 'HELAN' AND crop_type IS NULL;
UPDATE bbch_stages SET crop_type = 'pomme de terre' WHERE crop_eppo_code = 'SOLTU' AND crop_type IS NULL;
UPDATE bbch_stages SET crop_type = 'betterave' WHERE crop_eppo_code = 'BEAVA' AND crop_type IS NULL;
UPDATE bbch_stages SET crop_type = 'vigne' WHERE crop_eppo_code = 'VITVI' AND crop_type IS NULL;
UPDATE bbch_stages SET crop_type = 'seigle' WHERE crop_eppo_code = 'SECCE' AND crop_type IS NULL;
UPDATE bbch_stages SET crop_type = 'avoine' WHERE crop_eppo_code = 'AVESA' AND crop_type IS NULL;
UPDATE bbch_stages SET crop_type = 'triticale' WHERE crop_eppo_code = 'TTLSP' AND crop_type IS NULL;
UPDATE bbch_stages SET crop_type = 'soja' WHERE crop_eppo_code = 'GLXMA' AND crop_type IS NULL;
UPDATE bbch_stages SET crop_type = 'lin' WHERE crop_eppo_code = 'LIUUT' AND crop_type IS NULL;
UPDATE bbch_stages SET crop_type = 'pois' WHERE crop_eppo_code = 'PIBSX' AND crop_type IS NULL;
UPDATE bbch_stages SET crop_type = 'féverole' WHERE crop_eppo_code = 'VICFX' AND crop_type IS NULL;
UPDATE bbch_stages SET crop_type = 'luzerne' WHERE crop_eppo_code = 'MEDSA' AND crop_type IS NULL;
UPDATE bbch_stages SET crop_type = 'pommier' WHERE crop_eppo_code = 'MABSD' AND crop_type IS NULL;
UPDATE bbch_stages SET crop_type = 'prairie' WHERE crop_eppo_code = 'POAPR' AND crop_type IS NULL;

-- Add optional columns for agricultural parameters
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'bbch_stages' AND column_name = 'typical_duration_days'
    ) THEN
        ALTER TABLE bbch_stages ADD COLUMN typical_duration_days INTEGER;
        RAISE NOTICE 'Added typical_duration_days column to bbch_stages';
    END IF;
END $$;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'bbch_stages' AND column_name = 'kc_value'
    ) THEN
        ALTER TABLE bbch_stages ADD COLUMN kc_value NUMERIC(3,2);
        RAISE NOTICE 'Added kc_value column to bbch_stages';
    END IF;
END $$;

-- Create indexes
CREATE INDEX IF NOT EXISTS ix_bbch_crop_type ON bbch_stages(crop_type);
CREATE INDEX IF NOT EXISTS ix_bbch_crop_code ON bbch_stages(crop_type, bbch_code);


-- ============================================================================
-- STEP 2: Fix Diseases Table
-- ============================================================================

-- Add primary_crop_eppo column (if it doesn't exist)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'diseases' AND column_name = 'primary_crop_eppo'
    ) THEN
        ALTER TABLE diseases ADD COLUMN primary_crop_eppo VARCHAR(6);
        RAISE NOTICE 'Added primary_crop_eppo column to diseases';
    ELSE
        RAISE NOTICE 'primary_crop_eppo column already exists in diseases';
    END IF;
END $$;

-- Populate primary_crop_eppo from primary_crop using crops table
UPDATE diseases d
SET primary_crop_eppo = c.eppo_code
FROM crops c
WHERE d.primary_crop = c.name_fr
AND d.primary_crop_eppo IS NULL;

-- Add crop_id column (if it doesn't exist)
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'diseases' AND column_name = 'crop_id'
    ) THEN
        ALTER TABLE diseases ADD COLUMN crop_id INTEGER;
        RAISE NOTICE 'Added crop_id column to diseases';
    ELSE
        RAISE NOTICE 'crop_id column already exists in diseases';
    END IF;
END $$;

-- Populate crop_id from primary_crop_eppo
UPDATE diseases d
SET crop_id = c.id
FROM crops c
WHERE d.primary_crop_eppo = c.eppo_code
AND d.crop_id IS NULL;

-- Create indexes
CREATE INDEX IF NOT EXISTS ix_diseases_primary_crop_eppo ON diseases(primary_crop_eppo);
CREATE INDEX IF NOT EXISTS ix_diseases_crop_id ON diseases(crop_id);

-- Add comments
COMMENT ON COLUMN diseases.primary_crop_eppo IS 'EPPO code for primary crop (e.g., TRZAX for wheat)';
COMMENT ON COLUMN diseases.crop_id IS 'Foreign key to crops table (optional for referential integrity)';


-- ============================================================================
-- STEP 3: Verification Queries
-- ============================================================================

-- Check BBCH stages
SELECT 
    'BBCH Stages' as table_name,
    COUNT(*) as total_rows,
    COUNT(id) as with_id,
    COUNT(crop_type) as with_crop_type,
    COUNT(crop_eppo_code) as with_eppo_code
FROM bbch_stages;

-- Check diseases
SELECT 
    'Diseases' as table_name,
    COUNT(*) as total_rows,
    COUNT(primary_crop) as with_primary_crop,
    COUNT(primary_crop_eppo) as with_crop_eppo,
    COUNT(crop_id) as with_crop_id
FROM diseases;

-- Check crops
SELECT 
    'Crops' as table_name,
    COUNT(*) as total_rows,
    COUNT(DISTINCT eppo_code) as unique_eppo_codes
FROM crops
WHERE is_active = TRUE;

-- Show sample data
SELECT 
    id,
    crop_type,
    crop_eppo_code,
    bbch_code,
    description_fr
FROM bbch_stages
LIMIT 5;

SELECT 
    id,
    name,
    primary_crop,
    primary_crop_eppo,
    crop_id
FROM diseases
LIMIT 5;


-- ============================================================================
-- STEP 4: Optional Foreign Key Constraints (Commented Out)
-- ============================================================================

-- Uncomment these if you want strict referential integrity

-- Add foreign key from bbch_stages to crops
-- ALTER TABLE bbch_stages 
-- ADD CONSTRAINT fk_bbch_crop 
-- FOREIGN KEY (crop_eppo_code) REFERENCES crops(eppo_code);

-- Add foreign key from diseases to crops
-- ALTER TABLE diseases 
-- ADD CONSTRAINT fk_diseases_crop 
-- FOREIGN KEY (crop_id) REFERENCES crops(id);


-- ============================================================================
-- ROLLBACK (if needed)
-- ============================================================================

-- To rollback this migration, run:
-- ALTER TABLE bbch_stages DROP COLUMN IF EXISTS id CASCADE;
-- ALTER TABLE bbch_stages DROP COLUMN IF EXISTS crop_type;
-- ALTER TABLE bbch_stages DROP COLUMN IF EXISTS typical_duration_days;
-- ALTER TABLE bbch_stages DROP COLUMN IF EXISTS kc_value;
-- ALTER TABLE diseases DROP COLUMN IF EXISTS primary_crop_eppo;
-- ALTER TABLE diseases DROP COLUMN IF EXISTS crop_id;


-- ============================================================================
-- NOTES
-- ============================================================================

-- This migration:
-- 1. Adds missing columns to bbch_stages (id, crop_type, typical_duration_days, kc_value)
-- 2. Adds missing columns to diseases (primary_crop_eppo, crop_id)
-- 3. Populates new columns from existing data
-- 4. Creates indexes for performance
-- 5. Is idempotent (can be run multiple times safely)
-- 6. Is backward compatible (doesn't remove or modify existing columns)

-- After this migration:
-- - Ekumen-assistant models will match database schema
-- - Phase 2 features will work correctly
-- - All tests should pass (7/7)
-- - Crop table relationships will be functional

