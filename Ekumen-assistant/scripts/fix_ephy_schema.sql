-- Fix EPHY schema issues
-- Run this in Supabase SQL Editor

-- Increase numero_cas field length to handle multiple CAS numbers
ALTER TABLE ephy_substances 
ALTER COLUMN numero_cas TYPE VARCHAR(200);

-- Verify the change
SELECT 
    'ephy_substances.numero_cas' as field,
    data_type,
    character_maximum_length
FROM information_schema.columns
WHERE table_name = 'ephy_substances' 
AND column_name = 'numero_cas';

SELECT '✅ Schema fixed! You can now re-run the import.' as status;

