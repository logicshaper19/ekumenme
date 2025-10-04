-- Migration: Clean up any remaining FileStorage artifacts
-- This ensures a clean rollback from the complex approach

-- Drop any remaining file_storage_id columns (should already be done)
ALTER TABLE knowledge_base_documents 
DROP COLUMN IF EXISTS file_storage_id;

-- Drop any remaining file_storage tables (should already be done)
DROP TABLE IF EXISTS file_storage CASCADE;

-- Ensure file_hash column exists and is properly indexed
ALTER TABLE knowledge_base_documents 
ADD COLUMN IF NOT EXISTS file_hash VARCHAR(64);

-- Ensure file_path column exists
ALTER TABLE knowledge_base_documents 
ADD COLUMN IF NOT EXISTS file_path VARCHAR(500);

-- Create indexes if they don't exist
CREATE INDEX IF NOT EXISTS idx_knowledge_base_documents_file_hash 
ON knowledge_base_documents(file_hash);

CREATE INDEX IF NOT EXISTS idx_org_hash 
ON knowledge_base_documents(organization_id, file_hash);

-- Create unique constraint if it doesn't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint 
        WHERE conname = 'uq_org_file_hash'
    ) THEN
        ALTER TABLE knowledge_base_documents 
        ADD CONSTRAINT uq_org_file_hash 
        UNIQUE (organization_id, file_hash);
    END IF;
END $$;

-- Add comments
COMMENT ON COLUMN knowledge_base_documents.file_hash IS 'SHA-256 hash for per-organization duplicate detection';
COMMENT ON COLUMN knowledge_base_documents.file_path IS 'Local file path for the stored document';
COMMENT ON CONSTRAINT uq_org_file_hash ON knowledge_base_documents IS 'Prevents duplicate files within the same organization';

-- Log the migration
INSERT INTO migration_log (version, description, applied_at) 
VALUES ('007', 'Clean up FileStorage rollback and ensure proper schema', NOW())
ON CONFLICT (version) DO NOTHING;
