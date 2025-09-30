-- Migration: Add EPPO code column to diseases table
-- Date: 2025-09-30
-- Purpose: Add dedicated column for EPPO codes with unique constraint

-- Add eppo_code column
ALTER TABLE diseases 
ADD COLUMN IF NOT EXISTS eppo_code VARCHAR(10);

-- Create index for fast lookups
CREATE INDEX IF NOT EXISTS idx_diseases_eppo_code ON diseases(eppo_code);

-- Add unique constraint (after data migration)
-- ALTER TABLE diseases ADD CONSTRAINT unique_eppo_code UNIQUE (eppo_code);

-- Migrate existing EPPO codes from description field to eppo_code column
-- This extracts "EPPO: XXXXX" from description field

UPDATE diseases
SET eppo_code = 
    CASE 
        WHEN description LIKE '%EPPO:%' THEN
            TRIM(SUBSTRING(description FROM 'EPPO: ([A-Z0-9]+)'))
        ELSE NULL
    END
WHERE eppo_code IS NULL;

-- Verify migration
SELECT 
    name,
    scientific_name,
    eppo_code,
    primary_crop
FROM diseases
ORDER BY primary_crop, name;

-- Check for missing EPPO codes
SELECT 
    COUNT(*) as total_diseases,
    COUNT(eppo_code) as with_eppo_code,
    COUNT(*) - COUNT(eppo_code) as missing_eppo_code
FROM diseases;

