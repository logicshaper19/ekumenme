-- Migration: Add file_hash column to Supabase database
-- This adds the missing file_hash column to the knowledge_base_documents table

-- Add file_hash column if it doesn't exist
ALTER TABLE knowledge_base_documents 
ADD COLUMN IF NOT EXISTS file_hash VARCHAR(64);

-- Add file_path column if it doesn't exist (should already exist, but just in case)
ALTER TABLE knowledge_base_documents 
ADD COLUMN IF NOT EXISTS file_path VARCHAR(500);

-- Create index for file_hash if it doesn't exist
CREATE INDEX IF NOT EXISTS idx_knowledge_base_documents_file_hash 
ON knowledge_base_documents(file_hash);

-- Create index for organization_id + file_hash if it doesn't exist
CREATE INDEX IF NOT EXISTS idx_org_hash 
ON knowledge_base_documents(organization_id, file_hash);

-- Create unique constraint for per-organization deduplication if it doesn't exist
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
