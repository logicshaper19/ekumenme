-- Migration: Create crops table and update related tables
-- Date: 2025-09-30
-- Purpose: Create centralized crop reference table with EPPO codes
--
-- This migration:
-- 1. Creates crops table with EPPO standardization
-- 2. Populates with 24 major French crops
-- 3. Adds crop_eppo_code to bbch_stages
-- 4. Optionally adds crop_id to diseases (backward compatible)

-- ============================================================================
-- STEP 1: Create crops table
-- ============================================================================

CREATE TABLE IF NOT EXISTS crops (
    id SERIAL PRIMARY KEY,
    
    -- Names (multilingual)
    name_fr VARCHAR(100) NOT NULL UNIQUE,
    name_en VARCHAR(100),
    scientific_name VARCHAR(200),
    
    -- EPPO standardization
    eppo_code VARCHAR(6) NOT NULL UNIQUE,
    
    -- Classification
    category VARCHAR(50),
    family VARCHAR(100),
    
    -- Additional metadata
    common_names TEXT,
    description TEXT,
    
    -- Agricultural characteristics
    growing_season VARCHAR(50),
    typical_duration_days INTEGER,
    
    -- Status
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

-- Create indexes
CREATE INDEX IF NOT EXISTS ix_crops_name_fr ON crops(name_fr);
CREATE INDEX IF NOT EXISTS ix_crops_eppo_code ON crops(eppo_code);
CREATE INDEX IF NOT EXISTS ix_crops_category ON crops(category);
CREATE INDEX IF NOT EXISTS ix_crops_active ON crops(is_active);

-- Add comments
COMMENT ON TABLE crops IS 'Centralized crop reference data with EPPO standardization';
COMMENT ON COLUMN crops.name_fr IS 'French crop name (e.g., blé, maïs)';
COMMENT ON COLUMN crops.name_en IS 'English crop name (e.g., wheat, corn)';
COMMENT ON COLUMN crops.eppo_code IS 'Official EPPO code (e.g., TRZAX for wheat)';
COMMENT ON COLUMN crops.category IS 'Crop category: cereal, oilseed, root_crop, legume, fruit, vegetable, forage';


-- ============================================================================
-- STEP 2: Populate crops table with 24 major French crops
-- ============================================================================

INSERT INTO crops (name_fr, name_en, scientific_name, eppo_code, category, family, growing_season, typical_duration_days) VALUES
-- Cereals (Céréales)
('blé', 'wheat', 'Triticum aestivum', 'TRZAX', 'cereal', 'Poaceae', 'winter', 240),
('orge', 'barley', 'Hordeum vulgare', 'HORVX', 'cereal', 'Poaceae', 'winter', 180),
('maïs', 'corn', 'Zea mays', 'ZEAMX', 'cereal', 'Poaceae', 'summer', 150),
('seigle', 'rye', 'Secale cereale', 'SECCE', 'cereal', 'Poaceae', 'winter', 240),
('avoine', 'oat', 'Avena sativa', 'AVESA', 'cereal', 'Poaceae', 'spring', 120),
('triticale', 'triticale', 'Triticosecale', 'TTLSP', 'cereal', 'Poaceae', 'winter', 240),

-- Oilseeds (Oléagineux)
('colza', 'rapeseed', 'Brassica napus', 'BRSNN', 'oilseed', 'Brassicaceae', 'winter', 300),
('tournesol', 'sunflower', 'Helianthus annuus', 'HELAN', 'oilseed', 'Asteraceae', 'summer', 120),
('soja', 'soybean', 'Glycine max', 'GLXMA', 'oilseed', 'Fabaceae', 'summer', 140),
('lin', 'flax', 'Linum usitatissimum', 'LIUUT', 'oilseed', 'Linaceae', 'spring', 100),

-- Root crops (Cultures racines)
('betterave', 'sugar beet', 'Beta vulgaris', 'BEAVA', 'root_crop', 'Amaranthaceae', 'spring', 180),
('pomme de terre', 'potato', 'Solanum tuberosum', 'SOLTU', 'root_crop', 'Solanaceae', 'spring', 120),
('carotte', 'carrot', 'Daucus carota', 'DAUCA', 'root_crop', 'Apiaceae', 'spring', 90),

-- Legumes (Légumineuses)
('pois', 'pea', 'Pisum sativum', 'PIBSX', 'legume', 'Fabaceae', 'spring', 90),
('féverole', 'faba bean', 'Vicia faba', 'VICFX', 'legume', 'Fabaceae', 'winter', 210),
('luzerne', 'alfalfa', 'Medicago sativa', 'MEDSA', 'legume', 'Fabaceae', 'perennial', 365),
('haricot', 'bean', 'Phaseolus vulgaris', 'PHSVX', 'legume', 'Fabaceae', 'summer', 80),

-- Fruits & Vines (Fruits et vignes)
('vigne', 'grapevine', 'Vitis vinifera', 'VITVI', 'fruit', 'Vitaceae', 'perennial', 365),
('pommier', 'apple', 'Malus domestica', 'MABSD', 'fruit', 'Rosaceae', 'perennial', 365),
('poirier', 'pear', 'Pyrus communis', 'PYUCO', 'fruit', 'Rosaceae', 'perennial', 365),

-- Forages (Fourrages)
('prairie', 'meadow grass', 'Poa pratensis', 'POAPR', 'forage', 'Poaceae', 'perennial', 365),
('ray-grass', 'ryegrass', 'Lolium species', 'LOLSS', 'forage', 'Poaceae', 'perennial', 365),

-- Vegetables (Légumes)
('tomate', 'tomato', 'Solanum lycopersicum', 'LYPES', 'vegetable', 'Solanaceae', 'summer', 120),
('salade', 'lettuce', 'Lactuca sativa', 'LACSA', 'vegetable', 'Asteraceae', 'spring', 60)

ON CONFLICT (eppo_code) DO NOTHING;


-- ============================================================================
-- STEP 3: Add crop_eppo_code to bbch_stages table
-- ============================================================================

-- Add column
ALTER TABLE bbch_stages 
ADD COLUMN IF NOT EXISTS crop_eppo_code VARCHAR(6);

-- Populate from existing crop_type
UPDATE bbch_stages SET crop_eppo_code = 'TRZAX' WHERE crop_type = 'blé';
UPDATE bbch_stages SET crop_eppo_code = 'ZEAMX' WHERE crop_type = 'maïs';
UPDATE bbch_stages SET crop_eppo_code = 'BRSNN' WHERE crop_type = 'colza';
UPDATE bbch_stages SET crop_eppo_code = 'HORVX' WHERE crop_type = 'orge';
UPDATE bbch_stages SET crop_eppo_code = 'HELAN' WHERE crop_type = 'tournesol';
UPDATE bbch_stages SET crop_eppo_code = 'SOLTU' WHERE crop_type = 'pomme de terre';
UPDATE bbch_stages SET crop_eppo_code = 'BEAVA' WHERE crop_type = 'betterave';
UPDATE bbch_stages SET crop_eppo_code = 'VITVI' WHERE crop_type = 'vigne';
UPDATE bbch_stages SET crop_eppo_code = 'SECCE' WHERE crop_type = 'seigle';
UPDATE bbch_stages SET crop_eppo_code = 'AVESA' WHERE crop_type = 'avoine';
UPDATE bbch_stages SET crop_eppo_code = 'TTLSP' WHERE crop_type = 'triticale';
UPDATE bbch_stages SET crop_eppo_code = 'GLXMA' WHERE crop_type = 'soja';
UPDATE bbch_stages SET crop_eppo_code = 'LIUUT' WHERE crop_type = 'lin';
UPDATE bbch_stages SET crop_eppo_code = 'PIBSX' WHERE crop_type = 'pois';
UPDATE bbch_stages SET crop_eppo_code = 'VICFX' WHERE crop_type = 'féverole';
UPDATE bbch_stages SET crop_eppo_code = 'MEDSA' WHERE crop_type = 'luzerne';
UPDATE bbch_stages SET crop_eppo_code = 'MABSD' WHERE crop_type = 'pommier';
UPDATE bbch_stages SET crop_eppo_code = 'POAPR' WHERE crop_type = 'prairie';

-- Create index
CREATE INDEX IF NOT EXISTS ix_bbch_crop_eppo ON bbch_stages(crop_eppo_code);

-- Add foreign key constraint (optional - uncomment if you want strict referential integrity)
-- ALTER TABLE bbch_stages 
-- ADD CONSTRAINT fk_bbch_crop 
-- FOREIGN KEY (crop_eppo_code) REFERENCES crops(eppo_code);

COMMENT ON COLUMN bbch_stages.crop_eppo_code IS 'EPPO code linking to crops table';


-- ============================================================================
-- STEP 4: Optionally add crop_id to diseases table (backward compatible)
-- ============================================================================

-- Add column (nullable for backward compatibility)
ALTER TABLE diseases 
ADD COLUMN IF NOT EXISTS crop_id INTEGER;

-- Populate from existing primary_crop_eppo
UPDATE diseases d
SET crop_id = c.id
FROM crops c
WHERE d.primary_crop_eppo = c.eppo_code;

-- Create index
CREATE INDEX IF NOT EXISTS ix_diseases_crop_id ON diseases(crop_id);

-- Add foreign key constraint (optional - uncomment if you want strict referential integrity)
-- ALTER TABLE diseases 
-- ADD CONSTRAINT fk_diseases_crop 
-- FOREIGN KEY (crop_id) REFERENCES crops(id);

COMMENT ON COLUMN diseases.crop_id IS 'Foreign key to crops table (optional, for referential integrity)';


-- ============================================================================
-- STEP 5: Verification queries
-- ============================================================================

-- Check crops table
SELECT 
    COUNT(*) as total_crops,
    COUNT(DISTINCT category) as categories,
    COUNT(DISTINCT family) as families
FROM crops
WHERE is_active = TRUE;

-- Show crops by category
SELECT 
    category,
    COUNT(*) as crop_count,
    STRING_AGG(name_fr, ', ' ORDER BY name_fr) as crops
FROM crops
WHERE is_active = TRUE
GROUP BY category
ORDER BY category;

-- Check BBCH stages with EPPO codes
SELECT 
    crop_type,
    crop_eppo_code,
    COUNT(*) as stage_count
FROM bbch_stages
GROUP BY crop_type, crop_eppo_code
ORDER BY crop_type;

-- Check diseases with crop references
SELECT 
    primary_crop,
    primary_crop_eppo,
    crop_id,
    COUNT(*) as disease_count
FROM diseases
GROUP BY primary_crop, primary_crop_eppo, crop_id
ORDER BY primary_crop;

-- Verify crop linkages
SELECT 
    c.name_fr,
    c.eppo_code,
    COUNT(DISTINCT d.id) as disease_count,
    COUNT(DISTINCT b.id) as bbch_stage_count
FROM crops c
LEFT JOIN diseases d ON c.id = d.crop_id
LEFT JOIN bbch_stages b ON c.eppo_code = b.crop_eppo_code
WHERE c.is_active = TRUE
GROUP BY c.id, c.name_fr, c.eppo_code
ORDER BY c.name_fr;


-- ============================================================================
-- STEP 6: Create helper views (optional)
-- ============================================================================

-- View: Crops with disease and BBCH counts
CREATE OR REPLACE VIEW crop_summary AS
SELECT 
    c.id,
    c.name_fr,
    c.name_en,
    c.eppo_code,
    c.category,
    c.family,
    COUNT(DISTINCT d.id) as disease_count,
    COUNT(DISTINCT b.id) as bbch_stage_count,
    c.is_active
FROM crops c
LEFT JOIN diseases d ON c.id = d.crop_id
LEFT JOIN bbch_stages b ON c.eppo_code = b.crop_eppo_code
GROUP BY c.id, c.name_fr, c.name_en, c.eppo_code, c.category, c.family, c.is_active
ORDER BY c.name_fr;

COMMENT ON VIEW crop_summary IS 'Summary view of crops with disease and BBCH stage counts';


-- ============================================================================
-- ROLLBACK (if needed)
-- ============================================================================

-- To rollback this migration, run:
-- DROP VIEW IF EXISTS crop_summary;
-- ALTER TABLE diseases DROP COLUMN IF EXISTS crop_id;
-- ALTER TABLE bbch_stages DROP COLUMN IF EXISTS crop_eppo_code;
-- DROP TABLE IF EXISTS crops CASCADE;


-- ============================================================================
-- NOTES
-- ============================================================================

-- 1. This migration is backward compatible
-- 2. Old fields (primary_crop, crop_type) are kept
-- 3. New fields (crop_id, crop_eppo_code) are added
-- 4. Foreign key constraints are optional (commented out)
-- 5. Can be enabled later for strict referential integrity

-- Example queries after migration:
--
-- Get crop by EPPO code:
--   SELECT * FROM crops WHERE eppo_code = 'TRZAX';
--
-- Get all diseases for a crop:
--   SELECT d.* FROM diseases d
--   JOIN crops c ON d.crop_id = c.id
--   WHERE c.eppo_code = 'TRZAX';
--
-- Get BBCH stages for a crop:
--   SELECT b.* FROM bbch_stages b
--   JOIN crops c ON b.crop_eppo_code = c.eppo_code
--   WHERE c.name_fr = 'blé';
--
-- Get diseases and BBCH stages for a crop:
--   SELECT c.name_fr, d.name as disease, b.bbch_code, b.description_fr
--   FROM crops c
--   LEFT JOIN diseases d ON c.id = d.crop_id
--   LEFT JOIN bbch_stages b ON c.eppo_code = b.crop_eppo_code
--   WHERE c.eppo_code = 'TRZAX';

