-- Migration: Add file_hash field to knowledge_base_documents
-- This enables content-based duplicate detection and better file management

-- Add file_hash column with index for fast duplicate lookups
ALTER TABLE knowledge_base_documents 
ADD COLUMN IF NOT EXISTS file_hash VARCHAR(64);

-- Create index for fast duplicate detection queries
CREATE INDEX IF NOT EXISTS idx_knowledge_base_documents_file_hash 
ON knowledge_base_documents(file_hash);

-- Create composite index for organization-specific duplicate detection
CREATE INDEX IF NOT EXISTS idx_knowledge_base_documents_org_hash 
ON knowledge_base_documents(organization_id, file_hash);

-- Add comment explaining the field
COMMENT ON COLUMN knowledge_base_documents.file_hash IS 'SHA-256 hash of file content for duplicate detection and integrity verification';

-- Update existing documents with NULL file_hash (they will be calculated on next access)
-- This is safe as the field is nullable
UPDATE knowledge_base_documents 
SET file_hash = NULL 
WHERE file_hash IS NULL;

-- Log the migration
INSERT INTO migration_log (version, description, applied_at) 
VALUES ('004', 'Add file_hash field for content-based duplicate detection', NOW())
ON CONFLICT (version) DO NOTHING;
