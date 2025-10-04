-- Migration: Create FileStorage table and update KnowledgeBaseDocument
-- This implements the enhanced file storage system with reference counting

-- Create FileStorage table for physical file management
CREATE TABLE IF NOT EXISTS file_storage (
    id SERIAL PRIMARY KEY,
    file_hash VARCHAR(64) UNIQUE NOT NULL,
    stored_path VARCHAR(512) UNIQUE NOT NULL,
    file_size BIGINT NOT NULL,
    mime_type VARCHAR(127),
    original_filename VARCHAR(255),
    reference_count INTEGER DEFAULT 0 NOT NULL,
    last_accessed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW() NOT NULL
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_file_storage_hash ON file_storage(file_hash);
CREATE INDEX IF NOT EXISTS idx_file_storage_references ON file_storage(reference_count);
CREATE INDEX IF NOT EXISTS idx_file_storage_cleanup ON file_storage(reference_count, created_at);

-- Add file_storage_id column to knowledge_base_documents
ALTER TABLE knowledge_base_documents 
ADD COLUMN IF NOT EXISTS file_storage_id INTEGER REFERENCES file_storage(id);

-- Create index for the foreign key
CREATE INDEX IF NOT EXISTS idx_kb_docs_file_storage_id ON knowledge_base_documents(file_storage_id);

-- Add comments
COMMENT ON TABLE file_storage IS 'Physical file storage with reference counting for deduplication';
COMMENT ON COLUMN file_storage.file_hash IS 'SHA-256 hash of file content for deduplication';
COMMENT ON COLUMN file_storage.stored_path IS 'Physical file path on disk';
COMMENT ON COLUMN file_storage.reference_count IS 'Number of documents referencing this file';
COMMENT ON COLUMN knowledge_base_documents.file_storage_id IS 'Reference to physical file storage';

-- Update existing documents to have NULL file_storage_id (they will be migrated separately)
UPDATE knowledge_base_documents 
SET file_storage_id = NULL 
WHERE file_storage_id IS NULL;

-- Log the migration
INSERT INTO migration_log (version, description, applied_at) 
VALUES ('005', 'Create FileStorage table with reference counting', NOW())
ON CONFLICT (version) DO NOTHING;
