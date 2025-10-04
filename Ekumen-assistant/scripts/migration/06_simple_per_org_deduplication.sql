-- Migration: Implement simple per-organization deduplication
-- This replaces the complex FileStorage approach with simple per-org deduplication

-- Add unique constraint for per-org deduplication
ALTER TABLE knowledge_base_documents 
ADD CONSTRAINT uq_org_file_hash 
UNIQUE (organization_id, file_hash);

-- Create index for fast per-org duplicate lookups
CREATE INDEX IF NOT EXISTS idx_org_hash 
ON knowledge_base_documents(organization_id, file_hash);

-- Add comments
COMMENT ON CONSTRAINT uq_org_file_hash ON knowledge_base_documents IS 'Prevents duplicate files within the same organization';
COMMENT ON INDEX idx_org_hash IS 'Fast lookup for per-organization duplicate detection';

-- Log the migration
INSERT INTO migration_log (version, description, applied_at) 
VALUES ('006', 'Implement simple per-organization deduplication', NOW())
ON CONFLICT (version) DO NOTHING;
